
from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "de_deutsrent_ca"
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
SCRIPT_NAME = "de_deutsrent_ca"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

# format-1)in tender_html_element after click on "Vergebene Aufträge >> Liefer- und Dienstleistungen"=="Assigned Orders >> Delivery and Services" and if in type_of_procedure_actual "Negotiated award without participation competition=Verhandlungsvergabe ohne Teilnahmewettbewerb" or "Restricted tender=Beschränkte Ausschreibung" is present. 
# format-2)in tender_html_element after click on "Vergebene Aufträge >> Liefer- und Dienstleistungen"=="Assigned Orders >> Delivery and Services" and if in type_of_procedure_actual "open procedure=Offenes Verfahren" or "Negotiated procedure without participation competition	= Verhandlungsverfahren ohne Teilnahmewettbewerb" is present.

# format-3)in tender_html_element after click on "Vergebene Aufträge >> Bauleistungen"=="Assigned Orders >> construction work" and if in type_of_procedure_actual "Restricted tender=Beschränkte Ausschreibung"  or "Handover=Freihändige Vergabe" or "Free assignment=Freihändige Vergabe" is present.
# format_4)in tender_html_element after click on "Vergebene Aufträge >> Bauleistungen"=="Assigned Orders >> construction work" and if in type_of_procedure_actual "open procedure	=Offenes Verfahren" is present .

# note:in tender_html_element after click on "Vergebene Aufträge >> Architekten- und Ingenieurleistungen"=="Assigned Orders >> Architectural and engineering services" in this format currently no data is availabel. so at that point we keep it on hold.
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.script_name = 'de_deutsrent_ca'
    
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

#     formaat1 = if 'Verhandlungsvergabe ohne Teilnahmewettbewerb' in Format or "Restricted tender=Beschränkte Ausschreibung" in Format:
#     formaat2 = if 'Offenes Verfahren' in Format or "Verhandlungsverfahren ohne Teilnahmewettbewerb" in Format:
#     formaat3 = if 'Beschränkte Ausschreibung' in Format or "Handover=Freihändige Vergabe" in Format or "Free assignment=Freihändige Vergabe" in Format :
#     format4 = if 'Offenes Verfahren' in Format:
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
    # Onsite Comment -None
    try:
        notice_data.type_of_procedure_actual = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text
        type_of_procedure_actual = GoogleTranslator(source='de', target='en').translate(notice_data.type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("assets/de_deutsrent_ca_procedure.csv",type_of_procedure_actual)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
    except:
        pass

    try:
        notice_url = tender_html_element.get_attribute("data-href")
        notice_data.notice_url = "https://www.deutsche-rentenversicherung-bund.de/einkaufskoordination/NetServer/"+str(notice_url)
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#pagePublicationDetails > div').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -take this document_type_description for all format.

    try:
        notice_data.document_type_description = page_details.find_element(By.CSS_SELECTOR, 'div.col-lg-12 > h1').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"Vergabenummer:")]//following::td').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -1.use this selector for format-2 and format-4.

    try:
        dispatch_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Tag der Absendung dieser Bekanntmachung:")]//following::td').text
        dispatch_date = re.findall('\d+.\d+.\d{4}',dispatch_date)[0]
        notice_data.dispatch_date = datetime.strptime(dispatch_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in dispatch_date: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -1.use this selector for format-1.

    try:
        notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),"Art und Umfang der Leistung:")]//following::td[2]').text
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_summary_english)
    except:
        try:
            notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text()," Beschreibung der Beschaffung")]//following::td').text
            notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_summary_english)
        except:
            try:
                notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),"Auftragsgegenstand:")]//following::td[2]').text
                notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_summary_english)
            except Exception as e:
                logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
                pass

    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Art und Umfang der Leistung:")]//following::td[2]').text
    except:
        try:
            notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text()," Beschreibung der Beschaffung")]//following::td').text
        except:
            try:
                notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Auftragsgegenstand:")]//following::td[2]').text
            except Exception as e:
                logging.info("Exception in local_description: {}".format(type(e).__name__))
                pass
    # Onsite Field -None
    # Onsite Comment -1.use this selector for format-2 and format-4. 				2.split est_amount. eg., "Wert: 493.138,00 EUR" take only " 493.138,00"

    try:
        est_amount = page_details.find_element(By.XPATH, '//*[contains(text(),"Gesamtwert der Beschaffung")]//following::td').text.split("Wert: ")[1].split("EUR")[0]
        est_amount = re.sub("[^\d\.\,]","",est_amount)
        notice_data.est_amount =float(est_amount.replace('.','').replace(',','.').strip())
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -1.use this selector for format-2 and format-4. 				2.split est_amount. eg., "Wert: 493.138,00 EUR" take only " 493.138,00"

    try:
        notice_data.grossbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -1.for format-2 only and format-4 			2.Replace follwing keywords with given respective kywords ('Dienstleistungen =Service'),('Bauauftrag=works'),('Lieferauftrag=Supply')

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
    
# Onsite Field -None
# Onsite Comment -None
    try:
        tender_criteria_data = tender_criteria()

        tender_criteria_data.tender_criteria_title = page_details.find_element(By.XPATH, '//*[contains(text()," Zuschlagskriterien")]//following::td').text

        tender_criteria_data.tender_criteria_cleanup()
        notice_data.tender_criteria.append(tender_criteria_data)
    except Exception as e:
        logging.info("Exception in tender_criteria_title: {}".format(type(e).__name__))
        pass

    
# Onsite Field -None
# Onsite Comment -None

    try:              
        cpvs_data = cpvs()
    # Onsite Field -None
    # Onsite Comment -1.use this xpath for format-2 and format-4 				2.eg., "45421100-5" here take only "45421100" in cpv_code.
        cpvs_data.cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"CPV-Code Hauptteil")]//following::td').text.split("-")[0]
        cpvs_data.cpvs_cleanup()
        notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:
        customer_details_data = customer_details()
        customer_details_data.org_country = 'DE'
        customer_details_data.org_language = 'DE'
        # Onsite Field -Vergabestelle
        # Onsite Comment -1.take org_name for all formats
        try:
            customer_details_data.org_name = org_name
        except Exception as e:
            logging.info("Exception in org_name: {}".format(type(e).__name__))
            pass

    # Onsite Field -None
    # Onsite Comment -1.use this xpath for format-1 only and format-3

        try:
            customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Anschrift:")]//following::td').text
        except:
    # Onsite Field -None
    # Onsite Comment -1.use this selector for format-2 and format-4. 				2.split org_address between "Postanschrift:" and "Postleitzahl / Ort:"
            try:
                customer_details_data.org_address = page_details.find_element(By.CSS_SELECTOR, 'div:nth-child(2) > table > tbody > tr:nth-child(3) > td:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass

    # Onsite Field -Telefonnummer:
    # Onsite Comment -1.use this xpath for format-1 only and format-3

        try:
            customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Telefonnummer:")]//following::td').text
        except:
        # Onsite Field -Telefon:
        # Onsite Comment -1.use this selector for format-2 only and format-4 				2.split org_phone between "Telefon: " and "E-Mail:".
            try:
                customer_details_data.org_phone = page_details.find_element(By.CSS_SELECTOR, 'div:nth-child(2) > table > tbody > tr:nth-child(3) > td:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass

    # Onsite Field -Faxnummer:
    # Onsite Comment -1.use this xpath for format-1 only and format-3

        try:
            customer_details_data.org_fax = page_details.find_element(By.XPATH, '//*[contains(text(),"Faxnummer:")]//following::td').text
        except:
    # Onsite Field -Fax:
    # Onsite Comment -1.use this selector for format-2 only and format-4 				2.split org_fax after "Fax:".
            try:
                customer_details_data.org_fax = page_details.find_element(By.CSS_SELECTOR, 'div:nth-child(2) > table > tbody > tr:nth-child(3) > td:nth-child(2)').text.split("Fax:")[1].split("\n")[0].strip()
            except Exception as e:
                logging.info("Exception in org_fax: {}".format(type(e).__name__))
                pass

    # Onsite Field -E-Mail:
    # Onsite Comment -1.use this xpath for format-1 only and format-3

        try:
            customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"E-Mail:")]//following::td').text.strip()
        except:
    # Onsite Field -E-Mail:
    # Onsite Comment -1.use this selector for format-1 only and format-3 				2.split org_email between "E-Mail:" and "Fax:".
            try:
                customer_details_data.org_email = page_details.find_element(By.CSS_SELECTOR, 'div:nth-child(2) > table > tbody > tr:nth-child(3) > td:nth-child(2)').text.split("E-Mail:")[1].split("Fax:")[0].strip()
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass

    # Onsite Field -None
    # Onsite Comment -1.use this selector for format-2 only and format-4 				2.split customer_nuts between "NUTS-Code: " and "Kontaktstelle".

        try:
            customer_details_data.customer_nuts = page_details.find_element(By.XPATH, '//*[contains(text(),"I.1) Name and addresses")]//following::td[1]').text.split("NUTS-Code:")[1].split("\n")[0].strip()
        except:
            try:
                customer_details_data.customer_nuts = page_details.find_element(By.XPATH, '//*[contains(text(),"I.1) Name und Adressen")]//following::td[1]').text.split("NUTS-Code:")[1].split("\n")[0].strip()
            except Exception as e:
                logging.info("Exception in customer_nuts: {}".format(type(e).__name__))
                pass

    # Onsite Field -None
    # Onsite Comment -1.use this xpath for format-1 only and format-3

        try:
            customer_details_data.org_website = page_details.find_element(By.XPATH, '//*[contains(text(),"Internet:")]//following::td').text
        except:
    # Onsite Field -None
    # Onsite Comment -1.use this xpath for format-2 only and format-4 				2.split org_website after "Hauptadresse: (URL)".
            try:
                customer_details_data.org_website = page_details.find_element(By.XPATH, '//*[contains(text(),"Hauptadresse: (URL)")]//following::a').text
            except Exception as e:
                logging.info("Exception in org_website: {}".format(type(e).__name__))
                pass

        # Onsite Field -None
        # Onsite Comment -1.use this xpath for format-1 only and format-3 				2.take postal_code from in last line. take only number.don't grab city_name.

        try:
            customer_details_data.postal_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Anschrift:")]//following::td').text.split(" ")[0]
        except:
    # Onsite Field -None
    # Onsite Comment -1.use this selector for format-2 only and format-4 				2.split postal_code between "Postleitzahl / Ort: " and "Land". 				3.take only number in postal_code .don't grab city_name.
            try:
                customer_details_data.postal_code = page_details.find_element(By.CSS_SELECTOR, 'div:nth-child(2) > table > tbody > tr:nth-child(3) > td:nth-child(2)').text.split("Postleitzahl / Ort:")[1].split(" ")[0]
            except Exception as e:
                logging.info("Exception in postal_code: {}".format(type(e).__name__))
                pass

        # Onsite Field -None
        # Onsite Comment -1.use this selector for format-1 only and format-3 				2.split org_city between "Postleitzahl / Ort: " and "Land". 				3.take only name.don't grab number i.e postal_code.

        try:
            customer_details_data.org_city = page_details.find_element(By.CSS_SELECTOR, 'div:nth-child(2) > table > tbody > tr:nth-child(3) > td:nth-child(2)').text.split("Postleitzahl / Ort: ")[1].split(" ")[1]
        except:
    # Onsite Field -None
    # Onsite Comment -1.use this xpath for format-2 only and format-4 				2.take only city_name.don't grab number.
            try:
                customer_details_data.org_city = page_details.find_element(By.XPATH, '//*[contains(text(),"Ort der Ausführung:")]//following::td[2]').text
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except:
        pass
 
    
    try: 
        funding_agency = page_details.find_element(By.XPATH, '//*[contains(text(),"II.2.13) Angaben zu Mitteln der Europäischen Union")]//following::td[1]').text
        if 'Nein' in funding_agency:
            pass
        else:
            funding_agencies_data = funding_agencies()
            funding_agencies_data.funding_agency='European Agency (internal id: 1344862)'
            funding_agencies_data.funding_agencies_cleanup()
            notice_data.funding_agencies.append(funding_agencies_data)
    except Exception as e:
        logging.info("Exception in funding_agencies: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:
        lot_number = 1
        lot_details_data = lot_details()
        lots = page_details.find_element(By.CSS_SELECTOR, '#pagePublicationDetails > div').text.split('II.2) Beschreibung')
        for lot in lots:
            if "Los-Nr:" in lot and 'Beschreibung der Beschaffung' in lot:
                lot_details_data = lot_details()
                lot_details_data.lot_number = lot_number
    # #         # Onsite Field -Bezeichnung     div:nth-child(2) > fieldset
    # #         # Onsite Comment -take lot_title only when the field name "Bezeichnung" is available  if it is not available pass the local_title in lot_title

                lot_title = lot.split('Bezeichnung des Auftrags:')[1].split('\n')[0]
                lot_details_data.lot_title = GoogleTranslator(source='auto', target='en').translate(lot_title)
                try:
                    lot_description = lot.split('Beschreibung der Beschaffung')[1].split('\n')[0]
                    lot_details_data.lot_description = GoogleTranslator(source='auto', target='en').translate(lot_description)
                except:
                    pass
                    
                try:
                    contract_start_date = lot.split('Beginn:')[1].split('Ende:')[0]
                    contract_start_date = re.findall('\d+.\d+.\d{4}',contract_start_date)[0]
                    lot_details_data.contract_start_date = datetime.strptime(contract_start_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
                except:
                    try:
                        contract_start_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Lieferung/Ausführung ab:")]//following::td').text
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
                        contract_end_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Lieferung/Ausführung bis:")]//following::td').text
                        contract_end_date = re.findall('\d+.\d+.\d{4}',contract_end_date)[0]
                        lot_details_data.contract_end_date = datetime.strptime(contract_end_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
                    except:
                        pass     
                    
                try:
                    lot_details_data.contract_type = notice_data.notice_contract_type
                except Exception as e:
                    logging.info("Exception in contract_type: {}".format(type(e).__name__))
                    pass
                
                try:
                    lot_details_data.lot_nuts = page_details.find_element(By.XPATH, '//*[contains(text(),"NUTS-Code:")]//following::td').text.replace('\n',',')
                except Exception as e:
                    logging.info("Exception in lot_nuts: {}".format(type(e).__name__))
                    pass

#         # Onsite Field -None
#         # Onsite Comment -1.use this xpath for format-4. 						2.split contract_end_date between "Ende: "  and "Dieser Auftrag kann verlängert werden:"
                try:
                    lot_cpvs_data = lot_cpvs()
                    lot_cpvs_data.lot_cpv_code=lot.split('CPV-Code Hauptteil:')[1].split('-')[0].strip()
                    lot_cpvs_data.lot_cpvs_cleanup()
                    lot_details_data.lot_cpvs.append(lot_cpvs_data)
                except Exception as e:
                    logging.info("Exception in lot_cpvs: {}".format(type(e).__name__))
                    pass
                


#         # Onsite Field -None
#         # Onsite Comment -None

                try:
                    lot_criteria_data = lot_criteria()
                        # Onsite Field -None
                        # Onsite Comment -1.use this xpath for format-2. 							2.if the multiple lots avaialbel on page than take each records  							3.take  this url for example "https://www.deutsche-rentenversicherung-bund.de/einkaufskoordination/NetServer/PublicationControllerServlet?function=Detail&TOID=54321-NetTender-18899e1246b-fb48eda1dd2818a&Category=InvitationToTender"
                    lot_criteria_data.lot_criteria_title = lot.split(' Zuschlagskriterien')[1].split('\n')[0].strip()
                    lot_criteria_data.lot_criteria_cleanup()
                    lot_details_data.lot_criteria.append(lot_criteria_data)
                except Exception as e:
                    logging.info("Exception in lot_criteria: {}".format(type(e).__name__))
                    pass
                
                lot_criteria_data.lot_criteria_cleanup()

                lot_criteria_data.lot_criteria.append(lot_criteria_data)                
            else:
                lot_details_data.lot_title = notice_data.notice_title
                notice_data.is_lot_default = True
                lot_details_data.lot_description = notice_data.notice_title
                lot_details_data.lot_number = 1
                
        try:
            award_details_data = award_details()
            # Onsite Field -None
            # Onsite Comment -1.use this xpath for format-1 and format-3 					2.take only first line in bidder_name.
            try:
                award_details_data.bidder_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Auftragnehmer:")]//following::td').text.split("\n")[0].strip()
            except:
                try:
                    award_details_data.bidder_name = page_details.find_element(By.XPATH, '//*[contains(text(),"V.2.3) Name und Anschrift des Wirtschaftsteilnehmers, zu dessen Gunsten der Zuschlag erteilt wurde")]//following::td').text.split("Offizielle Bezeichnung:")[1].split("\n")[0].strip()
                except:
                   award_details_data.bidder_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Anschrift des Auftragnehmers/Konzessionärs")]//following::td').text.split("Offizielle Bezeichnung:")[1].split("\n")[0].strip()
                    

            # Onsite Field -None
            # Onsite Comment -1.use this xpath for format-2 and format-4 					2.take only name in this field.


            # Onsite Field -None
            # Onsite Comment -1.use this xpath for format-1 and format-3
            try:
                award_details_data.address = page_details.find_element(By.XPATH, '//*[contains(text(),"Auftragnehmer:")]//following::td').text
            except:
                try:
                    award_details_data.address = page_details.find_element(By.XPATH, '//*[contains(text(),"V.2.3) Name und Anschrift des Wirtschaftsteilnehmers, zu dessen Gunsten der Zuschlag erteilt wurde")]//following::td').text.split("Postanschrift:")[1].split("Postleitzahl / Ort:")[0]
                except:
                    pass
            

            # Onsite Field -None
            # Onsite Comment -1.use this xpath for format-2 and format-4 					2.split address between "Postanschrift:" and "Postleitzahl / Ort:"

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
page_details = fn.init_chrome_driver(arguments) 
page_main = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.deutsche-rentenversicherung-bund.de/einkaufskoordination/NetServer/PublicationSearchControllerServlet?function=SearchPublications&Gesetzesgrundlage=VOL&Category=ContractAward&thContext=awardPublications","https://www.deutsche-rentenversicherung-bund.de/einkaufskoordination/NetServer/PublicationSearchControllerServlet?function=SearchPublications&Gesetzesgrundlage=VOB&Category=ContractAward&thContext=awardPublications"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(2,4):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/div/div[2]/div/div/div/div[2]/table[1]/tbody/tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div/div[2]/div/div/div/div[2]/table[1]/tbody/tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div/div[2]/div/div/div/div[2]/table[1]/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/div/div[2]/div/div/div/div[2]/table[1]/tbody/tr'),page_check))
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
