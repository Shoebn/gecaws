from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "it_palermo_archive_spn"
log_config.log(SCRIPT_NAME)
import re
import jsons
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from deep_translator import GoogleTranslator
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
tnotice_count = 0
SCRIPT_NAME = "it_palermo_archive_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    global tnotice_count
    notice_data = tender()
    
    notice_data.script_name = 'it_palermo_archive_spn'
    
    notice_data.main_language = 'IT'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.procurement_method = 2
    
    notice_data.currency = 'EUR'

    notice_data.notice_type = 4
    
    # Onsite Field -Pubblicato il
    # Onsite Comment -None
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.content_mostra > a').get_attribute("href") 
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div.riga_pub_sta").text
        publish_date = re.findall('\d+.\d+.\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except:
        try:
            publish_date = page_details.find_element(By.XPATH, "//*[contains(text(),'Pubblicato il:')]//following::span[1]").text.split(':')[1].strip()
            publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.publish_date)
        except Exception as e:
            logging.info("Exception in publish_date: {}".format(type(e).__name__))
            pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    if notice_data.publish_date is None:
        return
    
    # Onsite Field -Scade il
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "div.riga_pub_sta > div:nth-child(4)").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    

    
    # Onsite Field -mostra
    # Onsite Comment -None

   
    
     # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#frame_contenuti > div.container > form').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
        # Onsite Field -Oggetto
    # Onsite Comment -None

    try:
        notice_data.local_title = page_details.find_element(By.CSS_SELECTOR, '#frame_contenuti > div.container > form > h1').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
   
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.content-link-allegato'):
            attachments_data = attachments()

            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')            

            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'a').text
            
            try:
                file_type = single_record.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
                attachments_data.file_type = file_type.split('.')[-1].strip()
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = 'Azienda Ospedaliera Ospedali Riuniti Villa Sofia Cervello'
        customer_details_data.org_country = 'IT'
        customer_details_data.org_language = 'IT'
        customer_details_data.org_parent_id = '4046674'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    tnotice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_details = fn.init_chrome_driver(arguments) 
page_main = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = '2022/01/01'
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://storico.ospedaliriunitipalermo.it/in_corso.html","https://storico.ospedaliriunitipalermo.it/avvisi.html","https://storico.ospedaliriunitipalermo.it/conclusi.html","https://storico.ospedaliriunitipalermo.it/altre_amministrazioni.html","https://storico.ospedaliriunitipalermo.it/non_scaduti.html"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,200):
            print(page_no-1)
            page_check = WebDriverWait(page_main, 100).until(EC.presence_of_element_located((By.CSS_SELECTOR,'div.content_pub_sta'))).text
            rows = WebDriverWait(page_main, 100).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.content_pub_sta')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 100).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.content_pub_sta')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break
                    
                if notice_count == 10:
                    output_json_file.copyFinalJSONToServer(output_json_folder)
                    output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
                    notice_count = 0

            try:   
                next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                page_main.execute_script("arguments[0].click();",next_page)
                logging.info("Next page")
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'div.content_pub_sta'),page_check))
            except Exception as e:
                logging.info("Exception in next_page: {}".format(type(e).__name__))
                logging.info("No next page")
                break
    logging.info("Finished processing. Scraped {} notices".format(tnotice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit() 
    output_json_file.copyFinalJSONToServer(output_json_folder)
    
