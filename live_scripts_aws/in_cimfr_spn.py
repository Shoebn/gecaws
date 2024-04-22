from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "in_cimfr_spn"
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
SCRIPT_NAME = "in_cimfr_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    

    notice_data.script_name = 'in_cimfr_spn'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'INR'
    notice_data.main_language = 'EN'
    notice_data.procurement_method = 2
    notice_data.notice_type = 4
    
    notice_data.document_type_description = "Tenders"
    
    try: 
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR,' td:nth-child(1)').text
    except:
        pass 
    
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR,' td:nth-child(1)').text
        try:
            publish_date =  re.findall('\d+/\d+/\d{4}',publish_date)[0]
            notice_data.publish_date= datetime.strptime(publish_date, '%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        except:
            try:
                publish_date =  re.findall('\d+.\d+.\d{4}',publish_date)[0]
                notice_data.publish_date= datetime.strptime(publish_date, '%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
            except:
                publish_date =  re.findall('\d+/\d+/\d+',publish_date)[0]
                notice_data.publish_date= datetime.strptime(publish_date, '%d/%m/%y').strftime('%Y/%m/%d %H:%M:%S')
    except:
        pass
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    try:
        document_opening_time = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        try:
            notice_data.document_opening_time = datetime.strptime(document_opening_time,'%dth %b, %Y').strftime('%Y-%m-%d')
        except:
            try:
                notice_data.document_opening_time = datetime.strptime(document_opening_time,'%dst %b, %Y').strftime('%Y-%m-%d')
            except:
                try:
                    notice_data.document_opening_time = datetime.strptime(document_opening_time,'%drd %b, %Y').strftime('%Y-%m-%d')
                except:
                    try:
                        notice_data.document_opening_time = datetime.strptime(document_opening_time,'%dnd %b, %Y').strftime('%Y-%m-%d')
                    except:
                        pass
        logging.info(notice_data.document_opening_time)
    except Exception as e:
        logging.info("Exception in document_opening_time: {}".format(type(e).__name__))
        pass
    
    

    try:
        notice_deadline =  tender_html_element.find_element(By.CSS_SELECTOR,' td:nth-child(4)').text
        try:
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%dth %b, %Y').strftime('%Y/%m/%d %H:%M:%S')
        except:
            try:
                notice_data.notice_deadline = datetime.strptime(notice_deadline,'%dst %b, %Y').strftime('%Y-%m-%d %H:%M:%S')
            except:
                try:
                    notice_data.notice_deadline = datetime.strptime(notice_deadline,'%drd %b, %Y').strftime('%Y-%m-%d %H:%M:%S')
                except:
                    try:
                        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%dnd %b, %Y').strftime('%Y-%m-%d %H:%M:%S')
                    except:
                        pass
    except:
        pass
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        notice_data.notice_title =  notice_data.local_title 
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = "CENTRAL INSTITUTE OF MINING AND FUEL RESEARCH"
        customer_details_data.org_parent_id = "7558169"
        customer_details_data.org_country = 'IN'
        customer_details_data.org_language = 'EN'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    notice_data.notice_url = url
    try:
        for single in tender_html_element.find_elements(By.CSS_SELECTOR,' td:nth-child(5) a'):
            attachments_data = attachments()

            attachments_data.file_name =  single.text
            if attachments_data.file_name == '':
                attachments_data.file_name =  "File"
            attachments_data.external_url = single.get_attribute('href')
            time.sleep(8)
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except:
        pass

    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
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
page_main = Doc_Download.page_details  
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://cimfr.nic.in/tenders.html"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        try:
            for page_no in range(2,10): #5
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,' #wrapper > div.section > div > div > div > table > tbody > tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#wrapper > div.section > div > div > div > table > tbody > tr')))
                length = len(rows)                                                                              
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ' #wrapper > div.section > div > div > div > table > tbody > tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
                        
                    if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                        logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                        break
                        
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 10).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 10).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#wrapper > div.section > div > div > div > table > tbody > tr'),page_check))
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
    output_json_file.copyFinalJSONToServer(output_json_folder)
