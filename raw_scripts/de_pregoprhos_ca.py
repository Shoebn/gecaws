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
SCRIPT_NAME = "de_pregoprhos_ca"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

# after opening url click on "Vergebene Aufträge=Assigned Orders" >> "Alle vergebenen Aufträge=All orders placed"
# format-1)if in type_of_procedure_actual "restricted tender=Beschränkte Ausschreibung" or "free hand allocation=Freihändige Vergabe" or "negotiated award without participation competition=Verhandlungsvergabe ohne Teilnahmewettbewerb" is present.
# format-2)if in type_of_procedure_actual "open procedure=Offenes Verfahren" is present.

    # Onsite Field -None
    # Onsite Comment -None
    notice_data.script_name = 'de_pregoprhos_ca'
    
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
    
    # Onsite Field -Erschienen am
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
    
    # Onsite Field -Ausschreibung
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Verfahrensart
    # Onsite Comment -split type_of_procedure_actual. here "VOB, Beschränkte Ausschreibung" take only "Beschränkte Ausschreibung".

    try:
        notice_data.type_of_procedure_actual = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Ausschreibung
    # Onsite Comment -split notice_no .eg., "Umgestaltung Freianlage/Schullandheim Oberthal (0003/23)" here take only "0003/23" in notice_no.

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -click on the tr

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'table.table.table-responsive > tbody > tr').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#pagePublicationDetails > div').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.document_type_description = page_details.find_element(By.CSS_SELECTOR, 'div.col-lg-12 > h1').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -1.if not availabel then take local_title in notice_summary_english.    2.use this selector for format-1.

    try:
        notice_data.notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),"Auftragsgegenstand:")]//following::tr[2]').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass

    # Onsite Field -None
    # Onsite Comment -1.use this selector for format-2.

    try:
        notice_data.notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),"II.1.4) Kurze Beschreibung:")]//following::td').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -
    # Onsite Comment -1.if not availabel then take local_title in local_description. 	  2.use this selector for format-1.
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Auftragsgegenstand:")]//following::tr[2]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass

    # Onsite Field -None
    # Onsite Comment -1.use this selector for format-2.

    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"II.1.4) Kurze Beschreibung:")]//following::td').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass

    # Onsite Field -None
    # Onsite Comment -1.for format-2. 	2.Replace follwing keywords with given respective kywords ('Dienstleistungen =Service'),('Bauauftrag=works'),('Lieferauftrag=Supply')

    try:
        notice_data.notice_contract_type = page_details.find_element(By.XPATH, '//*[contains(text()," Art des Auftrags")]//following::td').text
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass

    # Onsite Field -None
    # Onsite Comment -1.use this xpath for format-2.

    try:
        notice_data.est_amount = page_details.find_element(By.XPATH, '//*[contains(text(),"Gesamtwert der Beschaffung")]//following::td').text
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -1.use this xpath for format-2.

    try:
        notice_data.grossbudgetlc = page_details.find_element(By.XPATH, '//*[contains(text(),"Gesamtwert der Beschaffung")]//following::td').text
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div:nth-child(1) > table > tbody'):
            customer_details_data = customer_details()
        # Onsite Field -Vergabestelle
        # Onsite Comment -None

            try:
                customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
            customer_details_data.org_country = 'DE'
            customer_details_data.org_language = 'DE'
        # Onsite Field -None
        # Onsite Comment -1.use this xpath for format-1.

            try:
                customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Anschrift:")]//following::td').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass

        # Onsite Field -None
        # Onsite Comment -1.use this xpath for format-2. 	2.split org_address between "Postanschrift:" and "NUTS-Code:"

            try:
                customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"I.1) Name und Adressen")]//following::td').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -1.use this xpath for format-1.

            try:
                customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Telefonnummer:")]//following::td').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass

        # Onsite Field -None
        # Onsite Comment -1.use this selector for format-2. 	2.split org_phone between "Telefon: " and "E-Mail:".

            try:
                customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"I.1) Name und Adressen")]//following::td').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -1.use this xpath for format-1.

            try:
                customer_details_data.org_fax = page_details.find_element(By.XPATH, '//*[contains(text(),"Faxnummer:")]//following::td').text
            except Exception as e:
                logging.info("Exception in org_fax: {}".format(type(e).__name__))
                pass

        # Onsite Field -None
        # Onsite Comment -1.use this xpath for format-2. 	2.split org_fax after "Fax:".

            try:
                customer_details_data.org_fax = page_details.find_element(By.XPATH, '//*[contains(text(),"I.1) Name und Adressen")]//following::td').text
            except Exception as e:
                logging.info("Exception in org_fax: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -1.use this xpath for format-1.	

            try:
                customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"E-Mail:")]//following::td').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass

        # Onsite Field -None
        # Onsite Comment -1.use this xpath for format-2. 	2.split org_email after "E-Mail:" and "Fax:".

            try:
                customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"I.1) Name und Adressen")]//following::td').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass


        # Onsite Field -None
        # Onsite Comment -1.use this selector for format-2. 	 2.split customer_nuts between "NUTS-Code:" and "Kontaktstelle(n):".

            try:
                customer_details_data.customer_nuts = page_details.find_element(By.XPATH, '//*[contains(text(),"I.1) Name und Adressen")]//following::td').text
            except Exception as e:
                logging.info("Exception in customer_nuts: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -1.use this xpath for format-2.          2.split org_website after "Hauptadresse: (URL)".

            try:
                customer_details_data.org_website = page_details.find_element(By.XPATH, '//*[contains(text(),"Hauptadresse: (URL)")]//following::a').text
            except Exception as e:
                logging.info("Exception in org_website: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -1.use this xpath for format-1.    2.postal_code take from last line. eg.,"66119 Saarbrücken" take only "66119" in postal_code.

            try:
                customer_details_data.postal_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Anschrift:")]//following::td').text
            except Exception as e:
                logging.info("Exception in postal_code: {}".format(type(e).__name__))
                pass

        # Onsite Field -None
        # Onsite Comment -1.use this selector for format-2. 		2.split postal_code between "Postleitzahl / Ort: " and "Land". 	3.take only number in postal_code .don't grab city_name.

            try:
                customer_details_data.postal_code = page_details.find_element(By.XPATH, '//*[contains(text(),"I.1) Name und Adressen")]//following::td').text
            except Exception as e:
                logging.info("Exception in postal_code: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -1.use this xpath for format-1.     2.org_city take from last line. eg.,"66119 Saarbrücken" take only "Saarbrücken" in org_city

            try:
                customer_details_data.org_city = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Anschrift:")]//following::td').text
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass

        # Onsite Field -None
        # Onsite Comment -1.use this xpath for format-2. 	2.split org_city between "Postleitzahl / Ort: " and "Land". 		3.take only name.don't grab number i.e org_city.

            try:
                customer_details_data.org_city = page_details.find_element(By.XPATH, '//*[contains(text(),"I.1) Name und Adressen")]//following::td').text
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass


        # Onsite Field -None
        # Onsite Comment -1.use this xpath for format-2. 		2.split contact_person between "Kontaktstelle(n):" and "Telefon:"

            try:
                customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"I.1) Name und Adressen")]//following::td').text
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
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, '#pagePublicationDetails > div '):
            lot_details_data = lot_details()
        # Onsite Field -Ausschreibung
        # Onsite Comment -1.use this xpath for format-1 and format-2.

            try:
                lot_details_data.lot_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass

        # Onsite Field -None
        # Onsite Comment -1.use this xpath for format-2. 	2.split lot_title "Los 1 (KG410,420,430) Los-Nr: 1" here take only "Los 1 (KG410,420,430)" in lot_title. 	       2.if the multiple lots avaialbel on page than take each records.   	   3.use this url for reference "https://vergabe.landbw.de/NetServer/PublicationControllerServlet?function=Detail&TOID=54321-NetTender-186e06abfda-60fbc977b0522270&Category=ContractAward". 	4.if lot_title is not available then local_title as lot_title.
            try:
                lot_details_data.lot_title = page_details.find_element(By.XPATH, '//*[contains(text(),"II.2.1) Bezeichnung des Auftrags:")]//following::td').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass

        # Onsite Field -None
        # Onsite Comment -1.use this xpath for format-2. 	2.split lot_title "Fahrgestell & Aufbau Los-Nr: 1" here take only "Los-Nr: 1" in lot_actual_number.

            try:
                lot_details_data.lot_actual_number = page_details.find_element(By.XPATH, '//*[contains(text(),"II.2.1) Bezeichnung des Auftrags:")]//following::td').text
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -1.use this xpath for format-1.     2.if not availabel then take local_title in lot_description.

            try:
                lot_details_data.lot_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Auftragsgegenstand:")]//following::tr[2]').text
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass

        # Onsite Field -None
        # Onsite Comment -1.for format-2. 	2.Replace follwing keywords with given respective kywords ('Dienstleistungen =Service'),('Bauauftrag=works'),('Lieferauftrag=Supply')

            try:
                lot_details_data.contract_type = page_details.find_element(By.XPATH, '//*[contains(text()," Art des Auftrags")]//following::td').text
            except Exception as e:
                logging.info("Exception in contract_type: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -1.use this xpath for format-2. 	2.take all nuts seperatly for each lot.

            try:
                lot_details_data.lot_nuts = page_details.find_element(By.XPATH, '//*[contains(text(),"NUTS-Code:")]//following::td').text
            except Exception as e:
                logging.info("Exception in lot_nuts: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -None

            try:
                for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div:nth-child(3) > table > tbody'):
                    lot_cpvs_data = lot_cpvs()
		
                    # Onsite Field -None
                    # Onsite Comment -1.use this xpath for format-2. 				2.eg.,"CPV-Code Hauptteil: 77211500-7" here lot_cpvs_code split after "CPV-Code Hauptteil:". and also in lot_cpvs_code "77211500".  				3.grab only if possible. use this url for referencs "https://prego-vergabeplattform.prhos.com/NetServer/PublicationControllerServlet?function=Detail&TOID=54321-NetTender-188429b7a03-48d55993cf5d1f5c&Category=ContractAward"

                    lot_cpvs_data.lot_cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"II.2.2) Weitere(r) CPV-Code(s)")]//following::td').text
			
                    lot_cpvs_data.lot_cpvs_cleanup()
                    lot_details_data.lot_cpvs.append(lot_cpvs_data)
            except Exception as e:
                logging.info("Exception in lot_cpvs: {}".format(type(e).__name__))
                pass
			
        # Onsite Field -None
        # Onsite Comment -None

            try:
                for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div:nth-child(3) > table > tbody'):
                    lot_criteria_data = lot_criteria()
		
                    # Onsite Field -None
                    # Onsite Comment -1.use this xpath for format-2.		2.split lot_criteria_title. eg., "Name: Preis (40%), Gewichtung: 40,00" here take only "Preis" in lot_criteria_title.

                    lot_criteria_data.lot_criteria_title = page_details.find_element(By.XPATH, '//*[contains(text(),"Zuschlagskriterien")]//following::td').text
			
                    # Onsite Field -None
                    # Onsite Comment -1.use this xpath for format-2.		2.split lot_criteria_weight. eg., "Name: Preis (40%), Gewichtung: 40,00" here take only "40%" in lot_criteria_weight.

                    lot_criteria_data.lot_criteria_weight = page_details.find_element(By.XPATH, '//*[contains(text(),"Zuschlagskriterien")]//following::td').text
			
                    lot_criteria_data.lot_criteria_cleanup()
                    lot_details_data.lot_criteria.append(lot_criteria_data)
            except Exception as e:
                logging.info("Exception in lot_criteria: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -None

            try:
                for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div:nth-child(5) > table > tbody'):
                    award_details_data = award_details()
		
                    # Onsite Field -None
                    # Onsite Comment -1.take only first line in bidder_name.
                    award_details_data.bidder_name = page_details.find_element(By.XPATH, '//*[contains(text(),"1. Auftragnehmer")]//following::td').text

                    # Onsite Field -None
                    # Onsite Comment -1.use this xpath for format-2. 	2.split bidder_name before "Postanschrift:".
                    award_details_data.bidder_name = page_details.find_element(By.XPATH, '//*[contains(text(),"V.2.3) Name und Anschrift des Wirtschaftsteilnehmers, zu dessen Gunsten der Zuschlag erteilt wurde")]//following::td').text
			
                    # Onsite Field -None
                    # Onsite Comment -1.use this xpath for format-1.
                    award_details_data.address = page_details.find_element(By.XPATH, '//*[contains(text(),"1. Auftragnehmer")]//following::td').text
			
                    # Onsite Field -None
                    # Onsite Comment -1.use this xpath for format-2. 	2.split bidder_name before "Postanschrift:".
                    award_details_data.address = page_details.find_element(By.XPATH, '//*[contains(text(),"V.2.3) Name und Anschrift des Wirtschaftsteilnehmers, zu dessen Gunsten der Zuschlag erteilt wurde")]//following::td').text
			
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
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div:nth-child(3) > table > tbody'):
            cpvs_data = cpvs()
        # Onsite Field -None
        # Onsite Comment -1.use this xpath for format-2. 	2.eg., "34144210-3" here take only "34144210" in cpv_code.

            try:
                cpvs_data.cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"CPV-Code Hauptteil")]//following::td').text
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
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div:nth-child(3) > table > tbody'):
            funding_agencies_data = funding_agencies()
        # Onsite Field -None
        # Onsite Comment -1.use this xpath for format-2. 			2.if in below text written as " financed by European Union funds: No  " than pass the "None " in field name "funding_agency" "II.2.13) Information on European Union funds  >  The contract is related to a project and/or program financed by EU funds: no  " if the abve  text written as " financed by European Union funds: YES  " than pass the "Funding agency" name as "European Agency (internal id: 1344862) " in field name "T.FUNDING_AGENCIES::TEXT"

            try:
                funding_agencies_data.funding_agency = page_details.find_element(By.XPATH, '//*[contains(text(),"II.2.13) Angaben zu Mitteln der Europäischen Union")]//following::td').text
            except Exception as e:
                logging.info("Exception in funding_agency: {}".format(type(e).__name__))
                pass
        
            funding_agencies_data.funding_agencies_cleanup()
            notice_data.funding_agencies.append(funding_agencies_data)
    except Exception as e:
        logging.info("Exception in funding_agencies: {}".format(type(e).__name__)) 
        pass

    try:
        notice_data.dispatch_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Tag der Absendung dieser Bekanntmachung:")]//following::td').text
    except Exception as e:
        logging.info("Exception in dispatch_date: {}".format(type(e).__name__))
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
    urls = ["https://prego-vergabeplattform.prhos.com/NetServer/PublicationSearchControllerServlet?function=SearchPublications&Gesetzesgrundlage=All&Category=ContractAward&thContext=awardPublications"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,3):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[1]/div[2]/div/div/div/div[2]/table[1]/tbody/tr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/div[2]/div/div/div/div[2]/table[1]/tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/div[2]/div/div/div/div[2]/table[1]/tbody/tr')))[records]
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/div[1]/div[2]/div/div/div/div[2]/table[1]/tbody/tr'),page_check))
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