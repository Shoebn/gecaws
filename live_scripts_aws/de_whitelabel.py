from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "de_whitelabel"
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
SCRIPT_NAME = "de_whitelabel"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"

def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'de_whitelabel'
    notice_data.main_language = 'DE'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'DE'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'EUR'
    notice_data.procurement_method = 2
    notice_data.notice_type = 4
    
    # Onsite Field -Art der Leistung
    # Onsite Comment -split the data from tender_html_page

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td.td-art-der-leistung').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    
    # Onsite Field -Veröffentlicht
    # Onsite Comment -this is for all 3 format

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td.td-veroeffentlicht").text
        publish_date = re.findall('\d+.\d+.\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Fristablauf
    # Onsite Comment -this is for all 3 format

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td.td-fristablauf").text
        notice_deadline = re.findall('\d+.\d+.\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    try:
        click_element = tender_html_element.get_attribute('onclick').split("window.location = '")[1].split("'")[0]
        notice_data.notice_url = 'https://whitelabel.vergabe24.de'+click_element     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url

    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div > #detailText').get_attribute("outerHTML")                     
    except:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
        
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text()," Art des Auftrags")]//following::p[1]').text
    except:
        try:
            notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Kurze Beschreibung")]//following::span[1]').text
        except:
            try:
                notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Art der Leistung")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in local_description: {}".format(type(e).__name__))
                pass
    
    # Onsite Field -d) Art des Auftrags
    # Onsite Comment -split the following data from this field, format 1

    try:
        notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),"Art des Auftrags")]//following::p[1]').text
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_summary_english)
    except:
        try:
            notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),"Kurze Beschreibung")]//following::span[1]').text
            notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_summary_english)
        except:
            try:
                notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),"Art der Leistung")]//following::span[1]').text
                notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_summary_english)
            except Exception as e:
                logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
                pass
    
    try:
        type_of_procedure_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Vergabeverfahren:")]//following::span[1]').text.strip()
        notice_data.type_of_procedure_actual = GoogleTranslator(source='auto', target='en').translate(type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("assets/de_whitelabel_ca_procedure.csv",notice_data.type_of_procedure_actual)
    except:
        try:
            type_of_procedure_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Verfahrensart:")]//following::span[1]').text.strip()
            notice_data.type_of_procedure_actual = GoogleTranslator(source='auto', target='en').translate(type_of_procedure_actual)
            notice_data.type_of_procedure = fn.procedure_mapping("assets/de_whitelabel_ca_procedure.csv",notice_data.type_of_procedure_actual)
        except:
            try:
                type_of_procedure_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"IV.1.1)")]//following::span[1]').text.strip()
                notice_data.type_of_procedure_actual = GoogleTranslator(source='auto', target='en').translate(type_of_procedure_actual)
                notice_data.type_of_procedure = fn.procedure_mapping("assets/de_whitelabel_ca_procedure.csv",notice_data.type_of_procedure_actual)
            except Exception as e:
                logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
                pass

    # Onsite Field -II.1.5) Geschätzter Gesamtwert   Wert ohne MwSt.:
    # Onsite Comment -split the data from format 2

    try:
        est_amount = page_details.find_element(By.XPATH, '//*[contains(text(),"Geschätzter Gesamtwert")]//following::span[1]').text
        est_amount = re.sub("[^\d\.\,]", "",est_amount)
        est_amount = est_amount.replace('.','').replace(',','.').strip()
        notice_data.est_amount = float(est_amount)
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -II.1.5) Geschätzter Gesamtwert   Wert ohne MwSt.:
    # Onsite Comment -split the data from format 2

    try:
        notice_data.grossbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
    
    try:
        notice_contract_type = page_details.find_element(By.XPATH, '//*[contains(text(),"Art des Auftrags")]//following::span[1]').text
        if 'Dienstleistungen' in notice_contract_type:
            notice_data.notice_contract_type = 'Service'
        elif 'Bauauftrag' in notice_contract_type or 'Ausführung von Bauleistungen' in notice_contract_type:
            notice_data.notice_contract_type = 'Works'
        else:
            pass
    except:
        try:
            notice_contract_type = page_details.find_element(By.XPATH, '//*[contains(text(),"Art der Leistung")]//following::span[1]').text
            if 'Dienstleistungen' in notice_contract_type:
                notice_data.notice_contract_type = 'Service'
            elif 'Bauauftrag' in notice_contract_type or 'Ausführung von Bauleistungen' in notice_contract_type:
                notice_data.notice_contract_type = 'Works'
            else:
                pass
        except:
            try:
                notice_contract_type = page_details.find_element(By.XPATH, '//*[contains(text(),"Art des Auftrags")]//following::p[1]').text
                if 'Dienstleistungen' in notice_contract_type:
                    notice_data.notice_contract_type = 'Service'
                elif 'Bauauftrag' in notice_contract_type or 'Ausführung von Bauleistungen' in notice_contract_type:
                    notice_data.notice_contract_type = 'Works'
                else:
                    pass
            except Exception as e:
                logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
                pass
    
    # Onsite Field -Vergabeverfahren:
    # Onsite Comment -split the data from format 1
    try:
        notice_data.document_type_description = 'Public Contracts'
    except:
        pass
        
        
     # Onsite Field -l) Bereitstellung/Anforderung der Vergabeunterlagen
    # Onsite Comment -ref url : "https://whitelabel.vergabe24.de/index.php?id=870&view=OA&site=viewDetails&tid=7051680", format 1

    try:
        notice_data.additional_tender_url = page_details.find_element(By.XPATH, '//*[contains(text()," Bereitstellung/Anforderung der Vergabeunterlagen")]//following::a').get_attribute("href")
    except:
        try:
            notice_data.additional_tender_url = page_details.find_element(By.XPATH, '//*[contains(text(),"I.3) Kommunikation")]//following::a').get_attribute("href")
        except:
            try:
                notice_data.additional_tender_url = page_details.find_element(By.XPATH, '//*[contains(text(),"9. Elektronische Adresse, ")]//following::a').get_attribute("href")
            except Exception as e:
                logging.info("Exception in additional_tender_url: {}".format(type(e).__name__))
                pass

    # Onsite Field -II.2.13) Angaben zu Mitteln der Europäischen Union
    # Onsite Comment -if in below text written as " financed by European Union funds: No  " than pass the "None " in field name "T.FUNDING_AGENCIES::TEXT	" "II.2.13) Information about European Union Funds  >  The procurement is related to a project and/or programme financed by European Union funds: No  " if the abve  text written as " financed by European Union funds: YES  " than pass the "Funding agency" name as "European Agency (internal id: 1344862) " in field name "T.FUNDING_AGENCIES::TEXT", format 2

    try:
        funding_agencies = page_details.find_element(By.XPATH, '//*[contains(text(),"Angaben zu Mitteln der Europäischen Union")]//following::span[1]').text
        funding_agency = GoogleTranslator(source='auto', target='en').translate(funding_agency)
        if 'yes' in funding_agency or 'YES' in funding_agency or 'Yes' in funding_agency:
            funding_agencies_data = funding_agencies()
            funding_agencies_data.funding_agency = 1344862
            funding_agencies_data.funding_agencies_cleanup()
            notice_data.funding_agencies.append(funding_agencies_data)
        else:
            pass
    except Exception as e:
        logging.info("Exception in funding_agencies: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -VI.5) Tag der Absendung dieser Bekanntmachung:
    # Onsite Comment -split the following data from thsi field,  format 2

    try:
        dispatch_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Tag der Absendung dieser Bekanntmachung")]//following::span[1]').text
        dispatch_date = re.findall('\d+.\d+.\d{4}',dispatch_date)[0]
        notice_data.dispatch_date = datetime.strptime(dispatch_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in dispatch_date: {}".format(type(e).__name__))
        pass

# Onsite Field -"Öffentlicher Auftraggeber " ,  "1. Zur Angebotsabgabe auffordernde Stelle,"
# Onsite Comment -None

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'DE'
        customer_details_data.org_language = 'DE'
    # Onsite Field -Name und Anschrift:
    # Onsite Comment -split only org_name from this field ,  format1

        try:
            customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Anschrift")]//following::span[1]').text.split('\n')[0].strip()
        except:
            customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Adressen")]//following::span[1]').text.split(':')[1].split('\n')[0].strip()

    # Onsite Field -Name und Anschrift:
    # Onsite Comment -take the data between "Name und Anschrift:" and "Telefon" field  , split only org_address  from this field , format 1

        try:
            customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Anschrift")]//following::span[1]').text.strip()
        except:
            try:
                customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Adressen")]//following::span[1]').text.split(':')[1].split('NUTS-Code')[0].strip()
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass

        # Onsite Field -Name und Anschrift
        # Onsite Comment -split the last line of text value from this xpath, ref url : "https://whitelabel.vergabe24.de/index.php?id=870&view=OA&site=viewDetails&tid=7051680",   format 1

        try:
            org_city = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Anschrift")]//following::span[1]').text.split('\n')
            customer_details_data.org_city = org_city[-1].strip()
        except:
            try:
                customer_details_data.org_city = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Adressen")]//following::span[1]').text.split('Postleitzahl / Ort:')[1].split('Land')[0].strip() 
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass

        
    # Onsite Field -E-Mail:
    # Onsite Comment -split the following data from this field, format 1

        try:
            customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"E-Mail")]//following::span[1]').text.strip()
        except:
            try:
                customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Adressen")]//following::span[1]').text.split('E-Mail:')[1].split('\n')[0].strip()
            except:
                try:
                    customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"E-Mail-Adresse")]//following::span[1]').text.strip()
                except Exception as e:
                    logging.info("Exception in org_email: {}".format(type(e).__name__))
                    pass


    # Onsite Field -Telefon:
    # Onsite Comment -split the data from format 1

        try:
            customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Telefon")]//following::span[1]').text
        except:
            try:
                customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Telefonnummer")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
        
    # Onsite Field -Fax:
    # Onsite Comment -split the data from format 1

        try:
            customer_details_data.org_fax = page_details.find_element(By.XPATH, '//*[contains(text(),"Fax:")]//following::span[1]').text.strip()
        except:
            try:
                customer_details_data.org_fax = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Adressen")]//following::span[1]').text.split('Fax:')[1].strip()
            except:
                try:
                    customer_details_data.org_fax = page_details.find_element(By.XPATH, '//*[contains(text(),"Telefaxnummer")]//following::span[1]').text.strip()
                except Exception as e:
                    logging.info("Exception in org_fax: {}".format(type(e).__name__))
                    pass

    # Onsite Field -NUTS-Code
    # Onsite Comment -split the data between "Land:"  and "E-Mail:" field, ref url : "https://whitelabel.vergabe24.de/index.php?id=870&view=OA&site=viewDetails&tid=7003164" , format 2

        try:
            customer_details_data.customer_nuts = page_details.find_element(By.XPATH, '//*[contains(text()," Name und Adressen")]//following::span[1]').text.split('NUTS-Code:')[1].split('\n')[0].strip()
        except Exception as e:
            logging.info("Exception in customer_nuts: {}".format(type(e).__name__))
            pass

    # Onsite Field -Name und Anschrift
    # Onsite Comment -split the last line of (5 digit) number value from this xpath, ref url : "https://whitelabel.vergabe24.de/index.php?id=870&view=OA&site=viewDetails&tid=7051680", format 1

        try:
            postal_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Anschrift")]//following::span[1]').text
            postal_code = re.findall('\d{5}',postal_code)[0]
            customer_details_data.postal_code = postal_code
        except:
            try:
                postal_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Adressen")]//following::span[1]').text
                postal_code = re.findall('\d{5}',postal_code)[0]
                customer_details_data.postal_code = postal_code
            except Exception as e:
                logging.info("Exception in postal_code: {}".format(type(e).__name__))
                pass

    # Onsite Field -Internet:
    # Onsite Comment -split the following data from this xpath, ref url : "https://whitelabel.vergabe24.de/index.php?id=870&view=OA&site=viewDetails&tid=7051680", format 1

        try:
            customer_details_data.org_website = page_details.find_element(By.XPATH, '//*[contains(text(),"Internet:")]//following::a[1]').text
        except:
            try:
                customer_details_data.org_website = page_details.find_element(By.XPATH, '//*[contains(text(),"Hauptadresse")]//following::a[1]').text
            except:
                try:
                    customer_details_data.org_website = page_details.find_element(By.XPATH, '//*[contains(text(),"Internet-Adresse")]//following::a[1]').text
                except Exception as e:
                    logging.info("Exception in org_website: {}".format(type(e).__name__))
                    pass


        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try:              
        cpvs_data = cpvs()
    # Onsite Field -II.1.2) CPV-Code Hauptteil
    # Onsite Comment -split the cpv code from this field, ref url : "https://whitelabel.vergabe24.de/index.php?id=870&view=OA&site=viewDetails&tid=7003164"

        cpvs_data.cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"CPV-Code Hauptteil")]//following::span[1]').text.split('-')[0].strp()
        
        cpvs_data.cpvs_cleanup()
        notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
    
    # Onsite Field -r) Zuschlagskriterien
    # Onsite Comment -None

    try:              
        text = page_details.find_element(By.XPATH, '//*[@id="detailText"]').text
        if 'r) Zuschlagskriterien' in text:
            tender_criteria_data = tender_criteria()
            tender_criteria_data.tender_criteria_title = page_details.find_element(By.XPATH, '//*[contains(text(),"Zuschlagskriterien")]//following::p[1]').text
        # Onsite Field -r) Zuschlagskriterien
        # Onsite Comment -there is only one field in format 1, url ref : "https://whitelabel.vergabe24.de/index.php?id=870&view=OA&site=viewDetails&tid=7051680"
            tender_criteria_data.tender_criteria_cleanup()
            notice_data.tender_criteria.append(tender_criteria_data)
    except Exception as e:
        logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
        pass

    try:
        lot_number = 1
        for single_record in page_details.find_elements(By.XPATH, '//*[contains(text(),"II.2.1) Bezeichnung des Auftrags")]//following::span[1]'):
            lot_details_data = lot_details()
            lot_details_data.lot_number = lot_number
            
            # Onsite Field -II.2.1) Bezeichnung des Auftrags:
            # Onsite Comment -split only lot_title from this field, take the following value from "Bezeichnung des Auftrags:" this field

            lot_title = single_record.text.split(':')[1].split('\n')[0].strip()
            lot_details_data.lot_title = GoogleTranslator(source='auto', target='en').translate(lot_title)
            
        
        # Onsite Field -Los-Nr:
        # Onsite Comment -split the data between "II.2.1) Bezeichnung des Auftrags" and "II.2.2) Weitere(r) CPV-Code(s)" field, url ref : "https://whitelabel.vergabe24.de/index.php?id=870&view=OA&site=viewDetails&tid=7003164"

            try:
                lot_details_data.lot_actual_number = single_record.text.split('\n')[1].split('\n')[0].strip()
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass
            
        # Onsite Field -II.2.4) Beschreibung der Beschaffung
        # Onsite Comment -split the following data from this field, url ref : "https://whitelabel.vergabe24.de/index.php?id=870&view=OA&site=viewDetails&tid=7003164"
        
            try:
                lot_description = page_details.find_element(By.XPATH, '//*[contains(text(),"II.2.4) Beschreibung der Beschaffung")]//following::span[1]').text.split('Termine:')[0].strip()
                lot_details_data.lot_description = GoogleTranslator(source='auto', target='en').translate(lot_description)
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass
            
            # Onsite Field -d) Art des Auftrags
        # Onsite Comment -split the data from format 1  

            try:
                lot_details_data.contract_type = notice_data.notice_contract_type
            except Exception as e:
                logging.info("Exception in contract_type: {}".format(type(e).__name__))
                pass

        # Onsite Field -Beginn:
        # Onsite Comment -take the value from "Beginn:"  keyword,  ref url "https://whitelabel.vergabe24.de/index.php?id=870&view=OA&site=viewDetails&tid=7003164"

            try:
                contract_start_date = page_details.find_element(By.CSS_SELECTOR, 'p:nth-child(61) > span').text.split('Ende:')[0].strip()
                contract_start_date = re.findall('\d+.\d+.\d{4}',contract_start_date)[0]
                lot_details_data.contract_start_date = datetime.strptime(contract_start_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
            except Exception as e:
                logging.info("Exception in contract_start_date: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Ende:
        # Onsite Comment -take the value from "Ende"  keyword,  ref url "https://whitelabel.vergabe24.de/index.php?id=870&view=OA&site=viewDetails&tid=7003164"

            try:
                contract_end_date = page_details.find_element(By.CSS_SELECTOR, 'p:nth-child(61) > span').text.split('Ende:')[1].split('\n')[0].strip()
                contract_end_date = re.findall('\d+.\d+.\d{4}',contract_end_date)[0]
                lot_details_data.contract_end_date = datetime.strptime(contract_end_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
            except Exception as e:
                logging.info("Exception in contract_end_date: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -NUTS-Code:
        # Onsite Comment -split the data betweeen "Erfüllungsort"  and "Hauptort der Ausführung:" field,  ref url "https://whitelabel.vergabe24.de/index.php?id=870&view=OA&site=viewDetails&tid=7003164"

            try: 
                lot_details_data.lot_nuts = page_details.find_element(By.CSS_SELECTOR, '//*[contains(text(),"NUTS-Code:")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in lot_nuts: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -II.2.6) Geschätzter Wert   Wert ohne MwSt.:
        # Onsite Comment -ref url "https://whitelabel.vergabe24.de/index.php?id=870&view=OA&site=viewDetails&tid=7003164"

            try:
                lot_grossbudget_lc = page_details.find_element(By.XPATH, '//*[contains(text(),"II.2.6) Geschätzter Wert")]//following::span[1]').text
                lot_grossbudget_lc = re.sub("[^\d\.\,]","",lot_grossbudget_lc)
                lot_details_data.lot_grossbudget_lc =float(lot_grossbudget_lc.replace('.','').replace(',','.').strip()) 
            except Exception as e:
                logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
                pass

            try:
                lot_cpvs_data = lot_cpvs()

                # Onsite Field -II.2.2) Weitere(r) CPV-Code(s)   CPV-Code Hauptteil:
                # Onsite Comment -split the following data from this field

                lot_cpvs_data.lot_cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"II.2.2) Weitere(r) CPV-Code(s)")]//following::span[1]').text.split('-')[0].strip()

                lot_cpvs_data.lot_cpvs_cleanup()
                lot_details_data.lot_cpvs.append(lot_cpvs_data)
            except Exception as e:
                logging.info("Exception in lot_cpvs: {}".format(type(e).__name__))
                pass

            try:
                lot_criteria_data = lot_criteria()

                # Onsite Field -II.2.5) Zuschlagskriterien
                # Onsite Comment -ref url : "https://whitelabel.vergabe24.de/index.php?id=870&view=OA&site=viewDetails&tid=7003164"

                lot_criteria_data.lot_criteria_title = page_details.find_element(By.XPATH, '//*[contains(text(),"II.2.5) Zuschlagskriterien")]//following::span[1]').text

                lot_criteria_data.lot_criteria_cleanup()
                lot_details_data.lot_criteria.append(lot_criteria_data)
            except Exception as e:
                logging.info("Exception in lot_criteria: {}".format(type(e).__name__))
                pass

            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
            lot_number += 1
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) + str(notice_data.publish_date) +  str(notice_data.notice_url) 
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
    urls = ["https://whitelabel.vergabe24.de/?id=870"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)

        try:
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="wrapperResult"]/table/tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="wrapperResult"]/table/tbody/tr')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
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
