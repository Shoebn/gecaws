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
SCRIPT_NAME = "de_whitelabel_ca"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"




# first go to URL : "https://whitelabel.vergabe24.de/index.php?id=870&site=viewSearchResults&view=VA"
# to explore CA details go to "orders placed" option (In local language : "Vergebene Aufträge")
# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# Reference URL for 2 formats 

# ref URL 1 : https://whitelabel.vergabe24.de/index.php?id=870&view=VA&site=viewDetails&tid=7084009
# ref URL 2 : https://whitelabel.vergabe24.de/index.php?id=870&view=VA&site=viewDetails&tid=7062678
# -------------------------------------------------------------------------------------------------------------------------------------------------------------------

def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.script_name = 'de_whitelabel_ca'
    
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
    notice_data.notice_type = 7
    
    # Onsite Field -split the notice number from "Referenznummer der Bekanntmachung:" field name, ref url : "https://whitelabel.vergabe24.de/index.php?id=870&view=VA&site=viewDetails&tid=7062678"
    # Onsite Comment -None

    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"Bezeichnung des Auftrags:")]//following::span[1]').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Art der Leistung
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'tr> td.td-art-der-leistung').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Kurze Beschreibung")]//following::span[1]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Veröffentlicht
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "tbody > tr > td.td-veroeffentlicht").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -II.1.7) Gesamtwert der Beschaffung (ohne MwSt.)   Wert
    # Onsite Comment -ref url : "https://whitelabel.vergabe24.de/index.php?id=870&view=VA&site=viewDetails&tid=7063635"

    try:
        notice_data.est_amount = page_details.find_element(By.XPATH, '//*[contains(text(),"Gesamtwert der Beschaffung")]//following::span[1]').text
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -II.1.7) Gesamtwert der Beschaffung (ohne MwSt.)   Wert
    # Onsite Comment -ref url : "https://whitelabel.vergabe24.de/index.php?id=870&view=VA&site=viewDetails&tid=7063635"

    try:
        notice_data.grossbudgetlc = page_details.find_element(By.XPATH, '//*[contains(text(),"Gesamtwert der Beschaffung")]//following::span[1]').text
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -IV.1.1) Verfahrensart
    # Onsite Comment -ref url : "https://whitelabel.vergabe24.de/index.php?id=870&view=VA&site=viewDetails&tid=7063635"

    try:
        notice_data.type_of_procedure_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Verfahrensart")]//following::span[1]').text
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -II.1.3) Art des Auftrags
    # Onsite Comment -Replace following keywords with given respective keywords ('Dienstleistungen = Services ', 'Bauauftrag = Works', 'Ausführung von Bauleistungen = works'),  ref url : "https://whitelabel.vergabe24.de/index.php?id=870&view=VA&site=viewDetails&tid=7063635"

    try:
        notice_data.notice_contract_type = page_details.find_element(By.XPATH, '//*[contains(text(),"Art des Auftrags")]//following::span[1]').text
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -V.2) Auftragsvergabe
    # Onsite Comment -ref url : "https://whitelabel.vergabe24.de/index.php?id=870&view=VA&site=viewDetails&tid=7063635"

    try:
        notice_data.document_type_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Auftragsvergabe ")]//following::p[2]').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -II.1.4) Kurze Beschreibung:
    # Onsite Comment -ref url : "https://whitelabel.vergabe24.de/index.php?id=870&view=VA&site=viewDetails&tid=7063635"

    try:
        notice_data.notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),"Kurze Beschreibung")]//following::span[1]').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -II.2.13) Angaben zu Mitteln der Europäischen Union
    # Onsite Comment -if in below text written as " financed by European Union funds: No  " than pass the "None " in field name "T.FUNDING_AGENCIES::TEXT	" "II.2.13) Information about European Union Funds  >  The procurement is related to a project and/or programme financed by European Union funds: No  " if the abve  text written as " financed by European Union funds: YES  " than pass the "Funding agency" name as "European Agency (internal id: 1344862) " in field name "T.FUNDING_AGENCIES::TEXT"      ,ref url : "https://whitelabel.vergabe24.de/index.php?id=870&view=VA&site=viewDetails&tid=7063635"

    try:
        notice_data.funding_agencies = page_details.find_element(By.XPATH, '//*[contains(text(),"II.2.13)")]//following::span[1]').text
    except Exception as e:
        logging.info("Exception in funding_agencies: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -VI.5) Tag der Absendung dieser Bekanntmachung:
    # Onsite Comment -None

    try:
        notice_data.dispatch_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Tag der Absendung dieser Bekanntmachung")]//following::span[1]').text
    except Exception as e:
        logging.info("Exception in dispatch_date: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -there is no anchor link when we do the inspect element,

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, '#wrapperResult > table > tbody > tr').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += tender_html_element.find_element(By.CSS_SELECTOR, 'div > #detailText').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#detailText > div'):
            customer_details_data = customer_details()

            customer_details_data.org_country = 'DE'
            customer_details_data.org_language = 'DE'

        # Onsite Field -Name und Anschrift:
        # Onsite Comment -take only first line, split org_name only from this field, url ref : "https://whitelabel.vergabe24.de/index.php?id=870&view=VA&site=viewDetails&tid=7024126"

            try:
                customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Anschrift")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Name und Adressen   Offizielle Bezeichnung:
        # Onsite Comment -split org_name only from  "Name und Adressen   Offizielle Bezeichnung:" this field, url ref : "https://whitelabel.vergabe24.de/index.php?id=870&view=VA&site=viewDetails&tid=7062678"

            try:
                customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Adressen")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Name und Anschrift:
        # Onsite Comment -split the data between "Name und Anschrift:" and "Telefonnummer:" field, url ref : "https://whitelabel.vergabe24.de/index.php?id=870&view=VA&site=viewDetails&tid=7024126"

            try:
                customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Anschrift")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -I.1) Name und Adressen
        # Onsite Comment -split the data between "I.1) Name und Adressen" and "NUTS-Code:" field, url ref : "https://whitelabel.vergabe24.de/index.php?id=870&view=VA&site=viewDetails&tid=7063635"

            try:
                customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Adressen")]').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Name und Anschrift:
        # Onsite Comment -split the last text value from the given xpath, ref url : "https://whitelabel.vergabe24.de/index.php?id=870&view=VA&site=viewDetails&tid=7084009"

            try:
                customer_details_data.org_city = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Anschrift")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Postleitzahl / Ort:
        # Onsite Comment -split the data between "Postanschrift:" and "Land" field, url ref : "https://whitelabel.vergabe24.de/index.php?id=870&view=VA&site=viewDetails&tid=7063635",

            try:
                customer_details_data.org_city = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Adressen")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass
        

        # Onsite Field -E-Mail:
        # Onsite Comment -split the following data from this field,

            try:
                customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"E-Mail")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -E-Mail:
        # Onsite Comment -split the data betweeen "Telefon" and "Fax:" field, url ref : "https://whitelabel.vergabe24.de/index.php?id=870&view=VA&site=viewDetails&tid=7063635"

            try:
                customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Adressen")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Telefonnummer:
        # Onsite Comment -None

            try:
                customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Telefonnummer")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Telefon:
        # Onsite Comment -split the data between "NUTS-Code" and "E-Mail:", reference url : "https://whitelabel.vergabe24.de/index.php?id=870&view=VA&site=viewDetails&tid=7062678"

            try:
                customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Adressen")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Faxnummer:
        # Onsite Comment -split the data between "E-Mail:" and "Internet" field , reference url : "https://whitelabel.vergabe24.de/index.php?id=870&view=VA&site=viewDetails&tid=7084009"

            try:
                customer_details_data.org_fax = page_details.find_element(By.XPATH, '//*[contains(text(),"Faxnummer")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in org_fax: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Fax:
        # Onsite Comment -split the data between "E-Mail:" and "Internet-Adresse(n)   Hauptadresse: (URL)"  field , reference url : "https://whitelabel.vergabe24.de/index.php?id=870&view=VA&site=viewDetails&tid=7075224"

            try:
                customer_details_data.org_fax = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Adressen")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in org_fax: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -NUTS-Code
        # Onsite Comment -split the data between "Land:" and "Telefon:" field, ref url : "https://whitelabel.vergabe24.de/index.php?id=870&view=VA&site=viewDetails&tid=7062678"

            try:
                customer_details_data.customer_nuts = page_details.find_element(By.XPATH, '//*[contains(text()," Name und Adressen")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in customer_nuts: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Name und Anschrift:
        # Onsite Comment -split the last (5 digit) numeric value from this xpath, ref url : "https://whitelabel.vergabe24.de/index.php?id=870&view=VA&site=viewDetails&tid=7084009"

            try:
                customer_details_data.postal_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Anschrift")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in postal_code: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Postleitzahl / Ort:
        # Onsite Comment -split the numeric data between "Postanschrift:" and "Land" field, url ref : "https://whitelabel.vergabe24.de/index.php?id=870&view=VA&site=viewDetails&tid=7062678"

            try:
                customer_details_data.postal_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Adressen")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in postal_code: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Internet:
        # Onsite Comment -ref url : "https://whitelabel.vergabe24.de/index.php?id=870&view=VA&site=viewDetails&tid=7084009"

            try:
                customer_details_data.org_website = page_details.find_element(By.XPATH, '//*[contains(text(),"Internet:")]//following::a[1]').text
            except Exception as e:
                logging.info("Exception in org_website: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Internet-Adresse(n)   Hauptadresse: (URL)
        # Onsite Comment -ref url : "https://whitelabel.vergabe24.de/index.php?id=870&view=VA&site=viewDetails&tid=7062678"

            try:
                customer_details_data.org_website = page_details.find_element(By.XPATH, '//*[contains(text(),"Internet-Adresse(n)")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in org_website: {}".format(type(e).__name__))
                pass
        
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div > #detailText'):
            cpvs_data = cpvs()
        # Onsite Field -II.1.2) CPV-Code Hauptteil
        # Onsite Comment -split the first value from this xpath, url ref: "https://whitelabel.vergabe24.de/index.php?id=870&view=VA&site=viewDetails&tid=7062678"

            try:
                cpvs_data.cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"CPV-Code Hauptteil")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in cpv_code: {}".format(type(e).__name__))
                pass
        
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -if  "II.2.5) Zuschlagskriterien   Qualitätskriterium" this field not exist in lot section then we can  take as a tender_criteria details

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div > #detailText'):
            tender_criteria_data = tender_criteria()
        # Onsite Field -Name:
        # Onsite Comment -title and weight both are mentioned in same line but only take name as a title , split the data from "Name:" field, ref url : "https://whitelabel.vergabe24.de/index.php?id=870&view=VA&site=viewDetails&tid=7063635"

            try:
                tender_criteria_data.tender_criteria_title = page_details.find_element(By.XPATH, '//*[contains(text(),"Zuschlagskriterien")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in tender_criteria_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Gewichtung
        # Onsite Comment -title and weight both are mentioned in same line but only take data from "Gewichtung" field as a tender_criteria_weight , split the data from "Gewichtung" field, ref url : "https://whitelabel.vergabe24.de/index.php?id=870&view=VA&site=viewDetails&tid=7063635"

            try:
                tender_criteria_data.tender_criteria_weight = page_details.find_element(By.XPATH, '//*[contains(text(),"Zuschlagskriterien")]//following::span[1]').text
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
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div > #detailText'):
            lot_details_data = lot_details()
        # Onsite Field -Los-Nr:
        # Onsite Comment -split the data between "https://whitelabel.vergabe24.de/index.php?id=870&view=VA&site=viewDetails&tid=7062678"

            try:
                lot_details_data.lot_actual_number = page_details.find_element(By.XPATH, '//*[contains(text(),"II.2.1) Bezeichnung des Auftrags")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -II.2.1) Bezeichnung des Auftrags:
        # Onsite Comment -split the following data from this field, ref url : "https://whitelabel.vergabe24.de/index.php?id=870&view=VA&site=viewDetails&tid=7062678"

            try:
                lot_details_data.lot_title = page_details.find_element(By.XPATH, '//*[contains(text(),"II.2.1) Bezeichnung des Auftrags")]').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -II.2.4) Beschreibung der Beschaffung
        # Onsite Comment -ref url : "https://whitelabel.vergabe24.de/index.php?id=870&view=VA&site=viewDetails&tid=7062678"

            try:
                lot_details_data.lot_description = page_details.find_element(By.XPATH, '//*[contains(text(),"II.2.4) Beschreibung der Beschaffung")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -NUTS-Code:
        # Onsite Comment -ref url : "https://whitelabel.vergabe24.de/index.php?id=870&view=VA&site=viewDetails&tid=7062678"

            try:
                lot_details_data.lot_nuts = page_details.find_element(By.XPATH, '//*[contains(text(),"NUTS-Code:")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in lot_nuts: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -II.1.3) Art des Auftrags
        # Onsite Comment -ref url : "https://whitelabel.vergabe24.de/index.php?id=870&view=VA&site=viewDetails&tid=7063635"

            try:
                lot_details_data.contract_type = page_details.find_element(By.XPATH, '//*[contains(text(),"Art des Auftrags")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in contract_type: {}".format(type(e).__name__))
                pass

        # Onsite Field -Ursprünglich veranschlagter Gesamtwert des Auftrags/des Loses:
        # Onsite Comment -split the data between "V.2.4) Angaben zum Wert des Auftrags/Loses (ohne MwSt.)" and "Gesamtwert des Auftrags/Loses:" field, if the lots are awarded to multipule bidder than select all the bidder name and initial , gross details lot wise, url ref : "https://whitelabel.vergabe24.de/index.php?id=870&view=VA&site=viewDetails&tid=7062678"

            try:
                lot_details_data.lot_grossbudget_lc = page_details.find_element(By.XPATH, '//*[contains(text(),"V.2.4) Angaben zum Wert des Auftrags/Loses (ohne MwSt.)")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
                pass    
        
        # Onsite Field -None
        # Onsite Comment -None

            try:
                for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div > #detailText'):
                    lot_cpvs_data = lot_cpvs()
		
                    # Onsite Field -II.2.2) Weitere(r) CPV-Code(s)   CPV-Code Hauptteil:
                    # Onsite Comment -url ref : "https://whitelabel.vergabe24.de/index.php?id=870&view=VA&site=viewDetails&tid=7062678"

                    lot_cpvs_data.lot_cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"II.2.2) Weitere(r) CPV-Code(s)")]//following::span[1]').text
			
                    lot_cpvs_data.lot_cpvs_cleanup()
                    lot_details_data.lot_cpvs.append(lot_cpvs_data)
            except Exception as e:
                logging.info("Exception in lot_cpvs: {}".format(type(e).__name__))
                pass
			
        # Onsite Field -None
        # Onsite Comment -there are 2 format in contract award details, first take from "e) beauftragtes Unternehmen:" section  url ref : "https://whitelabel.vergabe24.de/index.php?id=870&view=VA&site=viewDetails&tid=7084009"  and second take from "Abschnitt V: Auftragsvergabe"  section url ref : "https://whitelabel.vergabe24.de/index.php?id=870&view=VA&site=viewDetails&tid=7014162"

            try:
                for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div > #detailText'):
                    award_details_data = award_details()
		
                    # Onsite Field -1. Auftragnehmer:
                    # Onsite Comment -split the following value from "1. Auftragnehmer: " this field, url ref : "https://whitelabel.vergabe24.de/index.php?id=870&view=VA&site=viewDetails&tid=7024126"

                    award_details_data.bidder_name = page_details.find_element(By.CSS_SELECTOR, 'p:nth-child(14) > span').text
			
                    # Onsite Field -V.2.3) Name und Anschrift des Wirtschaftsteilnehmers, zu dessen Gunsten der Zuschlag erteilt wurde   Offizielle Bezeichnung:
                    # Onsite Comment -split the following data from this field , url ref : "https://whitelabel.vergabe24.de/index.php?id=870&view=VA&site=viewDetails&tid=7062678"

                    award_details_data.bidder_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Gunsten der Zuschlag erteilt wurde")]').text
			
                    # Onsite Field -e) beauftragtes Unternehmen:
                    # Onsite Comment -split the last 2 lines as a org_address from selector, url ref : "https://whitelabel.vergabe24.de/index.php?id=870&view=VA&site=viewDetails&tid=7075234"

                    award_details_data.address = page_details.find_element(By.CSS_SELECTOR, 'p:nth-child(14) > span').text
			
                    # Onsite Field -Postal address:
                    # Onsite Comment -split the data between "Official name:" and "NUTS code", url ref : "https://whitelabel.vergabe24.de/index.php?id=870&view=VA&site=viewDetails&tid=7062678"

                    award_details_data.address = page_details.find_element(By.XPATH, '//*[contains(text(),"V.2.3) ")]//following::span[1]').text
			
                    # Onsite Field -Ursprünglich veranschlagter Gesamtwert des Auftrags/des Loses:
                    # Onsite Comment -split the following data from "  Ursprünglich veranschlagter Gesamtwert des Auftrags/des Loses:" field , there are multiple bidders are mentioned in this site , url ref : "https://whitelabel.vergabe24.de/index.php?id=870&view=VA&site=viewDetails&tid=7062678"

                    award_details_data.initial_estimated_value = page_details.find_element(By.XPATH, '//*[contains(text(),"V.2.4) Angaben zum Wert des Auftrags/Loses (ohne MwSt.)")]//following::span[1]').text
			
                    # Onsite Field -Gesamtwert des Auftrags/Loses:
                    # Onsite Comment -split the following data from "Gesamtwert des Auftrags/Loses:" field, there are multiple bidders are mentioned in this site , url ref : "https://whitelabel.vergabe24.de/index.php?id=870&view=VA&site=viewDetails&tid=7062678"

                    award_details_data.grossawardvaluelc = page_details.find_element(By.XPATH, '//*[contains(text(),"V.2.4) Angaben zum Wert des Auftrags/Loses (ohne MwSt.)")]//following::span[1]').text
			
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
    urls = ["https://whitelabel.vergabe24.de/index.php?id=870&site=viewSearchResults&view=VA"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,3):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="wrapperResult"]/table/tbody/tr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="wrapperResult"]/table/tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="wrapperResult"]/table/tbody/tr')))[records]
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="wrapperResult"]/table/tbody/tr'),page_check))
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