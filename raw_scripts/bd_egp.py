
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
SCRIPT_NAME = "bd_egp"
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
    notice_data.script_name = 'bd_egp'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'EN'
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.performance_country = None.find_element(By.None, 'BD').text
    except Exception as e:
        logging.info("Exception in performance_country: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'BDT'
    
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_type = 4
    
    # Onsite Field -Tender/Proposal ID
    # Onsite Comment -... Just take tender number  eg-"863696" from the data

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, '#resultTable td:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Procurement Nature, Title    ......."Goods - Supply" "Works - Works" "
    # Onsite Comment -just take "Procurement Nature" eg "good, services'

    try:
        notice_data.notice_contract_type = tender_html_element.find_element(By.CSS_SELECTOR, '#resultTable td:nth-child(3)').text
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Title
    # Onsite Comment -remove url just use title

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, '#resultTable td:nth-child(3) p').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Publishing Date and Time,
    # Onsite Comment -just split "Publishing Date and Time," from the data

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "#resultTable td:nth-child(6)").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Closing Date and Time
    # Onsite Comment -just split " Closing Date and Time" from the data

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "#resultTable td:nth-child(6)").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass


    # Onsite Field -Procurement Type 
    # Onsite Comment -if given as"NCT" take as "0"

    try:
        notice_data.procurement_method = page_details.find_element(By.XPATH, '//*[contains(text(),'Procurement Type ')]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in procurement_method: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Event Type :
    # Onsite Comment -None

    try:
        notice_data.document_type_description = page_details.find_element(By.XPATH, '//*[contains(text(),'Event Type')]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),'Category')]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Category
    # Onsite Comment -None

    try:
        notice_data.notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),'Category')]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass

           # Onsite Field -Project Name :
    # Onsite Comment -None

    try:
        notice_data.project_name = page_details.find_element(By.XPATH, '//*[contains(text(),'Project Name')]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in project_name: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Pre - Tender/Proposal meeting Start
    # Onsite Comment -None

    try:
        notice_data.pre_bid_meeting_date = page_details.find_element(By.XPATH, '//*[contains(text(),'Pre - Tender/Proposal meeting Start')]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in pre_bid_meeting_date: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -split data from Tender/Proposal Opening Date and Time :" till "Last Date and Time for Tender/Proposal Security"
    # Onsite Comment -None

    try:
        notice_data.document_opening_time = page_details.find_element(By.CSS_SELECTOR, 'table:nth-child(5) tr:nth-child(6) >td:nth-child(4)').text
    except Exception as e:
        logging.info("Exception in document_opening_time: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Category
    # Onsite Comment -ref url "https://www.eprocure.gov.bd/resources/common/ViewTender.jsp"

    try:
        notice_data.category = page_details.find_element(By.XPATH, '//*[contains(text(),'Category')]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in category: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Eligibility of Tenderer :
    # Onsite Comment -ref url "https://www.eprocure.gov.bd/resources/common/ViewTender.jsp"

    try:
        notice_data.eligibility = page_details.find_element(By.XPATH, '//*[contains(text(),'Eligibility of Tenderer')]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in eligibility: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Tender/Proposal Document Price (In BDT) :
    # Onsite Comment -ref url "https://www.eprocure.gov.bd/resources/common/ViewTender.jsp"

    try:
        notice_data.document_cost = page_details.find_element(By.XPATH, '//*[contains(text(),'Proposal Document Price')]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in document_cost: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -just take the title which is the url for detail page
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, '#resultTable td:nth-child(3) a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.XPATH, '#frmviewForm').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, '#frmviewForm'):
            customer_details_data = customer_details()
        # Onsite Field -Ministry, Division, Organization, PE
        # Onsite Comment -None

            try:
                customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, '#resultTable td:nth-child(4)').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Name of Official Inviting
        # Onsite Comment -None

            try:
                customer_details_data.contact_person = single_record.find_element(By.XPATH, '//*[contains(text(),"Name of Official Inviting")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Address
        # Onsite Comment -None

            try:
                customer_details_data.org_address = single_record.find_element(By.XPATH, '//*[contains(text(),"Address")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -City
        # Onsite Comment -None

            try:
                customer_details_data.org_city = single_record.find_element(By.XPATH, '//*[contains(text(),"City")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Phone No
        # Onsite Comment -None

            try:
                customer_details_data.org_phone = single_record.find_element(By.XPATH, '//*[contains(text(),"Phone No")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Fax No
        # Onsite Comment -None

            try:
                customer_details_data.org_fax = page_details.find_element(By.XPATH, '//*[contains(text(),"Fax No")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in org_fax: {}".format(type(e).__name__))
                pass
        
            customer_details_data.org_language = 'EN'
            customer_details_data.org_country = 'BD'
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -ref url "https://www.eprocure.gov.bd/resources/common/ViewTender.jsp"
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#frmviewForm'):
            lot_details_data = lot_details()
        # Onsite Field -Lot No.
        # Onsite Comment -None

            try:
                lot_details_data.lot_actual_number = single_record.find_element(By.CSS_SELECTOR, '#frmviewForm > table.tableList_1 td:nth-child(1)').text
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Identification of Lot
        # Onsite Comment -None

            try:
                lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, 'table.tableList_1 td:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Identification of Lot
        # Onsite Comment -None

            try:
                lot_details_data.lot_description = single_record.find_element(By.CSS_SELECTOR, 'table.tableList_1 td:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Tentative Start Date
        # Onsite Comment -None

            try:
                lot_details_data.contract_start_date = single_record.find_element(By.CSS_SELECTOR, 'table.tableList_1 td:nth-child(5)').text
            except Exception as e:
                logging.info("Exception in contract_start_date: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Tentative Completion Date
        # Onsite Comment -None

            try:
                lot_details_data.contract_end_date = single_record.find_element(By.CSS_SELECTOR, 'table.tableList_1 td:nth-child(6)').text
            except Exception as e:
                logging.info("Exception in contract_end_date: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Tender/Proposal security (Amount in BDT)
        # Onsite Comment -None

            try:
                lot_details_data.lot_grossbudget_lc = single_record.find_element(By.CSS_SELECTOR, 'table.tableList_1 td:nth-child(4)').text
            except Exception as e:
                logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
                pass
        
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
   
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#frmviewForm'):
            funding_agencies_data = funding_agencies()
        # Onsite Field -Development Partner :
        # Onsite Comment -None

            try:
                funding_agencies_data.funding_agency = page_details.find_element(By.XPATH, '//*[contains(text(),'Development Partner ')]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in funding_agency: {}".format(type(e).__name__))
                pass
        
            funding_agencies_data.funding_agencies_cleanup()
            notice_data.funding_agencies.append(funding_agencies_data)
    except Exception as e:
        logging.info("Exception in funding_agencies: {}".format(type(e).__name__)) 
        pass


# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#frmviewForm'):
            attachments_data = attachments()
        # Onsite Field -Documents
        # Onsite Comment -None

            attachments_data.external_url = page_details.find_element(By.CSS_SELECTOR, '#tdPrintDocument > td.t-align-left > a').get_attribute('href')
            
        
        # Onsite Field -Documents
        # Onsite Comment -None

            try:
                attachments_data.file_type = page_details.find_element(By.CSS_SELECTOR, '#tdPrintDocument > td.t-align-left > a').text
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Documents
        # Onsite Comment -None

            try:
                attachments_data.file_name = page_details.find_element(By.CSS_SELECTOR, '#tdPrintDocument > td.t-align-left > a').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass


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
page_details = fn.init_chrome_driver(arguments) 
page_main = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.eprocure.gov.bd/resources/common/StdTenderSearch.jsp?h=t"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,11):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="resultTable"]/tbody/tr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="resultTable"]/tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="resultTable"]/tbody/tr')))[records]
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="resultTable"]/tbody/tr'),page_check))
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
    