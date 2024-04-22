from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "in_bsnl_spn"
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
SCRIPT_NAME = "in_bsnl_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'in_bsnl_spn'

    notice_data.main_language = 'EN'

    notice_data.currency = 'INR'

    notice_data.procurement_method = 2

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)

    notice_data.notice_type = 4
    
    # Onsite Field -Number
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(9)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Date of Issue
    # Onsite Comment -None
    
    
    # Onsite Field -Submission Date
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(7)").text
        notice_deadline = re.findall('\d+-\d+-\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d-%m-%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
        
    if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
        return
    # Onsite Field -Category
    # Onsite Comment -None

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Details
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(10) > span > a').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
     # Onsite Field -Open Date
    # Onsite Comment -None

    try:
        document_opening_time = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(8)').text
        document_opening_time = re.findall('\d+-\d+-\d{4}',document_opening_time)[0]
        notice_data.document_opening_time = datetime.strptime(document_opening_time,'%d-%m-%Y').strftime('%Y-%m-%d')
    except Exception as e:
        logging.info("Exception in document_opening_time: {}".format(type(e).__name__))
        pass
    
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = 'Bharat Sanchar Nigam Limited'
        customer_details_data.org_parent_id = '7809008'
    # Onsite Field -#table1  td:nth-child(2)
    # Onsite Comment -None

        try:
            customer_details_data.org_state = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        except Exception as e:
            logging.info("Exception in org_state: {}".format(type(e).__name__))
            pass

    # Onsite Field -merge "SSA/UNIT" and "Department" as address
    # Onsite Comment -None

        try:
            org_address1 = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
            org_address2 = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
            customer_details_data.org_address = org_address1+' '+org_address2
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass

        customer_details_data.org_country = 'IN'
        customer_details_data.org_language = 'EN'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass


    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(10) > span > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url

    try:
        notice_data.local_description = page_details.find_element(By.XPATH, "//*[contains(text(),'Date of Issue')]//following::span[2]").text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Date of Issue
    # Onsite Comment -None

    try:
        notice_data.notice_summary_english = notice_data.local_description
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -split data from " Estimated cost put to tender" till "Earnest Money"
    # Onsite Comment -None
#     
    try:
        est_amount1 = page_details.find_element(By.XPATH, "//*[contains(text(),'Date of Issue')]//following::span[2]").text
        est_amount = re.search(r'Estimated cost put to tender Rs. \d+', est_amount1).group()
        est_amount = re.sub("[^\d\.\,]","",est_amount)
        notice_data.est_amount = float(est_amount.strip())
        notice_data.grossbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass

    # Onsite Field -split data from "Earnest Money" till " Period of completion"
    # Onsite Comment -None

    try:
        earnest_money_deposit1 = page_details.find_element(By.XPATH, "//*[contains(text(),'Date of Issue')]//following::span[2]").text
        earnest_money_deposit = re.search(r'Earnest Money Rs \d+', earnest_money_deposit1).group()
        notice_data.earnest_money_deposit = earnest_money_deposit.split("Earnest Money Rs ")[1]
    except Exception as e:
        logging.info("Exception in earnest_money_deposit: {}".format(type(e).__name__))
        pass
    

    # Onsite Field -split data from "Period of completion" till " 6 Tender Fee"
    # Onsite Comment -None

    try:
        contract_duration = page_details.find_element(By.XPATH, "//*[contains(text(),'Date of Issue')]//following::span[2]").text
        notice_data.contract_duration = re.search(r'Period of completion One month \d+', contract_duration).group()
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -split data from "Tender Fee(Non-refundable)" till " 7 Date of publication:"
    # Onsite Comment -None

    try: 
        document_cost1 = page_details.find_element(By.XPATH, "//*[contains(text(),'Date of Issue')]//following::span[2]").text
        document_cost = re.search(r'Tender Fee\(Non-refundable\) Rs. \d+', document_cost1).group()
        document_cost = re.sub("[^\d\.\,]","",document_cost)
        notice_data.document_cost =float(document_cost.strip())
    except Exception as e:
        logging.info("Exception in document_cost: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#middle').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')


    try:              
        attachments_data = attachments()

        attachments_data.external_url = page_details.find_element(By.CSS_SELECTOR, 'td:nth-child(4) > span > a').get_attribute('href')

        attachments_data.file_name = page_details.find_element(By.CSS_SELECTOR, 'td:nth-child(4) > span > a').text

        try:
            attachments_data.file_type = attachments_data.external_url.split(".")[-1]
        except Exception as e:
            logging.info("Exception in file_type: {}".format(type(e).__name__))
            pass

        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass

    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_url) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title)
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
    urls = ["http://tender.bsnl.co.in/bsnltenders/bsnltender/tender_live_view_main.jsp"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(2,5):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="table1"]/tbody/tr[3]'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="table1"]/tbody/tr')))
                length = len(rows)
                for records in range(2,length-1):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="table1"]/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="table1"]/tbody/tr[3]'),page_check))
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
    
