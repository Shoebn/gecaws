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

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "in_mglgov_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'in_mglgov_spn'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)
   
    notice_data.currency = 'INR'
    
    notice_data.main_language = 'EN'
    
    notice_data.notice_type = 4
    
    notice_data.procurement_method = 2
    
    notice_data.notice_url = url 

    notice_data.document_type_description = "Tenders"
            
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:         
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
        publish_date = re.findall('\d+ \w+ \d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d %b %Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try: 
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(5)').text
        notice_deadline = re.findall('\d+ \w+ \d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d %b %Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    try:
        notice_type = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        if "Corrigendum" in notice_type:
            notice_data.notice_type = 16
        else:
            notice_data.notice_type = 4
    except:
        pass
        
    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    except:
        pass

    try:              
        customer_details_data = customer_details() 
        customer_details_data.org_name = "GOVERNMENT OF MEGHALAYA"
        customer_details_data.org_parent_id = 7567711
        customer_details_data.org_state = "Meghalaya"
        try:
            customer_details_data.org_address = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
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
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)> a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url

    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"Reference Number")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    try: 
        document_opening_time = page_details.find_element(By.XPATH, '//*[contains(text(),"Opening Date")]//following::div[1]').text
        document_opening_time = re.findall('\d+ \w+ \d{4}',document_opening_time)[0]
        notice_data.document_opening_time = datetime.strptime(document_opening_time,'%d %b %Y').strftime('%Y-%m-%d')
    except Exception as e:
        logging.info("Exception in document_opening_time: {}".format(type(e).__name__))
        pass


    try:  
        attachments_data = attachments()
        attachments_data.external_url = page_details.find_element(By.XPATH,'//*[contains(text(),"Click here to View/Download")]//parent::a[1]').get_attribute('href')
        attachments_data.file_name = "tender_documents"
        attachments_data.file_size = page_details.find_element(By.XPATH,'//*[contains(text(),"Click here to View/Download")]//following::small[1]').text.split('/')[1].strip()

        try:
            attachments_data.file_type = attachments_data.external_url.split('.')[-1].strip()
        except:
            pass
        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass

    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#block-custom-zircon-content > div > div > div').get_attribute('outerHTML')
    except:
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
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://meghalaya.gov.in/tenders"] 
    for url in urls:
        fn.load_page(page_main, url, 80)
        logging.info('----------------------------------')
        logging.info(url)

        try:
            rows = WebDriverWait(page_main, 120).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#block-custom-zircon-content > div > div > div.view-content > table > tbody > tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 200).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#block-custom-zircon-content > div > div > div.view-content > table > tbody > tr')))[records]
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
