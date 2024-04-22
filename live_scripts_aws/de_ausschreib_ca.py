from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "de_ausschreib_ca"
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
SCRIPT_NAME = "de_ausschreib_ca"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(record):
    global notice_count
    global notice_data
    notice_data = tender()
        
    # after opening url click on "Vergebene Aufträge=Assigned Orders" >> "Alle vergebenen Aufträge=All orders placed"
    # format-1)if in type_of_procedure_actual "open procedure=Offenes Verfahren" or "Negotiated procedure without participation competition=Verhandlungsverfahren ohne Teilnahmewettbewerb" is present.
    # format-2)if in type_of_procedure_actual "Restricted tender=Beschränkte Ausschreibung".



    # Onsite Field -None
    # Onsite Comment -None
    notice_data.script_name = 'de_ausschreib_ca'
    
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
        publish_date = page_main.find_elements(By.CSS_SELECTOR, "table.table.table-responsive > tbody > tr > td:nth-child(1)")[record].text
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
        notice_data.local_title = page_main.find_elements(By.CSS_SELECTOR, 'table.table.table-responsive > tbody > tr > td:nth-child(2)')[record].text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    # Onsite Field -Verfahrensart
    # Onsite Comment -None
   
    try:
        notice_data.type_of_procedure_actual = page_main.find_elements(By.CSS_SELECTOR, "table.table.table-responsive > tbody > tr > td:nth-child(4)")[record].text
        notice_data.type_of_procedure = fn.procedure_mapping("assets/de_ausschreib_ca _procedure.csv",notice_data.type_of_procedure_actual)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -click on the tr
    try:  
        page_main.find_elements(By.CSS_SELECTOR,'table.table.table-responsive > tbody > tr')[record].click()
    except:
        pass
    try:
        notice_data.notice_url = page_main.current_url
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, '#pagePublicationDetails > div').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -use this selector for all format.

    try:
        document_type_description = page_main.find_element(By.CSS_SELECTOR, 'div.col-lg-12 > h1').text
        notice_data.document_type_description = GoogleTranslator(source='auto', target='en').translate(document_type_description)
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -1.use this selector for format-1

    try:
        notice_data.notice_no = page_main.find_element(By.XPATH, '//*[contains(text(),"Vergabenummer:")]//following::td').text
    except:
        try:
            notice_data.notice_no = page_main.find_element(By.CSS_SELECTOR, 'div.col-lg-12 > h2').text.split(' ')[-1]
        except Exception as e:
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass
    
    # Onsite Field -None
    # Onsite Comment -1.use this selector for format-2. 				2.split notice_no from this title.eg.,"Neubau Soleanlage SM Fürstenwalde_Los 2 ZD-2022-0052" here grab only "ZD-2022-0052". 				3.grab only if possible.

   
    
    # Onsite Field -None
    # Onsite Comment -1.use this selector for format-1.

    try:
        dispatch_date = page_main.find_element(By.XPATH, '//*[contains(text(),"Tag der Absendung dieser Bekanntmachung:")]//following::td').text
        notice_data.dispatch_date = datetime.strptime(dispatch_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in dispatch_date: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -1.use this selector for format-1.

    try:
        notice_summary_english = page_main.find_element(By.XPATH, '//*[contains(text(),"II.1.4) Kurze Beschreibung:")]//following::td').text
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_summary_english)
    except:
        try:
            notice_summary_english = page_main.find_element(By.XPATH, '//*[contains(text(),"c) Auftragsgegenstand:")]//following::td[2]').text
            notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_summary_english)
        except Exception as e:
            logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
            pass
    # Onsite Field -None
    # Onsite Comment -1.use this selector for format-2.

    
    try:
        notice_data.local_description = page_main.find_element(By.XPATH, '//*[contains(text(),"II.1.4) Kurze Beschreibung:")]//following::td[1]').text
    except:
        try:
            notice_data.local_description = page_main.find_element(By.XPATH, '//*[contains(text(),"c) Auftragsgegenstand:")]//following::td[2]').text
        except Exception as e:
            logging.info("Exception in local_description: {}".format(type(e).__name__))
            pass
    
    # Onsite Field -None
    # Onsite Comment -1.use this selector for format-1.

    try:
        est_amount = page_main.find_element(By.XPATH, '//*[contains(text(),"Gesamtwert der Beschaffung")]//following::td[1]').text
        if est_amount !='':
            notice_data.est_amount = est_amount

    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -1.use this selector for format-1.

    try:
        grossbudgetlc = page_main.find_element(By.XPATH, '//*[contains(text(),"Gesamtwert der Beschaffung")]//following::td[1]').text
        if grossbudgetlc !='':
            notice_data.grossbudgetlc = grossbudgetlc
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -1.for format-1 				2.Replace follwing keywords with given respective kywords ('Dienstleistungen =Service'),('Bauauftrag=works'),('Lieferauftrag=Supply')

    try:
        notice_data.notice_contract_type = page_main.find_element(By.XPATH, '//*[contains(text()," Art des Auftrags")]//following::td').text
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        tender_criteria_data = tender_criteria()
        # Onsite Field -None
        # Onsite Comment -1.for format-1.
        tender_criteria_data.tender_criteria_title = page_main.find_element(By.XPATH, '//*[contains(text()," Zuschlagskriterien")]//following::td').text
        tender_criteria_data.tender_criteria_cleanup()
        notice_data.tender_criteria.append(tender_criteria_data)
    except Exception as e:
        logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        cpvs_data = cpvs()
        # Onsite Field -None
        # Onsite Comment -1.use this xpath for format-1 				2.eg., "71000000-8" here take only "771000000" in cpv_code.
        cpvs_data.cpv_code = page_main.find_element(By.XPATH, '//*[contains(text(),"CPV-Code Hauptteil")]//following::td').text.split('-')[0]
        cpvs_data.cpvs_cleanup()
        notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
        # Onsite Field -None
        # Onsite Comment -None

    try:              
        # Onsite Field -None
        # Onsite Comment -1.use this xpath for format-1 2.if in below text written as " financed by European Union funds: No  " than pass the "None " in field name "funding_agency" "II.2.13) Information on European Union funds  >  The contract is related to a project and/or program financed by EU funds: no  " if the abve  text written as " financed by European Union funds: YES  " than pass the "Funding agency" name as "European Agency (internal id: 1344862) " in field name "T.FUNDING_AGENCIES::TEXT"

        funding_agency = page_main.find_element(By.XPATH, '//*[contains(text(),"II.2.13) Angaben zu Mitteln der Europäischen Union")]//following::td').text
        funding_agency = GoogleTranslator(source='auto', target='en').translate(funding_agency)
        if 'yes' in funding_agency.lower():
            funding_agencies_data = funding_agencies()
            funding_agencies_data.funding_agencies = 1344862
            funding_agencies_data.funding_agencies_cleanup()
            notice_data.funding_agencies.append(funding_agencies_data)  
    except Exception as e:
        logging.info("Exception in funding_agencies: {}".format(type(e).__name__)) 
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'DE'
        customer_details_data.org_language = 'DE'
        # Onsite Field -Vergabestelle
        # Onsite Comment -None

        try:
            customer_details_data.org_name = page_main.find_element(By.XPATH, '//*[contains(text(),"die Auskünfte über die Einlegung von Rechtsbehelfen erteilt")]//following::td').text.split('Offizielle Bezeichnung:')[1].split('\n')[0].strip()
        except Exception as e:
            logging.info("Exception in org_name: {}".format(type(e).__name__))
            pass
    
        # Onsite Field -None
        # Onsite Comment -1.use this selector for format-1. 				2.split org_address between "Postanschrift:" and "Postleitzahl / Ort:"

        try:
            customer_details_data.org_address = page_main.find_element(By.XPATH, '//*[contains(text(),"I.1) Name und Adressen")]//following::td').text.split('Postanschrift:')[1].split('NUTS-Code')[0]
        except:
            # Onsite Field -None
            # Onsite Comment -1.use this xpath for format-2.

            try:
                customer_details_data.org_address = page_main.find_element(By.XPATH, '//*[contains(text(),"Name und Anschrift:")]//following::td').text.split('Postleitzahl / Ort:')[1].split('NUTS-Code')[0]
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        
    # Onsite Field -None
    # Onsite Comment -1.use this selector for format-1. 				2.split org_phone between "Telefon: " and "E-Mail:".

        try:
            customer_details_data.org_phone = page_main.find_element(By.XPATH, '//*[contains(text(),"I.1) Name und Adressen")]//following::td').text.split('Telefon:')[1].split('\n')[0].strip()
        except:
    
            # Onsite Field -None
            # Onsite Comment -1.use this xpath for format-2

            try:
                customer_details_data.org_phone = page_main.find_element(By.XPATH, '//*[contains(text(),"Telefonnummer:")]//following::td').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
    
    # Onsite Field -None
    # Onsite Comment -1.use this selector for format-1. 				2.split org_fax after "Fax:".

        try:
            customer_details_data.org_fax = page_main.find_element(By.XPATH, '//*[contains(text(),"I.1) Name und Adressen")]//following::td').text.split('Fax: ')[1].split('\n')[0].strip()
        except:
            # Onsite Field -None
            # Onsite Comment -1.use this xpath for format-2.

            try:
                customer_details_data.org_fax = page_main.find_element(By.XPATH, '//*[contains(text(),"Faxnummer:")]//following::td').text
            except Exception as e:
                logging.info("Exception in org_fax: {}".format(type(e).__name__))
                pass
    
    # Onsite Field -None
    # Onsite Comment -1.use this selector for format-1. 				2.split org_email after "E-Mail:" and "Fax:".

        try:
            customer_details_data.org_email = page_main.find_element(By.XPATH, '//*[contains(text(),"I.1) Name und Adressen")]//following::td').text.split('E-Mail:')[1].split('\n')[0].strip() 
        except:
    
            # Onsite Field -None
            # Onsite Comment -1.use this xpath for format-2.

            try:
                customer_details_data.org_email = page_main.find_element(By.XPATH, '//*[contains(text(),"E-Mail:")]//following::td').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
    
    # Onsite Field -None
    # Onsite Comment -1.use this selector for format-1. 				2.split customer_nuts between "NUTS-Code:" and "Kontaktstelle(n):".

        try:
            customer_details_data.customer_nuts = page_main.find_element(By.XPATH, '//*[contains(text(),"I.1) Name und Adressen")]//following::td').text.split('NUTS-Code:')[1].split('\n')[0].strip() 
        except Exception as e:
            logging.info("Exception in customer_nuts: {}".format(type(e).__name__))
            pass
    
    # Onsite Field -None
    # Onsite Comment -1.use this xpath for format-1

        try:
            customer_details_data.org_website = page_main.find_element(By.XPATH, '//*[contains(text(),"Hauptadresse: (URL)")]//following::a').text
        except Exception as e:
            logging.info("Exception in org_website: {}".format(type(e).__name__))
            pass
    
    # Onsite Field -None
    # Onsite Comment -1.use this selector for format-1. 				2.split postal_code between "Postleitzahl / Ort: " and "Land". 				3.take only number in postal_code .don't grab city_name.

        try:
            postal_code = page_main.find_element(By.XPATH, '//*[contains(text(),"I.1) Name und Adressen")]//following::td').text.split('Postleitzahl / Ort:')[1].split('\n')[0].strip() 
            customer_details_data.postal_code = re.findall('\d+', postal_code)[0]
        except Exception as e:
            logging.info("Exception in postal_code: {}".format(type(e).__name__))
            pass
    
    # Onsite Field -None
    # Onsite Comment -1.use this selector for format-1. 				2.split org_city between "Postleitzahl / Ort: " and "Land". 				3.take only name.don't grab number i.e postal_code.

        try:
            customer_details_data.org_city = page_main.find_element(By.XPATH, '//*[contains(text(),"I.1) Name und Adressen")]//following::td').text.split('Postleitzahl / Ort:')[1].split('\n')[0].split(' ')[-1].strip() 
        except:
    
                # Onsite Field -None
                # Onsite Comment -1.use this selector for format-2. 				2.split org_city from third line. 				3.don't grab postal_code.

            try:
                customer_details_data.org_city = page_main.find_element(By.XPATH, '//*[contains(text(),"Name und Anschrift:")]//following::td').text
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass
    
    # Onsite Field -None
    # Onsite Comment -1.use this selector for format-1. 				2.split contact_person after "Kontaktstelle(n):".
       
        try:
            customer_details_data.contact_person = page_main.find_element(By.XPATH, '//*[contains(text(),"I.1) Name und Adressen")]//following::td').text.split('Kontaktstelle(n): ')[1].split('\n')[0]
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
        for lot_record in page_main.find_element(By.CSS_SELECTOR, '#pagePublicationDetails > div').text.split('Los-Nr: '): 
                # Onsite Field -None
                # Onsite Comment -1.use this xpath for format-1. 				2.if the multiple lots avaialbel on page than take each records.   				3.use this url for reference "https://www.ausschreibungen.ls.brandenburg.de/NetServer/PublicationControllerServlet?function=Detail&TOID=54321-NetTender-1879dcdb305-171ca95cadbce1a0&Category=ContractAward". 				4.if lot_title is not available then local_title as lot_title.
            # lot_details_data = lot_no+1
            lots_record = lot_record.split('\n')[0].strip()
            if lots_record.isdigit():
                lot_details_data = lot_details()
                lot_details_data.lot_number = int(lots_record)
                try:
                    lot_title = page_main.find_element(By.CSS_SELECTOR, '#pagePublicationDetails > div').text.split('Beschreibung der Beschaffung')[int(lots_record)].split('\n')[0]
                    lot_details_data.lot_title = GoogleTranslator(source='auto', target='en').translate(lot_title)
                except Exception as e:
                    logging.info("Exception in lot_title: {}".format(type(e).__name__))
                    pass
    
            
                    # Onsite Field -None
                    # Onsite Comment -1.use this xpath for format-1 				2.if not available then take local_title in lot_description

                try:
                    lot_description =  page_main.find_element(By.CSS_SELECTOR, '#pagePublicationDetails > div').text.split('Beschreibung der Beschaffung')[int(lots_record)].split('\n')[0]
                    lot_details_data.lot_description = GoogleTranslator(source='auto', target='en').translate(lot_description)
                except Exception as e:
                    logging.info("Exception in lot_description: {}".format(type(e).__name__))
                    pass
            
                    # Onsite Field -None
                    # Onsite Comment -1.for format-1 				2.Replace follwing keywords with given respective kywords ('Dienstleistungen =Service'),('Bauauftrag=works'),('Lieferauftrag=Supply')
                try:
                    if 'Dienstleistungen' in page_main.find_element(By.XPATH, '//*[contains(text()," Art des Auftrags")]//following::td').text:
                        lot_details_data.contract_type = 'Service'
                    elif 'Bauauftrag' in page_main.find_element(By.XPATH, '//*[contains(text()," Art des Auftrags")]//following::td').text:
                        lot_details_data.contract_type = 'works'
                    elif 'Lieferauftrag' in page_main.find_element(By.XPATH, '//*[contains(text()," Art des Auftrags")]//following::td').text:
                        lot_details_data.contract_type = 'Supply'
                except Exception as e:
                        logging.info("Exception in contract_type: {}".format(type(e).__name__))
                        pass 
            
                    # Onsite Field -None
                    # Onsite Comment -1.use this xpath for format-1. 				2.take all nuts seperatly.				2.Replace follwing keywords with given respective kywords ('Dienstleistungen =Service'),('Bauauftrag=works'),('Lieferauftrag=Supply')

                try:
                    lot_details_data.lot_nuts = page_main.find_element(By.XPATH, '//*[contains(text(),"NUTS-Code:")]//following::td').text
                except Exception as e:
                    logging.info("Exception in lot_nuts: {}".format(type(e).__name__))
                    pass
            
                # Onsite Field -None
                # Onsite Comment -None

                try:
                    lot_cpvs_data = lot_cpvs()
        
                    # Onsite Field -None
                    # Onsite Comment -1.use this xpath for format-1 				2.eg.,"CPV-Code Hauptteil: 77211500-7" here lot_cpvs_code split after "CPV-Code Hauptteil:". and also in lot_cpvs_code "77211500".  				3.grab only if possible. use this url for referencs "https://www.ausschreibungen.ls.brandenburg.de/NetServer/PublicationControllerServlet?function=Detail&TOID=54321-NetTender-1879dcdb305-171ca95cadbce1a0&Category=ContractAward"

                    lot_cpvs_data.lot_cpv_code = page_main.find_element(By.XPATH, '//*[contains(text(),"II.2.2) Weitere(r) CPV-Code(s)")]//following::td').text.split(' ')[-1].split('-')[0]
            
                    lot_cpvs_data.lot_cpvs_cleanup()
                    lot_details_data.lot_cpvs.append(lot_cpvs_data)
                except Exception as e:
                    logging.info("Exception in lot_cpvs: {}".format(type(e).__name__))
                    pass
                
                    # Onsite Field -None
                    # Onsite Comment -None

                try:
                    lot_criteria_data = lot_criteria()
        
                    # Onsite Field -None
                    # Onsite Comment -1.use this xpath for format-1

                    lot_criteria_data.lot_criteria_title = page_main.find_element(By.XPATH, '//*[contains(text()," Zuschlagskriterien")]//following::td').text
            
                    lot_criteria_data.lot_criteria_cleanup()
                    lot_details_data.lot_criteria.append(lot_criteria_data)
                except Exception as e:
                    logging.info("Exception in lot_criteria: {}".format(type(e).__name__))
                    pass
                
                    # Onsite Field -None
                    # Onsite Comment -None

                try:
                    
                    award_details_data = award_details()
                    try:
                        # Onsite Field -None
                        # Onsite Comment -1.use this xpath for format-1. 					2.take only first line in bidder_name.

                        award_details_data.bidder_name = page_main.find_element(By.XPATH, '//*[contains(text(),"V.2.3) Name und Anschrift des Wirtschaftsteilnehmers, zu dessen Gunsten der Zuschlag erteilt wurde")]//following::td').text.split('\n')[0].replace('Offizielle Bezeichnung:','')
                    except:
                            # Onsite Field -None
                            # Onsite Comment -1.use this xpath for format-2 					2.take only first line in bidder_name.
                        award_details_data.bidder_name = page_main.find_element(By.XPATH, '//*[contains(text(),"Auftragnehmer:")]//following::td').text.replace('Offizielle Bezeichnung:','')
                    
                    # Onsite Field -None
                    # Onsite Comment -1.use this xpath for format-1. 					2.split address between "Postanschrift:" and "Postleitzahl / Ort: ".
                    try:
                        award_details_data.address = page_main.find_element(By.XPATH, '//*[contains(text(),"V.2.3) Name und Anschrift des Wirtschaftsteilnehmers, zu dessen Gunsten der Zuschlag erteilt wurde")]//following::td').text.split('Postanschrift:')[1].split('Ort')[0]
                        # Onsite Field -None
                        # Onsite Comment -1.use this xpath for format-2
                    except:
                        try:
                            award_details_data.address =  page_main.find_element(By.XPATH, '//*[contains(text(),"Auftragnehmer:")]//following::td').text
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
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1

    
    page_main.back()
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.ausschreibungen.ls.brandenburg.de/NetServer/PublicationSearchControllerServlet?function=SearchPublications&Gesetzesgrundlage=All&Category=ContractAward&thContext=awardPublications"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/div[4]/div/div/div/div[2]/table[1]/tbody/tr')))
        length = len(rows)
        try:
            for record in range(0,length):
                extract_and_save_notice(record)
            if notice_count >= MAX_NOTICES:
                break
            if notice_data.publish_date is not None and notice_data.publish_date < threshold:
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
    output_json_file.copyFinalJSONToServer(output_json_folder)
