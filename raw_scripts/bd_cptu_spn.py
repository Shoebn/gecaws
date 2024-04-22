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
SCRIPT_NAME = "bd_cptu_spn"
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
    notice_data.script_name = 'bd_cptu_spn'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'EN'
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'BD'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'BDT'


#after opening the url insert date in both this field "div:nth-child(8) > div > div > div"  and then click on "Search".

    
    # Onsite Field -Title & Reference No.
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Issue Date
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Closing Date
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(5)").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Last Selling
    # Onsite Comment -None

    try:
        notice_data.document_purchase_start_time = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(6)').text
    except Exception as e:
        logging.info("Exception in document_purchase_start_time: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Title & Reference No.
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#bodyContent').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    # Onsite Field -None
    # Onsite Comment -1.if in this field written as "Request for Expressions of Interest " then take notice_type=5.Otherwise take it notice_type=4.

    try:
        notice_data.notice_type = page_details.find_element(By.CSS_SELECTOR, 'h5 > b:nth-child(1)').text
    except Exception as e:
        logging.info("Exception in notice_type: {}".format(type(e).__name__))
        pass
    





    # Onsite Field -KEY INFORMATION >> Procurement Method or KEY INFORMATION >> Procurement Sub-Method
    # Onsite Comment -1.in the given field written as "NCT" then take "procurement_method=0","ICT" then take "procurement_method=1" otherwise take "procurement_method=2"
    #ref_url:1)https://cptu.gov.bd/advertisement-goods/details-83109.html	2)https://cptu.gov.bd/advertisement-works/details-83116.html	3)https://cptu.gov.bd/advertisement-services/Civil-Estimator-(AutoCAD-Operator)---8348.html
    try:
        notice_data.procurement_method = page_details.find_element(By.XPATH, '//*[contains(text(),"KEY INFORMATION")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in procurement_method: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -EOI Ref. No.
    # Onsite Comment -None

    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"EOI Ref. No.")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Invitation Reference No
    # Onsite Comment -None

    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"Invitation Reference No")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Invitation For
    # Onsite Comment -1.replace folloeing keyword with given keyword("Goods=Supply","Works=Works","Services=Service")
    #ref_url:"https://cptu.gov.bd/advertisement-goods/details-83112.html"

    try:
        notice_data.notice_contract_type = page_details.find_element(By.XPATH, '//*[contains(text(),"Invitation For")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Invitation For
    # Onsite Comment -None

    try:
        notice_data.contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Invitation For")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Budget and Source of Funds :
    # Onsite Comment -None

    try:
        notice_data.source_of_funds = page_details.find_element(By.XPATH, '//*[contains(text(),"Budget and Source of Funds :")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in source_of_funds: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Project/Programme Name
    # Onsite Comment -None

    try:
        notice_data.project_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Project/Programme Name")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in project_name: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Tender Package No
    # Onsite Comment -None

    try:
        notice_data.related_tender_id = page_details.find_element(By.XPATH, '//*[contains(text(),"Tender Package No")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Tender Closing Date and Time
    # Onsite Comment -None
    #ref_url:"https://cptu.gov.bd/advertisement-goods/details-83112.html"

    try:
        notice_data.document_purchase_end_time = page_details.find_element(By.XPATH, '//*[contains(text(),"Tender Closing Date and Time")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in document_purchase_end_time: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -EOI Closing Date and Time
    # Onsite Comment -None
    #ref_url:"https://cptu.gov.bd/advertisement-services/Innovation-and-Commecialization-Specialist--8349.html"

    try:
        notice_data.document_purchase_end_time = page_details.find_element(By.XPATH, '//*[contains(text(),"EOI Closing Date and Time")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in document_purchase_end_time: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Tender Opening Date and Time
    # Onsite Comment -None

    try:
        notice_data.document_opening_time = page_details.find_element(By.XPATH, '//*[contains(text(),"Tender Opening Date and Time")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in document_opening_time: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Place/Date/Time of Tender Meeting (Optional):
    # Onsite Comment -1.split between "Date" and "Time".

    try:
        notice_data.pre_bid_meeting_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Place/Date/Time of Tender Meeting (Optional)")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in pre_bid_meeting_date: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Place/Date/Time of Tender Meeting (Optional):
    # Onsite Comment -1.split between "Date" and "Time".
    #ref_url:"https://cptu.gov.bd/advertisement-goods/details-83112.html"
    try:
        notice_data.eligibility = page_details.find_element(By.XPATH, '//*[contains(text(),"Eligibility of Tenderer ")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in eligibility: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Experience, Resources and Delivery Capacity Required
    # Onsite Comment -None
    #ref_url:"https://cptu.gov.bd/advertisement-services/Innovation-and-Commecialization-Specialist--8349.html"

    try:
        notice_data.eligibility = page_details.find_element(By.XPATH, '//*[contains(text(),"Experience, Resources and Delivery Capacity Required")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in eligibility: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Brief Description")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Brief Description of Goods or Works :
    # Onsite Comment -None

    try:
        notice_data.notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),"Brief Description")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Tender Lot Information >> Security Amount
    # Onsite Comment -None

    try:
        notice_data.earnest_money_deposit = page_details.find_element(By.CSS_SELECTOR, '#bodyContent tr:nth-child(32) > td > table > tbody > tr > td:nth-child(4)').text
    except Exception as e:
        logging.info("Exception in earnest_money_deposit: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -None
#ref_url:1)"https://cptu.gov.bd/advertisement-goods/details-83112.html"	2)"https://cptu.gov.bd/advertisement-services/Innovation-and-Commecialization-Specialist--8349.html".

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#bodyContent'):
            customer_details_data = customer_details()
            customer_details_data.org_country = 'BD'
            customer_details_data.org_language = 'EN'
        # Onsite Field -None
        # Onsite Comment -None

            try:
                customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Place
        # Onsite Comment -None

            try:
                customer_details_data.org_city = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(7)').text
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -1.add this both field in org_address "//*[contains(text(),"Ministry/Division")]//following::td[1]" and "//*[contains(text(),"Agency")]//following::td[1]".

            try:
                customer_details_data.org_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Ministry/Division")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in org_description: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Procuring Entity Code
        # Onsite Comment -None

            try:
                customer_details_data.type_of_authority_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Procuring Entity Code")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in type_of_authority_code: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Name of Official Inviting Tender :  or  Name of Official Inviting EOI
        # Onsite Comment -None

            try:
                customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"PROCURING ENTITY DETAILS")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Address of Official Inviting Tender :   or   Address of Official Inviting EOI
        # Onsite Comment -None

            try:
                customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"PROCURING ENTITY DETAILS")]//following::td[3]').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -1.split between "Phone" and "Fax".

            try:
                customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"PROCURING ENTITY DETAILS")]//following::td[4]').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -1.split between "Fax" and "Email"

            try:
                customer_details_data.org_fax = page_details.find_element(By.XPATH, '//*[contains(text(),"PROCURING ENTITY DETAILS")]//following::td[4]').text
            except Exception as e:
                logging.info("Exception in org_fax: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -1.split after "Email".

            try:
                customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"PROCURING ENTITY DETAILS")]//following::td[4]').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
        
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#bodyContent'):
            lot_details_data = lot_details()
        # Onsite Field -Invitation For
        # Onsite Comment -1.replace folloeing keyword with given keyword("Goods=Supply","Works=Works","Services=Service")

            try:
                lot_details_data.contract_type = page_details.find_element(By.XPATH, '//*[contains(text(),"Invitation For")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in contract_type: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Invitation For
        # Onsite Comment -None

            try:
                lot_details_data.lot_contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Invitation For")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in lot_contract_type_actual: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Tender Lot Information >> Lot No
        # Onsite Comment -None

            try:
                lot_details_data.lot_actual_number = page_details.find_element(By.CSS_SELECTOR, '#bodyContent tr:nth-child(32) > td > table > tbody > tr > td:nth-child(1)').text
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Tender Lot Information >> Identification
        # Onsite Comment -None

            try:
                lot_details_data.lot_title = page_details.find_element(By.CSS_SELECTOR, '#bodyContent tr:nth-child(32) > td > table > tbody > tr > td:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Tender Lot Information >> Completion Time in Weeks/Months
        # Onsite Comment -None

            try:
                lot_details_data.contract_duration = page_details.find_element(By.CSS_SELECTOR, '#bodyContent tr:nth-child(32) > td > table > tbody > tr > td:nth-child(5)').text
            except Exception as e:
                logging.info("Exception in contract_duration: {}".format(type(e).__name__))
                pass
        
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
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
    urls = ["https://cptu.gov.bd/advertisement-notices/notice-search.html"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,3):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/section[2]/section/div/div/div[2]/form/div[10]/table/tbody/tr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/section[2]/section/div/div/div[2]/form/div[10]/table/tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/section[2]/section/div/div/div[2]/form/div[10]/table/tbody/tr')))[records]
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/section[2]/section/div/div/div[2]/form/div[10]/table/tbody/tr'),page_check))
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