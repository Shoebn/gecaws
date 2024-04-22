#updated script for it_liguria(37428)
from gec_common.gecclass import *
import logging
import re
import jsonss
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from deep_translator import GoogleTranslator
from selenium import webdriver
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
import functions as fn
from functions import ET
import common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "it_liguria"
Doc_Download = common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.main_language = 'IT'
    
    notice_data.currency = 'EUR'
    
    notice_data.performance_country = 'IT'
    
    notice_data.notice_type = '4'
    
    notice_data.procurement_method = 'Other'
    
    # Onsite Field -Data di pubblicazione
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div.pc_latest_item_apertura.minisize").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: ", str(type(e)))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Data di chiusura
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "div.pc_latest_item_chiusura.minisize").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: ", str(type(e)))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.notice_url = page_main.find_element(By.CSS_SELECTOR, 'div.pc_latest_item_bando.col-xl-9 > div:nth-child(2) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
    except:
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.notice_text = page_details.find_element(By.XPATH, '//*[@id=content]/div[4]').text
    except Exception as e:
        logging.info("Exception in notice_text: ", str(type(e)))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.pc_latest_item_bando.col-xl-9 > div:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in local_title: ", str(type(e)))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.notice_summary_english = tender_html_element.find_element(By.CSS_SELECTOR, 'div.pc_latest_item_bando.col-xl-9 > div:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: ", str(type(e)))
        pass
    
# Onsite Field -None
# Onsite Comment -None



try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.pc_latest_item_bando.col-xl-9'):
            lot_details_data = lot_details()
        # Onsite Field -None
        # Onsite Comment -None

            try:
                lot_details_data.lot_title = page_details.find_element(By.CSS_SELECTOR, 'div.pc_latest_item_bando.col-xl-9 > div:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in lot_title: ", str(type(e)))
                pass
        
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: ", str(type(e))) 
        pass
		
try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.boxInfo'):
            customer_details_data = customer_details()
        # Onsite Field -Soggetto proponente
        # Onsite Comment -None

            try:
                customer_details_data.org_city = page_details.find_element(By.CSS_SELECTOR, 'div.pc_latest_item_enti.minisize').text
            except Exception as e:
                logging.info("Exception in org_city: ", str(type(e)))
                pass

			customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: ", str(type(e))) 
        pass
		
try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.doc_elenco_box'):
            attachments_data = attachments()
        # Onsite Field -DOCUMENTI
        # Onsite Comment -None

            try:
                attachments_data.file_name = page_details.find_element(By.CSS_SELECTOR, 'li > div:nth-child(2) > div > a').text
            except Exception as e:
                logging.info("Exception in file_name: ", str(type(e)))
                pass
        
        # Onsite Field -DOCUMENTI
        # Onsite Comment -None

			try:
                attachments_data.external_url = page_details.find_element(By.CSS_SELECTOR, 'div.doc_title_descr > div > a').get_attribute('href')
            except Exception as e:
                logging.info("Exception in external_url: ", str(type(e)))
                pass
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: ", str(type(e))) 
        pass

# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments) 
page_details = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = [https://www.regione.liguria.it/homepage-bandi-e-avvisi.html'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,18):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="pcCompetitionForm"]/div[2]'))).text
            rows = WebDriverWait(driver, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="pcCompetitionForm"]/div[2]')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id=sectionBandi880089626]/div[1]/div')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break
                
                if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                    logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                    break

                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break

            try:   
                next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                page_main.execute_script("arguments[0].click();",next_page)
                logging.info("Next page")
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id=sectionBandi880089626]/div[1]/div'),page_check))
            except Exception as e:
                logging.info("Exception in next_page: ", str(type(e)))
                logging.info("No next page")
                break
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit() 
    
    output_json_file.copyFinalJSONToServer(output_json_folder)