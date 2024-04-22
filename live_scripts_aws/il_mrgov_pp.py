from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "il_mrgov_pp"
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
from selenium.webdriver.common.keys import Keys



NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "il_mrgov_pp"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'il_mrgov_pp'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IL'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'ILS'
    notice_data.main_language = 'HE'
    notice_data.procurement_method = 2
    notice_data.notice_type = 3
    

    
    try:
        notice_data.local_title  = tender_html_element.find_element(By.CSS_SELECTOR, 'a').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass  
        
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div > div > span:nth-child(5)').text  
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass  
            
    notice_data.notice_text += tender_html_element.get_attribute('outerHTML') 
 
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'a').get_attribute("href")              
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
        time.sleep
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
        
    notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#mainContent').get_attribute("outerHTML")    

    try:     
        publish_date =  page_details.find_element(By.XPATH, '//*[contains(text(),"Updated:")]//following::span[1]').text        
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass  
        
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:
        notice_deadline = page_details.find_element(By.XPATH, '(//*[contains(text(),"Deadline:")]//following::span[1])[1]').text  
        notice_data.notice_deadline = datetime.strptime(notice_deadline, '%d/%m/%Y ,%H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass    
    
    try:
        notice_data.document_type_description = page_details.find_element(By.XPATH, '(//*[contains(text(),"Status:")]//following::span[1])[1]').text  
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass        

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = page_details.find_element(By.XPATH, '(//*[contains(text(),"Publisher:")]//following::h2)[1]').text  
        contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Contact Name: ")]').text  
        customer_details_data.contact_person = contact_person.split('Contact Name:')[1].strip()

        customer_details_data.org_country = 'IL'
        customer_details_data.org_language = 'HE'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass           
    
    try:
        for single_record in page_details.find_elements(By.CSS_SELECTOR,'#related-documents > div.related-documents-wrapper-desktop.d-none.d-lg-flex.custom-container > div'):  
            attachments_data = attachments()

            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR,'div:nth-child(1) > div:nth-child(2) > h3').text  

            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR,'div:nth-child(2) > div > a').get_attribute("href")  

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments_data: {}".format(type(e).__name__)) 
        pass   

    

    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url)+  str(notice_data.local_title) 
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
    urls = ["https://mr.gov.il/ilgstorefront/en/search/?s=TENDER"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        time.sleep(3)
        
        future_click = WebDriverWait(page_main, 10).until(EC.element_to_be_clickable((By.XPATH,'//*[contains(text(),"עתידי")]')))
        page_main.execute_script("arguments[0].click();",future_click)
        logging.info("future_click")
        
        try:
            for scroll in  range(1,3):
                page_main.find_element(By.CSS_SELECTOR,'body').send_keys(Keys.END)
                time.sleep(7)

            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'div.content-wrapper.d-flex.justify-content-between.align-items-start.h-100 > div:nth-child(1) > div'))).text  
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.content-wrapper.d-flex.justify-content-between.align-items-start.h-100 > div:nth-child(1) > div')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.content-wrapper.d-flex.justify-content-between.align-items-start.h-100 > div:nth-child(1) > div')))[records]  
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

        except Exception as e:
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
    