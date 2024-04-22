from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "br_balneariocamboriu_spn"
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
import gec_common.OutputJSON
from gec_common import functions as fn
import gec_common.Doc_Download
from selenium.webdriver.support.ui import Select


NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "br_balneariocamboriu_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"

# ----------------------------------------------------------------------------------------------------------------------------------------------------
# #     URL : https://www.balneariocamboriu.sc.gov.br/licitacoes.cfm
# #     go to "SITUAÇÃO" option and select "Todas " and "Aberto" for notice_type : 4 

# ------------------------------------------------------------------------------------------------------------------------------------------------------
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'br_balneariocamboriu_spn'

    notice_data.main_language = 'PT'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'BR'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'BRL'

    notice_data.notice_type = 4

    notice_data.procurement_method = 2
    
    # Onsite Field -N. de Processo:
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR,'td > a').get_attribute('href')                  
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url

    try:
        notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td > a > table > tbody > tr:nth-child(1) > td:nth-child(1)').text
        notice_data.notice_no = re.findall('Nº \d{3}.\d{4}',notice_no)[0]
    except:
        try:
            notice_data.notice_no = notice_data.notice_url.split('codigo=')[1].strip()
        except Exception as e:
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass



    # Onsite Field -None
    # Onsite Comment -if notice_no is not available in "N. de Processo:" then pass notice_no from notice_url

    # Onsite Field -Objeto:
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td > a > table > tbody > tr:nth-child(1) > td:nth-child(2)').text.split('Objeto:')[1].strip()
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Data da publicação:
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td > a > table > tbody > tr:nth-child(2) > td:nth-child(1)").text
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
        document_opening_time = tender_html_element.find_element(By.CSS_SELECTOR, 'td > a > table > tbody > tr:nth-child(2) > td:nth-child(3)').text.split(':')[1].strip()
        notice_data.document_opening_time = datetime.strptime(document_opening_time,'%d/%m/%Y').strftime('%Y-%m-%d')
    except Exception as e:
        logging.info("Exception in document_opening_time: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None
    
    try:
        cookies_click = WebDriverWait(page_details, 30).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'body > div.cardFlex > button')))
        page_details.execute_script("arguments[0].click();",cookies_click)
    except:
        pass
    
    scheight = .1

    while scheight < 9.9:
        page_details.execute_script("window.scrollTo(0, document.body.scrollHeight/%s);" % scheight)
        scheight += .01
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'body > div.super-wrapper > main > div').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    # Onsite Field -Valor estimado
    # Onsite Comment -split the est_amount after "Valor estimado" , ref_url : "https://www.balneariocamboriu.sc.gov.br/licitacao.cfm?codigo=2206"

    try:
        est_amount = page_details.find_element(By.CSS_SELECTOR, 'article > div > p:nth-child(1)').text.split('Valor estimado')[1].split('\n')[0].strip()
        est_amount = re.sub("[^\d\.\,]","",est_amount)
        notice_data.est_amount = float(est_amount.replace(',','.').replace('.',',').strip())
        notice_data.grossbudgetlc = notice_data.est_amount
    except:
        try:
            est_amount = page_details.find_element(By.CSS_SELECTOR, 'article > div > p:nth-child(1)').text.split('Valor máximo aceitável:')[1].split('\n')[0].strip()
            est_amount = re.sub("[^\d\.\,]","",est_amount)
            notice_data.est_amount = float(est_amount.replace(',','.').replace('.',',').strip())
            notice_data.grossbudgetlc = notice_data.est_amount
        except Exception as e:
            logging.info("Exception in est_amount: {}".format(type(e).__name__))
            pass
    
    # Onsite Field -Valor estimado
    # Onsite Comment -split the gross_budgetlc after "Valor estimado" , ref_url : "https://www.balneariocamboriu.sc.gov.br/licitacao.cfm?codigo=2206"


# Onsite Field -None
# Onsite Comment -None

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = 'Prefeitura de Balneário Camboriú'
        customer_details_data.org_parent_id = '7775788'
        customer_details_data.org_country = 'BR'
        customer_details_data.org_language = 'PT'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -Download the attachment
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'article:nth-child(1) > div > div'):
            attachments_data = attachments()
            attachments_data.file_name = 'tender documents'
        # Onsite Field -Download the attachment
        # Onsite Comment -None

            external_url = page_details.find_element(By.CSS_SELECTOR, 'article > div > div > button:nth-child(2)').get_attribute('onclick')
            attachments_data.external_url = external_url.split("('")[1].split("',")[0].strip()
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'ul.list-unstyled.lista-links.mt-1 > li'):
            attachments_data = attachments()
            attachments_data.file_type = 'pdf'
        # Onsite Field -None
        # Onsite Comment -split only file_name for ex."OBJECT : 1ST SAMPLE ANALYSIS - PUBLIC CALL Nº 012-2023 - PMBC" , here split only "1ST SAMPLE ANALYSIS - PUBLIC CALL Nº 012-2023 - PMBC" , ref_url : "https://www.balneariocamboriu.sc.gov.br/licitacao.cfm?codigo=2089"

            file_name = single_record.find_element(By.CSS_SELECTOR, 'a').get_attribute('innerHTML').split(">:")[1].split("<")[0].strip()
            attachments_data.file_name = file_name

            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    

    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
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
    urls = ["https://www.balneariocamboriu.sc.gov.br/licitacoes.cfm"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        try:
            cookies_click = WebDriverWait(page_main, 30).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'body > div.cardFlex > button')))
            page_main.execute_script("arguments[0].click();",cookies_click)
        except:
            pass
        
        index = [1,2]
        for types in index:
            pp_btn = Select(page_main.find_element(By.CSS_SELECTOR,'body > div.super-wrapper > main > div > div > div.col-sm-12.col-md-12 > form > div > div:nth-child(3) > div.col-md-4 > div > div > select'))
            pp_btn.select_by_index(types)
            
            search_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'body > div.super-wrapper > main > div > div > div.col-sm-12.col-md-12 > form > div > div:nth-child(3) > div.col-md-2 > div > input.btn.btn-primary')))
            page_main.execute_script("arguments[0].click();",search_click)
            time.sleep(5)
            
            scheight = .1

            while scheight < 9.9:
                page_main.execute_script("window.scrollTo(0, document.body.scrollHeight/%s);" % scheight)
                scheight += .01

            time.sleep(2)
            num = 2

            try:
                for page_no in range(1,5):
                    page_check = WebDriverWait(page_main, 80).until(EC.presence_of_element_located((By.CSS_SELECTOR,'body > div.super-wrapper > main > div > div > div.col-sm-12.col-md-12 > table > tbody > tr'))).text
                    rows = WebDriverWait(page_main, 80).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'body > div.super-wrapper > main > div > div > div.col-sm-12.col-md-12 > table > tbody > tr')))
                    length = len(rows)
                    for records in range(0,length):
                        tender_html_element = WebDriverWait(page_main, 80).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'body > div.super-wrapper > main > div > div > div.col-sm-12.col-md-12 > table > tbody > tr')))[records]
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
                        next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,"/html/body/div[1]/main/div/div/div[2]/nav/ul/li["+str(num)+"]/a")))
                        page_main.execute_script("arguments[0].click();",next_page)
                        logging.info("Next page")
                        WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'body > div.super-wrapper > main > div > div > div.col-sm-12.col-md-12 > table > tbody > tr'),page_check))
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
