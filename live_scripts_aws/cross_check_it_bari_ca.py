from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "cross_check_it_bari_ca"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from deep_translator import GoogleTranslator
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "cross_check_it_bari_ca"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "cross_check_output"

def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = cross_check_output()
   
    notice_data.script_name = 'it_bari_ca'
    notice_data.main_language = 'IT'
   
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
    
    notice_data.procurement_method = 2
    notice_data.notice_type = 7
    notice_data.currency = 'EUR'
    notice_data.additional_source_name = 'Servizio Contratti Pubblic'

    try:
        notice_data.notice_no = tender_html_element.text.split("CIG : ")[1].split("\n")[0].strip().strip()
    except:
        try:
            notice_data.notice_no = tender_html_element.text.split("CIG ")[1].split("\n")[0].strip().strip()
        except:
            pass

        
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'form > div > div:nth-child(2)').text.split("Titolo :")[1].strip()
        notice_data.local_title = notice_data.local_title.lower()
        if 'cig' in notice_data.local_title:
            notice_data.local_title = notice_data.local_title.split('cig')[0]
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Tipologia appalto :
    # Onsite Comment -1.split after "Tipologia appalto : "	2.Replace follwing keywords with given respective kywords ('Servizi = Service','Lavori = Works ','forniture = Supply').

    try:
        notice_contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'form > div > div:nth-child(3)').text.split("Tipologia appalto :")[1].strip()
        if 'Servizi' in notice_contract_type:
            notice_data.notice_contract_type = 'Service'
        elif 'Lavori' in notice_contract_type:
            notice_data.notice_contract_type = 'Works'
        elif 'Forniture' in notice_contract_type:
            notice_data.notice_contract_type = 'Supply'
        else:
            pass
        notice_data.contract_type_actual = notice_contract_type
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Data pubblicazione esito :
    # Onsite Comment -1.split after "Data pubblicazione esito :".

    try:
        publish_date = tender_html_element.text.split('Data pubblicazione esito :')[1].split('\n')[0]
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Riferimento procedura :
    # Onsite Comment -1.split after "Riferimento procedura :".

    try:
        notice_data.related_tender_id = tender_html_element.text.split("Riferimento procedura :")[1].split('\n')[0].strip()
    except Exception as e:
        logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Stato :
    # Onsite Comment -1.split after "Stato :".

    try:
        notice_data.document_type_description = tender_html_element.text.split('Stato :')[1].split("\n")[0].strip()
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'a.bkg.detail-very-big').get_attribute("href")                     
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
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
    urls = ["https://portaleappalti.comune.bari.it/PortaleAppalti/it/ppgare_esiti_lista.wp?_csrf=KV6LC3CD89YZHS2EMCAH1J6VI91L673X"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(1,10): #10
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'div.list-item'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.list-item')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.list-item')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break

                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
                    
                if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                    logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                    break

            if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                break

            try:   
                next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR ,"#pagination-navi > input.nav-button.nav-button-right")))
                page_main.execute_script("arguments[0].click();",next_page)
                logging.info("Next page")
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'div.list-item'),page_check))
            except Exception as e:
                logging.info("Exception in next_page: {}".format(type(e).__name__))
                logging.info("No next page")
                break
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    output_json_file.copycrosscheckoutputJSONToServer(output_json_folder)
