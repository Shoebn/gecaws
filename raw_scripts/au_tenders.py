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
SCRIPT_NAME = "au_tenders"
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
    notice_data.script_name = '"au_tenders"'
    
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
    # Onsite Comment -if document_type_description="Expression of Interest" then take notice_type = 5
    notice_data.notice_type = 4
    
    # Onsite Field -None
    # Onsite Comment -split the data from tender_html_page

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-sm-4 > div > p').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -ATM ID:
    # Onsite Comment -split only notice_no for ex . "ATM ID:DHA-PROC-71604", here split only "DHA-PROC-71604"

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-sm-8 div > div:nth-child(1)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Close Date & Time:
    # Onsite Comment --- split only notice_deadline for ex. "18-Aug-2023 2:00 pm (ACT Local Time)" , here split only "18-Aug-2023 "

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "div.col-sm-8 div:nth-child(2) div").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Full Details
    # Onsite Comment -inspect url for detail_page , ref url : "https://www.tenders.gov.au/Atm/Show/9d32f79d-27a2-4dd3-bab1-6c98e2f1ae85/"

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(6) >div > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += tender_html_element.find_element(By.CSS_SELECTOR, 'div.box.boxW.listInner').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    # Onsite Field -Publish Date:
    # Onsite Comment -split the publish_date from detail_page

    try:
        publish_date = single_record.find_element(By.XPATH, "//*[contains(text(),"Publish Date")]//following::div").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Description")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Description:
    # Onsite Comment -split the notice_summary_english from detail_page

    try:
        notice_data.notice_summary_english = single_record.find_element(By.XPATH, '//*[contains(text(),"Description")]//following::div').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -ATM Type:
    # Onsite Comment -split the data from detail_page, ref url : "https://www.tenders.gov.au/Atm/Show/e2444b5f-fccf-49d6-8cc3-59ad120f01f1"

    try:
        notice_data.document_type_description = single_record.find_element(By.XPATH, '//*[contains(text(),"ATM Type")]//following::div').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Estimated Value (AUD):
    # Onsite Comment -split only est_amount for ex. "From $1.00 to $180,000.00" , here split only "$180,000.00"

    try:
        notice_data.est_amount = single_record.find_element(By.XPATH, '//*[contains(text(),"Estimated Value (AUD)")]//following::div').text
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Estimated Value (AUD):
    # Onsite Comment -split only grossbudgetlc for ex. "From $1.00 to $180,000.00" , here split only "$180,000.00"

    try:
        notice_data.grossbudgetlc = single_record.find_element(By.XPATH, '//*[contains(text(),"Estimated Value (AUD)")]//following::div').text
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass


  
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#mainContent div > div.row'):
            customer_details_data = customer_details()

        
            customer_details_data.org_country = 'AU'
            customer_details_data.org_language = 'EN'
            
        # Onsite Field -Agency:
        # Onsite Comment -split the data from detail_page , ref url : "https://www.tenders.gov.au/Atm/Show/c818a625-d366-4b65-8408-9a873f90710b"

            try:
                customer_details_data.org_name = page_details.find_element(By.CSS_SELECTOR, 'div.box div:nth-child(2) > div').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass


        # Onsite Field -Contact Details
        # Onsite Comment -if specified selector selects person_name then  take this as org_address,     split the data from detail_page,   ref_url : "https://www.tenders.gov.au/Atm/Show/e2444b5f-fccf-49d6-8cc3-59ad120f01f1"

            try:
                customer_details_data.org_address = single_record.find_element(By.XPATH, '//*[contains(text(),"Contact Details")]//following::p[1]').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Contact Details
        # Onsite Comment -split the email_address from detail_page, url_ref: "https://www.tenders.gov.au/Atm/Show/319fd65a-4816-4a85-a34d-633954b6afaf"

            try:
                customer_details_data.org_email = single_record.find_element(By.XPATH, '//*[contains(text(),"Contact Details")]//following::a[1]').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Phone:
        # Onsite Comment -split the data between "Phone:" and "Email Address:" field,  ref_url : "https://www.tenders.gov.au/Atm/Show/e2444b5f-fccf-49d6-8cc3-59ad120f01f1" , "https://www.tenders.gov.au/Atm/Show/319fd65a-4816-4a85-a34d-633954b6afaf"

            try:
                customer_details_data.org_phone = single_record.find_element(By.XPATH, '//*[contains(text(),"Contact Details")]//following::p[2]').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass


            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    


# Onsite Field -Category:
# Onsite Comment -click on "Full Details" (selector : "div:nth-child(6) >div > a") for going  detail_page and split the data from "Category" field

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.box.boxW> div:nth-child(3)'):
            cpvs_data = cpvs()

        # Onsite Field -Category:
        # Onsite Comment -click on "Full Details" (selector : "div:nth-child(6) >div > a") for going  detail_page and split the data from "Category" field , for ex. "70140000 - Crop production and management and protection " here split only "70140000" , ref_url : "https://www.tenders.gov.au/Advert/Show/c4fde825-541e-404d-a5b4-047344669464"

            try:
                cpvs_data.cpv_code = single_record.find_element(By.XPATH, '//*[contains(text(),"Category")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in cpv_code: {}".format(type(e).__name__))
                pass
        
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
    



    # Onsite Field -ATM Documents
# Onsite Comment -in page_detail click on  "ATM Documents" (selector : "div.btn-actions > a:nth-child(1)" ) and add login credentials (login : padmavenim13@gmail.com password :Padma@12345) split the documents from page ,  ref_url for  page detail : "https://www.tenders.gov.au/Atm/Show/baab22ef-68df-4ce1-814b-e289f0d81726"

    try:              
        for single_record in page_details1.find_elements(By.CSS_SELECTOR, 'div.row > div.col-sm-8'):
            attachments_data = attachments()
        # Onsite Field -ATM Documents
        # Onsite Comment -in page_detail click on  "ATM Documents" (selector : "div.btn-actions > a:nth-child(1)" ) and add login credentials (login : padmavenim13@gmail.com password :Padma@12345) ,  ref_url for  page detail : "https://www.tenders.gov.au/Atm/Show/baab22ef-68df-4ce1-814b-e289f0d81726" ,  split only file_type for ex. "GEMS Products - attachment 12 - ATM - GEMS Check Testing Tender.docx" here, split only "docx" , ref url for page_detail_1 : "https://www.tenders.gov.au/Atm/ViewDocuments/1e1d7fa2-0516-4bc2-9ae8-ef00ed509db6"

            try:
                attachments_data.file_type = page_details1.find_element(By.CSS_SELECTOR, 'ul.file-list > li > a').text
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -ATM Documents
        # Onsite Comment -in page_detail click on  "ATM Documents" (selector : "div.btn-actions > a:nth-child(1)" ) and add login credentials (login : padmavenim13@gmail.com,  password :Padma@12345) split the documents from page_detail_1

            try:
                attachments_data.file_description = page_details1.find_element(By.CSS_SELECTOR, 'ul.file-list > li > a').text
            except Exception as e:
                logging.info("Exception in file_description: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -ATM Documents
        # Onsite Comment -in page_detail click on "ATM Documents" (selector : "div.btn-actions > a:nth-child(1)" ) and add login credentials (login : padmavenim13@gmail.com, password :Padma@12345), ref_url for page detail : "https://www.tenders.gov.au/Atm/Show/7ff2bc3d-9474-4d6b-905d-4a86a8ac2e69" ,  ------ split only file_name for ex. "PROC-71783 Schedule 2 -Annexures.zip    944 KB", here split only "zip" , ref url for page_detail_1 : "https://www.tenders.gov.au/Atm/ViewDocuments/7ff2bc3d-9474-4d6b-905d-4a86a8ac2e69"

            try:
                attachments_data.file_name = page_details1.find_element(By.CSS_SELECTOR, 'ul.file-list > li > a').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -ATM Documents
        # Onsite Comment -in page_detail click on "ATM Documents" (selector : "div.btn-actions > a:nth-child(1)" ) and add login credentials (login : padmavenim13@gmail.com, password :Padma@12345), ref_url for page detail : "https://www.tenders.gov.au/Atm/Show/7ff2bc3d-9474-4d6b-905d-4a86a8ac2e69" ,  ----- ref_url for page_detail_1 : "https://www.tenders.gov.au/Atm/ViewDocuments/7ff2bc3d-9474-4d6b-905d-4a86a8ac2e69"

            attachments_data.external_url = page_details1.find_element(By.CSS_SELECTOR, 'ul.file-list > li > a').get_attribute('href')
            
        
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
    urls = ["https://www.tenders.gov.au/atm"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,8):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="mainContent"]/div/div[3]/div/div'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="mainContent"]/div/div[3]/div/div')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="mainContent"]/div/div[3]/div/div')))[records]
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="mainContent"]/div/div[3]/div/div'),page_check))
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