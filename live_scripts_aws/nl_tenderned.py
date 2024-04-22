from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "nl_tenderned"
log_config.log(SCRIPT_NAME)
import re
import jsons
from dateparser import parse
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from deep_translator import GoogleTranslator
from selenium import webdriver
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn
import gec_common.Doc_Download_ingate as Doc_Download
from selenium.webdriver.chrome.options import Options

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "nl_tenderned"
Doc_Download = Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"

#Note : there are multiple tabs in detail page

#1)For Tender details : 1) go to url 
                       #2) in the Filter section click on "publication type" drop down 
                       #3) after clicking, select 4 options (Market consultation),(Advance notice),(Order announcement),(Rectification) for tender details
                       #4) no need to submit the result they will autometically generates the result

#2) For Contract Award details : 1) go to url 
                       #2) in the Filter section click on "publication type" drop down 
                       #3) after clicking, select (contract awarded notice) option for award details
                       #4) no need to submit the result they will autometically generates the result

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
    # Onsite Comment -take notice type 4 for 'tender details' and take notice type 7 for 'contract award details'
    
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_type = tender_html_element.find_element(By.CSS_SELECTOR, "mat-card-subtitle > div:nth-child(2)").text
        if 'Aankondiging van een gegunde opdracht' in notice_type:
            notice_data.notice_type = 7
        else:
            notice_data.notice_type = 4
    except:
        pass
       
    try:
        local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'mat-card-title > span').text
        if len(local_title)<=5:
            # local title len  less than minimum length of 5.
            return
        notice_data.local_title = local_title
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "mat-card-subtitle > div:nth-child(2)").text.split("-")[0]
        publish_date = GoogleTranslator(source='nl', target='en').translate(publish_date)
        publish_date = parse(publish_date)
        notice_data.publish_date = publish_date.strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    
    
    
    # Onsite Field -Procedure
    # Onsite Comment -None
    try:
        notice_data.type_of_procedure_actual = tender_html_element.text.split("Procedure")[1].split("\n")[1]
        type_of_procedure = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("assets/nl_tenderned.csv",type_of_procedure)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Type opdracht
    # Onsite Comment -Replace following keywords with given respective keywords ('Leveringen = Supply ','Diensten = Services ', 'Werken = Works')

    try:
        notice_contract_type = tender_html_element.text.split("Type opdracht")[1].split("\n")[1]
        if 'Leveringen' in notice_contract_type:
            notice_data.notice_contract_type = 'Supply'
        elif 'Diensten' in notice_contract_type:
            notice_data.notice_contract_type = 'Services'
        elif 'Werken' in notice_contract_type:
            notice_data.notice_contract_type = 'Works'
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
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
    try:
        notice_deadline = page_details.find_element(By.XPATH, '//*[contains(text(),"Sluitingsdatum")]//following::div[1]').text
        notice_deadline = GoogleTranslator(source='nl', target='en').translate(notice_deadline)
        notice_deadline = parse(notice_deadline)
        notice_data.notice_deadline = notice_deadline.strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"TenderNed-kenmerk")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    

    # Onsite Field -TenderNed reference
    # Onsite Comment -you have to go to the "Details" tab to split data, ref url : "https://www.tenderned.nl/aankondigingen/overzicht/303542/details"

    
    # Onsite Field -Publicatie
    # Onsite Comment -you have to go to the "Publicatie" tab to split data, ref url : "https://www.tenderned.nl/aankondigingen/overzicht/303821/publicatie"
    try:
        Publicatie_clk = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#tab-1')))
        page_details.execute_script("arguments[0].click();",Publicatie_clk)
    except:
        pass

    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Korte beschrijving")]//following::p[2]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    try:
        dispatch_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Datum van verzending van deze aankondiging")]//following::p[1]').text
        dispatch_date = re.findall('\d+/\d+/\d{4}',dispatch_date)[0]
        notice_data.dispatch_date = datetime.strptime(dispatch_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in dispatch_date: {}".format(type(e).__name__))
        pass
    
    try:
        document_type_description = WebDriverWait(page_details, 60).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#top-publication > h1'))).text
        notice_data.document_type_description = GoogleTranslator(source='auto', target='en').translate(document_type_description)
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -II.1.4) Korte beschrijving
    # Onsite Comment -split the data between "Korte beschrijving" and "Geraamde totale waarde" field, url ref: "https://www.tenderned.nl/aankondigingen/overzicht/303542/publicatie","https://www.tenderned.nl/aankondigingen/overzicht/303674/publicatie"

    try:
        notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),"Korte beschrijving")]//following::p[2]').text
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_summary_english) 
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -II.2.13) Inlichtingen over middelen van de Europese Unie = funding agencies, for ref url ="https://www.tenderned.nl/aankondigingen/overzicht/303814/publicatie"
    # Onsite Comment -if in below text written as " financed by European Union funds: No  " than pass the "None " in field name "T.FUNDING_AGENCIES::TEXT	" "II.2.13) Information about European Union Funds  >  The procurement is related to a project and/or programme financed by European Union funds: No  " if the abve  text written as " financed by European Union funds: YES  " than pass the "Funding agency" name as "European Agency (internal id: 1344862) " in field name "T.FUNDING_AGENCIES::TEXT"

    try:
        funding_agencies = page_details.find_element(By.XPATH, '//*[contains(text(),"Inlichtingen over middelen van de Europese Unie")]//following::p[1]').text
        if "neen" not in funding_agencies:
            funding_agencies_data = funding_agencies()
            funding_agencies_data.funding_agency = 1344862   
            funding_agencies_data.funding_agencies_cleanup()
            notice_data.funding_agencies.append(funding_agencies_data)
    except Exception as e:
        logging.info("Exception in funding_agencies: {}".format(type(e).__name__))
        pass

     # Onsite Field -II.1.5) Geraamde totale waarde
    # Onsite Comment -some sites are not contains  grossbudget_lc, url ref: "https://www.tenderned.nl/aankondigingen/overzicht/303481/publicatie"

    try:
        est_amount = page_details.find_element(By.XPATH, '//*[contains(text(),"Geraamde totale waarde")]//following::p[1]').text
        est_amount = re.sub("[^\d\.\,]","",est_amount).replace(' ','').replace(',','.').strip()
        notice_data.est_amount =float(est_amount)
        notice_data.grossbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -II.1.5) Geraamde totale waarde
    # Onsite Comment -some sites are not contains  grossbudget_lc, url ref: "https://www.tenderned.nl/aankondigingen/overzicht/303481/publicatie"

    
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
      
        
    # Onsite Field -Officiële benaming
    # Onsite Comment -None
        customer_details_data = customer_details()
        try:
            customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Officiële benaming")]//following::dd[1]').text
        except:
            customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Officiële naam")]//following::td/span[1]').text
    
    # Onsite Field -Mailing address: =  "org_address"
    # Onsite Comment -None

        try:
            customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Postadres:")]//following::dd[1]').text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass
        
    # Onsite Field -Plaats: = place
    # Onsite Comment -None

        try:
            customer_details_data.org_city = page_details.find_element(By.XPATH, '//*[contains(text(),"Plaats:")]//following::dd[1]').text
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass

        customer_details_data.org_country = 'NL'
        customer_details_data.org_language = 'NL'
    # Onsite Field -E-mail:
    # Onsite Comment -None

        try:
            customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"E-mail:")]//following::dd[1]').text
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
            org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Telefoon")]//following::dd[1]').text
            if len(org_phone)>9:
                customer_details_data.org_phone = org_phone
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass

    # Onsite Field -Fax:
    # Onsite Comment -None

        try:
            org_fax = page_details.find_element(By.XPATH, '//*[contains(text(),"Fax")]//following::dd[1]').text
            if len(org_fax)>9:
                customer_details_data.org_fax = org_fax
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
    


    try:              
        tender_criteria_data = tender_criteria()
    # Onsite Field -II.2.5) Gunningscriteria
    # Onsite Comment -above xpath code selecting multiple values you have to split only "Naam:" field for title
      
        tender_criteria_title =  page_details.find_element(By.XPATH, "//*[contains(text(),'Gunningscriteria')]//following::p[1]").text.split("Naam:")[1].split("\n")[0].strip()
        tender_criteria_data.tender_criteria_title = GoogleTranslator(source='nl', target='en').translate(tender_criteria_title)
        if 'Price' in tender_criteria_data.tender_criteria_title:
            tender_criteria_data.tender_is_price_related = True
        else:
            tender_criteria_data.tender_is_price_related = False

    # Onsite Field -II.2.5) Gunningscriteria
    # Onsite Comment -above xpath code selecting multiple values you have to split only "Weging" field for tender_criteria_weight

        try:
            tender_criteria_weight = page_details.find_element(By.XPATH, "//*[contains(text(),'Gunningscriteria')]//following::p[1]").text.split("Weging:")[1].strip()
            tender_criteria_data.tender_criteria_weight = int(tender_criteria_weight)
        except Exception as e:
            logging.info("Exception in tender_criteria_weight: {}".format(type(e).__name__))
            pass

        tender_criteria_data.tender_criteria_cleanup()
        notice_data.tender_criteria.append(tender_criteria_data)
    except Exception as e:
        logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
        pass

    try:
        lots = page_details.find_element(By.CSS_SELECTOR, 'div.tap-content').text.split('Beschrijving')
        for single_record in lots[1:]:
            
            lot_title1 = single_record.split("II.2.2) Aanvullende CPV-code(s)")[0]
            
            lot_title2 = lot_title1.split("Benaming")[1].split("\n")[1]
            if len(lot_title2)< 5 and (lot_title2 =='-'):
                continue
            lot_title = lot_title2
            
            
            if lot_title is not None and lot_title !='':
                lot_details_data = lot_details()
                lot_details_data.lot_title = lot_title
                lot_details_data.lot_title_english = GoogleTranslator(source='nl', target='en').translate(lot_title)
            else:
                lot_details_data.lot_title = notice_data.notice_title
                notice_data.is_lot_default = True
            if 'Perceel nr' in lot_title1:
                lot_actual_number = lot_title1.split('Perceel nr.:')[1].split("\n")[0]
                lot_details_data.lot_actual_number = 'Perceel nr.:'+str(lot_actual_number)
            try:
                lot_details_data.lot_number = int(lot_actual_number)
            except:
                lot_details_data.lot_number = 1

#           

        # Onsite Field -II.2.4) Beschrijving van de aanbesteding:
        # Onsite Comment -None

            try:
                lot_details_data.lot_description = page_details.find_element(By.CSS_SELECTOR, "div.tap-content > div").text.split("Beschrijving van de aanbesteding:")[1].split("Gunningscriteria")[0]
                lot_details_data.lot_description_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_description)
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass

    

        # Onsite Field -II.2.3) Plaats van uitvoering
        # Onsite Comment -above selector also select the cpv you have to only take nutcode, url ref: "https://www.tenderned.nl/aankondigingen/overzicht/303526/publicatie","https://www.tenderned.nl/aankondigingen/overzicht/303814/publicatie"

            try:
                lot_details_data.lot_nuts = page_details.find_element(By.XPATH, '//*[contains(text(),"Plaats van uitvoering")]//following::dd').text
            except Exception as e:
                logging.info("Exception in lot_nuts: {}".format(type(e).__name__))
                pass

            # Onsite Field -II.2.6) Geraamde waarde
            # Onsite Comment -url ref : "https://www.tenderned.nl/aankondigingen/overzicht/303526/publicatie"

            try:
                lot_grossbudget_lc = page_details.find_element(By.XPATH, '//*[contains(text(),"Geraamde waarde")]//following::p[1]').text
                lot_grossbudget_lc = re.sub("[^\d\.\,]","",lot_grossbudget_lc).replace(' ','').replace(',','.').strip()
                lot_details_data.lot_grossbudget_lc =float(lot_grossbudget_lc)
            except Exception as e:
                logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
                pass

    # Onsite Field -Type opdracht
    # Onsite Comment -Replace following keywords with given respective keywords ('Leveringen = Supply ','Diensten = Services ', 'Werken = Works')

            try:
                 lot_details_data.contract_type = notice_data.notice_contract_type
            except Exception as e:
                logging.info("Exception in contract_type: {}".format(type(e).__name__))
                pass

        # Onsite Field -II.2.7) Looptijd van de opdracht, de raamovereenkomst of het dynamische aankoopsysteem  = Duration of the contract, framework agreement or dynamic purchasing system
        # Onsite Comment -this xpath contains contract_start_date and end_date you have to split only start date

            try:
                contract_start_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Looptijd van de opdracht, de raamovereenkomst of het dynamische aankoopsysteem")]//following::p[1]').text.split("Aanvang:")[1].split("\n")[0]
                contract_start_date = re.findall('\d+/\d+/\d{4}',contract_start_date)[0]
                lot_details_data.contract_start_date = datetime.strptime(contract_start_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
            except Exception as e:
                logging.info("Exception in contract_start_date: {}".format(type(e).__name__))
                pass

            # Onsite Field -II.2.7) Looptijd van de opdracht, de raamovereenkomst of het dynamische aankoopsysteem  = Duration of the contract, framework agreement or dynamic purchasing system
            # Onsite Comment -this xpath contains contract_start_date and end_date you have to split only end date

            try:
                contract_end_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Looptijd van de opdracht, de raamovereenkomst of het dynamische aankoopsysteem")]//following::p[1]').text.split("Einde:")[1].split("\n")[0]
                contract_end_date = re.findall('\d+/\d+/\d{4}',contract_end_date)[0]
                lot_details_data.contract_end_date = datetime.strptime(contract_end_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
            except Exception as e:
                logging.info("Exception in contract_end_date: {}".format(type(e).__name__))
                pass


            # Onsite Field -II.2) Beschrijving
            # Onsite Comment -None

            try:
                lot_cpvs_data = lot_cpvs()

                # Onsite Field -II.2.1) Benaming
                # Onsite Comment -first go to "publicatie" tab , take only number value from this filed,   url ref: "https://www.tenderned.nl/aankondigingen/overzicht/303526/publicatie"

                lot_cpvs_data.lot_cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Aanvullende CPV-code(s)")]//following::dd[1]').text.split("-")[0].strip()
                lot_cpvs_data.lot_cpvs_cleanup()
                lot_details_data.lot_cpvs.append(lot_cpvs_data)
            except Exception as e:
                logging.info("Exception in lot_cpvs: {}".format(type(e).__name__))
                pass

            try:
                for single_record in page_details.find_elements(By.XPATH, '//*[contains(text(),"Gunningscriteria")]//following::p'):
                    lotcriteria = single_record.text
                    if 'Naam:' in lotcriteria or 'Prijs' in lotcriteria:
                        lot_criteria_data = lot_criteria()
                        if 'Prijs' in lotcriteria:
                            lot_criteria_data.lot_criteria_title = 'Price'
                        else:
                            lot_criteria_title = lotcriteria.split("Naam:")[1].split("\n")[0]
                            lot_criteria_data.lot_criteria_title = GoogleTranslator(source='auto', target='en').translate(lot_criteria_title)
                        try:
                            lot_criteria_weight = lotcriteria.split("Weging:")[1]
                            lot_criteria_data.lot_criteria_weight = int(lot_criteria_weight)
                        except:
                            pass
                        lot_criteria_data.lot_criteria_cleanup()
                        lot_details_data.lot_criteria.append(lot_criteria_data)       
            except Exception as e:
                logging.info("Exception in lot_criteria: {}".format(type(e).__name__))
                pass


            # Onsite Field -V.2.3) Naam en adres van de contractant
            # Onsite Comment -you have to select "publicatie" option to view award details

            try:
        #             for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.tap-content'):
                award_details_data = award_details()

                # Onsite Field -Officiële benaming
                # Onsite Comment -None
                award_details_data.bidder_name = page_details.find_element(By.XPATH, '//*[contains(text(),"V.2.3)")]//following::dd[1]').text
                # Onsite Field -Postadres:
                # Onsite Comment -None
                try:
                    award_details_data.address = page_details.find_element(By.XPATH, '//*[contains(text(),"V.2.3)")]//following::dd[3]').text
                except:
                    pass

                # Onsite Field -V.2.4) Inlichtingen over de waarde van de opdracht/het perceel (exclusief btw)
                # Onsite Comment -url ref: "https://www.tenderned.nl/aankondigingen/overzicht/303604/publicatie"
                try:
                    initial_estimated_value = page_details.find_element(By.XPATH, '//*[contains(text(),"Inlichtingen over de waarde van de opdracht/het perceel")]//following::p[1]').text.split("Aanvankelijk geraamde totale waarde van de opdracht/het perceel:")[1].split("\n")[1]
                    initial_estimated_value = re.sub("[^\d\.\,]","",initial_estimated_value)
                    award_details_data.initial_estimated_value  =float(initial_estimated_value.replace(' ','').strip())
                except:
                    pass
                    # Onsite Field -V.2.4) Inlichtingen over de waarde van de opdracht/het perceel (exclusief btw)
                    # Onsite Comment -url ref: "https://www.tenderned.nl/aankondigingen/overzicht/303604/publicatie"
                try:
                    grossawardvaluelc = page_details.find_element(By.XPATH, '//*[contains(text(),"Inlichtingen over de waarde van de opdracht/het perceel")]//following::p[2]').text.split("Totale waarde van de opdracht/het perceel:")[1].split("\n")[1]
                    grossawardvaluelc = re.sub("[^\d\.\,]","",grossawardvaluelc)
                    award_details_data.grossawardvaluelc  =float(grossawardvaluelc.replace(' ','').strip())
                except:
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
    
# Onsite Field -II.2.5) Gunningscriteria =  Award criteria
# Onsite Comment -None

# Onsite Field -Documenten
# Onsite Comment -you have to go "Documenten" tab for grab attachments, some attachments are not included in tenders

    try:
        Documenten_clk = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#tab-2')))
        page_details.execute_script("arguments[0].click();",Documenten_clk)
    except:
        pass

    try:              
        attachments_data = attachments()
    # Onsite Field -Alle documenten
    # Onsite Comment -None
        attachments_data.file_name = 'Download all documents'
    # Onsite Field -Alle documenten
    # Onsite Comment -above selector selects multiple field you have to take only file type, url ref : "https://www.tenderned.nl/aankondigingen/overzicht/303526/documenten"

        attachments_data.file_type = '.zip'
      
    # Onsite Field -Alle documenten
    # Onsite Comment -None

        external_url = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="app"]/tn-aankondigingen-page/div[2]/div/tn-aankondiging-detail/span/tn-aankondiging-documenten-tab/div/tn-secondary-button/div/button')))
        page_details.execute_script("arguments[0].click();",external_url)
        file_dwn = Doc_Download.file_download()
        attachments_data.external_url = str(file_dwn[0])

        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
   

    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
options = Options()
for argument in arguments:
    options.add_argument(argument)
page_main = webdriver.Chrome(options=options)
page_details = Doc_Download.page_details
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.tenderned.nl/aankondigingen/overzicht"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)

        clk1 = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="mat-select-value-1"]')))
        page_main.execute_script("arguments[0].click();",clk1)
        
        clk2 = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="mat-option-0"]')))
        page_main.execute_script("arguments[0].click();",clk2)
        
        clk3 = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="mat-option-1"]')))
        page_main.execute_script("arguments[0].click();",clk3)
        
        clk4 = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="mat-option-2"]')))
        page_main.execute_script("arguments[0].click();",clk4)
        
        clk5 = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="mat-option-3"]')))
        page_main.execute_script("arguments[0].click();",clk5)
        
        clk5 = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="mat-option-4"]')))
        page_main.execute_script("arguments[0].click();",clk5)

        try:
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="app"]/tn-aankondigingen-page/div[2]/div/tn-aankondiging-overzicht/mat-drawer-container/mat-drawer-content/div[2]/div[2]/mat-card')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="app"]/tn-aankondigingen-page/div[2]/div/tn-aankondiging-overzicht/mat-drawer-container/mat-drawer-content/div[2]/div[2]/mat-card')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
        except:
            logging.info("No new record")
            break

    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit() 
    output_json_file.copyFinalJSONToServer(output_json_folder)
