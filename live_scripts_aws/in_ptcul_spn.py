from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "in_ptcul_spn"
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

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "in_ptcul_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
   
    notice_data.script_name = 'in_ptcul_spn'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.main_language = 'EN'
    
    notice_data.currency = 'INR'
    
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 4
        
    notice_data.notice_url = url
    
    # Onsite Field -Click Here to download NIT no.
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Last Date of Downloading tender
    # Onsite Comment -None

    try:
        document_purchase_start_time = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        document_purchase_start_time = re.findall('\d+-\d+-\d{4}',document_purchase_start_time)[0]
        notice_data.document_purchase_start_time = datetime.strptime(document_purchase_start_time,'%d-%m-%Y').strftime('%Y/%m/%d')
    except Exception as e:
        logging.info("Exception in document_purchase_start_time: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Opening Date of tender
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text
        notice_deadline = re.findall('\d+-\d+-\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d-%m-%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
        return
    # Onsite Field -Opening Date of tender
    # Onsite Comment -None

    try:
        document_opening_time = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
        document_opening_time = re.findall('\d+-\d+-\d{4}',document_opening_time)[0]
        notice_data.document_opening_time = datetime.strptime(document_opening_time,'%d-%m-%Y').strftime('%Y-%m-%d')
    except Exception as e:
        logging.info("Exception in document_opening_time: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Closing Date of tender
    # Onsite Comment -None

    try:
        document_purchase_end_time = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
        document_purchase_end_time = re.findall('\d+-\d+-\d{4}',document_purchase_end_time)[0]
        notice_data.document_purchase_end_time = datetime.strptime(document_purchase_end_time,'%d-%m-%Y').strftime('%Y/%m/%d')
    except Exception as e:
        logging.info("Exception in document_purchase_end_time: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Description
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(9)').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:              
        attachments_data = attachments()
        # Onsite Field -Click Here to download NIT no.
        # Onsite Comment -1.take in text format.

        attachments_data.file_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a').text
        
        attachments_data.external_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a').get_attribute('href')

        try:
            attachments_data.file_type = attachments_data.external_url.split('.')[-1].strip()
        except Exception as e:
            logging.info("Exception in file_type: {}".format(type(e).__name__))
            pass

        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass

    try: 
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, 'td:nth-child(10) > a'):
            attachments_data = attachments()
        # Onsite Field -Download Tender Documents/Corrigendum
        # Onsite Comment -1.take file_name from "title" attribute title
            file_name = single_record.get_attribute('title')
            if file_name == '':
                attachments_data.file_name='Download Tender'
            else:
                attachments_data.file_name =file_name

            attachments_data.external_url = single_record.get_attribute('href')

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments1: {}".format(type(e).__name__)) 
        pass

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'IN'
        customer_details_data.org_language = 'EN'
        customer_details_data.org_name = 'Power Transmission Corporation Of Uttarakhand Limited'
        customer_details_data.org_parent_id = 7051013
        # Onsite Field -Address
        # Onsite Comment -None

        try:
            customer_details_data.org_address = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(7)').text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass

    # Onsite Field -Address
    # Onsite Comment -None

        try:
            customer_details_data.contact_person = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(7)').text
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
   
    try:
        notice_data.notice_text += tender_html_element.get_attribute("outerHTML")                     
    except:
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
    urls = ["https://ptcul.org/tender"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(2,4):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="pagin"]/tbody/tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="pagin"]/tbody/tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="pagin"]/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
                        break
    
                if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="pagin"]/tbody/tr'),page_check))
                except Exception as e:
                    logging.info("Exception in next_page: {}".format(type(e).__name__))
                    logging.info("No next page")
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
