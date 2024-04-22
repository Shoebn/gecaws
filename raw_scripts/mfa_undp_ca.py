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
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "mfa_undp_ca"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.script_name = 'mfa_undp_ca'
    
    # Onsite Field -UNDP Office
    # Onsite Comment -Note:Splite after "-".....Ex,"UNDP CO - TURKEY" take only "TURKEY"            Note:File_name=mfa_undp_ca_countrycode.csv
    try:
        notice_data.performance_country = tender_html_element.find_element(By.CSS_SELECTOR, 'table tr:nth-child(4) > td:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in performance_country: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'EN'

    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'USD'

    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_type = 7
    
    # Onsite Field -Title :
    # Onsite Comment -Note:Split after "Title :" this keyword

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'table tr:nth-child(1) > th').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Contract Reference Number
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'table tr:nth-child(2) > td:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Posted on
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "table tr:nth-child(3) > td:nth-child(2)").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Procurement Method
    # Onsite Comment -None

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'table tr:nth-child(6) > td:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass    
    
    try:
        notice_data.local_description = tender_html_element.find_element(By.CSS_SELECTOR, 'table tr:nth-child(11) > td').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Description of Contract
    # Onsite Comment -Note:If local_description is not took than take from "td.content > table > tbody" this selector splite after "Description of Contract" this keyword

    try:
        notice_data.notice_summary_english = tender_html_element.find_element(By.CSS_SELECTOR, 'table tr:nth-child(11) > td').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, 'td.content > table > tbody'):
            customer_details_data = customer_details()
            customer_details_data.org_name = 'United Nations Development Programme'
            customer_details_data.org_parent_id = '7586854'
        # Onsite Field -UNDP Office
        # Onsite Comment -None

            try:
                customer_details_data.org_address = tender_html_element.find_element(By.CSS_SELECTOR, 'table tr:nth-child(4) > td:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass

        # Onsite Field -UNDP Office
        # Onsite Comment -Note:Splite after "-".....Ex,"UNDP CO - TURKEY" take only "TURKEY"            Note:File_name=mfa_undp_ca_countrycode.csv
            try:
                customer_details_data.org_country = tender_html_element.find_element(By.CSS_SELECTOR, 'table tr:nth-child(4) > td:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in org_country: {}".format(type(e).__name__))
                pass
            
            customer_details_data.org_language = 'EN'       
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, 'td.content > table > tbody'):
            lot_details_data = lot_details()
        # Onsite Field -Title :
        # Onsite Comment -Note:Split after "Title :" this keyword

            try:
                lot_details_data.lot_title = tender_html_element.find_element(By.CSS_SELECTOR, 'table tr:nth-child(1) > th').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -None

            try:
                for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, 'td.content > table > tbody'):
                    award_details_data = award_details()
		
                    # Onsite Field -Name of Contractor
                    # Onsite Comment -None

                    award_details_data.bidder_name = tender_html_element.find_element(By.CSS_SELECTOR, 'table tr:nth-child(7) > td:nth-child(2)').text
			
                    # Onsite Field -Country of Contractor
                    # Onsite Comment -None

                    award_details_data.bidder_country = tender_html_element.find_element(By.CSS_SELECTOR, 'table tr:nth-child(8) > td:nth-child(2)').text
			
                    # Onsite Field -Date of Contract Signature
                    # Onsite Comment -None

                    award_details_data.award_date = tender_html_element.find_element(By.CSS_SELECTOR, 'table tr:nth-child(9) > td:nth-child(2)').text
			
                    # Onsite Field -Contract Amount in US
                    # Onsite Comment -None

                    award_details_data.grossawardvaluelc = tender_html_element.find_element(By.CSS_SELECTOR, 'table tr:nth-child(10) > td:nth-child(2)').text
			
                    award_details_data.award_details_cleanup()
                    lot_details_data.award_details.append(award_details_data)
            except Exception as e:
                logging.info("Exception in award_details: {}".format(type(e).__name__))
                pass
			
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.notice_deadline) + str(notice_data.local_title)
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
    urls = ["https://procurement-notices.undp.org/view_awards.cfm"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,5):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/table/tbody/tr[1]/td[2]/table/tbody'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/table/tbody/tr[1]/td[2]/table/tbody')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/table/tbody/tr[1]/td[2]/table/tbody')))[records]
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/table/tbody/tr[1]/td[2]/table/tbody'),page_check))
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
