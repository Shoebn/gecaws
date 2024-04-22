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
SCRIPT_NAME = "de_ever"
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
    notice_data.script_name = 'de_ever'
    
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
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_type = 4
    
    # Onsite Field -Bezeichnung
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Bezeichnung
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1) > div > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#content > main').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    # Onsite Field -Kurze Beschreibung
    # Onsite Comment -if the "Kurze Beschreibung" field is not available pass the local_title in notice_summary_english

    try:
        notice_data.notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),"Kurze Beschreibung")]//following::p').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Kurze Beschreibung")]//following::p').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Veröffentlichungsdatum:
    # Onsite Comment -None

    try:
        publish_date = page_details.find_element(By.XPATH, "//*[contains(text(),"Veröffentlichungsdatum:")]//following::span[1]").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Abgabefrist Angebot:
    # Onsite Comment -None

    try:
        notice_deadline = page_details.find_element(By.XPATH, "//*[contains(text(),"Abgabefrist Angebot:")]//following::span[1]").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Verfahrensart
    # Onsite Comment -None
    try:
        notice_data.type_of_procedure_actual = page_details.find_element(By.XPATH, "//*[contains(text(),"Verfahrensart")]//following::span[1]").text
        notice_data.type_of_procedure = fn.procedure_mapping("assets/de_ever_procedure",notice_data.type_of_procedure_actual)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Vertragsart
    # Onsite Comment -'//*[contains(text(),"Art des Auftrags")]//following::div[1]' use both this selectors and  Replace following keywords with given respective keywords ('Dienstleistungen=Services','Bauauftrag= works','Lieferauftrag= supply')

    try:
        notice_data.notice_contract_type = page_details.find_element(By.XPATH, '//*[contains(text(),"Vertragsart")]//following::span[1]').text
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Tag der Absendung dieser Bekanntmachung
    # Onsite Comment -None

    try:
        notice_data.dispatch_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Tag der Absendung dieser Bekanntmachung")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in dispatch_date: {}".format(type(e).__name__))
        pass
    
# Onsite Field -Namen und Adressen/Hauptauftraggeber (zur Angebotsabgabe auffordernde Stelle)
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#content > main'):
            customer_details_data = customer_details()
        # Onsite Field -Name:
        # Onsite Comment -'//*[contains(text(),"Offizielle Bezeichnung:")]//following::span[1]'-"Offizielle Bezeichnung:" use both this selectors

            try:
                customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Name:")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Postanschrift:
        # Onsite Comment -'//*[contains(text(),"Straße, Hausnummer:")]//following::span[1]'-"Straße, Hausnummer:" use both this selectors

            try:
                customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Postanschrift:")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Land:
        # Onsite Comment -None

            try:
                customer_details_data.org_city = page_details.find_element(By.XPATH, '//*[contains(text(),"Land:")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Postleitzahl:
        # Onsite Comment -'//*[contains(text(),"Postleitzahl (PLZ):")]//following::span[1]'-"Postleitzahl (PLZ):" use both this selectors

            try:
                customer_details_data.postal_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Postleitzahl:")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in postal_code: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -E-Mail:
        # Onsite Comment -None

            try:
                customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"E-Mail:")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Fax:
        # Onsite Comment -None

            try:
                customer_details_data.org_fax = page_details.find_element(By.XPATH, '//*[contains(text(),"Fax:")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in org_fax: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Hauptadresse:
        # Onsite Comment -None

            try:
                customer_details_data.org_website = page_details.find_element(By.XPATH, '//*[contains(text(),"Hauptadresse:")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in org_website: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -NUTS:
        # Onsite Comment -None

            try:
                customer_details_data.customer_nuts = page_details.find_element(By.XPATH, '//*[contains(text(),"NUTS:")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in customer_nuts: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Haupttätigkeit(en)
        # Onsite Comment -None

            try:
                customer_details_data.customer_main_activity = page_details.find_element(By.XPATH, '//*[contains(text(),"Haupttätigkeit(en)")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in customer_main_activity: {}".format(type(e).__name__))
                pass
        
            customer_details_data.org_country = 'DE'
            customer_details_data.org_language = 'DE'
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#content > main'):
            cpvs_data = cpvs()
        # Onsite Field -CPV code
        # Onsite Comment -None

            try:
                cpvs_data.cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"CPV code")]//following::div[1]').text
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
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#content > main'):
            funding_agencies_data = funding_agencies()
        # Onsite Field -Angaben zu Mitteln der Europäischen Union
        # Onsite Comment -if in below text written as " financed by European Union funds: No  " than pass the "None " in field name "T.FUNDING_AGENCIES::TEXT	" "II.2.13) Information about European Union Funds  >  The procurement is related to a project and/or programme financed by European Union funds: No  " if the abve  text written as " financed by European Union funds: YES  " than pass the "Funding agency" name as "European Agency (internal id: 1344862) " in field name "T.FUNDING_AGENCIES::TEXT"

            try:
                funding_agencies_data.funding_agency = page_details.find_element(By.XPATH, '//*[contains(text(),"Angaben zu Mitteln der Europäischen Union")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in funding_agency: {}".format(type(e).__name__))
                pass
        
            funding_agencies_data.funding_agencies_cleanup()
            notice_data.funding_agencies.append(funding_agencies_data)
    except Exception as e:
        logging.info("Exception in funding_agencies: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.XPATH, '#content > main'):
            tender_criteria_data = tender_criteria()
        # Onsite Field -Zuschlagskriterien
        # Onsite Comment -None

            try:
                tender_criteria_data.tender_criteria_title = page_details.find_element(By.CSS_SELECTOR, '//*[contains(text(),"Zuschlagskriterien")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in tender_criteria_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Zuschlagskriterien
        # Onsite Comment -None

            try:
                tender_criteria_data.tender_criteria_weight = page_details.find_element(By.CSS_SELECTOR, '//*[contains(text(),"Zuschlagskriterien")]//following::div[1]').text
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
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#content > main'):
            lot_details_data = lot_details()
        # Onsite Field -Bezeichnung
        # Onsite Comment -None

            try:
                lot_details_data.lot_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Kurze Beschreibung
        # Onsite Comment -if the "Kurze Beschreibung" field is not available pass the local_title in lot_ description

            try:
                lot_details_data.lot_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Kurze Beschreibung")]//following::p').text
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Beginn
        # Onsite Comment -None

            try:
                lot_details_data.contract_start_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Beginn")]//following::p[1]').text
            except Exception as e:
                logging.info("Exception in contract_start_date: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Ende
        # Onsite Comment -None

            try:
                lot_details_data.contract_end_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Ende")]//following::p[1]').text
            except Exception as e:
                logging.info("Exception in contract_end_date: {}".format(type(e).__name__))
                pass
        
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -Ausschreibungsunterlagen einsehen
# Onsite Comment -click on 'Ausschreibungsunterlagen einsehen' to get attachment

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.row > div > a'):
            attachments_data = attachments()
            attachments_data.file_name = 'Als ZIP-Datei herunterladen'
        # Onsite Field -Als ZIP-Datei herunterladen
        # Onsite Comment -"#Documents > a" use this selector also and for this selectorclick on 'Ausschreibungsunterlagen einsehen' to get data

            attachments_data.external_url = page_details.find_element(By.CSS_SELECTOR, '#content > main > div:nth-child(5) > div.link-container.text-right > a:nth-child(1)').get_attribute('href')
            
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url 
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
    urls = ['https://www.evergabe-online.de/search.html?0&cookieCheck'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,5):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="datatable"]/tbody/tr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="datatable"]/tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="datatable"]/tbody/tr')))[records]
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="datatable"]/tbody/tr'),page_check))
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
    