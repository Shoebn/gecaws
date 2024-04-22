
from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "jp_customs_spn"
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
SCRIPT_NAME = "jp_customs_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    notice_data.script_name = 'jp_customs_spn'
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'JP'
    notice_data.performance_country.append(performance_country_data)
    notice_data.currency = 'JPY'
    notice_data.main_language = 'JA'
    notice_data.procurement_method = 2
    notice_data.notice_type = 4
    
    try:
        local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
        notice_data.local_title = local_title.split('（PDF')[0].strip()
        notice_data.notice_title = GoogleTranslator(source='ja', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass              
                
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        publish_date = GoogleTranslator(source='ja', target='en').translate(publish_date)        
        notice_data.publish_date = datetime.strptime(publish_date, '%B %d, %Y').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass            
                
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return                   
        
    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
        notice_deadline = GoogleTranslator(source='ja', target='en').translate(notice_deadline)
        notice_data.notice_deadline = datetime.strptime(notice_deadline, '%B %d, %Y').strftime('%Y/%m/%d %H:%M:%S')        
        notice_data.document_purchase_end_time = datetime.strptime(notice_deadline, '%B %d, %Y').strftime('%Y/%m/%d')
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass     
            
    notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text    
    
    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML') 
    except:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, '#contents > div:nth-child(2) > table > tbody').get_attribute("outerHTML")  
    notice_data.notice_url = 'https://www.customs.go.jp/kyotsu/chotatsu/nyusatsu/n_index.htm'        
    
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = 'JAPAN PAVILION CUSTOMS TRANSPORT'
        customer_details_data.org_parent_id = '7457251'
        customer_details_data.org_address = '〒100-8940 東京都千代田区霞が関3-1-1'
        customer_details_data.org_city = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
        
        customer_details_data.org_country = 'JP'
        customer_details_data.org_language = 'JA'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass   

    try:              
        attachments_data = attachments()
        attachments_data.file_name = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text
        attachments_data.external_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4) > a').get_attribute('href') 
        try:
            attachments_data.file_type = attachments_data.external_url.split('.')[-1]
        except Exception as e:
            logging.info("Exception in file_type: {}".format(type(e).__name__))
            pass
        
        try:
            attachments_data.file_size = attachments_data.file_name.split('（PDF：')[1].split('）')[0]
        except Exception as e:
            logging.info("Exception in file_size: {}".format(type(e).__name__))
            pass    

        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass    

    notice_data.identifier = str(notice_data.script_name) + str(notice_data.local_title) +  str(notice_data.notice_type) +  str(notice_data.notice_url)+  str(notice_data.local_title) 
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
    urls = ["https://www.customs.go.jp/kyotsu/chotatsu/nyusatsu/n_index.htm"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        time.sleep(15)

        try:
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#contents > div:nth-child(2) > table > tbody > tr'))).text  
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#contents > div:nth-child(2) > table > tbody > tr')))
            length = len(rows)
            for records in range(1,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#contents > div:nth-child(2) > table > tbody > tr')))[records]  
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
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
    
    
