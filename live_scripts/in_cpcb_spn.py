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
from selenium.webdriver.support.ui import Select

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "in_cpcb_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    

    notice_data.script_name = 'in_cpcb_spn'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'INR'
    notice_data.main_language = 'EN'
    notice_data.procurement_method = 2
    notice_data.notice_type = 4
    
    notice_data.document_type_description = "Tenders"

    notice_data.notice_url = url
    
    try: 
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR,'div.reference-number').text.split('Reference Number')[1]
    except:
        pass

    try:
        publish_date =  tender_html_element.find_element(By.CSS_SELECTOR,' td:nth-child(4) ').text
        publish_date = re.findall('\d+/\d+/\d+ \d+:\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date, '%d/%m/%y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
    except:
        pass
    try:
        notice_deadline =  tender_html_element.find_element(By.CSS_SELECTOR,' td:nth-child(5)').text
        notice_deadline = re.findall(r'\d+/\w+/\d+ \d+:\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline, '%d/%m/%y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
    except:
        pass
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = "CENTRAL POLLUTION CONTROL BOARD"
        customer_details_data.org_parent_id = "7551616"
        try:
            org_phone = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
            customer_details_data.org_phone = re.findall('\d+-\d+',org_phone)[0]
        except:
            pass
        try:
            customer_details_data.contact_person = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text.replace(customer_details_data.org_phone,'')
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
        attachments_data = attachments()
        attachments_data.file_name = 'Tender document'
        attachments_data.external_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2) a').get_attribute('href')
        time.sleep(8)
        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except:
        pass
    try:
        attachments_data = attachments()
        attachments_data.file_name = 'Tender document'
        attachments_data.external_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(6) a').get_attribute('href')
        if attachments_data.external_url !='':
            notice_data.notice_type = 16
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
    urls = ["https://cpcb.nic.in/tender.php"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(2,5): 
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#tender > tbody > tr '))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#tender > tbody > tr')))
                length = len(rows)                                                                              
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#tender > tbody > tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break

                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    page_check2 = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#tender > tbody > tr '))).text
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#tender > tbody > tr'),page_check2))
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
