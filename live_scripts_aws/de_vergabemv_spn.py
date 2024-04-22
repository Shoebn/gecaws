from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "de_vergabemv_spn"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from selenium import webdriver
from gec_common import functions as fn
from deep_translator import GoogleTranslator

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "de_vergabemv_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"

def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'de_vergabemv_spn'
    
    notice_data.main_language = 'DE'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'DE'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.procurement_method = 2
    
    notice_data.currency = 'EUR'
    
    notice_data.notice_type = 4
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
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
        notice_data.type_of_procedure_actual = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text
        type_of_procedure_actual = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("assets/de_vergabemv_procedure.CSV",type_of_procedure_actual)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(6)").text
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
        org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
    except:
        pass
    
    try:
        notice_url_no = tender_html_element.get_attribute("data-oid")
        notice_data.notice_url = "https://vergabe.mv-regierung.de/NetServer/PublicationControllerServlet?function=Detail&TOID="+notice_url_no+"&Category=InvitationToTender"
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__)) 
        pass

    try:
        fn.load_page(page_details,notice_data.notice_url,60)
        logging.info(notice_data.notice_url)

        try:
            notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#pagePublicationDetails').get_attribute("outerHTML")                     
        except:
            pass

        try:
            notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"Vergabenummer:")]//following::td[1]').text
        except:
            try:
                notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"Vergabenr.")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in notice_no: {}".format(type(e).__name__))
                pass

        try:             
            customer_details_data = customer_details()
            customer_details_data.org_country = 'DE'
            customer_details_data.org_language = 'DE'

            customer_details_data.org_name = org_name

            try:
                org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Name und Anschrift:")]//following::td[1]').text
                if len(org_address) > 2:
                    customer_details_data.org_address = org_address
            except:
                try:
                    org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Beschaffer")]//following::td[1]').text.split('Offizielle Bezeichnung:')[1].split('Kontaktstelle:')[0].strip()
                    if len(org_address) > 2:
                        customer_details_data.org_address = org_address
                except Exception as e:
                    logging.info("Exception in org_address: {}".format(type(e).__name__)) 
                    pass

            try:
                contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Kontaktstelle (Ansprechpartner):")]//following::td[1]').text           
                if len(contact_person) > 2:
                    customer_details_data.contact_person = contact_person
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__)) 
                pass

            try:
                org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"E-Mail:")]//following::td[1]').text            
                if len(org_email) > 2:
                    email_regex = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b')
                    customer_details_data.org_email = email_regex.findall(org_email)[0]
            except:
                try:
                    org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"E-Mail-Adresse:")]//following::td[1]').text            
                    if len(org_email) > 2:
                        email_regex = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b')
                        customer_details_data.org_email = email_regex.findall(org_email)[0]

                except:
                    try:
                        org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Beschaffer")]//following::td[1]').text         
                        if len(org_email) > 2:
                            email_regex = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b')
                            customer_details_data.org_email = email_regex.findall(org_email)[0]
                    except Exception as e:
                        logging.info("Exception in org_email: {}".format(type(e).__name__)) 
                        pass

            try:
                org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Telefon:")]//following::td[1]').text         
                if len(org_phone) > 2:
                    customer_details_data.org_phone = org_phone
            except:
                try:
                    org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Telefonnummer:")]//following::td[1]').text         
                    if len(org_phone) > 2:
                        customer_details_data.org_phone = org_phone
                except:
                    try:
                        org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Beschaffer")]//following::td[1]').text.split('Telefon:')[1].split('\n')[0].strip()
                        if len(org_phone) > 2:
                            customer_details_data.org_phone = org_phone
                    except Exception as e:
                        logging.info("Exception in org_phone: {}".format(type(e).__name__)) 
                        pass

            try:
                org_fax = page_details.find_element(By.XPATH, '//*[contains(text(),"Fax:")]//following::td[1]').text           
                if len(org_fax) > 2:
                    customer_details_data.org_fax = org_fax
            except:
                try:
                    org_fax = page_details.find_element(By.XPATH, '//*[contains(text(),"Telefaxnummer:")]//following::td[1]').text           
                    if len(org_fax) > 2:
                        customer_details_data.org_fax = org_fax
                except:
                    try:
                        org_fax = page_details.find_element(By.XPATH, '//*[contains(text(),"Beschaffer")]//following::td[1]').text.split('Fax:')[1].split('\n')[0].strip()          
                        if len(org_fax) > 2:
                            customer_details_data.org_fax = org_fax
                    except Exception as e:
                        logging.info("Exception in org_fax: {}".format(type(e).__name__)) 
                        pass

            try:
                org_website = page_details.find_element(By.XPATH, '//*[contains(text(),"Internet:")]//following::td[1]').text           
                if len(org_website) > 2:
                    customer_details_data.org_website = org_website
            except:
                try:
                    org_website = page_details.find_element(By.XPATH, '//*[contains(text(),"Internet-Adresse:")]//following::td[1]').text           
                    if len(org_website) > 2:
                        customer_details_data.org_website = org_website
                except:
                    try:
                        org_website = page_details.find_element(By.XPATH, '//*[contains(text(),"Beschaffer")]//following::td[1]').text.split('Internet-Adresse (URL):')[1].split('\n')[0].strip()          
                        if len(org_website) > 2:
                            customer_details_data.org_website = org_website
                    except Exception as e:
                        logging.info("Exception in org_website: {}".format(type(e).__name__)) 
                        pass 

            try:
                type_of_authority_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Beschaffer")]//following::td[1]').text.split('Art des öffentlichen Auftraggebers:')[1].split('\n')[0].strip()          
                if len(type_of_authority_code) > 2:
                    customer_details_data.type_of_authority_code = type_of_authority_code
            except Exception as e:
                logging.info("Exception in type_of_authority_code: {}".format(type(e).__name__)) 
                pass 

            try:
                customer_main_activity = page_details.find_element(By.XPATH, '//*[contains(text(),"Beschaffer")]//following::td[1]').text.split('Haupttätigkeiten des öffentlichen Auftraggebers:')[1].split('\n')[0].strip()          
                if len(customer_main_activity) > 2:
                    customer_details_data.customer_main_activity = customer_main_activity
            except Exception as e:
                logging.info("Exception in customer_main_activity: {}".format(type(e).__name__)) 
                pass 

            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
        except Exception as e:
            logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
            pass

        try:
            notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Umfang der Beschaffung:")]//following::td[1]').text
            notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
        except:
            try:
                notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Beschreibung der Beschaffung")]//following::td[1]').text
                notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
            except:
                try:
                    notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Umfang der Leistung:")]//following::td[1]').text
                    notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
                except Exception as e:
                    logging.info("Exception in local_description: {}".format(type(e).__name__))
                    pass

        try:
            est_amount = page_details.find_element(By.XPATH, '//*[contains(text(),"Geschätzter Gesamtwert (netto):")]//following::td[1]').text
            est_amount = re.sub("[^\d\.\,]","",est_amount)
            notice_data.est_amount =float(est_amount.replace(',','.').replace('.','').strip())
            notice_data.netbudgetlc = notice_data.est_amount
        except Exception as e:
            logging.info("Exception in netbudgetlc: {}".format(type(e).__name__))
            pass 

        try:
            cpv_at_source = ''
            try:                   
                code = page_details.find_element(By.XPATH,'//*[contains(text(),"CPV-Code:")]//following::td[1]').text
            except:
                code = page_details.find_element(By.XPATH,'//*[contains(text(),"CPV-Code Hauptteil:")]//parent::td[1]').text
            cpv_regex = re.compile(r'\d{8}')
            lot_cpv = cpv_regex.findall(code)
            for cpv in lot_cpv:
                cpvs_data = cpvs()

                cpv_at_source += cpv
                cpv_at_source += ','

                cpvs_data.cpv_code = cpv

                cpvs_data.cpvs_cleanup()
                notice_data.cpvs.append(cpvs_data)

            notice_data.cpv_at_source = cpv_at_source.rstrip(',')
        except Exception as e:
            logging.info("Exception in cpv_code: {}".format(type(e).__name__))
            pass

        try: 
            notice_data.contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Vertragsart:")]//following::td[1]').text
            if 'Dienstleistung' in notice_data.contract_type_actual:
                notice_data.notice_contract_type = 'Service' 
            elif 'Lieferleistung' in notice_data.contract_type_actual:
                notice_data.notice_contract_type = 'Supply'
        except Exception as e:
            logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
            pass

        try:
            tender_contract_start_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Beginn der Ausführung:")]//following::td[1]').text
            tender_contract_start_date = re.findall('\d+.\d+.\d{4}',tender_contract_start_date)[0]
            notice_data.tender_contract_start_date = datetime.strptime(tender_contract_start_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.tender_contract_start_date)
        except Exception as e:
            logging.info("Exception in tender_contract_start_date: {}".format(type(e).__name__))
            pass

        try:
            tender_contract_end_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Fertigstellung oder Dauer der Leistungen:")]//following::td[1]').text
            tender_contract_end_date = re.findall('\d+.\d+.\d{4}',tender_contract_end_date)[0]
            notice_data.tender_contract_end_date = datetime.strptime(tender_contract_end_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.tender_contract_end_date)
        except Exception as e:
            logging.info("Exception in tender_contract_end_date: {}".format(type(e).__name__))
            pass

        try:
            funding_agency = page_details.find_element(By.XPATH, '//*[contains(text(),"Use of EU funds")]//following::td[1]').text
            funding_agency = GoogleTranslator(source='auto', target='en').translate(funding_agency)
            funding_agency1 = funding_agency.lower()
            if 'yes' in funding_agency1:
                funding_agencies_data = funding_agencies()
                funding_agencies_data.funding_agency = 1344862
                funding_agencies_data.funding_agencies_cleanup()
                notice_data.funding_agencies.append(funding_agencies_data)
        except Exception as e:
            logging.info("Exception in funding_agency: {}".format(type(e).__name__))
            pass

        try:
            criteria_title = page_details.find_element(By.XPATH, '//*[contains(text(),"Zuschlagskriterien")]//following::td[1]').text
            if criteria_title != '':
                tender_criteria_data = tender_criteria()
                tender_criteria_data.tender_criteria_title = criteria_title.split(':')[0].strip()

                if "price" in tender_criteria_data.tender_criteria_title.lower():
                    tender_criteria_data.tender_is_price_related = True

                tender_criteria_weight = criteria_title.split(':')[1].split(',')[0].strip()
                tender_criteria_data.tender_criteria_weight = int(tender_criteria_weight)

                tender_criteria_data.tender_criteria_cleanup()
                notice_data.tender_criteria.append(tender_criteria_data)    
        except Exception as e:
            logging.info("Exception in lot_criteria: {}".format(type(e).__name__))
            pass

        try:
            attachment_url = page_details.find_element(By.XPATH, '//*[contains(text(),"Unterlagen zur Ansicht herunterladen")]//parent::div[1]/a').get_attribute("href")
            fn.load_page(page_details1,attachment_url,60)
            logging.info(attachment_url)

            try:
                notice_data.notice_text += page_details1.find_element(By.CSS_SELECTOR, '#pageParticipantDetailsGuest').get_attribute("outerHTML")                     
            except:
                pass

            try:   
                click = WebDriverWait(page_details1, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"#pageParticipantDetailsGuest > div.content.border > div > div:nth-child(7) > div > table > tbody > tr > td:nth-child(3) > a > i")))
                page_details1.execute_script("arguments[0].click();",click)
                time.sleep(10) 

                WebDriverWait(page_details1, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#downloadSelection > div.folderBox > div')))

                for single_record in page_details1.find_elements(By.CSS_SELECTOR, '#downloadSelection > div.folderBox > div > a')[1:]:

                    attachments_data = attachments()

                    attachments_data.external_url = single_record.get_attribute('href')

                    attachments_data.file_name = single_record.text

                    if attachments_data.external_url != None:
                        attachments_data.attachments_cleanup()
                        notice_data.attachments.append(attachments_data)

                back_click = WebDriverWait(page_details1, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="buttonModalClose"]')))
                page_details1.execute_script("arguments[0].click();",back_click)
                time.sleep(5)

            except Exception as e:
                logging.info("Exception in attachments: {}".format(type(e).__name__)) 
                pass

        except Exception as e:
            logging.info("Exception in attachment_url: {}".format(type(e).__name__))
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
page_details1 =fn.init_chrome_driver(arguments)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://vergabe.mv-regierung.de/NetServer/PublicationSearchControllerServlet?function=SearchPublications&Gesetzesgrundlage=All&Category=InvitationToTender&thContext=publications"] 
    for url in urls:
        fn.load_page(page_main, url, 80)
        logging.info('----------------------------------')
        logging.info(url) 
            
        try:
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'table.table.table-responsive.table-striped.table-hover.tableHorizontalHeader > tbody > tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'table.table.table-responsive.table-striped.table-hover.tableHorizontalHeader > tbody > tr')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break  

                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
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
    page_details1.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)
