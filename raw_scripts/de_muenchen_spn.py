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



# select data in tab  "Alle Ausschreibungen" + "Ausschreibungen" + ["Natioal-EU"/"National"/"EU"]




# Foemat 1)Public announcement=Öffentliche Ausschreibung
# Format 2)Negotiation procedure with participation competition=Verhandlungsverfahren mit Teilnahmewettbewerb
# Format 3)Open procedure=Offenes Verfahren





#for cpv
#Case 1 : Tender CPV given, but lot CPV not given, than it will not be repeated in Lots.
#Case 2: Tender CPV not given, lots CPV Given. it will be repeated in Tender CPV comma separated.
#Case 3: Tender CPV given, lot CPV also given, In this case also lot CPVs will be repeated in Tender CPV comma separated. But in this make sure that Tender CPV should be first followed by lot CPVs.




NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "de_muenchen_spn"
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
    notice_data.script_name = 'de_muenchen_spn'
    
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
    
    # Onsite Field -Note:Replace following kegword("National - EU=0","National=0","EU=2")
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_type = 4
    
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
    
    # Onsite Field -Ausschreibung
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'tbody > tr > td:nth-child(2)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Abgabefrist
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "tbody > tr > td:nth-child(6)").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Verfahrensart
    # Onsite Comment -None
    try:
        notice_data.type_of_procedure_actual = tender_html_element.find_element(By.CSS_SELECTOR, "tbody > tr > td:nth-child(4)").text
        type_of_procedure = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("assets/de_muenchen_spn_procedure",type_of_procedure)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
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
        

# Format 1)
# Ref_url=https://vergabe.muenchen.de/NetServer/PublicationControllerServlet?function=Detail&TOID=54321-NetTender-18b8529ee9f-509a087497baf64f&Category=InvitationToTender    
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.downloadDocuments > a'):
            attachments_data = attachments()
        # Onsite Field -Download
        # Onsite Comment -Note:Don't take file extenstion ex.,(.pdf) 		Note:First click on "div.downloadDocuments > a" then second click on hear "tbody > tr > td > a" and grab the data 		Note:Open page_main the first click "Alles auswählen" then second click "Auswahl herunterladen"

            try:
                attachments_data.file_name = page_details1.find_element(By.CSS_SELECTOR, 'tbody > tr > td > a').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Download
        # Onsite Comment -None

            attachments_data.external_url = page_details1.find_element(By.CSS_SELECTOR, 'tbody > tr > td > a').get_attribute('href')
            
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    # Onsite Field -Vergabenr
    # Onsite Comment -None

    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"Vergabenr")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'body > div.page'):
            customer_details_data = customer_details()
        # Onsite Field -Name und Anschrift
        # Onsite Comment -Note:Take only first line

            try:
                customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Anschrift")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Name und Anschrift
        # Onsite Comment -None

            try:
                customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Anschrift")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Telefonnummer
        # Onsite Comment -None

            try:
                customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Telefonnummer")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Telefaxnummer
        # Onsite Comment -None

            try:
                customer_details_data.org_fax = page_details.find_element(By.XPATH, '//*[contains(text(),"Telefaxnummer")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in org_fax: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -E-Mail-Adresse
        # Onsite Comment -None

            try:
                customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"E-Mail-Adresse")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Internet-Adresse
        # Onsite Comment -None

            try:
                customer_details_data.org_website = page_details.find_element(By.XPATH, '//*[contains(text(),"Internet-Adresse")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in org_website: {}".format(type(e).__name__))
                pass
        
            customer_details_data.org_country = 'DE'
            customer_details_data.org_language = 'DE'
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    # Onsite Field -5. Art und Umfang sowie Ort der Leistung: >> Art der Leistung:
    # Onsite Comment -None

    try:
        notice_data.notice_contract_type = page_details.find_element(By.XPATH, '//*[contains(text(),"Art der Leistung:")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -5. Art und Umfang sowie Ort der Leistung: >> Menge und Umfang
    # Onsite Comment -None

    try:
        notice_data.tender_quantity_uom = page_details.find_element(By.XPATH, '//*[contains(text(),"Menge und Umfang")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in tender_quantity_uom: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -Note:if the lot published in "5. Type and scope as well as location of the service: > Quantity and scope:", tha take the lots in a Lot loop. refer below url  https://vergabe.muenchen.de/NetServer/PublicationControllerServlet?function=Detail&TOID=54321-NetTender-18b36a84a5a-2ceb2bea4a86c263&Category=InvitationToTender LotAcualNumber = 'Lot1" LotTitle = Lot 1: Supply of all types of filters

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'body > div.page'):
            lot_details_data = lot_details()
        # Onsite Field -5. Art und Umfang sowie Ort der Leistung: >> Menge und Umfang:
        # Onsite Comment -Note:1)here "Los 1: Lieferung von Filtern aller Art" take "Los 1" as lot_actual_number	2)take all lot_actual_number

            try:
                lot_details_data.lot_actual_number = page_details.find_element(By.XPATH, '//*[contains(text(),"Menge und Umfang")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -5. Art und Umfang sowie Ort der Leistung: >> Menge und Umfang:
        # Onsite Comment -Note:1)here "Los 1: Lieferung von Filtern aller Art" take "Lieferung von Filtern aller Art" as lot_title	2)take all lot_title

            try:
                lot_details_data.lot_title = page_details.find_element(By.XPATH, '//*[contains(text(),"Menge und Umfang")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass

# Format 2)
# Ref_urlhttps://vergabe.muenchen.de/NetServer/PublicationControllerServlet?function=Detail&TOID=54321-NetTender-18b7059437c-2d6328db64e75852&Category=InvitationToTender    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.downloadDocuments > a'):
            attachments_data = attachments()
        # Onsite Field -Download
        # Onsite Comment -Note:Don't take file extenstion ex.,(.pdf) 		Note:First click on "div.downloadDocuments > a" then second click on hear "tbody > tr > td > a" and grab the data 		Note:Open page_main the first click "Alles auswählen" then second click "Auswahl herunterladen"

            try:
                attachments_data.file_name = page_details1.find_element(By.CSS_SELECTOR, 'tbody > tr > td > a').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Download
        # Onsite Comment -None

            attachments_data.external_url = page_details1.find_element(By.CSS_SELECTOR, 'tbody > tr > td > a').get_attribute('href')
            
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'body > div.page'):
            customer_details_data = customer_details()
        # Onsite Field -Vertragspartei und Dienstleister >> Beschaffer >> Offizielle Bezeichnung
        # Onsite Comment -Note:Splite org_name after "Offizielle Bezeichnung" and "Registrierungsnummer"

            try:
                customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Beschaffer")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Vertragspartei und Dienstleister >> Beschaffer >> Internet-Adresse (URL)
        # Onsite Comment -None

            try:
                customer_details_data.org_address = page_details.find_element(By.CSS_SELECTOR, 'tbody > tr:nth-child(3) > td:nth-child(2) > a:nth-child(3)').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Vertragspartei und Dienstleister >> Beschaffer >> Postleitzahl / Ort
        # Onsite Comment -Note:Splite after "Postleitzahl / Ort" and "NUTS-3-Code"

            try:
                customer_details_data.postal_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Beschaffer")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in postal_code: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Vertragspartei und Dienstleister >> Beschaffer >> NUTS-3-Code
        # Onsite Comment -Note:Splite after "NUTS-3-Code" and "Land"

            try:
                customer_details_data.customer_nuts = page_details.find_element(By.XPATH, '//*[contains(text(),"Beschaffer")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in customer_nuts: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Vertragspartei und Dienstleister >> Beschaffer >> E-Mail
        # Onsite Comment -Note:Splite after "E-Mai" and "Art des öffentlichen Auftraggebers"

            try:
                customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Beschaffer")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Vertragspartei und Dienstleister >> Beschaffer >> Art des öffentlichen Auftraggebers
        # Onsite Comment -Note:Splite after "Art des öffentlichen Auftraggebers" and "Haupttätigkeiten des öffentlichen Auftraggebers"

            try:
                customer_details_data.type_of_authority_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Beschaffer")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in type_of_authority_code: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Vertragspartei und Dienstleister >> Beschaffer >> Haupttätigkeiten des öffentlichen Auftraggebers
        # Onsite Comment -Note:Splite after "Haupttätigkeiten des öffentlichen Auftraggebers" and "Profil des Erwerbers (URL)"

            try:
                customer_details_data.customer_main_activity = page_details.find_element(By.XPATH, '//*[contains(text(),"Beschaffer")]//following::td[1]').text
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
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Beschreibung")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Verfahren >> Umfang der Auftragsvergabe
    # Onsite Comment -None

    try:
        notice_data.netbudgetlc = page_details.find_element(By.XPATH, '//*[contains(text(),"Umfang der Auftragsvergabe")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in netbudgetlc: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.class_at_source = 'CPV'
    
    # Onsite Field -Verfahren >> Hauptklassifikation
    # Onsite Comment -None

    try:
        notice_data.cpv_at_source = page_details.find_element(By.XPATH, '//*[contains(text(),"Hauptklassifikation")]//following::td[3]').text
    except Exception as e:
        logging.info("Exception in cpv_at_source: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Verfahren >> Hauptklassifikation
    # Onsite Comment -None

    try:
        notice_data.cpv_at_source = page_details.find_element(By.XPATH, '//*[contains(text(),"Hauptklassifikation")]//following::td[5]').text
    except Exception as e:
        logging.info("Exception in cpv_at_source: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'body > div.page'):
            cpvs_data = cpvs()
        # Onsite Field -Verfahren >> Hauptklassifikation
        # Onsite Comment -None

            try:
                cpvs_data.cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Hauptklassifikation")]//following::td[3]').text
            except Exception as e:
                logging.info("Exception in cpv_code: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Verfahren >> Hauptklassifikation
        # Onsite Comment -None

            try:
                cpvs_data.cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Hauptklassifikation")]//following::td[5]').text
            except Exception as e:
                logging.info("Exception in cpv_code: {}".format(type(e).__name__))
                pass
        
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
    
    # Onsite Field -Beschaffungsinformationen (speziell) >> Geschätzte Laufzeit
    # Onsite Comment -None

    try:
        notice_data.contract_duration = page_details.find_element(By.XPATH, '//*[contains(text(),"Geschätzte Laufzeit")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'body > div.page'):
            funding_agencies_data = funding_agencies()
        # Onsite Field -Beschaffungsinformationen (speziell) >> Verwendung von EU-Mitteln
        # Onsite Comment -Note:"II.2.13) Information on European Union funds" , if the "financed by EU funds: No" it will be go null.. and if the"financed by EU funds: YES" it will pass the "Funding agency" name as "European Agency (internal id: 1344862)

            try:
                funding_agencies_data.funding_agency = page_details.find_element(By.XPATH, '//*[contains(text(),"Verwendung von EU-Mitteln")]//following::td[1]').text
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
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'body > div.page'):
            tender_criteria_data = tender_criteria()
        # Onsite Field -Beschaffungsinformationen (speziell) >> Zuschlagskriterien
        # Onsite Comment -Note:if the "Criterion: is " Price" grabb in criteria title  and Weight from  "Weighting out of 100%:" field  of the if the "Criterion: is " technical" grabb in criteria title  and Weight from  "Weighting out of 100%:" field  if above both keyword avaiable" Price", "technical" than only pass this in criteria title .. do not pass the hole line

            try:
                tender_criteria_data.tender_criteria_title = page_details.find_element(By.XPATH, '//*[contains(text(),"Zuschlagskriterien")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in tender_criteria_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Beschaffungsinformationen (speziell) >> Zuschlagskriterien
        # Onsite Comment -Note:if the "Criterion: is " Price" grabb in criteria title  and Weight from  "Weighting out of 100%:" field  of the if the "Criterion: is " technical" grabb in criteria title  and Weight from  "Weighting out of 100%:" field  if above both keyword avaiable" Price", "technical" than only pass this in criteria title .. do not pass the hole line

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
    

    # Format 3)
    # Ref_url=https://vergabe.muenchen.de/NetServer/PublicationControllerServlet?function=Detail&TOID=54321-NetTender-18afe9ddc3f-39b5dabffab0a4eb&Category=InvitationToTender
    # Onsite Field -Vergabenummer
    # Onsite Comment -None

    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"Vergabenummer:")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.downloadDocuments > a'):
            attachments_data = attachments()
        # Onsite Field -Download
        # Onsite Comment -Note:Don't take file extenstion ex.,(.pdf) 		Note:First click on "div.downloadDocuments > a" then second click on hear "tbody > tr > td > a" and grab the data 		Note:Open page_main the first click "Alles auswählen" then second click "Auswahl herunterladen"

            try:
                attachments_data.file_name = page_details1.find_element(By.CSS_SELECTOR, 'tbody > tr > td > a').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Download
        # Onsite Comment -None

            attachments_data.external_url = page_details1.find_element(By.CSS_SELECTOR, 'tbody > tr > td > a').get_attribute('href')
            
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'body > div.page'):
            customer_details_data = customer_details()
        # Onsite Field -Abschnitt I: Öffentlicher Auftraggeber >> I.1) Name und Adressen >> Offizielle Bezeichnung
        # Onsite Comment -Note:Splite after "Offizielle Bezeichnung" and "Postanschrift"

            try:
                customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Adressen")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Abschnitt I: Öffentlicher Auftraggeber >> I.1) Name und Adressen >> Postanschrift
        # Onsite Comment -Note:Splite after "Postanschrift" and "Postleitzahl / Ort"

            try:
                customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Adressen")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Abschnitt I: Öffentlicher Auftraggeber >> I.1) Name und Adressen >> Postleitzahl / Ort
        # Onsite Comment -Note:Splite after "Postleitzahl / Ort" and "Land"

            try:
                customer_details_data.postal_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Adressen")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in postal_code: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Abschnitt I: Öffentlicher Auftraggeber >> I.1) Name und Adressen >> NUTS-Code
        # Onsite Comment -Note:Splite after "NUTS-Code" and "Telefon"

            try:
                customer_details_data.customer_nuts = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Adressen")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in customer_nuts: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Abschnitt I: Öffentlicher Auftraggeber >> I.1) Name und Adressen >> Telefon
        # Onsite Comment -Note:Splie after "Telefon" and "E-Mail"

            try:
                customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Adressen")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Abschnitt I: Öffentlicher Auftraggeber >> I.1) Name und Adressen >> E-Mail
        # Onsite Comment -Note:Splite after "E-Mail" and "Fax"

            try:
                customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Adressen")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Abschnitt I: Öffentlicher Auftraggeber >> I.1) Name und Adressen >> Fax
        # Onsite Comment -Note:Splite after "Fax"

            try:
                customer_details_data.org_fax = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Adressen")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in org_fax: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Abschnitt I: Öffentlicher Auftraggeber >> Internet-Adresse(n) >> Hauptadresse
        # Onsite Comment -None

            try:
                customer_details_data.org_website = page_details.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(2) > a:nth-child(1)').text
            except Exception as e:
                logging.info("Exception in org_website: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Abschnitt I: Öffentlicher Auftraggeber >> I.4) Art des öffentlichen Auftraggebers
        # Onsite Comment -None

            try:
                customer_details_data.type_of_authority_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Art des öffentlichen Auftraggebers")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in type_of_authority_code: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Abschnitt I: Öffentlicher Auftraggeber >> I.5) Haupttätigkeit(en)
        # Onsite Comment -None

            try:
                customer_details_data.customer_main_activity = page_details.find_element(By.XPATH, '//*[contains(text(),"Haupttätigkeit(en)")]//following::td[1]').text
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
    notice_data.class_at_source = 'CPV'
    
    # Onsite Field -Abschnitt II: Gegenstand >> II.1.2) CPV-Code Hauptteil
    # Onsite Comment -None

    try:
        notice_data.cpv_at_source = page_details.find_element(By.XPATH, '//*[contains(text(),"II.1.2) CPV-Code Hauptteil")]//following::td[1]').text
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
                cpvs_data.cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"II.1.2) CPV-Code Hauptteil")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in cpv_code: {}".format(type(e).__name__))
                pass
        
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
    
    # Onsite Field -Abschnitt II: Gegenstand >> II.1.3) Art des Auftrags
    # Onsite Comment -Note:Replace follwing keywords with given respective kywords ('Dienstleistungen =Service'),('Lieferauftrag=Supply'),('Bauauftrag=Works')

    try:
        notice_data.notice_contract_type = page_details.find_element(By.XPATH, '//*[contains(text(),"II.1.3) Art des Auftrags")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"II.1.4) Kurze Beschreibung")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'body > div.page'):
            funding_agencies_data = funding_agencies()
        # Onsite Field -Abschnitt II: Gegenstand >> II.2.13) Angaben zu Mitteln der Europäischen Union
        # Onsite Comment -Note:"II.2.13) Information on European Union funds" , if the "financed by EU funds: No" it will be go null.. and if the"financed by EU funds: YES" it will pass the "Funding agency" name as "European Agency (internal id: 1344862)

            try:
                funding_agencies_data.funding_agency = page_details.find_element(By.XPATH, '//*[contains(text(),"II.2.13) Angaben zu Mitteln der Europäischen Union")]//following::td[1]').text
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
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'body > div.page'):
            lot_details_data = lot_details()
        # Onsite Field -Abschnitt II: Gegenstand >> Bezeichnung des Auftrags:
        # Onsite Comment -None

            try:
                lot_details_data.lot_title = page_details.find_element(By.XPATH, '//*[contains(text(),"II.2.1) Bezeichnung des Auftrags:")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Abschnitt II: Gegenstand >> II.2.2) Weitere(r) CPV-Code(s)
        # Onsite Comment -None

            try:
                lot_details_data.lot_cpv_at_source = page_details.find_element(By.XPATH, '//*[contains(text(),"II.2.2) Weitere(r) CPV-Code(s)")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in lot_cpv_at_source: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Abschnitt II: Gegenstand >> NUTS-Code:
        # Onsite Comment -None

            try:
                lot_details_data.lot_nuts = page_details.find_element(By.XPATH, '//*[contains(text(),"NUTS-Code:")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in lot_nuts: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Abschnitt II: Gegenstand >> II.2.4) Description of the procurement
        # Onsite Comment -None

            try:
                lot_details_data.lot_description = page_details.find_element(By.XPATH, '//*[contains(text(),"II.2.4) Description of the procurement")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Abschnitt II: Gegenstand >> II.2.7) Laufzeit des Vertrags, der Rahmenvereinbarung oder des dynamischen Beschaffungssystems
        # Onsite Comment -Note:Splite after "Beginn" and " Ende"

            try:
                lot_details_data.contract_start_date = page_details.find_element(By.XPATH, '//*[contains(text(),"II.2.7) Laufzeit des Vertrags, der Rahmenvereinbarung oder des dynamischen Beschaffungssystems")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in contract_start_date: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Abschnitt II: Gegenstand >> II.2.7) Laufzeit des Vertrags, der Rahmenvereinbarung oder des dynamischen Beschaffungssystems
        # Onsite Comment -Note:Splite after "Ende" and "Dieser Auftrag kann verlängert werden"

            try:
                lot_details_data.contract_end_date = page_details.find_element(By.XPATH, '//*[contains(text(),"II.2.7) Laufzeit des Vertrags, der Rahmenvereinbarung oder des dynamischen Beschaffungssystems")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in contract_end_date: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -None

            try:
                for single_record in page_details.find_elements(By.CSS_SELECTOR, 'body > div.page'):
                    lot_cpvs_data = lot_cpvs()
		
                    # Onsite Field -Abschnitt II: Gegenstand >> II.2.2) Weitere(r) CPV-Code(s)
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
                for single_record in page_details.find_elements(By.CSS_SELECTOR, 'body > div.page'):
                    lot_criteria_data = lot_criteria()
		
                    # Onsite Field -Abschnitt II: Gegenstand >> II.2.5) Zuschlagskriterien
                    # Onsite Comment -Note:if the "Criterion: is " Price" grabb in criteria title  and Weight from  "Weighting out of 100%:" field  of the if the "Criterion: is " technical" grabb in criteria title  and Weight from  "Weighting out of 100%:" field  if above both keyword avaiable" Price", "technical" than only pass this in criteria title .. do not pass the hole line

                    lot_criteria_data.lot_criteria_title = page_details.find_element(By.XPATH, '//*[contains(text(),"II.2.5) Zuschlagskriterien")]//following::td[1]').text
			
                    # Onsite Field -Abschnitt II: Gegenstand >> II.2.5) Zuschlagskriterien
                    # Onsite Comment -Note:if the "Criterion: is " Price" grabb in criteria title  and Weight from  "Weighting out of 100%:" field  of the if the "Criterion: is " technical" grabb in criteria title  and Weight from  "Weighting out of 100%:" field  if above both keyword avaiable" Price", "technical" than only pass this in criteria title .. do not pass the hole line

                    lot_criteria_data.lot_criteria_weight = page_details.find_element(By.XPATH, '//*[contains(text(),"II.2.5) Zuschlagskriterien")]//following::td[1]').text
			
                    lot_criteria_data.lot_criteria_cleanup()
                    lot_details_data.lot_criteria.append(lot_criteria_data)
            except Exception as e:
                logging.info("Exception in lot_criteria: {}".format(type(e).__name__))
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
page_details1 = fn.init_chrome_driver(arguments)
page_details = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://vergabe.muenchen.de/NetServer/PublicationSearchControllerServlet?function=SearchPublications&Gesetzesgrundlage=All&Category=InvitationToTender&thContext=publications&csrt=207473981149477300"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
    page_details1.quit()
    
    page_details.quit() 
    
    output_json_file.copyFinalJSONToServer(output_json_folder)