

from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "in_tezu_spn"
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
SCRIPT_NAME = "in_tezu_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    notice_data.script_name = 'in_tezu_spn'
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)
    notice_data.currency = 'INR'
    notice_data.main_language = 'EN'
    notice_data.procurement_method = 2
    
    
    local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > strong').text
    notice_data.local_title = local_title
    notice_data.notice_title = notice_data.local_title    

    notice_type = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text

    if 'Cancellation' in notice_type or 'Extension' in notice_type:
        notice_data.notice_type = 16
    else:
        notice_data.notice_type = 4

    notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1) > strong').text
    try:
        notice_data.notice_no = notice_no.split('Dated')[0].strip()
    except:
        notice_data.notice_no = notice_no
    
    try:
        publish_date = notice_no.split('Dated')[1].strip()
        notice_data.publish_date = datetime.strptime(publish_date,'%d-%m-%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except:
        try:
            publish_date = notice_no.split('Dated')[1].split('.')[0].strip()
            notice_data.publish_date = datetime.strptime(publish_date,'%d-%m-%Y').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.publish_date)
        except:
            try:
                publish_date = notice_no.split('Dated:')[1].split('.')[0].strip()
                notice_data.publish_date = datetime.strptime(publish_date,'%d-%m-%Y').strftime('%Y/%m/%d %H:%M:%S')
                logging.info(notice_data.publish_date)        
            except Exception as e:
                logging.info("Exception in publish_date: {}".format(type(e).__name__))
                pass  
            
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return      

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(3)").text
        notice_deadline = re.findall('\d+-\d+-\d+ \d+:\d+', notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline, '%d-%m-%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass            

    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML') 
    except:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, '#AutoNumber3 > tbody').get_attribute("outerHTML")     

    notice_data.notice_url = 'http://www.tezu.ernet.in/notice/tender.html'

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = "TEZPUR UNIVERSITY"
        customer_details_data.org_parent_id = 7544711
        customer_details_data.org_country = 'IN'
        customer_details_data.org_language = 'EN'
        customer_details_data.org_state = 'Assam'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass       
    try:              
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, 'td:nth-child(2)'):
            
            file_name = single_record.find_element(By.CSS_SELECTOR, 'strong > a').text
            attachments_data = attachments()
            attachments_data.file_name = file_name
            
            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'strong > a').get_attribute('href') 
            try:
                file_type = attachments_data.external_url
                attachments_data.file_type = file_type.split('.')[-1].strip()
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
            
    except Exception as e:
        logging.info("Exception in attachments_1: {}".format(type(e).__name__)) 
        pass  

    try:              
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, 'td:nth-child(2)'):
                        
            file_name = single_record.find_element(By.CSS_SELECTOR, 'span > strong > span > a').text
            attachments_data = attachments()
            attachments_data.file_name = file_name            
            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'span > strong > span > a').get_attribute('href') 
            try:
                file_type = attachments_data.external_url
                attachments_data.file_type = file_type.split('.')[-1].strip()
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
            
    except Exception as e:
        logging.info("Exception in attachments_2: {}".format(type(e).__name__)) 
        pass  

    try:              
        for itrater in range(2,6):
            if itrater%2!=0:
                for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, 'td.style7'):
                    
                    file_name = single_record.find_element(By.CSS_SELECTOR, f'a:nth-child({itrater})').text
                    attachments_data = attachments()
                    attachments_data.file_name = file_name                    
                    attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, f'a:nth-child({itrater})').get_attribute('href') 
                    try:
                        file_type = attachments_data.external_url
                        attachments_data.file_type = file_type.split('.')[-1].strip()
                    except Exception as e:
                        logging.info("Exception in file_type: {}".format(type(e).__name__))
                        pass
                    attachments_data.attachments_cleanup()
                    notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments_3: {}".format(type(e).__name__)) 
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
    urls = ["http://www.tezu.ernet.in/notice/tender.html"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        time.sleep(10)
        try:
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#AutoNumber3 > tbody > tr')))
            length = len(rows)
            for records in range(1,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#AutoNumber3 > tbody > tr')))[records]  
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
