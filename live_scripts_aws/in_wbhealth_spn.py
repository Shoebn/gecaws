from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "in_wbhealth_spn"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from selenium import webdriver
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn
from deep_translator import GoogleTranslator

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
tender_no = 0
SCRIPT_NAME = "in_wbhealth_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    global tender_no
    notice_data = tender()
    
    notice_data.script_name = 'in_wbhealth_spn'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)
    notice_data.currency = 'INR'
    
    notice_data.main_language = 'EN'
        
    notice_data.procurement_method = 2
    
    notice_data.notice_url = url
    
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = 'Government Of West Bengal Health & Family Welfare Department'
        customer_details_data.org_country = 'IN'
        customer_details_data.org_language = 'EN'
        customer_details_data.org_parent_id='7788206'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
        notice_data.notice_title =GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    if "expression of interest" in notice_data.local_title.lower():
        notice_data.notice_type = 5
    elif "cancellation notice" in notice_data.local_title.lower() or "corrigendum" in notice_data.local_title.lower() or "extension quotation notice" in notice_data.local_title.lower():
        notice_data.notice_type = 16
    else:
        notice_data.notice_type = 4
        
    try:
        attachments_data = attachments()
        attachments_data.external_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1) a').get_attribute("href")
        notice_data.notice_no = attachments_data.external_url.split('/')[-1].split('.')[0]
        try:
            attachments_data.file_type = attachments_data.external_url.split(".")[-1]
        except Exception as e:
            logging.info("Exception in file_type: {}".format(type(e).__name__))
            pass

        attachments_data.file_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1) a').text
        
        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    if notice_data.notice_url == 'https://www.wbhealth.gov.in/pages/notice':
        try:
            publish_date = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(3)').text
            notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.publish_date)
        except Exception as e:
            logging.info("Exception in publish_date: {}".format(type(e).__name__))
            pass

        if notice_data.publish_date is not None and notice_data.publish_date < threshold:
            return

        try:
            notice_data.local_description = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
            notice_data.notice_summary_english =GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
        except Exception as e:
            logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
            pass
    else:
        try:
            notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(2)').text
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.notice_deadline)
        except Exception as e:
            logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
            pass

        if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
            return
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    tender_no += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.wbhealth.gov.in/pages/tender","https://www.wbhealth.gov.in/pages/notice"] 
    for url in urls:
        fn.load_page(page_main, url, 80)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            page_check = WebDriverWait(page_main, 120).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#rap > table > tbody > tr > td:nth-child(2) > div > table > tbody > tr > td:nth-child(1) > div > div > div > div:nth-child(3) > table > tbody > tr'))).text
            rows = WebDriverWait(page_main, 120).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#rap > table > tbody > tr > td:nth-child(2) > div > table > tbody > tr > td:nth-child(1) > div > div > div > div:nth-child(3) > table > tbody > tr')))
            length = len(rows)
            for records in range(1,length,2):
                tender_html_element = WebDriverWait(page_main, 200).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#rap > table > tbody > tr > td:nth-child(2) > div > table > tbody > tr > td:nth-child(1) > div > div > div > div:nth-child(3) > table > tbody > tr')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break
    
                if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
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
