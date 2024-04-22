from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "de_hessen"
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
SCRIPT_NAME = "de_hessen"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    # Onsite Field -None
    # Onsite Comment -format 1 :- if type_of_procedure_actual have keywords like 'open procedure', 'negotiated procedure with participation competition' and format 2 :- if type_of_procedure_actual have keywords like 'Public tender'
    notice_data.script_name = 'de_hessen'
    
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
    # Onsite Comment -'https://vergabe.hessen.de/NetServer/PublicationSearchControllerServlet?function=SearchPublications&Gesetzesgrundlage=All&Category=PriorInformation&thContext=preinformations&Order=desc&OrderBy=Publishing&Max=25' notice type will be 3 for this link
    if 'https://vergabe.hessen.de/NetServer/PublicationSearchControllerServlet?function=SearchPublications&Gesetzesgrundlage=All&Category=PriorInformation&thContext=preinformations&Order=desc&OrderBy=Publishing&Max=25' == url:
        notice_data.notice_type = 3
    else:
        notice_data.notice_type = 4
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'div > h1').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'p.mb-3').text
        try:
            notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
        except:
            return
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-5 > p:nth-child(4)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Art:
    # Onsite Comment - split type_of_procedure_actual from the selector eg :from "VOB, Öffentliche Ausschreibung" take only "Öffentliche Ausschreibung"
    try:
        notice_data.type_of_procedure_actual = tender_html_element.find_element(By.CSS_SELECTOR, "div.col-7  > div:nth-child(1)  > div > div:nth-child(2)").text.split(',')[1]
        type_of_procedure_actual = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("assets/de_hessen_procedure.csv",type_of_procedure_actual)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Abgabefrist:
    # Onsite Comment -take notice_deadline as threshold for notice type 2

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "div.col-7  > div:nth-child(3)  > div > div:nth-child(2)").text
        notice_deadline = re.findall('\d+.\d+.\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
        return
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.publish_date = date.today().strftime('%Y/%m/%d %H:%M:%S')
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'section > div> a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#content-section').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Kurze Beschreibung:
    # Onsite Comment -use this selector for FORMAT 1 and if notice_summary_english is not available then pass local_title as notice_summary_english

    try:
        notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),"Kurze Beschreibung:")]//following::td[1]').text
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_summary_english)
    except:
        try:
            # Onsite Field -None
            # Onsite Comment -use this selector for FORMAT 2
            # selector not working
            notice_data.notice_summary_english = notice_data.notice_title
        except Exception as e:
            logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
            pass
    
    # Onsite Field -Tag der Absendung dieser Bekanntmachung:
    # Onsite Comment -None

    try:
        dispatch_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Tag der Absendung dieser Bekanntmachung:")]//following::td[1]').text
        notice_data.dispatch_date = datetime.strptime(dispatch_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in dispatch_date: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Geschätzter Gesamtwert
    # Onsite Comment -None
    # https://vergabe.hessen.de/NetServer/PublicationControllerServlet?function=Detail&TOID=54321-NetTender-18805ab6c23-11e9ccaf409cabb8&Category=PriorInformation
    
    try:
        grossbudgetlc = page_details.find_element(By.XPATH, '//*[contains(text(),"Geschätzter Gesamtwert")]//following::td[1]').text.split(':')[1].replace(' EUR','').replace('.','').strip()
        notice_data.grossbudgetlc = float(grossbudgetlc.replace(',','.'))
        notice_data.est_amount = float(grossbudgetlc.replace(',','.'))
    except:
        try:
            grossbudgetlc = page_details.find_element(By.XPATH, '//*[contains(text(),"Geschätzter Wert")]//following::td[1]').text.split(':')[1].replace(' EUR','').replace('.','').strip()
            notice_data.grossbudgetlc = float(grossbudgetlc.replace(',','.'))
            notice_data.est_amount = float(grossbudgetlc.replace(',','.'))
        except Exception as e:
            logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
            pass
   
# Onsite Field -None
# Onsite Comment -None

    try:              
        # for single_record in page_details.find_elements(By.CSS_SELECTOR, '#content-section'):
        customer_details_data = customer_details()
        customer_details_data.org_country = 'DE'
        # Onsite Field -None
        # Onsite Comment -None
        try:
            org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Anschrift:")]//following::td[1]').text
            customer_details_data.org_name = org_name.split('\n')[0].strip()
        except:
            try:
                org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Adressen")]//following::td[1]').text
                customer_details_data.org_name = org_name.split('Offizielle Bezeichnung:')[1].split("\n")[0].strip()
            except:
                org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Adressen")]//following::td[1]').text
                customer_details_data.org_name = org_name.split('\n')[0].strip()
        # Onsite Field -Name und Adressen
        # Onsite Comment -use this selector for FORMAT 1

        try:
            customer_details_data.org_address = page_details.find_element(By.CSS_SELECTOR, 'tbody > tr:nth-child(3) > td:nth-child(2)').text.split('Postanschrift:')[1].split('NUTS')[0]
        except:
            # Onsite Field -Name und Anschrift:
            # Onsite Comment -use this selector for FORMAT 2

            try:
                customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Anschrift:")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
    
        # Onsite Field -Telefonnummer:
        # Onsite Comment -use this selector for FORMAT 2

        try:
            customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Adressen")]//following::td[1]').text.split('Telefon: ')[1].split('E-Mail')[0] 
        except:
            try:
                customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Telefonnummer:")]//following::td[1]').text
            except:
                try:
                    org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Telefon:")]//following::td[1]').text.strip()
                    if org_phone !='':
                        customer_details_data.org_phone = org_phone
                except Exception as e:
                    logging.info("Exception in org_phone: {}".format(type(e).__name__))
                    pass
        
        # Onsite Field -E-Mail:
        # Onsite Comment -use this selector for FORMAT 1 and split org_email from the given selector take only 'E-Mail:'

        try:
            customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Adressen")]//following::td[1]').text.split('E-Mail:')[1].split('Fax:')[0].strip().lower().replace('\n','')
        except:
    
            # Onsite Field -E-Mail:
            # Onsite Comment -use this selector for FORMAT 2

            try:
                customer_details_data.org_email =fn.get_email(page_details.find_element(By.CSS_SELECTOR, '#content-section').get_attribute("outerHTML").strip().lower().replace('\n',''))
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Fax:
        # Onsite Comment -use this selector for FORMAT 1 and split org_fax from the given selector take only 'Fax:'

        try:
            customer_details_data.org_fax = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Adressen")]//following::td[1]').text.split('Fax:')[1] 
        except:
    
            # Onsite Field -faxnummer:
            # Onsite Comment -use this selector for FORMAT 2

            try:
                customer_details_data.org_fax = page_details.find_element(By.XPATH, '//*[contains(text(),"faxnummer:")]//following::td[1]').text
            except:
                try:
                    customer_details_data.org_fax = page_details.find_element(By.XPATH, '//*[contains(text(),"Fax:")]//following::td[1]').text 
                except:
                    try:
                        customer_details_data.org_fax = page_details.find_element(By.XPATH, '//*[contains(text(),"Telefaxnummer:")]//following::td[1]').text
                    except Exception as e:
                        logging.info("Exception in org_fax: {}".format(type(e).__name__))
                        pass
    
        # Onsite Field -Internet-Adresse(n)
        # Onsite Comment -use this selector for FORMAT 1

        try:
            customer_details_data.org_website = page_details.find_element(By.XPATH, '//*[contains(text(),"Internet-Adresse(n)")]//following::a[1]').text
        except:
            try:
                # Onsite Field -Internet
                # Onsite Comment -use this selector for FORMAT 2
                customer_details_data.org_website = page_details.find_element(By.XPATH, '//*[contains(text(),"Internet-Adresse")]//following::a[1]').text
            except:
                try:
                    customer_details_data.org_website = page_details.find_element(By.XPATH, '//*[contains(text(),"Internet")]//following::a[1]').text
                except Exception as e:
                    logging.info("Exception in org_website: {}".format(type(e).__name__))
                    pass
    
        # Onsite Field -Name und Adressen
        # Onsite Comment -use this selector for FORMAT 1  split customer_nuts from the given selector take only 'NUTS-Code:'

        try:
            customer_details_data.customer_nuts = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Adressen")]//following::td[1]').text.split('NUTS-Code: ')[1].split('\n')[0]
        except:
            pass
    
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:     
                 
        for cpvs_records in page_details.find_elements(By.XPATH, '//*[contains(text(),"CPV")]//following::td[1]'):
            for cpv in cpvs_records.text.split('\n'):
                # if cpv is not cpv.isalpha:
                #     continue
                single_cpv = re.findall('\d+', cpv)[0]
                if len(single_cpv)>6: 
                    cpvs_data = cpvs()
                    # Onsite Field -CPV-Code Hauptteil
                    # Onsite Comment -use this selector for FORMAT 1

                    cpvs_data.cpv_code = single_cpv
                    cpvs_data.cpvs_cleanup()
                    notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        # for single_record in page_details.find_elements(By.CSS_SELECTOR, '#content-section'):
            tender_criteria_data = tender_criteria()
            # Onsite Field -Zuschlagskriterien
            # Onsite Comment -use this selector for FORMAT 1
            tender_criteria_title = page_details.find_element(By.XPATH, '//*[contains(text(),"Zuschlagskriterien")]//following::tr[2]').text
            if '' != tender_criteria_title:
                if 'Preis' in tender_criteria_title:
                    # for Preis in tender_criteria_title.split('Kriterium'):
                    tender_criteria_data.tender_criteria_title= GoogleTranslator(source='auto', target='en').translate(tender_criteria_title.split('Gewichtung')[0])
                    try:
                        tender_criteria_data.tender_criteria_weight = int(tender_criteria_title.split(' ')[-1].split(',')[0])
                    except:
                        pass
                else:
                    tender_criteria_data.tender_criteria_title= GoogleTranslator(source='auto', target='en').translate(tender_criteria_title)
            tender_criteria_data.tender_criteria_cleanup()
            notice_data.tender_criteria.append(tender_criteria_data)
    except Exception as e:
        logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
            
        # Onsite Field -Angaben zu Mitteln der Europäischen Union
        # Onsite Comment -if in below text written as "Angaben zu Mitteln der Europäischen Union Der Auftrag steht in Verbindung mit einem Vorhaben und/oder Programm, das aus Mitteln der EU finanziert wird: Nein" than pass the "None" in field name "T.FUNDING_AGENCIES::TEXT" and if "Angaben zu Mitteln der Europäischen Union Der Auftrag steht in Verbindung mit einem Vorhaben und/oder Programm, das aus Mitteln der EU finanziert wird:YES  " than pass the "Funding agency" name as "European Agency (internal id: 1344862)" in field name "T.FUNDING_AGENCIES::TEXT"

        funding_agency = page_details.find_element(By.XPATH, '//*[contains(text(),"Angaben zu Mitteln der Europäischen Union")]//following::td[1]').text
        funding_agency =  GoogleTranslator(source='auto', target='en').translate(funding_agency)
        if 'yes' in funding_agency.lower():
            funding_agencies_data = funding_agencies()
            funding_agencies_data.funding_agency 
            funding_agencies_data.funding_agencies_cleanup()
            notice_data.funding_agencies.append(funding_agencies_data)
    except Exception as e:
        logging.info("Exception in funding_agencies: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        lot_details_data = lot_details()
        
    # Onsite Field -None
    # Onsite Comment -None

        try:
            lot_details_data.lot_title = tender_html_element.find_element(By.CSS_SELECTOR, 'p.mb-3').text
        except Exception as e:
            logging.info("Exception in lot_title: {}".format(type(e).__name__))
            pass
            # Onsite Field -Kurze Beschreibung:
            # Onsite Comment -use this selector for FORMAT 1 and if lot_description is not available then pass local_title as lot_description

        try:
            lot_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Kurze Beschreibung:")]//following::td[1]').text
            lot_details_data.lot_description = GoogleTranslator(source='auto', target='en').translate(lot_description)
        except:

            # Onsite Field -None
            # Onsite Comment -use this selector for FORMAT 2

            try:
                lot_description = page_details.find_element(By.CSS_SELECTOR, 'p.mb-3').text
                lot_details_data.lot_description = GoogleTranslator(source='auto', target='en').translate(lot_description)
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass
    
    # Onsite Field -Geschätzter Gesamtwert
    # Onsite Comment -None
        try:
            lot_grossbudget_lc = page_details.find_element(By.XPATH, '//*[contains(text(),"Geschätzter Gesamtwert")]//following::td[1]').text.strip()
            notice_data.lot_grossbudget_lc = int(re.findall('\d+',lot_grossbudget_lc)[0])
        except:
            try:
                lot_grossbudget_lc = page_details.find_element(By.XPATH, '//*[contains(text(),"Geschätzter Wert")]//following::td[1]').text.strip()
                notice_data.lot_grossbudget_lc = int(re.findall('\d+',lot_grossbudget_lc)[0])   
            except Exception as e:
                logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
                pass
                
        
    
    # Onsite Field -Laufzeit des Vertrags, der Rahmenvereinbarung oder des dynamischen Beschaffungssystems
    # Onsite Comment -use this selector for FORMAT 1 and split contract_start_date from the given selector

        try:
            contract_start_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Laufzeit des Vertrags, der Rahmenvereinbarung oder des dynamischen Beschaffungssystems")]//following::td[1]').text
            contract_start_date = re.findall('\d+.\d+.\d{4}',contract_start_date)[0]
            lot_details_data.contract_start_date = datetime.strptime(contract_start_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
        except:
    
            # Onsite Field -Beginn
            # Onsite Comment -use this selector for FORMAT 2

            try:
                contract_start_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Beginn")]//following::td[1]').text
                contract_start_date = re.findall('\d+.\d+.\d{4}',contract_start_date)[0]
                lot_details_data.contract_start_date = datetime.strptime(contract_start_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
            except Exception as e:
                logging.info("Exception in contract_start_date: {}".format(type(e).__name__))
                pass
    
    # Onsite Field -Ende:
    # Onsite Comment -use this selector for FORMAT 1 and split contract_end_date from the given selector

        try:
            contract_end_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Laufzeit des Vertrags, der Rahmenvereinbarung oder des dynamischen Beschaffungssystems")]//following::td[1]').text
            contract_end_date = re.findall('\d+.\d+.\d{4}',contract_end_date)[0]
            lot_details_data.contract_end_date = datetime.strptime(contract_end_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
        except:
            # Onsite Field -Ende
            # Onsite Comment -use this selector for FORMAT 2

            try:
                contract_end_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Ende")]//following::td[1]').text
                contract_end_date = re.findall('\d+.\d+.\d{4}',contract_end_date)[0]
                lot_details_data.contract_end_date = datetime.strptime(contract_end_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
            except Exception as e:
                logging.info("Exception in contract_end_date: {}".format(type(e).__name__))
                pass
    
    # Onsite Field -None
    # Onsite Comment -None
        try:     
                 
            for cpvs_records in page_details.find_elements(By.XPATH, '//*[contains(text(),"CPV")]//following::td[1]'):
                for cpv in cpvs_records.text.split('\n'):
                    single_cpv = re.findall('\d+', cpv)[0]
                    if len(single_cpv)>6: 
                        lot_cpvs_data = lot_cpvs()
                        # Onsite Field -CPV-Code Hauptteil
                        # Onsite Comment -use this selector for FORMAT 1

                        lot_cpvs_data.lot_cpv_code = single_cpv
                        lot_cpvs_data.lot_cpvs_cleanup()
                        lot_details_data.lot_cpvs.append(lot_cpvs_data)
        except Exception as e:
            logging.info("Exception in lot_cpvs: {}".format(type(e).__name__)) 
            pass
        
    # Onsite Field -None
    # Onsite Comment -None

        try:
            lot_criteria_data = lot_criteria()
            # Onsite Field -Zuschlagskriterien
            # Onsite Comment -use this selector for FORMAT 1
            try:
                lot_criteria_title = page_details.find_element(By.XPATH, '//*[contains(text(),"Zuschlagskriterien")]//following::td[1]').text
                
                if lot_criteria_title !='':
                    lot_criteria_data.lot_criteria_title= GoogleTranslator(source='auto', target='en').translate(lot_criteria_title)
                   
            except:
                # Onsite Field -Zuschlagskriterien
                # Onsite Comment -use this selector for FORMAT 2
                lot_criteria_title = page_details.find_element(By.XPATH, '//*[contains(text(),"Zuschlagskriterien")]//following::tr[2]').text
                # 
                if lot_criteria_title !='':
                    lot_criteria_data.lot_criteria_title  =  GoogleTranslator(source='auto', target='en').translate(lot_criteria_title)
                   
            if lot_criteria_data.lot_criteria_title is not None:
                lot_criteria_data.lot_criteria_cleanup()
                lot_details_data.lot_criteria.append(lot_criteria_data)
        except Exception as e:
            logging.info("Exception in lot_criteria: {}".format(type(e).__name__))
            pass
        lot_details_data.lot_number =1
        lot_details_data.lot_details_cleanup()
        notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -click on "Unterlagen & Nachrichten" selector :- 'div.row.hideInPrint > div:nth-child(1) > a' and then click on download icon selector:-'td:nth-child(3) > a' then click on "Alles auswählen" and click on "Auswahl herunterladen" to download all the records

    try:              
        for single_record in page_details.find_element(By.CSS_SELECTOR, '#content-section').find_elements(By.CSS_SELECTOR, 'a'):
            external_url = single_record.get_attribute('href')
            if 'pdf' in external_url or 'PDF' in external_url or 'doc' in external_url or 'xml' in external_url or 'xmls' in external_url:
                attachments_data = attachments()
                attachments_data.file_name = 'Bestandteile der Teilnahmewettbewerbsunterlagen'
                attachments_data.file_name = 'Bestandteile der Vergabeunterlagen'
                # Onsite Field -None
                # Onsite Comment -Both format
                attachments_data.external_url = external_url
                attachments_data.file_type = external_url.split('.')[-1]
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
page_details = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://vergabe.hessen.de/NetServer/PublicationSearchControllerServlet?function=SearchPublications&PublicationType=&Searchkey=&Category=InvitationToTender&thContext=publications&Order=desc&OrderBy=Publishing&Max=25','https://vergabe.hessen.de/NetServer/PublicationSearchControllerServlet?function=SearchPublications&Gesetzesgrundlage=All&Category=PriorInformation&thContext=preinformations&Order=desc&OrderBy=Publishing&Max=25'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(2,6):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="searchForm"]/div/div/div/section/div'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="searchForm"]/div/div/div/section/div')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="searchForm"]/div/div/div/section/div')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
                  
                if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="searchForm"]/div/div/div/section/div'),page_check))
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
    
