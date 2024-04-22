from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "br_balneariocamboriu_ca"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from deep_translator import GoogleTranslator
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select 
import gec_common.OutputJSON
from gec_common import functions as fn

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "br_balneariocamboriu_ca"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"

# -------------------------------------------------------------------------------------------------------------------------------------------------
#   open URL : "https://www.balneariocamboriu.sc.gov.br/licitacoes.cfm"

#  Go to  "SITUAÇÃO" and select "concluido" for award details and after that click on "Buscar" for apply


# ------------------------------------------------------------------------------------------------------------------------------------------------------------
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'br_balneariocamboriu_ca'
    notice_data.main_language = 'PT'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'BR'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'BRL'
    notice_data.notice_type = 7
    notice_data.procurement_method = 2

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'tr:nth-child(1)> td:nth-child(2)').get_attribute("innerHTML").split('>')[2].strip()
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Data da publicação:
    # Onsite Comment -None  

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "a tr:nth-child(2) > td:nth-child(1)").get_attribute("innerHTML")
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Data Abertura:
    # Onsite Comment -None

    try:
        document_opening_time = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').get_attribute("innerHTML")
        document_opening_time = re.findall('\d+/\d+/\d{4}',document_opening_time)[0]
        notice_data.document_opening_time = datetime.strptime(document_opening_time,'%d/%m/%Y').strftime('%Y/%m/%d')
    except Exception as e:
        logging.info("Exception in document_opening_time: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-sm-12.col-md-12   tr > td > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
        
    try: 
        ACEITO_clk = WebDriverWait(page_details, 10).until(EC.element_to_be_clickable((By.XPATH,"/html/body/div[6]/button"))).click()
        time.sleep(2)
    except:
        pass 
     
    try:
        notice_data.notice_no = notice_data.notice_url.split('=')[-1].strip()
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'body > div.super-wrapper > main > div').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')

    # Onsite Field -Samaroni Benedet Secretário de Compras
    # Onsite Comment - grab the data between "Balneário Camboriú 01 de dezembro de 2023" and "Secretário de Compras" field ,  ref_url : "https://www.balneariocamboriu.sc.gov.br/licitacao.cfm?codigo=2197"

    try:
        text_data = page_details.find_element(By.XPATH, '/html/body/div[1]/main/div/div/div[2]').text
    except:
        pass
    
    try:
        notice_data.contract_duration = text_data.split("Prazo de entrega:")[1].split('\n')[0].strip()
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass
    # Onsite Field -Preço global: , 
    # Onsite Comment -split the data between "Preço global:" and " (cento e três mil e setecentos reais)." , ref_url : "https://www.balneariocamboriu.sc.gov.br/licitacao.cfm?codigo=2208"

    try:
        if "Preço global:" in text_data:
            est_amount = text_data.split("Preço global:")[1].split('\n')[0].strip()
        elif "VALOR ESTIMADO:" in text_data:
            est_amount = text_data.split("VALOR ESTIMADO:")[1].split('\n')[0].strip()
        elif "Valor do contrato:" in text_data:
            est_amount = text_data.split("Valor do contrato:")[1].split('\n')[0].strip()
        else:
            pass
        est_amount = re.sub("[^\d\.\,]","",est_amount)
        notice_data.est_amount =float(est_amount.replace('.','').replace(',','.').strip())
        notice_data.grossbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = 'Prefeitura de Balneário Camboriú'
        customer_details_data.org_parent_id = '7775788'
        customer_details_data.org_country = 'BR'
        customer_details_data.org_language = 'PT'
        
        try: 
            contact_person1 = re.findall('[A-Za-zÀ-ÿ ]+. [0-9]{2} de [A-Za-zÀ-ÿ ]+ de [0-9]{4}\.',text_data)[0]
            contact_person = text_data.split(contact_person1)[1].strip()
            customer_details_data.contact_person = contact_person.split('\n')[0].strip()
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass
    
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    
    try:              
        lot_details_data = lot_details()
        lot_details_data.lot_number = 1
        lot_details_data.lot_title = notice_data.local_title
        notice_data.is_lot_default = True

        award_details_data = award_details()

        bidder_name = page_details.find_element(By.XPATH, '/html/body/div[1]/main/div/div/div[2]').text
        if "Empresa:" in bidder_name:
            bidder_names = bidder_name.split("Empresa:")[1].split('\n')[0].strip()
        elif "Contratado:" in bidder_name:
            bidder_names = bidder_name.split("Contratado:")[1].split('\n')[0].strip()
        award_details_data.bidder_name = bidder_names
        if bidder_names is not None or  bidder_names != '':
            award_details_data.award_details_cleanup()
            lot_details_data.award_details.append(award_details_data)
        
        if lot_details_data.award_details !=[]:
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass


    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) + str(notice_data.publish_date) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments) 
page_details = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://www.balneariocamboriu.sc.gov.br/licitacoes.cfm'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            time.sleep(2)
            ACEITO_clk = WebDriverWait(page_main, 10).until(EC.element_to_be_clickable((By.XPATH,"/html/body/div[6]/button"))).click()
            time.sleep(2)
        except:
            pass
        
        pp_btn = Select(page_main.find_element(By.CSS_SELECTOR,'div:nth-child(3) > div.col-md-4 > div > div > select')) 
        pp_btn.select_by_index(4) 
        time.sleep(2)
        
        BUSCAR_clk = WebDriverWait(page_main, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"input.btn.btn-primary"))).click()
        time.sleep(2)
        num = 2

        try:
            for page_no in range(1,5):
                page_check = WebDriverWait(page_main, 100).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[1]/main/div/div/div[2]/table/tbody/tr'))).text
                rows = WebDriverWait(page_main, 100).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/main/div/div/div[2]/table/tbody/tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 100).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/main/div/div/div[2]/table/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 180).until(EC.element_to_be_clickable((By.XPATH,"/html/body/div[1]/main/div/div/div[2]/nav/ul/li["+str(num)+"]/a")))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 100).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/div[1]/main/div/div/div[2]/table/tbody/tr'),page_check))
                    num +=1
                except Exception as e:
                    logging.info("Exception in next_page: {}".format(type(e).__name__))
                    logging.info("No next page")
                    break
        except:
            logging.info('No new record')
            break
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit()     
    output_json_file.copyFinalJSONToServer(output_json_folder)
