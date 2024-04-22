from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "cross_check_it_novara_spn"
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

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "cross_check_it_novara_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder =  "cross_check_output"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = cross_check_output()

    notice_data.script_name = 'it_novara_spn'
    notice_data.main_language = 'IT'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'

    notice_data.currency = 'EUR'
    notice_data.procurement_method = 2
    notice_data.notice_type = 4
    notice_data.class_at_source = 'CPV'
    notice_data.additional_source_name = 'Servizio Contratti Pubblic'
    
    #This script have 2 formats..
    # format-1) after opening the url click on this "Avvisi pubblici in corso".     "Tipologia" is unique keyword in format-1.
    try:
        notice_data.local_title = tender_html_element.text.split("Titolo :")[1].split("\n")[0].strip()
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:
        publish_date = tender_html_element.text.split('Data pubblicazione')[1].split("\n")[0].strip()
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    try:
        notice_deadline = tender_html_element.text.split('Data scadenza')[1].split("\n")[0].strip()
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.list-action > a.bkg.detail-very-big').get_attribute("href")                     
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
        
    try:
        notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'a.bkg.table').get_attribute("href")                     
    except Exception as e:
        logging.info("Exception in page_details1: {}".format(type(e).__name__))
           
    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    except:
        pass       
   
    try:
        notice_contract_type = tender_html_element.text.split("Avviso per :")[1].split("\n")[0].strip()
        if 'Servizi' in notice_contract_type:
            notice_data.notice_contract_type = 'Service'
        elif 'Lavori' in notice_contract_type:
            notice_data.notice_contract_type = 'Works'
        elif 'forniture' in notice_contract_type:
            notice_data.notice_contract_type = 'Supply'
        else:
            pass
        notice_data.contract_type_actual = notice_contract_type
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
        
    # Onsite Field -Tipologia appalto
    # Onsite Comment -1.split after "Tipologia appalto"	2)Repleace following keywords with given keywords("Lavori=Works","Servizi=Service")
    try:
        notice_contract_type = tender_html_element.text.split('Tipologia appalto :')[1].split("\n")[0].strip()
        if 'Servizi' in notice_contract_type:
            notice_data.notice_contract_type = 'Service'
        if 'Lavori' in notice_contract_type:
            notice_data.notice_contract_type = 'Works'
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass

    try:
        notice_data.contract_type_actual = notice_contract_type
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass
    # Onsite Field -Stato
    # Onsite Comment -1.split after "Stato"
    try:
        notice_data.document_type_description = tender_html_element.text.split("Stato :")[1].split("\n")[0].strip()
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    # Onsite Field -None
    # Onsite Comment -add also this clicks in notice_text:1)click on "div.list-action > a.bkg.table" in tender_html_element."main > div > div" use this selector for notice_text. 2)click on "//*[contains(text(),'Lotti')]//following::a[1]" this two clicks in page_details."main > div > div" use this selector for notice_text.
    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')              
    except:
        pass

    try:
        est_amount = tender_html_element.text.split("Importo :")[1].split('\n')[0]
        est_amount = re.sub("[^\d\.\,]","",est_amount).replace('.','').replace(',','.').strip()
        notice_data.est_amount = float(est_amount)
        notice_data.netbudgetlc = notice_data.est_amount
        notice_data.netbudgeteuro = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in est_amount2: {}".format(type(e).__name__))
        pass
      
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
    urls = ['https://llpp.comune.novara.it/PortaleAppalti/it/ppgare_avvisi_lista.wp?_csrf=P9LAICEYB3R6UL2JAQRJTU67H4RZEU7E','https://llpp.comune.novara.it/PortaleAppalti/it/ppgare_bandi_lista.wp?_csrf=2GK4JJ0896F537EU2R9ITE17DDG3U496'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(1,4):
            try:
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'div.list-item'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR,'div.list-item')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.list-item')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break

                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break

                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break

                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'input.nav-button.nav-button-right')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'div.list-item'),page_check))
                except Exception as e:
                    logging.info("Exception in next_page: {}".format(type(e).__name__))
                    logging.info("No next page")
                    break
            except:
                pass
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    output_json_file.copycrosscheckoutputJSONToServer(output_json_folder)
