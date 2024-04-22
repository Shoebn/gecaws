from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "de_pregoprhos_ca"
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
SCRIPT_NAME = "de_pregoprhos_ca"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

# after opening url click on "Vergebene Aufträge=Assigned Orders" >> "Alle vergebenen Aufträge=All orders placed"
# format-1)if in type_of_procedure_actual "restricted tender=Beschränkte Ausschreibung" or "free hand allocation=Freihändige Vergabe" or "negotiated award without participation competition=Verhandlungsvergabe ohne Teilnahmewettbewerb" is present.
# format-2)if in type_of_procedure_actual "open procedure=Offenes Verfahren" is present.

    notice_data.script_name = 'de_pregoprhos_ca'
    notice_data.main_language = 'DE'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'DE'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'EUR'
    notice_data.procurement_method = 2
    notice_data.notice_type = 7
    
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
    # Onsite Comment -split type_of_procedure_actual. here "VOB, Beschränkte Ausschreibung" take only "Beschränkte Ausschreibung".

    try:
        notice_data.type_of_procedure_actual = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text.split(',')[1].strip()
        notice_data.type_of_procedure = fn.procedure_mapping("assets/de_pregoprhos_ca_procedure.csv",notice_data.type_of_procedure_actual)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Ausschreibung
    # Onsite Comment -split notice_no .eg., "Umgestaltung Freianlage/Schullandheim Oberthal (0003/23)" here take only "0003/23" in notice_no.

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text.split('(')[1].split(')')[0].strip()
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -click on the tr

    try:
        notice_url = tender_html_element.get_attribute("data-oid")
        notice_data.notice_url = 'https://prego-vergabeplattform.prhos.com/NetServer/PublicationControllerServlet?function=Detail&TOID='+notice_url+'&Category=ContractAward'
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url

    try:
        notice_data.notice_text += page_details.find_element(By.XPATH, '//*[@id="pagePublicationDetails"]/div').get_attribute("outerHTML")                     
    except:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass

    try:
        document_type_description = page_details.find_element(By.XPATH, '//*[@id="printarea"]/div[1]/h1').text.strip()
        notice_data.document_type_description = GoogleTranslator(source='auto', target='en').translate(document_type_description)
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -1.if not availabel then take local_title in notice_summary_english.    2.use this selector for format-1.

    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Auftragsgegenstand:")]//following::tr[2]').text
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
    except:
        try:
            notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"II.1.4) Kurze Beschreibung:")]//following::td').text
            notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
        except:
            try:
                notice_data.notice_summary_english = notice_data.notice_title
                notice_data.local_description = notice_data.local_title
            except Exception as e:
                logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
                pass

    # Onsite Field -None
    # Onsite Comment -1.for format-2. 	2.Replace follwing keywords with given respective kywords ('Dienstleistungen =Service'),('Bauauftrag=works'),('Lieferauftrag=Supply')

    try:
        notice_contract_type = page_details.find_element(By.XPATH, '//*[contains(text()," Art des Auftrags")]//following::td').text
        if 'Dienstleistungen' in notice_contract_type:
            notice_data.notice_contract_type =  'Service'
        elif 'Bauauftrag' in notice_contract_type:
            notice_data.notice_contract_type = 'Works'
        elif 'Lieferauftrag' in notice_contract_type:
            notice_data.notice_contract_type = 'Supply'
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass


    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'DE'
        customer_details_data.org_language = 'DE'
    # Onsite Field -Vergabestelle
    # Onsite Comment -None

        try:
            customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        except Exception as e:
            logging.info("Exception in org_name: {}".format(type(e).__name__))
            pass

    # Onsite Field -None
    # Onsite Comment -1.use this xpath for format-1.

        try:
            customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Anschrift:")]//following::td').text
        except:
            try:
                customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"I.1) Name und Adressen")]//following::td').text.split('Postanschrift:')[1].split('NUTS-Code:')[0].strip()
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass

    # Onsite Field -None
    # Onsite Comment -1.use this xpath for format-1.

        try:
            customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Telefonnummer:")]//following::td').text
        except:
            try:
                customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"I.1) Name und Adressen")]//following::td').text.split('Telefon:')[1].split('\n')[0].strip()
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass

    # Onsite Field -None
    # Onsite Comment -1.use this xpath for format-1.

        try:
            customer_details_data.org_fax = page_details.find_element(By.XPATH, '//*[contains(text(),"Faxnummer:")]//following::td').text
        except:
            try:
                customer_details_data.org_fax = page_details.find_element(By.XPATH, '//*[contains(text(),"I.1) Name und Adressen")]//following::td').text.split('Fax:')[1].split('\n')[0].strip()
            except Exception as e:
                logging.info("Exception in org_fax: {}".format(type(e).__name__))
                pass


    # Onsite Field -None
    # Onsite Comment -1.use this xpath for format-1.

        try:
            customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"E-Mail:")]//following::td').text
        except:
            try:
                customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"I.1) Name und Adressen")]//following::td').text.split('E-Mail:')[1].split('\n')[0].strip()
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass

    # Onsite Field -None
    # Onsite Comment -1.use this selector for format-2. 	 2.split customer_nuts between "NUTS-Code:" and "Kontaktstelle(n):".

        try:
            customer_details_data.customer_nuts = page_details.find_element(By.XPATH, '//*[contains(text(),"I.1) Name und Adressen")]//following::td').text.split('NUTS-Code:')[1].split('\n')[0].strip()
        except Exception as e:
            logging.info("Exception in customer_nuts: {}".format(type(e).__name__))
            pass

    # Onsite Field -None
    # Onsite Comment -1.use this xpath for format-2.          2.split org_website after "Hauptadresse: (URL)".

        try:
            customer_details_data.org_website = page_details.find_element(By.XPATH, '//*[contains(text(),"Hauptadresse: (URL)")]//following::a').text
        except Exception as e:
            logging.info("Exception in org_website: {}".format(type(e).__name__))
            pass
        
    # Onsite Field -None
    # Onsite Comment -1.use this xpath for format-1.    2.postal_code take from last line. eg.,"66119 Saarbrücken" take only "66119" in postal_code.

        try:
            postal_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Anschrift:")]//following::td').text
            postal_code = re.findall('\d{5}',postal_code)[0]
            customer_details_data.postal_code = postal_code
        except:
            try:
                postal_code = page_details.find_element(By.XPATH, '//*[contains(text(),"I.1) Name und Adressen")]//following::td').text
                postal_code = re.findall('\d{5}',postal_code)[0]
                customer_details_data.postal_code = postal_code
            except Exception as e:
                logging.info("Exception in postal_code: {}".format(type(e).__name__))
                pass

    # Onsite Field -None
    # Onsite Comment -1.use this xpath for format-1.     2.org_city take from last line. eg.,"66119 Saarbrücken" take only "Saarbrücken" in org_city
        try:
            org_city = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Anschrift:")]//following::td').text.split('\n')
            org_city = org_city[-1].strip()
            customer_details_data.org_city = re.sub("[\d{5}\s]", "",org_city)
        except:
            try:
                org_city = page_details.find_element(By.XPATH, '//*[contains(text(),"I.1) Name und Adressen")]//following::td').text.split('Postleitzahl / Ort:')[1].split('Land')[0].strip()
                customer_details_data.org_city = re.sub("[\d{5}\s]", "",org_city)
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass

    # Onsite Field -None
    # Onsite Comment -1.use this xpath for format-2. 2.split contact_person between "Kontaktstelle(n):" and "Telefon:"

        try:
            customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"I.1) Name und Adressen")]//following::td').text.split('Kontaktstelle(n):')[1].split('\n')[0].strip()
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass
        
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -None  # //*[contains(text(),"II.2.1) Bezeichnung des Auftrags:")]//following::td[1]

    try:
        lot_number = 1   
        lots = page_details.find_element(By.CSS_SELECTOR, '#pagePublicationDetails > div').text.split('II.2) Beschreibung')
        for lot in lots[1:]:
            lot_details_data = lot_details()
            if 'Los-Nr' in lot:

                try:
                    lot_title = lot.split('II.2.1) Bezeichnung des Auftrags:')[1].split('\n')[0].strip()
                    lot_details_data.lot_title = GoogleTranslator(source='auto', target='en').translate(lot_title)
                    lot_details_data.lot_actual_number = lot.split('II.2.1) Bezeichnung des Auftrags:')[1].split('\n')[1].split('\n')[0].strip()
                except:
                    lot_details_data.lot_title = notice_data.notice_title
                    notice_data.is_lot_default = True
                    
            # Onsite Field -None
            # Onsite Comment -1.use this xpath for format-1.     2.if not availabel then take local_title in lot_description.

                try:
                    lot_details_data.lot_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Auftragsgegenstand:")]//following::tr[2]').text
                except:
                    lot_details_data.lot_description = notice_data.notice_title
                    
                # Onsite Field -None
                # Onsite Comment -1.for format-2. 	2.Replace follwing keywords with given respective kywords ('Dienstleistungen =Service'),('Bauauftrag=works'),('Lieferauftrag=Supply')

                try:
                    lot_details_data.contract_type = notice_data.notice_contract_type
                except Exception as e:
                    logging.info("Exception in contract_type: {}".format(type(e).__name__))
                    pass
                
                # Onsite Field -None
                # Onsite Comment -1.use this xpath for format-2. 	2.take all nuts seperatly for each lot.

                try:
                    lot_details_data.lot_nuts = page_details.find_element(By.XPATH, '//*[contains(text(),"NUTS-Code:")]//following::td').text
                except Exception as e:
                    logging.info("Exception in lot_nuts: {}".format(type(e).__name__))
                    pass

                try:
                    lot_cpvs_data = lot_cpvs()

                    # Onsite Field -None
                    # Onsite Comment -1.use this xpath for format-2. 				2.eg.,"CPV-Code Hauptteil: 77211500-7" here lot_cpvs_code split after "CPV-Code Hauptteil:". and also in lot_cpvs_code "77211500".  				3.grab only if possible. use this url for referencs "https://prego-vergabeplattform.prhos.com/NetServer/PublicationControllerServlet?function=Detail&TOID=54321-NetTender-188429b7a03-48d55993cf5d1f5c&Category=ContractAward"

                    lot_cpvs_data.lot_cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"II.2.2) Weitere(r) CPV-Code(s)")]//following::td').text.split('CPV-Code Hauptteil:')[1].split('-')[0].strip()

                    lot_cpvs_data.lot_cpvs_cleanup()
                    lot_details_data.lot_cpvs.append(lot_cpvs_data)
                except Exception as e:
                    logging.info("Exception in lot_cpvs: {}".format(type(e).__name__))
                    pass

                try:
                    lot_criteria_data = lot_criteria()

                    # Onsite Field -None
                    # Onsite Comment -1.use this xpath for format-2.		2.split lot_criteria_title. eg., "Name: Preis (40%), Gewichtung: 40,00" here take only "Preis" in lot_criteria_title.

                    lot_criteria_data.lot_criteria_title = page_details.find_element(By.XPATH, '//*[contains(text(),"Zuschlagskriterien")]//following::td').text.split('Name:')[1].split('(')[0].strip()
                    # Onsite Field -None
                    # Onsite Comment -1.use this xpath for format-2.		2.split lot_criteria_weight. eg., "Name: Preis (40%), Gewichtung: 40,00" here take only "40%" in lot_criteria_weight.

                    lot_criteria_weight = page_details.find_element(By.XPATH, '//*[contains(text(),"Zuschlagskriterien")]//following::td').text.split('(')[1].split('%)')[0].strip()
                    lot_criteria_data.lot_criteria_weight = int(lot_criteria_weight)

                    lot_criteria_data.lot_criteria_cleanup()
                    lot_details_data.lot_criteria.append(lot_criteria_data)
                except Exception as e:
                    logging.info("Exception in lot_criteria: {}".format(type(e).__name__))
                    pass

                try:
                    award_details_data = award_details()
                    # Onsite Field -None
                    # Onsite Comment -1.take only first line in bidder_name.
                    try:
                        award_details_data.bidder_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Auftragnehmer")]//following::td').text.split('\n')[0]
                    except:
                        try:
                            award_details_data.bidder_name = page_details.find_element(By.XPATH, '//*[contains(text(),"V.2.3) Name und Anschrift des Wirtschaftsteilnehmers, zu dessen Gunsten der Zuschlag erteilt wurde")]//following::td').text.split('Offizielle Bezeichnung:')[1].split('\n')[0].strip()
                            # Onsite Field -None
                            # Onsite Comment -1.use this xpath for format-1.
                        except:
                            award_details_data.bidder_name = page_details.find_element(By.XPATH, '//*[contains(text(),"1. Auftragnehmer:")]//following::td').text.split('\n')[0]
                            
                    try:
                        award_details_data.address = page_details.find_element(By.XPATH, '//*[contains(text(),"1. Auftragnehmer")]//following::td').text
                    except:
                        try:
                            award_details_data.address = page_details.find_element(By.XPATH, '//*[contains(text(),"V.2.3) Name und Anschrift des Wirtschaftsteilnehmers, zu dessen Gunsten der Zuschlag erteilt wurde")]//following::td').text.split('Postanschrift:')[1].split('NUTS-Code')[0].strip()
                        # Onsite Field -None
                        # Onsite Comment -1.use this xpath for format-2. 	2.split bidder_name before "Postanschrift:".
                        except:
                            pass

                    award_details_data.award_details_cleanup()
                    lot_details_data.award_details.append(award_details_data)
                except Exception as e:
                    logging.info("Exception in award_details: {}".format(type(e).__name__))
                    pass
            else:
                lot_details_data.lot_title = notice_data.notice_title
                notice_data.is_lot_default = True
                try:
                    award_details_data = award_details()
                    try:
                        award_details_data.bidder_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Auftragnehmer")]//following::td').text.split('\n')[0]
                    except:
                        try:
                            award_details_data.bidder_name = page_details.find_element(By.XPATH, '//*[contains(text(),"V.2.3) Name und Anschrift des Wirtschaftsteilnehmers, zu dessen Gunsten der Zuschlag erteilt wurde")]//following::td').text.split('Offizielle Bezeichnung:')[1].split('\n')[0].strip()
                            # Onsite Field -None
                            # Onsite Comment -1.use this xpath for format-1.
                        except:
                            award_details_data.bidder_name = page_details.find_element(By.XPATH, '//*[contains(text(),"1. Auftragnehmer:")]//following::td').text.split('\n')[0]
                            
                    try:
                        award_details_data.address = page_details.find_element(By.XPATH, '//*[contains(text(),"1. Auftragnehmer")]//following::td').text
                    except:
                        try:
                            award_details_data.address = page_details.find_element(By.XPATH, '//*[contains(text(),"V.2.3) Name und Anschrift des Wirtschaftsteilnehmers, zu dessen Gunsten der Zuschlag erteilt wurde")]//following::td').text.split('Postanschrift:')[1].split('NUTS-Code')[0].strip()
                        # Onsite Field -None
                        # Onsite Comment -1.use this xpath for format-2. 	2.split bidder_name before "Postanschrift:".
                        except:
                            pass

                    award_details_data.award_details_cleanup()
                    lot_details_data.award_details.append(award_details_data)
                except Exception as e:
                    logging.info("Exception in award_details: {}".format(type(e).__name__))
                    pass
            if lot_details_data.lot_title is not None:
                lot_details_data.lot_number = lot_number
                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
                lot_number += 1
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass

    try:              
        cpvs_data = cpvs()
    # Onsite Field -None
    # Onsite Comment -1.use this xpath for format-2. 2.eg., "34144210-3" here take only "34144210" in cpv_code.

        cpvs_data.cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"CPV-Code Hauptteil")]//following::td').text.split('-')[0].strip()

        cpvs_data.cpvs_cleanup()
        notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass

    # Onsite Field -None
    # Onsite Comment -1.use this xpath for format-2. 2.if in below text written as " financed by European Union funds: No  " than pass the "None " in field name "funding_agency" "II.2.13) Information on European Union funds  >  The contract is related to a project and/or program financed by EU funds: no  " if the abve  text written as " financed by European Union funds: YES  " than pass the "Funding agency" name as "European Agency (internal id: 1344862) " in field name "T.FUNDING_AGENCIES::TEXT"
    try:
        funding_agencies_data.funding_agency = page_details.find_element(By.XPATH, '//*[contains(text(),"II.2.13) Angaben zu Mitteln der Europäischen Union")]//following::td').text
        funding_agency = GoogleTranslator(source='auto', target='en').translate(funding_agency)
        if 'yes' in funding_agency or 'YES' in funding_agency or 'Yes' in funding_agency:
            funding_agencies_data = funding_agencies()
            funding_agencies_data.funding_agency = 1344862
            funding_agencies_data.funding_agencies_cleanup()
            notice_data.funding_agencies.append(funding_agencies_data)
        else:
            pass
    except Exception as e:
        logging.info("Exception in funding_agency: {}".format(type(e).__name__))
        pass

    try:
        dispatch_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Tag der Absendung dieser Bekanntmachung:")]//following::td').text
        dispatch_date = re.findall('\d+.\d+.\d{4}',dispatch_date)[0]
        notice_data.dispatch_date = datetime.strptime(dispatch_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in dispatch_date: {}".format(type(e).__name__))
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
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://prego-vergabeplattform.prhos.com/NetServer/PublicationSearchControllerServlet?function=SearchPublications&Gesetzesgrundlage=All&Category=ContractAward&thContext=awardPublications"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)

        try:
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/div[2]/div/div/div/div[2]/table[1]/tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/div[2]/div/div/div/div[2]/table[1]/tbody/tr')))[records]
                extract_and_save_notice(tender_html_element)
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
    page_details.quit() 
    output_json_file.copyFinalJSONToServer(output_json_folder)
