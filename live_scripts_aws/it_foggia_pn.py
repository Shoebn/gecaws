from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "it_foggia_pn"
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
SCRIPT_NAME = "it_foggia_pn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    

    notice_data.script_name = 'it_foggia_pn'
    
    notice_data.main_language = 'IT'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.procurement_method = 2
    
    notice_data.currency = 'EUR'
    
    notice_data.notice_type = 1
    
    notice_data.type_of_procedure = 'Other'
    
    
    
      # Onsite Field -Riferimento procedura
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(4)').text.split(':')[1].split('(')[0]
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Titolo procedura
    # Onsite Comment -None

    try:
        notice_data.local_description = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(5)').text
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Data invio
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "div:nth-child(1)").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    
    # Onsite Field -Testo
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(3)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Oggetto
    # Onsite Comment -None

    try:
        document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(2)').text
        if 'Oggetto' in document_type_description:
            notice_data.document_type_description = document_type_description
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Visualizza scheda
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.list-action > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except:
        notice_data.notice_url = url
        
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div > main').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Procedura di gara
    # Onsite Comment -None

    try:
        notice_data.type_of_procedure_actual = page_details.find_element(By.CSS_SELECTOR, 'div > main').text.split('Procedura di gara :')[1].split('\n')[0]
        if 'Procedura aperta' in notice_data.type_of_procedure_actual:
            notice_data.type_of_procedure = 'Open'
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Importo a base di gara
    # Onsite Comment -None

    try:
        est_amount = page_details.find_element(By.CSS_SELECTOR, 'div > main').text.split('Importo a base di gara :')[1].split('€')[0]
        est_amount = re.sub("[^\d\.\,]", "",est_amount)
        est_amount = est_amount.replace('.','').replace(',','.').strip()
        notice_data.est_amount = float(est_amount)
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    

    try:
        grossbudgetlc = page_details.find_element(By.CSS_SELECTOR, 'div > main').text.split('Importo a base di gara :')[1].split('€')[0]
        grossbudgetlc = re.sub("[^\d\.\,]", "",grossbudgetlc)
        grossbudgetlc = grossbudgetlc.replace('.','').replace(',','.').strip()
        notice_data.grossbudgetlc = float(grossbudgetlc)
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Data scadenza
    # Onsite Comment -None

    try:
        publish_date = page_details.find_element(By.CSS_SELECTOR, 'div > main').text.split('Data pubblicazione : ')[1].split('\n')[0]
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    try:              
        customer_details_data = customer_details()
    # Onsite Field -Responsabile unico procedimento
    # Onsite Comment -None
        try:
            customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[@id="ext-container"]/div/div/div/main/div/div/div[3]/div[2]').text.split(':')[1]
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass

    # Onsite Field -Denominazione
    # Onsite Comment -None

        customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[@id="ext-container"]/div/div/div/main/div/div/div[3]/div[1]').text.split(':')[1]
        

        customer_details_data.org_country = 'IT'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    



    try:              
        # Onsite Field -Categoria/Prestazione
        # Onsite Comment -split from "Category/Performance: " take only title
        
        lots_url = page_details.find_element(By.CSS_SELECTOR, 'div:nth-child(12) > ul > li > a').get_attribute("href")                     
        fn.load_page(page_details1,lots_url,80)
        
        lot_number = 1
        for single_record in page_details1.find_elements(By.CSS_SELECTOR, 'div.detail-subrow > div > div'):
            lot_details_data = lot_details()
            lot_details_data.lot_number = lot_number

        
        # Onsite Field -Categoria/Prestazione
        # Onsite Comment -split from "Category/Performance: " take only title

            lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, 'div:nth-child(1)').text.split(':')[1]
            lot_details_data.lot_title_english =  GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
        # Onsite Field -Categoria/Prestazione
        # Onsite Comment -split from "Category/Performance: " take only number

            try:
                lot_details_data.lot_actual_number = single_record.find_element(By.CSS_SELECTOR, 'div:nth-child(1)').text.split(':')[1].split('-')[0]
            except Exception as e:
                logging.info("Exception in lot_number: {}".format(type(e).__name__))
                pass  
            
  
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
            lot_number += 1
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    

    try:              
        # Onsite Field -Atti e documenti (art.29 c.1 DLgs 50/2016)
        # Onsite Comment -None
        attachments_url = page_details.find_element(By.CSS_SELECTOR, 'div:nth-child(13) > ul > li > a').get_attribute("href")                     
        fn.load_page(page_details2,attachments_url,80)
            
        for single_record in page_details2.find_elements(By.CSS_SELECTOR, 'div.detail-section > div > ul > li'):
            attachments_data = attachments()
            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'a').text
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
page_details1 = fn.init_chrome_driver(arguments) 
page_details2 = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://appalti.provincia.foggia.it/PortaleAppalti/it/ppgare_doc_news.wp?_csrf=A2VE5KOAE2BMEG5YYPQQG87JBKNYLO7Z'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(1,5):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="ext-container"]/div/div/div/main/div/div/form/div'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="ext-container"]/div/div/div/main/div/div/form/div')))
                length = len(rows)
                for records in range(0,length-1):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="ext-container"]/div/div/div/main/div/div/form/div')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#pagination-navi > input.nav-button.nav-button-right')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="ext-container"]/div/div/div/main/div/div/form/div'),page_check))
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
    page_details1.quit()
    page_details2.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)
