from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "de_branden"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from deep_translator import GoogleTranslator
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "de_branden"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    
    # Onsite Field -None
    # Onsite Comment -take data if available in "Veröffentlichungstyp" select "Beabsichtigte Ausschreibung" and in "Vergabeordnung" select "Alle" for gpn in "Veröffentlichungstyp" select "Ausschreibung" and in "Vergabeordnung" select "Alle" for spnin "Veröffentlichungstyp" select "Vergebener Auftrag" and in "Vergabeordnung" select "Alle" fro ca
    notice_data.script_name = 'de_branden'
    
    notice_data.main_language = 'DE'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'DE'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'EUR'
    
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -if document_type_description have keyword "Beabsichtigte Ausschreibung" then  notice type will be 2 , "Ausschreibung" then notice type will be 4 , "Vergebener Auftrag" then notice type will be 7
    try:
        notice_type = tender_html_element.find_element(By.CSS_SELECTOR, 'tr td:nth-child(4)').text
        if "Beabsichtigte Ausschreibung" in notice_type:
            notice_data.notice_type = 2
        elif "Ausschreibung" in notice_type:
            notice_data.notice_type = 4
        elif "Vergebener Auftrag" in notice_type:
            notice_data.notice_type = 7
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Typ
    # Onsite Comment -for document_type_description split data from given selector for eg: from "UVgO Beabsichtigte Ausschreibung" take only "Beabsichtigte Ausschreibung" repeat the same for spn and ca.

    try:
        document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
        document_type_description =re.split("\s",document_type_description,1)[1]
        notice_data.document_type_description = GoogleTranslator(source='auto', target='en').translate(document_type_description)
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
        publish_date = re.findall('\d+.\d+.\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
        
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Angebots- / Teilnahmefrist
    # Onsite Comment -take notice_deadline when document_type_description have keyword "Ausschreibung" only  and take notice_deadline as threshold date 1 year after the publish_date when document_type_description have keyword "Beabsichtigte Ausschreibung"

    try:
        if notice_data.notice_type == 4 or notice_data.notice_type == 2:
            notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(2)").text
            notice_deadline = re.findall('\d+.\d+.\d{4}',notice_deadline)[0]
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Aktion
    # Onsite Comment -None

    try:
        page_details_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(6) > a').get_attribute("href")
        id= page_details_url.split('id=')[1]
        id= id.split('%',1)[0]
        notice_data.notice_url = 'https://vergabemarktplatz.brandenburg.de/VMPCenter/public/company/projectForwarding.do?pid='+id
        logging.info(notice_data.notice_url)
        fn.load_page(page_details, notice_data.notice_url,  10)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
   
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#mainBox').get_attribute("outerHTML")                     
    except Exception as e:
        notice_data.notice_text = tender_html_element.get_attribute('outerHTML')
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Ausschreibungs-ID
    # Onsite Comment -None

    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"Ausschreibungs-ID")]//following::div[1]').text
    except:
        try:
            notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"Bekanntmachungs-ID:")]//following::div[1]').text
        except Exception as e:
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass
    
    
    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#content > div > div:nth-child(12) > div > div:nth-child(n) > p > b'):
            cpvs_data = cpvs()
            
        # Onsite Field -Auftragsgegenstand
        # Onsite Comment -take only "Auftragsgegenstand" field data if available in detail pg and take numeric value only and if the cpv is not available in detail pg then take auto cpv
            cpvs_data.cpv_code = single_record.text.split("-")[0]
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
    
    
    try:
        click = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,"Verfahrensangaben")))
        page_details.execute_script("arguments[0].click();",click)
        time.sleep(10)
    except:
        pass
    
    try:
        WebDriverWait(page_details, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#body')))
    except:
        pass
    
    # Onsite Field -Kurze Beschreibung
    # Onsite Comment -for notice_summary_english click on "Verfahrensangaben" in detail page and if the "Kurze Beschreibung" field is not available pass the local_title in notice_summary_english

    try:
        notice_data.notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),"Kurze Beschreibung")]//following::div[1]').text
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_summary_english)
    except Exception as e:
        
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
        
    # Onsite Field -Kurze Beschreibung
    # Onsite Comment -for local_description click on "Verfahrensangaben" in detail page and if the "Kurze Beschreibung" field is not available pass the local_title in local_description 
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Kurze Beschreibung")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -UST.-ID
    # Onsite Comment -Verfahrensangaben > "Zur Angebotsabgabe / Teilnahme auffordernde Stelle " or "Auftraggeber"

    try:
        notice_data.vat = page_details.find_element(By.XPATH, '//*[contains(text(),"UST.-ID")]//following::div[1]/span[1]').text
    except Exception as e:
        logging.info("Exception in vat: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Art des Auftrags/Art der Leistung:
    # Onsite Comment -'//*[contains(text(),"Art der Leistung:")]//following::span[1]' use this selector if given selector is not working for some tender and take only tick mark(✔) data if available and Replace following keywords with given respective keywords ("Dienstleistung" = service , "Lieferleistung"  = supply,"Bauleistung" = work)

    try:
        for single_record in page_details.find_elements(By.XPATH, '//*[contains(text(),"Art des Auftrags")]//following::label')[:3]:
            notice_con = single_record.get_attribute("outerHTML")
            if "checked-element" in notice_con:
                notice_contract_type = single_record.text
                if 'Dienstleistung' in notice_contract_type:
                    notice_data.notice_contract_type = 'Service' 
                elif 'Lieferleistung' in notice_contract_type:
                    notice_data.notice_contract_type = 'Supply'
                elif 'Bauleistung' in notice_contract_type:
                    notice_data.notice_contract_type = 'Works'
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Geschätzter Wert
    # Onsite Comment -take data in numeric if available in the detail page (if the given selector is not working use the below selector :- '//*[contains(text(),"Gesamtwert der Beschaffung (ohne MwSt.)")]//following::div[1]' )

    try:
        grossbudgetlc = page_details.find_element(By.XPATH, '//*[contains(text(),"Geschätzter Wert")]//following::div[1]').text
        grossbudgetlc = re.sub("[^\d\.\,]","",grossbudgetlc)
        notice_data.grossbudgetlc =float(grossbudgetlc.replace('.','').replace(',','.').strip())
        notice_data.est_amount = notice_data.grossbudgetlc
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
  
    # Onsite Field -Verfahrensart
    # Onsite Comment -None
    try:
        notice_data.type_of_procedure_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Verfahrensart")]//following::span[1]').text
        type_of_procedure_actual = GoogleTranslator(source='de', target='en').translate(notice_data.type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("assets/de_branden_procedure.csv",type_of_procedure_actual)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Technische und berufliche Leistungsfähigkeit
    # Onsite Comment -take only tick mark(✔) data

    try:
        notice_data.eligibility = page_details.find_element(By.XPATH, '//*[contains(text(),"Technische und berufliche Leistungsfähigkeit")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in eligibility: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -in page detail click on "Verfahrensangaben" for customer detail  Verfahrensangaben > "Zur Angebotsabgabe / Teilnahme auffordernde Stelle " or "Auftraggeber"

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'DE'
        customer_details_data.org_language = 'DE'
        
        # Onsite Field -Offizielle Bezeichnung
        # Onsite Comment -None

        try:
            customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Offizielle Bezeichnung")]//following::div[1]/span[1]').text
        except:
            try:
                customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Bezeichnung")]//following::div[1]/span[1]').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                return
        
        # Onsite Field -Kontaktstelle
        # Onsite Comment -None

        try:
            customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Kontaktstelle")]//following::div[1]/span[1]').text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Ort
        # Onsite Comment -None

        try:
            customer_details_data.org_city = page_details.find_element(By.XPATH, '//*[contains(text(),"Ort")]//following::div[1]/span[1]').text
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Postleitzahl
        # Onsite Comment -None

        try:
            customer_details_data.postal_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Postleitzahl")]//following::div[1]/span[1]').text
        except Exception as e:
            logging.info("Exception in postal_code: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -zu Händen von
        # Onsite Comment -None

        try:
            customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"zu Händen von")]//following::div[1]/span[1]').text
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Telefon
        # Onsite Comment -None

        try:
            customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Telefon")]//following::div[1]/span[1]').text
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -E-Mail
        # Onsite Comment -None

        try:
            customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"E-Mail")]//following::div[1]/span[1]').text
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Fax
        # Onsite Comment -None

        try:
            customer_details_data.org_fax = page_details.find_element(By.XPATH, '//*[contains(text(),"Fax")]//following::div[1]/span[1]').text
        except Exception as e:
            logging.info("Exception in org_fax: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Internet-Adresse (URL)
        # Onsite Comment -'//*[contains(text(),"Adresse des Beschafferprofils (URL)")]//following::a[1]' and '//*[contains(text(),"Hauptadresse (URL)")]//following::a[1]'  use this selectors if link is available in this field  ]

        try:
            customer_details_data.org_website = page_details.find_element(By.XPATH, '//*[contains(text(),"Internet-Adresse (URL)")]//following::a[1]').text
        except Exception as e:
            logging.info("Exception in org_website: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -NUTS Code
        # Onsite Comment -None

        try:
            customer_details_data.customer_nuts = page_details.find_element(By.XPATH, '//*[contains(text(),"NUTS Code")]//following::div[1]/span[1]').text
        except Exception as e:
            logging.info("Exception in customer_nuts: {}".format(type(e).__name__))
            pass
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
        
    try:              
        # Onsite Field -Angaben zu Mitteln der Europäischen Union
        # Onsite Comment -if the below text get tick mark than the tender will be funded and pass static funding agency as "European Union"(1344862)  Information on European Union funds = "Angaben zu Mitteln der Europäischen Union" > The contract is related to a project and/or program funded by EU funds ="Der Auftrag steht in Verbindung mit einem Vorhaben und/oder Programm, das aus Mitteln der EU finanziert wird"
        for single_record in page_details.find_element(By.XPATH, '//*[contains(text(),"Angaben zu Mitteln der Europäischen Union")]//following::label')[:3]:
            funding_agency = single_record.get_attribute("outerHTML")
            if "checked-element" in funding_agency:
                funding_agencies_data = funding_agencies()
                funding_agencies_data.funding_agency = 1344862
                funding_agencies_data.funding_agencies_cleanup()
                notice_data.funding_agencies.append(funding_agencies_data)
    except Exception as e:
        logging.info("Exception in funding_agencies: {}".format(type(e).__name__)) 
        pass

    try:
        tender_criteria_data = page_details.find_element(By.XPATH, '//*[contains(text(),"Zuschlagskriterien")]//following::div[1]')
        if 'table' in tender_criteria_data.get_attribute("outerHTML"):
            for tender_crit in tender_criteria_data.find_elements(By.CSS_SELECTOR, 'div'):
                tender_criteriaa = tender_crit.get_attribute("outerHTML")
                if "checked-element" in tender_criteriaa :
                    tender_criteria_data = tender_criteria()
                    tender_criteria_title = tender_crit.find_element(By.CSS_SELECTOR,'table > tbody > tr:nth-child(2) >  td:nth-child(1)').text
                    tender_criteria_data.tender_criteria_title = GoogleTranslator(source='auto', target='en').translate(tender_criteria_title)
                    tender_criteria_weight = re.sub("[^\d\.]","",tender_criteria_weight)
                    tender_criteria_data.tender_criteria_weight = int(tender_criteria_weight)
                    tender_criteria_data.tender_criteria_cleanup()
                    notice_data.tender_criteria.append(tender_criteria_data)
        else:
            for tender_crit in tender_criteria_data.find_elements(By.CSS_SELECTOR, 'label'):
                tender_criteriaa = tender_crit.get_attribute("outerHTML")
                if "checked-element" in tender_criteriaa:
                    tender_criteria_data = tender_criteria()
                    tender_criteria_title = tender_crit.text
                    tender_criteria_data.tender_criteria_title = GoogleTranslator(source='auto', target='en').translate(tender_criteria_title)
                    tender_criteria_data.tender_criteria_cleanup()
                    notice_data.tender_criteria.append(tender_criteria_data)
    except Exception as e:
        logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -IMP NOTE: if the lots are awarded to multipule bidder than select all the bidder name lot wise (ex:  https://vergabemarktplatz.brandenburg.de/VMPSatellite/public/company/project/CXP9YCU6CVS/de/processdata?3)

    try:
        lot_number = 1
        for single_record in page_details.find_elements(By.XPATH, '/html/body/div[2]/div[4]/div/span[2]/div/div[3]/div/div/div'):
            lot = single_record.text
            lot_details_data = lot_details()
            lot_details_data.lot_number = lot_number

# #         # Onsite Field -Bezeichnung     div:nth-child(2) > fieldset
# #         # Onsite Comment -take lot_title only when the field name "Bezeichnung" is available  if it is not available pass the local_title in lot_title

            try:
                if "Los-Nr." in lot and 'Art und Umfang der Leistung' in lot:
                    lot_title = lot.split('Bezeichnung')[1].split('\n')[1].split('\n')[0]
                    lot_details_data.lot_title = GoogleTranslator(source='auto', target='en').translate(lot_title)
                else:
                    lot_details_data.lot_title = notice_data.notice_title
                    notice_data.is_lot_default = True
            except:
                lot_details_data.lot_title = notice_data.notice_title
                notice_data.is_lot_default = True
                # #         # Onsite Field -Beschreibung der Beschaffung
# #         # Onsite Comment -take lot_ description only when the field name "Beschreibung der Beschaffung" is available  if it is not available pass the local_title in lot_ description

            try:
                if "Los-Nr." in lot and 'Art und Umfang der Leistung' in lot:
                    lot_description = lot.split('Art und Umfang der Leistung')[1].split('\n')[1].split('\n')[0]
                    lot_details_data.lot_description = GoogleTranslator(source='auto', target='en').translate(lot_description)
                else:
                    lot_details_data.lot_description = notice_data.notice_title
            except:
                lot_details_data.lot_description = notice_data.notice_title
                
              
        # Onsite Field -Angaben zum Wert des Auftrags/Loses (ohne MwSt.)
        # Onsite Comment -take only tick mark(✔) data and  take data in numeric if available in the detail page

            try:
                lot_grossbudget_lc = page_details.find_element(By.XPATH, '//*[contains(text(),"Angaben zum Wert des Auftrags/Loses (ohne MwSt.)")]//following::div[6]').text
                lot_grossbudget_lc = re.sub("[^\d\.\,]","",lot_grossbudget_lc)
                lot_details_data.lot_grossbudget_lc =float(lot_grossbudget_lc.replace('.','').replace(',','.').strip())
            except Exception as e:
                logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
                pass
                
        # Onsite Field -Beginn
        # Onsite Comment -take only date from the on site  "Laufzeit des Vertrags, der Rahmenvereinbarung oder des dynamischen Beschaffungssystems > Beginn "

            try:
                contract_start_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Beginn")]//following::div[1]').text
                contract_start_date = re.findall('\d+.\d+.\d{4}',contract_start_date)[0]
                lot_details_data.contract_start_date = datetime.strptime(contract_start_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
            except Exception as e:
                logging.info("Exception in contract_start_date: {}".format(type(e).__name__))
                pass
                
        # Onsite Field -Ende
        # Onsite Comment -take only date from the on site  "Laufzeit des Vertrags, der Rahmenvereinbarung oder des dynamischen Beschaffungssystems > Ende "

            try:
                contract_end_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Ende")]//following::div[4]').text
                contract_end_date = re.findall('\d+.\d+.\d{4}',contract_end_date)[0]
                lot_details_data.contract_end_date = datetime.strptime(contract_end_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
            except Exception as e:
                logging.info("Exception in contract_end_date: {}".format(type(e).__name__))
                pass

            try:
                for single_record in page_details.find_elements(By.XPATH, '//*[contains(text(),"Weiterer CPV Code")]//following::div[1]'):
                    lot_cpvs_data = lot_cpvs()
    # Onsite Field -Weiterer CPV Code
#         # Onsite Comment -take only "Weiterer CPV Code" field data if available in detail pg and take numeric value only and if the "Weiterer CPV Code" fieldis not available in detail pg then pass the tender cpv data from "Auftragsgegenstand" field
                    lot_cpvs_data.lot_cpv_code = single_record.text.split("-")[0]
                    lot_cpvs_data.lot_cpvs_cleanup()
                    lot_details_data.lot_cpvs.append(lot_cpvs_data)
            except Exception as e:
                logging.info("Exception in lot_cpvs: {}".format(type(e).__name__))
                pass


            try:
            # Onsite Field -Zuschlagskriterien
            # Onsite Comment -take "Zuschlagskriterien" as lot_criteria if available in page_detail in field name "Bezeichnung" and  take only tick mark(✔) data
                if "Los-Nr." in lot and 'Art und Umfang der Leistung' in lot:
                    lot_criteria_data = lot_criteria()
                    lot_criteria_title = lot.split('Zuschlagskriterien')[1].split('Ausführungsfristen')[0].strip()
                    lot_criteria_data.lot_criteria_title = GoogleTranslator(source='auto', target='en').translate(lot_criteria_title)
                    lot_criteria_data.lot_criteria_cleanup()
                    lot_details_data.lot_criteria.append(lot_criteria_data)
            except Exception as e:
                logging.info("Exception in lot_criteria: {}".format(type(e).__name__))
                pass

        # Onsite Field -None
        # Onsite Comment -take award details for ca only "Verfahren" > "Allgemeine Angaben" and "Auftragsvergabe" and take data from "Verfahren" > "Allgemeine Angaben" and "Auftragsvergabe" / "Verfahren" > "Name und Anschrift des Wirtschaftsteilnehmers, zu dessen Gunsten der Zuschlag erteilt wurde" only

            try:
                if notice_data.notice_type == 7:
                    notice_text_data= page_details.find_element(By.CSS_SELECTOR, '#mainBox').text
                    if "Name und Anschrift des Wirtschaftsteilnehmers, zu dessen Gunsten der Zuschlag erteilt wurde" in notice_text_data:
                        text=notice_text_data.split("Name und Anschrift des Wirtschaftsteilnehmers, zu dessen Gunsten der Zuschlag erteilt wurde")[1]
                        award_details_data = award_details()
                        
                    # Onsite Field -Offizielle Bezeichnung
                    # Onsite Comment -None

                        try:
                            award_details_data.bidder_name = text.split("Offizielle Bezeichnung")[1].split('\n')[1].split('\n')[0].strip()
                        except Exception as e:
                            logging.info("Exception in bidder_name: {}".format(type(e).__name__))
                            pass
                    # Onsite Field -Ort
                    # Onsite Comment -'//*[contains(text(),"Postleitzahl")]//following::div[1]/span[1]'   take both this fields in address
                        try:
                            award_details_data.address = text.split("Postanschrift")[1].split("Der Auftragnehmer ist ein KMU")[0].strip()
                        except:
                            pass
                    # Onsite Field -Angaben zum Wert des Auftrags/Loses (ohne MwSt.)
                    # Onsite Comment -take data in numeric if available in the detail page and take only tick mark(✔) data
                        try:
                            grossawardvaluelc = text.split("Gesamtwert des Auftrags/Loses")[1].split("Angaben zur Vergabe von Unteraufträgen")[0]
                            grossawardvaluelc = re.sub("[^\d\.\,]","",grossawardvaluelc)
                            award_details_data.grossawardvaluelc =float(grossawardvaluelc.replace('.','').replace(',','.').strip())
                        except:
                            pass
                        award_details_data.award_details_cleanup()
                        lot_details_data.award_details.append(award_details_data)
            except Exception as e:
                logging.info("Exception in award_details: {}".format(type(e).__name__))
                pass
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
            lot_number += 1
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
    try:
        click = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,"Vergabeunterlagen")))
        page_details.execute_script("arguments[0].click();",click)
        time.sleep(5)
    except:
        pass
    
    try:
        WebDriverWait(page_details, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,' span:nth-child(2) > div > h2')))
    except:
        pass

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'table.margin-bottom-20 >tbody > tr'):
            attachments_data = attachments()
             # Onsite Field -Dateiname
        # Onsite Comment -None

            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, ' td:nth-child(1)').text
            
        # Onsite Field -Typ
        # Onsite Comment -None

            try:
                attachments_data.file_type = single_record.find_element(By.CSS_SELECTOR, ' td:nth-child(1)').text.split(".")[-1]
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
       
        # Onsite Field -Größe
        # Onsite Comment -None

            try:
                attachments_data.file_size = single_record.find_element(By.CSS_SELECTOR, ' td:nth-child(4)').text
            except Exception as e:
                logging.info("Exception in file_size: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Aktion
        # Onsite Comment -for more attachment click on "Vergabeunterlagen" in detail page (click on "Alle Dokumente als ZIP-Datei herunterladen" to download the document and selector for the button 'div.csx-project-form > div > a' )

            external_url = single_record.find_element(By.CSS_SELECTOR, ' td:nth-child(5) > span').click()
            file_dwn = Doc_Download.file_download()
            attachments_data.external_url = str(file_dwn[0])
            
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
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
page_details = Doc_Download.page_details

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://vergabemarktplatz.brandenburg.de/VMPCenter/common/project/search.do?method=showExtendedSearch&fromExternal=true#eyJjcHZDb2RlcyI6W10sImNvbnRyYWN0aW5nUnVsZXMiOlsiVk9MIiwiVk9CIiwiVlNWR1YiLCJTRUtUVk8iLCJPVEhFUiJdLCJwdWJsaWNhdGlvblR5cGVzIjpbIkV4QW50ZSIsIlRlbmRlciIsIkV4UG9zdCJdLCJkaXN0YW5jZSI6MCwicG9zdGFsQ29kZSI6IiIsIm9yZGVyIjoiMCIsInBhZ2UiOiIxIiwic2VhcmNoVGV4dCI6IiIsInNvcnRGaWVsZCI6IlBST0pFQ1RfUFVCTElDQVRJT05fREFURV9MTkcifQ'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(1,9):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="listTemplate"]/table/tbody/tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="listTemplate"]/table/tbody/tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="listTemplate"]/table/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
        
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'a#nextPage.browseForward.waitClick')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    time.sleep(5)
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="listTemplate"]/table/tbody/tr'),page_check))
                except Exception as e:
                    logging.info("Exception in next_page: {}".format(type(e).__name__))
                    logging.info("No next page")
                    break
        except:
            logging.info('No new record')
            break
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit() 
    output_json_file.copyFinalJSONToServer(output_json_folder)
