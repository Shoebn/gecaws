from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "it_gpaappaltiamo_spn"
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

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "it_gpaappaltiamo_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
   
    notice_data.script_name = 'it_gpaappaltiamo_spn'
    
    notice_data.main_language = 'IT'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'EUR'
    
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 4

    try:
        notice_data.document_type_description = page_main.find_element(By.CSS_SELECTOR, 'h2.text-center').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Oggetto
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Codice
    # Onsite Comment -if the given notice_no is not available the take notice_no from notice_url

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Scadenza
    # Onsite Comment -None  15/02/2024 13:00:00

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text
        notice_deadline = re.findall('\d+/\d+/\d{4} \d+:\d+:\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
        return
    # Onsite Field -Tipo
    # Onsite Comment -split and take data before first '-'
    
    try:
        notice_data.type_of_procedure_actual = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(5)").text.split('-')[0].strip()
        type_of_procedure = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("assets/it_gpaappaltiamo_spn_procedure.csv",type_of_procedure)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    try:              
        customer_details_data = customer_details()
        # Onsite Field -Ente
        # Onsite Comment -None

        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text

        customer_details_data.org_language = 'IT'
        customer_details_data.org_country = 'IT'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
       
    # Onsite Field -Dettagli
    # Onsite Comment -None 

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, ' td:nth-child(6) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
        
    try:
        if notice_data.notice_no == None:
            notice_data.notice_no = notice_data.notice_url.split('?id=')[-1].strip()
    except Exception as e:
        logging.info("Exception in notice_no2: {}".format(type(e).__name__))
    
    # Onsite Field -None
    # Onsite Comment -take tender_html_page data also (selector :- "/html/body/form/div[4]/div/div[3]/table/tbody/tr")
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'section.col-12').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    # Onsite Field -Durata
    # Onsite Comment -None

    try:
        notice_data.contract_duration = page_details.find_element(By.XPATH, '//*[contains(text(),"Durata")]//following::em[1]').text
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Importo
    # Onsite Comment -None

    try:
        est_amount = page_details.find_element(By.XPATH, '//*[contains(text(),"Importo")]//following::em[1]').text
        est_amount = re.sub("[^\d\.\,]","",est_amount)
        notice_data.est_amount =float(est_amount.replace('.','').replace(',','.').strip())
        notice_data.netbudgetlc = notice_data.est_amount
        notice_data.netbudgeteuro = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
     
    # Onsite Field -Ambito
    # Onsite Comment -Replace the following keywords with respective keywords(Lavori = Works , Servizi = Service , Forniture = Supply )

    try:
        notice_data.contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Ambito")]//following::em[1]').text
        if 'Lavori' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Works'
        elif 'Servizi' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Service'
        elif 'Forniture' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Supply'
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
# Onsite Field -Lotti
# Onsite Comment -None

    try:  
        lot_number = 1
        lots = page_details.find_element(By.XPATH, '//*[contains(text(),"Lotti")]//following::table[2]')
        for single_record in lots.find_elements(By.CSS_SELECTOR, '#riepilogolotti > table > tbody > tr '):
            lot_details_data = lot_details()
            lot_details_data.lot_number = lot_number
            lot_details_data.contract_type = notice_data.notice_contract_type
            lot_details_data.lot_contract_type_actual = notice_data.contract_type_actual 
        # Onsite Field -CIG
        # Onsite Comment -None

            try:
                lot_details_data.lot_actual_number = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Oggetto
        # Onsite Comment -None

            lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
            lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
        # Onsite Field -Durata
        # Onsite Comment -None

            try:
                lot_details_data.contract_duration = single_record.find_element(By.CSS_SELECTOR, ' td:nth-child(4)').text
            except Exception as e:
                logging.info("Exception in contract_duration: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Importo
        # Onsite Comment -None

            try:
                lot_grossbudget_lc = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
                lot_grossbudget_lc = re.sub("[^\d\.\,]","",lot_grossbudget_lc)
                lot_details_data.lot_netbudget_lc =float(lot_grossbudget_lc.replace('.','').replace(',','.').strip())
                lot_details_data.lot_netbudget = lot_details_data.lot_netbudget_lc
            except Exception as e:
                logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
                pass
        
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
            lot_number += 1
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -Documenti gara
# Onsite Comment -None 

    try:              
        attachment = page_details.find_element(By.XPATH, '//*[contains(text(),"Documenti gara")]//following::table[1]')
        for single_record in attachment.find_elements(By.CSS_SELECTOR, '#documentigara > table > tbody > tr'):
            attachments_data = attachments()

            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
        # Onsite Field -File
        # Onsite Comment -None

            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(4) > a').get_attribute('href')
            if attachments_data.external_url != None:
                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -Buste
# Onsite Comment -None 

    try:       
        attachment2 = page_details.find_element(By.XPATH, '//*[contains(text(),"Lotti")]//following::table[2]')
        for single_record in attachment2.find_elements(By.CSS_SELECTOR, 'div.link-list-wrapper > ul > li > ul > li > a'):
            attachments_data = attachments()
        # Onsite Field -Buste
        # Onsite Comment -take file_name in textform

            attachments_data.file_name = single_record.text
        # Onsite Field -Buste
        # Onsite Comment -None

            attachments_data.external_url = single_record.get_attribute('href')
            if attachments_data.external_url != None:
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
    urls = ['https://gpa.appaltiamo.eu/procedure.aspx'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(2,5):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/form/div[4]/div/div[3]/table/tbody/tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/form/div[4]/div/div[3]/table/tbody/tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/form/div[4]/div/div[3]/table/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
                        break
    
                if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/form/div[4]/div/div[3]/table/tbody/tr'),page_check))
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
    
