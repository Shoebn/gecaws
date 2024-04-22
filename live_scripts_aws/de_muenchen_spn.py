from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "de_muenchen_spn"
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

# select data in tab  "Alle Ausschreibungen" + "Ausschreibungen" + ["Natioal-EU"/"National"/"EU"]

# Foemat 1)Public announcement=Öffentliche Ausschreibung
# Format 2)Negotiation procedure with participation competition=Verhandlungsverfahren mit Teilnahmewettbewerb
# Format 3)Open procedure=Offenes Verfahren

#for cpv
#Case 1 : Tender CPV given, but lot CPV not given, than it will not be repeated in Lots.
#Case 2: Tender CPV not given, lots CPV Given. it will be repeated in Tender CPV comma separated.
#Case 3: Tender CPV given, lot CPV also given, In this case also lot CPVs will be repeated in Tender CPV comma separated. But in this make sure that Tender CPV should be first followed by lot CPVs.

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "de_muenchen_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'de_muenchen_spn'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'DE'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'EUR'
    
    notice_data.main_language = 'DE'
    
    # Onsite Field -Note:Replace following kegword("National - EU=0","National=0","EU=2")
    # Onsite Comment -None

    notice_data.notice_type = 4
    
    if i == 0 or i == 2:
        notice_data.procurement_method = 1
    else:
        notice_data.procurement_method = 0
        
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
    
    # Onsite Field -Abgabefrist
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(6)").text
        notice_deadline = re.findall('\d+.\d+.\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Verfahrensart
    # Onsite Comment -None
    try:
        notice_data.type_of_procedure_actual = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text.strip()
        type_of_procedure_actual = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("assets/de_muenchen_spn_procedure.csv",type_of_procedure_actual)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
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
            
    try:
        notice_summary_english = notice_data.local_description
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_summary_english)
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    #     # Onsite Field -Abschnitt II: Gegenstand >> II.1.3) Art des Auftrags
#     # Onsite Comment -Note:Replace follwing keywords with given respective kywords ('Dienstleistungen =Service'),('Lieferauftrag=Supply'),('Bauauftrag=Works')
    
    try:
        notice_data.contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Beschreibung")]//following::td[1]').text.split("Art des Auftrags: ")[1]
        if 'Dienstleistungen' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Service'
        elif "Lieferauftrag" in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Supply'
        elif "Bauauftrag" in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Works'
    except:
        try:
            notice_data.contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Art des Auftrags")]//following::td[1]').text
            if 'Dienstleistungen' in notice_data.contract_type_actual:
                notice_data.notice_contract_type = 'Service'
            elif "Lieferauftrag" in notice_data.contract_type_actual:
                notice_data.notice_contract_type = 'Supply'
            elif "Bauauftrag" in notice_data.contract_type_actual:
                notice_data.notice_contract_type = 'Works'
        except Exception as e:
            logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
            pass
    
    try:              
        
        # Onsite Field -Beschaffungsinformationen (speziell) >> Verwendung von EU-Mitteln
        # Onsite Comment -Note:"II.2.13) Information on European Union funds" , if the "financed by EU funds: No" it will be go null.. and if the"financed by EU funds: YES" it will pass the "Funding agency" name as "European Agency (internal id: 1344862)

        funding_agency = page_details.find_element(By.XPATH, '//*[contains(text(),"Verwendung von EU-Mitteln")]//following::td[1]').text
        funding_agency = GoogleTranslator(source='auto', target='en').translate(funding_agency)
        if 'yes' in funding_agency:
            funding_agencies_data = funding_agencies()
            funding_agencies_data.funding_agency = 1344862
            funding_agencies_data.funding_agencies_cleanup()
            notice_data.funding_agencies.append(funding_agencies_data)
    except:
        try:              
        # Onsite Field -Abschnitt II: Gegenstand >> II.2.13) Angaben zu Mitteln der Europäischen Union
        # Onsite Comment -Note:"II.2.13) Information on European Union funds" , if the "financed by EU funds: No" it will be go null.. and if the"financed by EU funds: YES" it will pass the "Funding agency" name as "European Agency (internal id: 1344862)

            funding_agencies_data.funding_agency = page_details.find_element(By.XPATH, '//*[contains(text(),"II.2.13) Angaben zu Mitteln der Europäischen Union")]//following::td[1]').text
            funding_agency = GoogleTranslator(source='auto', target='en').translate(funding_agency)
            if 'yes' in funding_agency:
                funding_agencies_data = funding_agencies()
                funding_agencies_data.funding_agency = 1344862
                funding_agencies_data.funding_agencies_cleanup()
                notice_data.funding_agencies.append(funding_agencies_data)
                funding_agencies_data.funding_agencies_cleanup()
                notice_data.funding_agencies.append(funding_agencies_data)
        except Exception as e:
            logging.info("Exception in funding_agencies: {}".format(type(e).__name__)) 
            pass
    #     # Onsite Field -5. Art und Umfang sowie Ort der Leistung: >> Menge und Umfang
#     # Onsite Comment -None

    try:
        notice_data.tender_quantity_uom = page_details.find_element(By.XPATH, '//*[contains(text(),"Menge und Umfang")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in tender_quantity_uom: {}".format(type(e).__name__))
        pass
    
    #     # Onsite Field -Verfahren >> Umfang der Auftragsvergabe
#     # Onsite Comment -None

    try:
        netbudgetlc = page_details.find_element(By.XPATH, '//*[contains(text(),"Umfang der Auftragsvergabe")]//following::td[1]').text
        netbudgetlc= netbudgetlc.replace('.','').replace(',','.')
        notice_data.netbudgetlc = float(netbudgetlc)
    except Exception as e:
        logging.info("Exception in netbudgetlc: {}".format(type(e).__name__))
        pass
    
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
    
    try:
        notice_data.contract_duration = page_details.find_element(By.XPATH, '//*[contains(text(),"Geschätzte Laufzeit")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass
        

# Format 1)
# Ref_url=https://vergabe.muenchen.de/NetServer/PublicationControllerServlet?function=Detail&TOID=54321-NetTender-18b8529ee9f-509a087497baf64f&Category=InvitationToTender    
    try:
        attach_url = WebDriverWait(page_details, 60).until(EC.presence_of_element_located((By.CSS_SELECTOR, "tbody > tr > td > a"))).get_attribute("href")                     
        logging.info(attach_url)
        fn.load_page(page_details1,attach_url,100)
        time.sleep(3)
    except:
        pass
    
    try:
        attach_url1 = WebDriverWait(page_details1, 60).until(EC.presence_of_element_located((By.CSS_SELECTOR, " strong > a"))).get_attribute("href")                     
        logging.info(attach_url1)
        fn.load_page(page_details2,attach_url1,100)
        time.sleep(3)
    except:
        pass
    
    
    try:              
        for single_record in page_details2.find_elements(By.CSS_SELECTOR, ' article > div:nth-child(n) > div > div > div > div > ul > li:nth-child(n) > a'):
            attachments_data = attachments()
        # Onsite Field -Download
        # Onsite Comment -Note:Don't take file extenstion ex.,(.pdf) 		Note:First click on "div.downloadDocuments > a" then second click on hear "tbody > tr > td > a" and grab the data 		Note:Open page_main the first click "Alles auswählen" then second click "Auswahl herunterladen"

            attachments_data.file_name = single_record.text
            
        
        # Onsite Field -Download
        # Onsite Comment -None

            attachments_data.external_url = single_record.get_attribute('href')

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    try:
        attach_url2 = WebDriverWait(page_details, 60).until(EC.presence_of_element_located((By.CSS_SELECTOR, " div.downloadDocuments > a"))).get_attribute("href")                     
        logging.info(attach_url2)
        fn.load_page(page_details3,attach_url2,100)
        time.sleep(3)
    except:
        pass
    try:
        click2 = WebDriverWait(page_details3, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'tbody > tr > td > a')))
        page_details3.execute_script("arguments[0].click();",click2)
        time.sleep(5)
    except:
        pass
    
    try:              
        for single_record in page_details3.find_elements(By.CSS_SELECTOR, ' div.folderBox > div:nth-child(n) > a'):
            attachments_data = attachments()
            # Onsite Field -Download
            # Onsite Comment -Note:Don't take file extenstion ex.,(.pdf) 		Note:First click on "div.downloadDocuments > a" then second click on hear "tbody > tr > td > a" and grab the data 		Note:Open page_main the first click "Alles auswählen" then second click "Auswahl herunterladen"
           
            attachments_data.file_name = single_record.text

            # Onsite Field -Download
            # Onsite Comment -None

            attachments_data.external_url = single_record.get_attribute('href')

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    try:
        click2 = WebDriverWait(page_details3, 10).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="buttonModalClose"]')))
        page_details3.execute_script("arguments[0].click();",click2)
        time.sleep(5)
    except:
        pass

    try:              
        customer_details_data = customer_details()
        # Onsite Field -Name und Anschrift
        # Onsite Comment -Note:Take only first line

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
            
    # Onsite Field -Name und Anschrift
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

    # Onsite Field -Telefonnummer
    # Onsite Comment -None

        try:
            customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Beschaffer")]//following::td[1]').text.split("Telefon:")[1].split("Fax:")[0].split("Art des öffentlichen Auftraggebers:")[0].strip()
        except:
            try:
                org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Telefonnummer")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass

    # Onsite Field -Telefaxnummer
    # Onsite Comment -None

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

    # Onsite Field -E-Mail-Adresse
    # Onsite Comment -None

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

    # Onsite Field -Internet-Adresse
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
        try:
            customer_details_data.customer_main_activity = page_details.find_element(By.XPATH, '//*[contains(text(),"Beschaffer")]//following::td[1]').text.split("Haupttätigkeiten des öffentlichen Auftraggebers: ")[1].split("Profil des Erwerbers (URL):")[0].strip()
        except:
            try:
                customer_details_data.customer_main_activity = page_details.find_element(By.XPATH, '//*[contains(text(),"Haupttätigkeit(en)")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in customer_main_activity: {}".format(type(e).__name__))
                pass
        
        try:
            customer_details_data.postal_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Beschaffer")]//following::td[1]').text.split("Postleitzahl / Ort:")[1].split("NUTS-3-Code:")[0].strip()
        except:
            try:
                customer_details_data.postal_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Adressen")]//following::td[1]').text.split("Postleitzahl / Ort:")[1].split("Land:")[0].strip()
            except Exception as e:
                logging.info("Exception in postal_code: {}".format(type(e).__name__))
                pass
            
        try:
            customer_details_data.customer_nuts = page_details.find_element(By.XPATH, '//*[contains(text(),"Beschaffer")]//following::td[1]').text.split("NUTS-3-Code:")[1].split("Land: ")[0].strip()
        except:
            try:
                customer_details_data.customer_nuts = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Adressen")]//following::td[1]').text.split("NUTS-Code:")[1].split("E-Mail:")[0].strip()
            except Exception as e:
                logging.info("Exception in customer_nuts: {}".format(type(e).__name__))
                pass
        try:
            customer_details_data.type_of_authority_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Beschaffer")]//following::td[1]').text.split("Art des öffentlichen Auftraggebers:")[1].split("Haupttätigkeiten des öffentlichen Auftraggebers:")[0].strip()
        except:
            try:
                customer_details_data.type_of_authority_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Art des öffentlichen Auftraggebers")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in type_of_authority_code: {}".format(type(e).__name__))
                pass
        

        customer_details_data.org_country = 'DE'
        customer_details_data.org_language = 'DE'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
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
        
    # Onsite Field -Beschaffungsinformationen (speziell) >> Zuschlagskriterien
    # Onsite Comment -Note:Splite before "Gewichtung"

        tender_criteria_title = page_details.find_element(By.XPATH, '//*[contains(text(),"Zuschlagskriterien")]//following::td[5]').text.split(", ")[0].strip()
        tender_criteria_data = tender_criteria()
        tender_criteria_data.tender_criteria_title = GoogleTranslator(source='de', target='en').translate(tender_criteria_title)

    # Onsite Field -Beschaffungsinformationen (speziell) >> Zuschlagskriterien
    # Onsite Comment -Note:Splite after "Gewichtung"

        tender_criteria_weight = page_details.find_element(By.XPATH, '//*[contains(text(),"Zuschlagskriterien")]//following::td[5]').text.split(", ")[0].strip()
        tender_criteria_weight = re.findall('\d{2}',tender_criteria_weight)[0]
        tender_criteria_data.tender_criteria_weight = int(tender_criteria_weight)

        tender_criteria_data.tender_criteria_cleanup()
        notice_data.tender_criteria.append(tender_criteria_data)
    except Exception as e:
        logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
        pass

    notice_data.class_at_source = 'CPV'

    try:      
        cpv_at_source = ''
        for single_record in page_details.find_elements(By.XPATH, '//*[contains(text(),"CPV-Code Hauptteil")]'):
         # Onsite Field -Verfahren >> CPV-Code Hauptteil
         # Onsite Comment -Note:Split before "CPV-Code Hauptteil"
            cpv_code = single_record.text
            cpv_code = re.findall('\d{8}',cpv_code)[0]
            cpv_at_source += cpv_code
            cpv_at_source += ','
            
            cpvs_data = cpvs()
            cpvs_data.cpv_code = cpv_code
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
            
        notice_data.cpv_at_source = cpv_at_source.rstrip(',') 
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass

    
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
                    lot_cpv_at_source = ''
                    lot_cpv_at_source = single_record.find_element(By.XPATH, '//*[contains(text(),"CPV-Code Hauptteil")]').text
                    lot_cpv_at_source += re.findall('\d{8}',lot_cpv_at_source)[0]
                    lot_cpv_at_source += ','
                    lot_details_data.lot_cpv_at_source = lot_cpv_at_source.rstrip(',')
                except Exception as e:
                    logging.info("Exception in cpv_at_source: {}".format(type(e).__name__))
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
                    lot_criteria_data = lot_criteria()
                # Onsite Field -Beschaffungsinformationen (speziell) >> Zuschlagskriterien
                # Onsite Comment -Note:Splite before "Gewichtung"
                    lot_criteria_title = single_record.text.split("Zuschlagskriterien")[1].split("Gewichtung:")[0].strip()
                    lot_criteria_data.lot_criteria_title = GoogleTranslator(source='de', target='en').translate(lot_criteria_title)


                # Onsite Field -Beschaffungsinformationen (speziell) >> Zuschlagskriterien
                # Onsite Comment -Note:Splite after "Gewichtung"
                    lot_criteria_weight = single_record.text.split("Zuschlagskriterien")[1].split("Gewichtung:")[1].strip()
                    lot_criteria_weight = re.findall('\d+',lot_criteria_weight)[0]
                    lot_criteria_data.lot_criteria_weight = int(lot_criteria_weight.replace('.','').replace(',','').strip())

                    lot_criteria_data.lot_criteria_cleanup()
                    lot_details_data.lot_criteria.append(lot_criteria_data)
                except Exception as e:
                    logging.info("Exception in lot_criteria_data: {}".format(type(e).__name__)) 
                    pass

                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
                lot_number += 1
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
# # Onsite Field -None
# # Onsite Comment -Note:if the lot published in "5. Type and scope as well as location of the service: > Quantity and scope:", tha take the lots in a Lot loop. refer below url  https://vergabe.muenchen.de/NetServer/PublicationControllerServlet?function=Detail&TOID=54321-NetTender-18b36a84a5a-2ceb2bea4a86c263&Category=InvitationToTender LotAcualNumber = 'Lot1" LotTitle = Lot 1: Supply of all types of filters

    try:              
        lot = page_details.find_element(By.XPATH, '//*[contains(text(),"Menge und Umfang")]//following::td[1]').text.split("Lose.")[1].strip()
        lot_number = 1
        for l in lot.split('\n'):
            lot_details_data = lot_details()
            lot_details_data.lot_number = lot_number
    # Onsite Field -5. Art und Umfang sowie Ort der Leistung: >> Menge und Umfang:
    # Onsite Comment -Note:1)here "Los 1: Lieferung von Filtern aller Art" take "Los 1" as lot_actual_number	2)take all lot_actual_number

            try:
                lot_details_data.lot_actual_number = l.split(":")[0]
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass

        # Onsite Field -5. Art und Umfang sowie Ort der Leistung: >> Menge und Umfang:
        # Onsite Comment -Note:1)here "Los 1: Lieferung von Filtern aller Art" take "Lieferung von Filtern aller Art" as lot_title	2)take all lot_title

            lot_details_data.lot_title = l.split(":")[1]
            lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)

            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
            lot_number += 1
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
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
page_details2 = fn.init_chrome_driver(arguments)
page_details3 = fn.init_chrome_driver(arguments)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://vergabe.muenchen.de/NetServer/PublicationSearchControllerServlet?function=SearchPublications&Gesetzesgrundlage=All&Category=InvitationToTender&thContext=publications&csrt=207473981149477300"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        click1 = WebDriverWait(page_main, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'  button.btn.btn-link.btn-extendet-search')))
        page_main.execute_script("arguments[0].click();",click1)
        time.sleep(5)
        
        index=[0,1]
        for i in index:
            select_fr = Select(page_main.find_element(By.CSS_SELECTOR,'#publicationCategorySelect'))
            select_fr.select_by_index(i)
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
    page_details1.quit()
    page_details2.quit()
    page_details3.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)
