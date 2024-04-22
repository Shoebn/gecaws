from gec_common.gecclass import *
import logging
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
from deep_translator import GoogleTranslator
from selenium.webdriver.support.ui import Select

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
tender_no = 0
SCRIPT_NAME = "in_nbri_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    global tender_no
    notice_data = tender()
    
    notice_data.script_name = 'in_nbri_spn'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)
   
    notice_data.currency = 'INR'
    
    notice_data.main_language = 'EN'
    
    notice_data.notice_type = 4
    
    notice_data.procurement_method = 2

    notice_data.notice_url = url

    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text.split('(Tender')[0].strip()
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:  
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text.split('Tender ID:')[1].split(")")[0].strip()
    except:
        try:
            notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text.split('Tender ID :')[1].split(")")[0].strip()
        except:
            try:
                notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text.split('Tender Id :')[1].split(")")[0].strip()
            except Exception as e:
                logging.info("Exception in notice_no: {}".format(type(e).__name__))
                pass

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        publish_date = re.findall('\d{4}-\d+-\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%Y-%m-%d').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try: 
        due_date = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(4)').text
        deadline = re.findall('\d+-\d+-\d{4}',due_date)[0]
        due_time = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(5)').text
        deadline_time = re.findall('\d+:\d+ \w+',due_time)[0]
        notice_deadline = deadline + ' '+ deadline_time
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d-%m-%Y %H:%M %p').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    try:
        document_opening_time = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(6)').text
        document_opening_time = re.findall('\d+-\d+-\d{4}',document_opening_time)[0]
        notice_data.document_opening_time = datetime.strptime(document_opening_time,'%d-%m-%Y').strftime('%Y-%m-%d')
    except Exception as e:
        logging.info("Exception in document_opening_time: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    except:
        pass

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = "C.S.I.R- NATIONAL BOTANICAL RESEARCH INSTITUTE"
        customer_details_data.org_parent_id = 7427435
        customer_details_data.org_address = "436, Pratap Marg, Lucknow - 226001, Uttar Pradesh, India"
        customer_details_data.org_country = 'IN'
        customer_details_data.org_email = 'director@nbri.res.in'
        customer_details_data.org_phone = '+91-522-2297802 / +91-522-2205839'
        customer_details_data.org_website = 'https://www.nbri.res.in'
        customer_details_data.org_language = 'EN'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
        
    try:
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, 'td:nth-child(8) > a'):
            attachments_data = attachments()
            attachments_data.external_url =  single_record.get_attribute('href')
            attachments_data.file_name = 'Tender document'
            attachments_data.file_type = attachments_data.external_url.split('.')[-1].strip()
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
        
            
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) + str(notice_data.local_title)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments) 
page_details = fn.init_chrome_driver(arguments)
page_details1 = fn.init_chrome_driver(arguments)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://nbri.res.in/tenders/"] 
    for url in urls:
        fn.load_page(page_main, url, 80)
        logging.info('----------------------------------')
        logging.info(url)
        
        try:
            rows = WebDriverWait(page_main, 120).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'body > section > div.col-md-12.innercontent > div > div.col-md-8 > table:nth-child(8) > tbody > tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main,100).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'body > section > div.col-md-12.innercontent > div > div.col-md-8 > table:nth-child(8) > tbody > tr')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break

                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
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
    page_details1.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)