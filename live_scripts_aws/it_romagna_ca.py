from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "it_romagna_ca"
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
SCRIPT_NAME = "it_romagna_ca"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'it_romagna_ca'
    notice_data.main_language = 'IT'
    notice_data.currency = 'EUR'
    notice_data.procurement_method = 2
    
    # Onsite Field -for "Rinnovi ed estensioni" keyword take notice type 16
    # Onsite Comment -ref url "https://intercenter.regione.emilia-romagna.it/servizi-pa/convenzioni/convenzioni-attive/2023/fattore-viii-2023-2013-2025-esclusivi"
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -Data di attivazione
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(2) > div").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Convenzioni
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -Convenzioni

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1) a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url

    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#portal-column-content > div').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
        
    if "Rinnovi ed estensioni" in notice_data.notice_text:
        notice_data.notice_type = 16
    else:
        notice_data.notice_type = 7
        
        
    # Onsite Field -Durata degli Ordinativi
    # Onsite Comment -take the following data from where the  xpath is been selected
#     import pdb;pdb.set_trace()
    try:
        notice_data.contract_duration = page_details.find_element(By.XPATH, "//*[contains(text(),'Durata degli Ordinativi')]/..").text.split('Durata degli Ordinativi:')[1].strip()
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -for format 2 : "https://intercenter.regione.emilia-romagna.it/servizi-pa/convenzioni/convenzioni-attive/2023/servizi-di-collaudo-per-le-aziende-sanitarie-rer-per-interventi-pnrr"  use selector "//*[contains(text(),'Referente amministrativo')]"

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_language = 'IT'
        customer_details_data.org_country = 'IT'
    # Onsite Field -
    # Onsite Comment -take the following data from where the xpath is been selected 

        customer_details_data.org_name = page_details.find_element(By.XPATH, "//*[contains(text(),'Destinatari')]/..").text.split('Destinatari:')[1].strip()
        
        # Onsite Field - ref url - "https://intercenter.regione.emilia-romagna.it/servizi-pa/convenzioni/convenzioni-attive/2022/aghi-per-anestesia"
        # Onsite Comment -split data from"Referenti amministrativi:"till "tel"
        try:
            contact_person = page_details.find_element(By.XPATH, "//*[contains(text(),'Referenti amministrativi:')]/..").text
            if '–' in contact_person:
                customer_details_data.contact_person = contact_person.split(':')[1].split('–')[0].strip()
            elif '-' in contact_person:
                customer_details_data.contact_person = contact_person.split(':')[1].split('-')[0].strip()
        except:
            try:
                contact_person = page_details.find_element(By.XPATH, "//*[contains(text(),'Referenti amministrativi:')]//following::li[1]").text
                if '–' in contact_person:
                    customer_details_data.contact_person = contact_person.split(':')[1].split('–')[0].strip()
                elif '-' in contact_person:
                    customer_details_data.contact_person = contact_person.split(':')[1].split('-')[0].strip()
            except:
                try:
                    contact_person = page_details.find_element(By.XPATH, "//*[contains(text(),'Referente amministrativo')]/..").text
                    if '–' in contact_person:
                        customer_details_data.contact_person = contact_person.split(':')[1].split('–')[0].strip()
                    elif '-' in contact_person:
                        customer_details_data.contact_person = contact_person.split(':')[1].split('-')[0].strip()
                except Exception as e:
                    logging.info("Exception in contact_person: {}".format(type(e).__name__))
                    pass
        
        # Onsite Field - ref url - "https://intercenter.regione.emilia-romagna.it/servizi-pa/convenzioni/convenzioni-attive/2022/aghi-per-anestesia"
        # Onsite Comment -split data from"tel" till "e-mail"
        try:
            org_phone = page_details.find_element(By.XPATH, "//*[contains(text(),'Referenti amministrativi:')]/..").text
            customer_details_data.org_phone = re.sub("[^\d]","",org_phone)
        except:
            try:
                org_phone = page_details.find_element(By.XPATH, "//*[contains(text(),'Referenti amministrativi:')]//following::li[1]").text
                customer_details_data.org_phone = re.sub("[^\d]","",org_phone)
            except:
                try:
                    org_phone = page_details.find_element(By.XPATH, "//*[contains(text(),'Referente amministrativo')]/..").text
                    customer_details_data.org_phone = re.sub("[^\d]","",org_phone)
                except Exception as e:
                    logging.info("Exception in org_phone: {}".format(type(e).__name__))
                    pass
        
        # Onsite Field - ref url - "https://intercenter.regione.emilia-romagna.it/servizi-pa/convenzioni/convenzioni-attive/2022/aghi-per-anestesia"
        # Onsite Comment -split data from"e-mail"
        try:
            org_email = page_details.find_element(By.XPATH, "//*[contains(text(),'Referenti amministrativi:')]/..").text
            customer_details_data.org_email = fn.get_email(org_email)
        except:
            try:
                org_email = page_details.find_element(By.XPATH, "//*[contains(text(),'Referenti amministrativi:')]//following::li[1]").text
                customer_details_data.org_email = fn.get_email(org_email)
            except:
                try:
                    org_email = page_details.find_element(By.XPATH, "//*[contains(text(),'Referente amministrativo')]/..").text
                    customer_details_data.org_email = fn.get_email(org_email)
                except Exception as e:
                    logging.info("Exception in org_email: {}".format(type(e).__name__))
                    pass
        
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -ref url : "https://intercenter.regione.emilia-romagna.it/servizi-pa/convenzioni/convenzioni-attive/2023/medicinali-biologici-e-biosimilari-esclusivi-2023-2024/medicinali-biologici-e-biosimilari-esclusivi-2023-2024"
# Onsite Comment -None

    try:
        lot_number = 1
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#content-core > div.content-text > table > tbody > tr')[1:]:
            if 'Lotto' in single_record.text or 'Lotti' in single_record.text or 'Lot' in single_record.text or 'Lots' in single_record.text:
                lot_details_data = lot_details()
                lot_details_data.lot_number = lot_number
        # Onsite Field -ref url : "https://intercenter.regione.emilia-romagna.it/servizi-pa/convenzioni/convenzioni-attive/2023/medicinali-biologici-e-biosimilari-esclusivi-2023-2024/medicinali-biologici-e-biosimilari-esclusivi-2023-2024"
        # Onsite Comment -None

                lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
                lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
        

        # Onsite Field -Repertoire number
        # Onsite Comment -ref url : "https://intercenter.regione.emilia-romagna.it/servizi-pa/convenzioni/convenzioni-attive/2023/medicinali-biologici-e-biosimilari-esclusivi-2023-2024/medicinali-biologici-e-biosimilari-esclusivi-2023-2024"

                try:
                    lot_details_data.lot_actual_number = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
                except Exception as e:
                    logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                    pass
        
        # Onsite Field -None
        # Onsite Comment -None

                try:
                    award_details_data = award_details()

                    # Onsite Field -Fornitore
                    # Onsite Comment -None

                    award_details_data.bidder_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text

                    # Onsite Field -Data scadenza
                    # Onsite Comment -None
                    try:
                        award_date = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
                        award_date = re.findall('\d+/\d+/\d{4}',award_date)[0]
                        award_details_data.award_date = datetime.strptime(award_date,'%d/%m/%Y').strftime('%Y/%m/%d')
                    except Exception as e:
                        logging.info("Exception in award_date: {}".format(type(e).__name__))
                        pass
                    
                    if notice_data.publish_date is None or notice_data.publish_date=='':
                        notice_data.publish_date = award_details_data.award_date
                        

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

    try:              
        attachments_data = attachments()
    # Onsite Field -Referenti aggiudicatari
    # Onsite Comment -None

        attachments_data.external_url = page_details.find_element(By.XPATH, "//*[contains(text(),'Referenti aggiudicatari')]//following::a[1]").get_attribute('href')

    # Onsite Field -Referenti aggiudicatari
    # Onsite Comment -None

        try:
            attachments_data.file_size = page_details.find_element(By.XPATH, "//*[contains(text(),'Referenti aggiudicatari')]//following::a[1]").text.split('(')[1].split(')')[0].strip()
        except Exception as e:
            logging.info("Exception in file_size: {}".format(type(e).__name__))
            pass
        
    # Onsite Field -Referenti aggiudicatari
    # Onsite Comment -None

        attachments_data.file_name = page_details.find_element(By.XPATH, "//*[contains(text(),'Referenti aggiudicatari')]//following::a[1]").text.split('(')[0].strip()

    # Onsite Field -Referenti aggiudicatari
    # Onsite Comment -None
        try:
            if 'pdf' in attachments_data.external_url.lower():
                attachments_data.file_type = 'pdf'
            elif 'zip' in attachments_data.external_url.lower():
                attachments_data.file_type = 'zip'
            elif 'docx' in attachments_data.external_url.lower():
                attachments_data.file_type = 'docx'
            elif 'xlsx' in attachments_data.external_url.lower():
                attachments_data.file_type = 'xlsx'
            else:
                pass
        except:
            pass

        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    #format 3 : https://intercenter.regione.emilia-romagna.it/servizi-pa/convenzioni/convenzioni-attive/2023/servizi-di-collaudo-per-le-aziende-sanitarie-rer-per-interventi-pnrr

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.subfolders-wrapper > div:nth-child(1) > ul > li'):
            attachments_data = attachments()

            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')

            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'a').text
            
            try:
                if 'pdf' in attachments_data.external_url.lower():
                    attachments_data.file_type = 'pdf'
                elif 'zip' in attachments_data.external_url.lower():
                    attachments_data.file_type = 'zip'
                elif 'docx' in attachments_data.external_url.lower():
                    attachments_data.file_type = 'docx'
                elif 'xlsx' in attachments_data.external_url.lower():
                    attachments_data.file_type = 'xlsx'
                else:
                    pass
            except:
                pass
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass

    if notice_data.publish_date is None:
        notice_data.publish_date = threshold
        
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
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
    urls = ["https://intercenter.regione.emilia-romagna.it/servizi-pa/convenzioni/convenzioni-attive"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)

        try:
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="parent-fieldname-text"]/table/tbody/tr')))
            length = len(rows)
            for records in range(1,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="parent-fieldname-text"]/table/tbody/tr')))[records]
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
