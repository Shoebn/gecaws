from gec_common.gecclass import *
import logging
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
SCRIPT_NAME = "in_ppclgov_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.main_language = 'EN'
    notice_data.currency = 'INR'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.procurement_method = 2
    
    notice_data.script_name = "in_ppclgov_spn"
    
    notice_data.notice_type = 4
    
    notice_data.document_type_description = "Tenders"
          
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, ' td:nth-child(2) ').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass 

    
    notice_data.notice_url = url
        
    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, ' td:nth-child(3)').text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, " td:nth-child(4)").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
   
            
    try:              
        customer_details_data = customer_details()
        # Onsite Field -Organization
        # Onsite Comment -None

        customer_details_data.org_name = "PUDUCHERRY POWER CORPORATION LIMITED"
            
        customer_details_data.org_phone = "04132204043"
        
        org_parent_id ="7648025"
        customer_details_data.org_parent_id = int(org_parent_id)
        
        customer_details_data.org_country = 'IN'
        customer_details_data.org_language = 'EN'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:  
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, '  td:nth-child(2) a'):
            attachments_data = attachments()

            attachments_data.file_name = single_record.text

            attachments_data.external_url = single_record.get_attribute('href')

            attachments_data.file_type = "pdf"

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__))
        pass
    

    notice_data.identifier = str(notice_data.script_name) + str(notice_data.publish_date) +  str(notice_data.notice_url) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title)      
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments) 

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d %H:%M:%S')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['http://ppclgov.in/index.php?page=tenders'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        for page_no in range(1,5):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[3]/div[2]/div/div[2]/div/div/div/table/tbody/tr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[3]/div[2]/div/div[2]/div/div/div/table/tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[3]/div[2]/div/div[2]/div/div/div/table/tbody/tr')))[records]
                extract_and_save_notice(tender_html_element)
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break

            if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
                break

        try:   
            next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
            page_main.execute_script("arguments[0].click();",next_page)
            logging.info("Next page")
            WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/div[3]/div[2]/div/div[2]/div/div/div/table/tbody/tr'),page_check))
        except Exception as e:
            logging.info("Exception in next_page: {}".format(type(e).__name__))
            logging.info("No next page")
            
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)
