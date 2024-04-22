
from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "in_kmrl_spn"
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
SCRIPT_NAME = "in_kmrl_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    notice_data.script_name = 'in_kmrl_spn'
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)
    notice_data.currency = 'INR'
    notice_data.main_language = 'EN'
    notice_data.procurement_method = 2
    notice_data.notice_type = 4

    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass           
    
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass           
    
    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(7)').text  
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass             

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text
        notice_data.publish_date = datetime.strptime(publish_date,'%d-%b-%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass    
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return 
    
    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(10)").text
        notice_deadline = re.findall('\d+-\w+-\d+ \d+:\d+ [apAP][mM]', notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline, '%d-%b-%Y  %I:%M %p').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)    
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass            
    
    try:
        notice_data.contract_type_actual = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(8)").text

        if 'WORK' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Works'
        elif 'SERVICE' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Service'
        elif 'STORE' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Supply'
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass     
    
    notice_data.notice_text += tender_html_element.get_attribute('outerHTML')     
    notice_data.notice_url = 'https://kochimetro.org/tenders/index.php?action=view_tenders&tab=0&ctab=0&sort_field=not_pub_date&sort_order=DESC&limit=50&page=1'  
    
    try:
        remarks_click = WebDriverWait(tender_html_element, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'td:nth-child(11) > button')))  
        page_main.execute_script("arguments[0].click();",remarks_click)
        logging.info("remarks_click")    
        time.sleep(5)
        notice_data.notice_text += tender_html_element_2.find_element(By.CSS_SELECTOR, "td > div > div > div > table > tbody").get_attribute('outerHTML')   
    except Exception as e:
        logging.info("Exception in remarks_click: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.contract_duration = tender_html_element_2.find_element(By.CSS_SELECTOR, "td > div > div > div > table > tbody > tr:nth-child(6) > td:nth-child(2)").text  
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass 
    
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = "KOCHI METRO RAIL LIMITED"
        customer_details_data.org_parent_id = 7250746
        customer_details_data.org_email = 'itadmin@kmrl.co.in'
        customer_details_data.org_phone = '+91-484-2846700, +91-484-2846770'
        customer_details_data.contact_person = tender_html_element_2.find_element(By.CSS_SELECTOR, "td > div > div > div > table > tbody > tr:nth-child(2) > td:nth-child(2)").text  
        customer_details_data.org_country = 'IN'
        customer_details_data.org_language = 'EN'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass        

    try:
        fees_click = WebDriverWait(tender_html_element_2, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'td > div > div > ul > li:nth-child(2) > a')))  
        page_main.execute_script("arguments[0].click();",fees_click)
        logging.info("fees_click")    
        time.sleep(5)    
        notice_data.notice_text += tender_html_element_2.find_element(By.CSS_SELECTOR, "td > div > div > div:nth-child(3) > table").get_attribute('outerHTML')   
    except Exception as e:
        logging.info("Exception in fees_click: {}".format(type(e).__name__)) 
        pass    
    
    try:
        notice_data.document_fee = tender_html_element_2.find_element(By.CSS_SELECTOR, "td > div > div > div:nth-child(3) > table > tbody > tr:nth-child(3) > td:nth-child(2)").text   
    except Exception as e:
        logging.info("Exception in document_fee: {}".format(type(e).__name__)) 
        pass   
    
    try:
        notice_data.earnest_money_deposit = tender_html_element_2.find_element(By.CSS_SELECTOR, "td > div > div > div:nth-child(3) > table > tbody > tr:nth-child(4) > td:nth-child(2)").text   
    except Exception as e:
        logging.info("Exception in earnest_money_deposit: {}".format(type(e).__name__)) 
        pass   
    
    try:
        Submission_click = WebDriverWait(tender_html_element_2, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'td > div > div > ul > li:nth-child(3) > a')))  
        page_main.execute_script("arguments[0].click();",Submission_click)
        logging.info("Submission_click")    
        time.sleep(5)      
    except Exception as e:
        logging.info("Exception in Submission_click: {}".format(type(e).__name__)) 
        pass     
    
    notice_data.notice_text += tender_html_element_2.find_element(By.CSS_SELECTOR, "td > div > div > div:nth-child(4) > table").get_attribute('outerHTML')    
    
    try:
        document_opening_time_text = tender_html_element_2.find_element(By.CSS_SELECTOR, "td > div > div > div:nth-child(4) > table > tbody > tr:nth-child(6)").text   
        if 'Opening Date/Time' in document_opening_time_text:
            document_opening_time = tender_html_element_2.find_element(By.CSS_SELECTOR, "td > div > div > div:nth-child(4) > table > tbody > tr:nth-child(6) > td:nth-child(2)").text   
        else:           
            document_opening_time = tender_html_element_2.find_element(By.CSS_SELECTOR, "td > div > div > div:nth-child(4) > table > tbody > tr:nth-child(7) > td:nth-child(2)").text   
        document_opening_time = re.findall('\d+-\w+-\d+', document_opening_time)[0] 
        notice_data.document_opening_time = datetime.strptime(document_opening_time,'%d-%b-%Y').strftime('%Y-%m-%d')
    except Exception as e:
        logging.info("Exception in document_opening_time: {}".format(type(e).__name__)) 
        pass  
    
    try:
        pre_bid_meeting_date_text = tender_html_element_2.find_element(By.CSS_SELECTOR, " td > div > div > div:nth-child(4) > table > tbody > tr:nth-child(1)").text   
        if 'Pre-bid Date' in pre_bid_meeting_date_text:
            pre_bid_meeting_date = tender_html_element_2.find_element(By.CSS_SELECTOR, " td > div > div > div:nth-child(4) > table > tbody > tr:nth-child(1) > td:nth-child(2)").text 
            pre_bid_meeting_date = re.findall('\d+-\w+-\d+', pre_bid_meeting_date)[0] 
            notice_data.pre_bid_meeting_date = datetime.strptime(pre_bid_meeting_date,'%d-%b-%Y').strftime('%Y/%m/%d')
    except Exception as e:
        logging.info("Exception in pre_bid_meeting_date: {}".format(type(e).__name__)) 
        pass  
        
    try:
        Tender_Documents_click = WebDriverWait(tender_html_element_2, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'td > div > div > ul > li:nth-child(4) > a')))  
        page_main.execute_script("arguments[0].click();",Tender_Documents_click)
        logging.info("Tender_Documents_click")    
        time.sleep(5)      
        notice_data.notice_text += tender_html_element_2.find_element(By.CSS_SELECTOR, "td > div > div > div:nth-child(5) > table").get_attribute('outerHTML')    
    except Exception as e:
        logging.info("Exception in pre_bid_meeting_date: {}".format(type(e).__name__)) 
        pass          
        
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
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
arguments= ['ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments) 

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://kochimetro.org/tenders/index.php?action=view_tenders&tab=0&ctab=0&sort_field=not_pub_date&sort_order=DESC&limit=50&page=1"]
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        time.sleep(5)
                
        try:
            for page_no in range(1,3):
                page_check = WebDriverWait(page_main, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#form_tender_search > table > tbody > tr:nth-child(1)'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#form_tender_search > table > tbody > tr')))
                length = len(rows)
                for records in range(2,length,2):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#form_tender_search > table > tbody > tr')))[records] 
                    tender_html_element_2 = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#form_tender_search > table > tbody > tr')))[records+1] 
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break

                        if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
                            break
                        if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                            logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                            break
                    if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
                        break

                try:   
                    next_page = WebDriverWait(page_main, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'td > div > ul > li:nth-child(3) > a')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    page_check2 = WebDriverWait(page_main, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#form_tender_search > table > tbody > tr:nth-child(1)'))).text  
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#form_tender_search > table > tbody > tr:nth-child(1)'),page_check))
                except Exception as e:
                    logging.info("Exception in next_page: {}".format(type(e).__name__))
                    logging.info("No next page")
                    break
        except Exception as e:
            logging.info('No new record')
            break
            
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)            
            
