
from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "in_pdicai_spn"
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
SCRIPT_NAME = "in_pdicai_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    notice_data.script_name = 'in_pdicai_spn'
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)
    notice_data.currency = 'INR'
    notice_data.main_language = 'EN'
    notice_data.procurement_method = 2
    notice_data.notice_type = 4
    

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td > div > ul > li:nth-child(2) > div:nth-child(2) >p:nth-child(1)').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass                  
    
    try:
        notice_data.local_description = tender_html_element.find_element(By.CSS_SELECTOR, 'td > div > ul > li:nth-child(2) > div:nth-child(2) >p:nth-child(1)').text
        notice_data.notice_summary_english = notice_data.local_description
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass                  

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td > div > ul > li:nth-child(2) > div:nth-child(4)").text  
        publish_date = re.findall('\d+ \w+ \d+', publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d %b %Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass        

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return      

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td > div > ul > li:nth-child(1) > div").text
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%b, %d %Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)    
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass                 

    notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td > div > ul > li:nth-child(2) > div:nth-child(1) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
        
        notice_data.notice_no = notice_data.notice_url.split('=')[1].strip()
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#form1 > section.whatnew > div > div').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url    
        
    try:              
        customer_details_data = customer_details()
        
        org_name = tender_html_element.find_element(By.CSS_SELECTOR, "td > div > ul > li:nth-child(2) > div:nth-child(1)").text  
        customer_details_data.org_name = org_name.split(',')[0].strip()
                
        org_address = tender_html_element.find_element(By.CSS_SELECTOR, "td > div > ul > li:nth-child(2) > div:nth-child(2) >p:nth-child(2)").text  
        customer_details_data.org_address = org_address.split('Address : ')[1].strip()
        
        customer_details_data.org_city = customer_details_data.org_address.split(',')[0].strip()        
        customer_details_data.org_state = customer_details_data.org_address.split(',')[1].strip()
        org_phone = tender_html_element.find_element(By.CSS_SELECTOR, "td > div > ul > li:nth-child(2) > div:nth-child(2) >p:nth-child(3)").text  
        customer_details_data.org_phone = org_phone.split('Phone : ')[1].strip()
        
        org_email = tender_html_element.find_element(By.CSS_SELECTOR, "td > div > ul > li:nth-child(2) > div:nth-child(2) >p:nth-child(4)").text  
        customer_details_data.org_email = org_email.split('Email :')[1].strip()
        
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
        attachments_data.external_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td > div > ul > li:nth-child(2) > p > a').get_attribute('href')   
        try:
            attachments_data.file_type = external_url.split('.')[-1]
        except Exception as e:
            logging.info("Exception in file_type: {}".format(type(e).__name__))
            pass          
        
        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass        
            
    notice_data.identifier = str(notice_data.script_name)  +  str(notice_data.local_description) + str(notice_data.notice_type) +  str(notice_data.notice_url) 
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
arguments= ['ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments) 
page_details = fn.init_chrome_driver(arguments) 

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://pdicai.org/Opportunities.aspx"]
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        time.sleep(5)
                
        try:
            for page_no in range(2,10):
                page_check = WebDriverWait(page_main, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#ContentPlaceHolder1_gdvOpp > tbody > tr:nth-child(1)'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#ContentPlaceHolder1_gdvOpp > tbody > tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#ContentPlaceHolder1_gdvOpp > tbody > tr')))[records]   
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
                       
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
                try:   
                    next_page = WebDriverWait(page_main, 10).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    page_check2 = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#ContentPlaceHolder1_gdvOpp > tbody > tr:nth-child(1)'))).text  
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#ContentPlaceHolder1_gdvOpp > tbody > tr:nth-child(1)'),page_check))
                except Exception as e:
                    logging.info("Exception in next_page: {}".format(type(e).__name__))
                    logging.info("No next page")
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
            
    
    
