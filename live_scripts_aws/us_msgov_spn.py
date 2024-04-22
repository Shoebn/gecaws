from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "us_msgov_spn"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from selenium import webdriver
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "us_msgov_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"

# ------------------------------------------------------------------------------------------------------------------------------------------------
# Visit the URL 'https://www.ms.gov/dfa/contract_bid_search/Bid?autoloadGrid=False', 
# click on 'ADVANCED SEARCH OPTIONS,' choose 'Open' from the 'STATUS' drop-down menu, and then click the 'SEARCH' button
# ---------------------------------------------------------------------------------------------------------------------------------------------

def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'us_msgov_spn'
    
    notice_data.main_language = 'EN'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'US'
    notice_data.performance_country.append(performance_country_data)
   
    notice_data.notice_type = 4
    
    notice_data.procurement_method = 2
  
    notice_data.currency = 'USD'
    
    # Onsite Field -RFx Number
    
    # Onsite Field -Smart Number
    # Onsite Comment -if  notice_no is not available in "RFx Number" field then take notice_no from "Smart Number"
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        if notice_data.notice_no == None:
            notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    try:
        org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
    except:
        pass
    
    # Onsite Field -RFx Number  
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3) a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
        
        # Onsite Field -RFx Number https://www.ms.gov/dfa/contract_bid_search/Bid/Details/34773?AppId=1&Status=Open
        # Onsite Comment -if notice_no is not available "RFx Number" or "Smart Number" then take from notice_url
        try:
            if notice_data.notice_no == None:
                notice_data.notice_no = notice_data.notice_url.split('Details/')[1].split('?AppId')[0].strip()
        except Exception as e:
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass
        
        # Onsite Comment -along with notice text (page detail) also take data from tender_html_element (main page) ---- give td / tbody of main pg ( "/html/body/div[4]/section/div[2]/div/div/div/div/table/tbody/tr" )
        try:
            notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#body > section > div').get_attribute("outerHTML")                     
        except:
            notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
            
        # Onsite Field -Advertised Date  01/30/2024 8:00 AM
        try:
            publish_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Advertised Date")]//following::td[1]').text
            publish_date = re.findall('\d+/\d+/\d{4} \d+:\d+ [AMPMampm]+',publish_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date,'%m/%d/%Y %I:%M %p').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.publish_date)
        except Exception as e:
            logging.info("Exception in publish_date: {}".format(type(e).__name__))
            pass
        if notice_data.publish_date is not None and notice_data.publish_date < threshold:
            return
        
        # Onsite Field -Submission Date
        try:
            notice_deadline = page_details.find_element(By.XPATH, '//*[contains(text(),"Submission Date")]//following::td[1]').text
            notice_deadline = re.findall('\d+/\d+/\d{4} \d+:\d+ [AMPMampm]+',notice_deadline)[0]
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%m/%d/%Y %I:%M %p').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.notice_deadline)
        except Exception as e:
            logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -RFx Type
        try:
            notice_data.document_type_description = page_details.find_element(By.XPATH, '//*[contains(text(),"RFx Type")]//following::td[1]').text
        except Exception as e:
            logging.info("Exception in document_type_description: {}".format(type(e).__name__))
            pass
        
         # Onsite Field -RFx Opening Date
        try:
            document_opening_time = page_details.find_element(By.XPATH, '//*[contains(text(),"RFx Opening Date")]//following::td[1]').text
            document_opening_time = re.findall('\d+/\d+/\d{4}',document_opening_time)[0]
            notice_data.document_opening_time = datetime.strptime(document_opening_time,'%m/%d/%Y').strftime('%Y-%m-%d')
        except Exception as e:
            logging.info("Exception in document_opening_time: {}".format(type(e).__name__))
            pass

        # Onsite Field -Major Procurement Category
        try:
            notice_data.category = page_details.find_element(By.XPATH, '//*[contains(text(),"Major Procurement Category")]//following::td[1]').text
        except Exception as e:
            logging.info("Exception in category: {}".format(type(e).__name__))
            pass

        # Onsite Field -RFx Description
        try:
            notice_data.local_title = page_details.find_element(By.XPATH, '//*[contains(text(),"RFx Description")]//following::td[1]').text
            notice_data.notice_title = notice_data.local_title
        except Exception as e:
            logging.info("Exception in local_title: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Agency
        try:              
            customer_details_data = customer_details()
            customer_details_data.org_country = 'US'
            customer_details_data.org_language = 'EN'
            customer_details_data.org_name = org_name

            # Onsite Field -Contact Information >> Name
            # Onsite Comment -ref_url : "https://www.ms.gov/dfa/contract_bid_search/Bid/Details/34776?AppId=1&Status=Open"
            try:
                customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Name")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass

            # Onsite Field -Contact Information >> Email
            # Onsite Comment -ref_url : "https://www.ms.gov/dfa/contract_bid_search/Bid/Details/34776?AppId=1&Status=Open"
            try:
                customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Email")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass

            # Onsite Field -Contact Information >> Phone
            # Onsite Comment -ref_url : "https://www.ms.gov/dfa/contract_bid_search/Bid/Details/34776?AppId=1&Status=Open"
            try:
                customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Phone")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass

        # Onsite Field -Contact Information >> Fax
        # Onsite Comment -ref_url : "https://www.ms.gov/dfa/contract_bid_search/Bid/Details/34776?AppId=1&Status=Open"

            try:
                customer_details_data.org_fax = page_details.find_element(By.XPATH, '//*[contains(text(),"Fax")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in org_fax: {}".format(type(e).__name__))
                pass

            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
        except Exception as e:
            logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
            pass
        
        # Onsite Field -Bid Attachments
        # Onsite Comment -ref_url : "https://www.ms.gov/dfa/contract_bid_search/Bid/Details/34671?AppId=1&Status=Open"
        try:              
            for single_record in page_details.find_elements(By.XPATH, '//*[contains(text(),"Attachments")]//following::td//span//a'):
                attachments_data = attachments()

                # Onsite Field -Bid Attachments
                # Onsite Comment -take only data as a textual value
                attachments_data.file_name = single_record.text

                # Onsite Field -Bid Attachments
                attachments_data.external_url = single_record.get_attribute('href')

                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
        except Exception as e:
            logging.info("Exception in attachments: {}".format(type(e).__name__)) 
            pass
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
options = Options()
for argument in arguments:
    options.add_argument(argument)
page_main = webdriver.Chrome(options=options)
page_details = webdriver.Chrome(options=options)

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.ms.gov/dfa/contract_bid_search/Bid?autoloadGrid=False"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        Advanced_Search_Options_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="advanceSearchToggle"]')))
        page_main.execute_script("arguments[0].click();",Advanced_Search_Options_click)
        time.sleep(3)
        
        Status_click = Select(page_main.find_element(By.XPATH,'//*[@id="Status"]'))
        Status_click.select_by_index(1)
        
        time.sleep(5)
        search_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="btnSubmit"]')))
        page_main.execute_script("arguments[0].click();",search_click)
        time.sleep(30)
        
        
        rows = WebDriverWait(page_main, 180).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[4]/section/div[2]/div/div/div/div/table/tbody/tr')))
        length = len(rows)
        for records in range(1,length):
            tender_html_element = WebDriverWait(page_main, 180).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[4]/section/div[2]/div/div/div/div/table/tbody/tr')))[records]
            extract_and_save_notice(tender_html_element)
            if notice_count >= MAX_NOTICES:
                break

            if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                break

    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit() 
    
    output_json_file.copyFinalJSONToServer(output_json_folder)
