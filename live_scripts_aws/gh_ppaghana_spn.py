from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "gh_ppaghana_spn"
log_config.log(SCRIPT_NAME)
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
SCRIPT_NAME = "gh_ppaghana_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'gh_ppaghana_spn'

    notice_data.main_language = 'EN'

    notice_data.notice_type = 4
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'GH'
    notice_data.performance_country.append(performance_country_data)
    
 
    # Onsite Field -Tender Type:
    # Onsite Comment -if NCT then  = procurment method : 0 ,  if ICT then  =  procurment method : 1 )

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.list-title > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
        
    try:
        procurement_method = page_details.find_element(By.CSS_SELECTOR, 'div.col-md-9  dl:nth-child(2) > dd').text
        if 'NCT' in procurement_method:
            notice_data.procurement_method = 0
        elif 'ICT' in procurement_method:
            notice_data.procurement_method = 1
        else:
            pass
    except Exception as e:
        logging.info("Exception in procurement_method: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -split the left side date as a publish_date

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div.list-date").text
        publish_date = re.findall('\d+th \w+, \d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%dth %B, %Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Deadline :
    # Onsite Comment -split the right side date as a notice_deadline

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "div.list-date").text.split('Deadline :')[1].strip()
        notice_deadline = re.findall('\d+th \w+, \d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%dth %B, %Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    notice_data.document_type_description = 'Open Tenders'
    
    try:
        currency = page_details.find_element(By.XPATH, "//*[contains(text(),'Currency:')]//following::dd[1]").text
        notice_data.currency = fn.procedure_mapping("assets/gh_ppaghana_spn_currency.csv",currency)
    except:
        pass
    
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.col-md-9').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    # Onsite Field -Tender Name:
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.list-title > a').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Package No:
    # Onsite Comment -None

    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"Package No:")]//following::dd[1]').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -if notice_no is not available in "Package No:" field then pass notice_no from notice_url


    # Onsite Field -Price of Tender Document:
    # Onsite Comment -None
    
    try:
        notice_data.document_fee = page_details.find_element(By.XPATH, '//*[contains(text(),"Price of Tender Document:")]//following::dd[1]').text
    except Exception as e:
        logging.info("Exception in document_fee: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.document_cost = page_details.find_element(By.XPATH, '//*[contains(text(),"Price of Tender Document:")]//following::dd[1]').text
    except Exception as e:
        logging.info("Exception in document_cost: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Tender Description:")]//following::dd[1]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Tender Description:
    # Onsite Comment -None

    try:
        notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),"Tender Description:")]//following::dd[1]').text
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_summary_english)
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Source of Funds:
    # Onsite Comment -if provided CSV has contains funding agency same as site then take , otherwise it take as a None

    try:
        funding_agencies_data = funding_agencies()
        funding_agency = page_details.find_element(By.XPATH, '//*[contains(text(),"Source of Funds:")]//following::dd[1]').text
        funding_agencies_data.funding_agency = fn.procedure_mapping("assets/gh_ppaghana_spn_fundingagencycode.csv",funding_agency)
    except Exception as e:
        logging.info("Exception in source_of_funds: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_language = 'EN'
        customer_details_data.org_country = 'GH'
    # Onsite Field -Agency:
    # Onsite Comment -split the data after "Agency:"

        customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Agency:")]//following::dd[1]').text
        
        try:
            contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Contact Person:")]//following::dd[1]').text
            if 'P.O' in contact_person:
                customer_details_data.contact_person = contact_person.split('P.O')[0].strip()
                customer_details_data.org_address = contact_person.split('P.O')[1].strip()
            else:
                customer_details_data.contact_person = contact_person
        except Exception as e:
            logging.info("Exception in org_name: {}".format(type(e).__name__))
            pass

    # Onsite Field -Contact Person:
    # Onsite Comment -split the data after "Contact Person:" , ref_url : "https://tenders.ppa.gov.gh/tenders/30161"


    # Onsite Field -Email:
    # Onsite Comment -split the data after "Email:" , ref_url : "https://tenders.ppa.gov.gh/tenders/30161"

        try:
            customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Email:")]//following::dd[1]').text
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass

    # Onsite Field -Telphone:
    # Onsite Comment -split the data after "Telphone:" , ref_url : "https://tenders.ppa.gov.gh/tenders/30161"

        try:
            customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Telphone:")]//following::dd[1]').text
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass

    # Onsite Field -Fax:
    # Onsite Comment -split the data after "Fax::" , ref_url : "https://tenders.ppa.gov.gh/tenders/30161"

        try:
            customer_details_data.org_fax = page_details.find_element(By.XPATH, '//*[contains(text(),"Fax:")]//following::dd[1]').text
        except Exception as e:
            logging.info("Exception in org_fax: {}".format(type(e).__name__))
            pass

    # Onsite Field -Website:
    # Onsite Comment -split the data after "Website::" , ref_url : "https://tenders.ppa.gov.gh/tenders/30160"

        try:
            customer_details_data.org_website = page_details.find_element(By.XPATH, '//*[contains(text(),"Website:")]//following::dd[1]').text
        except Exception as e:
            logging.info("Exception in org_website: {}".format(type(e).__name__))
            pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -Tender Description:
# Onsite Comment -ref_url : "https://tenders.ppa.gov.gh/tenders/30193"

    try: 
        lot_number = 1
        lots_details = page_details.find_element(By.XPATH, '//*[contains(text(),"Tender Description:")]//following::dd[1]').text
        if 'Lot' in lots_details:
            for single_record in lots_details.split('Lot')[1:]:
                
                try:
                    actual_number = single_record.split(':')[0].strip()
                    lot_actual_number = re.findall('\d+',actual_number)[0]
                except Exception as e:
                    logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                    pass
                
                lots_info = single_record.rstrip( ).split('\n')[1:]
                for lots in lots_info:
                    lot_details_data = lot_details()
                    lot_details_data.lot_number = lot_number
        # Onsite Field -Tender Description:
        # Onsite Comment -split the lot_actual_number for ex."Lot 1:" , "Lot 2:"

#         # Onsite Field -Tender Description:
#         # Onsite Comment -split only lot_title  for ex. "a. Laptop computers - qty 25 sets" , here take only "Laptop computers"
                    try:    
                        lot_details_data.lot_actual_number = 'Lot'+ '' +lot_actual_number
                    except:
                        pass
                    
                    lot_details_data.lot_title = lots.split('-')[0].strip()                
#         # Onsite Field -Tender Description:
#         # Onsite Comment -split only lot_quantity  for ex. "a. Laptop computers - qty 25 sets" , here take only "qty 25 sets"

                    try:
                        lot_quantity = lots.split('-')[1].strip()
                        lot_details_data.lot_quantity = float(re.findall('\d+',lot_quantity)[0])
                    except Exception as e:
                        logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                        pass
        
                    lot_number += 1
                    lot_details_data.lot_details_cleanup()
                    notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments) 
page_details = fn.init_chrome_driver(arguments) 
page_main = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["http://tenders.ppa.gov.gh/tenders"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(2,5):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[1]/section[2]/div/div/div/div/div[2]/div/div'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/section[2]/div/div/div/div/div[2]/div/div')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/section[2]/div/div/div/div/div[2]/div/div')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
        
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/div[1]/section[2]/div/div/div/div/div[2]/div/div'),page_check))
                except Exception as e:
                    logging.info("Exception in next_page: {}".format(type(e).__name__))
                    logging.info("No next page")
                    break
        except:
            logging.info('No new record')
            break
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit() 
    
    output_json_file.copyFinalJSONToServer(output_json_folder)
