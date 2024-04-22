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
SCRIPT_NAME = "de_hessen_ca"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    # Onsite Field -None
    # Onsite Comment -format 1 :- if type_of_procedure_actual have keywords like 'open procedure' and format 2 :- if type_of_procedure_actual have keywords like 'restricted tender','negotiated award without competitive tender','negotiated award without participation competition','free hand assignment'
    notice_data.script_name = 'de_hessen_ca'
    
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
    notice_data.notice_type = 7
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'div > h1').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'p.mb-3').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-5 > p:nth-child(4)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Art:
    # Onsite Comment -split type_of_procedure_actual from the selector eg :from "VOB, Öffentliche Ausschreibung" take only "Öffentliche Ausschreibung"
    try:
        notice_data.type_of_procedure_actual = tender_html_element.find_element(By.CSS_SELECTOR, "div.col-7  > div:nth-child(1)  > div > div:nth-child(2)").text
        notice_data.type_of_procedure = fn.procedure_mapping("assets/de_hessen_ca_procedure",notice_data.type_of_procedure_actual)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.publish_date = 'take publish_date as threshold'
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'section > div> a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#content-section').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Kurze Beschreibung:
    # Onsite Comment -use this selector for FORMAT 1 and if notice_summary_english is not available then pass local_title as notice_summary_english

    try:
        notice_data.notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),"Kurze Beschreibung:")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -use this selector for FORMAT 2

    try:
        notice_data.notice_summary_english = page_details.find_element(By.CSS_SELECTOR, 'p.mb-3').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
 
    # Onsite Field -None
    # Onsite Comment -use this selector for FORMAT 1 and if local_description is not available then pass local_title as local_description
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Kurze Beschreibung:")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
        
    # Onsite Field -None
    # Onsite Comment -use this selector for FORMAT 2    
    try:
        notice_data.local_description = page_details.find_element(By.CSS_SELECTOR, 'p.mb-3').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -II.1.7) Gesamtwert der Beschaffung (ohne MwSt.)
    # Onsite Comment -None

    try:
        notice_data.grossbudgetlc = page_details.find_element(By.XPATH, '//*[contains(text(),"II.1.7) Gesamtwert der Beschaffung (ohne MwSt.)")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#content-section'):
            customer_details_data = customer_details()
        # Onsite Field -Vergabestelle:
        # Onsite Comment -None

            try:
                customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-7  > div:nth-child(2) >div > div:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Name und Adressen
        # Onsite Comment -use this selector for FORMAT 1

            try:
                customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Adressen")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Name und Anschrift:
        # Onsite Comment -use this selector for FORMAT 2

            try:
                customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Anschrift:")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Telefon:
        # Onsite Comment -use this selector for FORMAT 1 and split org_phone from the given selector take only 'Telefon:'

            try:
                customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Adressen")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Telefon:
        # Onsite Comment -use this selector for FORMAT 2

            try:
                customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Telefon:")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -E-Mail:
        # Onsite Comment -use this selector for FORMAT 1 and split org_email from the given selector take only 'E-Mail:'

            try:
                customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Adressen")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -E-Mail:
        # Onsite Comment -use this selector for FORMAT 2

            try:
                customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"E-Mail:")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Fax:
        # Onsite Comment -use this selector for FORMAT 1 and split org_fax from the given selector take only 'Fax:'

            try:
                customer_details_data.org_fax = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Adressen")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in org_fax: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Fax:
        # Onsite Comment -use this selector for FORMAT 2

            try:
                customer_details_data.org_fax = page_details.find_element(By.XPATH, '//*[contains(text(),"Fax:")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in org_fax: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Internet-Adresse(n)
        # Onsite Comment -use this selector for FORMAT 1

            try:
                customer_details_data.org_website = page_details.find_element(By.XPATH, '//*[contains(text(),"Internet-Adresse(n)")]//following::a[1]').text
            except Exception as e:
                logging.info("Exception in org_website: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Internet
        # Onsite Comment -use this selector for FORMAT 2

            try:
                customer_details_data.org_website = page_details.find_element(By.XPATH, '//*[contains(text(),"Internet")]//following::a[1]').text
            except Exception as e:
                logging.info("Exception in org_website: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -NUTS-Code:
        # Onsite Comment -use this selector for FORMAT 1  split customer_nuts from the given selector take only 'NUTS-Code:'

            try:
                customer_details_data.customer_nuts = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Adressen")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in customer_nuts: {}".format(type(e).__name__))
                pass
        
            customer_details_data.org_language = 'DE'
            customer_details_data.org_country = 'DE'
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#content-section'):
            cpvs_data = cpvs()
        # Onsite Field -CPV-Code Hauptteil
        # Onsite Comment -use this selector for FORMAT 1 and take only cpv-code

            try:
                cpvs_data.cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"CPV-Code Hauptteil")]//following::td[1]').text
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
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#content-section'):
            funding_agencies_data = funding_agencies()
        # Onsite Field -Angaben zu Mitteln der Europäischen Union
        # Onsite Comment -if in below text written as "Angaben zu Mitteln der Europäischen Union Der Auftrag steht in Verbindung mit einem Vorhaben und/oder Programm, das aus Mitteln der EU finanziert wird: Nein" than pass the "None" in field name "T.FUNDING_AGENCIES::TEXT" and if "Angaben zu Mitteln der Europäischen Union Der Auftrag steht in Verbindung mit einem Vorhaben und/oder Programm, das aus Mitteln der EU finanziert wird:YES  " than pass the "Funding agency" name as "European Agency (internal id: 1344862)" in field name "T.FUNDING_AGENCIES::TEXT"

            try:
                funding_agencies_data.funding_agency = page_details.find_element(By.XPATH, '//*[contains(text(),"Angaben zu Mitteln der Europäischen Union")]//following::td[1]').text
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
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#content-section'):
            tender_criteria_data = tender_criteria()
        # Onsite Field -Zuschlagskriterien
        # Onsite Comment -None

            try:
                tender_criteria_data.tender_criteria_title = page_details.find_element(By.XPATH, '//*[contains(text(),"Zuschlagskriterien")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in tender_criteria_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Zuschlagskriterien
        # Onsite Comment -None

            try:
                tender_criteria_data.tender_criteria_weight = page_details.find_element(By.XPATH, '//*[contains(text(),"Zuschlagskriterien")]//following::td[1]').text
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
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#content-section'):
            lot_details_data = lot_details()
        # Onsite Field -Los-Nr:
        # Onsite Comment -split lot_actual_number from the given selector take only 'Los-Nr:'

            try:
                lot_details_data.lot_actual_number = page_details.find_element(By.XPATH, '//*[contains(text(),"II.2.1) Bezeichnung des Auftrags:")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Bezeichnung des Auftrags:
        # Onsite Comment -take only lot_title from the given selector and if lot_title is not available then pass local_title as lot_title

            try:
                lot_details_data.lot_title = page_details.find_element(By.XPATH, '//*[contains(text(),"II.2.1) Bezeichnung des Auftrags:")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Beschreibung der Beschaffung
        # Onsite Comment -if lot_description is not available then pass local_title as lot_description

            try:
                lot_details_data.lot_description = page_details.find_element(By.XPATH, '//*[contains(text(),"II.2.4) Beschreibung der Beschaffung")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Gesamtwert der Beschaffung (ohne MwSt.)
        # Onsite Comment -None

            try:
                lot_details_data.lot_grossbudget_lc = page_details.find_element(By.XPATH, '//*[contains(text(),"II.1.7) Gesamtwert der Beschaffung (ohne MwSt.)")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Information über die Nichtvergabe
        # Onsite Comment -None

            try:
                lot_details_data.lot_is_canceled = page_details.find_element(By.XPATH, '//*[contains(text(),"Information über die Nichtvergabe")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in lot_is_canceled: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -None

            try:
                for single_record in page_details.find_elements(By.CSS_SELECTOR, '#content-section'):
                    lot_cpvs_data = lot_cpvs()
		
                    # Onsite Field -II.2.2) Weitere(r) CPV-Code(s)
                    # Onsite Comment -None

                    lot_cpvs_data.lot_cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"II.2.2) Weitere(r) CPV-Code(s)")]//following::td[1]').text
			
                    lot_cpvs_data.lot_cpvs_cleanup()
                    lot_details_data.lot_cpvs.append(lot_cpvs_data)
            except Exception as e:
                logging.info("Exception in lot_cpvs: {}".format(type(e).__name__))
                pass
			
        # Onsite Field -None
        # Onsite Comment -None

            try:
                for single_record in page_details.find_elements(By.CSS_SELECTOR, '#content-section'):
                    lot_criteria_data = lot_criteria()
		
                    # Onsite Field -II.2.5) Zuschlagskriterien
                    # Onsite Comment -None

                    lot_criteria_data.lot_criteria_title = page_details.find_element(By.XPATH, '//*[contains(text(),"II.2.5) Zuschlagskriterien")]//following::td[1]').text
			
                    # Onsite Field -II.2.5) Zuschlagskriterien
                    # Onsite Comment -None

                    lot_criteria_data.lot_criteria_weight = page_details.find_element(By.XPATH, '//*[contains(text(),"II.2.5) Zuschlagskriterien")]//following::td[1]').text
			
                    lot_criteria_data.lot_criteria_cleanup()
                    lot_details_data.lot_criteria.append(lot_criteria_data)
            except Exception as e:
                logging.info("Exception in lot_criteria: {}".format(type(e).__name__))
                pass
			
        # Onsite Field -None
        # Onsite Comment -None

            try:
                for single_record in page_details.find_elements(By.CSS_SELECTOR, '#content-section'):
                    award_details_data = award_details()
		
                    # Onsite Field -Auftragnehmer:
                    # Onsite Comment -split bidder_name and take first line as bidder_name from the given selector

                    award_details_data.bidder_name = page_details.find_element(By.XPATH, '//*[contains(text()," Auftragnehmer:")]//following::td[1]').text
			
                    # Onsite Field -Auftragnehmer:
                    # Onsite Comment -split address and take second and third line as address from the given selector

                    award_details_data.address = page_details.find_element(By.XPATH, '//*[contains(text()," Auftragnehmer:")]//following::td[1]').text
			
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
page_main = fn.init_chrome_driver(arguments) 
page_details = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://vergabe.hessen.de/NetServer/PublicationSearchControllerServlet?function=SearchPublications&Gesetzesgrundlage=All&Category=ContractAward&thContext=awardPublications&Order=desc&OrderBy=Publishing&Max=25'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,6):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="searchForm"]/div/div/div/section/div'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="searchForm"]/div/div/div/section/div')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="searchForm"]/div/div/div/section/div')))[records]
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="searchForm"]/div/div/div/section/div'),page_check))
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
    