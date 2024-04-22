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

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "in_edcilindia_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"

def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'in_edcilindia_spn'
    
    notice_data.main_language = 'EN'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.procurement_method = 2
  
    notice_data.currency = 'INR'
        
    notice_data.notice_type = 4
    
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, " td:nth-child(3)").text  
    except Exception as e:
        logging.info("Exception in notice_type: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        notice_data.notice_title = notice_data.local_title
        if len(notice_data.local_title) < 5:
            return
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass 
    
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, " td:nth-child(4)").text 
        notice_data.publish_date = datetime.strptime(publish_date,'%d %B %Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:
        notice_data.notice_text += tender_html_element.get_attribute("outerHTML")                     
    except:
        pass
    
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'IN'
        customer_details_data.org_language = 'EN'
        customer_details_data.org_name =  "EDCIL (INDIA) LIMITED"
        customer_details_data.org_parent_id = 7253573
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass    
    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, " td:nth-child(2) > a").get_attribute("href")
    except:
        pass

    try:
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)       
    except:
        pass
    
    format_type = page_main.find_element(By.CSS_SELECTOR, 'body > div.innerText > div > div > div.col-md-9.paddingLeft.wow.animated > div.wow.animated > h2').text
    
    if "E-Tenders" in format_type:
        
        notice_data.document_type_description = 'E-Tenders'
        
        try:
            notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#main > div').get_attribute("outerHTML")                     
        except:
            pass 
        
        try:               
            for single_record in page_details.find_elements(By.CSS_SELECTOR, '#main > div > div > table.table.table-striped.table-bordered > tbody > tr:nth-child(4) > td > a'):
                attachments_data = attachments()
                attachments_data.file_name = single_record.text

                attachments_data.external_url = single_record.get_attribute("href")

                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
        except Exception as e:
            logging.info("Exception in attachments_1: {}".format(type(e).__name__)) 
            pass
        
        try:            
            for single_record in page_details.find_elements(By.CSS_SELECTOR, '#main > div > div > table:nth-child(2) > tbody > tr > td:nth-child(1) > a'):
                attachments_data = attachments()
                notice_data.notice_type = 16
                attachments_data.file_name = single_record.text
                
                attachments_data.external_url = single_record.get_attribute("href")

                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
        except Exception as e:
            logging.info("Exception in attachments_3: {}".format(type(e).__name__)) 
            pass   
        
    else:
        notice_data.document_type_description = 'Tenders'
        
        try:
            notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(5)").text
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d %B %Y').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.notice_deadline)
        except Exception as e:
            logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
            pass
        
        try:
            notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'body > form').get_attribute("outerHTML")                     
        except:
            pass   
        
        try:             
            for single_record in page_details.find_elements(By.CSS_SELECTOR, 'td:nth-child(1) > ul > li > a'):
                attachments_data = attachments()
                attachments_data.file_name = single_record.text
                
                attachments_data.external_url = single_record.get_attribute("href")

                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
        except Exception as e:
            logging.info("Exception in attachments_2: {}".format(type(e).__name__)) 
            pass   
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title) 
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments) 
page_details =fn.init_chrome_driver(arguments)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.edcilindia.co.in/TenderAwardeds"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)  
        
        for no in range(0,2):
            url1 = page_main.find_elements(By.CSS_SELECTOR, "body > div.innerText > div > div > div.col-md-3.wow.animated > div > ul > li > a")[no]
            sub_url = url1.get_attribute("href")
            fn.load_page(page_main, sub_url, 50)
            time.sleep(5)
            try:
                for page_no in range(1,5):
                    page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#grid > div > table.table.table-striped.table-bordered > tbody > tr'))).text
                    rows = WebDriverWait(page_main, 80).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#grid > div > table.table.table-striped.table-bordered > tbody > tr')))
                    length = len(rows)
                    for records in range(0,length):
                        tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#grid > div > table.table.table-striped.table-bordered > tbody > tr')))[records]
                        extract_and_save_notice(tender_html_element)
                        if notice_count >= MAX_NOTICES:
                            break
                    try:   
                        next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,"Next »")))
                        page_main.execute_script("arguments[0].click();",next_page)
                        logging.info("Next page")
                        WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#grid > div > table.table.table-striped.table-bordered > tbody > tr'),page_check))
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
