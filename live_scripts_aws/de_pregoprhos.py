from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "de_pregoprhos"
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

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "de_pregoprhos"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'de_pregoprhos'
    
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
    # Onsite Comment -split type_of_procedure_actual.eg., here "UVgO/VgV, Öffentliche Ausschreibung" take only "Öffentliche Ausschreibung".
    
    try:
        type_of_procedure_actual = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text
        notice_data.type_of_procedure_actual =re.split("\s",type_of_procedure_actual,1)[1]
        type_of_procedure_actual = GoogleTranslator(source='de', target='en').translate(notice_data.type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("assets/de_pregoprhos_procedure.csv",type_of_procedure_actual)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Abgabefrist
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(5)").text
        notice_deadline = re.findall('\d+.\d+.\d{4} \d+:\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d.%m.%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Ausschreibung
    # Onsite Comment -split notice_no. eg., here "Sanierung und Modernisierung Filmgebäude - Raumlufttechnische Anlagen (SR-2023-0003_4-020_OVK)" take only "SR-2023-0003_4-020_OVK" in notice_no.

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text.split("(")[1].split(")")[0]
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -click on the tr
    
    try:
        notice_url = tender_html_element.find_element(By.CSS_SELECTOR,"td:nth-child(1)").click()
        notice_data.notice_url = page_main.current_url
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        logging.info('notice_url:-' , notice_data.notice_url)
        notice_data.notice_url = url
    time.sleep(5)
    
    # Onsite Field -None
    # Onsite Comment -take this notice_text for all format.
    try:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, '#printarea > div.col-lg-12.contractNoticeHeader').get_attribute("outerHTML")                     
    except:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -1.use this selector for all fromats.

    try:
        notice_data.document_type_description = "Notice"
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -1.use this xpath for format-1.

    try:
        dispatch_date = page_main.find_element(By.XPATH, '//*[contains(text(),"VI.5) Tag der Absendung dieser Bekanntmachung:")]//following::td').text
        dispatch_date = re.findall('\d+.\d+.\d{4}',dispatch_date)[0]
        notice_data.dispatch_date = datetime.strptime(dispatch_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in dispatch_date: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -1.use this xpath for format-1.       2.Replace follwing keywords with given respective keywords ('Dienstleistungen =Service'),('Lieferauftrag=Supply'),('Bauauftrag=Works').

    try:
        notice_contract_type = page_main.find_element(By.XPATH, '//*[contains(text()," Art des Auftrags")]//following::td').text
        if "Dienstleistungen" in notice_contract_type:
            notice_data.notice_contract_type = "Service"
        elif "Lieferauftrag" in notice_contract_type:
            notice_data.notice_contract_type = "Supply"
        elif "Bauauftrag" in notice_contract_type:
            notice_data.notice_contract_type = "Works"
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -1.use this xpath for format-1
    
     # Onsite Field -None
    # Onsite Comment -1.use this xpath for format-2. 2.add also this "//*[contains(text(),"Umfang der Leistung:")]//following::td" in notice_summary_english.

    try:
        notice_summary_english = page_main.find_element(By.XPATH, '//*[contains(text()," Kurze Beschreibung:")]//following::td').text
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_summary_english)
    except:
        try:
            notice_summary_english = page_main.find_element(By.XPATH, '//*[contains(text(),"Art der Leistung:")]//following::td').text
            notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_summary_english)
        except:
            try:
                notice_summary_english = page_main.find_element(By.XPATH, '//*[contains(text(),"Umfang der Leistung:")]//following::td').text
                notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_summary_english)
            except Exception as e:
                logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
                pass
    
    try:
        notice_data.local_description = page_main.find_element(By.XPATH, '//*[contains(text()," Kurze Beschreibung:")]//following::td').text
    except:
        try:
            notice_data.local_description = page_main.find_element(By.XPATH, '//*[contains(text(),"Art der Leistung:")]//following::td').text
        except Exception as e:
            logging.info("Exception in local_description: {}".format(type(e).__name__))
            pass
    
    # Onsite Field -None
    # Onsite Comment -1.use this xpath for format-1.

    try:
        est_amount = page_main.find_element(By.XPATH, '//*[contains(text(),"II.1.5) Geschätzter Gesamtwert")]//following::td').text
        est_amount = re.sub("[^\d\.\,]","",est_amount)
        notice_data.est_amount =float(est_amount.replace(',','.').strip())
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
#     Onsite Field -None
#     Onsite Comment -1.use this xpath for format-1.

    try:
        notice_data.grossbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
    
    try:              
        cpvs_data = cpvs()
        # Onsite Field -None
        # Onsite Comment -1.use this xpath for format-1. 	2.split cpv_code as given eg., 45000000-7 take only 45000000.

        cpv_code = page_main.find_element(By.XPATH, '//*[contains(text(),"II.1.2) CPV-Code Hauptteil")]//following::td[1]').text
        cpvs_data.cpv_code = cpv_code.split("-")[0]
        cpvs_data.cpvs_cleanup()
        notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
        
    try:              
        # Onsite Field -None
        # Onsite Comment -1.use this xpath for format-1. 	2.if in below text written as " financed by European Union funds: No  " than pass the "None " in field name "T.FUNDING_AGENCIES::TEXT	" "II.2.13) Information about European Union Funds  >  The procurement is related to a project and/or programme financed by European Union funds: No  " if the abve  text written as " financed by European Union funds: YES  " than pass the "Funding agency" name as "European Agency (internal id: 1344862) " in field name "T.FUNDING_AGENCIES::TEXT"

        funding_agency = page_main.find_element(By.XPATH, '//*[contains(text(),"Angaben zu Mitteln der Europäischen Union")]//following::td').text
        funding_agency = GoogleTranslator(source='auto', target='en').translate(funding_agency)
        if 'yes' in funding_agency:
            funding_agencies_data = funding_agencies()
            funding_agencies_data.funding_agency = 1344862
            funding_agencies_data.funding_agencies_cleanup()
            notice_data.funding_agencies.append(funding_agencies_data)
    except Exception as e:
        logging.info("Exception in funding_agencies: {}".format(type(e).__name__)) 
        pass

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'DE'
        customer_details_data.org_language = 'DE'
        
        try:
            customer_details_data.org_name = page_main.find_element(By.XPATH, '//*[contains(text(),"Name und Adressen")]//following::td').text.split("Offizielle Bezeichnung: ")[1].split("\n")[0]
        except:
            customer_details_data.org_name = page_main.find_element(By.XPATH, '//*[contains(text(),"Name und Anschrift:")]//following::td').text.split("\n")[0]
                                                                  
        # Onsite Field -None
        # Onsite Comment -1.use this xpath for format-1. 	2.split org_address between "Postanschrift:" and "NUTS-Code:" .
        
         # Onsite Field -Non
        # Onsite Comment -1.use this xpath for format-2.

        try:
            customer_details_data.org_address = page_main.find_element(By.CSS_SELECTOR, '#pagePublicationDetails > div').text.split("Postanschrift:")[1].split("NUTS-Code:")[0]
        except:
            try:
                customer_details_data.org_address = page_main.find_element(By.XPATH, '//*[contains(text(),"Name und Anschrift:")]//following::td').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -1.use this xpath for format-1.       2.split org_fax after "Fax:".
        
         # Onsite Field -None
        # Onsite Comment -1.use this xpath for format-2. 	2.use this xpath "//*[contains(text(),"Fax:")]//following::td" if given xpath is not working.


        try:
            customer_details_data.org_fax = page_main.find_element(By.CSS_SELECTOR, '#pagePublicationDetails > div').text.split("Fax: ")[1].split("\n")[0]
        except:
            try:
                customer_details_data.org_fax = page_main.find_element(By.XPATH, '//*[contains(text(),"Telefaxnummer:")]//following::td').text
            except Exception as e:
                logging.info("Exception in org_fax: {}".format(type(e).__name__))
                pass

        # Onsite Field -None
        # Onsite Comment -1.use this xpath for format-1. 	2.org_email split between "E-Mail:" and "Fax: "
        
        # Onsite Field -None
        # Onsite Comment -1.use this xpath for format-2. 	2.use this xpath "//*[contains(text(),"E-Mail")]//following::td" if given xpath is not working.


        try:
            customer_details_data.org_email = page_main.find_element(By.CSS_SELECTOR, '#pagePublicationDetails > div').text.split("E-Mail:")[1].split("\n").strip()
        except:
            try:
                customer_details_data.org_email = page_main.find_element(By.XPATH, '//*[contains(text(),"E-Mail-Adresse:")]//following::td').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
       
        # Onsite Field -None
        # Onsite Comment -1.use this xpath for format-1.         2.split org_phone between "Telefon: " and "E-Mail:".
        
        # Onsite Field -None
        # Onsite Comment -1.use this xpath for format-2.       2.use this xpath "//*[contains(text(),"Telefon:")]//following::td" if given xpath is not working.

        try:
            customer_details_data.org_phone = page_main.find_element(By.CSS_SELECTOR, '#pagePublicationDetails > div').text.split("Telefon:")[1].split("\n")[0]
        except:
            try:
                customer_details_data.org_phone = page_main.find_element(By.XPATH, '//*[contains(text(),"Telefonnummer:")]//following::td').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
       
        
        # Onsite Field -None
        # Onsite Comment -1.use this xpath for format-1.         2.split org_website after "Hauptadresse: (URL) ".
        
        # Onsite Field -None
        # Onsite Comment -1.use this xpath for format-1. 	2.use this xpath "//*[contains(text(),"Internet:")]//following::td" if given xpath is not working.

        try:
            customer_details_data.org_website = page_main.find_element(By.XPATH, '//*[contains(text(),"Internet-Adresse(n)")]//following::td').text.split("Hauptadresse: (URL)")[1]
        except:
            try:
                customer_details_data.org_website = page_main.find_element(By.XPATH, '//*[contains(text(),"Internet-Adresse:")]//following::td').text
            except Exception as e:
                logging.info("Exception in org_website: {}".format(type(e).__name__))
                pass
        
        
        # Onsite Field -None
        # Onsite Comment -1.use this xpath for format-1. 	2.split postal_code between "Postleitzahl / Ort: " and "Land:". 	3.grab only number. eg., "15366 Hoppegarten" here take only "15366"

        try:
            postal_code = page_main.find_element(By.XPATH, '//*[contains(text(),"Name und Adressen")]//following::td').text.split("Postleitzahl / Ort:")[1].split("Land:")[0]
            customer_details_data.postal_code = re.findall('\d+',postal_code)[0]
        except Exception as e:
            logging.info("Exception in postal_code: {}".format(type(e).__name__))
            pass

        # Onsite Field -None
        # Onsite Comment -1.use this xpath for format-1.      2.split org_city between "Postleitzahl / Ort: " and "Land:". 	3.grab only text. eg., "15366 Hoppegarten" here take only "Hoppegarten"

        try:
            customer_details_data.org_city = page_main.find_element(By.XPATH, '//*[contains(text()," Name und Adressen")]//following::td').text.split("Postleitzahl / Ort:")[1].split("\n")[0]
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass

        # Onsite Field -None
        # Onsite Comment -1.use this xpath for format-1. 	2.split customer_nuts after "NUTS-Code: ".

        try:
            customer_details_data.customer_nuts = page_main.find_element(By.XPATH, '//*[contains(text()," Name und Adressen")]//following::td').text.split("NUTS-Code:")[1].split("\n")[0]
        except Exception as e:
            logging.info("Exception in customer_nuts: {}".format(type(e).__name__))
            pass
        
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
        
    try:              
        tender_criteria_data = tender_criteria()
        # Onsite Field -None
        # Onsite Comment -1.use this xpath for format-1. 	2.tender_criteria_title split after "Die nachstehenden Kriterien"
        
          # Onsite Field -None
        # Onsite Comment -1.use this xpath for format-2.

        try:
            tender_criteria_title = page_main.find_element(By.XPATH, '//*[contains(text(),"II.2.5) Zuschlagskriterien")]//following::td').text.split("Die nachstehenden Kriterien")[1].strip()
            tender_criteria_data.tender_criteria_title = GoogleTranslator(source='de', target='en').translate(tender_criteria_title)
        except:
            try:
                tender_criteria_title = page_main.find_element(By.XPATH, '//*[contains(text(),"Zuschlagskriterien")]//following::td[2]').text
                tender_criteria_data.tender_criteria_title = GoogleTranslator(source='de', target='en').translate(tender_criteria_title)
            except Exception as e:
                logging.info("Exception in tender_criteria_title: {}".format(type(e).__name__))
                pass
            
        tender_criteria_data.tender_criteria_cleanup()
        notice_data.tender_criteria.append(tender_criteria_data)
    except Exception as e:
        logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
        pass
    

    try:
        lot_number = 1
        row=0
        for lot in page_main.find_elements(By.XPATH, '//*[contains(text(),"Bezeichnung des Auftrags:")]//following::td[1]'):
            if "Los-Nr:" in lot.text:
                
                # Onsite Field -Ausschreibung
                # Onsite Comment -1.use this selector for format-2. 	2.take local_title as lot_title.
                
                # Onsite Field -None
                # Onsite Comment -1.use this xpath for format-1. 	2.use this url for reference "https://vergabe.landbw.de/NetServer/PublicationControllerServlet?function=Detail&TOID=54321-NetTender-18925921b46-1476bc44334d996&Category=InvitationToTender".	 	3.eg., "HLS Los-Nr: 1"	take only "Los-Nr: 1" in lot_actual_number.
                
                lot_details_data = lot_details()
                lot_details_data.lot_number = lot_number
                lot_title = lot.text.split('\n')[0]
                lot_details_data.lot_title = GoogleTranslator(source='auto', target='en').translate(lot_title)
                lot_details_data.lot_actual_number = lot.text.split('\n')[1]
                lot_details_data.contract_type = notice_data.notice_contract_type
                
             # Onsite Field -None
            # Onsite Comment -1.use this xpath for format-1. 	2.use this url for reference "https://prego-vergabeplattform.prhos.com/NetServer/PublicationControllerServlet?function=Detail&TOID=54321-NetTender-188f687d27e-5036756b3808ad32&Category=InvitationToTender". 						3.take lot_description seperately fot each lot.if not present then take notice_summary_english in lot_description.
            
             # Onsite Field -None
             # Onsite Comment -1.use this xpath for format-2. 	2.take notice_summary_english as lot_description if lot_description not availabel.

                try:
                    lot_description = page_main.find_elements(By.XPATH, '//*[contains(text(),"Beschreibung der Beschaffung")]//following::td[1]')[row].text
                    lot_details_data.lot_description = GoogleTranslator(source='auto', target='en').translate(lot_description)
                except:
                    pass
                
                # Onsite Field -None
                # Onsite Comment -1.use this xpath for format-2.

                try:
                    contract_start_date = page_main.find_elements(By.XPATH, '//*[contains(text(),"II.2.7) Laufzeit des Vertrags, der Rahmenvereinbarung oder des dynamischen Beschaffungssystems")]//following::td[1]')[row].text
                    contract_start_date = re.findall('\d+.\d+.\d{4}',contract_start_date)[0]
                    lot_details_data.contract_end_date = datetime.strptime(contract_start_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
                except Exception as e:
                    logging.info("Exception in contract_start_date: {}".format(type(e).__name__))
                    pass
                
               # Onsite Field -None
                 # Onsite Comment -1.use this xpath for format-1. 	2.split contract_start_date between "Beginn: " and "Ende: "
                
                 # Onsite Field -None
                # Onsite Comment -1.use this xpath for format-1. 	2.split contract_end_date between "Ende: "  and "Dieser Auftrag kann verlängert werden:"
                    
                  # Onsite Field -None
                   # Onsite Comment -1.use this xpath for format-2

                try:
                    contract_end_date = page_main.find_elements(By.XPATH, '//*[contains(text(),"II.2.7) Laufzeit des Vertrags, der Rahmenvereinbarung oder des dynamischen Beschaffungssystems")]//following::td[1]')[row].text
                    contract_end_date = re.findall('\d+.\d+.\d{4}',contract_end_date)[0]
                    lot_details_data.contract_end_date = datetime.strptime(contract_end_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
                except Exception as e:
                    logging.info("Exception in contract_end_date: {}".format(type(e).__name__))
                    pass
                
                 # Onsite Field -None
                 # Onsite Comment -1.use this xpath for format-1 	     2.take only if 	"II.2.6) Geschätzter Wert" under "Los-Nr:". 	3.split lot_grossbudget_lc after "Wert ohne MwSt.:" 	4.refer this url "https://prego-vergabeplattform.prhos.com/NetServer/PublicationControllerServlet?function=Detail&TOID=54321-NetTender-188f687d27e-5036756b3808ad32&Category=InvitationToTender".

                try:
                    lot_grossbudget_lc = page_main.find_elements(By.XPATH, '//*[contains(text(),"II.2.6) Geschätzter Wert")]//following::td[1]')[row].text
                    lot_grossbudget_lc = re.sub("[^\d\.\,]","",lot_grossbudget_lc)
                    lot_details_data.lot_grossbudget_lc =float(lot_grossbudget_lc.replace(',','.').strip())
                except Exception as e:
                    logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
                    pass
                
                 # Onsite Field -None
                # Onsite Comment -1.use this xpath for format-1. 	2.if the multiple lots avaialbel on page than take each records.  	3.refer this url "https://prego-vergabeplattform.prhos.com/NetServer/PublicationControllerServlet?function=Detail&TOID=54321-NetTender-188f687d27e-5036756b3808ad32&Category=InvitationToTender".
                try:
                    lot_details_data.lot_nuts = page_main.find_elements(By.XPATH, '//*[contains(text(),"NUTS-Code:")]//following::td[1]')[row].text
                except Exception as e:
                    logging.info("Exception in lot_nuts: {}".format(type(e).__name__))
                    pass
                
                try:
                    lot_cpvs_data = lot_cpvs()

                        # Onsite Field -None
                        # Onsite Comment -1.use this xpath for format-1.  2.eg., "CPV-Code Hauptteil: 79540000-1" here take only "79540000"
                     
                    lot_cpv = page_main.find_elements(By.XPATH, '//*[contains(text(),"CPV-Code")]//following::td[1]')[row].text
                    lot_cpvs_data.lot_cpv_code = re.findall('\d{8}',lot_cpv)[0]
                    lot_cpvs_data.lot_cpvs_cleanup()
                    lot_details_data.lot_cpvs.append(lot_cpvs_data)
                except Exception as e:
                    logging.info("Exception in lot_cpvs: {}".format(type(e).__name__))
                    pass
                
                try:
                    lot_criteria_data = lot_criteria()

                    # Onsite Field -None
                    # Onsite Comment -1.use this xpath for format-1. 	2.if the multiple lots avaialbel on page than take each records  	3.take  this url for example "https://prego-vergabeplattform.prhos.com/NetServer/PublicationControllerServlet?function=Detail&TOID=54321-NetTender-188f687d27e-5036756b3808ad32&Category=InvitationToTender".

                    lot_criteria_title = page_main.find_elements(By.XPATH, '//*[contains(text(),"II.2.5) Zuschlagskriterien")]//following::td[1]')[row].text
                    lot_criteria_data.lot_criteria_title = GoogleTranslator(source='auto', target='en').translate(lot_criteria_title)
                    lot_criteria_data.lot_criteria_cleanup()
                    lot_details_data.lot_criteria.append(lot_criteria_data)
                except Exception as e:
                    logging.info("Exception in lot_criteria: {}".format(type(e).__name__))
                    pass
                row +=1
                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
                lot_number += 1
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -"div.downloadDocuments > a" click on this url to get attachments_details in page_main

    try:
        click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"div.downloadDocuments > a"))).click()
        time.sleep(3)
    except:
        pass
    
    try:
        click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"tbody > tr > td:nth-child(3) > a > i"))).click()
        time.sleep(3)
    except:
        pass
    
    try:
        WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'div > div:nth-child(7) > h4')))
    except:
        pass
    
    try: 
        for single_record in page_main.find_element(By.CSS_SELECTOR, '#downloadSelection > div.folderBox').find_elements(By.CSS_SELECTOR, 'div > a'):
            attachments_data = attachments()

            attachments_data.external_url = single_record.get_attribute('href')
            attachments_data.file_name = single_record.text

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    try:
        click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"  div.modal-header > button > span")))
        page_main.execute_script("arguments[0].click();",click)
    except:
        pass
    
    try:
        WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'div > div:nth-child(7) > h4')))
    except:
        pass
    
    page_main.execute_script("window.history.go(-1)")
    
    try:
        WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'div.col-lg-12.contractNoticeHeader > h1')))
    except:
        pass
    
    page_main.execute_script("window.history.go(-1)")
    
    try:
        WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'table.table.table-responsive > tbody > tr')))
    except:
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
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://prego-vergabeplattform.prhos.com/NetServer/"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'table.table.table-responsive > tbody > tr')))
            length = len(rows)
            for records in range(1,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'table.table.table-responsive > tbody > tr')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break
                    
                if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                    logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                    break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
        except:
            logging.info("No Tenders")

    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)
