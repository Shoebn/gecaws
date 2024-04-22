#1)for bidder name
# As discussed with shoeib added below condition .. (1) if lot avaialble than condition 
# lot_title ="blank "and award_details ="blank" []
# than lot_details =[]
# (2) if lots not avaible than
# award_details= []
# and lot_details= []

from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "es_adjudicacionestic_ca"
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
SCRIPT_NAME = "es_adjudicacionestic_ca"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
   
    notice_data.script_name = 'es_adjudicacionestic_ca'
    
    notice_data.main_language = 'ES'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'ES'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'EUR'
    
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 7
    
    # Onsite Field -Fecha
    # Onsite Comment -None
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(1)").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    # Onsite Field -Organismo | Adjudicatario | Título de la adjudicación
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a > h3:nth-child(3)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass


    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
        
    # Onsite Field -None
    # Onsite Comment -1.split notice_no from url.

    try:
        notice_no = notice_data.notice_url.split("=")[1]
        notice_data.notice_no = re.findall('\d+',notice_no)[0]
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    

    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#award-page > div.container').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'ES'
        customer_details_data.org_language = 'ES'
    # Onsite Field -Organismo | Adjudicatario | Título de la adjudicación
    # Onsite Comment -None
        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a > h3:nth-child(1)').text.strip()
        
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        lot_details_data = lot_details()
    # Onsite Field -Organismo | Adjudicatario | Título de la adjudicación
    # Onsite Comment -None
        lot_details_data.lot_number = 1
        lot_details_data.lot_title = notice_data.local_title
        notice_data.is_lot_default = True
        lot_details_data.lot_title_english = notice_data.notice_title
        
        award_details_data = award_details()
        # Onsite Field -Organismo | Adjudicatario | Título de la adjudicación
        # Onsite Comment -None

        award_details_data.bidder_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a > h3:nth-child(2)').text
        # Onsite Field -Importe
        # Onsite Comment -None 197.833€
        try:
            netawardvaluelc1 = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
            netawardvaluelc = re.sub("[^\d\.\,]", "", netawardvaluelc1)
            award_details_data.netawardvaluelc = float(netawardvaluelc.replace('.','').replace(',','.').strip())
            award_details_data.netawardvalueeuro = award_details_data.netawardvaluelc
        except:
            pass

        # Onsite Field -Fecha adjudicación
        # Onsite Comment -None
        try:
            award_date = page_details.find_element(By.CSS_SELECTOR, 'div.row.clear.adj-header-2 > div:nth-child(2) > h2 > strong').text
            award_date = re.findall('\d+/\d+/\d{4}',award_date)[0]
            award_details_data.award_date = datetime.strptime(award_date,'%d/%m/%Y').strftime('%Y/%m/%d')
        except:
            pass
        award_details_data.award_details_cleanup()
        lot_details_data.award_details.append(award_details_data)

        if lot_details_data.award_details != []:
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -Documentos
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.row.adj-header-3 > div.col1-3 > h4 > a'):
            attachments_data = attachments()
        # Onsite Field -Documentos
        # Onsite Comment -1.take in text format.
            attachments_data.file_name = single_record.text
        
        # Onsite Field -Documentos
        # Onsite Comment -None
            attachments_data.external_url = single_record.get_attribute('href')
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
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
    urls = ["https://www.adjudicacionestic.com/front/adjudicaciones-tic.php"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(2,7):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="adjudicacionesTIC-page-table"]/tbody/tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="adjudicacionesTIC-page-table"]/tbody/tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="adjudicacionesTIC-page-table"]/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="adjudicacionesTIC-page-table"]/tbody/tr'),page_check))
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
