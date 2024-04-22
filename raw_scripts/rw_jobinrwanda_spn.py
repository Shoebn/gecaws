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
SCRIPT_NAME = "rw_jobinrwanda_spn"
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
    notice_data.main_language = 'EN'
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'RW'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'RWF'
    
    # Onsite Field -None
    # Onsite Comment -if the local_title has the "Request for Expressions of Interest (EoI)" keyword then take notice_type = 5,   if the local_title has the "AMENDED RFP" keyword then take notice_type = 16, if the local_title has "INVITATION FOR PRE-QUALIFICATION " keyword then take notice_type = 6
    notice_data.notice_type = 4
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-10 > div  h5').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Published on
    # Onsite Comment -split the data between "Published on" and " | Deadline" keyword

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div > div  div.col-10  p").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Deadline
    # Onsite Comment -split the date after "Deadline " keyword

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "div > div  div.col-10  p").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'div > p > span').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-10 > div.card-body > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#main > div').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, '#block-jix-core-theme-content > div > div > div > div > div'):
            customer_details_data = customer_details()
        # Onsite Field -None
        # Onsite Comment -None

            try:
                customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'article > div > div > div > div.col-10  p a').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
            customer_details_data.org_country = 'RW'
            customer_details_data.org_language = 'EN'
        # Onsite Field -None
        # Onsite Comment -for org_city split the data between "location symbol" and "Published on" keyword

            try:
                customer_details_data.org_city = tender_html_element.find_element(By.CSS_SELECTOR, 'div > div div.col-10 p').text
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -None

            try:
                customer_details_data.org_website = page_details.find_element(By.CSS_SELECTOR, 'div.card-footer.border-0.p-1  div.col-8 > a').text
            except Exception as e:
                logging.info("Exception in org_website: {}".format(type(e).__name__))
                pass

        # Onsite Field -None
        # Onsite Comment -click on "Read More" to open more details

            try:
                customer_details_data.org_description = page_details.find_element(By.CSS_SELECTOR, 'div > div#rmjs-1').text
            except Exception as e:
                logging.info("Exception in org_description: {}".format(type(e).__name__))
                pass
        
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
   
        
    # Onsite Field -Procurement Reference Number:
    # Onsite Comment -split the data after "Procurement Reference Number:" , ref_url : "https://www.jobinrwanda.com/job/amended-rfp-affordable-housing-study-afrrfp-affordable-housingdec2023"

    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, '(//*[contains(text(),'Procurement Reference Number:')])[1]//following::td//p[1]').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -RFQ No.
    # Onsite Comment -ref_no : "https://www.jobinrwanda.com/job/rfq-printing-services"

    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, '( //*[contains(text(),'RFQ No.')])[1]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -TENDER REFERENCE NUMBER:
    # Onsite Comment -ref_url: "https://www.jobinrwanda.com/job/tender-maintenance-various-it-equipment" , split the data after "TENDER REFERENCE NUMBER:"

    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),'TENDER REFERENCE NUMBER:')]').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -RFP#:
    # Onsite Comment -ref_url : "https://www.jobinrwanda.com/job/request-proposals-recruitment-consultant-develop-constitution-and-governance-structure-african"

    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),'RFP#:')]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -RFP#:
    # Onsite Comment -ref_url : "https://www.jobinrwanda.com/job/request-proposals-recruitment-consultant-develop-constitution-and-governance-structure-african"

    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),'RFP#:')]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -TENDER REFERENCE NUMBER:
    # Onsite Comment -ref_url: "https://www.jobinrwanda.com/job/tender-maintenance-various-it-equipment" , split the data after "TENDER REFERENCE NUMBER:"

    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),'TENDER REFERENCE NUMBER:')]').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -TENDER REFERENCE NUMBER:
    # Onsite Comment -ref_url: "https://www.jobinrwanda.com/job/tender-maintenance-various-it-equipment" , split the data after "TENDER REFERENCE NUMBER:"

    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),'TENDER REFERENCE NUMBER:')]').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
        
    # Onsite Field -Tender Document price (Frw)
    # Onsite Comment -ref_url : "https://www.jobinrwanda.com/job/tender-purchase-pick-double-cabin-vehicle-rwanda-rural-rehabilitation-initiative-rwarri"

    try:
        notice_data.document_cost = page_details.find_element(By.CSS_SELECTOR, 'tr> td:nth-child(4)').text
    except Exception as e:
        logging.info("Exception in document_cost: {}".format(type(e).__name__))
        pass
        
    
# Onsite Field -7.1 Technical Criteria
# Onsite Comment -ref_url : "https://www.jobinrwanda.com/job/request-proposals-recruitment-consultant-develop-constitution-and-governance-structure-african"

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.clearfix > table:nth-child(64)'):
            tender_criteria_data = tender_criteria()
        # Onsite Field -7.1 Technical Criteria
        # Onsite Comment -ref_url : "https://www.jobinrwanda.com/job/request-proposals-recruitment-consultant-develop-constitution-and-governance-structure-african"

            try:
                tender_criteria_data.tender_criteria_title = page_details.find_element(By.CSS_SELECTOR, 'table:nth-child(64) td:nth-child(1) > p:nth-child(1) > strong').text
            except Exception as e:
                logging.info("Exception in tender_criteria_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -7.1 Technical Criteria >> Points range
        # Onsite Comment -split data like "/30"  ,   ref_url : "https://www.jobinrwanda.com/job/request-proposals-recruitment-consultant-develop-constitution-and-governance-structure-african"

            try:
                tender_criteria_data.tender_criteria_weight = page_details.find_element(By.XPATH, '//*[contains(text(),'Points range')]//following::tr/td[2]').text
            except Exception as e:
                logging.info("Exception in tender_criteria_weight: {}".format(type(e).__name__))
                pass
        
            tender_criteria_data.tender_criteria_cleanup()
            notice_data.tender_criteria.append(tender_criteria_data)
    except Exception as e:
        logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -1. Attachment 1: Price schedule template
# Onsite Comment -ref_url : "https://www.jobinrwanda.com/job/rfq-printing-services"

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'table:nth-child(20)'):
            lot_details_data = lot_details()
        # Onsite Field -Item Name
        # Onsite Comment -ref_url : "https://www.jobinrwanda.com/job/rfq-printing-services"

            try:
                lot_details_data.lot_title = page_details.find_element(By.CSS_SELECTOR, 'table:nth-child(20) > tbody > tr> td:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -QTY
        # Onsite Comment -ref_url : "https://www.jobinrwanda.com/job/rfq-printing-services"

            try:
                lot_details_data.lot_quantity = page_details.find_element(By.CSS_SELECTOR, 'table:nth-child(20) > tbody > tr> td:nth-child(4)').text
            except Exception as e:
                logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Unity price in number (VAT inclusive)
        # Onsite Comment -ref_url : "https://www.jobinrwanda.com/job/rfq-printing-services"

            try:
                lot_details_data.lot_grossbudget_lc = page_details.find_element(By.CSS_SELECTOR, 'table:nth-child(20) > tbody > tr> td:nth-child(5)').text
            except Exception as e:
                logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
                pass
        
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -ref_url : "https://www.jobinrwanda.com/job/tender-purchase-pick-double-cabin-vehicle-rwanda-rural-rehabilitation-initiative-rwarri"

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'table > tbody'):
            lot_details_data = lot_details()
        # Onsite Field -Title of Tender
        # Onsite Comment -ref_url : "https://www.jobinrwanda.com/job/tender-purchase-pick-double-cabin-vehicle-rwanda-rural-rehabilitation-initiative-rwarri"

            try:
                lot_details_data.lot_title = page_details.find_element(By.CSS_SELECTOR, 'tr> td:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    

# Onsite Field -Attachment
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.XPATH, '//*[contains(text(),'Attachment')]'):
            attachments_data = attachments()
        # Onsite Field -Attachment
        # Onsite Comment -split ony text value

            try:
                attachments_data.file_name = page_details.find_element(By.XPATH, '//*[contains(text(),'Attachment')]//following::a[1]').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Attachment
        # Onsite Comment -None

            attachments_data.external_url = page_details.find_element(By.XPATH, '//*[contains(text(),'Attachment')]//following::a[1]').get_attribute('href')
            
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_url) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.notice_deadline) + str(notice_data.local_title) 
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
    urls = ["https://www.jobinrwanda.com/jobs/tender"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,3):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="block-jix-core-theme-content"]/div/div/div/div/div/article/div'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="block-jix-core-theme-content"]/div/div/div/div/div/article/div')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="block-jix-core-theme-content"]/div/div/div/div/div/article/div')))[records]
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="block-jix-core-theme-content"]/div/div/div/div/div/article/div'),page_check))
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