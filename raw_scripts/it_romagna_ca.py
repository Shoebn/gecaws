
from gec_common.gecclass import *
import logging
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
import functions as fn
from functions import ET
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "it_romagna_ca"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.script_name = 'it_romagna_ca'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'IT'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'EUR'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -for "Rinnovi ed estensioni" keyword take notice type 16
    # Onsite Comment -ref url "https://intercenter.regione.emilia-romagna.it/servizi-pa/convenzioni/convenzioni-attive/2023/fattore-viii-2023-2013-2025-esclusivi"
    notice_data.notice_type = 7
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -Data di attivazione
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(2) > div").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Convenzioni
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Durata degli Ordinativi
    # Onsite Comment -take the following data from where the  xpath is been selected

    try:
        notice_data.contract_duration = page_details.find_element(By.XPATH, '//*[contains(text(),'Durata degli Ordinativi')]').text
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -Convenzioni

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#portal-column-content > div').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
# Onsite Field -None
# Onsite Comment -for format 2 : "https://intercenter.regione.emilia-romagna.it/servizi-pa/convenzioni/convenzioni-attive/2023/servizi-di-collaudo-per-le-aziende-sanitarie-rer-per-interventi-pnrr"  use selector "//*[contains(text(),'Referente amministrativo')]"

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#portal-column-content > div'):
            customer_details_data = customer_details()
        # Onsite Field -
        # Onsite Comment -take the following data from where the xpath is been selected 

            try:
                customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),'Destinatari')]').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
            customer_details_data.org_language = 'IT'
        # Onsite Field - ref url - "https://intercenter.regione.emilia-romagna.it/servizi-pa/convenzioni/convenzioni-attive/2022/aghi-per-anestesia"
        # Onsite Comment -split data from"Referenti amministrativi:"till "tel"

            try:
                customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),'Referenti amministrativi:')]//following::li[1]').text
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass
        
        # Onsite Field - ref url - "https://intercenter.regione.emilia-romagna.it/servizi-pa/convenzioni/convenzioni-attive/2022/aghi-per-anestesia"
        # Onsite Comment -split data from"tel" till "e-mail"

            try:
                customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),'Referenti amministrativi:')]//following::li').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
        
        # Onsite Field - ref url - "https://intercenter.regione.emilia-romagna.it/servizi-pa/convenzioni/convenzioni-attive/2022/aghi-per-anestesia"
        # Onsite Comment -split data from"e-mail"

            try:
                customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),'Referenti amministrativi:')]//following::li').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
        
            customer_details_data.org_country = 'IT'
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -ref url : "https://intercenter.regione.emilia-romagna.it/servizi-pa/convenzioni/convenzioni-attive/2023/medicinali-biologici-e-biosimilari-esclusivi-2023-2024/medicinali-biologici-e-biosimilari-esclusivi-2023-2024"
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#content-core > div.content-text'):
            lot_details_data = lot_details()
        # Onsite Field -ref url : "https://intercenter.regione.emilia-romagna.it/servizi-pa/convenzioni/convenzioni-attive/2023/medicinali-biologici-e-biosimilari-esclusivi-2023-2024/medicinali-biologici-e-biosimilari-esclusivi-2023-2024"
        # Onsite Comment -None

            try:
                lot_details_data.lot_title = page_details.find_element(By.CSS_SELECTOR, '#content-core td:nth-child(1)').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        

        # Onsite Field -Repertoire number
        # Onsite Comment -ref url : "https://intercenter.regione.emilia-romagna.it/servizi-pa/convenzioni/convenzioni-attive/2023/medicinali-biologici-e-biosimilari-esclusivi-2023-2024/medicinali-biologici-e-biosimilari-esclusivi-2023-2024"

            try:
                lot_details_data.lot_actual_number = page_details.find_element(By.CSS_SELECTOR, '#content-core td:nth-child(5)').text
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -None

            try:
                for single_record in page_details.find_elements(By.CSS_SELECTOR, '#content-core > div.content-text'):
                    award_details_data = award_details()
		
                    # Onsite Field -Fornitore
                    # Onsite Comment -None

                    award_details_data.bidder_name = page_details.find_element(By.CSS_SELECTOR, '#content-core td:nth-child(4)').text
			
                    # Onsite Field -Data scadenza
                    # Onsite Comment -None

                    award_details_data.award_date = page_details.find_element(By.CSS_SELECTOR, '#content-core td:nth-child(3)').text
			
                    award_details_data.award_details_cleanup()
                    lot_details_data.award_details.append(award_details_data)
            except Exception as e:
                logging.info("Exception in award_details: {}".format(type(e).__name__))
                pass
			
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    

# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#content-core > div.content-text'):
            attachments_data = attachments()
        # Onsite Field -Referenti aggiudicatari
        # Onsite Comment -None

            attachments_data.external_url = page_details.find_element(By.XPATH, '//*[contains(text(),'Referenti aggiudicatari')]//following::a[1]').get_attribute('href')
            
        
        # Onsite Field -Referenti aggiudicatari
        # Onsite Comment -None

            try:
                attachments_data.file_size = page_details.find_element(By.XPATH, '//*[contains(text(),'Referenti aggiudicatari')]//following::a[1]').text
            except Exception as e:
                logging.info("Exception in file_size: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Referenti aggiudicatari
        # Onsite Comment -None

            try:
                attachments_data.file_name = page_details.find_element(By.XPATH, '//*[contains(text(),'Referenti aggiudicatari')]//following::a[1]').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Referenti aggiudicatari
        # Onsite Comment -None

            try:
                attachments_data.file_type = page_details.find_element(By.XPATH, '//*[contains(text(),'Referenti aggiudicatari')]//following::a[1]').text
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    


    #format 3 : https://intercenter.regione.emilia-romagna.it/servizi-pa/convenzioni/convenzioni-attive/2023/servizi-di-collaudo-per-le-aziende-sanitarie-rer-per-interventi-pnrr
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, ' div.subfolders-wrapper > div:nth-child(1) > ul > li'):
            attachments_data = attachments()
        # Onsite Field -None
        # Onsite Comment -None

            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'div.subfolders-wrapper > div:nth-child(1) > ul > li > a').get_attribute('href')
            
        
        
        # Onsite Field -None
        # Onsite Comment -None

            try:
                attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'div.subfolders-wrapper > div:nth-child(1) > ul > li > a').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -None

            try:
                attachments_data.file_type = single_record.find_element(By.CSS_SELECTOR, 'div.subfolders-wrapper > div:nth-child(1) > ul > li > a').text
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) + str(notice_data.publish_date) +  str(notice_data.notice_url) 
    duplicate_check_data = fn.duplicate_check_data_from_previous_scraping(SCRIPT_NAME,MAX_NOTICES_DUPLICATE,notice_data.identifier,previous_scraping_log_check)
    NOTICE_DUPLICATE_COUNT = duplicate_check_data[1]
    if duplicate_check_data[0] == False:
        return
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_details = fn.init_chrome_driver(arguments) 
page_main = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://intercenter.regione.emilia-romagna.it/servizi-pa/convenzioni/convenzioni-attive"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,10):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="parent-fieldname-text"]/table/tbody/tr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="parent-fieldname-text"]/table/tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="parent-fieldname-text"]/table/tbody/tr')))[records]
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
                next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                page_main.execute_script("arguments[0].click();",next_page)
                logging.info("Next page")
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="parent-fieldname-text"]/table/tbody/tr'),page_check))
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
    page_details.quit() 
    
    output_json_file.copyFinalJSONToServer(output_json_folder)
    