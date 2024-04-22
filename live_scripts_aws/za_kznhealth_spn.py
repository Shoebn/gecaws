from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "za_kznhealth_spn"
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
SCRIPT_NAME = "za_kznhealth_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'za_kznhealth_spn'

    notice_data.main_language = 'EN'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'ZA'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'ZAR'
    
    notice_data.procurement_method = 2

    try:
        try:
            notice_type = tender_html_element.find_element(By.CSS_SELECTOR,'th:nth-child(2) > span > a').text
        except:
            try:
                notice_type = tender_html_element.find_element(By.CSS_SELECTOR,'th:nth-child(2) > font > span > a').text
            except:
                try:
                    notice_type = tender_html_element.find_element(By.CSS_SELECTOR,'th:nth-child(2) > p > span > a').text
                except:
                    pass

        if 'Amendment' in notice_type:
            notice_data.notice_type = 16
        else:
            notice_data.notice_type = 4
    except Exception as e:
        logging.info("Exception in notice_type: {}".format(type(e).__name__))
        pass

    notice_data.document_type_description = "Current Tenders"
    notice_no = tender_html_element.find_element(By.CSS_SELECTOR,'th:nth-child(1)').text
    try:
        notice_data.notice_no = notice_no.split('  ')[1]
    except:
        notice_data.notice_no = notice_no
    
    notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR,'th:nth-child(2)').text
    notice_data.notice_title  = notice_data.local_title    
    
    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "th:nth-child(3)").text  
        notice_data.notice_deadline = datetime.strptime(notice_deadline, '%d %B %Y').strftime('%Y/%m/%d %H:%M:%S')   
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
        
    if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
        return

    notice_data.notice_url = "https://www.kznhealth.gov.za/Tenders/current-tenders.htm"
    notice_data.notice_text += tender_html_element.get_attribute('outerHTML')

    try:
        customer_details_data = customer_details()
        customer_details_data.org_country = 'ZA'
        customer_details_data.org_language = 'EN'
        customer_details_data.org_parent_id = 6991344
        customer_details_data.org_name = "KWAZULU-NATAL DEPARTMENT HEALTH"

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass    
    
    try:
        attachments_data = attachments()
        attachments_data.file_name = notice_type
        try:
            attachments_data.external_url = tender_html_element.find_element(By.CSS_SELECTOR,'th:nth-child(2) > span > a').get_attribute("href")  
        except:
            try:
                attachments_data.external_url = tender_html_element.find_element(By.CSS_SELECTOR,'th:nth-child(2) > font > span > a').get_attribute("href")    
            except:
                attachments_data.external_url = tender_html_element.find_element(By.CSS_SELECTOR,'th:nth-child(2) > p > span > a').get_attribute("href")    
                
        attachments_data.file_type = attachments_data.external_url.split('.')[-1]        
        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass        
    
    try:
        attachments_data = attachments()
        attachments_data.file_name = notice_data.notice_no
        try:
            attachments_data.external_url = tender_html_element.find_element(By.CSS_SELECTOR,'th:nth-child(1) > span > a').get_attribute("href")
        except:
            attachments_data.external_url = tender_html_element.find_element(By.CSS_SELECTOR,'th:nth-child(1) > a').get_attribute("href")
        attachments_data.file_type = attachments_data.external_url.split('.')[-1]
        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
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
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.kznhealth.gov.za/Tenders/current-tenders.htm"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'body > div.container-fluid > div > div > div.container > div.table-responsive > table > thead > tr'))).text
        rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'body > div.container-fluid > div > div > div.container > div.table-responsive > table > thead > tr')))
        length = len(rows)
        for records in range(1,length):
            tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'body > div.container-fluid > div > div > div.container > div.table-responsive > table > thead > tr')))[records] 
            extract_and_save_notice(tender_html_element)
            if notice_count >= MAX_NOTICES:
                break
                
            if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                break

    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()    
    output_json_file.copyFinalJSONToServer(output_json_folder)
