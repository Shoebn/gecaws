from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "in_cewacor_spn"
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

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "in_cewacor_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'in_cewacor_spn'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)
   
    notice_data.currency = 'INR'
    
    notice_data.main_language = 'EN'

    notice_data.procurement_method = 2
    
    notice_data.notice_type = 4
    
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Details
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Date >> Closing
    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(6)").text
        notice_deadline = re.findall('\d+-\d+-\d{4} \d+:\d+:\d+ \w+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d-%m-%Y %I:%M:%S %p').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(7) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#basicForm > div > div.panel.panel-primary > div.panel-body').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    try:
        publish_date = page_details.find_element(By.XPATH,'''//*[contains(text(),"Publishing Date")]//following::div[1]''').text
        publish_date = re.findall('\d+/\d+/\d{4} \d+:\d+:\d+ \w+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%m/%d/%Y %I:%M:%S %p').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    try:
        for contract in page_details.find_elements(By.XPATH, '//*[contains(text(),"Tender Category")]//following::div[1]/select/option'):
            contract_type_actual = contract.get_attribute('innerHTML')
            if 'selected' in contract_type_actual:
                notice_data.contract_type_actual = contract.find_element(By.CSS_SELECTOR,'option').text
                if 'Goods' in notice_data.contract_type_actual:
                    notice_data.notice_contract_type = 'Supply'
                if 'Works' in notice_data.contract_type_actual:
                    notice_data.notice_contract_type = 'Works'
                if 'Services' in notice_data.contract_type_actual:
                    notice_data.notice_contract_type = 'Service'
                else:
                    pass
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH,'''//*[contains(text(),'Work/Item Title ')]//following::div[1]''').text
        notice_data.notice_summary_english = notice_data.local_description
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    try:
        est_amount = WebDriverWait(page_details, 50).until(EC.presence_of_element_located((By.XPATH,'''(//*[contains(text(),'Tender Value ')]//following::div[3])[1]'''))).text
        est_amount = float(est_amount)
        notice_data.est_amount = est_amount
        notice_data.grossbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    try:
        for contract_days in page_details.find_elements(By.XPATH, '''//*[contains(text(),'Bid Validity Days')]//following::div[1]/select/option'''):
            contract_duration = contract_days.get_attribute('innerHTML')
            if 'selected' in contract_duration:
                notice_data.contract_duration = contract_days.find_element(By.CSS_SELECTOR,'option').text
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.document_cost = page_details.find_element(By.XPATH, '''(//*[contains(text(),'Tender Fee ')]//following::div[1])[1]''').text 
    except Exception as e:
        logging.info("Exception in document_cost: {}".format(type(e).__name__))
        pass
    
    try:
        document_opening_time = page_details.find_element(By.XPATH,'''//*[contains(text(),"Bid Opening Date ")]//following::div[1]''').text
        document_opening_time = re.findall('\d+/\d+/\d{4}',document_opening_time)[0]
        notice_data.document_opening_time = datetime.strptime(document_opening_time,'%m/%d/%Y').strftime('%Y-%m-%d')
    except Exception as e:
        logging.info("Exception in document_opening_time: {}".format(type(e).__name__))
        pass
    
    try:
        pre_bid_meeting_date = page_details.find_element(By.XPATH,'''//*[contains(text(),"PreBid Meeting Date")]//following::div[1]''').text
        pre_bid_meeting_date = re.findall('\d+/\d+/\d{4}',pre_bid_meeting_date)[0]
        notice_data.pre_bid_meeting_date = datetime.strptime(pre_bid_meeting_date,'%m/%d/%Y').strftime('%Y/%m/%d')
    except Exception as e:
        logging.info("Exception in pre_bid_meeting_date: {}".format(type(e).__name__))
        pass
    
    try:
        document_purchase_start_time = page_details.find_element(By.XPATH,'''//*[contains(text(),"Document Download / Sale Start Date")]//following::div[1]''').text
        document_purchase_start_time = re.findall('\d+/\d+/\d{4}',document_purchase_start_time)[0]
        notice_data.document_purchase_start_time = datetime.strptime(document_purchase_start_time,'%m/%d/%Y').strftime('%Y/%m/%d')
    except Exception as e:
        logging.info("Exception in document_purchase_start_time: {}".format(type(e).__name__))
        pass
    
    try:
        for description in page_details.find_elements(By.XPATH, '''//*[contains(text(),"Tender Type ")]//following::div[1]/select/option'''):
            document_type_description = description.get_attribute('outerHTML')
            if 'selected' in document_type_description:
                notice_data.document_type_description = description.get_attribute('innerHTML')
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = "Central Warehousing Corporation"

        try:
            customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Inviting Officer Address")]//following::div[1]').text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass

        try:
            for state in page_details.find_elements(By.XPATH, '//*[contains(text(),"State")]//following::div[1]/select/option'):
                org_state = state.get_attribute('outerHTML')
                if 'selected' in org_state:
                    customer_details_data.org_state = state.get_attribute('innerHTML')
        except Exception as e:
            logging.info("Exception in org_state: {}".format(type(e).__name__))
            pass

        try:
            customer_details_data.postal_code = page_details.find_element(By.XPATH, '(//*[contains(text(),"Pincode")]//following::div[1])[1]').text
        except Exception as e:
            logging.info("Exception in postal_code: {}".format(type(e).__name__))
            pass
        
        try:
            customer_details_data.contact_person = page_details.find_element(By.XPATH, '(//*[contains(text(),"Inviting Officer ")]//following::div[1])[1]').text
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass

        customer_details_data.org_country = 'IN'
        customer_details_data.org_language = 'EN'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:
        for single_record in WebDriverWait(page_details, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#detailsTable > tbody > tr:nth-child(2)')))[1:]:
                attachments_data = attachments()
                file_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
                if 'NIT' in file_name:
                    attachments_data.file_name = 'NIT Document'
                else:
                    attachments_data.file_name = 'Work/Item Documents'
                    
                attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, ' td:nth-child(4) > h4 > a').get_attribute('href')
                try:
                    attachments_data.file_type = attachments_data.external_url.split('.')[-1].strip()
                except Exception as e:
                    logging.info("Exception in file_type: {}".format(type(e).__name__))
                    pass

                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass

    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
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
    urls = ["https://cewacor.nic.in/Home/TenderList"] 
    for url in urls:
        fn.load_page(page_main, url, 80)
        logging.info('----------------------------------')
        logging.info(url)
        
        for scroll in  range(1,4):
            scroll = page_main.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)

        try:
            page_check = WebDriverWait(page_main, 120).until(EC.presence_of_element_located((By.XPATH,'//*[@id="datatablelist"]/tbody/tr'))).text
            rows = WebDriverWait(page_main, 120).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="datatablelist"]/tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 200).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="datatablelist"]/tbody/tr')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
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
