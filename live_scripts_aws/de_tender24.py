from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "de_tender24"
log_config.log(SCRIPT_NAME)
import re
import jsons
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from deep_translator import GoogleTranslator
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "de_tender24"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'de_tender24'
    notice_data.main_language = 'DE'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'DE'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'EUR'
    notice_data.procurement_method = 2
    notice_data.notice_type = 4
    
    # Onsite Field -Erschienen am
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
    
    # Onsite Field -Ausschreibung
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Verfahrensart
    # Onsite Comment -split type_of_procedure_actual. eg.,"VOB, Öffentliche Ausschreibung" here take only "Öffentliche Ausschreibung".
    try:
        notice_data.type_of_procedure_actual = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text.split(',')[1].strip()
        notice_data.type_of_procedure = fn.procedure_mapping("assets/de_tender24_procedure.csv",notice_data.type_of_procedure_actual)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Abgabefrist
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(5)").text
        notice_deadline = re.findall('\d+.\d+.\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -click on the tr
    try:
        notice_url = tender_html_element.get_attribute("data-oid")
        notice_data.notice_url = 'https://www.tender24.de/NetServer/PublicationControllerServlet?function=Detail&TOID='+notice_url+'&Category=InvitationToTender'
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -take this notice_text for all format.
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#pagePublicationDetails > div').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -1.use this selector for all fromats.

    try:
        document_type_description = page_details.find_element(By.CSS_SELECTOR, 'div.col-lg-12 > h1').text
        notice_data.document_type_description = GoogleTranslator(source='auto', target='en').translate(document_type_description)
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -1.use this xpath for format-1 and format-3. 2.use this xpath if given xpath is not working "//*[contains(text(),"Vergabenummer:")]//following::td"
    # Onsite Field -None
    # Onsite Comment -1.use this selector for format-2.
    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"Vergabenr.")]//following::td').text.strip()
    except:
        try:
            notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"Vergabenummer:")]//following::td').text.strip()
        except Exception as e:
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass

    # Onsite Field -None
    # Onsite Comment -1.use this xpath for format-2.

    try:
        dispatch_date = page_details.find_element(By.XPATH, '//*[contains(text(),"VI.5) Tag der Absendung dieser Bekanntmachung:")]//following::td').text
        dispatch_date = re.findall('\d+.\d+.\d{4}',dispatch_date)[0]
        notice_data.dispatch_date = datetime.strptime(dispatch_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in dispatch_date: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -1.use this xpath for format-2 and format-4 		2.Replace follwing keywords with given respective kywords ('Dienstleistungen =Service'),('Lieferauftrag=Supply'),('Bauauftrag=Works').

    try:
        notice_contract_type = page_details.find_element(By.XPATH, '//*[contains(text()," Art des Auftrags")]//following::td').text
        if 'Lieferauftrag' in notice_contract_type:
            notice_data.notice_contract_type = 'Supply'
        elif 'Dienstleistungen' in notice_contract_type:
            notice_data.notice_contract_type = 'Service'
        elif 'Bauauftrag' in notice_contract_type:
            notice_data.notice_contract_type = 'Works'
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -1.use this xpath for format-1.   2.add this also in notice_summary_english "//*[contains(text(),"Menge und Umfang:")]//following::td"
    try:
        notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),"Umfang der Leistung:")]//following::td').text
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_summary_english)
        notice_data.local_description = notice_summary_english
    except:
        try:
            notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),"Art der Leistung:")]//following::td').text
            notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_summary_english) 
            notice_summary = page_details.find_element(By.XPATH, '//*[contains(text(),"Menge und Umfang:")]//following::td').text
            notice_summary = GoogleTranslator(source='auto', target='en').translate(notice_summary)
            notice_data.notice_summary_english = notice_summary_english+' '+notice_summary
            notice_data.local_description = notice_summary_english
        except:
            try:
                notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text()," Kurze Beschreibung:")]//following::td').text       
                notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_summary_english)
                notice_data.local_description = notice_summary_english
            except Exception as e:
                logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
                pass

    # Onsite Field -None
    # Onsite Comment -1.use this xpath for format-2. 2.split cpv_code as given eg., 45000000-7 take only 45000000  	3.take this also in cpv_code "//*[contains(text(),"II.2.2) Weitere(r) CPV-Code(s)")]//following::td". here take each cpv_code seperately.cpv code split after "CPV-Code Hauptteil:"

    try:
        cpvs_data = cpvs()
        cpvs_data.cpv_code  = page_details.find_element(By.XPATH, '//*[contains(text(),"II.1.2) CPV-Code Hauptteil")]//following::td').text.split('-')[0].strip()
        cpvs_data.cpvs_cleanup()
        notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpv: {}".format(type(e).__name__)) 
        pass
    
    try:
        single_record = page_details.find_element(By.XPATH,'//*[contains(text(),"II.2.2) Weitere(r) CPV-Code(s)")]//following::td').text
        cpv_regex = re.compile(r'\d{8}')
        cpvs_data = cpv_regex.findall(single_record)
        for cpv in cpvs_data:
            cpvs_data = cpvs()
            cpvs_data.cpv_code = cpv
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
    
    # Onsite Field -None
    # Onsite Comment -1.use this xpath for format-2.

    try:
        est_amount = page_details.find_element(By.XPATH, '//*[contains(text(),"Geschätzter Wert")]//following::td').text
        notice_data.est_amount = float(est_amount)
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -1.use this xpath for format-2.

    try:
        grossbudgetlc = page_details.find_element(By.XPATH, '//*[contains(text(),"Geschätzter Wert")]//following::td').text
        notice_data.grossbudgetlc = float(grossbudgetlc)
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'DE'
        customer_details_data.org_language = 'DE'
    # Onsite Field -Vergabestelle
    # Onsite Comment -None

        try:
            customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'table.table.table-responsive > tbody > tr > td:nth-child(3)').text
        except Exception as e:
            logging.info("Exception in org_name: {}".format(type(e).__name__))
            pass

    # Onsite Field -None
    # Onsite Comment -1.use this xpath for format-1 and format-3.
    # Onsite Field -None
    # Onsite Comment -1.use this xpath for format-2. 2.split org_address between "Postanschrift:" and "Postleitzahl / Ort: " .

        try:
            customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Anschrift:")]//following::td').text
        except:
            try:
                customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text()," Name und Adressen")]//following::td').text.split('Postanschrift:')[1].split('NUTS-Code:')[0].strip()
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass

    # Onsite Field -None
    # Onsite Comment -1.use this xpath for format-1 and format-3.  //*[contains(text(),"Fax:")]//following::td
    # Onsite Field -None
    # Onsite Comment -1.use this xpath for format-2. 2.split_org fax after "Fax:"

        try:
            customer_details_data.org_fax = page_details.find_element(By.XPATH, '//*[contains(text(),"Telefaxnummer:")]//following::td').text
        except:
            try:
                customer_details_data.org_fax = page_details.find_element(By.XPATH, '//*[contains(text()," Name und Adressen")]//following::td').text.split('Fax:')[1].strip()
            except:
                try:
                    customer_details_data.org_fax = page_details.find_element(By.XPATH, '//*[contains(text(),"Fax:")]//following::td').text 
                except Exception as e:
                    logging.info("Exception in org_fax: {}".format(type(e).__name__))
                    pass

    # Onsite Field -None
    # Onsite Comment -1.use this xpath for format-1 and format-3.
    
    # Onsite Field -None
    # Onsite Comment -1.use this xpath for format-2. 2.org_email split after "E-Mail:".

        try:
            org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"E-Mail-Adresse:")]//following::td').text.strip()
            if '.de-' in org_email:
                customer_details_data.org_email = org_email.replace('.de-','.de')                  
        except:
            try:
                org_email = page_details.find_element(By.XPATH, '//*[contains(text()," Name und Adressen")]//following::td').text
                if 'E-Mail:' in org_email and 'Fax:' in org_email:
                    customer_details_data.org_email = org_email.split('E-Mail:')[1].split('Fax:')[0].strip()
                else:
                    customer_details_data.org_email = org_email.split('E-Mail:')[1].strip()
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass

    # Onsite Field -None
    # Onsite Comment -1.use this xpath for format-1 and format-3.

        try:
            customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Telefonnummer:")]//following::td').text
        except:
            try:
                customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Telefon:")]//following::td').text
            except:
                try:
                    org_phone = page_details.find_element(By.XPATH, '//*[contains(text()," Name und Adressen")]//following::td').text
                    if 'Telefon:' in org_phone and 'E-Mail:' in org_phone:
                        customer_details_data.org_phone = org_phone.split('Telefon:')[1].split('E-Mail:')[0].strip()
                    else:
                        pass
                except Exception as e:
                    logging.info("Exception in org_phone: {}".format(type(e).__name__))
                    pass

    # Onsite Field -None
    # Onsite Comment -1.use this xpath for format-2. 2.split org_phone between "Telefon: " and "E-Mail:".

    # Onsite Field -None
    # Onsite Comment -1.use this xpath for format-1 and format-3.

        try:
            customer_details_data.org_website = page_details.find_element(By.XPATH, '//*[contains(text(),"Internet-Adresse:")]//following::td').text.strip()
        except:
            try:
                customer_details_data.org_website = page_details.find_element(By.XPATH, '//*[contains(text(),"Internet-Adresse(n)")]//following::td').text.split('Hauptadresse: (URL)')[1].split('\n')[0].strip()
            except:
                try:
                    customer_details_data.org_website = page_details.find_element(By.XPATH, '//*[contains(text(),"Internet:")]//following::td').text.strip()
                except Exception as e:
                    logging.info("Exception in org_website: {}".format(type(e).__name__))
                    pass
        
    # Onsite Field -None
    # Onsite Comment -1.use this xpath for format-2. 2.split org_website after "Hauptadresse: (URL) ".
    # Onsite Field -None
    # Onsite Comment -1.use this xpath for format-2. 2.split postal_code between "Postleitzahl / Ort: " and "Land:". 3.grab only number. eg., "15366 Hoppegarten" here take only "15366"

        try:
            postal_code = page_details.find_element(By.XPATH, '//*[contains(text()," Name und Adressen")]//following::td').text
            postal_code1 = re.findall('\d{5}',postal_code)
            for item in postal_code1:
                 customer_details_data.postal_code = item
        except Exception as e:
            logging.info("Exception in postal_code: {}".format(type(e).__name__))
            pass
        
    # Onsite Field -None
    # Onsite Comment -1.use this xpath for format-2. 2.split org_city between "Postleitzahl / Ort: " and "Land:". 3.grab only text. eg., "15366 Hoppegarten" here take only "Hoppegarten"

        try:
            customer_details_data.org_city = page_details.find_element(By.XPATH, '//*[contains(text()," Name und Adressen")]//following::td').text.split('Postleitzahl / Ort:')[1].split('Land:')[0].strip()
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass

    # Onsite Field -None
    # Onsite Comment -1.use this xpath for format-2.2.split customer_nuts after "NUTS-Code: " and "Kontaktstelle(n):".

        try:
            customer_details_data.customer_nuts = page_details.find_element(By.XPATH, '//*[contains(text()," Name und Adressen")]//following::td').text.split('NUTS-Code:')[1].split('\n')[0].strip()
        except Exception as e:
            logging.info("Exception in customer_nuts: {}".format(type(e).__name__))
            pass
        
    # Onsite Field -None
    # Onsite Comment -1.use this xpath for format-2. 2.split contact_person after "Kontaktstelle(n):".

        try:
            customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text()," Name und Adressen")]//following::td').text.split('Kontaktstelle(n):')[1].split('\n')[0].strip()
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try:              
        tender_criteria_data = tender_criteria()
    # Onsite Field -None
    # Onsite Comment -1.use this xpath for format-1 and format-3.

        try:
            tender_criteria_data.tender_criteria_title = page_details.find_element(By.XPATH, '//*[contains(text(),"Zuschlagskriterien")]//following::td[2]').text
        except:
            tender_criteria_title = page_details.find_element(By.XPATH, '//*[contains(text(),"Zuschlagskriterien")]//following::td').text
            tender_criter_title = tender_criteria_title.split('\n')
            for i in tender_criter_title:
                if 'Name:' in i:
                    tender_criteria_data.tender_criteria_title = i.split('Name:')[1].split(',')[0]
    # Onsite Field -None
    # Onsite Comment -1.use this xpath for format-2. 2.split tender_criteria_title between "Name: " and "Gewichtung: ". 		3.use this url for reference "https://www.tender24.de/NetServer/PublicationControllerServlet?function=Detail&TOID=54321-NetTender-1892b88c2d8-7af316cbcc37c9be&Category=InvitationToTender".Take each tender_criteria_title seperately.

    # Onsite Field -None
    # Onsite Comment -1.use this xpath for format-2. 2.split tender_criteria_weight after "Gewichtung: ".    3.use this url for reference "https://www.tender24.de/NetServer/PublicationControllerServlet?function=Detail&TOID=54321-NetTender-1892b88c2d8-7af316cbcc37c9be&Category=InvitationToTender".Take each tender_criteria_weight seperately.
        try:
            tender_criteria_weight = page_details.find_element(By.XPATH, '//*[contains(text(),"Zuschlagskriterien")]//following::td').text
            tender_criteria_weight = tender_criteria_weight.split('\n')
            for i in tender_criteria_weight:
                if 'Gewichtung:' in i:
                    tender_criteria_data.tender_criteria_weight =int(i.split('Gewichtung:')[1].split('\n')[0].strip())
        except Exception as e:
            logging.info("Exception in tender_criteria_weight: {}".format(type(e).__name__))
            pass

        tender_criteria_data.tender_criteria_cleanup()
        notice_data.tender_criteria.append(tender_criteria_data)
    except Exception as e:
        logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
        pass

    try:              
        
    # Onsite Field -None
    # Onsite Comment -1.use this xpath for format-2. 2.if in below text written as " financed by European Union funds: No  " than pass the "None " in field name "T.FUNDING_AGENCIES::TEXT	" "II.2.13) Information about European Union Funds  >  The procurement is related to a project and/or programme financed by European Union funds: No  " if the abve  text written as " financed by European Union funds: YES  " than pass the "Funding agency" name as "European Agency (internal id: 1344862) " in field name "T.FUNDING_AGENCIES::TEXT"

        funding_agency = page_details.find_element(By.XPATH, '//*[contains(text(),"Angaben zu Mitteln der Europäischen Union")]//following::td').text
        funding_agency = GoogleTranslator(source='auto', target='en').translate(funding_agency)
        if 'yes' in funding_agency or 'YES' in funding_agency or 'Yes' in funding_agency:
            funding_agencies_data = funding_agencies()
            funding_agencies_data.funding_agency = 1344862
            funding_agencies_data.funding_agencies_cleanup()
            notice_data.funding_agencies.append(funding_agencies_data)
            
    except Exception as e:
        logging.info("Exception in funding_agencies: {}".format(type(e).__name__)) 
        pass
    
    try:
        lot_number = 1
        lot_details_data = lot_details()
        lot_details_data.lot_number = lot_number
        
    # Onsite Field -None
    # Onsite Comment -1.use this xpath for format-1. 2.use this url for reference "https://www.tender24.de/NetServer/PublicationControllerServlet?function=Detail&TOID=54321-NetTender-18944d7702e-3465eea506075671&Category=InvitationToTender". 						3.take lot_title between "Los 1 " and "Los 2 ".

        try:
            lot_title = page_details.find_element(By.XPATH, '//*[contains(text(),"Art der Leistung:")]//following::td').text.split('Los-Nr:')[0]
            lot_details_data.lot_title = GoogleTranslator(source='auto', target='en').translate(lot_title)
        except:
            try:
                lot_title = page_details.find_element(By.XPATH, '//*[contains(text(),"II.2.1) Bezeichnung des Auftrags:")]//following::td').text.split('Los-Nr:')[0]
                lot_details_data.lot_title = GoogleTranslator(source='auto', target='en').translate(lot_title)
            except:
                try:
                    lot_details_data.lot_title = notice_data.notice_title
                    notice_data.is_lot_default = True
                except Exception as e:
                    logging.info("Exception in lot_title: {}".format(type(e).__name__))
                    pass
                
    # Onsite Field -None
    # Onsite Comment -1.use this xpath for format-1. 2.use this url for reference "https://www.ausschreibungen.ls.brandenburg.de/NetServer/PublicationControllerServlet?function=Detail&TOID=54321-NetTender-1892b080da0-699a9a6d0697cd31&Category=InvitationToTender". 						3.take lot_description between "Los 1 " and "Los 2 ".

        try:
            lot_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Menge und Umfang:")]//following::td').text
            lot_details_data.lot_description = GoogleTranslator(source='auto', target='en').translate(lot_description)
        except:
            try:
                lot_description = page_details.find_element(By.XPATH, '//*[contains(text(),"II.2.4) Beschreibung der Beschaffung")]//following::td').text
                lot_details_data.lot_description = GoogleTranslator(source='auto', target='en').translate(lot_description)
            except:
                try:
                    lot_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Umfang der Leistung:")]//following::td').text
                    lot_details_data.lot_description = GoogleTranslator(source='auto', target='en').translate(lot_description)
                except Exception as e:
                    logging.info("Exception in lot_description: {}".format(type(e).__name__))
                    pass
        
    # Onsite Field -None
    # Onsite Comment -1.use this xpath for format-1 and format-3.

        try:
            contract_start_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Beginn der Ausführungsfrist:")]//following::td').text
            contract_start_date = re.findall('\d+.\d+.\d{4}',contract_start_date)[0]
            lot_details_data.contract_start_date = datetime.strptime(contract_start_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
        except:
            try:
                contract_start_date = page_details.find_element(By.XPATH, '//*[contains(text(),"II.2.7) Laufzeit des Vertrags, der Rahmenvereinbarung oder des dynamischen Beschaffungssystems")]//following::td').text
                contract_start_date = re.findall('\d+.\d+.\d{4}',contract_start_date)[0]
                lot_details_data.contract_start_date = datetime.strptime(contract_start_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
            except Exception as e:
                logging.info("Exception in contract_start_date: {}".format(type(e).__name__))
                pass
        
    # Onsite Field -None
    # Onsite Comment -1.use this xpath for format-1 and format-3.

        try:
            contract_end_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Ende der Ausführungsfrist:")]//following::td').text
            contract_end_date = re.findall('\d+.\d+.\d{4}',contract_end_date)[0]
            lot_details_data.contract_end_date = datetime.strptime(contract_end_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
        except:
            try:
                contract_end_date = page_details.find_element(By.XPATH, '//*[contains(text(),"II.2.7) Laufzeit des Vertrags, der Rahmenvereinbarung oder des dynamischen Beschaffungssystems")]//following::td').text.split('Ende:')[1]
                contract_end_date = re.findall('\d+.\d+.\d{4}',contract_end_date)[0]
                lot_details_data.contract_end_date = datetime.strptime(contract_end_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
            except Exception as e:
                logging.info("Exception in contract_end_date: {}".format(type(e).__name__))
                pass

    # Onsite Field -None
    # Onsite Comment -1.use this xpath for format-2. 2.refer this url "https://www.tender24.de/NetServer/PublicationControllerServlet?function=Detail&TOID=54321-NetTender-1892b88c2d8-7af316cbcc37c9be&Category=InvitationToTender" 						3.if "Laufzeit in Monaten:" is presenet then take it in contract_duration. 						4.split after "Laufzeit in Monaten:".

        try:
            contract_duration = page_details.find_element(By.XPATH, '//*[contains(text(),"II.2.7) Laufzeit des Vertrags, der Rahmenvereinbarung oder des dynamischen Beschaffungssystems")]//following::td').text.split()
            contract_duration1 = re.findall('\w+: \d+',contract_duration)
            for item in contract_duration1:
                lot_details_data.contract_duration = item
        except Exception as e:
            logging.info("Exception in contract_duration: {}".format(type(e).__name__))
            pass

    # Onsite Field -None
    # Onsite Comment -1.use this xpath for format-2. 2.take only if 	"II.2.6) Geschätzter Wert" under "Los-Nr:". 3.refer this url "https://www.tender24.de/NetServer/PublicationControllerServlet?function=Detail&TOID=54321-NetTender-1891a8c2889-4ad86db6d6b49b20&Category=InvitationToTender"

        try:
            lot_grossbudget_lc = page_details.find_element(By.XPATH, '//*[contains(text(),"II.2.6) Geschätzter Wert")]//following::td').text
            lot_details_data.lot_grossbudget_lc = float(lot_grossbudget_lc)
        except Exception as e:
            logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
            pass
        
        try:
            lot_cpvs_data = lot_cpvs()
            lot_cpvs_data.lot_cpv_code  = page_details.find_element(By.XPATH, '//*[contains(text(),"II.1.2) CPV-Code Hauptteil")]//following::td').text.split('-')[0].strip()
            lot_cpvs_data.lot_cpvs_cleanup()
            lot_details_data.lot_cpvs.append(lot_cpvs_data)
        except Exception as e:
            logging.info("Exception in cpv_code: {}".format(type(e).__name__)) 
            pass

        try:
            single_record = page_details.find_element(By.XPATH,'//*[contains(text(),"II.2.2) Weitere(r) CPV-Code(s)")]//following::td').text
            cpv_regex = re.compile(r'\d{8}')
            lot_cpvs_data = cpv_regex.findall(single_record)
            for cpv in lot_cpvs_data:
                lot_cpvs_data = lot_cpvs()
                lot_cpvs_data.lot_cpv_code = cpv
                lot_cpvs_data.lot_cpvs_cleanup()
                lot_details_data.lot_cpvs.append(lot_cpvs_data)
        except Exception as e:
            logging.info("Exception in cpv_code: {}".format(type(e).__name__)) 
            pass
        
        try:
            lot_criteria_data = lot_criteria()

            # Onsite Field -None
            # Onsite Comment -1.use this xpath for format-2. 		2.if the multiple lots avaialbel on page than take each records.  	3.refer this url "https://www.tender24.de/NetServer/PublicationControllerServlet?function=Detail&TOID=54321-NetTender-1891a8c2889-4ad86db6d6b49b20&Category=InvitationToTender".

            lot_criteria_data.lot_criteria_title = page_details.find_element(By.XPATH, '//*[contains(text(),"II.2.5) Zuschlagskriterien")]//following::td').text

            lot_criteria_data.lot_criteria_cleanup()
            lot_details_data.lot_criteria.append(lot_criteria_data)
        except Exception as e:
            logging.info("Exception in lot_criteria: {}".format(type(e).__name__))
            pass

    # Onsite Field -None
    # Onsite Comment -1.use this xpath for format-2.

        try:
            lot_details_data.lot_nuts = page_details.find_element(By.XPATH, '//*[contains(text(),"NUTS-Code:")]//following::td').text.strip()
        except Exception as e:
            logging.info("Exception in lot_nuts: {}".format(type(e).__name__))
            pass
        
        lot_details_data.lot_details_cleanup()
        notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass

# Onsite Field -None
# Onsite Comment -"div.downloadDocuments > a" click on this url to get attachments_details in page_main
    try:
        attachments_url = page_details.find_element(By.XPATH, '//*[@id="printarea"]/div[1]/div[2]/a').get_attribute("href")
        fn.load_page(page_details1,attachments_url,80)
    except:
        pass       

    try:                
        attachments_data = attachments()
    # Onsite Field -None
    # Onsite Comment -1.use this selector for all format

        file_name = page_details1.find_element(By.XPATH, '//*[@id="pageParticipantDetailsGuest"]/div[1]/div/div[2]/h4').text.strip()
        attachments_data.file_name = GoogleTranslator(source='auto', target='en').translate(file_name)

        attachments_data.external_url = page_details1.find_element(By.XPATH, '//*[@id="pageParticipantDetailsGuest"]/div[1]/div/div[2]/div/table/tbody/tr/td[3]/a[2]').get_attribute('href')

        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
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
    urls = ["https://www.tender24.de/NetServer/PublicationSearchControllerServlet?function=SearchPublications&Gesetzesgrundlage=All&Category=InvitationToTender&thContext=publications"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(2,4):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/div/div/div/div/div[2]/div[2]/table[1]/tbody/tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div/div/div/div/div[2]/div[2]/table[1]/tbody/tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div/div/div/div/div[2]/div[2]/table[1]/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/div/div/div/div/div[2]/div[2]/table[1]/tbody/tr'),page_check))
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
    page_details1.quit() 
    output_json_file.copyFinalJSONToServer(output_json_folder)
