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
SCRIPT_NAME = "in_apeproc"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    # Onsite Field -None
    # Onsite Comment -Note: Go to home page > "current tender" click on more And Tack also "Upcoming Tenders" click on more.
    notice_data.script_name = 'in_apeproc'
    
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
    notice_data.main_language = 'EN'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 0
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_type = 4
    
    # Onsite Field -IFB/Tender Notice Number
    # Onsite Comment -split notice_number

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Name of Project
    # Onsite Comment -None

    try:
        notice_data.local_title = page_main.find_element(By.XPATH, '//*[contains(text(),"Name of Project")]//following::td[1]').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_main.find_element(By.XPATH, '//*[contains(text(),"Name of Work")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Name of Work
    # Onsite Comment -None

    try:
        notice_data.notice_summary_english = page_main.find_element(By.XPATH, '//*[contains(text(),"Name of Work")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Bid Validity Period (in Days)
    # Onsite Comment -None

    try:
        notice_data.contract_duration = page_main.find_element(By.CSS_SELECTOR, 'table:nth-child(13) tr:nth-child(4) > td.tdwhite').text
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Bid Start Date & Time
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(7)").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Bid Submission Closing Date& Time
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(8)").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Bid Document Download Start Date & Time
    # Onsite Comment -None

    try:
        notice_data.document_purchase_start_time = page_main.find_element(By.CSS_SELECTOR, 'table:nth-child(13) tr:nth-child(1) > td.tdwhite').text
    except Exception as e:
        logging.info("Exception in document_purchase_start_time: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Bid Document Download End Date & Time
    # Onsite Comment -None

    try:
        notice_data.document_purchase_end_time = page_main.find_element(By.CSS_SELECTOR, 'table:nth-child(13) tr:nth-child(2) > td.tdwhite').text
    except Exception as e:
        logging.info("Exception in document_purchase_end_time: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Bid Submission Closing Date & Time
    # Onsite Comment -None

    try:
        notice_data.pre_bid_meeting_date = page_main.find_element(By.CSS_SELECTOR, 'table:nth-child(13) tr:nth-child(3) > td.tdwhite').text
    except Exception as e:
        logging.info("Exception in pre_bid_meeting_date: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Estimated Contract Value
    # Onsite Comment -None

    try:
        notice_data.grossbudgetlc = tender_html_element.find_element(By.CSS_SELECTOR, 'tbody > tr td.sorting_1').text
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Transaction Fee Details
    # Onsite Comment -None

    try:
        notice_data.document_fee = page_main.find_element(By.CSS_SELECTOR, 'table:nth-child(9)').text
    except Exception as e:
        logging.info("Exception in document_fee: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Action
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td > a:nth-child(1)').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, '#viewTenderBean').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    # Onsite Field -Tender Category
    # Onsite Comment -Relace following keywords with given keywords("WORKS=Works","PRODUCTS=Supply")

    try:
        notice_data.notice_contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'tbody tr td:nth-child(4)').text
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Bid Security (INR)
    # Onsite Comment -None

    try:
        notice_data.earnest_money_deposit = page_main.find_element(By.CSS_SELECTOR, 'table:nth-child(20) td.tdwhite').text
    except Exception as e:
        logging.info("Exception in earnest_money_deposit: {}".format(type(e).__name__))
        pass

# Onsite Field -None
# Onsite Comment -click on "Download Tender Documents" this selector on tender_html_element to get attachments data.

    try:              
        for single_record in page_main.find_elements(By.CSS_SELECTOR, '#viewTenderDocBean'):
            attachments_data = attachments()
        # Onsite Field -File Name
        # Onsite Comment -split file_name.eg.,"Volume - 1 400kV SS KSEZ.zip" don't take ".zip" in file_name.

            try:
                attachments_data.file_name = page_main.find_element(By.CSS_SELECTOR, 'table:nth-child(2) tr > td:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -File Name
        # Onsite Comment -split file_type.eg.,"Volume - 1 400kV SS KSEZ.zip" take only ".zip" in file_type.

            try:
                attachments_data.file_type = page_main.find_element(By.CSS_SELECTOR, 'table:nth-child(2) tr > td:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -File Description
        # Onsite Comment -None

            try:
                attachments_data.file_description = page_main.find_element(By.CSS_SELECTOR, 'table:nth-child(2) tr > td:nth-child(3)').text
            except Exception as e:
                logging.info("Exception in file_description: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -File Size(in Bytes)
        # Onsite Comment -None

            try:
                attachments_data.file_size = page_main.find_element(By.CSS_SELECTOR, 'table:nth-child(2) tr > td:nth-child(4)').text
            except Exception as e:
                logging.info("Exception in file_size: {}".format(type(e).__name__))
                pass
        
            # Onsite Field -Bulk DownLoad
            # Onsite Comment -Click on "Bulk DownLoad"
            
            external_url = page_main.find_element(By.CSS_SELECTOR, 'td > input:nth-child(2)').click()
            file_dwn = Doc_Download.file_download()
            attachments_data.external_url = str(file_dwn[0])
            
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, '#post-2609 > div > div.vc_hidden'):
            customer_details_data = customer_details()
            customer_details_data.org_country = 'IN'
            customer_details_data.org_state = 'AP'
            customer_details_data.org_language = 'EN'
        # Onsite Field -Department Name
        # Onsite Comment -None

            try:
                customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Address
        # Onsite Comment -None

            try:
                customer_details_data.org_address = page_main.find_element(By.CSS_SELECTOR, 'table:nth-child(17)  tr:nth-child(3) > td.tdwhite').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Email
        # Onsite Comment -None

            try:
                customer_details_data.org_email = page_main.find_element(By.CSS_SELECTOR, 'table:nth-child(17)  tr:nth-child(5) > td.tdwhite').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Contact Details
        # Onsite Comment -None

            try:
                customer_details_data.org_phone = page_main.find_element(By.CSS_SELECTOR, 'table:nth-child(17)  tr:nth-child(4) > td.tdwhite').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
        
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -Note:take lots by clicking "Schedules Details + view details "  >  "Enquiry Forms + Itemwise Formatx " tab  getting Lots details

    try:              
        for single_record in page_main.find_elements(By.CSS_SELECTOR, '#taTable > tbody > tr'):
            lot_details_data = lot_details()
        # Onsite Field -Item Name
        # Onsite Comment -None

            try:
                lot_details_data.lot_title = page_main.find_element(By.CSS_SELECTOR, '#taTable td:nth-child(3)').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Description Of Item
        # Onsite Comment -None

            try:
                lot_details_data.lot_description = page_main.find_element(By.CSS_SELECTOR, '#taTable td:nth-child(4)').text
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Quantity
        # Onsite Comment -None

            try:
                lot_details_data.lot_quantity = page_main.find_element(By.CSS_SELECTOR, '#taTable td:nth-child(6)').text
            except Exception as e:
                logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Bid Validity Period (in Days)
        # Onsite Comment -None

            try:
                lot_details_data.contract_duration = page_main.find_element(By.CSS_SELECTOR, 'table:nth-child(13) tr:nth-child(4) > td.tdwhite').text
            except Exception as e:
                logging.info("Exception in contract_duration: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Estimated Contract Value
        # Onsite Comment -Note:if the "lot_grossbudget_lc(Total Amount)" is not available in detail page take Tender grossbudget_lc in this field.

            try:
                lot_details_data.lot_grossbudget_lc = tender_html_element.find_element(By.CSS_SELECTOR, 'tbody > tr td.sorting_1').text
            except Exception as e:
                logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
                pass
                
        # Onsite Field -None
        # Onsite Comment -Note:take lot_details by clicking "View BOQ Item Details"

            try:
                lot_details_data.lot_title = page_main.find_element(By.CSS_SELECTOR, 'tbody tr.even').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -Note:take lot_details by clicking "View BOQ Item Details"

            try:
                lot_details_data.lot_description = page_main.find_element(By.CSS_SELECTOR, 'tbody tr.even').text
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Quantity
        # Onsite Comment -Note:take lot_details clicking "View BOQ Item Details"

            try:
                lot_details_data.lot_quantity = page_main.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(4)').text
            except Exception as e:
                logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -UOM
        # Onsite Comment -Note:take lot_details by clicking "View BOQ Item Details"

            try:
                lot_details_data.lot_quantity_uom = page_main.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(5)').text
            except Exception as e:
                logging.info("Exception in lot_quantity_uom: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Amount(INR)
        # Onsite Comment -Note:take lot_details by clicking "View BOQ Item Details"

            try:
                lot_details_data.lot_grossbudget_lc = page_main.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(7)').text
            except Exception as e:
                logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
                pass
                
        # Onsite Field -None
        # Onsite Comment -None

            try:
                for single_record in page_main.find_elements(By.CSS_SELECTOR, '#taTable > tbody > tr'):
                    lot_criteria_data = lot_criteria()
		
                    # Onsite Field -Award Criteria
                    # Onsite Comment -None

                    lot_criteria_data.lot_criteria_title = page_main.find_element(By.CSS_SELECTOR, '#taTable td:nth-child(9)').text
			
                    lot_criteria_data.lot_criteria_cleanup()
                    lot_details_data.lot_criteria.append(lot_criteria_data)
            except Exception as e:
                logging.info("Exception in lot_criteria: {}".format(type(e).__name__))
                pass
                
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
    # Onsite Field -Estimated Contract Value
    # Onsite Comment -None

    try:
        notice_data.est_amount = tender_html_element.find_element(By.CSS_SELECTOR, 'tbody > tr td.sorting_1').text
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_main.find_elements(By.CSS_SELECTOR, 'table > tbody > tr'):
            tender_criteria_data = tender_criteria()
        # Onsite Field -Evaluation Criteria
        # Onsite Comment -None

            try:
                tender_criteria_data.tender_criteria_title = page_main.find_element(By.CSS_SELECTOR, 'tr:nth-child(17) > td.tdwhite').text
            except Exception as e:
                logging.info("Exception in tender_criteria_title: {}".format(type(e).__name__))
                pass
        
            tender_criteria_data.tender_criteria_cleanup()
            notice_data.tender_criteria.append(tender_criteria_data)
    except Exception as e:
        logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    duplicate_check_data = fn.duplicate_check_data_from_previous_scraping(SCRIPT_NAME,MAX_NOTICES_DUPLICATE,notice_data.identifier,previous_scraping_log_check)
    NOTICE_DUPLICATE_COUNT = duplicate_check_data[1]
    if duplicate_check_data[0] == False:
        return
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
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
page_main = fn.init_chrome_driver(arguments) 
page_details = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://tender.apeprocurement.gov.in/login.html"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
    urls = ["https://tender.apeprocurement.gov.in/login.html"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,3):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="pagetable13"]/tbody/tr	3'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="pagetable13"]/tbody/tr	3')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="pagetable13"]/tbody/tr	3')))[records]
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="pagetable13"]/tbody/tr	3'),page_check))
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
        for page_no in range(2,3):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="pagetable14"]/tbody/tr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="pagetable14"]/tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="pagetable14"]/tbody/tr')))[records]
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="pagetable14"]/tbody/tr'),page_check))
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
    
    page_details.quit() 
    
    output_json_file.copyFinalJSONToServer(output_json_folder)