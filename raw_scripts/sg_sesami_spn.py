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
SCRIPT_NAME = "sg_sesami_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.script_name = 'sg_sesami_spn'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'EN'
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'SG'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'SGD'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_type = 4
    
    # Onsite Field -Type
    # Onsite Comment -None

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, '#DataGrid1 > tbody > tr > td:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -RFQ Ref. No.
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, '#DataGrid1 > tbody > tr > td:nth-child(3)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Description
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, '#DataGrid1 > tbody > tr > td:nth-child(4)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Starting Date
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "#DataGrid1 > tbody > tr > td:nth-child(5)").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Description
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, '#DataGrid1 > tbody > tr > td:nth-child(4)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Closing Date
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "#DataGrid1 > tbody > tr > td:nth-child(6)").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Action
    # Onsite Comment -when you inspect for notice_url , there is no URL available in href , kindly add the condition for it

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, '#DataGrid1 > tbody > tr > td:nth-child(5)').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -Action
    # Onsite Comment -if notice_no is not available in "RFQ Ref. No." then grab from notice_url

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, '#DataGrid1 > tbody > tr > td:nth-child(8) a').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Action
    # Onsite Comment -if notice_no is not available in "RFQ Ref. No." then grab from notice_url

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, '#DataGrid1 > tbody > tr > td:nth-child(8) a').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Action
    # Onsite Comment -when you inspect for notice_url , there is no URL available in href , kindly add the condition for it

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, '#DataGrid1 > tbody > tr > td:nth-child(5)').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, '#DataGrid1 > tbody > tr > td:nth-child(1)'):
            customer_details_data = customer_details()
        # Onsite Field -Buyer Company
        # Onsite Comment -None

            try:
                customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, '#DataGrid1 > tbody > tr > td:nth-child(1)').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
            customer_details_data.org_country = 'SG'
            customer_details_data.org_language = 'EN'
        # Onsite Field -Vendor Criteria/Site Showround/Briefing (if applicable):
        # Onsite Comment -for org_address split the data between "Place: " and "Contact person " , ref_url : "https://worldconnect.sesami.net/BO/RFQDetailsPopup.aspx?ITT_No=8ce7f987-f736-45d6-b3e9-6dc8f38e34e4"

            try:
                customer_details_data.org_address = page_details.find_element(By.CSS_SELECTOR, 'table > tbody > tr:nth-child(5) > td:nth-child(2) > b > font').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Vendor Eligibility: >> Location:
        # Onsite Comment -split the data after "Location: " , ref_url : "https://worldconnect.sesami.net/BO/RFQDetailsPopup.aspx?ITT_No=46ca1d19-37c5-4520-89c1-26d257ca526f"

            try:
                customer_details_data.org_address = page_details.find_element(By.CSS_SELECTOR, 'table > tbody > tr:nth-child(5) > td:nth-child(2) > b > font').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Contact person :
        # Onsite Comment -split the data after "Contact person :" , ref_url : "https://worldconnect.sesami.net/BO/RFQDetailsPopup.aspx?ITT_No=8ce7f987-f736-45d6-b3e9-6dc8f38e34e4"

            try:
                customer_details_data.contact_person = page_details.find_element(By.CSS_SELECTOR, 'table > tbody > tr:nth-child(5) > td:nth-child(2) > b > font').text
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass
        
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'tr:nth-child(2) > td > table > tbody > tr > td:nth-child(2) > table > tbody').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_url) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title)
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
    urls = [https://worldconnect.sesami.net/BO/businessOpportunities.aspx#] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,7):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/form/div[3]/table/tbody/tr[2]/td/table/tbody/tr/td/table/tbody/tr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/form/div[3]/table/tbody/tr[2]/td/table/tbody/tr/td/table/tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/form/div[3]/table/tbody/tr[2]/td/table/tbody/tr/td/table/tbody/tr')))[records]
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/form/div[3]/table/tbody/tr[2]/td/table/tbody/tr/td/table/tbody/tr'),page_check))
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