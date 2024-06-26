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
SCRIPT_NAME = "de_bielefeld"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    try:
        notice_data.local_description = page_main.find_element(By.XPATH, '//*[contains(text(),"Art und Umfang der Leistung")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -1. take this url for "https://www.vergabe-westfalen.de/VMPSatellite/public/company/project/CXPWYDZLRMS/de/processdata?56" reference.   2.click on "Verfahrensangaben " to get lot_details in page_details.

    try:              
        for single_record in page_main.find_elements(By.CSS_SELECTOR, '#content > div'):
            lot_details_data = lot_details()
        # Onsite Field -Beschreibung >> Bezeichnung
        # Onsite Comment -1.if lot_title is not abailabel then take local_title as lot_title

            try:
                lot_details_data.lot_title = page_main.find_element(By.CSS_SELECTOR, 'fieldset > div:nth-child(2) > div > div > div > span').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Beschreibung >> Bezeichnung
        # Onsite Comment -1.if lot_title is not abailabel then take local_title as lot_description

            try:
                lot_details_data.lot_description = page_main.find_element(By.CSS_SELECTOR, 'fieldset > div:nth-child(2) > div > div > div > span').text
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -take this url for "https://www.vergabe-westfalen.de/VMPSatellite/public/company/project/CXPWYDZLRMS/de/processdata?56" reference.

            try:
                for single_record in page_main.find_elements(By.CSS_SELECTOR, '#content > div'):
                    lot_criteria_data = lot_criteria()
		
            # Onsite Field -Beschreibung >> Zuschlagskriterien
            # Onsite Comment -None

                    try:
                        lot_criteria_data.lot_criteria_title = page_main.find_element(By.CSS_SELECTOR, 'div:nth-child(1) > div:nth-child(1) > div > label > span.label-inside-label').text
                    except Exception as e:
                        logging.info("Exception in lot_criteria_title: {}".format(type(e).__name__))
                        pass
			
                    lot_criteria_data.lot_criteria_cleanup()
                    lot_details_data.lot_criteria.append(lot_criteria_data)
            except Exception as e:
                logging.info("Exception in lot_criteria: {}".format(type(e).__name__))
                pass
			
        # Onsite Field -None
        # Onsite Comment -None

            try:
                for single_record in page_main.find_elements(By.ID, '#content > div'):
                    award_details_data = award_details()
		
    # Onsite Field -None
    # Onsite Comment -in the give selector "td:nth-child(3) > div" if the keyword "Vergebener Auftrag" is present then take notice_type=7.if the "Beabsichtigte Ausschreibung" keyword is present then take notice_type=2. otherwise notice_type=4.
    notice_data.notice_type = 4
    
            # Onsite Field -Vergebene Aufträge >> Offizielle Bezeichnung
            # Onsite Comment -1.take bidder_name only if notice_type=7. 				2.refer this url "https://www.vergabe-westfalen.de/VMPSatellite/public/company/project/CXPWYDZLRM4/de/processdata?74"

                    try:
                        award_details_data.bidder_name = page_main.find_element(By.XPATH, '//*[contains(text(),"Offizielle Bezeichnung")]//following::div[1]').text
                    except Exception as e:
                        logging.info("Exception in bidder_name: {}".format(type(e).__name__))
                        pass
			
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
# Onsite Comment -Take attachments from page_details. also take attachments after clicking on "Vergabeunterlagen" in page_details.

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#content > div > div:nth-child(6)'):
            attachments_data = attachments()
        # Onsite Field -Dateiname
        # Onsite Comment -1.in file_name don't take file extension. eg., in "Bekanntmachung.pdf" take only "Bekanntmachung" in file_name. in page_main.	 			2.span:nth-child(14) > div > div > a		 take this attachments data  after clicking on "Vergabeunterlagen" in page_main.  			3.take only text

            try:
                attachments_data.file_name = page_details.find_element(By.CSS_SELECTOR, 'td.truncate-data-cell-nowrap').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Dateiname
        # Onsite Comment -1.in file_type don't take file name. eg., in "Bekanntmachung.pdf" take only "pdf" in file_type. 			2.take file_type for "attachments after clicking on "Vergabeunterlagen" in page_main" as static ".zip".

            try:
                attachments_data.file_type = page_details.find_element(By.CSS_SELECTOR, 'td.truncate-data-cell-nowrap').text
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Größe
        # Onsite Comment -None

            try:
                attachments_data.file_size = page_details.find_element(By.CSS_SELECTOR, 'div:nth-child(6) > div > table > tbody > tr > td:nth-child(3)').text
            except Exception as e:
                logging.info("Exception in file_size: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Aktion
        # Onsite Comment -1.span:nth-child(14) > div > div > a	take this also as external_url after clicking on "Vergabeunterlagen" in page_main.

            try:
                attachments_data.external_url = page_details.find_element(By.CSS_SELECTOR, 'td:nth-child(5) > a').get_attribute('href')
            except Exception as e:
                logging.info("Exception in external_url: {}".format(type(e).__name__))
                pass
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    # Onsite Field -None
    # Onsite Comment -1.to take eligibility click on "Verfahrensangaben" in page_details.	 	2.take this url for "https://www.vergabe-westfalen.de/VMPSatellite/public/company/project/CXPWYDZLRMS/de/processdata?56" reference.   	3.split eligibility between  "Technische und berufliche Leistungsfähigkeit" and "Sonstige".

    try:
        notice_data.eligibility = page_main.find_element(By.CSS_SELECTOR, '#content > div').text
    except Exception as e:
        logging.info("Exception in eligibility: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -1.click on "Verfahrensangaben " to get customer_details in page_details...

    try:              
        for single_record in page_main.find_elements(By.ID, '#content > div'):
            customer_details_data = customer_details()
            customer_details_data.org_country = 'DE'
            customer_details_data.org_language = 'DE'
        # Onsite Field -Auftraggeber >> Offizielle Bezeichnung
        # Onsite Comment -None

            try:
                customer_details_data.org_name = page_main.find_element(By.XPATH, '//*[contains(text(),"Offizielle Bezeichnung")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Auftraggeber >> Ort
        # Onsite Comment -None

            try:
                customer_details_data.org_city = page_main.find_element(By.XPATH, '//*[contains(text(),"Ort")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Auftraggeber >> Kontaktstelle
        # Onsite Comment -None

            try:
                customer_details_data.org_address = page_main.find_element(By.XPATH, '//*[contains(text(),"Kontaktstelle")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Auftraggeber >> Telefon
        # Onsite Comment -None

            try:
                customer_details_data.org_phone = page_main.find_element(By.XPATH, '//*[contains(text(),"Telefon")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Auftraggeber >> Fax
        # Onsite Comment -None

            try:
                customer_details_data.org_fax = page_main.find_element(By.XPATH, '//*[contains(text(),"Fax")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in org_fax: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Auftraggeber >> E-Mail
        # Onsite Comment -None

            try:
                customer_details_data.org_email = page_main.find_element(By.XPATH, '//*[contains(text(),"E-Mail")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Auftraggeber >> Postleitzahl
        # Onsite Comment -None

            try:
                customer_details_data.postal_code = page_main.find_element(By.XPATH, '//*[contains(text(),"Postleitzahl")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in postal_code: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Auftraggeber >> zu Händen von
        # Onsite Comment -None

            try:
                customer_details_data.contact_person = page_main.find_element(By.XPATH, '//*[contains(text(),"zu Händen von")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Auftraggeber >> NUTS Code
        # Onsite Comment -None

            try:
                customer_details_data.customer_nuts = page_main.find_element(By.XPATH, '//*[contains(text(),"NUTS Code")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in customer_nuts: {}".format(type(e).__name__))
                pass
        
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.script_name = 'de_bielefeld'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'DE'
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'DE'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'EUR'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -Veröffentlicht
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
    
    # Onsite Field -Frist
    # Onsite Comment -1.don't take notice_deadline for notice_type=7. 2. take notice_deadline as threshold date 1 year after the publish_date if notice_type=2.

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(2)").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Bezeichnung
    # Onsite Comment -take "VOB/A Vergebener Auftrag" in document_type_description only.split "VOB/A Vergebener Auftrag" and take only "Vergebener Auftrag".

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3) > div').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -take in text format

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3) > div > div > a').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Bezeichnung
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3) > div > div > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -Ausschreibungs-ID
    # Onsite Comment -None

    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"Ausschreibungs-ID")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.ID, '#content'):
            cpvs_data = cpvs()
        # Onsite Field -Auftragsgegenstand
        # Onsite Comment -while taking cpv take numeric value before "-". eg., in "45233120-6" take only "45233120".

            try:
                cpvs_data.cpv_code = page_details.find_element(By.CSS_SELECTOR, 'div.control-group > p > b').text
            except Exception as e:
                logging.info("Exception in cpv_code: {}".format(type(e).__name__))
                pass
        
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.ID, '#content').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Vergabeart:
    # Onsite Comment -None
    try:
        notice_data.type_of_procedure_actual = page_details.find_element(By.CSS_SELECTOR, "td:nth-child(5) > span:nth-child(2)").text
        notice_data.type_of_procedure = fn.procedure_mapping("assets/de_bielefeld_procedure.csv",notice_data.type_of_procedure_actual)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -1.click on "Verfahrensangaben " to get tender_criteria in page_details. 			2.take this url for "https://www.vergabe-westfalen.de/VMPSatellite/public/company/project/CXPWYDZLRMS/de/processdata?56" reference.

    try:              
        for single_record in page_main.find_elements(By.ID, '#content > div'):
            tender_criteria_data = tender_criteria()
        # Onsite Field -Auftragsgegenstand >> Zuschlagskriterien
        # Onsite Comment -tender_criteria_title split after "Kriterium"

            try:
                tender_criteria_data.tender_criteria_title = page_main.find_element(By.CSS_SELECTOR, 'tr:nth-child(2) > td:nth-child(1)').text
            except Exception as e:
                logging.info("Exception in tender_criteria_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Auftragsgegenstand >> Zuschlagskriterien
        # Onsite Comment -tender_criteria_weight split after "Gewichtung"

            try:
                tender_criteria_data.tender_criteria_weight = page_main.find_element(By.CSS_SELECTOR, 'tr:nth-child(2) > td:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in tender_criteria_weight: {}".format(type(e).__name__))
                pass
        
            tender_criteria_data.tender_criteria_cleanup()
            notice_data.tender_criteria.append(tender_criteria_data)
    except Exception as e:
        logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
        pass
    
    # Onsite Field -Auftragsgegenstand >> Art und Umfang der Leistung
    # Onsite Comment -click on "Verfahrensangaben " to get notice_summary_english.

    try:
        notice_data.notice_summary_english = page_main.find_element(By.XPATH, '//*[contains(text(),"Art und Umfang der Leistung")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
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
    urls = ["https://www.bielefeld.de/bekanntmachungen/ausschreibungen"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,1):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'tbody > tr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'tbody > tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'tbody > tr')))[records]
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'tbody > tr'),page_check))
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