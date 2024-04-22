from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "us_iowa_spn"
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
SCRIPT_NAME = "us_iowa_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
   
    notice_data.script_name = 'us_iowa_spn'
    
    notice_data.main_language = 'EN'
   
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'US'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'USD'
    
    notice_data.notice_type = 4
    
    notice_data.procurement_method = 2
    
    # Onsite Field -Bid Number
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Title
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Effective Date
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(6)").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%m/%d/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Expiration Date
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(7)").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%m/%d/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    try:              
        attachments_data = attachments()
        attachments_data.file_name = 'tender_document'

        attachments_data.external_url = tender_html_element.find_element(By.CSS_SELECTOR, ' td:nth-child(8) a').get_attribute('href')

        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass

        
    # Onsite Field -Bid Number
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, ' td:nth-child(2) a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
        
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#node-1781 > div').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    try:              
        customer_details_data = customer_details()
    # Onsite Field -Agency
    # Onsite Comment -None

        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        
        customer_details_data.org_language = 'EN'
        customer_details_data.org_country = 'US'
    # Onsite Field -Contact
    # Onsite Comment -None

        try:
            customer_details_data.contact_person = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass

    # Onsite Field -Address 1
    # Onsite Comment -if "Address 1" is blank then grab the address from "Address 2"

        try:
            customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Address 1")]//following::div[1]').text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass

    # Onsite Field -City/State/Zip
    # Onsite Comment -split only city for ex."Ames, IA 50010" , here grab only "Ames"

        try:
            customer_details_data.org_city = page_details.find_element(By.XPATH, '//*[contains(text(),"City/State/Zip")]//following::div[1]').text.split(",")[0].strip()
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass

    # Onsite Field -City/State/Zip
    # Onsite Comment -split only state for ex."Ames, IA 50010" , here grab only "IA"IA"

        try:
            org_state = page_details.find_element(By.XPATH, '//*[contains(text(),"City/State/Zip")]//following::div[1]').text.split(",")[1].strip()
            customer_details_data.org_state = org_state.split(" ")[0].strip()
        except Exception as e:
            logging.info("Exception in org_state: {}".format(type(e).__name__))
            pass

    # Onsite Field -City/State/Zip
    # Onsite Comment -split only city for ex."Ames, IA 50010" , here grab only "50010"

        try:
            postal_code = page_details.find_element(By.XPATH, '//*[contains(text(),"City/State/Zip")]//following::div[1]').text
            customer_details_data.postal_code =re.findall('\d{5}',postal_code)[0]
        except Exception as e:
            logging.info("Exception in postal_code: {}".format(type(e).__name__))
            pass

    # Onsite Field -Contact Phone Number
    # Onsite Comment -split the data after "Contact Phone Number"

        try:
            customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Contact Phone Number")]//following::div[1]').text
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass

    # Onsite Field -Contact Fax Number
    # Onsite Comment -split the data after "Contact Fax Number"

        try:
            customer_details_data.org_fax = page_details.find_element(By.XPATH, '//*[contains(text(),"Contact Fax Number")]//following::div[1]').text
        except Exception as e:
            logging.info("Exception in org_fax: {}".format(type(e).__name__))
            pass

    # Onsite Field -Contact Email
    # Onsite Comment -split the data after "Contact Email"

        try:
            customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Contact Email")]//following::div[1]').text
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    
    # Onsite Field -Bid Information >> Solicitation Type
    # Onsite Comment -Extract the data after the 'name' field.

    try:
        notice_data.document_type_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Solicitation Type")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '(//*[contains(text(),"Description")])[2]//following::div[1]').text
        notice_data.notice_summary_english = notice_data.local_description
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    
    # Onsite Field -Valid Dates >> From
    # Onsite Comment -split the data after "From"

    try:
        tender_contract_start_date = page_details.find_element(By.XPATH, '//*[contains(text(),"From")]//following::div[1]').text
        tender_contract_start_date = re.findall('\d+/\d+/\d{4} \d+:\d+:\d+ [apAP][mM]',tender_contract_start_date)[0]
        notice_data.tender_contract_start_date = datetime.strptime(tender_contract_start_date,'%m/%d/%Y %I:%M:%S %p').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in tender_contract_start_date: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Valid Dates >> Until
    # Onsite Comment -split the data after "Until"

    try:
        tender_contract_end_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Until")]//following::div[1]').text
        tender_contract_end_date = re.findall('\d+/\d+/\d{4} \d+:\d+:\d+ [apAP][mM]',tender_contract_end_date)[0]
        notice_data.tender_contract_end_date = datetime.strptime(tender_contract_end_date,'%m/%d/%Y %I:%M:%S %p').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in tender_contract_end_date: {}".format(type(e).__name__))
        pass
    
    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.col-md-8 > a'):
            attachments_data = attachments()
        # Onsite Field -Documents/Attachments
        # Onsite Comment -take only textual data

            attachments_data.file_name = single_record.text
        
        # Onsite Field -Documents/Attachments
        # Onsite Comment -None

            attachments_data.external_url = single_record.get_attribute('href')
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    # Onsite Field -None
    # Onsite Comment -ref_url : "https://bidopportunities.iowa.gov/Home/BidInfo?bidId=42d38166-ac85-4be1-862e-db75daae9ee0"
    # //*[@id="node-1781"]/div/div/div/div/div/div[8]/div/div[2]/div/div[2]/a
    try:
        notice_data.additional_tender_url = page_details.find_element(By.XPATH, '//*[contains(text(),"Links")]//following::a[1]').text
    except Exception as e:
        logging.info("Exception in additional_tender_url: {}".format(type(e).__name__))
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_url) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title)
    logging.info(notice_data.identifier)
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
    urls = ["https://bidopportunities.iowa.gov/"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,4):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="hostedBidsTbl"]/tbody/tr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="hostedBidsTbl"]/tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="hostedBidsTbl"]/tbody/tr')))[records]
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="hostedBidsTbl"]/tbody/tr'),page_check))
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
    