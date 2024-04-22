from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "ch_simap_amd"
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
from selenium import webdriver
from gec_common import functions as fn

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "ch_simap_amd"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"

def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'ch_simap_amd'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'CH'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.procurement_method = 2
    
    notice_data.currency = 'CHF'
    
    notice_data.notice_type = 4
    
    notice_data.class_at_source = 'CPV'

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass 
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4) > a').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
        publish_date = re.findall('\d+.\d+.\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(3)").text
        notice_deadline = re.findall('\d+.\d+.\d{4} \d+:\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d.%m.%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass 
    
    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    except:
        pass
    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4) > a').get_attribute("href")
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__)) 
        pass

    try:
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)

        try:
            notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#Formcontent').get_attribute("outerHTML")
            if '1.1 Offizieller Name und Adresse des Auftraggebers' in notice_data.notice_text:
                 notice_data.main_language = 'DE'
            elif '1.1 Nom officiel et adresse du pouvoir adjudicateur' in notice_data.notice_text:
                 notice_data.main_language = 'FR'
            elif '1.1 Nome ufficiale e indirizzo del committente' in notice_data.notice_text:
                 notice_data.main_language = 'IT'
            elif '1.1 Official name and address of the contracting authority' in notice_data.notice_text:
                 notice_data.main_language = 'EN'
        except:
            pass

        try:
            notice_data.document_type_description = page_details.find_element(By.CSS_SELECTOR, 'div.result_head').text.split('|')[-1].strip()
            if 'Cancellation of invitation to tender' in notice_data.document_type_description or 'Rectification' in notice_data.document_type_description:
                notice_data.notice_type = 16
        except Exception as e:
            logging.info("Exception in document_type_description: {}".format(type(e).__name__)) 
            pass

        try:  
            class_codes_at_source = ''
            class_title_at_source = ''
            cpv_at_source = ''
            for code in page_details.find_elements(By.XPATH, '//*[contains(text(),"CPV:")]//ancestor::tbody[1]/tr'):
                cpv_code = code.text

                class_title_at_source += cpv_code.split('-')[1].strip()

                cpv_regex = re.compile(r'\d{8}')
                cpv_code_list = cpv_regex.findall(cpv_code)[0]
                cpvs_data = cpvs()

                class_codes_at_source += cpv_code_list
                class_codes_at_source += ','

                cpv_at_source += cpv_code_list
                cpv_at_source += ','

                cpvs_data.cpv_code = cpv_code_list
                cpvs_data.cpvs_cleanup()
                notice_data.cpvs.append(cpvs_data)

            notice_data.class_codes_at_source = class_codes_at_source.rstrip(',')

            notice_data.class_title_at_source = class_title_at_source.rstrip(',')        

            notice_data.cpv_at_source = cpv_at_source.rstrip(',')        
        except Exception as e:
            logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
            pass

#******************************************* FORMAT 1 ******************************************************

        if '1.1 Nome ufficiale e indirizzo del committente' in notice_data.notice_text:

            try:              
                customer_details_data = customer_details()
                customer_details_data.org_country = 'CH'
                customer_details_data.org_language = notice_data.main_language

                customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Servizio richiedente/Ente aggiudicatore:")]//parent::dd[1]').text.split('Servizio richiedente/Ente aggiudicatore:')[1].split('\n')[0].strip()

                try:
                    customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Servizio richiedente/Ente aggiudicatore:")]//parent::dd[1]').text.split("Servizio d'acquisto/Organizzatore:")[1].split('Telefono')[0].strip()
                except Exception as e:
                    logging.info("Exception in org_address_1: {}".format(type(e).__name__)) 
                    pass

                try:
                    customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Servizio richiedente/Ente aggiudicatore:")]//parent::dd[1]').text.split("Telefono:")[1].split(',')[0].strip()
                except Exception as e:
                    logging.info("Exception in org_phone_1: {}".format(type(e).__name__)) 
                    pass

                try:
                    org_email1 = page_details.find_element(By.XPATH, '//*[contains(text(),"Servizio richiedente/Ente aggiudicatore:")]//parent::dd[1]').text
                    if 'E-Mail' in org_email1:
                        org_email = org_email1.split("E-Mail:")[1].strip()
                    elif 'E-mail' in org_email1:
                        org_email = org_email1.split('E-mail:')[1].strip()
                    email_regex = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b')
                    customer_details_data.org_email = email_regex.findall(org_email)[0]
                except Exception as e:
                    logging.info("Exception in org_email_1: {}".format(type(e).__name__)) 
                    pass

                try:
                    customer_details_data.type_of_authority_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Tipo di committente")]//following::dl[1]').text
                except Exception as e:
                    logging.info("Exception in type_of_authority_code_1: {}".format(type(e).__name__)) 
                    pass 

                customer_details_data.customer_details_cleanup()
                notice_data.customer_details.append(customer_details_data)
            except Exception as e:
                logging.info("Exception in customer_details_1: {}".format(type(e).__name__)) 
                pass

            try:
                notice_data.type_of_procedure_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Tipo di procedura")]//following::dl[1]').text
                type_of_procedure_actual = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
                type_of_procedure  = type_of_procedure_actual.lower()
                notice_data.type_of_procedure = fn.procedure_mapping("assets/ch_simap_procedure.csv",type_of_procedure)
            except Exception as e:
                logging.info("Exception in type_of_procedure_actual_1: {}".format(type(e).__name__))
                pass

            try: 
                notice_data.contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Tipo di commessa")]//following::dl[1]').text
                if "Commessa edile" in notice_data.contract_type_actual:
                    notice_data.notice_contract_type = "Works"
                elif "Commessa di servizi" in notice_data.contract_type_actual:
                    notice_data.notice_contract_type = "Service"
                else:
                    pass
            except Exception as e:
                logging.info("Exception in notice_contract_type_1: {}".format(type(e).__name__))
                pass

            try:
                notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Oggetto e entità della commessa")]//following::dl[1]').text
                notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
            except Exception as e:
                logging.info("Exception in local_description_1: {}".format(type(e).__name__))
                pass

            try:
                notice_data.related_tender_id = page_details.find_element(By.XPATH, '//*[contains(text(),"Informazioni per la pubblicazione della domanda")]//following::dl[1]').text.split('Numero della pubblicazione')[1].split('\n')[0].strip()
            except Exception as e:
                logging.info("Exception in related_tender_id_1: {}".format(type(e).__name__))
                pass 


 #******************************************* FORMAT 2 ****************************************************** 

        elif '1.1 Offizieller Name und Adresse des Auftraggebers' in notice_data.notice_text:

            try:              
                customer_details_data = customer_details()
                customer_details_data.org_country = 'CH'
                customer_details_data.org_language = notice_data.main_language

                customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Bedarfsstelle/Vergabestelle:")]//parent::dd[1]').text.split('Bedarfsstelle/Vergabestelle:')[1].split('\n')[0].strip()

                try:
                    customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Bedarfsstelle/Vergabestelle:")]//parent::dd[1]').text.split("Beschaffungsstelle/Organisator:")[1].split('Telefon')[0].strip()
                except Exception as e:
                    logging.info("Exception in org_address_2: {}".format(type(e).__name__)) 
                    pass

                try:
                    customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Bedarfsstelle/Vergabestelle:")]//parent::dd[1]').text.split("Telefon:")[1].split(',')[0].strip()
                except Exception as e:
                    logging.info("Exception in org_phone_2: {}".format(type(e).__name__)) 
                    pass

                try:
                    org_email1 = page_details.find_element(By.XPATH, '//*[contains(text(),"Bedarfsstelle/Vergabestelle:")]//parent::dd[1]').text#.split("E-Mail:")[1].split('E-mail:')[1].strip()
                    if 'E-Mail' in org_email1:
                        org_email = org_email1.split("E-Mail:")[1].strip()
                    elif 'E-mail' in org_email1:
                        org_email = org_email1.split('E-mail:')[1].strip()
                    email_regex = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b')
                    customer_details_data.org_email = email_regex.findall(org_email)[0]
                except Exception as e:
                    logging.info("Exception in org_email_2: {}".format(type(e).__name__)) 
                    pass

                try:
                    customer_details_data.org_website = page_details.find_element(By.XPATH, '//*[contains(text(),"Bedarfsstelle/Vergabestelle:")]//parent::dd[1]').text.split("URL")[1].split('\n')[0].strip()
                except Exception as e:
                    logging.info("Exception in org_website_2: {}".format(type(e).__name__)) 
                    pass

                try:
                    customer_details_data.type_of_authority_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Art des Auftraggebers")]//following::dl[1]').text
                except Exception as e:
                    logging.info("Exception in type_of_authority_code_2: {}".format(type(e).__name__)) 
                    pass 


                customer_details_data.customer_details_cleanup()
                notice_data.customer_details.append(customer_details_data)
            except Exception as e:
                logging.info("Exception in customer_details_2: {}".format(type(e).__name__)) 
                pass

            try:
                notice_data.type_of_procedure_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Verfahrensart")]//following::dl[1]').text
                type_of_procedure_actual = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
                type_of_procedure  = type_of_procedure_actual.lower()
                notice_data.type_of_procedure = fn.procedure_mapping("assets/ch_simap_procedure.csv",type_of_procedure)
            except Exception as e:
                logging.info("Exception in type_of_procedure_actual_2: {}".format(type(e).__name__))
                pass

            try: 
                notice_data.contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Auftragsart")]//following::dl[1]').text
                if "Bauauftrag" in notice_data.contract_type_actual:
                    notice_data.notice_contract_type = "Works"
                elif "Dienstleistungsauftrag" in notice_data.contract_type_actual:
                    notice_data.notice_contract_type = "Service"
                elif "Lieferauftrag" in notice_data.contract_type_actual or 'Wettbewerb' in notice_data.contract_type_actual:
                    notice_data.notice_contract_type = "Supply"
                else:
                    pass
            except Exception as e:
                logging.info("Exception in notice_contract_type_2: {}".format(type(e).__name__))
                pass

            try:
                notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Gegenstand und Umfang des Auftrags")]//following::dl[1]').text
                notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
            except Exception as e:
                logging.info("Exception in local_description_2: {}".format(type(e).__name__))
                pass

            try:
                notice_data.related_tender_id = page_details.find_element(By.XPATH, '//*[contains(text(),"Angaben zur Publikation der Ausschreibung")]//following::dl[1]').text.split('Meldungsnummer')[1].split('\n')[0].strip()
            except:
                try:
                    notice_data.related_tender_id = page_details.find_element(By.XPATH, '//*[contains(text(),"Referenznummer der Bekanntmachung")]//following::dl[1]').text.split('Meldungsnummer')[1].split('\n')[0].strip()
                except Exception as e:
                    logging.info("Exception in related_tender_id_2: {}".format(type(e).__name__))
                    pass 

#******************************************* FORMAT 3 ****************************************************** 

        elif '1.1 Nom officiel et adresse du pouvoir adjudicateur' in notice_data.notice_text:

            try:              
                customer_details_data = customer_details()
                customer_details_data.org_country = 'CH'
                customer_details_data.org_language = notice_data.main_language

                customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Service demandeur/Entité adjudicatrice:")]//parent::dd[1]').text.split('Service demandeur/Entité adjudicatrice:')[1].split('\n')[0].strip()

                try:
                    customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Service demandeur/Entité adjudicatrice:")]//parent::dd[1]').text.split("Service organisateur/Entité organisatrice:")[1].split('Téléphone:')[0].strip()
                except Exception as e:
                    logging.info("Exception in org_address_3: {}".format(type(e).__name__)) 
                    pass

                try:
                    customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Service demandeur/Entité adjudicatrice:")]//parent::dd[1]').text.split("Téléphone:")[1].split(',')[0].strip()
                except Exception as e:
                    logging.info("Exception in org_phone_3: {}".format(type(e).__name__)) 
                    pass 

                try:
                    org_email1 = page_details.find_element(By.XPATH, '//*[contains(text(),"Service demandeur/Entité adjudicatrice:")]//parent::dd[1]').text#.split("E-mail:")[1].strip()
                    if 'E-Mail' in org_email1:
                        org_email = org_email1.split("E-Mail:")[1].strip()
                    elif 'E-mail' in org_email1:
                        org_email = org_email1.split('E-mail:')[1].strip()
                    email_regex = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b')
                    customer_details_data.org_email = email_regex.findall(org_email)[0]
                except Exception as e:
                    logging.info("Exception in org_email_3: {}".format(type(e).__name__)) 
                    pass

                try:
                    customer_details_data.type_of_authority_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Genre de pouvoir adjudicateur")]//following::dl[1]').text
                except Exception as e:
                    logging.info("Exception in type_of_authority_code_3: {}".format(type(e).__name__)) 
                    pass 

                customer_details_data.customer_details_cleanup()
                notice_data.customer_details.append(customer_details_data)
            except Exception as e:
                logging.info("Exception in customer_details_3: {}".format(type(e).__name__)) 
                pass

            try:
                notice_data.type_of_procedure_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Mode de procédure choisi")]//following::dl[1]').text
                type_of_procedure_actual = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
                type_of_procedure  = type_of_procedure_actual.lower()
                notice_data.type_of_procedure = fn.procedure_mapping("assets/ch_simap_procedure.csv",type_of_procedure)
            except Exception as e:
                logging.info("Exception in type_of_procedure_actual_3: {}".format(type(e).__name__))
                pass

            try: 
                notice_data.contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Genre de marché")]//following::dl[1]').text
                if "Travaux" in notice_data.contract_type_actual or 'Marché de travaux de construction' in notice_data.contract_type_actual:
                    notice_data.notice_contract_type = "Works"
                elif "Marché de services" in notice_data.contract_type_actual:
                    notice_data.notice_contract_type = "Service"
                elif "Marché de fournitures" in notice_data.contract_type_actual:
                    notice_data.notice_contract_type = "Supply"
                else:
                    pass
            except Exception as e:
                logging.info("Exception in notice_contract_type_3: {}".format(type(e).__name__))
                pass

            try:
                notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Objet et étendue du marché")]//following::dl[1]').text
                notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
            except Exception as e:
                logging.info("Exception in local_description_3: {}".format(type(e).__name__))
                pass

            try: 
                notice_data.related_tender_id = page_details.find_element(By.XPATH, '''//*[contains(text(),"Informations pour la publication de l'avis de marché")]//following::dl[1]''').text.split('Numéro de la publication')[1].split('\n')[0].strip()
            except:
                try:
                    notice_data.related_tender_id = page_details.find_element(By.XPATH, '''//*[contains(text(),"Numéro de la publication")]//following::dl[1]''').text.split('Numéro de la publication')[1].split('\n')[0].strip()
                except Exception as e:
                    logging.info("Exception in related_tender_id_3: {}".format(type(e).__name__))
                    pass 
        
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) + str(notice_data.publish_date) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments) 
page_details =fn.init_chrome_driver(arguments)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.simap.ch/shabforms/COMMON/application/applicationGrid.jsp?template=2&view=1&page=/MULTILANGUAGE/simap/content/start.jsp"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)  
        
        sub_url = page_main.find_element(By.CSS_SELECTOR, '#formShab > div:nth-child(2) > a:nth-child(10)').get_attribute("href")
        fn.load_page(page_main,sub_url,80)
        logging.info(sub_url)

        fn.load_page(page_details,sub_url,80)
    
        try:
            for page_no in range(2,5):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#resultList > tbody > tr:nth-child(3)'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#resultList > tbody > tr')))
                length = len(rows)
                for records in range(1,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#resultList > tbody > tr')))[records]
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
                    time.sleep(5)
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#resultList > tbody > tr:nth-child(3)'),page_check))
                except Exception as e:
                    logging.info("Exception in next_page: {}".format(type(e).__name__))
                    logging.info("No next page")
                    break
        except:
            logging.info("No new record")
            break
            
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit() 
    output_json_file.copyFinalJSONToServer(output_json_folder)
