#ref URL = "https://plattform.aumass.de/Publication/TenderPreviewQrCode?id=0bb12ee6-e574-425c-9227-952328361f34", 
#ref URL = "https://plattform.aumass.de/Publication/TenderPreviewQrCode?id=961f8844-5885-453a-ab1a-1b347cbcfd41",
#ref URL = "https://plattform.aumass.de/Publication/TenderPreviewQrCode?id=9dde0154-1de6-40a4-b709-ac7906cada04"

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
SCRIPT_NAME = "de_aumass"
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
    notice_data.script_name = 'de_aumass'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'EUR'
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'DE'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'DE'
    
    # Onsite Field -Veröffentlichungsdatum
    # Onsite Comment -None

    try:
        publish_date = page_details.find_element(By.XPATH, "//*[contains(text(),'Veröffentlichungsdatum')]//following::td[1]").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Verfahren
    # Onsite Comment -None

    try:
        notice_data.type_of_procedure_actual = tender_html_element.find_element(By.CSS_SELECTOR, '#page div > div:nth-child(5)').text
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -aumass-Id
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, '#page div > div:nth-child(1)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Projekt
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, '#page div > div:nth-child(2)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Kurztext
    # Onsite Comment -None

    try:
        notice_data.notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),'Kurztext')]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),'Kurztext')]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -ref url "https://plattform.aumass.de/Publication/TenderPreviewQrCode?id=7a243b29-ecc8-4702-a093-a8126f00418e#bidderQuestionTab"

    try:
        notice_data.document_type_description = page_details.find_element(By.CSS_SELECTOR, 'section:nth-child(2) > fieldset > h2').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -offer period
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "#page div > div:nth-child(4)").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Angaben zu Mitteln der Europäischen Union
    # Onsite Comment -ref url "https://plattform.aumass.de/Publication/TenderPreviewQrCode?id=961f8844-5885-453a-ab1a-1b347cbcfd41"

    try:
        notice_data.funding_agencies = page_details.find_element(By.XPATH, '//*[contains(text(),'Europäischen Union')]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in funding_agencies: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -inspect url for detail page
    # Onsite Comment -None

    try:
        notice_data.notice_url = page_details.find_element(By.XPATH, '#page div > div:nth-child(6)').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#content > div'):
            customer_details_data = customer_details()
        # Onsite Field -Auftraggeber
        # Onsite Comment -ref url="https://plattform.aumass.de/Publication/TenderPreviewQrCode?id=961f8844-5885-453a-ab1a-1b347cbcfd41"

            try:
                customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),'Auftraggeber')]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Postanschrift:
        # Onsite Comment -ref url="https://plattform.aumass.de/Publication/TenderPreviewQrCode?id=961f8844-5885-453a-ab1a-1b347cbcfd41"

            try:
                customer_details_data.org_address = page_details.find_element(By.CSS_SELECTOR, '#AbschnitteI1_0__Postanschrift').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Anschrift
        # Onsite Comment -ref url="https://plattform.aumass.de/Publication/TenderPreviewQrCode?id=961f8844-5885-453a-ab1a-1b347cbcfd41"

            try:
                customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),'Anschrift')]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Postleitzahl
        # Onsite Comment -ref url="https://plattform.aumass.de/Publication/TenderPreviewQrCode?id=961f8844-5885-453a-ab1a-1b347cbcfd41"

            try:
                customer_details_data.postal_code = page_details.find_element(By.XPATH, '//*[contains(text(),'Postleitzahl')]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in postal_code: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Postleitzahl
        # Onsite Comment -ref URL=  "https://plattform.aumass.de/Publication/TenderPreviewQrCode?id=8a838d63-be73-4a27-bb5c-958a221ce74e"

            try:
                customer_details_data.postal_code = page_details.find_element(By.CSS_SELECTOR, '#AbschnitteI1_0__Postleitzahl').text
            except Exception as e:
                logging.info("Exception in postal_code: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Telefon
        # Onsite Comment -ref URL=  "https://plattform.aumass.de/Publication/TenderPreviewQrCode?id=8a838d63-be73-4a27-bb5c-958a221ce74e"

            try:
                customer_details_data.org_phone = page_details.find_element(By.CSS_SELECTOR, '#AbschnitteI1_0__Telefon').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Telefon
        # Onsite Comment -ref URL= "https://plattform.aumass.de/Publication/TenderPreviewQrCode?id=8a838d63-be73-4a27-bb5c-958a221ce74e"

            try:
                customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),'Telefon:')]').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Fax:
        # Onsite Comment -ref URL = "https://plattform.aumass.de/Publication/TenderPreviewQrCode?id=8a838d63-be73-4a27-bb5c-958a221ce74e"

            try:
                customer_details_data.org_fax = page_details.find_element(By.CSS_SELECTOR, '#AbschnitteI1_0__Fax').text
            except Exception as e:
                logging.info("Exception in org_fax: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Fax:
        # Onsite Comment -ref URL = "https://plattform.aumass.de/Publication/TenderPreviewQrCode?id=961f8844-5885-453a-ab1a-1b347cbcfd41"

            try:
                customer_details_data.org_fax = page_details.find_element(By.XPATH, '//*[contains(text(),'Fax')]').text
            except Exception as e:
                logging.info("Exception in org_fax: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Email
        # Onsite Comment -ref URL = "https://plattform.aumass.de/Publication/TenderPreviewQrCode?id=961f8844-5885-453a-ab1a-1b347cbcfd41"

            try:
                customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),'Email')]').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Email
        # Onsite Comment -ref URL = "https://plattform.aumass.de/Publication/TenderPreviewQrCode?id=8a838d63-be73-4a27-bb5c-958a221ce74e"

            try:
                customer_details_data.org_email = page_details.find_element(By.CSS_SELECTOR, '#AbschnitteI1_0__EMail').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Nuts:
        # Onsite Comment -ref URL = "https://plattform.aumass.de/Publication/TenderPreviewQrCode?id=8a838d63-be73-4a27-bb5c-958a221ce74e"

            try:
                customer_details_data.customer_nuts = page_details.find_element(By.XPATH, '//*[contains(text(),'NUTS-Code')]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in customer_nuts: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -ref URL = "https://plattform.aumass.de/Publication/TenderPreviewQrCode?id=8a838d63-be73-4a27-bb5c-958a221ce74e"

            try:
                customer_details_data.contract_start_date = page_details.find_element(By.CSS_SELECTOR, 'fieldset.row.row_ii_2_7 > div:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in contract_start_date: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -ref URL = "https://plattform.aumass.de/Publication/TenderPreviewQrCode?id=8a838d63-be73-4a27-bb5c-958a221ce74e"

            try:
                customer_details_data.contract_end_date = page_details.find_element(By.CSS_SELECTOR, 'fieldset.row.row_ii_2_7 > div:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in contract_end_date: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -ref URL = "https://plattform.aumass.de/Publication/TenderPreviewQrCode?id=0bb12ee6-e574-425c-9227-952328361f34"

            try:
                customer_details_data.contract_start_date = page_details.find_element(By.XPATH, '//*[contains(text(),'Beginn der Ausführung')]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in contract_start_date: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -ref URL = "https://plattform.aumass.de/Publication/TenderPreviewQrCode?id=0bb12ee6-e574-425c-9227-952328361f34"

            try:
                customer_details_data.contract_end_date = page_details.find_element(By.XPATH, '//*[contains(text(),'Fertigstellung der Leistungen')]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in contract_end_date: {}".format(type(e).__name__))
                pass
        
            customer_details_data.org_country = 'DE'
            customer_details_data.org_language = 'DE'
        # Onsite Field -Ausführungsort
        # Onsite Comment -None

            try:
                customer_details_data.org_city = tender_html_element.find_element(By.CSS_SELECTOR, '#page div > div:nth-child(3)').text
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass
        
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += tender_html_element.find_element(By.CSS_SELECTOR, '#content > div').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#content > div'):
            lot_details_data = lot_details()
        # Onsite Field -None
        # Onsite Comment -ref url "https://plattform.aumass.de/Publication/TenderPreviewQrCode?id=8a838d63-be73-4a27-bb5c-958a221ce74e"

            try:
                lot_details_data.lot_number = page_details.find_element(By.XPATH, '//*[contains(text(),'Los-Nr')]').text
            except Exception as e:
                logging.info("Exception in lot_number: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -ref url "https://plattform.aumass.de/Publication/TenderPreviewQrCode?id=8a838d63-be73-4a27-bb5c-958a221ce74e"

            try:
                lot_details_data.lot_title = page_details.find_element(By.XPATH, '//*[contains(text(),'Bezeichnung des Auftrags:')]').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -ref url "https://plattform.aumass.de/Publication/TenderPreviewQrCode?id=8a838d63-be73-4a27-bb5c-958a221ce74e"

            try:
                lot_details_data.lot_title = page_details.find_element(By.XPATH, '//*[contains(text(),'Titel')]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -ref url "https://plattform.aumass.de/Publication/TenderPreviewQrCode?id=8a838d63-be73-4a27-bb5c-958a221ce74e"

            try:
                lot_details_data.lot_description = page_details.find_element(By.XPATH, '//*[contains(text(),'Titel')]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -ref url "https://plattform.aumass.de/Publication/TenderPreviewQrCode?id=8a838d63-be73-4a27-bb5c-958a221ce74e"

            try:
                lot_details_data.lot_description = page_details.find_element(By.XPATH, '//*[contains(text(),'Beschreibung der Beschaffung')]').text
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -ref URL = "https://plattform.aumass.de/Publication/TenderPreviewQrCode?id=8a838d63-be73-4a27-bb5c-958a221ce74e"

            try:
                lot_details_data.lot_nuts = page_details.find_element(By.XPATH, '//*[contains(text(),'NUTS-Code:')]').text
            except Exception as e:
                logging.info("Exception in lot_nuts: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -ref URL = "https://plattform.aumass.de/Publication/TenderPreviewQrCode?id=8a838d63-be73-4a27-bb5c-958a221ce74e"

            try:
                for single_record in page_details.find_elements(By.CSS_SELECTOR, '#content > div'):
                    lot_cpvs_data = lot_cpvs()
		
                    # Onsite Field -None
                    # Onsite Comment -ref URL = "https://plattform.aumass.de/Publication/TenderPreviewQrCode?id=8a838d63-be73-4a27-bb5c-958a221ce74e"

                    lot_cpvs_data.lot_cpv_code = page_details.find_element(By.CSS_SELECTOR, '//*[contains(text(),'CPV-Code Hauptteil')]').text
			
                    lot_cpvs_data.lot_cpvs_cleanup()
                    lot_details_data.lot_cpvs.append(lot_cpvs_data)
            except Exception as e:
                logging.info("Exception in lot_cpvs: {}".format(type(e).__name__))
                pass


         # Onsite Field -("Dienstleistung" = service , "Lieferleistung"  = supply,"Bauleistung" = work)
        # Onsite Comment -ref URL = "https://plattform.aumass.de/Publication/TenderPreviewQrCode?id=961f8844-5885-453a-ab1a-1b347cbcfd41"

            try:
                lot_details_data.contract_type = page_details.find_element(By.XPATH, '//*[contains(text(),'II.1.3) Art des Auftrags')]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in contract_type: {}".format(type(e).__name__))
                pass
        
			
        # Onsite Field -None
        # Onsite Comment -None

            try:
                lot_details_data.lot_nuts = page_details.find_element(By.XPATH, '//*[contains(text(),'NUTS-Code')]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in lot_nuts: {}".format(type(e).__name__))
                pass
        
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#content > div'):
            cpvs_data = cpvs()
        # Onsite Field -II.1.2) CPV
        # Onsite Comment -ref URL = "https://plattform.aumass.de/Publication/TenderPreviewQrCode?id=8a838d63-be73-4a27-bb5c-958a221ce74e"

            try:
                cpvs_data.cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),'II.1.2) CPV')]//following::div[2]').text
            except Exception as e:
                logging.info("Exception in cpv_code: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -CPV
        # Onsite Comment -ref URL = "https://plattform.aumass.de/Publication/TenderPreviewQrCode?id=9dde0154-1de6-40a4-b709-ac7906cada04" ,   ref URL = "https://plattform.aumass.de/Publication/TenderPreviewQrCode?id=0bb12ee6-e574-425c-9227-952328361f34"

            try:
                cpvs_data.cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),'CPV')]//following::td[42]').text
            except Exception as e:
                logging.info("Exception in cpv_code: {}".format(type(e).__name__))
                pass
        
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -ref url "https://plattform.aumass.de/Publication/TenderPreviewQrCode?id=961f8844-5885-453a-ab1a-1b347cbcfd41"

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#content > div'):
            tender_criteria_data = tender_criteria()
        # Onsite Field -None
        # Onsite Comment -ref URL = "https://plattform.aumass.de/Publication/TenderPreviewQrCode?id=961f8844-5885-453a-ab1a-1b347cbcfd41"

            try:
                tender_criteria_data.tender_criteria_title = page_details.find_element(By.XPATH, '//*[contains(text(),'II.2.5) Award criteria')]//following::div[3]').text
            except Exception as e:
                logging.info("Exception in tender_criteria_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -ref URL = "https://plattform.aumass.de/Publication/TenderPreviewQrCode?id=961f8844-5885-453a-ab1a-1b347cbcfd41"

            try:
                tender_criteria_data.tender_criteria_weight = page_details.find_element(By.XPATH, '//*[contains(text(),'II.2.5) Award criteria')]//following::div[3]').text
            except Exception as e:
                logging.info("Exception in tender_criteria_weight: {}".format(type(e).__name__))
                pass
        
            tender_criteria_data.tender_criteria_cleanup()
            notice_data.tender_criteria.append(tender_criteria_data)
    except Exception as e:
        logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.XPATH, '//*[contains(text(),'Vergabeunterlagen')]//following::div[3]'):
            attachments_data = attachments()
        # Onsite Field -None
        # Onsite Comment -ref URL = "https://plattform.aumass.de/Publication/TenderPreviewQrCode?id=961f8844-5885-453a-ab1a-1b347cbcfd41"

            try:
                attachments_data.file_type = page_details.find_element(By.XPATH, '//*[contains(text(),'Vergabeunterlagen')]//following::div[3]').text
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -ref URL = "https://plattform.aumass.de/Publication/TenderPreviewQrCode?id=0bb12ee6-e574-425c-9227-952328361f34"

            try:
                attachments_data.file_type = page_details.find_element(By.XPATH, '//*[contains(text(),'Vergabeunterlagen')]//following::div[3]').text
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -ref URL = "https://plattform.aumass.de/Publication/TenderPreviewQrCode?id=0bb12ee6-e574-425c-9227-952328361f34"

            try:
                attachments_data.file_name = page_details.find_element(By.XPATH, '//*[contains(text(),'Vergabeunterlagen')]//following::div[3]').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -ref URL = "https://plattform.aumass.de/Publication/TenderPreviewQrCode?id=961f8844-5885-453a-ab1a-1b347cbcfd41"

            try:
                attachments_data.file_name = page_details.find_element(By.XPATH, '//*[contains(text(),'Vergabeunterlagen')]//following::div[3]').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Download
        # Onsite Comment -None

            attachments_data.external_url = page_details.find_element(By.CSS_SELECTOR, '#fileData > div > div > a').get_attribute('href')
            
        
        # Onsite Field -Dateigröße
        # Onsite Comment -ref url "https://plattform.aumass.de/Publication/TenderPreviewQrCode?id=0bb12ee6-e574-425c-9227-952328361f34"

            try:
                attachments_data.file_size = page_details.find_element(By.XPATH, '//*[contains(text(),'Vergabeunterlagen')]//following::div[3]').text
            except Exception as e:
                logging.info("Exception in file_size: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Dateigröße
        # Onsite Comment -ref url "https://plattform.aumass.de/Publication/TenderPreviewQrCode?id=cf7cd1eb-4d81-4acf-a442-fc94bd028470"

            try:
                attachments_data.file_size = page_details.find_element(By.XPATH, '//*[contains(text(),'Vergabeunterlagen')]//following::div[3]').text
            except Exception as e:
                logging.info("Exception in file_size: {}".format(type(e).__name__))
                pass
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    # Onsite Field -("Dienstleistung" = service , "Lieferleistung"  = supply,"Bauleistung" = work)
    # Onsite Comment -ref URL = "https://plattform.aumass.de/Publication/TenderPreviewQrCode?id=961f8844-5885-453a-ab1a-1b347cbcfd41"

    try:
        notice_data.notice_contract_type = page_details.find_element(By.XPATH, '//*[contains(text(),'II.1.3) Art des Auftrags')]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    

    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title) 
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
    urls = ['https://www.aumass.de/ausschreibungen?params='] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,10):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/section/main/div[4]/div[1]/div[2]/div[14]/a'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/section/main/div[4]/div[1]/div[2]/div[14]/a')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/section/main/div[4]/div[1]/div[2]/div[14]/a')))[records]
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/section/main/div[4]/div[1]/div[2]/div[14]/a'),page_check))
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
    