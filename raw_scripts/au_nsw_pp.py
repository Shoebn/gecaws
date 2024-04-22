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
import functions as fn
from functions import ET
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "au_nsw_pp"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.script_name = '"au_nsw_pp"'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'EN'
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'AU'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'AUD'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_type = 3
    
    # Onsite Field -Closes
    # Onsite Comment -split only date-month-year for ex."Closes: 4-Sep-2023 10:00" , here split only "4-Sep-2023"

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "li > p:nth-child(2)").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -split the data from tender_html_page

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'ul > li > h3').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -RFT ID
    # Onsite Comment -split only notice_no for ex."RFT ID: DCJ202316" , here split only "DCJ202316"

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, '#search-results li > ul > li').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass


    # Onsite Field -See details
    # Onsite Comment -if notice_no is not available from "RFT ID:" field, then split the notice_no from notice_url

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'li > div > a:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    
    # Onsite Field -RFT type
    # Onsite Comment -split the following data from "RFT type" field

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'li dl > dd:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -See details
    # Onsite Comment -inspect url for detail_page, ref_url for detail_page : "https://suppliers.buy.nsw.gov.au/scheme/1C132E95-DA3D-9683-2C7F54C02DFC2F0F"

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'li > div > a:nth-child(2)').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'section >div.nsw-wysiwyg-content').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    # Onsite Field -Last updated
    # Onsite Comment -split the data from detail_page

    try:
        publish_date = page_details.find_element(By.CSS_SELECTOR, "div:nth-child(2)  div > p.h2").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
 
    # Onsite Field -Scope  
    # Onsite Comment -take the data from detail_page, in the detail_page split the data between "Scope" ( xpath : "//*[contains(text(),"Scope")] " ) and "Instructions" ( xpath : " //*[contains(text(),"Instructions")] " )field, ref_url : "https://suppliers.buy.nsw.gov.au/scheme/1C132E95-DA3D-9683-2C7F54C02DFC2F0F"
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Scope")]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass

        
    # Onsite Field -Scope
    # Onsite Comment -take the data from detail_page, in the detail_page split the data between "Scope" ( xpath : "//*[contains(text(),"Scope")] " ) and "Instructions" ( xpath : " //*[contains(text(),"Instructions")] " )field, ref_url : "https://suppliers.buy.nsw.gov.au/scheme/1C132E95-DA3D-9683-2C7F54C02DFC2F0F"

    try:
        notice_data.notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),"Scope")]').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, '#search-results > ul > li'):
            customer_details_data = customer_details()

            customer_details_data.org_country = 'AU'
            customer_details_data.org_language = 'EN'

        # Onsite Field -Agency
        # Onsite Comment -split the data from tender_html_page

            try:
                customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'li> div > dl > dd:nth-child(4)').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
      
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    

    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'section > div.nsw-wysiwyg-content'):
            attachments_data = attachments()
        # Onsite Field -None
        # Onsite Comment -split only file_type for ex. "Schedule-2---Customer-Order-Form.docx", here split only "docx"

            try:
                attachments_data.file_type = page_details.find_element(By.CSS_SELECTOR, 'div.nsw-link-list__link > div:nth-child(2) span:nth-child(1)').text
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -if file_name contains following pattern "250523 SCM0053 Scheme Rules and Conditions - v2.0.pdf", then split only "250523 SCM0053 Scheme Rules and Conditions - v2.0

            try:
                attachments_data.file_name = page_details.find_element(By.CSS_SELECTOR, 'div.nsw-link-list__link > div > a').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -if file_size field contains following pattern for ex. "(VND.OPENXMLFORMATS-OFFICEDOCUMENT.WORDPROCESSINGML.DOCUMENT, 82 kb)", "(PDF, 389 kb)" , then here split only "82 kb" or "389 kb"

            try:
                attachments_data.file_size = page_details.find_element(By.CSS_SELECTOR, 'div.nsw-link-list__link > div:nth-child(2) span:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in file_size: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -None

            attachments_data.external_url = page_details.find_element(By.CSS_SELECTOR, 'div.nsw-link-list__link > div > a').get_attribute('href')
            
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) + str(notice_data.publish_date) +  str(notice_data.notice_url) 
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
    urls = ["https://suppliers.buy.nsw.gov.au/opportunity/search?query=&categories=&types=Schemes&page=1"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,5):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="search-results"]/ul/li'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="search-results"]/ul/li')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="search-results"]/ul/li')))[records]
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

            try:   
                next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                page_main.execute_script("arguments[0].click();",next_page)
                logging.info("Next page")
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="search-results"]/ul/li'),page_check))
            except Exception as e:
                logging.info("Exception in next_page: {}".format(type(e).__name__))
                logging.info("No next page")
                break
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit() 
    
    output_json_file.copyFinalJSONToServer(output_json_folder)