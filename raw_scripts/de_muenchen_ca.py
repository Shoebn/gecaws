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



#check comments for additional changes
#1)for bidder name
# As discussed with shoeib added below condition .. (1) if lot avaialble than condition 
# lot_title ="blank "and award_details ="blank" []
# than lot_details =[]
# (2) if lots not avaible than
# award_details= []
# and lot_details= []


# format 1)open procedure=Offenes Verfahren
# format 2)restricted tender=Beschränkte Ausschreibung,Negotiated award without participation competition=Verhandlungsvergabe ohne Teilnahmewettbewerb,Free contract award=Freihändige Vergabe
# format 3)Order changes during the EU contract term (so-called supplementary procedure)=Auftragsänderungen während der Vertragslaufzeit EU (sog. Nachtragsverfahren)



NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "de_muenchen_ca"
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
    notice_data.script_name = 'de_muenchen_ca'
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'DE'
    notice_data.performance_country.append(performance_country_data)
    
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
    notice_data.main_language = 'DE'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_type = 7
    
    # Onsite Field -Ausschreibung
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'tbody > tr > td.tender').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Verfahrensart
    # Onsite Comment -None

    try:
        notice_data.type_of_procedure_actual = tender_html_element.find_element(By.CSS_SELECTOR, 'tbody > tr > td:nth-child(4)').text
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Erschienen am
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "tbody > tr > td:nth-child(1)").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -None
    # Onsite Comment -Note:Click on "<tr>tag"

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'tbody > tr').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'body > div.page').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
# Onsite Field -None
# Onsite Comment -None
# format 1
# ref_url=https://vergabe.muenchen.de/NetServer/PublicationControllerServlet?function=Detail&TOID=54321-

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'body > div.page'):
            customer_details_data = customer_details()
        # Onsite Field -Vertragspartei und Dienstleister >> Beschaffer >>Offizielle Bezeichnung
        # Onsite Comment -Note:Splite org_name after "Offizielle Bezeichnung" and "Registrierungsnummer"

            try:
                customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Beschaffer")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Vertragspartei und Dienstleister >> Beschaffer
        # Onsite Comment -None

            try:
                customer_details_data.org_address = page_details.find_element(By.CSS_SELECTOR, 'tbody > tr:nth-child(3) > td:nth-child(2) > a:nth-child(3)').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Vertragspartei und Dienstleister >> Beschaffer
        # Onsite Comment -Note:Split postal_code between	"Postleitzahl / Ort" and "NUTS-3-Code"

            try:
                customer_details_data.postal_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Beschaffer")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in postal_code: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Vertragspartei und Dienstleister >> Beschaffer
        # Onsite Comment -Note:Split customer_nuts between "NUTS-3-Code" and "Land"

            try:
                customer_details_data.customer_nuts = page_details.find_element(By.XPATH, '//*[contains(text(),"Beschaffer")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in customer_nuts: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Vertragspartei und Dienstleister >> Beschaffer
        # Onsite Comment -Note:Split org_email between "E-Mail" and "Telefon"

            try:
                customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Beschaffer")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Vertragspartei und Dienstleister >> Beschaffer
        # Onsite Comment -Note:Split org_phone between "Telefon" and "Fax"

            try:
                customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Beschaffer")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Vertragspartei und Dienstleister >> Beschaffer
        # Onsite Comment -Note:Split org_fax between "Fax" and "Art des öffentlichen Auftraggebers"

            try:
                customer_details_data.org_fax = page_details.find_element(By.XPATH, '//*[contains(text(),"Beschaffer")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in org_fax: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Vertragspartei und Dienstleister >> Beschaffer
        # Onsite Comment -Note:Split org_fax between "Fax" and "Art des öffentlichen Auftraggebers"

            try:
                customer_details_data.org_fax = page_details.find_element(By.XPATH, '//*[contains(text(),"Beschaffer")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in org_fax: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Vertragspartei und Dienstleister >> Beschaffer
        # Onsite Comment -Note:Split customer_main_activity between "Haupttätigkeiten des öffentlichen Auftraggebers" to "Profil des Erwerbers (URL)"

            try:
                customer_details_data.customer_main_activity = page_details.find_element(By.XPATH, '//*[contains(text(),"Beschaffer")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in customer_main_activity: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Beschaffungsinformationen (allgemein) >> Überprüfungsstelle
        # Onsite Comment -Note:Splite contact_person between "Offizielle Bezeichnung" and "Registrierungsnummer"

            try:
                customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Überprüfungsstelle")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Beschaffungsinformationen (allgemein) >> Überprüfungsstelle
        # Onsite Comment -Note:Splite contact_person between "Offizielle Bezeichnung" and "Registrierungsnummer"

            try:
                customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Überprüfungsstelle")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Vertragspartei und Dienstleister >> Beschaffer
        # Onsite Comment -Note:Split between "Art des öffentlichen Auftraggebers" to "Haupttätigkeiten des öffentlichen Auftraggebers"

            try:
                customer_details_data.type_of_authority_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Beschaffer")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in type_of_authority_code: {}".format(type(e).__name__))
                pass
        
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Beschreibung")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Verfahren >> Beschreibung
    # Onsite Comment -Note:Split local_description between "Beschreibung" and "Art des Auftrags"

    try:
        notice_data.notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),"Beschreibung")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Verfahren >> Beschreibung
    # Onsite Comment -Note:Split notice_contract_type before "Art des Auftrags" 	        Note:Repleace following keywords with given keywords("Dienstleistungen=Service")

    try:
        notice_data.notice_contract_type = page_details.find_element(By.XPATH, '//*[contains(text(),"Beschreibung")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Verfahren >> Beschreibung
    # Onsite Comment -None

    try:
        notice_data.contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Beschreibung")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.class_at_source = 'CPV'
    
    # Onsite Field -Verfahren >> CPV-Code Hauptteil
    # Onsite Comment -Note:Split before "CPV-Code Hauptteil"

    try:
        notice_data.cpv_at_source = page_details.find_element(By.XPATH, '//*[contains(text(),"CPV-Code Hauptteil")]').text
    except Exception as e:
        logging.info("Exception in cpv_at_source: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Verfahren >> Weitere CPV-Code Hauptteile
    # Onsite Comment -Note:Split before "Weitere CPV-Code Hauptteile"

    try:
        notice_data.cpv_at_source = page_details.find_element(By.XPATH, '//*[contains(text(),"Weitere CPV-Code Hauptteile")]').text
    except Exception as e:
        logging.info("Exception in cpv_at_source: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'body > div.page'):
            cpvs_data = cpvs()
        # Onsite Field -Verfahren >> CPV-Code Hauptteil
        # Onsite Comment -Note:Split before "CPV-Code Hauptteil"

            try:
                cpvs_data.cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"CPV-Code Hauptteil")]').text
            except Exception as e:
                logging.info("Exception in cpv_code: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Verfahren >> Weitere CPV-Code Hauptteile
        # Onsite Comment -Note:Split before "Weitere CPV-Code Hauptteile"

            try:
                cpvs_data.cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Weitere CPV-Code Hauptteile")]').text
            except Exception as e:
                logging.info("Exception in cpv_code: {}".format(type(e).__name__))
                pass
        
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
    
    # Onsite Field -Beschaffungsinformationen (speziell) >> Geschätzte Laufzeit
    # Onsite Comment -Note:Splite before "Beginn" and "Ende"

    try:
        notice_data.tender_contract_start_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Geschätzte Laufzeit")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in tender_contract_start_date: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Beschaffungsinformationen (speziell) >> Geschätzte Laufzeit
    # Onsite Comment -Note:Splite after "Ende"

    try:
        notice_data.tender_contract_start_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Geschätzte Laufzeit")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in tender_contract_start_date: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'body > div.page'):
            tender_criteria_data = tender_criteria()
        # Onsite Field -Beschaffungsinformationen (speziell) >> Zuschlagskriterien
        # Onsite Comment -Note:Splite before "Gewichtung"

            try:
                tender_criteria_data.tender_criteria_title = page_details.find_element(By.XPATH, '//*[contains(text(),"Zuschlagskriterien")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in tender_criteria_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Beschaffungsinformationen (speziell) >> Zuschlagskriterien
        # Onsite Comment -Note:Splite after "Gewichtung"

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
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'body > div.page'):
            lot_details_data = lot_details()
        # Onsite Field -Ausschreibung
        # Onsite Comment -None

            try:
                lot_details_data.lot_title = tender_html_element.find_element(By.CSS_SELECTOR, 'tbody > tr > td.tender').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -None

            try:
                for single_record in page_details.find_elements(By.CSS_SELECTOR, 'body > div.page'):
                    award_details_data = award_details()
		
                    # Onsite Field -Ergebnis >> Bieter
                    # Onsite Comment -Note:Splite before "Offizielle Bezeichnung" and "Registrierungsnummer (Umsatzsteuer-ID)"

                    award_details_data.bidder_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Bieter")]//following::td[6]').text
			
                    # Onsite Field -Ergebnis >> Bieter
                    # Onsite Comment -Note:Splite before "Postanschrift" and "Der Auftragnehmer ist ein KMU"

                    award_details_data.address = page_details.find_element(By.XPATH, '//*[contains(text(),"Bieter")]//following::td[6]').text
			
                    # Onsite Field -Ergebnis >> Vertrag >> Datum des Vertragsabschlusses
                    # Onsite Comment -Note:Splite before "Datum des Vertragsabschlusses"

                    award_details_data.award_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Datum des Vertragsabschlusses")]').text
			
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
# format 2
# ref_url=https://vergabe.muenchen.de/NetServer/PublicationControllerServlet?function=Detail&TOID=54321-NetTender-18b1f3e084b-6357e6a6f76986c2&Category=ContractAward
    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'body > div.page'):
            customer_details_data = customer_details()
        # Onsite Field -Öffentlicher Auftraggeber (Vergabestelle) >> Name und Anschrift
        # Onsite Comment -Note:Take only first line

            try:
                customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Anschrift")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Öffentlicher Auftraggeber (Vergabestelle) >> Name und Anschrift
        # Onsite Comment -None

            try:
                customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Anschrift")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Öffentlicher Auftraggeber (Vergabestelle) >> Telefonnummer
        # Onsite Comment -None

            try:
                customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Telefonnummer")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Öffentlicher Auftraggeber (Vergabestelle) >> E-Mail
        # Onsite Comment -None

            try:
                customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"E-Mail")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Öffentlicher Auftraggeber (Vergabestelle) >> Faxnummer
        # Onsite Comment -None

            try:
                customer_details_data.org_fax = page_details.find_element(By.XPATH, '//*[contains(text(),"Faxnummer")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in org_fax: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Öffentlicher Auftraggeber (Vergabestelle) >> Internet
        # Onsite Comment -None

            try:
                customer_details_data.org_website = page_details.find_element(By.CSS_SELECTOR, 'tbody > tr:nth-child(7) > td:nth-child(2) > a').text
            except Exception as e:
                logging.info("Exception in org_website: {}".format(type(e).__name__))
                pass
        
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Art und Umfang der Leistung")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Zeitraum der 	Leistungserbringung >> Lieferung/Ausführung ab
    # Onsite Comment -None

    try:
        notice_data.tender_contract_start_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Lieferung/Ausführung ab")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in tender_contract_start_date: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Zeitraum der Leistungserbringung >> Lieferung/Ausführung bis
    # Onsite Comment -None

    try:
        notice_data.tender_contract_end_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Lieferung/Ausführung bis")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in tender_contract_end_date: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'body > div.page'):
            lot_details_data = lot_details()
        # Onsite Field -Ausschreibung
        # Onsite Comment -None

            try:
                lot_details_data.lot_title = tender_html_element.find_element(By.CSS_SELECTOR, 'tbody > tr > td.tender').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -None

            try:
                for single_record in page_details.find_elements(By.CSS_SELECTOR, 'body > div.page'):
                    award_details_data = award_details()
		
                    # Onsite Field -beauftragtes Unternehmen >> Auftragnehmer
                    # Onsite Comment -Note:Take only first line

                    award_details_data.bidder_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Auftragnehmer")]//following::td[1]').text
			
                    # Onsite Field -beauftragtes Unternehmen >> Auftragnehmer
                    # Onsite Comment -None

                    award_details_data.address = page_details.find_element(By.XPATH, '//*[contains(text(),"Auftragnehmer")]//following::td[1]').text
			
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
# format 3
# ref_url=https://vergabe.muenchen.de/NetServer/PublicationControllerServlet?function=Detail&TOID=54321-NetTender-18b4842d056-640851def78c3472&Category=ContractAward

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'body > div.page'):
            customer_details_data = customer_details()
        # Onsite Field -Abschnitt I: Öffentlicher Auftraggeber/Auftraggeber >> Name und Adressen
        # Onsite Comment -Note:Splite before "Offizielle Bezeichnung" and "Postanschrift"

            try:
                customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Adressen")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Abschnitt I: Öffentlicher Auftraggeber/Auftraggeber >> Name und Adressen
        # Onsite Comment -None

            try:
                customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Adressen")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Abschnitt I: Öffentlicher Auftraggeber/Auftraggeber >> E-Mail
        # Onsite Comment -Note:Splite before "E-Mail" and "Fax"

            try:
                customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Adressen")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Abschnitt I: Öffentlicher Auftraggeber/Auftraggeber >> Fax
        # Onsite Comment -Note:Splite after "Fax"

            try:
                customer_details_data.org_fax = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Adressen")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in org_fax: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Abschnitt I: Öffentlicher Auftraggeber/Auftraggeber >> Internet-Adresse(n) >> Hauptadresse
        # Onsite Comment -None

            try:
                customer_details_data.org_website = page_details.find_element(By.CSS_SELECTOR, 'tbody > tr > td:nth-child(2) > a:nth-child(1)').text
            except Exception as e:
                logging.info("Exception in org_website: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Abschnitt I: Öffentlicher Auftraggeber/Auftraggeber >> NUTS-Code
        # Onsite Comment -Note:Splite before "NUTS-Code" and "E-Mail"

            try:
                customer_details_data.customer_nuts = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Adressen")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in customer_nuts: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Abschnitt I: Öffentlicher Auftraggeber/Auftraggeber >> Postleitzahl / Ort
        # Onsite Comment -Note:Splite before "Postleitzahl / Ort" and "Land"

            try:
                customer_details_data.postal_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Adressen")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in postal_code: {}".format(type(e).__name__))
                pass
        
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Beschreibung der Beschaffung")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Abschnitt II: Gegenstand >> Beschreibung der Beschaffung
    # Onsite Comment -None

    try:
        notice_data.notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),"Beschreibung der Beschaffung")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.class_at_source = 'CPV'
    
    # Onsite Field -Abschnitt II: Gegenstand >> II.1.2) CPV-Code Hauptteil
    # Onsite Comment -None

    try:
        notice_data.cpv_at_source = page_details.find_element(By.XPATH, '//*[contains(text(),"CPV-Code Hauptteil")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in cpv_at_source: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Abschnitt II: Gegenstand >> II.1.2) CPV-Code Hauptteil
    # Onsite Comment -None

    try:
        notice_data.cpv_at_source = page_details.find_element(By.XPATH, '//*[contains(text(),"Weitere(r) CPV-Code(s)")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in cpv_at_source: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'body > div.page'):
            cpvs_data = cpvs()
        # Onsite Field -Abschnitt II: Gegenstand >> II.1.2) CPV-Code Hauptteil
        # Onsite Comment -None

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
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'body > div.page'):
            funding_agencies_data = funding_agencies()
        # Onsite Field -Abschnitt II: Gegenstand >> II.2.13) Angaben zu Mitteln der Europäischen Union
        # Onsite Comment -Note:"II.2.13) Information on European Union funds" , if the "financed by EU funds: No" it will be go null.. and if the"financed by EU funds: YES" it will pass the "Funding agency" name as "European Agency (internal id: 1344862)

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
    
    # Onsite Field -Abschnitt IV: Verfahren >> Bekanntmachungsnummer im ABl
    # Onsite Comment -Note:Splite after "Bekanntmachungsnummer im ABl"

    try:
        notice_data.related_tender_id = page_details.find_element(By.XPATH, '//*[contains(text(),"Bekanntmachungsnummer im ABl")]').text
    except Exception as e:
        logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
        pass
    # Onsite Field -Abschnitt II: Gegenstand >> Art des Auftrags
    # Onsite Comment -Note:Repleace following keywords with given keywords("Dienstleistungen=Service")

    try:
        notice_data.notice_contract_type = page_details.find_element(By.XPATH, '//*[contains(text(),"Art des Auftrags")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Abschnitt II: Gegenstand >> Art des Auftrags
    # Onsite Comment -None

    try:
        notice_data.contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Art des Auftrags")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass       
    
# Onsite Field -None
# Onsite Comment -None
# ref_url:https://vergabe.muenchen.de/NetServer/PublicationControllerServlet?function=Detail&TOID=54321-NetTender-18738142dc0-2a8f6012f4bcc563&Category=ContractAward

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'body > div.page'):
            lot_details_data = lot_details()
        # Onsite Field -Ausschreibung
        # Onsite Comment -None

            try:
                lot_details_data.lot_title = tender_html_element.find_element(By.CSS_SELECTOR, 'tbody > tr > td.tender').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Abschnitt II: Gegenstand >> NUTS-Code
        # Onsite Comment -None

            try:
                lot_details_data.lot_nuts = page_details.find_element(By.XPATH, '//*[contains(text(),"NUTS-Code")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in lot_nuts: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Abschnitt II: Gegenstand >> II.2.4) Beschreibung der Beschaffung
        # Onsite Comment -None

            try:
                lot_details_data.lot_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Beschreibung der Beschaffung")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Abschnitt II: Gegenstand >> II.2.7) Laufzeit des Vertrags, der Rahmenvereinbarung, des dynamischen Beschaffungssystems oder der Konzession
        # Onsite Comment -Note:Splite before "Beginn" and "Ende"

            try:
                lot_details_data.contract_start_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Laufzeit des Vertrags")]//following::td[2]').text
            except Exception as e:
                logging.info("Exception in contract_start_date: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Abschnitt II: Gegenstand >> II.2.7) Laufzeit des Vertrags, der Rahmenvereinbarung, des dynamischen Beschaffungssystems oder der Konzession
        # Onsite Comment -Note:Splite after "Ende"

            try:
                lot_details_data.contract_end_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Laufzeit des Vertrags")]//following::td[2]').text
            except Exception as e:
                logging.info("Exception in contract_end_date: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -None

            try:
                for single_record in page_details.find_elements(By.CSS_SELECTOR, 'body > div.page'):
                    lot_cpvs_data = lot_cpvs()
		
                    # Onsite Field -Abschnitt II: Gegenstand >> II.1.2) CPV-Code Hauptteil
                    # Onsite Comment -None

                    lot_cpvs_data.lot_cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Weitere(r) CPV-Code(s)")]//following::td[1]').text
			
                    lot_cpvs_data.lot_cpvs_cleanup()
                    lot_details_data.lot_cpvs.append(lot_cpvs_data)
            except Exception as e:
                logging.info("Exception in lot_cpvs: {}".format(type(e).__name__))
                pass
			
        # Onsite Field -None
        # Onsite Comment -None

            try:
                for single_record in page_details.find_elements(By.CSS_SELECTOR, 'body > div.page'):
                    award_details_data = award_details()
		
                    # Onsite Field -Abschnitt V: Auftragsvergabe/Konzessionsvergabe - Auftrags-Nr. 1 - Bezeichnung des Auftrags: Catering im Young Refugee Center >> Tag des Abschlusses des Vertrags/der Entscheidung über die Konzessionsvergabe
                    # Onsite Comment -None

                    award_details_data.award_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Tag des Abschlusses des Vertrags/der Entscheidung über die Konzessionsvergabe")]//following::td[1]').text
			
                    # Onsite Field -Abschnitt V: Auftragsvergabe/Konzessionsvergabe - Auftrags-Nr. 1 - Bezeichnung des Auftrags: Catering im Young Refugee Center >> Name und Anschrift des Auftragnehmers/Konzessionärs >> Offizielle Bezeichnung
                    # Onsite Comment -Note:Splite before	"Offizielle Bezeichnung" and "Postanschrift"

                    award_details_data.bidder_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Anschrift des Auftragnehmers/Konzessionärs")]//following::td[1]').text
			
                    # Onsite Field -VII.2) Angaben zu den Änderungen >> VII.2.3) Preiserhöhung
                    # Onsite Comment -None

                    award_details_data.netawardvaluelc = page_details.find_element(By.XPATH, '//*[contains(text(),"Preiserhöhung")]//following::td[1]').text
			
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
    urls = ["https://vergabe.muenchen.de/NetServer/PublicationSearchControllerServlet?function=SearchPublications&Gesetzesgrundlage=All&Category=ContractAward&thContext=awardPublications'"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,10):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[1]/div[3]/div/div[2]/div[3]/table[1]/tbody/tr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/div[3]/div/div[2]/div[3]/table[1]/tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/div[3]/div/div[2]/div[3]/table[1]/tbody/tr')))[records]
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/div[1]/div[3]/div/div[2]/div[3]/table[1]/tbody/tr'),page_check))
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