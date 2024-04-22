from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "in_gsecl_spn"
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
from selenium.webdriver.support.ui import Select

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "in_gsecl_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'INR'
    notice_data.main_language = 'EN'
    notice_data.procurement_method = 2
    notice_data.script_name = 'in_gsecl_spn'
    notice_data.notice_type = 4
    

    try:              
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR,'td:nth-child(8) a'):
            attachments_data = attachments()
            attachments_data.external_url= single_record.get_attribute('href')
            attachments_data.file_name = 'Tender Document'
            attachments_data.file_type = attachments_data.external_url.split('.')[-1]
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    try:
        notice_url = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(9) a').get_attribute('onclick')
        notice_url = notice_url.split('(')[1].split(')')[0]
        notice_data.notice_url = 'https://gsecl.in/tender/4tenderdocs.html?tenderdocs='+str(notice_url)+''
        fn.load_page(page_details,notice_data.notice_url,80)
        try:              
            for single_record in page_details.find_elements(By.CSS_SELECTOR,'#user_data > tr'):
                attachments_data = attachments()
                attachments_data.external_url= single_record.find_element(By.CSS_SELECTOR,'td:nth-child(3) a').get_attribute('href')
                attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR,'td:nth-child(2)').text
                try:
                    attachments_data.file_type = attachments_data.external_url.split('.')[-1]
                except:
                    pass
                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
        except Exception as e:
            logging.info("Exception in attachments: {}".format(type(e).__name__)) 
            pass
    except:
         notice_data.notice_url = url

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in notice_title: {}".format(type(e).__name__)) 
        pass
    
    try:
        publish_date =  tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(6)').text
        notice_data.publish_date = datetime.strptime(publish_date, '%d-%m-%Y').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__)) 
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    try:
        notice_deadline =  tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(7)').text.strip()
        notice_data.notice_deadline = datetime.strptime(notice_deadline, '%d-%m-%Y').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__)) 
        pass 
    try: 
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(1)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__)) 
        pass

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        try:
            org_address1 = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
            org_address2 = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
            customer_details_data.org_address = org_address1 + ' ' +org_address2
        except:
            pass
        customer_details_data.org_country = 'IN'
        customer_details_data.org_language = 'EN'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
        notice_data.notice_text += page_details.find_element(By.XPATH,'//*[@id="user_data"]').get_attribute('outerHTML')
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.notice_deadline) + str(notice_data.local_title)
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
    for page_no in range(1,5):
        urls = ['https://gsecl.in/tender/index.html?page='+str(page_no)+''] 

        for url in urls:
            fn.load_page(page_main, url, 50)
            logging.info('----------------------------------')
            logging.info(url)

            try:
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#table_user_data > tr')))
                length = len(rows) 
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#table_user_data > tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break

                    if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                        logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                        break
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
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
    page_details.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)
