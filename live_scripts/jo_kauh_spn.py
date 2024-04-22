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
tender_no = 0
SCRIPT_NAME = "jo_kauh_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    global tender_no
    notice_data = tender()
    
    notice_data.script_name = 'jo_kauh_spn'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'JO'
    notice_data.performance_country.append(performance_country_data)
   
    notice_data.currency = 'JOD'
    
    notice_data.main_language = 'AR'
    
    notice_data.notice_type = 4
    
    notice_data.procurement_method = 2

    notice_data.notice_url = url

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1) > span').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        notice_data.notice_title = GoogleTranslator(source='ar', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:
        notice_data.document_cost = float(tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3) > span').text)
    except Exception as e:
        logging.info("Exception in document_cost: {}".format(type(e).__name__))
        pass
    

    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    except:
        pass

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(4)').text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
        return
        
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = "King Abdullah University Hospital"
        customer_details_data.org_parent_id = 7813789
        customer_details_data.org_country = 'JO'
        customer_details_data.org_language = 'AR'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass


    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5) > a').get_attribute("href")                     
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url

    try:
        fn.load_page(page_details,notice_data.notice_url,80)
        try:
            for single_record in page_details.find_elements(By.CSS_SELECTOR, '#ContentPlaceHolder1_gvImages > tbody > tr')[1:]:
                attachments_data = attachments()
                attachments_data.external_url =  single_record.find_element(By.CSS_SELECTOR,'td:nth-child(2) > a').get_attribute('href')
                attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR,'td:nth-child(1)').text
                attachments_data.file_type = attachments_data.external_url.split('.')[-1].strip()
                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
        except Exception as e:
            logging.info("Exception in attachments1: {}".format(type(e).__name__)) 
            pass
    
        try:
            single_record=page_details.find_elements(By.CSS_SELECTOR, '#ContentPlaceHolder1_Panel5 > div.col-md-12 > div > ul > a')
            for single_record in page_details.find_elements(By.CSS_SELECTOR, '#ContentPlaceHolder1_Panel5 > div.col-md-12 > div > ul > a')[:-1]:
                attachments_data = attachments()
                attachments_data.external_url =  single_record.get_attribute('href')
                attachments_data.file_name = single_record.text
                attachments_data.file_type = attachments_data.external_url.split('.')[-1].strip()
                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
        except Exception as e:
            logging.info("Exception in attachments2: {}".format(type(e).__name__)) 
            pass
             
        try:
            notice_data.notice_text += page_details.find_element(By.XPATH,'//*[@id="ContentPlaceHolder1_Panel5"]/div[2]').get_attribute('outerHTML')
        except:
            pass
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
    urls = ["https://www.kauh.edu.jo/%D8%A7%D9%84%D8%B9%D8%B7%D8%A7%D8%A1%D8%A7%D8%AA"] 
    for url in urls:
        fn.load_page(page_main, url, 80)
        logging.info('----------------------------------')
        logging.info(url)

        try:
            page_check = WebDriverWait(page_main, 120).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#ContentPlaceHolder1_GridView1 > tbody > tr:nth-child(2)'))).text
            rows = WebDriverWait(page_main, 120).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#ContentPlaceHolder1_GridView1 > tbody > tr')))
            length = len(rows)
            for records in range(1,length):
                tender_html_element = WebDriverWait(page_main,100).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#ContentPlaceHolder1_GridView1 > tbody > tr')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break
                    
                if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
                    return
        
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