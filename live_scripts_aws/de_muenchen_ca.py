from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "de_muenchen_ca"
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
from selenium.webdriver.support.ui import Select

#check comments for additional changes
#1)for bidder name
# As discussed with shoeib added below condition .. (1) if lot avaialble than condition 
# lot_title ="blank "and award_details ="blank" []
# than lot_details =[]
# (2) if lots not avaible than
# award_details= []
# and lot_details= []

# format 1)open procedure=Offenes Verfahren
# format 2)restricted tender=Beschränkte Ausschreibung,Negotiated award without participation competition=Verhandlungsvergabe ohne Teilnahmewettbewerb,Free contract award=Freihändige Vergabe
# format 3)Order changes during the EU contract term (so-called supplementary procedure)=Auftragsänderungen während der Vertragslaufzeit EU (sog. Nachtragsverfahren)

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "de_muenchen_ca"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'de_muenchen_ca'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'DE'
    notice_data.performance_country.append(performance_country_data)
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'DE'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'EUR'
    
    notice_data.main_language = 'DE'
        
    notice_data.notice_type = 7
    
    if i == 0 or i == 2:
        notice_data.procurement_method = 1
    else:
        notice_data.procurement_method = 0
    
    
    # Onsite Field -Ausschreibung
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td.tender').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Verfahrensart
    # Onsite Comment -None

    try:
        notice_data.type_of_procedure_actual = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text.strip()
        type_of_procedure_actual = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("assets/de_muenchen_ca_procedure.csv",type_of_procedure_actual)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
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
    
    # Onsite Field -None
    # Onsite Comment -Note:Click on "<tr>tag"
    notice_url1 = tender_html_element.get_attribute("data-oid")
    notice_url2 = tender_html_element.get_attribute("data-category")

    try:
        notice_data.notice_url = "https://vergabe.muenchen.de/NetServer/PublicationControllerServlet?function=Detail&TOID="+notice_url1+"&Category="+notice_url2                    
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    try:
        notice_no = notice_data.notice_url
        notice_data.notice_no = re.findall('\d{5}',notice_no)[0]
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'body > div.page').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
        
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Beschreibung")]//following::td[1]').text
    except:
        try:
            notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Art und Umfang der Leistung")]//following::td[1]').text
        except:
            try:
                notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Beschreibung der Beschaffung")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in local_description: {}".format(type(e).__name__))
                pass
    
    # Onsite Field -Verfahren >> Beschreibung
    # Onsite Comment -Note:Split local_description between "Beschreibung" and "Art des Auftrags"

    try:
        notice_summary_english = notice_data.local_description
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_summary_english)
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Verfahren >> Beschreibung
    # Onsite Comment -Note:Split notice_contract_type before "Art des Auftrags" 	        Note:Repleace following keywords with given keywords("Dienstleistungen=Service")

    try:
        notice_data.contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Beschreibung")]//following::td[1]').text.split("Art des Auftrags: ")[1]
        if 'Dienstleistungen' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Service'
        else:
            notice_data.contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Art des Auftrags")]//following::td[1]').text
            if 'Dienstleistungen' in notice_data.contract_type_actual:
                notice_data.notice_contract_type = 'Service'
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
        
    #     # Onsite Field -Beschaffungsinformationen (speziell) >> Geschätzte Laufzeit
#     # Onsite Comment -Note:Splite before "Beginn" and "Ende"

    try:
        tender_contract_start_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Geschätzte Laufzeit")]//following::td[1]').text.split("Beginn:")[1].split("Ende:")[0].strip()
        tender_contract_start_date = re.findall('\d+.\d+.\d{4}',tender_contract_start_date)[0]
        notice_data.tender_contract_start_date = datetime.strptime(tender_contract_start_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
    except:
        try:
            tender_contract_start_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Lieferung/Ausführung ab")]//following::td[1]').text
            tender_contract_start_date = re.findall('\d+.\d+.\d{4}',tender_contract_start_date)[0]
            notice_data.tender_contract_start_date = datetime.strptime(tender_contract_start_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
        except Exception as e:
            logging.info("Exception in tender_contract_start_date: {}".format(type(e).__name__))
            pass
    
    # Onsite Field -Beschaffungsinformationen (speziell) >> Geschätzte Laufzeit
    # Onsite Comment -Note:Splite after "Ende"
     # Onsite Field -Zeitraum der 	Leistungserbringung >> Lieferung/Ausführung ab
#     # Onsite Comment -None

    try:
        tender_contract_end_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Geschätzte Laufzeit")]//following::td[1]').text.split("Ende:")[1].strip()
        tender_contract_end_date = re.findall('\d+.\d+.\d{4}',tender_contract_end_date)[0]
        notice_data.tender_contract_end_date = datetime.strptime(tender_contract_end_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
    except:
        try:
            tender_contract_end_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Lieferung/Ausführung bis")]//following::td[1]').text
            tender_contract_end_date = re.findall('\d+.\d+.\d{4}',tender_contract_end_date)[0]
            notice_data.tender_contract_end_date = datetime.strptime(tender_contract_end_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
        except Exception as e:
            logging.info("Exception in tender_contract_start_date: {}".format(type(e).__name__))
            pass

# format 1
# ref_url=https://vergabe.muenchen.de/NetServer/PublicationControllerServlet?function=Detail&TOID=54321-

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'DE'
        customer_details_data.org_language = 'DE'
    # Onsite Field -Vertragspartei und Dienstleister >> Beschaffer >>Offizielle Bezeichnung
    # Onsite Comment -Note:Splite org_name after "Offizielle Bezeicung" and "Registrierungsnummer"

        try:
            customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Beschaffer")]//following::td[1]').text.split("Offizielle Bezeichnung: ")[1].split("Registrierungsnummer: ")[0].strip()
        except:
            try:
                customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Anschrift")]//following::td[1]').text.split("\n")[0]
            except:
                try:
                    customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Adressen")]//following::td[1]').text.split("Offizielle Bezeichnung")[1].split("Postanschrift")[0].strip()
                except Exception as e:
                    logging.info("Exception in org_name: {}".format(type(e).__name__))
                    pass

    # Onsite Field -Vertragspartei und Dienstleister >> Beschaffer
    # Onsite Comment -None

        try:
            customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Beschaffer")]//following::td[1]').text.split("Postanschrift:")[1].split("NUTS-3-Code:")[0].strip()
        except:
            try:
                customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Anschrift")]//following::td[1]').text
            except:
                try:
                    customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Adressen")]//following::td[1]').text
                except Exception as e:
                    logging.info("Exception in org_address: {}".format(type(e).__name__))
                    pass
           
    # Onsite Field -Vertragspartei und Dienstleister >> Beschaffer
    # Onsite Comment -Note:Split postal_code between	"Postleitzahl / Ort" and "NUTS-3-Code"

        try:
            customer_details_data.postal_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Beschaffer")]//following::td[1]').text.split("Postleitzahl / Ort:")[1].split("NUTS-3-Code:")[0].strip()
        except:
            try:
                customer_details_data.postal_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Adressen")]//following::td[1]').text.split("Postleitzahl / Ort:")[1].split("Land:")[0].strip()
            except Exception as e:
                logging.info("Exception in postal_code: {}".format(type(e).__name__))
                pass
        

    # Onsite Field -Vertragspartei und Dienstleister >> Beschaffer
    # Onsite Comment -Note:Split customer_nuts between "NUTS-3-Code" and "Land"

        try:
            customer_details_data.customer_nuts = page_details.find_element(By.XPATH, '//*[contains(text(),"Beschaffer")]//following::td[1]').text.split("NUTS-3-Code:")[1].split("Land: ")[0].strip()
        except:
            try:
                customer_details_data.customer_nuts = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Adressen")]//following::td[1]').text.split("NUTS-Code:")[1].split("E-Mail:")[0].strip()
            except Exception as e:
                logging.info("Exception in customer_nuts: {}".format(type(e).__name__))
                pass
         

    # Onsite Field -Vertragspartei und Dienstleister >> Beschaffer
    # Onsite Comment -Note:Split org_email between "E-Mail" and "Telefon"

        try:
            customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Beschaffer")]//following::td[1]').text.split("E-Mail: ")[1].split("Telefon:")[0].strip()
        except:
            try:
                customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"E-Mail")]//following::td[1]').text
            except:
                try:
                    customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Adressen")]//following::td[1]').text.split("E-Mail:")[1].split("Fax")[0].strip()
                except Exception as e:
                    logging.info("Exception in org_email: {}".format(type(e).__name__))
                    pass
             

    # Onsite Field -Vertragspartei und Dienstleister >> Beschaffer
    # Onsite Comment -Note:Split org_phone between "Telefon" and "Fax"

        try:
            customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Beschaffer")]//following::td[1]').text.split("Telefon:")[1].split("Fax:")[0].split("Art des öffentlichen Auftraggebers:")[0].strip()
        except:
            try:
                customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Telefonnummer")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass

    # Onsite Field -Vertragspartei und Dienstleister >> Beschaffer
    # Onsite Comment -Note:Split org_fax between "Fax" and "Art des öffentlichen Auftraggebers"

        try:
            customer_details_data.org_fax = page_details.find_element(By.XPATH, '//*[contains(text(),"Beschaffer")]//following::td[1]').text.split("Fax:")[1].split("Art des öffentlichen Auftraggebers:")[0].strip()
        except:
            try:
                org_fax = page_details.find_element(By.XPATH, '//*[contains(text(),"Faxnummer")]//following::td[1]').text
                customer_details_data.org_fax = re.findall('\+\d{2} \d+',org_fax)[0]
            except:
                try:
                    customer_details_data.org_fax = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Adressen")]//following::td[1]').text
                except Exception as e:
                    logging.info("Exception in org_fax: {}".format(type(e).__name__))
                    pass

   

    # Onsite Field -Vertragspartei und Dienstleister >> Beschaffer
    # Onsite Comment -Note:Split customer_main_activity between "Haupttätigkeiten des öffentlichen Auftraggebers" to "Profil des Erwerbers (URL)"

        try:
            customer_details_data.customer_main_activity = page_details.find_element(By.XPATH, '//*[contains(text(),"Beschaffer")]//following::td[1]').text.split("Haupttätigkeiten des öffentlichen Auftraggebers: ")[1].split("Profil des Erwerbers (URL):")[0].strip()
        except Exception as e:
            logging.info("Exception in customer_main_activity: {}".format(type(e).__name__))
            pass

    # Onsite Field -Beschaffungsinformationen (allgemein) >> Überprüfungsstelle
    # Onsite Comment -Note:Splite contact_person between "Offizielle Bezeichnung" and "Registrierungsnummer"

        try:
            customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Überprüfungsstelle")]//following::td[1]').text.split("Offizielle Bezeichnung:")[1].split("Registrierungsnummer: ")[0].strip()
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass


    # Onsite Field -Vertragspartei und Dienstleister >> Beschaffer
    # Onsite Comment -Note:Split between "Art des öffentlichen Auftraggebers" to "Haupttätigkeiten des öffentlichen Auftraggebers"

        try:
            customer_details_data.type_of_authority_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Beschaffer")]//following::td[1]').text.split("Art des öffentlichen Auftraggebers:")[1].split("Haupttätigkeiten des öffentlichen Auftraggebers:")[0].strip()
        except Exception as e:
            logging.info("Exception in type_of_authority_code: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Öffentlicher Auftraggeber (Vergabestelle) >> Internet
        # Onsite Comment -None

        try:
            customer_details_data.org_website = page_details.find_element(By.CSS_SELECTOR, 'tbody > tr:nth-child(7) > td:nth-child(2) > a').text
        except:
            try:
                customer_details_data.org_website = page_details.find_element(By.XPATH, '//*[contains(text(),"Beschaffer")]//following::td[1]').text.split("Internet-Adresse (URL):")[1].split("Postanschrift: ")[0].strip()
            except:
                try:
                    customer_details_data.org_website = page_details.find_element(By.CSS_SELECTOR, 'tbody > tr > td:nth-child(2) > a:nth-child(1)').text
                except Exception as e:
                    logging.info("Exception in org_website: {}".format(type(e).__name__))
                    pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    notice_data.class_at_source = 'CPV'
    
    try:              
    # Onsite Field -Verfahren >> CPV-Code Hauptteil
    # Onsite Comment -Note:Split before "CPV-Code Hauptteil"

        try:
            cpvs_data = cpvs()
            cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"CPV-Code Hauptteil")]').text
            cpvs_data.cpv_code = re.findall('\d{8}',cpv_code)[0]
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
        except Exception as e:
            logging.info("Exception in cpv_code: {}".format(type(e).__name__))
            pass

    # Onsite Field -Verfahren >> Weitere CPV-Code Hauptteile
    # Onsite Comment -Note:Split before "Weitere CPV-Code Hauptteile"

        try:
            cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Weitere CPV-Code Hauptteile")]').text
            cpvs_data.cpv_code = re.findall('\d{8}',cpv_code)[0]
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
        except Exception as e:
            logging.info("Exception in cpv_code: {}".format(type(e).__name__))
            pass
        
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
    
    try:
        try:
            cpv_at_source = ''
            cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"CPV-Code Hauptteil")]').text
            cpv_at_source += re.findall('\d{8}',cpv_code)[0]
            cpv_at_source += ','
            notice_data.cpv_at_source = cpv_at_source.rstrip(',')
        except Exception as e:
            logging.info("Exception in cpv_at_source: {}".format(type(e).__name__))
            pass

        try:
            cpv_at_source = ''
            cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Weitere CPV-Code Hauptteile")]').text
            cpv_at_source += re.findall('\d{8}',cpv_code)[0]
            cpv_at_source += ','
            notice_data.cpv_at_source = cpv_at_source.rstrip(',')
        except Exception as e:
            logging.info("Exception in cpv_at_source: {}".format(type(e).__name__))
            pass
    except Exception as e:
        logging.info("Exception in cpv_at_source: {}".format(type(e).__name__)) 
        pass


    criteria = page_details.find_element(By.CSS_SELECTOR, ' div:nth-child(4) > table > tbody').text
    if "Beschaffungsinformationen (speziell)" in criteria:

        try:              
            for single_record in page_details.find_elements(By.XPATH, '//*[contains(text(),"Zuschlagskriterien")]//following::td[1]'):
                tender_criteria_data = tender_criteria()
            # Onsite Field -Beschaffungsinformationen (speziell) >> Zuschlagskriterien
            # Onsite Comment -Note:Splite before "Gewichtung"

                tender_criteria_title = single_record.text.split("Gewichtung:")[0].strip()
                tender_criteria_data.tender_criteria_title = GoogleTranslator(source='de', target='en').translate(tender_criteria_title)
                    

            # Onsite Field -Beschaffungsinformationen (speziell) >> Zuschlagskriterien
            # Onsite Comment -Note:Splite after "Gewichtung"

                tender_criteria_weight = single_record.text.split("Gewichtung:")[1].strip()
                tender_criteria_weight = re.findall('\d+',tender_criteria_weight)[0]
                tender_criteria_data.tender_criteria_weight = int(tender_criteria_weight.replace('.','').replace(',','').strip())

                tender_criteria_data.tender_criteria_cleanup()
                notice_data.tender_criteria.append(tender_criteria_data)
        except Exception as e:
            logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
            pass
    else:
        pass
    
    try:
        funding_agency = page_details.find_element(By.XPATH, '//*[contains(text(),"Angaben zu Mitteln der Europäischen Union")]//following::td[1]').text
        funding_agency = GoogleTranslator(source='auto', target='en').translate(funding_agency)
        if 'yes' in funding_agency:
            funding_agencies_data = funding_agencies()
            funding_agencies_data.funding_agency = 1344862
            funding_agencies_data.funding_agencies_cleanup()
            notice_data.funding_agencies.append(funding_agencies_data)
    except Exception as e:
        logging.info("Exception in funding_agency: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Abschnitt IV: Verfahren >> Bekanntmachungsnummer im ABl
    # Onsite Comment -Note:Splite after "Bekanntmachungsnummer im ABl"

    try:
        notice_data.related_tender_id = page_details.find_element(By.XPATH, '//*[contains(text(),"Bekanntmachungsnummer im ABl")]').text
    except Exception as e:
        logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
        pass

    
# Onsite Field -None
# Onsite Comment -None
# ref_url:https://vergabe.muenchen.de/NetServer/PublicationControllerServlet?function=Detail&TOID=54321-NetTender-18738142dc0-2a8f6012f4bcc563&Category=ContractAward
    
    try:  
        lot_number = 1
        for single_record in page_details.find_elements(By.XPATH, '//*[@id="printarea"]/div[2]/div/table/tbody')[3:]:  
            lot = single_record.text
            if "Beschaffungsinformationen (Los " in lot:
                lot_details_data = lot_details()
                lot_details_data.lot_number = lot_number
                lot_details_data.lot_title = notice_data.local_title
                notice_data.is_lot_default = True
                lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
                # Onsite Field -Ausschreibung
                # Onsite Comment -None


                # Onsite Field -Abschnitt II: Gegenstand >> NUTS-Code
                # Onsite Comment -None

                try:
                    lot_details_data.lot_nuts = single_record.text.split("NUTS-3-Code:")[1].split("Land:")[0].strip()
                except Exception as e:
                    logging.info("Exception in lot_nuts: {}".format(type(e).__name__))
                    pass

            # Onsite Field -Abschnitt II: Gegenstand >> II.2.4) Beschreibung der Beschaffung
            # Onsite Comment -None

                try:
                    lot_details_data.lot_description = single_record.text.split("Beschreibung des Loses")[1].split("Umfang der Auftragsvergabe")[0].strip()
                    lot_details_data.lot_description_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_description)
                except Exception as e:
                    logging.info("Exception in lot_description: {}".format(type(e).__name__))
                    pass

            # Onsite Field -Abschnitt II: Gegenstand >> II.2.7) Laufzeit des Vertrags, der Rahmenvereinbarung, des dynamischen Beschaffungssystems oder der Konzession
            # Onsite Comment -Note:Splite before "Beginn" and "Ende"

                try:
                    contract_start_date = single_record.text.split("Beginn:")[1].split("Ende:")[0].strip()
                    contract_start_date = re.findall('\d+.\d+.\d{4}',contract_start_date)[0]
                    lot_details_data.contract_start_date = datetime.strptime(contract_start_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
                except Exception as e:
                    logging.info("Exception in contract_start_date: {}".format(type(e).__name__))
                    pass

    #             # Onsite Field -Abschnitt II: Gegenstand >> II.2.7) Laufzeit des Vertrags, der Rahmenvereinbarung, des dynamischen Beschaffungssystems oder der Konzession
    #             # Onsite Comment -Note:Splite after "Ende"

                try:
                    contract_end_date = single_record.text.split("Ende:")[1].split("Verlängerung des Vertrags")[0].strip()
                    contract_end_date = re.findall('\d+.\d+.\d{4}',contract_end_date)[0]
                    lot_details_data.contract_end_date = datetime.strptime(contract_end_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
                except Exception as e:
                    logging.info("Exception in contract_end_date: {}".format(type(e).__name__))
                    pass

                try:
                    lot_cpvs_data = lot_cpvs()

                    # Onsite Field -Abschnitt II: Gegenstand >> II.1.2) CPV-Code Hauptteil
                    # Onsite Comment -None

                    lot_cpv_code = single_record.find_element(By.XPATH, '//*[contains(text(),"CPV-Code Hauptteil")]').text
                    lot_cpvs_data.lot_cpv_code = re.findall('\d{8}',lot_cpv_code)[0]

                    lot_cpvs_data.lot_cpvs_cleanup()
                    lot_details_data.lot_cpvs.append(lot_cpvs_data)
                except Exception as e:
                    logging.info("Exception in lot_cpvs: {}".format(type(e).__name__))
                    pass
                
                try:
                    lot_cpv_at_source = ''
                    lot_cpv_at_source = single_record.find_element(By.XPATH, '//*[contains(text(),"CPV-Code Hauptteil")]').text
                    lot_cpv_at_source += re.findall('\d{8}',lot_cpv_at_source)[0]
                    lot_cpv_at_source += ','
                    lot_details_data.lot_cpv_at_source = lot_cpv_at_source.rstrip(',')
                except Exception as e:
                    logging.info("Exception in cpv_at_source: {}".format(type(e).__name__))
                    pass

                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
                lot_number += 1
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
    try:              
        lot_details_data = lot_details()
        # Onsite Field -Ausschreibung
        # Onsite Comment -None
        lot_details_data.lot_number = 1
        lot_details_data.lot_title = notice_data.local_title
        notice_data.is_lot_default = True
        lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)

        try:
            award_details_data = award_details()

            # Onsite Field -Ergebnis >> Bieter
            # Onsite Comment -Note:Splite before "Offizielle Bezeichnung" and "Registrierungsnummer (Umsatzsteuer-ID)"

            award_details_data.bidder_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Bieter")]//following::td[6]').text.split("Offizielle Bezeichnung:")[1].split("Registrierungsnummer (Umsatzsteuer-ID):")[0].strip()
            # Onsite Field -Ergebnis >> Bieter
            # Onsite Comment -Note:Splite before "Postanschrift" and "Der Auftragnehmer ist ein KMU"

            award_details_data.address = page_details.find_element(By.XPATH, '//*[contains(text(),"Bieter")]//following::td[6]').text.split("Postanschrift: ")[1].split("Der Auftragnehmer ist ein KMU:")[0].strip()
            # Onsite Field -Ergebnis >> Vertrag >> Datum des Vertragsabschlusses
            # Onsite Comment -Note:Splite before "Datum des Vertragsabschlusses"

            award_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Datum des Vertragsabschlusses")]').text
            award_date = re.findall('\d+.\d+.\d{4}',award_date)[0]
            award_details_data.award_date = datetime.strptime(award_date,'%d.%m.%Y').strftime('%Y/%m/%d')
            
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

    try:
        lot_details_data = lot_details()
        lot_details_data.lot_number = 1
        lot_details_data.lot_title = notice_data.local_title
        notice_data.is_lot_default = True
        lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)

        try:
            lot = page_details.find_element(By.CSS_SELECTOR, 'body > div.page').text
            if "Auftragnehmer:" in lot:
                award_details_data = award_details()

                # Onsite Field -beauftragtes Unternehmen >> Auftragnehmer
                # Onsite Comment -Note:Take only first line

                award_details_data.bidder_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Auftragnehmer")]//following::td[1]').text.split("\n")[0]

                # Onsite Field -beauftragtes Unternehmen >> Auftragnehmer
                # Onsite Comment -None

                award_details_data.address = page_details.find_element(By.XPATH, '//*[contains(text(),"Auftragnehmer")]//following::td[1]').text#.split("\n")[1]

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
    
    try:
        WebDriverWait(page_details, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,' th:nth-child(2)')))
    except:
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
    urls = ["https://vergabe.muenchen.de/NetServer/PublicationSearchControllerServlet?function=SearchPublications&Gesetzesgrundlage=All&Category=ContractAward&thContext=awardPublications"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        click1 = WebDriverWait(page_main, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'  button.btn.btn-link.btn-extendet-search')))
        page_main.execute_script("arguments[0].click();",click1)
        time.sleep(5)
        
        select_fr = Select(page_main.find_element(By.CSS_SELECTOR,'#publicationCategorySelect'))
        select_fr.select_by_index(2)
        time.sleep(5)
        
        index=[0,1,2]
        for i in index:
            select_fr = Select(page_main.find_element(By.CSS_SELECTOR,'#tenderKindnSelect'))
            select_fr.select_by_index(i)
            time.sleep(5)
            
            click2 = WebDriverWait(page_main, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#btnSearchSubmit')))
            page_main.execute_script("arguments[0].click();",click2)
            time.sleep(5)
            try:
                for page_no in range(2,4):
                    page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,' table.table.table-responsive.table-striped.table-hover.tableHorizontalHeader > tbody > tr'))).text
                    rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'table.table.table-responsive.table-striped.table-hover.tableHorizontalHeader > tbody > tr')))
                    length = len(rows)
                    for records in range(0,length):
                        tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'table.table.table-responsive.table-striped.table-hover.tableHorizontalHeader > tbody > tr')))[records]
                        extract_and_save_notice(tender_html_element)
                        if notice_count >= MAX_NOTICES:
                            break
    
                        if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                            break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
    
                    try:   
                        next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                        page_main.execute_script("arguments[0].click();",next_page)
                        logging.info("Next page")
                        WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'table.table.table-responsive.table-striped.table-hover.tableHorizontalHeader > tbody > tr'),page_check))
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
