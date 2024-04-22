from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "in_mumbaiport_spn"
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
from selenium.webdriver.support.ui import Select

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "in_mumbaiport_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    

    notice_data.script_name = 'in_mumbaiport_spn'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'INR'
    notice_data.main_language = 'EN'
    notice_data.procurement_method = 2
    notice_data.notice_type = 4
    
    notice_data.document_type_description = "Tenders"
    
    try:
        notice_deadline =  tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(5)').text
        notice_data.notice_deadline = datetime.strptime(notice_deadline, '%d.%m.%Y upto %H:%M hrs.').strftime('%Y/%m/%d %H:%M:%S')
    except:
        pass
    if notice_data.notice_deadline ==None:
        return
    if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
        return
    try:
        notice_url = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(6) a').get_attribute('href').split('id=')[1].split("%")[0]
        notice_data.notice_url = 'https://mumbaiport.gov.in/tenderdetail.asp?tenderid='+str(notice_url)+''
        fn.load_page(page_details,notice_data.notice_url,80)
    except:
        pass
    
    try: 
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(2)').text
    except:
        pass

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    try:
        document_purchase_start_time = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text.split('to')[0].split('From')[1].strip()
        notice_data.document_purchase_start_time = datetime.strptime(document_purchase_start_time,'%d.%m.%Y').strftime('%Y/%m/%d')
    except:
        pass
    try:
        document_purchase_end_time = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text.split('to')[1].strip()
        notice_data.document_purchase_end_time = datetime.strptime(document_purchase_end_time,'%d.%m.%Y').strftime('%Y/%m/%d')
    except:
        pass
    try:
        document_opening_time = page_details.find_element(By.XPATH,'//*[contains(text(),"Due Date and Time of opening of Tender document")]//following::td[1]').text.split('at')[0].strip()
        notice_data.document_opening_time = datetime.strptime(document_opening_time,'%d.%m.%Y').strftime('%Y-%m-%d')
    except:
        pass

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = "Mumbai Port Authority"
        customer_details_data.org_parent_id = "7777783"
        try:
            customer_details_data.org_address =page_details.find_element(By.XPATH,'//*[contains(text(),"Department")]//following::td[1]').text
        except:
            pass
        customer_details_data.org_country = 'IN'
        customer_details_data.org_language = 'EN'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    try:
        for single_record in page_details.find_elements(By.XPATH,'//*[contains(text(),"Tender Details")]//following::td[1]/p/a'):
            attachments_data = attachments()
            attachments_data.file_name = single_record.text
            attachments_data.external_url = single_record.get_attribute('href')
            try:
                attachments_data.file_type = attachments_data.external_url.split('.')[-1]
            except:
                pass
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except:
        pass

    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR,'body > table:nth-child(3) > tbody').get_attribute('outerHTML')
    except:
        pass


    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.notice_deadline) + str(notice_data.local_title)
    logging.info(notice_data.identifier)
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
    urls = ["https://mumbaiport.gov.in/tender_n.asp"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        try:
            for page_no in range(2,10): 
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,' body > table > tbody > tr:nth-child(2) > td > table > tbody > tr:nth-child(4) > td:nth-child(2) > table:nth-child(2) > tbody > tr:nth-child(n)'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'body > table > tbody > tr:nth-child(2) > td > table > tbody > tr:nth-child(4) > td:nth-child(2) > table:nth-child(2) > tbody > tr:nth-child(n)')))
                length = len(rows)                                                                              
                for records in range(2,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'body > table > tbody > tr:nth-child(2) > td > table > tbody > tr:nth-child(4) > td:nth-child(2) > table:nth-child(2) > tbody > tr:nth-child(n)')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break

                    if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                        logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                        break
                if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
                    break

                try:   
                    next_page = WebDriverWait(page_main, 10).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    page_check2 = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,' body > table > tbody > tr:nth-child(2) > td > table > tbody > tr:nth-child(4) > td:nth-child(2) > table:nth-child(2) > tbody > tr:nth-child(n)'))).text
                    WebDriverWait(page_main, 10).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'body > table > tbody > tr:nth-child(2) > td > table > tbody > tr:nth-child(4) > td:nth-child(2) > table:nth-child(2) > tbody > tr:nth-child(n)'),page_check2))
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