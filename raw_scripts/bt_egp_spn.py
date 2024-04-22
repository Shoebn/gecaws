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
SCRIPT_NAME = "bt_egp_spn"
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
    notice_data.script_name = 'bt_egp_spn'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'EN'
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -Currency Name
    # Onsite Comment -ref_url : "https://www.egp.gov.bt/resources/common/ViewNotice.jsp?id=16844&h=t" , if currency field is  not available then pass static as a "BTN"

    try:
        notice_data.currency = page_details.find_element(By.CSS_SELECTOR, '#tblCurrency  tr > td.t-align-left').text
    except Exception as e:
        logging.info("Exception in currency: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -if the following field  i.e ("Tender ID, Reference No, Public Status")  has  "Live" keyword  then take notice_type = 4  and the field has "Amendment/Corrigendum issued:" keyword then take notice_type 16
    notice_data.notice_type = 4
    
    # Onsite Field -Type, Method
    # Onsite Comment -take only procurment_method for ex."NCB", "ICB",     if "Type Method" has "ICB" then take procurment_method=1,  if "Type Method" has "NCB" then take procurment_method=0

    try:
        notice_data.procurement_method = tender_html_element.find_element(By.CSS_SELECTOR, '#resultTable > tbody > tr> td:nth-child(5)').text
    except Exception as e:
        logging.info("Exception in procurement_method: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Tender ID, Reference No, Public Status
    # Onsite Comment -take only  notice_no,  for ex."16909, MD/DzEHSS-20/2023-2024/1206, Live", here split only "16909, MD/DzEHSS-20/2023-2024/1206"

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, '#resultTable   td:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Procurement Category, Title
    # Onsite Comment -split only notice_contract_type   for ex. "Works (Small), Construction of Inclusive class room at Mongar Middle Secondary School" , here split only "Works" , i.e first word,               Replace following keywords with given respective keywords ('Works = Works' , 'Goods = Supply' , 'Services = Service')

    try:
        notice_data.notice_contract_type = tender_html_element.find_element(By.CSS_SELECTOR, '#resultTable   td:nth-child(3)').text
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Procurement Category, Title
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, '#resultTable td:nth-child(3) a > span > p').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Publishing Date & Time | Closing Date & Time
    # Onsite Comment -split only first line as a publish_date  for ex."09-Nov-2023 09:00 | 01-Dec-2023 09:30" , here take only "09-Nov-2023"

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "#resultTable  td:nth-child(6)").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Publishing Date & Time | Closing Date & Time
    # Onsite Comment -split only second line as a notice_deadline  for ex."09-Nov-2023 09:00 | 01-Dec-2023 09:30" , here take only "01-Dec-2023 09:30"

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "#resultTable  td:nth-child(6)").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Procurement Category, Title
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
        notice_data.notice_text += page_details.find_element(By.ID, '#frmviewForm').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    # Onsite Field -Document last selling / downloading Date and Time :
    # Onsite Comment -ref_url : "https://www.egp.gov.bt/resources/common/ViewNotice.jsp?id=16919&h=t"

    try:
        notice_data.document_purchase_end_time = page_details.find_element(By.CSS_SELECTOR, 'table:nth-child(4) tr:nth-child(5) > td:nth-child(4)').text
    except Exception as e:
        logging.info("Exception in document_purchase_end_time: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Category :
    # Onsite Comment -ref_url : "https://www.egp.gov.bt/resources/common/ViewNotice.jsp?id=16919&h=t"

    try:
        notice_data.category = page_details.find_element(By.XPATH, '//*[contains(text(),"Category : ")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in category: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#frmviewForm > table:nth-child(2)'):
            funding_agencies_data = funding_agencies()
        # Onsite Field -Development Partner :
        # Onsite Comment -"Funding agency" name as "World Bank (internal id: 1012)" / "Austrian Development Agency (internal id: 7307798)" /  "ADB  (internal id:  106)" in field name "T.FUNDING_AGENCIES::TEXT"  ref_url : "https://www.egp.gov.bt/resources/common/ViewNotice.jsp?id=16927&h=t"

            try:
                funding_agencies_data.funding_agency = page_details.find_element(By.XPATH, '//*[contains(text(),"Development Partner :")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in funding_agency: {}".format(type(e).__name__))
                pass
        
            funding_agencies_data.funding_agencies_cleanup()
            notice_data.funding_agencies.append(funding_agencies_data)
    except Exception as e:
        logging.info("Exception in funding_agencies: {}".format(type(e).__name__)) 
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Brief Description ")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Brief Description of Goods and Related Service :
    # Onsite Comment -ref_url : "https://www.egp.gov.bt/resources/common/ViewNotice.jsp?id=16911&h=t"

    try:
        notice_data.notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),"Brief Description ")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.ID, '#frmviewForm'):
            customer_details_data = customer_details()
        # Onsite Field -Procuring Agency :
        # Onsite Comment -ref_url : "https://www.egp.gov.bt/resources/common/ViewNotice.jsp?id=16914&h=t"

            try:
                customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Procuring Agency :")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
            customer_details_data.org_country = 'BT'
            customer_details_data.org_language = 'EN'
        # Onsite Field -Name of Official Inviting Tender :
        # Onsite Comment -None

            try:
                customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Name of Official Inviting  Tender :")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Official Address :
        # Onsite Comment -None

            try:
                customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Address ")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -City
        # Onsite Comment -None

            try:
                customer_details_data.org_city = page_details.find_element(By.XPATH, '//*[contains(text(),"City")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Phone No
        # Onsite Comment -None

            try:
                customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Phone No")]//following::td[1]').text
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
        
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#frmviewForm > table.tableList_1'):
            lot_details_data = lot_details()
        # Onsite Field -None
        # Onsite Comment -None

            try:
                lot_details_data.lot_actual_number = page_details.find_element(By.XPATH, '//*[contains(text(),"Lot No.")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Identification of Lot
        # Onsite Comment -ref_url : "https://www.egp.gov.bt/resources/common/ViewNotice.jsp?id=16842&h=t"

            try:
                lot_details_data.lot_title = page_details.find_element(By.XPATH, '//*[contains(text(),"Lot No.")]//following::td[2]').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Contract Start Date
        # Onsite Comment -ref_url : "https://www.egp.gov.bt/resources/common/ViewNotice.jsp?id=16842&h=t"

            try:
                lot_details_data.contract_start_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Lot No.")]//following::td[5]').text
            except Exception as e:
                logging.info("Exception in contract_start_date: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Contract End Date
        # Onsite Comment -ref_url : "https://www.egp.gov.bt/resources/common/ViewNotice.jsp?id=16842&h=t"

            try:
                lot_details_data.contract_end_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Lot No.")]//following::td[6]').text
            except Exception as e:
                logging.info("Exception in contract_end_date: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Procurement Category, Title
        # Onsite Comment -split only notice_contract_type for ex. "Works (Small), Construction of Inclusive class room at Mongar Middle Secondary School" , here split only "Works" ,

            try:
                lot_details_data.contract_type = page_details.find_element(By.CSS_SELECTOR, '#resultTable td:nth-child(3)').text
            except Exception as e:
                logging.info("Exception in contract_type: {}".format(type(e).__name__))
                pass
        
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
    # Onsite Field -Procurement Category, Title
    # Onsite Comment -None

    try:
        notice_data.contract_type_actual = tender_html_element.find_element(By.CSS_SELECTOR, '#resultTable td:nth-child(3)').text
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, 'div > div:nth-child(2)'):
            attachments_data = attachments()
            attachments_data.file_name = 'Documents'
            # Onsite Field -None
            # Onsite Comment -ref_url : "https://www.egp.gov.bt/resources/common/ViewNotice.jsp?id=16842&h=t"
            
            external_url = page_details.find_element(By.CSS_SELECTOR, 'div > div:nth-child(2) > input').click()
            file_dwn = Doc_Download.file_download()
            attachments_data.external_url = str(file_dwn[0])
            
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -Information for Bidder/Consultant :
# Onsite Comment -ref_url : "https://www.egp.gov.bt/resources/common/ViewNotice.jsp?id=16907&h=t"

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#frmviewForm > table:nth-child(6)'):
            tender_criteria_data = tender_criteria()
        # Onsite Field -Information for Bidder/Consultant : >> Weightage For Technical Evaluation (%) :
        # Onsite Comment -ref_url : "https://www.egp.gov.bt/resources/common/ViewNotice.jsp?id=16907&h=t"

            try:
                tender_criteria_data.tender_criteria_title = page_details.find_element(By.XPATH, '//*[contains(text(),"Weightage For Technical Evaluation (%) :")]').text
            except Exception as e:
                logging.info("Exception in tender_criteria_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Information for Bidder/Consultant : >> Weightage For Technical Evaluation (%) :
        # Onsite Comment -ref_url : "https://www.egp.gov.bt/resources/common/ViewNotice.jsp?id=16907&h=t"

            try:
                tender_criteria_data.tender_criteria_weight = page_details.find_element(By.XPATH, '//*[contains(text(),"Weightage For Technical Evaluation (%) :")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in tender_criteria_weight: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Information for Bidder/Consultant : >>  Weightage For Financial Evaluation (%) :
        # Onsite Comment -ref_url : "https://www.egp.gov.bt/resources/common/ViewNotice.jsp?id=16907&h=t"

            try:
                tender_criteria_data.tender_criteria_title = page_details.find_element(By.XPATH, '//*[contains(text(),"Weightage For Financial Evaluation (%) :")]').text
            except Exception as e:
                logging.info("Exception in tender_criteria_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Information for Bidder/Consultant : >>  Weightage For Financial Evaluation (%) :
        # Onsite Comment -ref_url : "https://www.egp.gov.bt/resources/common/ViewNotice.jsp?id=16907&h=t"

            try:
                tender_criteria_data.tender_criteria_weight = page_details.find_element(By.XPATH, '//*[contains(text(),"Weightage For Financial Evaluation (%) :")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in tender_criteria_weight: {}".format(type(e).__name__))
                pass
        
            tender_criteria_data.tender_criteria_cleanup()
            notice_data.tender_criteria.append(tender_criteria_data)
    except Exception as e:
        logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
        pass
    
    # Onsite Field -Procurement Category, Title
    # Onsite Comment -if notice_number is not available in "Tender ID, Reference No, Public Status"  then pass notice_no from notice_url

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, '#resultTable td:nth-child(3) a').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Document Fees :
    # Onsite Comment -None

    try:
        notice_data.document_fee = page_details.find_element(By.XPATH, '//*[contains(text(),"Document Fees")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in document_fee: {}".format(type(e).__name__))
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
page_main = fn.init_chrome_driver(arguments) 
page_details = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.egp.gov.bt/resources/common/TenderListing.jsp?h=t"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,None):
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