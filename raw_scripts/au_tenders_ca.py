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
SCRIPT_NAME = "au_tenders_ca"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"

# --------------------------------------------------------------------------------------------------------------------------------------------------


# to explore CA detail -------- 1) Go to url "tenders.gov.au/cn/search"
#                              2) scroll down and click on magneflying glass button (selector : "#actions > div > button")  
#           
                     


#  in the  tender_html_page if contract_notices shows "Amends:" (ex. " Amends:CN3911899 ") field, then skip that notice 


# -------------------------------------------------------------------------------------------------------------------------------------------------------------

def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.script_name = 'au_tenders_ca'
    
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
    notice_data.notice_type = 7
    
    # Onsite Field -CN ID:
    # Onsite Comment -split the data from tender_html page

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'article div.col-sm-8 div div:nth-child(1)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Publish Date:
    # Onsite Comment -specified selector is only for "publish_date" if they  selects "agency" skip that contract_notice

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div.col-sm-8 div:nth-child(3) > div").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Full Details
    # Onsite Comment -inspect url for detail_page , ref_url for detail_page : "https://www.tenders.gov.au/Cn/Show/dea386ba-7fdb-46ef-be92-ee56e49af7e1"

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'a.detail').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#mainContent div.row').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    # Onsite Field -Description:
    # Onsite Comment -split local_title from detail_page

    try:
        notice_data.local_title = page_details.find_element(By.XPATH, '//*[contains(text(),"Description")]//following::div[1]').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Description")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Description:
    # Onsite Comment -excluding the "Local_title /  Local_description "all fields should be in English,      , split notice_summary_english from detail_page

    try:
        notice_data.notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),"Description")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Procurement Method:
    # Onsite Comment -split the data from detail_page
    try:
        notice_data.type_of_procedure_actual = page_details.find_element(By.XPATH, "//*[contains(text(),"Procurement Method")]//following::div[1]").text
        notice_data.type_of_procedure = fn.procedure_mapping("assets/au_tenders_ca_procedure",notice_data.type_of_procedure_actual)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -split the customer_details from detail_page

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#mainContent div.row'):
            customer_details_data = customer_details()


            customer_details_data.org_country = 'AU'
            customer_details_data.org_language = 'EN'

        # Onsite Field -Agency:
        # Onsite Comment -split the data from detail_page

            try:
                customer_details_data.org_name = single_record.find_element(By.XPATH, '//*[contains(text(),"Agency:")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Contact Name:
        # Onsite Comment -split the data from "Agency Details" field , in detail_page, ref_url : "https://www.tenders.gov.au/Cn/Show/2a334fcb-ec18-4663-a360-a27bc04dfe3c"

            try:
                customer_details_data.contact_person = single_record.find_element(By.XPATH, '//*[contains(text(),"Agency Details")]//following::p[1]').text
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Phone:
        # Onsite Comment -split the data between "Phone:" and "Email Address:" field, ref_url : "https://www.tenders.gov.au/Cn/Show/2a334fcb-ec18-4663-a360-a27bc04dfe3c"

            try:
                customer_details_data.org_phone = single_record.find_element(By.XPATH, '//*[contains(text(),"Agency Details")]//following::p[2]').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Email Address:
        # Onsite Comment -split the data between "Email Address:" and "Division:" field, ref_url : "https://www.tenders.gov.au/Cn/Show/61afdf8f-c566-4fed-8172-bc2b8d0e1508"

            try:
                customer_details_data.org_website = single_record.find_element(By.XPATH, '//*[contains(text(),"Agency Details")]//following::p[3]').text
            except Exception as e:
                logging.info("Exception in org_website: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Office Postcode:
        # Onsite Comment -ref_url : "https://www.tenders.gov.au/Cn/Show/138d0d57-fbf6-4486-8741-b7f2a1dcd875"

            try:
                customer_details_data.postal_code = single_record.find_element(By.XPATH, '//*[contains(text(),"Agency Details")]//following::p[5]').text
            except Exception as e:
                logging.info("Exception in postal_code: {}".format(type(e).__name__))
                pass
        
      
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -split the data from detail_page

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#mainContent div.row >div:nth-child(2)'):
            lot_details_data = lot_details()
        # Onsite Field -Description:
        # Onsite Comment -split lot_title from detail_page

            try:
                lot_details_data.lot_title = single_record.find_element(By.XPATH, '//*[contains(text(),"Description")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Description:
        # Onsite Comment -split lot_description from detail_page

            try:
                lot_details_data.lot_description = single_record.find_element(By.XPATH, '//*[contains(text(),"Description")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Contract Period:
        # Onsite Comment -split contract_start_date for ex."7-Aug-2023 to 30-Oct-2024", here split only "7-Aug-2023" ,        ref_url : "https://www.tenders.gov.au/Cn/Show/61afdf8f-c566-4fed-8172-bc2b8d0e1508"

            try:
                lot_details_data.contract_start_date = single_record.find_element(By.XPATH, '//*[contains(text(),"Contract Period")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in contract_start_date: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Contract Period:
        # Onsite Comment -split contract_end_date for ex."7-Aug-2023 to 30-Oct-2024", here split only "30-Oct-2024" ,        ref_url : "https://www.tenders.gov.au/Cn/Show/61afdf8f-c566-4fed-8172-bc2b8d0e1508"

            try:
                lot_details_data.contract_end_date = single_record.find_element(By.XPATH, 'split contract_end_date for ex."7-Aug-2023 to 30-Oct-2024", here split only "30-Oct-2024" ,        ref_url : "https://www.tenders.gov.au/Cn/Show/61afdf8f-c566-4fed-8172-bc2b8d0e1508"').text
            except Exception as e:
                logging.info("Exception in contract_end_date: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Supplier Details
        # Onsite Comment -split the "award_details" from "Supplier Details" field, ref_url : "https://www.tenders.gov.au/Cn/Show/80a1f195-da33-4b60-b77b-6ca184fa0bed"

            try:
                for single_record in page_details.find_elements(By.CSS_SELECTOR, '#mainContent div.row >div:nth-child(2)'):
                    award_details_data = award_details()
		
                    # Onsite Field -Name:
                    # Onsite Comment -split the "bidder_name" from "Supplier Details" field, ref_url : "https://www.tenders.gov.au/Cn/Show/80a1f195-da33-4b60-b77b-6ca184fa0bed"

                    award_details_data.bidder_name = single_record.find_element(By.XPATH, '//*[contains(text(),"Supplier Details")]//following::div[1]').text
			
                    # Onsite Field -Postal Address:
                    # Onsite Comment -split the "address" from "Postal Address:" to "country" field (i.e take "Postal Address:","Town/City:","Postcode:","State/Territory:","Country:" , all fields in address), ref_url : "https://www.tenders.gov.au/Cn/Show/80a1f195-da33-4b60-b77b-6ca184fa0bed"

                    award_details_data.address = single_record.find_element(By.XPATH, '//*[contains(text(),"Postal Address:")]//following::div[1]').text
			
                    # Onsite Field -Contract Value (AUD):
                    # Onsite Comment -split the "grossawardvaluelc" from "Contract Value (AUD)" field, ref_url : "https://www.tenders.gov.au/Cn/Show/80a1f195-da33-4b60-b77b-6ca184fa0bed"

                    award_details_data.grossawardvaluelc = single_record.find_element(By.XPATH, '//*[contains(text(),"Contract Value")]//following::div[1]').text
			
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
    urls = ["https://www.tenders.gov.au/cn/search"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,7):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="mainContent"]/div[3]/div[2]/article/div/div[2]'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="mainContent"]/div[3]/div[2]/article/div/div[2]')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="mainContent"]/div[3]/div[2]/article/div/div[2]')))[records]
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="mainContent"]/div[3]/div[2]/article/div/div[2]'),page_check))
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