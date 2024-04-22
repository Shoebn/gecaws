from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "in_optcl_spn"
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
SCRIPT_NAME = "in_optcl_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"

def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'in_optcl_spn'
    
    notice_data.main_language = 'EN'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.procurement_method = 2
  
    notice_data.currency = 'INR'
    
    notice_data.document_type_description = 'Tenders / EOI'
    
    notice_data.notice_url = url 
    
    notice_data.document_type_description = "Active Tenders"
  
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-md-7.tenderdetails > div > strong').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    try:
        notice_type = tender_html_element.find_element(By.CSS_SELECTOR, ' div.col-md-7.tenderdetails > div > p:nth-child(3)').text
        if "Corrigendum" in notice_type:
            notice_data.notice_type = 16
        else:
            notice_data.notice_type = 4
    except Exception as e:
        logging.info("Exception in notice_type: {}".format(type(e).__name__))
        pass
            
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-md-7.tenderdetails > div > p:nth-child(2)').text.split('SCOPE OF WORK:')[1].strip()
        if len(notice_data.local_title) < 5:
            return
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:               
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div.col-md-5.tenderrequirement > ul > li:nth-child(2)").text
        try:
            publish_date = re.findall('\d+/\w+/\d{4} \d+:\d+ [AMPMampm]+',publish_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date,'%d/%b/%Y %I:%M %p').strftime('%Y/%m/%d %H:%M:%S')
        except:
            publish_date = re.findall('\d+/\w+/\d{4}',publish_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date,'%d/%b/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "div.col-md-5.tenderrequirement > ul > li:nth-child(5)").text
        try:
            notice_deadline = re.findall('\d+/\w+/\d{4} \d+:\d+ [AMPMampm]+',notice_deadline)[0]
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%b/%Y %I:%M %p').strftime('%Y/%m/%d %H:%M:%S')
        except:
            notice_deadline = re.findall('\d+/\w+/\d{4}',notice_deadline)[0]
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%b/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    try:
        document_opening_time1 = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-md-5.tenderrequirement > ul > li:nth-child(4)').text
        document_opening_time = re.findall('\d+/\w+/\d{4}',document_opening_time1)[0]
        notice_data.document_opening_time = datetime.strptime(document_opening_time,'%d/%b/%Y').strftime('%Y-%m-%d')
        logging.info(notice_data.document_opening_time)
    except Exception as e:
        logging.info("Exception in document_opening_time: {}".format(type(e).__name__))
        pass
    
    try:
        document_purchase_start_time = tender_html_element.find_element(By.CSS_SELECTOR, "div.col-md-5.tenderrequirement > ul > li:nth-child(2)").text
        document_purchase_start_time = re.findall('\d+/\w+/\d{4}',document_purchase_start_time)[0]
        notice_data.document_purchase_start_time = datetime.strptime(document_purchase_start_time,'%d/%b/%Y').strftime('%Y/%m/%d')
    except Exception as e:
        logging.info("Exception in document_purchase_start_time: {}".format(type(e).__name__))
        pass 
    
    try:
        document_purchase_end_time = tender_html_element.find_element(By.CSS_SELECTOR, "div.col-md-5.tenderrequirement > ul > li:nth-child(3)").text
        document_purchase_end_time = re.findall('\d+/\w+/\d{4}',document_purchase_end_time)[0]
        notice_data.document_purchase_end_time = datetime.strptime(document_purchase_end_time,'%d/%b/%Y').strftime('%Y/%m/%d')
    except Exception as e:
        logging.info("Exception in document_purchase_end_time: {}".format(type(e).__name__))
        pass 
    
    try:
        notice_data.notice_text += tender_html_element.get_attribute("outerHTML")                     
    except:
        pass
    
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'IN'
        customer_details_data.org_language = 'EN'
        customer_details_data.org_name =  "ODISHA POWER TRANSMISSION CORPORATION LIMITED"
        customer_details_data.org_parent_id = 7527457
        customer_details_data.org_state = "Odisha"
        
        try:
            customer_details_data.org_address = tender_html_element.find_element(By.CSS_SELECTOR, "div.col-md-5.tenderrequirement > ul > li:nth-child(1)").text.split('Issuing authority:')[1].strip()
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass 
    
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass    
    
    try:               
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, 'div.col-md-7.tenderdetails > div > p:nth-child(3) > a'):
            attachments_data = attachments()
            
            attachments_data.file_name = single_record.text

            attachments_data.external_url = single_record.get_attribute("href")
            
            try:
                attachments_data.file_type = attachments_data.external_url.split('.')[-1].strip()
            except:
                pass

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://optcl.co.in/Tender.aspx"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)  
          
        try:
            rows = WebDriverWait(page_main, 80).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#aspnetForm > div.wrapper > div:nth-child(3) > div.container > div > div')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#aspnetForm > div.wrapper > div:nth-child(3) > div.container > div > div')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break

        except:
            logging.info("No new record")
            break
        
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)
