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
SCRIPT_NAME = "de_vg_rlp"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    # Onsite Field -None
    # Onsite Comment -click on "Erweiterte Suche"  > "Suchen" to get all the data and take data if available in "Veröffentlichungstyp" select "Beabsichtigte Ausschreibung" and in "Vergabeordnung" select "Alle" for gpn in "Veröffentlichungstyp" select "Ausschreibung" and in "Vergabeordnung" select "Alle" for spn in "Veröffentlichungstyp" select "Vergebener Auftrag" and in "Vergabeordnung" select "Alle" fro ca
    notice_data.script_name = 'de_vg_rlp'
    
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
    # Onsite Comment -if document_type_description have keyword "Beabsichtigte Ausschreibung" then  notice type will be 2 , "Ausschreibung" then notice type will be 4 , "Vergebener Auftrag" then notice type will be 7
    notice_data.notice_type = 4
    
    # Onsite Field -Typ
    # Onsite Comment -for document_type_description split data from given selector for eg: from "UVgO Beabsichtigte Ausschreibung" take only "Beabsichtigte Ausschreibung" repeat the same for spn and ca.

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Bezeichnung
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
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
    
    # Onsite Field -Angebots- / Teilnahmefrist
    # Onsite Comment -take notice_deadline when document_type_description have keyword "Ausschreibung" only  and take notice_deadline as threshold date 1 year after the publish_date when document_type_description have keyword "Beabsichtigte Ausschreibung"

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(2)").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Aktion
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(6) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#mainBox').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Ausschreibungs-ID
    # Onsite Comment -None

    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"Ausschreibungs-ID")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Kurze Beschreibung
    # Onsite Comment -for notice_summary_english click on "Verfahrensangaben" in detail page and if the "Kurze Beschreibung" field is not available pass the local_title in notice_summary_english

    try:
        notice_data.notice_summary_english = page_details1.find_element(By.XPATH, '//*[contains(text(),"Kurze Beschreibung")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_details1.find_element(By.XPATH, '//*[contains(text(),"Kurze Beschreibung")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -UST.-ID
    # Onsite Comment -Verfahrensangaben > "Zur Angebotsabgabe / Teilnahme auffordernde Stelle " or "Auftraggeber"

    try:
        notice_data.vat = page_details1.find_element(By.XPATH, '//*[contains(text(),"UST.-ID")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in vat: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Art des Auftrags
    # Onsite Comment -take only tick mark(✔) data if available and Replace following keywords with given respective keywords ("Dienstleistung" = service , "Lieferleistung"  = supply,"Bauleistung" = work)

    try:
        notice_data.notice_contract_type = page_details1.find_element(By.XPATH, '//*[contains(text(),"Art des Auftrags")]//following::span[1]').text
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Geschätzter Wert
    # Onsite Comment -take data in numeric if available in the detail page (if the given selector is not working use the below selector :- '//*[contains(text(),"Gesamtwert der Beschaffung (ohne MwSt.)")]//following::div[1]'/'//*[contains(text(),"Angaben zum Wert des Auftrags/Loses (ohne MwSt.)")]//following::span[2]' )

    try:
        notice_data.grossbudgetlc = page_details1.find_element(By.XPATH, '//*[contains(text(),"Geschätzter Wert")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Geschätzter Wert
    # Onsite Comment -take data in numeric if available in the detail page (if the given selector is not working use the below selector :- '//*[contains(text(),"Gesamtwert der Beschaffung (ohne MwSt.)")]//following::div[1]'/'//*[contains(text(),"Angaben zum Wert des Auftrags/Loses (ohne MwSt.)")]//following::span[2]' )

    try:
        notice_data.est_amount = page_details1.find_element(By.XPATH, '//*[contains(text(),"Geschätzter Wert")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Verfahrensart
    # Onsite Comment -None
    try:
        notice_data.type_of_procedure_actual = page_details1.find_element(By.XPATH, "//*[contains(text(),"Verfahrensart")]//following::span[1]").text
        notice_data.type_of_procedure = fn.procedure_mapping("assets/de_vg_rlp_procedure",notice_data.type_of_procedure_actual)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Technische und berufliche Leistungsfähigkeit
    # Onsite Comment -take only tick mark(✔) data

    try:
        notice_data.eligibility = page_details1.find_element(By.XPATH, '//*[contains(text(),"Technische und berufliche Leistungsfähigkeit")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in eligibility: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -in page detail click on "Verfahrensangaben" for customer detail  Verfahrensangaben > "Zur Angebotsabgabe / Teilnahme auffordernde Stelle " or "Auftraggeber"

    try:              
        for single_record in page_details1.find_elements(By.CSS_SELECTOR, '#mainBox'):
            customer_details_data = customer_details()
        # Onsite Field -Offizielle Bezeichnung
        # Onsite Comment -None

            try:
                customer_details_data.org_name = page_details1.find_element(By.XPATH, '//*[contains(text(),"Offizielle Bezeichnung")]//following::div[1]/span[1]').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Postanschrift
        # Onsite Comment -None

            try:
                customer_details_data.org_address = page_details1.find_element(By.XPATH, '//*[contains(text(),"Postanschrift")]//following::div[1]/span[1]').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Ort
        # Onsite Comment -None

            try:
                customer_details_data.org_city = page_details1.find_element(By.XPATH, '//*[contains(text(),"Ort")]//following::div[1]/span[1]').text
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Postleitzahl
        # Onsite Comment -None

            try:
                customer_details_data.postal_code = page_details1.find_element(By.XPATH, '//*[contains(text(),"Postleitzahl")]//following::div[1]/span[1]').text
            except Exception as e:
                logging.info("Exception in postal_code: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -zu Händen von
        # Onsite Comment -None

            try:
                customer_details_data.contact_person = page_details1.find_element(By.XPATH, '//*[contains(text(),"zu Händen von")]//following::div[1]/span[1]').text
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Telefon
        # Onsite Comment -None

            try:
                customer_details_data.org_phone = page_details1.find_element(By.XPATH, '//*[contains(text(),"Telefon")]//following::div[1]/span[1]').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -E-Mail
        # Onsite Comment -None

            try:
                customer_details_data.org_email = page_details1.find_element(By.XPATH, '//*[contains(text(),"E-Mail")]//following::div[1]/span[1]').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Fax
        # Onsite Comment -None

            try:
                customer_details_data.org_fax = page_details1.find_element(By.XPATH, '//*[contains(text(),"Fax")]//following::div[1]/span[1]').text
            except Exception as e:
                logging.info("Exception in org_fax: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Hauptadresse (URL)
        # Onsite Comment -'//*[contains(text(),"Internet-Adresse (URL)")]//following::a[1]' and '//*[contains(text(),"Adresse des Beschafferprofils (URL)")]//following::a[1]' use this selectors if link is available in this field

            try:
                customer_details_data.org_website = page_details1.find_element(By.XPATH, '//*[contains(text(),"Hauptadresse (URL)")]//following::a[1]').text
            except Exception as e:
                logging.info("Exception in org_website: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -NUTS Code
        # Onsite Comment -None

            try:
                customer_details_data.customer_nuts = page_details1.find_element(By.XPATH, '//*[contains(text(),"NUTS Code")]//following::div[1]/span[1]').text
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
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#mainBox'):
            cpvs_data = cpvs()
        # Onsite Field -Auftragsgegenstand
        # Onsite Comment -take only "Auftragsgegenstand" field data if available in detail pg and take numeric value only and if the cpv is not available in detail pg then take auto cpv

            try:
                cpvs_data.cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Auftragsgegenstand")]//following::div').text
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
        for single_record in page_details1.find_elements(By.CSS_SELECTOR, '#mainBox'):
            funding_agencies_data = funding_agencies()
        # Onsite Field -Angaben zu Mitteln der Europäischen Union
        # Onsite Comment -if the below text get tick mark than the tender will be funded and pass static funding agency as "European Union" (  1344862 )  Information on European Union funds = "Angaben zu Mitteln der Europäischen Union" > The contract is related to a project and/or program funded by EU funds ="Der Auftrag steht in Verbindung mit einem Vorhaben und/oder Programm, das aus Mitteln der EU finanziert wird"

            try:
                funding_agencies_data.funding_agency = page_details1.find_element(By.XPATH, '//*[contains(text(),"Angaben zu Mitteln der Europäischen Union")]//following::div[1]').text
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
        for single_record in page_details1.find_elements(By.CSS_SELECTOR, '#mainBox'):
            tender_criteria_data = tender_criteria()
        # Onsite Field -Zuschlagskriterien
        # Onsite Comment -take tender_criteria if available in page_detail and take only tick mark(✔) data

            try:
                tender_criteria_data.tender_criteria_title = page_details1.find_element(By.XPATH, '//*[contains(text(),"Zuschlagskriterien")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in tender_criteria_title: {}".format(type(e).__name__))
                pass
        
            tender_criteria_data.tender_criteria_cleanup()
            notice_data.tender_criteria.append(tender_criteria_data)
    except Exception as e:
        logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -if the lots are awarded to multipule bidder than select all the bidder name lot wise  for lot_detail ref use this link (ex: https://landesverwaltung.vergabe.rlp.de/VMPSatellite/public/company/project/CXPDYD8YCDJ/de/processdata?4)

    try:              
        for single_record in page_details1.find_elements(By.CSS_SELECTOR, '#mainBox'):
            lot_details_data = lot_details()
        # Onsite Field -Los-Nr.
        # Onsite Comment -None

            try:
                lot_details_data.lot_actual_number = page_details1.find_element(By.XPATH, '//*[contains(text(),"Los-Nr.")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Bezeichnung
        # Onsite Comment -take lot_title only when the field name "Auftragsgegenstand" > "Beschreibung" is available   if it is not available pass the local_title in lot_title

            try:
                lot_details_data.lot_title = page_details1.find_element(By.XPATH, '//*[contains(text(),"Bezeichnung")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Beschreibung der Beschaffung
        # Onsite Comment -take lot_ description only when the field name "Auftragsgegenstand" > "Beschreibung der Beschaffung" is available  if it is not available pass the local_title in lot_ description

            try:
                lot_details_data.lot_description = page_details1.find_element(By.XPATH, '//*[contains(text(),"Beschreibung der Beschaffung")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Gesamtwert der Beschaffung (ohne MwSt.)
        # Onsite Comment -take only tick mark(✔) data and  take data in numeric if available in the detail page (use the below selector :- '//*[contains(text(),"Gesamtwert der Beschaffung (ohne MwSt.)")]//following::div[1]' / '//*[contains(text(),"Geschätzter Wert")]//following::div[1]' /  '//*[contains(text(),"Angaben zum Wert des Auftrags/Loses (ohne MwSt.)")]//following::span[5]' for some tender)

            try:
                lot_details_data.lot_grossbudget_lc = page_details1.find_element(By.XPATH, '//*[contains(text(),"Gesamtwert der Beschaffung (ohne MwSt.)")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Beginn
        # Onsite Comment -take only date from the on site  "Laufzeit des Vertrags, der Rahmenvereinbarung oder des dynamischen Beschaffungssystems > Beginn "

            try:
                lot_details_data.contract_start_date = page_details1.find_element(By.XPATH, '//*[contains(text(),"Beginn")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in contract_start_date: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Ende
        # Onsite Comment -take only date from the on site  "Laufzeit des Vertrags, der Rahmenvereinbarung oder des dynamischen Beschaffungssystems > Ende "

            try:
                lot_details_data.contract_end_date = page_details1.find_element(By.XPATH, '//*[contains(text(),"Ende")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in contract_end_date: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -None

            try:
                for single_record in page_details1.find_elements(By.CSS_SELECTOR, '#mainBox'):
                    lot_cpvs_data = lot_cpvs()
		
                    # Onsite Field -Weiterer CPV Code
                    # Onsite Comment -take only "Weiterer CPV Code" field data if available in detail pg and take numeric value only and if the cpv is not available in detail pg then take auto cpv

                    lot_cpvs_data.lot_cpv_code = page_details1.find_element(By.XPATH, '//*[contains(text(),"Weiterer CPV Code")]//following::div[1]').text
			
                    lot_cpvs_data.lot_cpvs_cleanup()
                    lot_details_data.lot_cpvs.append(lot_cpvs_data)
            except Exception as e:
                logging.info("Exception in lot_cpvs: {}".format(type(e).__name__))
                pass
			
        # Onsite Field -None
        # Onsite Comment -None

            try:
                for single_record in page_details1.find_elements(By.CSS_SELECTOR, '#mainBox'):
                    lot_criteria_data = lot_criteria()
		
                    # Onsite Field -Zuschlagskriterien
                    # Onsite Comment -take "Zuschlagskriterien" as lot_criteria if available in page_detail in field name "Bezeichnung" and  take only tick mark(✔) data

                    lot_criteria_data.lot_criteria_title = page_details1.find_element(By.XPATH, '//*[contains(text(),"Zuschlagskriterien")]//following::div[1]').text
			
                    # Onsite Field -Zuschlagskriterien
                    # Onsite Comment -take "Zuschlagskriterien" as lot_criteria if available in page_detail in field name "Bezeichnung" and  take only tick mark(✔) data

                    lot_criteria_data.lot_criteria_weight = page_details1.find_element(By.XPATH, '//*[contains(text(),"Zuschlagskriterien")]//following::div[1]').text
			
                    lot_criteria_data.lot_criteria_cleanup()
                    lot_details_data.lot_criteria.append(lot_criteria_data)
            except Exception as e:
                logging.info("Exception in lot_criteria: {}".format(type(e).__name__))
                pass
			
        # Onsite Field -None
        # Onsite Comment -take data from "Verfahren" > "Allgemeine Angaben" and "Auftragsvergabe" / "Verfahren" > "Name und Anschrift des Wirtschaftsteilnehmers, zu dessen Gunsten der Zuschlag erteilt wurde" only and for ref use this link('https://landesverwaltung.vergabe.rlp.de/VMPSatellite/public/company/project/CXPDYY6YCAY/de/processdata?8')

            try:
                for single_record in page_details1.find_elements(By.CSS_SELECTOR, '#mainBox'):
                    award_details_data = award_details()
		
                    # Onsite Field -Offizielle Bezeichnung
                    # Onsite Comment -None

                    award_details_data.bidder_name = page_details1.find_element(By.XPATH, '//*[contains(text(),"Offizielle Bezeichnung")]//following::div[1]').text
			
                    # Onsite Field -Ort
                    # Onsite Comment -'//*[contains(text(),"Postleitzahl")]//following::div[1]'   take both this fields in address

                    award_details_data.address = page_details1.find_element(By.XPATH, '//*[contains(text(),"Ort")]//following::div[1]').text
			
                    # Onsite Field -Angaben zum Wert des Auftrags/Loses (ohne MwSt.)
                    # Onsite Comment -take data in numeric if available in the detail page and take only tick mark(✔) data

                    award_details_data.grossawardvaluelc = page_details1.find_element(By.XPATH, '//*[contains(text(),"Angaben zum Wert des Auftrags/Loses (ohne MwSt.)")]//following::span[4]').text
			
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
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'table.margin-bottom-20'):
            attachments_data = attachments()
        # Onsite Field -Typ
        # Onsite Comment -None

            try:
                attachments_data.file_type = page_details.find_element(By.CSS_SELECTOR, 'table.margin-bottom-20 > tbody >tr > td:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Dateiname
        # Onsite Comment -None

            try:
                attachments_data.file_name = page_details.find_element(By.CSS_SELECTOR, 'table.margin-bottom-20 > tbody >tr > td:nth-child(1)').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Größe
        # Onsite Comment -None

            try:
                attachments_data.file_size = page_details.find_element(By.CSS_SELECTOR, 'table.margin-bottom-20 > tbody >tr > td:nth-child(3)').text
            except Exception as e:
                logging.info("Exception in file_size: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Aktion
        # Onsite Comment -for more attachment click on "Vergabeunterlagen" in detail page (click on "Alle Dokumente als ZIP-Datei herunterladen" to download the document and selector for the button 'div.csx-project-form > div > a' )

            attachments_data.external_url = page_details.find_element(By.CSS_SELECTOR, 'td:nth-child(5) > a').get_attribute('href')
            
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
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
page_details1 = fn.init_chrome_driver(arguments)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://www.vergabe.rlp.de/VMPCenter/company/welcome.do'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,6):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="listTemplate"]/table/tbody/tr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="listTemplate"]/table/tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="listTemplate"]/table/tbody/tr')))[records]
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="listTemplate"]/table/tbody/tr'),page_check))
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
    
    page_details1.quit()
    
    output_json_file.copyFinalJSONToServer(output_json_folder)
    