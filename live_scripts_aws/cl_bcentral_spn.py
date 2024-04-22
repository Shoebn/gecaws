from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "cl_bcentral_spn"
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

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "cl_bcentral_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
   
    notice_data.script_name = 'cl_bcentral_spn'
    
    notice_data.main_language = 'ES'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'CL'
    notice_data.performance_country.append(performance_country_data)
  
    notice_data.currency = 'CLF'
   
    notice_data.notice_type = 4
    
    notice_data.procurement_method = 2

    notice_data.document_type_description = 'Licitaciones y cotizaciones públicas'

    # Onsite Field - Fecha
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(1)").text
        publish_date = re.findall('\d+-\d+-\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d-%m-%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    # Onsite Field -Número
    # Onsite Comment -take only text value

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
  
    # Onsite Field -Title of the tender	
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    # Onsite Field -Número
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2) a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url

    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#portlet_urlamigable  div.portlet-content-container > div').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')

    try:
        notice_data.local_description = page_details.find_element(By.CSS_SELECTOR, 'section > div > h3').text
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass  

    # Onsite Field -CLOSE DATE & TIME
    # Onsite Comment -None December 28, 2023 until 2:00 p.m.
    try:
        notice_deadline = page_details.find_element(By.XPATH, '//*[contains(text(),"Fecha de recepción de Ofertas:")]//following::dd[1]').text
        notice_deadline = GoogleTranslator(source='auto', target='en').translate(notice_deadline)
        notice_deadline_date = re.findall('\w+ \d+, \d{4}',notice_deadline)[0]
        notice_deadline_time = re.findall('\d+:\d+',notice_deadline)[0]
        notice_deadline = notice_deadline_date+' '+notice_deadline_time
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%B %d, %Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    # Onsite Field -Fecha de adjudicación: January 17, 2024
    # Onsite Comment -split the date after "Fecha de adjudicación: "

    try:
        tender_award_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Fecha de adjudicación:")]//following::dd[1]').text
        tender_award_date = GoogleTranslator(source='auto', target='en').translate(tender_award_date)
        notice_data.tender_award_date = datetime.strptime(tender_award_date,'%B %d, %Y').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in tender_award_date: {}".format(type(e).__name__))
        pass

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = 'Banco Central Chile'
        customer_details_data.org_language = 'ES'
        customer_details_data.org_country = 'CL'
        customer_details_data.org_parent_id = '7769237'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

# Onsite Comment -ref_url : "https://www.bcentral.cl/contenido/-/detalle/servicio-corporativo-impresion-digitalizacion-copiado"
    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#portlet_urlamigable > div > div.portlet-content-container > div > div > section > div > div:nth-child(4) > div'):
            attachments_data = attachments()

            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'div > a > div.linkdoc-coltext').text
        
            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    duplicate_check_data = fn.duplicate_check_data_from_previous_scraping(SCRIPT_NAME,MAX_NOTICES_DUPLICATE,notice_data.identifier,previous_scraping_log_check)
    NOTICE_DUPLICATE_COUNT = duplicate_check_data[1]
    if duplicate_check_data[0] == False:
        return
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
    urls = ["https://www.bcentral.cl/en/el-banco/licitaciones-y-cotizaciones-publicas"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, "//*[@class='table-consultas  table-mobile']/tbody/tr")))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, "//*[@class='table-consultas  table-mobile']/tbody/tr")))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
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
