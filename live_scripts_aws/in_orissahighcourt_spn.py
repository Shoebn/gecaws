
from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "in_orissahighcourt_spn"
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

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "in_orissahighcourt_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    notice_data.script_name = 'in_orissahighcourt_spn'
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)
    notice_data.currency = 'INR'
    notice_data.main_language = 'EN'
    notice_data.procurement_method = 2
    
    local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'a').text
    notice_data.local_title = local_title
    notice_data.notice_title = notice_data.local_title
    
    if 'Corrigendum' in local_title:
        notice_data.notice_type = 16
    else:
        notice_data.notice_type = 4
    notice_data.document_type_description = 'Tender Notice'

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "span:nth-child(2)").text
        publish_date = re.findall('\d+-\d+-\d+', publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d-%m-%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass  

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return      

    try:
        document_opening_time = tender_html_element.find_element(By.CSS_SELECTOR, "span:nth-child(3)").text
        document_opening_time = re.findall('\d+-\d+-\d+', document_opening_time)[0]
        notice_data.document_opening_time = datetime.strptime(document_opening_time,'%d-%m-%Y').strftime('%Y-%m-%d')
        logging.info(notice_data.document_opening_time)
    except Exception as e:
        logging.info("Exception in document_opening_time: {}".format(type(e).__name__))
        pass  

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "span:nth-child(4)").text
        notice_deadline = re.findall('\d+-\d+-\d+', notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d-%m-%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass  

    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML') 
    except:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, '#searchDetails').get_attribute("outerHTML")  

    notice_data.notice_url = 'https://www.orissahighcourt.nic.in/tender-notice/'

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = "HIGH COURT OF ORISSA"
        customer_details_data.org_parent_id = 7281210
        customer_details_data.org_state = 'orissa'
        customer_details_data.org_country = 'IN'
        customer_details_data.org_language = 'EN'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass       

    try:              
        attachments_data = attachments()
        attachments_data.file_name = 'Tender Document'
        attachments_data.external_url = tender_html_element.find_element(By.CSS_SELECTOR, 'span:nth-child(5) > a').get_attribute('href') 
        try:
            file_size = tender_html_element.find_element(By.CSS_SELECTOR, 'span:nth-child(5) > a').text
            attachments_data.file_size = file_size
        except Exception as e:
            logging.info("Exception in file_size: {}".format(type(e).__name__))
            pass
        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass


    notice_data.identifier = str(notice_data.script_name) + str(notice_data.local_title) +  str(notice_data.notice_type) +  str(notice_data.notice_url)+  str(notice_data.local_title) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
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
    urls = ["https://www.orissahighcourt.nic.in/tender-notice/"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        time.sleep(10)
        try:
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#searchDetails > li'))).text  
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#searchDetails > li')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#searchDetails > li')))[records]  
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
    output_json_file.copyFinalJSONToServer(output_json_folder)
