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
SCRIPT_NAME = "de_had"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"

# Note : url is not changeble and that's why  url reference not mentioned in "on site comment"


#how to explore tender details :   1) go to url 
#                                  2) select "Advanced search" option       (left side) 
#                                  3) in the scroll bar select "Contract notice/Prior information notice" , click on submit button

                                        
# there are 4 variations in this site :     1) prior notice (preliminary information)          ------ notice type(2)  
#                                           2) public tender(format 1 for tender )                ------ notice type(4) 
#                                           3) contract notice( format 2 for tender)              ------ notice type(4)  
#                                           4) correction                                          ----- notice type(16)   
#                                           5) correction notice                                   ----- notice type(16)  





def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.script_name = 'de_had'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'DE'
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'DE'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -"Öffentliche Ausschreibung/Auftragsbekanntmachung" , "Korrekturbekanntmachung / Berichtigung" , "Vorinformation"
    # Onsite Comment -for  "Öffentliche Ausschreibung" and  "Auftragsbekanntmachung" keyword take notice type(4)  , for  "Korrekturbekanntmachung"  and "Berichtigung" this keyword take notice type (16),  for " Vorinformation" this keyword take notice type(2)
    notice_data.notice_type = 4
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'EUR'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    


    # Onsite Field -II.1.1)Bezeichnung des Auftrags
    # Onsite Comment -this xpath is local title of "prior information"  (notice type: 2)

    try:
        notice_data.local_title = page_main.find_element(By.XPATH, '//*[contains(text(),"Bezeichnung des Auftrags")]').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -d)Art des Auftrags:
    # Onsite Comment -split following data from this xpath, this xpath is local title of "public tender"  (notice type: 4)

    try:
        notice_data.local_title = page_main.find_element(By.XPATH, '//*[contains(text(),"Art des Auftrags"])').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass


    # Onsite Field -II.1.1)Bezeichnung des Auftrags
    # Onsite Comment - this xpath is local title of "contract notice"  (notice type: 4)

    try:
        notice_data.local_title = page_main.find_element(By.XPATH, '//*[contains(text(),"Bezeichnung des Auftrags")]//following::td[3]').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -II.1.1)Bezeichnung des Auftrags
    # Onsite Comment -this xpath is local title of "correction"  (notice type: 16)

    try:
        notice_data.local_title = page_main.find_element(By.XPATH, '//*[contains(text(),"Bezeichnung des Auftrags")]//following::td[3]').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    # Onsite Field -I.3)Kommunikation
    # Onsite Comment -this xpath is additional url for ("prior notice(2)" , "contract notice(4)" ,"correction(16)") "notice type" pages

    try:
        notice_data.additional_tender_url = page_main.find_element(By.XPATH, '//*[contains(text(),"Kommunikation")]//following::a').text
    except Exception as e:
        logging.info("Exception in additional_tender_url: {}".format(type(e).__name__))
        pass


    
    try:
        notice_data.local_description = page_main.find_element(By.XPATH, '//*[contains(text(),"Kurze Beschreibung")]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_main.find_element(By.XPATH, '//*[contains(text(),"Art des Auftrags")]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_main.find_element(By.XPATH, '//*[contains(text(),"Kurze Beschreibung")]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_main.find_element(By.XPATH, '//*[contains(text(),"Kurze Beschreibung")]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass

     # Onsite Field -HAD-Referenz-Nr
    # Onsite Comment -split the  following data from this field

    try:
        notice_data.notice_no = page_main.find_element(By.XPATH, '//*[contains(text(),"HAD-Referenz-Nr")]').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -veröffentlicht am/ Ablauftermin
    # Onsite Comment -this selector is "publish date" of all notice types, publication date and notice_deadline are both mention in same column, upper date is the publication date and below date is the notice_deadline

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "tr > td:nth-child(3)").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -veröffentlicht am/ Ablauftermin
    # Onsite Comment -this selector is "notice_deadline" of all type of pages, publication date and notice_deadline are both mention in same column, upper date is the publication date and below date is the notice_deadline

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "tr > td:nth-child(3)").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -this selector is "document_type_description" of all notice types

    try:
        notice_data.document_type_description = page_main.find_element(By.CSS_SELECTOR, 'td > h3').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Verfahren  Leistung
    # Onsite Comment -this selector is "type_of_procedure_actual" of all notice types, procedure types are not mentioned in some column table , there is only 2 procedures are available (open procedure, negotiated procedure)
    try:
        notice_data.type_of_procedure_actual = tender_html_element.find_element(By.CSS_SELECTOR, "tr> td:nth-child(2) > div").text
        notice_data.type_of_procedure = fn.procedure_mapping("assets/de_had_procedure",notice_data.type_of_procedure_actual)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Art des Auftrags
    # Onsite Comment -split the following data from "Art des Auftrags" field,  this selector is "notice_contract_type" of all notice types
    # eplace following keywords with given respective keywords ('Dienstleistung / Dienstleistungen = services' ,  'Lieferleistung = supply' , 'Bauauftrag = works')

    try:
        notice_data.notice_contract_type = page_main.find_element(By.XPATH, '//*[contains(text(),"Art des Auftrags")]').text
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Kurze Beschreibung
    # Onsite Comment -split following data from this xpath, this xpath is notice_summary_english of "prior information","contract notice", "correction"

    try:
        notice_data.notice_summary_english = page_main.find_element(By.XPATH, '//*[contains(text(),"Kurze Beschreibung")]').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Art des Auftrags
    # Onsite Comment -split following data from this xpath, this xpath is notice_summary_english of "public tender"  format 1

    try:
        notice_data.notice_summary_english = page_main.find_element(By.XPATH, '//*[contains(text(),"Art des Auftrags")]').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Angaben zu Mitteln der Europäischen Union
    # Onsite Comment -if in below text written as " financed by European Union funds: No " than pass the "None " in field name "T.FUNDING_AGENCIES::TEXT " "II.2.13) Information about European Union Funds > The procurement is related to a project and/or programme financed by European Union funds: No " if the abve text written as " financed by European Union funds: YES " than pass the "Funding agency" name as "European Agency (internal id: 1344862) " in field name "T.FUNDING_AGENCIES::TEXT", this xpath is the funding_agencies of (contract notice and prior information) page

    try:
        notice_data.funding_agencies = page_main.find_element(By.XPATH, '//*[contains(text(),"Angaben zu Mitteln der Europäischen Union")]').text
    except Exception as e:
        logging.info("Exception in funding_agencies: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Geschätzter Wert
    # Onsite Comment -this xpath is the gross_budget_lc of (prior information and contract notice ) page

    try:
        notice_data.grossbudgetlc = page_main.find_element(By.XPATH, '//*[contains(text(),"Geschätzter Wert")]').text
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass


    # Onsite Field -Geschätzter Wert
    # Onsite Comment -this xpath is the est_amount of (prior information and contract notice ) page

    try:
        notice_data.est_amount = page_main.find_element(By.XPATH, '//*[contains(text(),"Geschätzter Wert")]').text
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass


    

# Onsite Field -None
# Onsite Comment - this is for tender cpvs

    try:              
        for single_record in page_main.find_elements(By.CSS_SELECTOR, 'table:nth-child(2)'):
            cpvs_data = cpvs()
        # Onsite Field -Gemeinsames Vokabular für öffentliche Aufträge (CPV)
        # Onsite Comment -split the following data from this field, take only number as a cpv code, this xpath is the "cpv_code" of (correction notice)

            try:
                cpvs_data.cpv_code = page_main.find_element(By.XPATH, '//*[contains(text(),"Gemeinsames Vokabular für öffentliche Aufträge (CPV)")]').text
            except Exception as e:
                logging.info("Exception in cpv_code: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Art und Umfang der Leistun
        # Onsite Comment -split the data from this section, there is no perticular keyword for cpv code, this xpath is the "cpv_code" of (public tender)

            try:
                cpvs_data.cpv_code = page_main.find_element(By.XPATH, '//*[contains(text(),"Produktschlüssel")]').text
            except Exception as e:
                logging.info("Exception in cpv_code: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -II.1.2)CPV-Code Hauptteil:
        # Onsite Comment -split the data from this section, this xpath is the "cpv_code" of (correction)

            try:
                cpvs_data.cpv_code = page_main.find_element(By.XPATH, '//*[contains(text(),"CPV-Code Hauptteil').text
            except Exception as e:
                logging.info("Exception in cpv_code: {}".format(type(e).__name__))
                pass
        
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass




    # Onsite Field -Zuschlagskriterien
# Onsite Comment -split the "tender_criteria"  data from this field

    try:              
        for single_record in page_main.find_elements(By.XPATH, 'table:nth-child(2)'):
            tender_criteria_data = tender_criteria()
        # Onsite Field -Zuschlagskriterien
        # Onsite Comment -split the "tender_criteria_title"   from this "Kriterium" subfield,

            try:
                tender_criteria_data.tender_criteria_title = page_main.find_element(By.XPATH, '//*[contains(text(),"Zuschlagskriterien")]').text
            except Exception as e:
                logging.info("Exception in tender_criteria_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Zuschlagskriterien
        # Onsite Comment -split the "tender_criteria_weight"   from this "Gewichtung" subfield

            try:
                tender_criteria_data.tender_criteria_weight = page_main.find_element(By.XPATH, '//*[contains(text(),"Zuschlagskriterien")]').text
            except Exception as e:
                logging.info("Exception in tender_criteria_weight: {}".format(type(e).__name__))
                pass
        
            tender_criteria_data.tender_criteria_cleanup()
            notice_data.tender_criteria.append(tender_criteria_data)
    except Exception as e:
        logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
        pass


    
    # Onsite Field -HAD-Ref
    # Onsite Comment -this xpath is the notice_url for all notice_type page

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'form > table > tbody > tr').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -this selector is  the notice_text for all "notice type" page
    try:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, 'table:nth-child(2)').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
# Onsite Field -"Abschnitt I: Öffentlicher Auftraggeber" ,  "a)	Auftraggeber (Vergabestelle):"
# Onsite Comment -for customer details there are two formats  1) "Abschnitt I: Öffentlicher Auftraggeber" and  2) "a)Auftraggeber (Vergabestelle):" , (first format is for "prior notice", "contract notice", and "correction") and (second format is for "public tender" and "correction notice")

    try:              
        for single_record in page_main.find_elements(By.CSS_SELECTOR, 'table:nth-child(2)'):
            customer_details_data = customer_details()
        # Onsite Field -Vergabestelle/Ort
        # Onsite Comment -this selector is "org_name" of all notice types

            try:
                customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(4)').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -E-Mail:
        # Onsite Comment -this selector is  "org_email" for  all notice type pages,   take data from "E-mail:" named field

            try:
                customer_details_data.org_email = page_main.find_element(By.XPATH, '//*[contains(text(),"E-Mail")]').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Vergabestelle/Ort
        # Onsite Comment -one column contains two data first is "org_name" and another is "org-address",   we have to take org_name's following data for ex :("65549 Limburg", "63069 Offenbach am Main"), this selector is for all notice type pages

            try:
                customer_details_data.org_address = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(4)').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        
            customer_details_data.org_country = 'DE'
            customer_details_data.org_language = 'DE'
        # Onsite Field -Fax
        # Onsite Comment -this xpath is the "org_fax"  of  all (notice_type ) pages

            try:
                customer_details_data.org_fax = page_main.find_element(By.XPATH, '//*[contains(text(),"Fax")]').text
            except Exception as e:
                logging.info("Exception in org_fax: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Telefon:
        # Onsite Comment -this xpath is the "org_phone"  of  all (notice_type ) pages, some pages cannot detect field, you can split data from "Telefon:" field

            try:
                customer_details_data.org_phone = page_main.find_element(By.XPATH, '//*[contains(text(),"Telefon:")]').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass


        # Onsite Field -Haupttätigkeit(en)
        # Onsite Comment -split the following data from 'Haupttätigkeit(en)'  ,  the details include in "prior notice(2)" and "contract notice(4)" notice type pages

            try:
                customer_details_data.customer_main_activity = page_main.find_element(By.XPATH, '//*[contains(text(),"Haupttätigkeit(en)")]').text
            except Exception as e:
                logging.info("Exception in customer_main_activity: {}".format(type(e).__name__))
                pass    

          # Onsite Field -"Art des öffentlichen Auftraggebers"
        # Onsite Comment -split the following data from 'Art des öffentlichen Auftraggebers'  ,  the details include in "prior notice(2)" and "contract notice(4)" notice type page

            try:
                customer_details_data.type_of_authority_code = page_main.find_element(By.XPATH, '//*[contains(text(),"Art des öffentlichen Auftraggebers")]').text
            except Exception as e:
                logging.info("Exception in type_of_authority_code: {}".format(type(e).__name__))
                pass    
        
        # Onsite Field -NUTS-Code:
        # Onsite Comment -this xpath is the "nut code"  of  all (notice_type ) pages

            try:
                customer_details_data.customer_nuts = page_main.find_element(By.XPATH, '//*[contains(text(),"NUTS-Code:")]').text
            except Exception as e:
                logging.info("Exception in customer_nuts: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Hauptadresse
        # Onsite Comment -this xpath is the "org_website"  of   ("prior notice", "contract notice","correction") pages

            try:
                customer_details_data.org_website = page_main.find_element(By.XPATH, '//*[contains(text(),"Hauptadresse")]//following::a').text
            except Exception as e:
                logging.info("Exception in org_website: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Name und Adressen
        # Onsite Comment -this xpath is the "postal code"  of   ("prior notice", "contract notice","correction") page, split the data from 3rd position which is 5 digit number

            try:
                customer_details_data.postal_code = page_main.find_element(By.XPATH, '//*[contains(text(),"Name und Adressen")]').text
            except Exception as e:
                logging.info("Exception in postal_code: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Stadt/Ort
        # Onsite Comment -this xpath is the "postal code"  of   ("public tender","correction notice") page, split the data from "Stadt/Ort" field and it is 5 digit number

            try:
                customer_details_data.postal_code = page_main.find_element(By.XPATH, '//*[contains(text(),"Auftraggeber (Vergabestelle):")]').text
            except Exception as e:
                logging.info("Exception in postal_code: {}".format(type(e).__name__))
                pass
        
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -this loop contains all notice_type of lot details
# Onsite Comment -None

    try:              
        for single_record in page_main.find_elements(By.CSS_SELECTOR, 'table:nth-child(2)'):
            lot_details_data = lot_details()
        # Onsite Field -Bezeichnung des Auftrags
        # Onsite Comment -this xpath is the "lot title" of "prior notice(2)","contract notice(4)" and "correction(16)"

            try:
                lot_details_data.lot_title = page_main.find_element(By.XPATH, '//*[contains(text(),"Bezeichnung des Auftrags")]').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -"Los 1:" , "Los 2:" , "Los 3"
        # Onsite Comment -this xpath is the "lot title" of "public tender(4)", split the data from this onsite field, inner subfield name is "kurze Beschreibung"

            try:
                lot_details_data.lot_title = page_main.find_element(By.XPATH, 'tr:nth-child(12) > td:nth-child(3) > b').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Beschreibung der Beschaffung
        # Onsite Comment -this xpath is the "lot description" of "prior notice(2)","contract notice(4)"

            try:
                lot_details_data.lot_description = page_main.find_element(By.XPATH, '//*[contains(text(),"Beschreibung der Beschaffung")]').text
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -"Los 1:" , "Los 2:" , "Los 3"
        # Onsite Comment -this xpath is the "lot description" of "public tender(4)", split the description from "kurze Beschreibung" this subfield

            try:
                lot_details_data.lot_description = page_main.find_element(By.XPATH, '//*[contains(text(),"Größe und Art der einzelnen Lose:")]').text
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -II.1.4)Kurze Beschreibung
        # Onsite Comment -this xpath is the "lot description" of "correction(16)"

            try:
                lot_details_data.lot_description = page_main.find_element(By.XPATH, '//*[contains(text(),"Kurze Beschreibung")]').text
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -f)Art und Umfang der einzelnen Lose:
        # Onsite Comment -this xpath is the "lot number" of "public tender(4)"

            try:
                lot_details_data.lot_number = page_main.find_element(By.XPATH, 'tr:nth-child(12) > td:nth-child(3) > b').text
            except Exception as e:
                logging.info("Exception in lot_number: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Geschätzter Wert
        # Onsite Comment -this xpath is the "lot_grossbudgetlc" of  (prior information) and (contract notice ) page

            try:
                lot_details_data.lot_grossbudget_lc = page_main.find_element(By.XPATH, '//*[contains(text(),"Geschätzter Wert")]').text
            except Exception as e:
                logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
                pass

        
        # Onsite Field -Ausführungsfristen:
        # Onsite Comment -this xpath is the "contract_start_date" of  (public tender(4))

            try:
                lot_details_data.contract_start_date = page_main.find_element(By.XPATH, '//*[contains(text(),"Ausführungsfristen:")]//following::b[1]').text
            except Exception as e:
                logging.info("Exception in contract_start_date: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -II.2.7)Laufzeit des Vertrags, der Rahmenvereinbarung oder des dynamischen Beschaffungssystems
        # Onsite Comment -this xpath is the "contract_start_date" of  (contract notice(4)), split the data from "Beginn:" keyword

            try:
                lot_details_data.contract_start_date = page_main.find_element(By.XPATH, '//*[contains(text(),"Laufzeit des Vertrags")]').text
            except Exception as e:
                logging.info("Exception in contract_start_date: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Ausführungsfristen:
        # Onsite Comment -this xpath is the "contract_end_date" of  (public tender)

            try:
                lot_details_data.contract_end_date = page_main.find_element(By.XPATH, '//*[contains(text(),"Ausführungsfristen:")]//following::b[2]').text
            except Exception as e:
                logging.info("Exception in contract_end_date: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -II.2.7)Laufzeit des Vertrags, der Rahmenvereinbarung oder des dynamischen Beschaffungssystems
        # Onsite Comment -this xpath is the "contract_end_date" of  (contract notice), split the data from "Ende:" keyword

            try:
                lot_details_data.contract_end_date = page_main.find_element(By.XPATH, '//*[contains(text(),"Laufzeit des Vertrags")]').text
            except Exception as e:
                logging.info("Exception in contract_end_date: {}".format(type(e).__name__))
                pass
        
        
        # Onsite Field -II.2.3)Erfüllungsort
        # Onsite Comment -take the second value from xpath, split the following data from this field, this xpath is the "lot_nuts" of  ("prior notice","contract notice","correction") page

            try:
                lot_details_data.lot_nuts = page_main.find_element(By.XPATH, '//*[contains(text(),"NUTS-Code:")]').text
            except Exception as e:
                logging.info("Exception in lot_nuts: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -NUTS-Code :
        # Onsite Comment -take the follo split the following data from this field, this xpath is the "lot_nuts" of  ("public tender") page

            try:
                lot_details_data.lot_nuts = page_main.find_element(By.XPATH, '//*[contains(text(),"NUTS-Code")]').text
            except Exception as e:
                logging.info("Exception in lot_nuts: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Art des Auftrags
        # Onsite Comment -take following data from this field, this xpath is the "contract type" of  all "notice type" pages

            try:
                lot_details_data.contract_type = page_main.find_element(By.XPATH, '//*[contains(text(),"Art des Auftrags")]').text
            except Exception as e:
                logging.info("Exception in contract_type: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Art des Auftrags
        # Onsite Comment -take following data from this field, this xpath is the "contract type" of  all "notice type" pages

            try:
                lot_details_data.contract_type = page_main.find_element(By.XPATH, '//*[contains(text(),"Art des Auftrags")]').text
            except Exception as e:
                logging.info("Exception in contract_type: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -None

            try:
                for single_record in page_main.find_elements(By.CSS_SELECTOR, 'table:nth-child(2)'):
                    lot_cpvs_data = lot_cpvs()
		
            
			         # Onsite Field -II.2.2)Weitere(r) CPV-Code(s)
                    # Onsite Comment -this xpath is the "lot_cpv_code" of (contract notice) and (prior notice), split the following data from this xpath

                    lot_cpvs_data.lot_cpv_code = page_main.find_element(By.XPATH, '//*[contains(text(),"Weitere(r) CPV-Code(s)")]').text
			
                    
                    lot_cpvs_data.lot_cpvs_cleanup()
                    lot_details_data.lot_cpvs.append(lot_cpvs_data)
            except Exception as e:
                logging.info("Exception in lot_cpvs: {}".format(type(e).__name__))
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
page_main = fn.init_chrome_driver(arguments) 
page_details = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.had.de/onlinesuche_erweitert.html"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,5):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="innerframe"]/table[1]/tbody/tr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="innerframe"]/table[1]/tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="innerframe"]/table[1]/tbody/tr')))[records]
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="innerframe"]/table[1]/tbody/tr'),page_check))
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