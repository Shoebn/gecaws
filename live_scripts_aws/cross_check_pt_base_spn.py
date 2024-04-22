#click on "Pesquisa avançada" next >>>  click on Anuncios(Adverts) from top left box>>> select dates "Data da publicação" >>> next click on "Pesquisar"

from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "cross_check_pt_base_spn"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from deep_translator import GoogleTranslator
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "cross_check_pt_base_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "cross_check_output"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = cross_check_output()

    notice_data.script_name = 'pt_base_spn'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'PT'
 
    notice_data.main_language = 'PT'
    notice_data.currency = 'EUR'
    notice_data.procurement_method = 2
    notice_data.notice_type = 4
    notice_data.class_at_source = 'CPV'


    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(7)>a').get_attribute("href")
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    
    try:
        notice_data.notice_no = notice_data.notice_url.split('=')[-1].strip()
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
        
    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(2)").text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
        
    # Onsite Field -Publicação
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(6)").text
        publish_date = re.findall('\d+-\d+-\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d-%m-%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return


    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

      # Onsite Field -Tipo de procedimento
    # Onsite Comment -None

    try:
        notice_data.type_of_procedure_actual = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        notice_data.type_of_procedure = fn.procedure_mapping("assets/pt_base_spn_procedure.csv",notice_data.type_of_procedure_actual)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass

    # Onsite Field -Prazo para apresentação de propostas
    # Onsite Comment -None
     # Onsite Field -Preço contratual
    # Onsite Comment -None

    try:
        est_amount = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
        est_amount = re.sub("[^\d\.\,]","",est_amount)
        notice_data.est_amount =float(est_amount.replace('.','').replace(',','.').strip())
        notice_data.netbudgetlc = notice_data.est_amount
        notice_data.netbudgeteuro = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
  
    notice_data.notice_text += tender_html_element.get_attribute('outerHTML')

    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.base.gov.pt/Base4/pt/pesquisa/?type=anuncios&texto=&numeroanuncio=&emissora=&desdedatapublicacao=&atedatapublicacao=&desdeprecobase=&ateprecobase=&tipoacto=0&tipomodelo=0&tipocontrato=0&cpv="] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        clk = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="advanced_anuncios"]'))).click()
        time.sleep(2)
        date_data = th.strftime('%Y-%m-%d')
        yest_date = page_main.find_element(By.XPATH,'//*[@id="desdedatapublicacao2"]').clear()
        yest_date = page_main.find_element(By.XPATH,'//*[@id="desdedatapublicacao2"]').send_keys(date_data)
        time.sleep(5)
        clk = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="search_anuncios2"]'))).click()
        time.sleep(2)
        try:
            for page_no in range(1,100):#100
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[2]/div/div/div[2]/div[2]/div[4]/table/tbody/tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[2]/div/div/div[2]/div[2]/div[4]/table/tbody/tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[2]/div/div/div[2]/div[2]/div[4]/table/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break

                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break

                    if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                        logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                        break

                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break

                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#page_'+str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/div[2]/div/div/div[2]/div[2]/div[4]/table/tbody/tr'),page_check))
                except Exception as e:
                    logging.info("Exception in next_page: {}".format(type(e).__name__))
                    logging.info("No next page")
                    break
        except:
            logging.info("No new record")
            break
            
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()

    output_json_file.copycrosscheckoutputJSONToServer(output_json_folder)
