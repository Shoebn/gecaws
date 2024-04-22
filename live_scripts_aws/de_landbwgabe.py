from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "de_landbwgabe"
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
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "de_landbwgabe"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
# after opening the url click on "Ausschreibungen" and then select "Alle Ausschreibungen".
# format-1)if in type_of_procedure_actual "open procedure=Offenes Verfahren" or "negotiation procedure with participation competition=Verhandlungsverfahren mit Teilnahmewettbewerb" or "restricted procedure=Nichtoffenes Verfahren" is present.
# format-2)if in type_of_procedure_actual "Public tender=Öffentliche Ausschreibung" or "restricted invitation to tender with participation competition=Beschränkte Ausschreibung mit Teilnahmewettbewerb" is present.    
    
    notice_data.script_name = 'de_landbwgabe'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'EUR'  
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'DE'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'DE'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -None
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
    # Onsite Comment -split type_of_procedure_actual.eg., here "UVgO/VgV, Offenes Verfahren" take only "Offenes Verfahren".
    try:
        notice_data.type_of_procedure_actual = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text.split(",")[1].strip()
        type_of_procedure = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("assets/de_landbwgabe_procedure.csv",type_of_procedure)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Abgabefrist
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(5)").text
        notice_deadline = re.findall('\d+.\d+.\d{4} \d+:\d+',notice_deadline)[0]
        if "24" in notice_deadline:
            notice_deadline = notice_deadline.replace("24","00")
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d.%m.%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        else:
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d.%m.%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -click on the tr

    try:
        notice_url = tender_html_element.get_attribute("data-oid")
        notice_data.notice_url = 'https://vergabe.landbw.de/NetServer/PublicationControllerServlet?function=Detail&TOID='+str(notice_url)+'&Category=InvitationToTender'
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
        notice_data.document_type_description = page_details.find_element(By.CSS_SELECTOR, 'div.col-lg-12 > h1').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -1.use this xpath for format-1.

    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"Vergabenummer:")]//following::td').text
    except:
    # Onsite Field -None
    # Onsite Comment -1.use this xpath for format-2. 	2.also use this xpath "//*[contains(text(),"Vergabenummer:")]//following::td".
        try:
            notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"Vergabenr.")]//following::td').text
        except Exception as e:
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass

    try:
        dispatch_date = page_details.find_element(By.XPATH, '//*[contains(text(),"VI.5) Tag der Absendung dieser Bekanntmachung:")]//following::td').text
        dispatch_date = re.findall('\d+.\d+.\d{4}',dispatch_date)[0]
        notice_data.dispatch_date = datetime.strptime(dispatch_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in dispatch_date: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -1.use this xpath for format-1.     2.Replace follwing keywords with given respective kywords ('Dienstleistungen =Service'),('Lieferauftrag=Supply'),('Bauauftrag=Works').

    try:
        notice_contract_type = page_details.find_element(By.XPATH, '//*[contains(text()," Art des Auftrags")]//following::td').text
        if 'Dienstleistungen' in notice_contract_type:
            notice_data.notice_contract_type = 'Service'
        if 'Bauauftrag' in notice_contract_type:
            notice_data.notice_contract_type = 'Works'
        if 'Lieferauftrag' in notice_contract_type:
            notice_data.notice_contract_type = 'Supply'
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass

    try:
        notice_data.additional_tender_url = page_details.find_element(By.CSS_SELECTOR, 'td:nth-child(1) > a').text
    except:
    # Onsite Field -None
    # Onsite Comment -1.use this xapth for format-2.
        try:
            notice_data.additional_tender_url = page_details.find_element(By.XPATH, '//*[contains(text(),"unter:")]//following::td').text
        except Exception as e:
            logging.info("Exception in additional_tender_url: {}".format(type(e).__name__))
            pass
    # Onsite Field -None
    # Onsite Comment -1.use this xpath for format-1.

    try:
        notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text()," Kurze Beschreibung:")]//following::td').text
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_summary_english)
    except:
    # Onsite Field -None
    # Onsite Comment -1.use this xpath for format-2. 	2.add also this "//*[contains(text(),"Umfang der Leistung:")]//following::td" in notice_summary_english.
        try:
            notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),"Art der Leistung:")]//following::td').text
            notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_summary_english)
        except:
            try:
                notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),"Umfang der Leistung:")]//following::td').text
                notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_summary_english)
            except Exception as e:
                logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
                pass
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text()," Kurze Beschreibung:")]//following::td').text
    except:
        try:
            notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text()," Kurze Beschreibung:")]//following::td//*[contains(text(),"Art der Leistung:")]//following::td').text
        except Exception as e:
            logging.info("Exception in local_description: {}".format(type(e).__name__))
            pass
    # Onsite Field -None
    # Onsite Comment -1.use this xpath for format-1.        2.split est_amount after "Wert ohne MwSt.:"

    try:
        est_amount = page_details.find_element(By.XPATH, '//*[contains(text(),"II.1.5) Geschätzter Gesamtwert")]//following::td').text.split(":")[1]
        est_amount = re.sub("[^\d\.\,]", "", est_amount)  
        notice_data.est_amount = float(est_amount.replace('.','').replace(',','.').strip())
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -1.use this xpath for format-1. 	2.split gross_budget_lc after "Wert ohne MwSt.:"

    try:
        notice_data.grossbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        cpvs_data = cpvs()
        # Onsite Field -None
        # Onsite Comment -1.use this xpath for format-1. 	2.split cpv_code as given eg., 45000000-7 take only 45000000
        cpvs_data.cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"II.1.2) CPV-Code Hauptteil")]//following::td').text.split("-")[0]
        cpvs_data.cpvs_cleanup()
        notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        customer_details_data = customer_details()
    # Onsite Field -Vergabestelle
    # Onsite Comment -1.use this selector for all fromats.

        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'table.table.table-responsive > tbody > tr > td:nth-child(3)').text
        customer_details_data.org_country = 'DE'
        customer_details_data.org_language = 'DE'
# Onsite Field -None
# Onsite Comment -1.use this xpath for format-1. 	2.split org_address between "Postanschrift:" and "Postleitzahl / Ort: " .

        try:
            customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text()," Name und Adressen")]//following::td').text.split("Postanschrift:")[1].split("\n")[0].strip()
        except:
        # Onsite Field -None
        # Onsite Comment -1.use this xpath for format-2.
            try:
                customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Anschrift:")]//following::td').text.strip()
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass

    # Onsite Field -None
    # Onsite Comment -1.use this xpath for format-1. 	2.split org_fax after "Fax:".

        try:
            customer_details_data.org_fax = page_details.find_element(By.XPATH, '//*[contains(text()," Name und Adressen")]//following::td').text.split("Fax:")[1].split("\n")[0]
        except:
        # Onsite Field -None
        # Onsite Comment -1.use this xpath for format-2. 					2.use this xpath "//*[contains(text(),"Fax:")]//following::td" if given xpath is not working.
            try:
                customer_details_data.org_fax = page_details.find_element(By.XPATH, '//*[contains(text(),"Fax:")]//following::td').text
            except Exception as e:
                logging.info("Exception in org_fax: {}".format(type(e).__name__))
                pass

    # Onsite Field -None
    # Onsite Comment -1.use this xpath for format-1. 	2.org_email split between "E-Mail:" and "Fax: "

        try:
            customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text()," Name und Adressen")]//following::td').text.split("E-Mail:")[1].split("\n")[0].strip()
        except:
    # Onsite Field -None
    # Onsite Comment -1.use this xpath for format-2. 	2.use this xpath "//*[contains(text(),"E-Mail")]//following::td" if given xpath is not working.
            try:
                customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"E-Mail")]//following::td').text.strip()
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
        
    # Onsite Field -None
    # Onsite Comment -1.use this xpath for format-1. 	2.split org_phone between "Telefon: " and "E-Mail:".

        try:
            customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text()," Name und Adressen")]//following::td').text.split("Telefon:")[1].split("\n")[0]
        except:
    # Onsite Field -None
    # Onsite Comment -1.use this xpath for format-2. 	2.use this xpath "//*[contains(text(),"Telefon:")]//following::td" if given xpath is not working.
            try:
                customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Telefon:")]//following::td').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
        
    # Onsite Field -None
    # Onsite Comment -1.use this xpath for format-1.      2.split org_website after "Hauptadresse: (URL) ".

        try:
            customer_details_data.org_website = page_details.find_element(By.XPATH, '//*[contains(text(),"Internet-Adresse(n)")]//following::td').text.split("Hauptadresse: (URL)")[1]
        except:
    # Onsite Field -None
    # Onsite Comment -1.use this xpath for format-1 		2.use this xpath "//*[contains(text(),"Internet:")]//following::td" if given xpath is not working.
            try:
                customer_details_data.org_website = page_details.find_element(By.XPATH, '//*[contains(text(),"Internet:")]//following::td').text
            except Exception as e:
                logging.info("Exception in org_website: {}".format(type(e).__name__))
                pass
        
    # Onsite Field -None
    # Onsite Comment -1.use this xpath for format-1.         2.split postal_code between "Postleitzahl / Ort: " and "Land:". 	3.grab only number. eg., "15366 Hoppegarten" here take only "15366"

        try:
            customer_details_data.postal_code = page_details.find_element(By.XPATH, '//*[contains(text()," Name und Adressen")]//following::td').text.split("Postleitzahl / Ort: ")[1].split(" ")[0]
        except Exception as e:
            logging.info("Exception in postal_code: {}".format(type(e).__name__))
            pass

    # Onsite Field -None
    # Onsite Comment -1.use this xpath for format-1. 	2.split org_city between "Postleitzahl / Ort: " and "Land:". 	3.grab only text. eg., "15366 Hoppegarten" here take only "Hoppegarten"

        try:
            customer_details_data.org_city = page_details.find_element(By.XPATH, '//*[contains(text()," Name und Adressen")]//following::td').text.split("Postleitzahl / Ort: ")[1].split(" ")[1]
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass

    # Onsite Field -None
    # Onsite Comment -1.use this xpath for format-1. 	2.split customer_nuts after "NUTS-Code: ".

        try:
            customer_details_data.customer_nuts = page_details.find_element(By.XPATH, '//*[contains(text()," Name und Adressen")]//following::td').text.split("NUTS-Code:")[1].split("\n")[0]
        except Exception as e:
            logging.info("Exception in customer_nuts: {}".format(type(e).__name__))
            pass
        
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try:
        lot_number = 1
        lots = page_details.find_element(By.CSS_SELECTOR, '#pagePublicationDetails > div').text.split('II.2) Beschreibung')
        for lot in lots:
            if "Los-Nr:" in lot and 'Beschreibung der Beschaffung' in lot:
                lot_details_data = lot_details()
                lot_details_data.lot_number = lot_number
    # #         # Onsite Field -Bezeichnung     div:nth-child(2) > fieldset
    # #         # Onsite Comment -take lot_title only when the field name "Bezeichnung" is available  if it is not available pass the local_title in lot_title

                lot_title = lot.split('Bezeichnung des Auftrags:')[1].split('\n')[0]
                lot_details_data.lot_title = GoogleTranslator(source='auto', target='en').translate(lot_title)
                
                lot_details_data.contract_type = notice_data.notice_contract_type
                try:
                    lot_description = lot.split('Beschreibung der Beschaffung')[1].split('\n')[0]
                    lot_details_data.lot_description = GoogleTranslator(source='de', target='en').translate(lot_description)
                except:
                    try:
                        lot_description1 = page_details.find_element(By.XPATH, '//*[contains(text(),"Art der Leistung:")]//following::td').text
                        lot_description2 = page_details.find_element(By.XPATH, '//*[contains(text(),"Menge und Umfang:")]//following::td').text
                        lot_description = lot_description1 + lot_description2
                        lot_details_data.lot_description = GoogleTranslator(source='auto', target='en').translate(lot_description)
                    except:
                        pass
                try:
                    lot_details_data.lot_actual_number = page_details.find_element(By.XPATH, '//*[contains(text(),"II.2.1) Bezeichnung des Auftrags:")]//following::td').text
                except Exception as e:
                    logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                    pass

                try:
                    contract_start_date = lot.split('Beginn:')[1].split('Ende:')[0]
                    contract_start_date = re.findall('\d+.\d+.\d{4}',contract_start_date)[0]
                    lot_details_data.contract_start_date = datetime.strptime(contract_start_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
                except:
                    try:
                        contract_start_date = page_details.find_element(By.XPATH,'//*[contains(text(),"Beginn der Ausführung:")]//following::td').text
                        contract_start_date = re.findall('\d+.\d+.\d{4}',contract_start_date)[0]
                        lot_details_data.contract_start_date = datetime.strptime(contract_start_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
                    except:
                        pass

                try:
                    contract_end_date = lot.split('Ende:')[1].split('\n')[0]
                    contract_end_date = re.findall('\d+.\d+.\d{4}',contract_end_date)[0]
                    lot_details_data.contract_end_date = datetime.strptime(contract_end_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
                except:
                    try:
                        contract_end_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Fertigstellung oder Dauer der Leistungen:")]//following::td').text
                        contract_end_date = re.findall('\d+.\d+.\d{4}',contract_end_date)[0]
                        lot_details_data.contract_end_date = datetime.strptime(contract_end_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
                    except:
                        pass

                try:
                    lot_details_data.lot_grossbudget_lc = notice_data.grossbudgetlc
                except Exception as e:
                    logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
                    pass

                try:
                    lot_details_data.lot_nuts = page_details.find_element(By.XPATH, '//*[contains(text(),"NUTS-Code:")]//following::td').text
                except Exception as e:
                    logging.info("Exception in lot_nuts: {}".format(type(e).__name__))
                    pass

                try:
                    lot_cpvs_data = lot_cpvs()
                    lot_cpvs_data.lot_cpv_code=lot.split('CPV-Code Hauptteil:')[1].split('-')[0].strip()
                    lot_cpvs_data.lot_cpvs_cleanup()
                    lot_details_data.lot_cpvs.append(lot_cpvs_data)
                except Exception as e:
                    logging.info("Exception in lot_cpvs: {}".format(type(e).__name__))
                    pass
                
                try:
                    lot_criteria_data = lot_criteria()
                    # Onsite Field -None
                    # Onsite Comment -1.use this xpath for format-1.    2.if the multiple lots avaialbel on page than take each records.  	3.take  this url for example "https://vergabe.landbw.de/NetServer/PublicationControllerServlet?function=Detail&TOID=54321-NetTender-18925921b46-1476bc44334d996&Category=InvitationToTender".
                    lot_criteria_title = lot.split('Zuschlagskriterien')[1].split('\n')[0]
                    lot_criteria_data.lot_criteria_title = GoogleTranslator(source='auto', target='en').translate(lot_criteria_title)

                    lot_criteria_data.lot_criteria_cleanup()
                    lot_details_data.lot_criteria.append(lot_criteria_data)
                except Exception as e:
                    logging.info("Exception in lot_criteria: {}".format(type(e).__name__))
                    pass
            else:
                lot_details_data = lot_details()
                lot_details_data.lot_number = lot_number

                lot_details_data.contract_type = notice_data.notice_contract_type
                lot_details_data.lot_title = notice_data.notice_title
                notice_data.is_lot_default = True
                try:
                    lot_details_data.lot_description = notice_data.notice_title
                except Exception as e:
                    logging.info("Exception in lot_description: {}".format(type(e).__name__))
                    pass
            
                try:
                    contract_start_date = lot.split('Beginn:')[1].split('Ende:')[0]
                    contract_start_date = re.findall('\d+.\d+.\d{4}',contract_start_date)[0]
                    lot_details_data.contract_start_date = datetime.strptime(contract_start_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
                except:
                    try:
                        contract_start_date = page_details.find_element(By.XPATH,'//*[contains(text(),"Beginn der Ausführung:")]//following::td').text
                        contract_start_date = re.findall('\d+.\d+.\d{4}',contract_start_date)[0]
                        lot_details_data.contract_start_date = datetime.strptime(contract_start_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
                    except:
                        pass

                try:
                    contract_end_date = lot.split('Ende:')[1].split('\n')[0]
                    contract_end_date = re.findall('\d+.\d+.\d{4}',contract_end_date)[0]
                    lot_details_data.contract_end_date = datetime.strptime(contract_end_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
                except:
                    try:
                        contract_end_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Fertigstellung oder Dauer der Leistungen:")]//following::td').text
                        contract_end_date = re.findall('\d+.\d+.\d{4}',contract_end_date)[0]
                        lot_details_data.contract_end_date = datetime.strptime(contract_end_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
                    except:
                        pass
            
                try:
                    lot_details_data.lot_grossbudget_lc = notice_data.grossbudgetlc
                except Exception as e:
                    logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
                    pass

                try:
                    lot_details_data.lot_nuts = page_details.find_element(By.XPATH, '//*[contains(text(),"NUTS-Code:")]//following::td').text
                except Exception as e:
                    logging.info("Exception in lot_nuts: {}".format(type(e).__name__))
                    pass

                try:
                    lot_cpvs_data = lot_cpvs()
                    lot_cpvs_data.lot_cpv_code=lot.split('CPV-Code Hauptteil:')[1].split('-')[0].strip()
                    lot_cpvs_data.lot_cpvs_cleanup()
                    lot_details_data.lot_cpvs.append(lot_cpvs_data)
                except Exception as e:
                    logging.info("Exception in lot_cpvs: {}".format(type(e).__name__))
                    pass

                try:
                    lot_criteria_data = lot_criteria()
                    # Onsite Field -None
                    # Onsite Comment -1.use this xpath for format-1.    2.if the multiple lots avaialbel on page than take each records.  	3.take  this url for example "https://vergabe.landbw.de/NetServer/PublicationControllerServlet?function=Detail&TOID=54321-NetTender-18925921b46-1476bc44334d996&Category=InvitationToTender".
                    lot_criteria_title = page_details.find_element(By.XPATH, '//*[contains(text(),"II.2.5) Zuschlagskriterien")]//following::td').text
                    lot_criteria_data.lot_criteria_title = GoogleTranslator(source='auto', target='en').translate(lot_criteria_title)
                    
                    lot_criteria_data.lot_criteria_cleanup()
                    lot_details_data.lot_criteria.append(lot_criteria_data)
                except Exception as e:
                    logging.info("Exception in lot_criteria: {}".format(type(e).__name__))
                    pass

                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
                lot_number +=1
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
    try:              
        tender_criteria_data = tender_criteria()
    # Onsite Field -None
    # Onsite Comment -1.use this xpath for format-1. 	2.tender_criteria_title split after "Die nachstehenden Kriterien"
        try:
            tender_criteria_data.tender_criteria_title = page_details.find_element(By.XPATH, '//*[contains(text(),"II.2.5) Zuschlagskriterien")]//following::td').text.split("Die nachstehenden Kriterien")[1].split("\n")[0]
        except:
            tender_criteria_data.tender_criteria_title = page_details.find_element(By.XPATH, '//*[contains(text(),"Zuschlagskriterien")]//following::td[2]').text
            
    # Onsite Field -None
    # Onsite Comment -1.use this xpath for format-2. 	2.tender_criteria_weight split after "Gewichtung:"
        tender_criteria_weight = page_details.find_element(By.XPATH, '//*[contains(text(),"r) Die Zuschlagskriterien, sofern")]//following::td[2]').text.split("Gewichtung:")[1].split(",")[0]
        tender_criteria_data.tender_criteria_weight = int(tender_criteria_weight)

        tender_criteria_data.tender_criteria_cleanup()
        notice_data.tender_criteria.append(tender_criteria_data)
    except Exception as e:
        logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
        pass
    
    try:              
        # Onsite Field -None
        # Onsite Comment -1.use this xpath for format-1. 	2.if in below text written as " financed by European Union funds: No  " than pass the "None " in field name "T.FUNDING_AGENCIES::TEXT	" "II.2.13) Information about European Union Funds  >  The procurement is related to a project and/or programme financed by European Union funds: No  " if the abve  text written as " financed by European Union funds: YES  " than pass the "Funding agency" name as "European Agency (internal id: 1344862) " in field name "T.FUNDING_AGENCIES::TEXT"
        funding_agency = page_details.find_element(By.XPATH, '//*[contains(text(),"Angaben zu Mitteln der Europäischen Union")]//following::td').text
        if 'Nein' not in funding_agency:
            funding_agencies_data = funding_agencies()
            funding_agencies_data.funding_agency = 1344862    
            funding_agencies_data.funding_agencies_cleanup()
            notice_data.funding_agencies.append(funding_agencies_data)
    except Exception as e:
        logging.info("Exception in funding_agencies: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -"div.downloadDocuments > a" click on this url to get attachments_details in page_details

    try:           
        document_url = page_details.find_element(By.CSS_SELECTOR,'div.downloadDocuments > a').get_attribute("href")
        fn.load_page(page_details1,document_url,80)   
        attachments_data = attachments()
        attachments_data.file_name = 'tender documents'
        attachments_data.file_type = '.zip'
        clk1 = page_details1.find_element(By.CSS_SELECTOR,'a.btn-modal.zipFileContents').click()
        clk2 = WebDriverWait(page_details1, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'div.fileDownload > input:nth-child(1)')))
        page_details1.execute_script("arguments[0].click();",clk2)
        external_url = WebDriverWait(page_details1, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div.fileDownload > input:nth-child(2)')))
        page_details1.execute_script("arguments[0].click();",external_url)
        file_dwn = Doc_Download.file_download()
        attachments_data.external_url = str(file_dwn[0])

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
page_details = fn.init_chrome_driver(arguments)
page_details1 = Doc_Download.page_details
page_main = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://vergabe.landbw.de/NetServer/PublicationSearchControllerServlet?function=SearchPublications&Gesetzesgrundlage=All&Category=InvitationToTender&thContext=publications"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(2,8):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="main-frame"]/div/div/div/div/div[2]/table[1]/tbody/tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="main-frame"]/div/div/div/div/div[2]/table[1]/tbody/tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="main-frame"]/div/div/div/div/div[2]/table[1]/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="main-frame"]/div/div/div/div/div[2]/table[1]/tbody/tr'),page_check))
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
