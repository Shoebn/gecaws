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
SCRIPT_NAME = "us_msgov_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
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
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.script_name = 'us_msgov_spn'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'EN'
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'US'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_type = 4
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'USD'
    
    # Onsite Field -RFx Number
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'tbody > tr > td:nth-child(3)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Smart Number
    # Onsite Comment -if  notice_no is not available in "RFx Number" field then take notice_no from "Smart Number"

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'tbody > tr > td:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -RFx Number
    # Onsite Comment -if notice_no is not available "RFx Number" or "Smart Number" then take from notice_url

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'tbody > tr > td:nth-child(3) a').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass


    # Onsite Field -None
    # Onsite Comment -along with notice text (page detail) also take data from tender_html_element (main page) ---- give td / tbody of main pg ( "/html/body/div[4]/section/div[2]/div/div/div/div/table/tbody/tr" )
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#body > section > div').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')


    
      # Onsite Field -Advertised Date
    # Onsite Comment -None

    try:
        publish_date = page_details.find_element(By.XPATH, "//*[contains(text(),"Advertised Date")]//following::td[1]").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Submission Date
    # Onsite Comment -None

    try:
        notice_deadline = page_details.find_element(By.XPATH, "//*[contains(text(),"Submission Date")]//following::td[1]").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass


    
    # Onsite Field -RFx Number
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'tbody > tr > td:nth-child(3) a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -RFx Type
    # Onsite Comment -None

    try:
        notice_data.document_type_description = page_details.find_element(By.XPATH, '//*[contains(text(),"RFx Type")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -RFx Opening Date
    # Onsite Comment -None

    try:
        notice_data.document_opening_time = page_details.find_element(By.XPATH, '//*[contains(text(),"RFx Opening Date")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in document_opening_time: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Major Procurement Category
    # Onsite Comment -None

    try:
        notice_data.category = page_details.find_element(By.XPATH, '//*[contains(text(),"Major Procurement Category")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in category: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -RFx Description
    # Onsite Comment -None

    try:
        notice_data.local_title = page_details.find_element(By.XPATH, '//*[contains(text(),"RFx Description")]//following::td[1]').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
# Onsite Field -Agency
# Onsite Comment -None

    try:              
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, 'tbody  td.sorting_1'):
            customer_details_data = customer_details()
        # Onsite Field -Agency
        # Onsite Comment -None

            try:
                customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'tbody  td.sorting_1').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
            customer_details_data.org_country = 'US'
            customer_details_data.org_language = 'EN'
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
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div > div:nth-child(15)'):
            attachments_data = attachments()
        # Onsite Field -Bid Attachments
        # Onsite Comment -take only data as a textual value

            try:
                attachments_data.file_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Attachments")]//following::td[1]//span//a').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Bid Attachments
        # Onsite Comment -None

            attachments_data.external_url = page_details.find_element(By.XPATH, '//*[contains(text(),"Attachments")]//following::td[1]//span//a').get_attribute('href')
            
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title) 
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
    urls = ["https://www.ms.gov/dfa/contract_bid_search/Bid?autoloadGrid=False"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,3):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[4]/section/div[2]/div/div/div/div/table/tbody/tr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[4]/section/div[2]/div/div/div/div/table/tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[4]/section/div[2]/div/div/div/div/table/tbody/tr')))[records]
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/div[4]/section/div[2]/div/div/div/div/table/tbody/tr'),page_check))
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