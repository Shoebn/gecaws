from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "jo_arabpotash_spn"
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
SCRIPT_NAME = "jo_arabpotash_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.main_language = 'EN'
    notice_data.currency = 'JOD'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'JO'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.procurement_method = 2
    notice_data.script_name = "jo_arabpotash_spn"
    
    notice_data.notice_type = 4
          
    try:
        local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'h5.card-title.font-bold.mb-2.BorderClass').text
        local_title =re.split('\d{6}\/[A-Za-z]+',local_title)[1]
        if "-" or ":" in local_title:
            local_title = local_title.replace("-","").replace(":","").strip()
            notice_data.local_title = local_title
            notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass  
    
    
    try:
        notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'h5.card-title.font-bold.mb-2.BorderClass').text
        notice_data.notice_no =re.findall('\d{6}\/[A-Za-z]+',notice_no)[0]
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    except:
        pass
    
    try:
        notice_data.notice_url = tender_html_element.get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
        
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#aspnetForm > section.company-overview > div').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    try:
        document_purchase_end_time = page_details.find_element(By.CSS_SELECTOR, '''div#ctl00_ctl00_MainContent_ContentDetails_TendersSection''').text.split("Purchase Date:")[1].split("\n")[0].strip()
        document_purchase_end_time = re.findall('\d+/\d+/\d{4}',document_purchase_end_time)[0]
        notice_data.document_purchase_end_time = datetime.strptime(document_purchase_end_time,'%d/%m/%Y').strftime('%Y/%m/%d')
    except Exception as e:
        logging.info("Exception in document_purchase_end_time: {}".format(type(e).__name__))
        pass
    
    
    try:
        notice_deadline = page_details.find_element(By.CSS_SELECTOR, '''div#ctl00_ctl00_MainContent_ContentDetails_TendersSection''').text.split("Closing date:")[1].split("\n")[0].strip()
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
        return
    
    try:
        notice_data.earnest_money_deposit = page_details.find_element(By.CSS_SELECTOR, '''div#ctl00_ctl00_MainContent_ContentDetails_TendersSection''').text.split("Bid Bond Value:")[1].split("\n")[0].strip()
    except Exception as e:
        logging.info("Exception in earnest_money_deposit: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.document_fee = page_details.find_element(By.CSS_SELECTOR, '''div#ctl00_ctl00_MainContent_ContentDetails_TendersSection''').text.split("Copy Price:")[1].split("\n")[0].strip()
    except Exception as e:
        logging.info("Exception in document_fee: {}".format(type(e).__name__))
        pass
    
    notice_data.document_type_description = "Active Tenders"
        
    try:              
        customer_details_data = customer_details()
        # Onsite Field -Organization
        # Onsite Comment -None

        customer_details_data.org_name = "Arab Potash"
        customer_details_data.org_phone = "+962-6-5200520"
        customer_details_data.org_email = "procurment@arabpotash.com"
        
        org_parent_id ="7805282"
        customer_details_data.org_parent_id = int(org_parent_id)
        
        customer_details_data.org_country = 'JO'
        customer_details_data.org_language = 'EN'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:  
        for single_record in page_details.find_elements(By.XPATH, '/html/body/form/section[2]/div/div[1]/div/div/p'):
            attachments_data = attachments()

            attachments_data.file_name = single_record.text

            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, ' a').get_attribute('href')

            attachments_data.file_type = "pdf"
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__))
        pass
        
    
    notice_data.identifier = str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
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
    threshold = th.strftime('%Y/%m/%d %H:%M:%S')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://www.arabpotash.com/En/Modules/Tenders'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)

        try:
            for page_no in range(2,5):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/form/section[2]/div/div[1]/div/div/div[2]/section/div/div/div/div/a'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/form/section[2]/div/div[1]/div/div/div[2]/section/div/div/div/div/a')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/form/section[2]/div/div[1]/div/div/div[2]/section/div/div/div/div/a')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
                        
                    if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                        logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                        break
                        
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/form/section[2]/div/div[1]/div/div/div[2]/section/div/div/div/div/a'),page_check))
                except Exception as e:
                    logging.info("Exception in next_page: {}".format(type(e).__name__))
                    logging.info("No next page")
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
