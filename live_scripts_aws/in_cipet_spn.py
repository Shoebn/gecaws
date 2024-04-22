

from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "in_cipet_spn"
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
SCRIPT_NAME = "in_cipet_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    notice_data.script_name = 'in_cipet_spn'
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)
    notice_data.currency = 'INR'
    notice_data.main_language = 'EN'
    notice_data.procurement_method = 2
    notice_data.notice_type = 4

    notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'tr:nth-child(3) > td:nth-child(2)').text
    notice_data.notice_title = notice_data.local_title    
    notice_data.document_type_description = 'TENDER NOTICE(S)'
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, 'tr:nth-child(1) > td:nth-child(2)').text
        try:
            publish_date = publish_date.split(',')[0]
            publish_date = publish_date.split('&')[0].strip()
        except:
            pass
        notice_data.publish_date = datetime.strptime(publish_date,'%d-%m-%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)        
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass  

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return      

    try:
        if 'Last Date' in tender_html_element.text:
            notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, 'tr:nth-child(4) > td:nth-child(2)').text
            notice_deadline = re.findall('\d+-\d+-\d+, \d+.\d+', notice_deadline)[0]
            notice_data.notice_deadline = datetime.strptime(notice_deadline, '%d-%m-%Y, %H.%M').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass            
    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML') 
    except:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, 'body > div.contbg > div.container > div').get_attribute("outerHTML")     
    notice_data.notice_url = 'https://www.cipet.gov.in/tender-notice/index.php'
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = tender_html_element.find_element(By.XPATH, f'(//*[contains(text(),"Centre")]//following::td[1])[{records+2}]').text  
        customer_details_data.org_country = 'IN'
        customer_details_data.org_language = 'EN'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass       
    try:           
        attachments_text = tender_html_element.find_element(By.CSS_SELECTOR,'tr:nth-child(4)').text
        if 'Download' in attachments_text:
            for single_record in tender_html_element.find_elements(By.CSS_SELECTOR,'tr:nth-child(4) > td:nth-child(2) > ul > li'):
                attachments_data = attachments()
                attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'a').get_attribute('href') 
                file_name = single_record.text
                attachments_data.file_name = file_name.split('(')[0].strip()
                try:
                    attachments_data.file_type = attachments_data.external_url.split('.')[-1]
                except Exception as e:
                    logging.info("Exception in file_type: {}".format(type(e).__name__))
                    pass          
                try:
                    attachments_data.file_size = file_name.split('(File Size:')[1].split(')')[0]
                except Exception as e:
                    logging.info("Exception in file_size: {}".format(type(e).__name__))
                    pass                 
                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
        else:
            for single_record in tender_html_element.find_elements(By.CSS_SELECTOR,'tr:nth-child(5) > td:nth-child(2) > ul > li'):
                attachments_data = attachments()
                attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'a').get_attribute('href') 
                file_name = single_record.text
                attachments_data.file_name = file_name.split('(')[0].strip()
                try:
                    attachments_data.file_type = attachments_data.external_url.split('.')[-1]
                except Exception as e:
                    logging.info("Exception in file_type: {}".format(type(e).__name__))
                    pass          
                try:
                    attachments_data.file_size = file_name.split('(File Size:')[1].split(')')[0]
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
    urls = ["https://www.cipet.gov.in/tender-notice/index.php"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        time.sleep(3)
        try:
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'body > div.contbg > div.container > div > div > table > tbody')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'body > div.contbg > div.container > div > div > table > tbody')))[records]  
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
