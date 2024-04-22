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
SCRIPT_NAME = "it_trascultura_ca"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"





# for explore the CA details go to url : 1) "https://trasparenza.cultura.gov.it/pagina960_affidamenti-diretti-di-lavori-servizi-e-forniture-di-somma-urgenza-e-di-protezione-civile.html"
#                                        2) scroll down the page 
# 
#                           ref urls :   1) "https://trasparenza.cultura.gov.it/archivio11_bandi-gare-e-contratti_0_155119_960_1.html"
#                                        2) "https://trasparenza.cultura.gov.it/archivio11_bandi-gare-e-contratti_0_156642_960_1.html"

# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------




def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.script_name = 'it_trascultura_ca'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'IT'
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'EUR'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_type = 7
    
    # Onsite Field -OGGETTO
    # Onsite Comment -split the data from tender_html_page

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(1) > a').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -CIG
    # Onsite Comment -split the data from tender_html_page

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(2) > div').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Data di pubblicazione
    # Onsite Comment -split the data from tender_html_page

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "tr > td:nth-child(4) > div").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    try:
        notice_data.local_description = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(1) > a').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -OGGETTO
    # Onsite Comment -split the data from tender_html_page

    try:
        notice_data.notice_summary_english = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(1) > a').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -document_type_description for notice_type = 7
    notice_data.document_type_description = '"Affidamenti diretti di lavori, servizi e forniture di somma urgenza e di protezione civile"'
    
    # Onsite Field -OGGETTO
    # Onsite Comment -inspect url for details page , ref url : "https://trasparenza.cultura.gov.it/archivio11_bandi-gare-e-contratti_0_155254_960_1.html"

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(1) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#reviewOggetto > div > div').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
# Onsite Field -None
# Onsite Comment -scroll down and split the data from detail page

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#reviewOggetto > div > div'):
            customer_details_data = customer_details()
        # Onsite Field -Ufficio:
        # Onsite Comment -split the data between "Importo di aggiudicazione" and "RUP:" field, url ref : "https://trasparenza.cultura.gov.it/archivio11_bandi-gare-e-contratti_0_155119_960_1.html"

            try:
                customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Ufficio: ")]//following::a[1]').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
            customer_details_data.org_country = 'IT'
            customer_details_data.org_language = 'IT'
        # Onsite Field -RUP:
        # Onsite Comment -split the data between "Ufficio" and "Data dell'atto" field, url ref : "https://trasparenza.cultura.gov.it/archivio11_bandi-gare-e-contratti_0_156154_960_1.html"

            try:
                customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"RUP: ")]//following::a[1]').text
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass
        
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#reviewOggetto > div > div'):
            lot_details_data = lot_details()
        # Onsite Field -OGGETTO
        # Onsite Comment -None

            try:
                lot_details_data.lot_title = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(1) > a').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Data di effettivo inizio dei lavori o forniture
        # Onsite Comment -split the following data from this field, ref url :  "https://trasparenza.cultura.gov.it/archivio11_bandi-gare-e-contratti_0_156642_960_1.html"

            try:
                lot_details_data.contract_start_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Tempi di completamento dell")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in contract_start_date: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Data di ultimazione dei lavori o forniture
        # Onsite Comment -split the following data from this field, ref url :  "https://trasparenza.cultura.gov.it/archivio11_bandi-gare-e-contratti_0_156642_960_1.html"

            try:
                lot_details_data.contract_end_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Tempi di completamento dell")]//following::div[2]').text
            except Exception as e:
                logging.info("Exception in contract_end_date: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -None

            try:
                for single_record in page_details.find_elements(By.CSS_SELECTOR, '#reviewOggetto > div > div'):
                    award_details_data = award_details()
		
                    # Onsite Field -Aggiudicatari
                    # Onsite Comment -ref url : "https://trasparenza.cultura.gov.it/archivio11_bandi-gare-e-contratti_0_155119_960_1.html"

                    award_details_data.bidder_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Aggiudicatari")]//following::li[1]').text
			
                    # Onsite Field -Importo di aggiudicazione
                    # Onsite Comment -split the following data from "Importo di aggiudicazione" field,  ref url : "https://trasparenza.cultura.gov.it/archivio11_bandi-gare-e-contratti_0_155419_960_1.html"

                    award_details_data.grossawardvaluelc = page_details.find_element(By.XPATH, '//*[contains(text(),"Importi")]//following::div[2]').text
			
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
    
# Onsite Field -Allegati
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#reviewOggetto > div > div'):
            attachments_data = attachments()
        # Onsite Field -Allegati
        # Onsite Comment -split file_type such as "pdf, xlsx" data from this xpath, ref url : "https://trasparenza.cultura.gov.it/archivio11_bandi-gare-e-contratti_0_155119_960_1.html"

            try:
                attachments_data.file_type = page_details.find_element(By.XPATH, '//*[contains(text(),"Allegati")]//following::a').text
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Allegati
        # Onsite Comment -split only file_name i.e (data before the extension) from this xpath , ref url : "https://trasparenza.cultura.gov.it/archivio11_bandi-gare-e-contratti_0_155119_960_1.html"

            try:
                attachments_data.file_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Allegati")]//following::a').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Allegati
        # Onsite Comment -split all the data from "Allegati" section,

            try:
                attachments_data.file_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Allegati")]//following::div').text
            except Exception as e:
                logging.info("Exception in file_description: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Allegati
        # Onsite Comment -split file_size. eg.,"(Pubblicato il 17/07/2023 - Aggiornato il 17/07/2023 - 1248 kb - pdf)" here take only "1248 kb" in file_size., url ref : "https://trasparenza.cultura.gov.it/archivio11_bandi-gare-e-contratti_0_155119_960_1.html"

            try:
                attachments_data.file_size = page_details.find_element(By.XPATH, '//*[contains(text(),"Allegati")]//following::span').text
            except Exception as e:
                logging.info("Exception in file_size: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Allegati
        # Onsite Comment -None

            attachments_data.external_url = page_details.find_element(By.XPATH, '//*[contains(text(),"Allegati")]//following::a[1]').get_attribute('href')
            
        
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
page_main = fn.init_chrome_driver(arguments) 
page_details = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://trasparenza.cultura.gov.it/pagina960_affidamenti-diretti-di-lavori-servizi-e-forniture-di-somma-urgenza-e-di-protezione-civile.html"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,"https://trasparenza.cultura.gov.it/pagina960_affidamenti-diretti-di-lavori-servizi-e-forniture-di-somma-urgenza-e-di-protezione-civile.html"):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="regola_default"]/div[2]/div/section/div[2]//tbody/tr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="regola_default"]/div[2]/div/section/div[2]//tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="regola_default"]/div[2]/div/section/div[2]//tbody/tr')))[records]
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="regola_default"]/div[2]/div/section/div[2]//tbody/tr'),page_check))
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