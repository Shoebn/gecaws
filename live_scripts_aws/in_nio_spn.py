from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "in_nio_spn"
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
from deep_translator import GoogleTranslator

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
tender_no = 0
SCRIPT_NAME = "in_nio_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    global tender_no
    notice_data = tender()
    
    notice_data.script_name = 'in_nio_spn'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)
   
    notice_data.currency = 'INR'
    
    notice_data.main_language = 'EN'
    
    notice_data.notice_type = 4
    
    notice_data.procurement_method = 2

    notice_data.notice_url = url


    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
        
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    except:
        pass

    try: 
        document_opening_time = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
        document_opening_time = re.findall('\d{4}-\d+-\d+',document_opening_time)[0]
        notice_data.document_opening_time = datetime.strptime(document_opening_time,'%Y-%m-%d').strftime('%Y-%m-%d')
    except Exception as e:
        logging.info("Exception in document_opening_time: {}".format(type(e).__name__))
        pass

    try: 
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(3)').text
        notice_deadline = re.findall('\d{4}-\d+-\d+ \d+:\d+:\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%Y-%m-%d %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
        return

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = 'CSIR-NATIONAL INSTITUTE OF OCEANOGRAPHY'
        customer_details_data.org_parent_id = 7642370
        customer_details_data.org_country = 'IN'
        customer_details_data.org_language = 'EN'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try:
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, 'td:nth-child(6) > a'):
            attachments_data = attachments()
            attachments_data.external_url =  single_record.get_attribute('href')
            attachments_data.file_name = single_record.text
            attachments_data.file_type = attachments_data.external_url.split('.')[-1].strip()
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1) > a').get_attribute("href")                     
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url

    try:
        fn.load_page(page_details,notice_data.notice_url,80)
        try:
            document_purchase_start_time = page_details.find_element(By.XPATH, '//*[contains(text(),"Sale of Tender(s) Starts on")]//following::dd[1]').text
            document_purchase_start_time = re.findall('\d{4}-\d+-\d+',document_purchase_start_time)[0]
            notice_data.document_purchase_start_time = datetime.strptime(document_purchase_start_time,'%Y-%m-%d').strftime('%Y/%m/%d')
        except Exception as e:
            logging.info("Exception in document_purchase_start_time: {}".format(type(e).__name__))
            pass
        
        try:
            document_purchase_end_time = page_details.find_element(By.XPATH, '//*[contains(text(),"Last date for sale of tenders")]//following::dd[1]').text
            document_purchase_end_time = re.findall('\d{4}-\d+-\d+',document_purchase_end_time)[0]
            notice_data.document_purchase_end_time = datetime.strptime(document_purchase_end_time,'%Y-%m-%d').strftime('%Y/%m/%d')
        except Exception as e:
            logging.info("Exception in document_purchase_end_time: {}".format(type(e).__name__))
            pass

        try:
            notice_data.related_tender_id = page_details.find_element(By.XPATH, '//*[contains(text(),"E-Tender Reference No")]//following::td[1]').text
        except Exception as e:
            logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
            pass
        
        try:
            earnest_money_deposit = page_details.find_element(By.XPATH, '//*[contains(text(),"EMD")]//following::td[1]').text
            earnest_money_deposit = re.sub("[^\d\.\,]", "", earnest_money_deposit)
            notice_data.earnest_money_deposit = earnest_money_deposit
        except Exception as e:
            logging.info("Exception in earnest_money_deposit: {}".format(type(e).__name__))
            pass

        try:
            for single_record in page_details.find_elements(By.XPATH, '//*[contains(text(),"Related Document(s)")]//following::td/a'):
                attachments_data = attachments()
                attachments_data.external_url =  single_record.get_attribute('href')
                attachments_data.file_name = single_record.text
                attachments_data.file_type = attachments_data.external_url.split('.')[-1].strip()
                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
        except Exception as e:
            logging.info("Exception in attachments1: {}".format(type(e).__name__)) 
            pass

        try:
            notice_data.notice_text += page_details.find_element(By.XPATH,'/html/body/div[3]/div[3]/div/div/div/div[2]/div[2]/div[2]/div[2]/div[5]/main').get_attribute('outerHTML')
        except:
            pass
    except:
        pass
            
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) + str(notice_data.local_title)
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    tender_no += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments) 
page_details = fn.init_chrome_driver(arguments)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.nio.res.in/tenders/tenders-open"] 
    for url in urls:
        fn.load_page(page_main, url, 80)
        logging.info('----------------------------------')
        logging.info(url)

        try:
            for page_no in range(2,4):
                page_check = WebDriverWait(page_main, 120).until(EC.presence_of_element_located((By.CSS_SELECTOR,'div.dataTables_scrollBody > table > tbody > tr'))).text
                rows = WebDriverWait(page_main, 120).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.dataTables_scrollBody > table > tbody > tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main,100).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.dataTables_scrollBody > table > tbody > tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
        
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    time.sleep(3)
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'div.dataTables_scrollBody > table > tbody > tr'),page_check))
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
