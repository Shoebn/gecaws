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
SCRIPT_NAME = "in_delhimetro"
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
    notice_data.script_name = 'in_delhimetro'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'EN'
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'INR'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_type = 4
    
    # Onsite Field -Tender
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1) p:nth-child(2)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    



    # Onsite Field -Tender
    # Onsite Comment -None

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'span:nth-child(2) > p:nth-child(1)').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    

    # Onsite Field -Date of Sale of Tender
    # Onsite Comment -split only first date, For ex. "From 27.07.2023 to 17.08.2023 (upto 15:00 hrs)" , here split only "27.07.2023"

    try:
        notice_data.document_purchase_start_time = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in document_purchase_start_time: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Date of Sale of Tender
    # Onsite Comment -split only 2nd date, For ex. "From 27.07.2023 to 17.08.2023 (upto 15:00 hrs)" , here split only "17.08.2023"

    try:
        notice_data.document_purchase_end_time = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in document_purchase_end_time: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Date of Sale of Tender
    # Onsite Comment -split only first date, For ex."From 27.07.2023 to 17.08.2023 (upto 15:00 hrs)" , here split only "27.07.2023"

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "tr > td:nth-child(2)").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Date & Time for Submission of Tender
    # Onsite Comment -split only notice_deadline, For ex. "11.08.2023 (from 09:00 Hrs) to 17.08.2023 (upto 15:00 Hrs)" , here split only "17.08.2023"

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "tr > td:nth-child(3)").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Date & Time of Opening of Tender
    # Onsite Comment -split only Date, For ex. "12.09.2023 (at 1500 Hrs)" , here split only "12.09.2023"

    try:
        notice_data.document_opening_time = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(4)').text
    except Exception as e:
        logging.info("Exception in document_opening_time: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_url = 'notice_url for this site : "https://www.delhimetrorail.com/pages/en/tenders_by_category/6uww"'
    
    # Onsite Field -None
    # Onsite Comment -there is no detail_page in this site
    try:
        notice_data.notice_text += tender_html_element.find_element(By.CSS_SELECTOR, 'div.table-responsive').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
# Onsite Field -None
# Onsite Comment -split the data from tender_html_page

    try:              
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, 'div.table-responsive'):
            customer_details_data = customer_details()
            customer_details_data.org_name = 'DELHI METRO RAIL CORPORATION LIMITED'
        # Onsite Field -Tender Issuing Authority
        # Onsite Comment -None

            try:
                customer_details_data.org_address = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(5)').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        
            customer_details_data.org_parent_id = '7247228'
            customer_details_data.org_country = 'IN'
            customer_details_data.org_language = 'EN'
            customer_details_data.org_city = 'Delhi'
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    

# Onsite Field -Tender
# Onsite Comment -None

    try:              
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, 'tr > td:nth-child(1)'):
            attachments_data = attachments()

        # Onsite Field -Tender
        # Onsite Comment -None

            try:
                attachments_data.file_type = tender_html_element.find_element(By.CSS_SELECTOR, 'span:nth-child(2) > p > img').text
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Tender
        # Onsite Comment -None

            try:
                attachments_data.file_name = tender_html_element.find_element(By.CSS_SELECTOR, 'span:nth-child(2) > p > img +a').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Tender
        # Onsite Comment -None

            attachments_data.external_url = tender_html_element.find_element(By.CSS_SELECTOR, 'span:nth-child(2) > p > img +a').get_attribute('href')
            
        
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
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://www.delhimetrorail.com/pages/en/tenders_by_category/6uww' ,  'https://www.delhimetrorail.com/pages/en/tenders_by_category/72mo',  'https://www.delhimetrorail.com/pages/en/tenders_by_category/7acg' ,  'https://www.delhimetrorail.com/pages/en/tenders_by_category/7i28',   'https://www.delhimetrorail.com/pages/en/tenders_by_category/7ps0',   'https://www.delhimetrorail.com/pages/en/tenders_by_category/7xhs',     'https://www.delhimetrorail.com/pages/en/tenders_by_category/8scw',     'https://www.delhimetrorail.com/pages/en/tenders_by_category/902o'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,3):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="root"]/div/div[3]/div[2]/table/tbody/tr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="root"]/div/div[3]/div[2]/table/tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="root"]/div/div[3]/div[2]/table/tbody/tr')))[records]
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="root"]/div/div[3]/div[2]/table/tbody/tr'),page_check))
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
    output_json_file.copyFinalJSONToServer(output_json_folder)