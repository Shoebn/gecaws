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
SCRIPT_NAME = "nl_tenderned"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"

#Note : there are multiple tabs in detail page

#1)For Tender details : 1) go to url 
                       #2) in the Filter section click on "publication type" drop down 
                       #3) after clicking, select 4 options (Marktconsultatie),(Aankondiging opdracht),(Rectificatie),(Aankondiging van een wijziging) for tender details
                       #4) no need to submit the result they will automatically generates the result

def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.script_name = 'nl_tenderned'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'NL'
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'NL'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'EUR'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -notice_type will be 4 for "(Marktconsultatie)and(Aankondiging opdracht)" and notice_type will be 16 for "(Rectificatie)and (Aankondiging van een wijziging)"    
    notice_data.notice_type = 4
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'mat-card-title>h3').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div:nth-child(2) > font").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "mat-card-content > div:nth-child(1)").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Procedure
    # Onsite Comment -None
    try:
        notice_data.type_of_procedure_actual = tender_html_element.find_element(By.CSS_SELECTOR, "mat-card-content > div:nth-child(2)").text
        notice_data.type_of_procedure = fn.procedure_mapping("assets/nl_tenderned_procedure",notice_data.type_of_procedure_actual)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Type opdracht
    # Onsite Comment -Replace following keywords with given respective keywords ('Leveringen = Supply ','Diensten = Services ', 'Werken = Works')

    try:
        notice_data.notice_contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'mat-card-content > div:nth-child(3)').text
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Korte beschrijving")]//following::p').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -TenderNed reference
    # Onsite Comment -you have to go to the "Details" tab to split data, ref url : "https://www.tenderned.nl/aankondigingen/overzicht/303542/details"

    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"TenderNed-kenmerk")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Publicatie
    # Onsite Comment -you have to go to the "Publicatie" tab to split data, ref url : "https://www.tenderned.nl/aankondigingen/overzicht/303821/publicatie"

    try:
        notice_data.document_type_description = page_details.find_element(By.CSS_SELECTOR, '#top-publication > h1').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -II.1.4) Korte beschrijving
    # Onsite Comment -split the data between "Korte beschrijving" and "Geraamde totale waarde" field, url ref: "https://www.tenderned.nl/aankondigingen/overzicht/303542/publicatie","https://www.tenderned.nl/aankondigingen/overzicht/303674/publicatie"

    try:
        notice_data.notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),"Korte beschrijving")]//following::p').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -II.2.13) Inlichtingen over middelen van de Europese Unie = funding agencies, for ref url ="https://www.tenderned.nl/aankondigingen/overzicht/303814/publicatie"
    # Onsite Comment -if in below text written as " financed by European Union funds: No  " than pass the "None " in field name "T.FUNDING_AGENCIES::TEXT	" "II.2.13) Information about European Union Funds  >  The procurement is related to a project and/or programme financed by European Union funds: No  " if the abve  text written as " financed by European Union funds: YES  " than pass the "Funding agency" name as "European Agency (internal id: 1344862) " in field name "T.FUNDING_AGENCIES::TEXT"

    try:
        notice_data.funding_agencies = page_details.find_element(By.XPATH, '//*[contains(text(),"Inlichtingen over middelen van de Europese Unie")]//following::p[1]').text
    except Exception as e:
        logging.info("Exception in funding_agencies: {}".format(type(e).__name__))
        pass

     # Onsite Field -II.1.5) Geraamde totale waarde
    # Onsite Comment -some sites are not contains  grossbudget_lc, url ref: "https://www.tenderned.nl/aankondigingen/overzicht/303481/publicatie"

    try:
        notice_data.est_amount = page_details.find_element(By.XPATH, '//*[contains(text(),"Geraamde totale waarde")]//following::p[1]').text
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -II.1.5) Geraamde totale waarde
    # Onsite Comment -some sites are not contains  grossbudget_lc, url ref: "https://www.tenderned.nl/aankondigingen/overzicht/303481/publicatie"

    try:
        notice_data.grossbudgetlc = page_details.find_element(By.XPATH, '//*[contains(text(),"Geraamde totale waarde")]//following::p[1]').text
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -after clicking you will see  tabs  such as  "details","publication","documents","questions answers"

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'a.tn-link').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -there are 2 tabs are avaialable to fetch all data sych as "details" and "publication"
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.tap-content').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
# Onsite Field -Publicatie = publication tab
# Onsite Comment -customer details are available in this field "I.1) Naam en adressen" = "name and address"

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'tn-aankondiging-publicatie-tab>div>div'):
            customer_details_data = customer_details()
        # Onsite Field -Officiële benaming
        # Onsite Comment -None

            try:
                customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Officiële benaming")]//following::dd[1]').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Mailing address: =  "org_address"
        # Onsite Comment -None

            try:
                customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Mailing address")]//following::dd[1]').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Plaats: = place
        # Onsite Comment -None

            try:
                customer_details_data.org_city = page_details.find_element(By.XPATH, '//*[contains(text(),"Place")]//following::dd[1]').text
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass
        
            customer_details_data.org_country = 'NL'
            customer_details_data.org_language = 'NL'
        # Onsite Field -E-mail:
        # Onsite Comment -None

            try:
                customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"E-mail")]//following::dd[1]').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Contactpersoon
        # Onsite Comment -None

            try:
                customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Contactpersoon")]//following::dd[1]').text
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Telefoon:
        # Onsite Comment -None

            try:
                customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Telefoon")]//following::dd[1]').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Fax:
        # Onsite Comment -None

            try:
                customer_details_data.org_fax = page_details.find_element(By.XPATH, '//*[contains(text(),"Fax")]//following::dd[1]').text
            except Exception as e:
                logging.info("Exception in org_fax: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -NUTS-code:
        # Onsite Comment -None

            try:
                customer_details_data.customer_nuts = page_details.find_element(By.XPATH, '//*[contains(text(),"NUTS-code")]//following::dd[1]').text
            except Exception as e:
                logging.info("Exception in customer_nuts: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Postcode:
        # Onsite Comment -None

            try:
                customer_details_data.postal_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Postcode:")]//following::dd[1]').text
            except Exception as e:
                logging.info("Exception in postal_code: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Hoofdadres:
        # Onsite Comment -None

            try:
                customer_details_data.org_website = page_details.find_element(By.XPATH, '//*[contains(text(),"Hoofdadres:")]//following::a[1]').text
            except Exception as e:
                logging.info("Exception in org_website: {}".format(type(e).__name__))
                pass
        
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
            
    
# Onsite Field -II.1.6) Inlichtingen over percelen  = "information about lots"
# Onsite Comment -lot details are available in publication tab

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.tap-content'):
            lot_details_data = lot_details()
        # Onsite Field -II.2.1) Benaming
        # Onsite Comment -split only lot title from following field "II.2.1) Benaming", url ref: "https://www.tenderned.nl/aankondigingen/overzicht/303526/publicatie"

            try:
                lot_details_data.lot_title = page_details.find_element(By.XPATH, '//*[contains(text(),'Benaming')]//following::p[1]').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -II.2.4) Beschrijving van de aanbesteding:
        # Onsite Comment -None

            try:
                lot_details_data.lot_description = page_details.find_element(By.XPATH, '//*[contains(text(),'Beschrijving van de aanbesteding:')]//following::p[1]').text
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -II.2.1) Benaming
        # Onsite Comment -split only tender no from "II.2.1) Benaming" field

            try:
                lot_details_data.lot_number = page_details.find_element(By.XPATH, '//*[contains(text(),"Benaming")]//following::p[2]').text
            except Exception as e:
                logging.info("Exception in lot_number: {}".format(type(e).__name__))
                pass
        
        
        # Onsite Field -II.2.3) Plaats van uitvoering
        # Onsite Comment -above selector also select the cpv you have to only take nutcode, url ref: "https://www.tenderned.nl/aankondigingen/overzicht/303526/publicatie","https://www.tenderned.nl/aankondigingen/overzicht/303814/publicatie"

            try:
                lot_details_data.lot_nuts = page_details.find_element(By.XPATH, '//*[contains(text(),"Plaats van uitvoering")]//following::dl').text
            except Exception as e:
                logging.info("Exception in lot_nuts: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -II.2.6) Geraamde waarde
        # Onsite Comment -url ref : "https://www.tenderned.nl/aankondigingen/overzicht/303526/publicatie"

            try:
                lot_details_data.lot_grossbudget_lc = page_details.find_element(By.XPATH, '//*[contains(text(),"Geraamde waarde")]//following::p[1]').text
            except Exception as e:
                logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
                pass



        # Onsite Field -Type opdracht
        # Onsite Comment -Replace following keywords with given respective keywords ('Leveringen = Supply ','Diensten = Services ', 'Werken = Works')

            try:
                 lot_details_data.contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'mat-card-content > div:nth-child(3)').text
            except Exception as e:
                 logging.info("Exception in contract_type: {}".format(type(e).__name__))
                pass
    
        
        # Onsite Field -II.2.7) Looptijd van de opdracht, de raamovereenkomst of het dynamische aankoopsysteem  = Duration of the contract, framework agreement or dynamic purchasing system
        # Onsite Comment -this xpath contains contract_start_date and end_date you have to split only start date

            try:
                lot_details_data.contract_start_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Looptijd van de opdracht, de raamovereenkomst of het dynamische aankoopsysteem")]//following::p[1]').text
            except Exception as e:
                logging.info("Exception in contract_start_date: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -II.2.7) Looptijd van de opdracht, de raamovereenkomst of het dynamische aankoopsysteem  = Duration of the contract, framework agreement or dynamic purchasing system
        # Onsite Comment -this xpath contains contract_start_date and end_date you have to split only end date

            try:
                lot_details_data.contract_end_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Looptijd van de opdracht, de raamovereenkomst of het dynamische aankoopsysteem")]//following::p[1]').text
            except Exception as e:
                logging.info("Exception in contract_end_date: {}".format(type(e).__name__))
                pass


        # Onsite Field -II.2) Beschrijving
        # Onsite Comment -None

            try:
                for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.tap-content'):
                    lot_cpvs_data = lot_cpvs()
		
                    # Onsite Field -II.2.1) Benaming
                    # Onsite Comment -first go to "publicatie" tab , take only number value from this filed,   url ref: "https://www.tenderned.nl/aankondigingen/overzicht/303526/publicatie"

                    lot_cpvs_data.lot_cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Aanvullende CPV-code(s)")]//following::dd[1]').text
			
                    lot_cpvs_data.lot_cpvs_cleanup()
                    lot_details_data.lot_cpvs.append(lot_cpvs_data)
            except Exception as e:
                logging.info("Exception in lot_cpvs: {}".format(type(e).__name__))
                pass

            
        # Onsite Field -V.2.3) Naam en adres van de contractant
        # Onsite Comment -you have to select "publicatie" option to view award details

            try:
                for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.tap-content'):
                    award_details_data = award_details()
		
                    # Onsite Field -Officiële benaming
                    # Onsite Comment -None

                    award_details_data.bidder_name = page_details.find_element(By.XPATH, '//*[contains(text(),"V.2.3)")]//following::dd[1]').text
			
                    # Onsite Field -Postadres:
                    # Onsite Comment -None

                    award_details_data.address = page_details.find_element(By.XPATH, '//*[contains(text(),"V.2.3)")]//following::dd[3]').text
			
                    # Onsite Field -V.2.4) Inlichtingen over de waarde van de opdracht/het perceel (exclusief btw)
                    # Onsite Comment -url ref: "https://www.tenderned.nl/aankondigingen/overzicht/303604/publicatie"

                    award_details_data.initial_estimated_value = page_details.find_element(By.XPATH, '//*[contains(text(),"V.2.4)")]//following::p[1]').text
			
                    # Onsite Field -V.2.4) Inlichtingen over de waarde van de opdracht/het perceel (exclusief btw)
                    # Onsite Comment -url ref: "https://www.tenderned.nl/aankondigingen/overzicht/303604/publicatie"

                    award_details_data.grossawardvaluelc = page_details.find_element(By.XPATH, '//*[contains(text(),"V.2.4)")]//following::p[2]').text
			
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
    
# Onsite Field -II.2.5) Gunningscriteria =  Award criteria
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.tap-content'):
            tender_criteria_data = tender_criteria()
        # Onsite Field -II.2.5) Gunningscriteria
        # Onsite Comment -above xpath code selecting multiple values you have to split only "Naam:" field for title

            try:
                tender_criteria_data.tender_criteria_title = page_details.find_element(By.XPATH, '//*[contains(text(),'Gunningscriteria')]//following::p[2]').text
            except Exception as e:
                logging.info("Exception in tender_criteria_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -II.2.5) Gunningscriteria
        # Onsite Comment -above xpath code selecting multiple values you have to split only "Weging" field for tender_criteria_weight

            try:
                tender_criteria_data.tender_criteria_weight = page_details.find_element(By.XPATH, '//*[contains(text(),'Gunningscriteria')]//following::p[2]').text
            except Exception as e:
                logging.info("Exception in tender_criteria_weight: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -II.2.5) Gunningscriteria
        # Onsite Comment -above xpath code selecting multiple values you have to split only "Prijs" field for tender_is_price_related

            try:
                tender_criteria_data.tender_is_price_related = page_details.find_element(By.XPATH, '//*[contains(text(),'Gunningscriteria')]//following::p[2]').text
            except Exception as e:
                logging.info("Exception in tender_is_price_related: {}".format(type(e).__name__))
                pass
        
            tender_criteria_data.tender_criteria_cleanup()
            notice_data.tender_criteria.append(tender_criteria_data)
    except Exception as e:
        logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -Documenten
# Onsite Comment -you have to go "Documenten" tab for grab attachments, some attachments are not included in tenders

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'tn-aankondiging-documenten-tab'):
            attachments_data = attachments()
        # Onsite Field -Alle documenten
        # Onsite Comment -None

            try:
                attachments_data.file_name = page_details.find_element(By.CSS_SELECTOR, 'div > div.tn-document-title > div> h4').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Alle documenten
        # Onsite Comment -above selector selects multiple field you have to take only file type, url ref : "https://www.tenderned.nl/aankondigingen/overzicht/303526/documenten"

            try:
                attachments_data.file_type = page_details.find_element(By.CSS_SELECTOR, 'div.tn-document-title > div:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Alle documenten
        # Onsite Comment -None

            attachments_data.external_url = page_details.find_element(By.CSS_SELECTOR, 'div > div.tn-document-title > div> h4').get_attribute('href')
            
        
        # Onsite Field -Alle documenten
        # Onsite Comment -above selector selects multiple field value you have to take only file size, url ref : "https://www.tenderned.nl/aankondigingen/overzicht/303526/documenten"

            try:
                attachments_data.file_size = page_details.find_element(By.CSS_SELECTOR, 'div.tn-document-title > div:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in file_size: {}".format(type(e).__name__))
                pass
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
 


    # Onsite Field -None
    # Onsite Comment -below code is for new updated format.....


    # Onsite Field -None
    # Onsite Comment -split and take data after publish_date

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'mat-card-header > div > mat-card-subtitle > div:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'span.tn-h3 > a').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
        
    # Onsite Field -None
    # Onsite Comment -split and take only date and take time also if available

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, 'mat-card-header > div > mat-card-subtitle > div:nth-child(2)').text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return    
    # Onsite Field -None
    # Onsite Comment -take time also if available

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "mat-card-content > div:nth-child(1) > div:nth-child(2").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Procedure
    # Onsite Comment -split and take "Procedure" only
    try:
        notice_data.type_of_procedure_actual = tender_html_element.find_element(By.CSS_SELECTOR, "mat-card-content").text
        notice_data.type_of_procedure = fn.procedure_mapping("assets/nl_tenderned_procedure",notice_data.type_of_procedure_actual)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Type opdracht
    # Onsite Comment -split and take "Type opdracht" only and  Replace following keywords with given respective keywords ('Leveringen = Supply ','Diensten = Services ', 'Werken = Works')

    try:
        notice_data.notice_contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'mat-card-content').text
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
  
    # Onsite Field -Type opdracht
    # Onsite Comment -split and take "Type opdracht" only 
    try:
        notice_data.contract_type_actual = tender_html_element.find_element(By.CSS_SELECTOR, 'mat-card-content').text
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -after clicking you will see  tabs  such as  "Details","Publicatie","Documenten","Vraag en antwoord"

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'a.tn-link').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -take data from all tabs ("Details","Publicatie","Documenten","Vraag en antwoord") and close take data from tender_html_page ( "//*[@id="app"]/tn-aankondigingen-page/div[2]/div/tn-aankondiging-overzicht/mat-drawer-container/mat-drawer-content/div[2]/div[2]/mat-card" )
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.tap-content').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass

        
    # Onsite Field -Beschrijving
    # Onsite Comment - click on "Publicatie" then click on dropdown "2. Procedure" to get the data 

    try:
        notice_data.notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),"Beschrijving")]//following::span[2]').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass

    # Onsite Field -Beschrijving
    # Onsite Comment - click on "Publicatie" then click on dropdown "2. Procedure" to get the data 
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Beschrijving")]//following::span[2]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
           
    # Onsite Field -Referentienummer
    # Onsite Comment - click on "Details" to get the data

    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"Referentienummer")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    # Onsite Field -Geraamde waarde exclusief btw
    # Onsite Comment -click on "Publicatie" then click on dropdown "2. Procedure" to get the data..., url ref: "https://www.tenderned.nl/aankondigingen/overzicht/322684"

    try:
        notice_data.est_amount = page_details.find_element(By.XPATH, '//*[contains(text(),"Geraamde waarde exclusief btw")]//following::span[2]').text
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
        # Onsite Field -Geraamde waarde exclusief btw
        # Onsite Comment -click on "Publicatie" then click on dropdown "2. Procedure" to get the data ..., url ref: "https://www.tenderned.nl/aankondigingen/overzicht/322684"

    try:
        notice_data.netbudgetlc = page_details.find_element(By.XPATH, '//*[contains(text(),"Geraamde waarde exclusief btw")]//following::span[2]').text
    except Exception as e:
        logging.info("Exception in netbudgetlc: {}".format(type(e).__name__))
        pass
        
        # Onsite Field -Geraamde waarde exclusief btw
        # Onsite Comment -click on "Publicatie" then click on dropdown "2. Procedure" to get the data ..., url ref: "https://www.tenderned.nl/aankondigingen/overzicht/322684"

    try:
        notice_data.netbudgeteuro = page_details.find_element(By.XPATH, '//*[contains(text(),"Geraamde waarde exclusief btw")]//following::span[2]').text
    except Exception as e:
        logging.info("Exception in netbudgeteuro: {}".format(type(e).__name__))
        pass 
            
    # Onsite Field -Aanvang opdracht
    # Onsite Comment - click on "Details" to get the data

    try:
        notice_data.tender_contract_start_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Aanvang opdracht")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in tender_contract_start_date: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Voltooiing opdracht
    # Onsite Comment - click on "Details" to get the data

    try:
        notice_data.tender_contract_end_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Voltooiing opdracht")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in tender_contract_end_date: {}".format(type(e).__name__))
        pass 
        
    # Onsite Field -None
    # Onsite Comment -None
        notice_data.class_at_source = 'CPV'         

    # Onsite Field -Hoofdopdracht (CPV code)
    # Onsite Comment - click on "Details" to get the data

    try:
        notice_data.cpv_at_source = page_details.find_element(By.XPATH, '//*[contains(text(),"Hoofdopdracht (CPV code)")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in cpv_at_source: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Bijkomende opdracht(-en) (CPV code)
    # Onsite Comment - click on "Details" to get the data

    try:
        notice_data.cpv_at_source = page_details.find_element(By.XPATH, '//*[contains(text(),"Bijkomende opdracht(-en) (CPV code)")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in cpv_at_source: {}".format(type(e).__name__))
        pass        

# Onsite Field -Publicatie
# Onsite Comment -click on "Publicatie" than click on "Organisaties", ref link "https://www.tenderned.nl/aankondigingen/overzicht/322518"

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.tap-content'):
            customer_details_data = customer_details()
        # Onsite Field -Officiële naam
        # Onsite Comment -None

            try:
                customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Officiële naam")]//following::span[2]').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass

        
        # Onsite Field -Postadres
        # Onsite Comment -None

            try:
                customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Postadres")]//following::span[2]').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Stad
        # Onsite Comment -None

            try:
                customer_details_data.org_city = page_details.find_element(By.XPATH, '//*[contains(text(),"Stad")]//following::span[2]').text
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass
        
            customer_details_data.org_country = 'NL'
            customer_details_data.org_language = 'NL'
            
        # Onsite Field -E-mail
        # Onsite Comment -None

            try:
                customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"E-mail")]//following::span[2]').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Contactpunt
        # Onsite Comment -None

            try:
                customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Contactpunt")]//following::span[2]').text
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Telefoon
        # Onsite Comment -None

            try:
                customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Telefoon")]//following::span[2]').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass

        # Onsite Field -Fax:
        # Onsite Comment -None

            try:
                customer_details_data.org_fax = page_details.find_element(By.XPATH, '//*[contains(text(),"Fax")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in org_fax: {}".format(type(e).__name__))
                pass
        
        
        # Onsite Field -Postcode
        # Onsite Comment -None

            try:
                customer_details_data.postal_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Postcode")]//following::span[2]').text
            except Exception as e:
                logging.info("Exception in postal_code: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Internetadres
        # Onsite Comment -None

            try:
                customer_details_data.org_website = page_details.find_element(By.XPATH, '//*[contains(text(),"Internetadres")]//following::span[2]').text
            except Exception as e:
                logging.info("Exception in org_website: {}".format(type(e).__name__))
                pass

        # Onsite Field -Activiteit van de aanbestedende dienst: 
        # Onsite Comment -None

            try:
                customer_details_data.customer_main_activity  = page_details.find_element(By.XPATH, '//*[contains(text(),"Activiteit van de aanbestedende dienst")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in customer_main_activity : {}".format(type(e).__name__))
                pass

            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
 
 
# Onsite Field -Hoofdopdracht (CPV code)
# Onsite Comment - click on "Details" to get the data and take all cpvs in lots and also append lot cpvs in tender cpv 

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.tap-content'):
            cpvs_data = cpvs()
        # Onsite Field -Hoofdopdracht (CPV code)
        # Onsite Comment -None
            try:
                cpvs_data.cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Hoofdopdracht (CPV code)")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in cpv_code: {}".format(type(e).__name__))
                pass

        # Onsite Field -Bijkomende opdracht(-en) (CPV code)
        # Onsite Comment -None
            try:
                cpvs_data.cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Bijkomende opdracht(-en) (CPV code)")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in cpv_code: {}".format(type(e).__name__))
                pass
       
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
        
        
            
# Onsite Field -Perceel = "information about lots"
# Onsite Comment -click on "Publicatie" than click on "Perceel", ref link "https://www.tenderned.nl/aankondigingen/overzicht/322690"

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.tap-content'):
            lot_details_data = lot_details()
        # Onsite Field -Titel
        # Onsite Comment -None

            try:
                lot_details_data.lot_title = page_details.find_element(By.XPATH, '//*[contains(text(),"Titel")]//following::span[2]').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Beschrijving
        # Onsite Comment -take "Beschrijving" which is only in lots and after lot_title 

            try:
                lot_details_data.lot_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Beschrijving")]//following::span[2]').text
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Perceel
        # Onsite Comment -here take only "LOT-0001" as lot_actual_number
            try:
                lot_details_data.lot_actual_number = page_details.find_element(By.XPATH, '//*[contains(text(),"Perceel")]//following::span[2]').text
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass
                
        
        # Onsite Field -Onderverdeling land (NUTS)
        # Onsite Comment -ref url: "https://www.tenderned.nl/aankondigingen/overzicht/322684" 

            try:
                lot_details_data.lot_nuts = page_details.find_element(By.XPATH, '//*[contains(text(),"Onderverdeling land (NUTS)")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in lot_nuts: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Geraamde waarde exclusief btw
        # Onsite Comment -

            try:
                lot_details_data.lot_netbudget_lc = page_details.find_element(By.XPATH, '//*[contains(text(),"Geraamde waarde exclusief btw")]//following::span[2]').text
            except Exception as e:
                logging.info("Exception in lot_netbudget_lc: {}".format(type(e).__name__))
                pass

        # Onsite Field -Geraamde waarde exclusief btw
        # Onsite Comment -

            try:
                lot_details_data.lot_netbudget = page_details.find_element(By.XPATH, '//*[contains(text(),"Geraamde waarde exclusief btw")]//following::span[2]').text
            except Exception as e:
                logging.info("Exception in lot_netbudget: {}".format(type(e).__name__))
                pass

        # Onsite Field -Aard van het contract
        # Onsite Comment -Replace following keywords with given respective keywords ('Leveringen = Supply ','Diensten = Services ', 'Werken = Works')ref url "https://www.tenderned.nl/aankondigingen/overzicht/322690"

            try:
                 lot_details_data.contract_type = page_details.find_element(By.XPATH, '//*[contains(text(),"Aard van het contract")]//following::span[2]').text
            except Exception as e:
                 logging.info("Exception in contract_type: {}".format(type(e).__name__))
                pass

         # Onsite Field -Aard van het contract
        # Onsite Comment -ref url "https://www.tenderned.nl/aankondigingen/overzicht/322690"

            try:
                 lot_details_data.lot_contract_type_actual = tpage_details.find_element(By.XPATH, '//*[contains(text(),"Aard van het contract")]//following::span[2]').text
            except Exception as e:
                 logging.info("Exception in lot_contract_type_actual: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Begindatum
        # Onsite Comment -ref url "https://www.tenderned.nl/aankondigingen/overzicht/322690"

            try:
                lot_details_data.contract_start_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Begindatum")]//following::span[2]').text
            except Exception as e:
                logging.info("Exception in contract_start_date: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Einddatum

        # Onsite Comment -ref url "https://www.tenderned.nl/aankondigingen/overzicht/322690"
            try:
                lot_details_data.contract_end_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Einddatum")]//following::span[2]').text
            except Exception as e:
                logging.info("Exception in contract_end_date: {}".format(type(e).__name__))
                pass

        # Onsite Field -Hoeveelheid
        # Onsite Comment -None

            try:
                lot_details_data.lot_quantity = page_details.find_element(By.XPATH, '//*[contains(text(),"Hoeveelheid")]//following::span[2]').text
            except Exception as e:
                logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                pass
                
        # Onsite Field -Geraamde duur >> Looptijd
        # Onsite Comment -ref urle :- "https://www.tenderned.nl/aankondigingen/overzicht/323006"

            try:
                lot_details_data.contract_duration = page_details.find_element(By.XPATH, '//*[contains(text(),"Looptijd")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in contract_duration: {}".format(type(e).__name__))
                pass        
                
        # Onsite Field -Belangrijkste classificatie
        # Onsite Comment -None

            try:
                lot_details_data.lot_cpv_at_source = page_details.find_element(By.XPATH, '//*[contains(text(),"Belangrijkste classificatie")]//following::td[1]/span[1]').text
            except Exception as e:
                logging.info("Exception in lot_cpv_at_source: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Aanvullende classificatie
        # Onsite Comment -None

            try:
                lot_details_data.lot_cpv_at_source = page_details.find_element(By.XPATH, '//*[contains(text(),"Aanvullende classificatie")]//following::td[1]/span[1]').text
            except Exception as e:
                logging.info("Exception in lot_cpv_at_source: {}".format(type(e).__name__))
                pass        

        # Onsite Field -II.2) Beschrijving
        # Onsite Comment -None

            try:
                for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.tap-content'):
                    lot_cpvs_data = lot_cpvs()
		
                    # Onsite Field -Belangrijkste classificatie
                    # Onsite Comment -None

                    lot_cpvs_data.lot_cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Belangrijkste classificatie")]//following::td[1]/span[1]').text
                    
                    # Onsite Field -Aanvullende classificatie
                    # Onsite Comment -None

                    lot_cpvs_data.lot_cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Aanvullende classificatie")]//following::td[1]/span[1]').text
			
                    lot_cpvs_data.lot_cpvs_cleanup()
                    lot_details_data.lot_cpvs.append(lot_cpvs_data)
            except Exception as e:
                logging.info("Exception in lot_cpvs: {}".format(type(e).__name__))
                pass

        # Onsite Field -5.1.10 Gunningscriteria
        # Onsite Comment -take data which is in "Gunningscriteria"

            try:
                for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.tap-content'):
                    lot_criteria_data = lot_criteria()

            # Onsite Field -5.1.10 Gunningscriteria >> Naam
            # Onsite Comment -None

                    try:
                        lot_criteria_data.lot_criteria_title = page_details.find_element(By.XPATH, '//*[contains(text(),"Naam")]//following::span[2]').text
                    except Exception as e:
                        logging.info("Exception in lot_criteria_title: {}".format(type(e).__name__))
                        pass

            # Onsite Field -5.1.10 Gunningscriteria >> Gewicht (punten, exact)
            # Onsite Comment - None

                    try:
                        lot_criteria_data.lot_criteria_weight = page_details.find_element(By.XPATH, '//*[contains(text(),"Gewicht (punten, exact)")]//following::span[2]').text
                    except Exception as e:
                        logging.info("Exception in lot_criteria_weight: {}".format(type(e).__name__))
                        pass

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
    
    
# Onsite Field -Publicatie
# Onsite Comment -click on "Publicatie" and click on " Download PDF " to get attachment

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.tap-content'):
            attachments_data = attachments()
            
            attachments_data.file_name = 'Tender Documents'
        
            
        # Onsite Field -Publicatie
        # Onsite Comment -click on "Publicatie" and click on " Download PDF " to get attachment 

            attachments_data.external_url = page_details.find_element(By.CSS_SELECTOR, 'div.secondary-button-container > button').get_attribute('href')
         
         
        # Onsite Field -Documenten
        # Onsite Comment -you have to go "Documenten" tab for more attachment attachments   
            attachments_data.file_name = 'Tender Documents'
            
        # Onsite Field -Documenten
        # Onsite Comment -click on "Documenten" and click on "  Download alle documenten  " to get all attachment 

            attachments_data.external_url = page_details.find_element(By.CSS_SELECTOR, 'div.secondary-button-container > button').get_attribute('href')    
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    


# REF URL:- https://www.tenderned.nl/aankondigingen/overzicht/324249 for new identified format
    # Onsite Field -Description
    # Onsite Comment - click on "Publicatie" then click on dropdown "2. Procedure" to get the data 
    try:
        notice_data.notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),"Description")]//following::span[2]').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    # Onsite Field -Description
    # Onsite Comment - click on "Publicatie" then click on dropdown "2. Procedure" to get the data 
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Description")]//following::span[2]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
           
# Onsite Field -Publicatie
# Onsite Comment -click on "Publicatie" than click on ". Organisations", 
    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.tap-content'):
            customer_details_data = customer_details()
        # Onsite Field -Official name
        # Onsite Comment -None
            try:
                customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Official name")]//following::span[2]').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass        
        # Onsite Field -Postal address
        # Onsite Comment -None
            try:
                customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Postal address")]//following::span[2]').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass        
        # Onsite Field -Town
        # Onsite Comment -None
            try:
                customer_details_data.org_city = page_details.find_element(By.XPATH, '//*[contains(text(),"Town")]//following::span[2]').text
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass        
            customer_details_data.org_country = 'NL'
            customer_details_data.org_language = 'NL'            
        # Onsite Field -Email
        # Onsite Comment -None
            try:
                customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Email")]//following::span[2]').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass        
        # Onsite Field -Contact point
        # Onsite Comment -None
            try:
                customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Contact point")]//following::span[2]').text
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass        
        # Onsite Field -Telefoon
        # Onsite Comment -None
            try:
                customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Telefoon")]//following::span[2]').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
        # Onsite Field -Fax:
        # Onsite Comment -None
            try:
                customer_details_data.org_fax = page_details.find_element(By.XPATH, '//*[contains(text(),"Fax")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in org_fax: {}".format(type(e).__name__))
                pass        
        # Onsite Field -Postcode
        # Onsite Comment -None
            try:
                customer_details_data.postal_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Postcode")]//following::span[2]').text
            except Exception as e:
                logging.info("Exception in postal_code: {}".format(type(e).__name__))
                pass        
        # Onsite Field -Internet address
        # Onsite Comment -None
            try:
                customer_details_data.org_website = page_details.find_element(By.XPATH, '//*[contains(text(),"Internet address")]//following::span[2]').text
            except Exception as e:
                logging.info("Exception in org_website: {}".format(type(e).__name__))
                pass
        # Onsite Field -Activity of the contracting authority
        # Onsite Comment -None
            try:
                customer_details_data.customer_main_activity  = page_details.find_element(By.XPATH, '//*[contains(text(),"Activity of the contracting authority")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in customer_main_activity : {}".format(type(e).__name__))
                pass
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
               
# Onsite Field -Perceel = "information about lots"
# Onsite Comment -click on "Publicatie" than click on "Part",
    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.tap-content'):
            lot_details_data = lot_details()
        # Onsite Field -Title
        # Onsite Comment -None
            try:
                lot_details_data.lot_title = page_details.find_element(By.XPATH, '//*[contains(text(),"Title")]//following::span[2]').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        # Onsite Field -Description
        # Onsite Comment -take "Description" which is only in lots and after lot_title 
            try:
                lot_details_data.lot_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Description")]//following::span[2]').text
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass       
        # Onsite Field - Part
        # Onsite Comment -here take only "PAR-0000" as lot_actual_number
            try:
                lot_details_data.lot_actual_number = page_details.find_element(By.XPATH, '//*[contains(text()," Part")]//following::span[2]').text
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass 
        # Onsite Field -Country subdivision (NUTS)
        # Onsite Comment -
            try:
                lot_details_data.lot_nuts = page_details.find_element(By.XPATH, '//*[contains(text(),"Country subdivision (NUTS)")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in lot_nuts: {}".format(type(e).__name__))
                pass  
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
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
page_main = fn.init_chrome_driver(arguments) 
page_details = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.tenderned.nl/aankondigingen/overzicht"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,3):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="app"]/tn-aankondigingen-page/div[2]/div/tn-aankondiging-overzicht/mat-drawer-container/mat-drawer-content/div[2]/div[2]/mat-card'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="app"]/tn-aankondigingen-page/div[2]/div/tn-aankondiging-overzicht/mat-drawer-container/mat-drawer-content/div[2]/div[2]/mat-card')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="app"]/tn-aankondigingen-page/div[2]/div/tn-aankondiging-overzicht/mat-drawer-container/mat-drawer-content/div[2]/div[2]/mat-card')))[records]
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="app"]/tn-aankondigingen-page/div[2]/div/tn-aankondiging-overzicht/mat-drawer-container/mat-drawer-content/div[2]/div[2]/mat-card'),page_check))
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