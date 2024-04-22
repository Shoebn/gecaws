from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "it_agenziademanio"
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
SCRIPT_NAME = "it_agenziademanio"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    notice_data.main_language = 'IT'
    notice_data.currency = 'EUR'
    notice_data.procurement_method = 2
    notice_data.notice_type = 4
    notice_data.script_name = "it_agenziademanio"
    notice_data.document_type_description="Progettazione e Lavori"
    notice_data.local_description=notice_data.local_title
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
    notice_data.performance_country.append(performance_country_data)
    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'h2 a').get_attribute('href')
        fn.load_page(page_details, notice_data.notice_url, 50)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        pass
    logging.info(notice_data.notice_url )
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'h2 a').text
        notice_data.notice_title = GoogleTranslator(source='it', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in notice_title: {}".format(type(e).__name__))
        pass
  
    try:
        tender_criteria_title = page_details.find_element(By.CSS_SELECTOR, 'div > p.criterio').text.split(':')[1]
        if tender_criteria_title != '':
            tender_criteria_data = tender_criteria()
            tender_criteria_data.tender_criteria_title = tender_criteria_title
            tender_criteria_data.tender_criteria_weight = 100
            tender_criteria_data.tender_criteria_cleanup()
            notice_data.tender_criteria.append(tender_criteria_data)    
    except Exception as e:
        logging.info("Exception in lot_criteria: {}".format(type(e).__name__))
        pass

   
    try:
    
        lot_details_data = lot_details() 
        lot_details_data.lot_number=1
        lot_details_data.lot_title = notice_data.notice_title
        notice_data.is_lot_default = True

        try:
            lot_details_data.lot_quantity_uom = page_details.find_element(By.CSS_SELECTOR, 'p.lotti').text.split("N. di lotti in gara:")[1].strip()
        except Exception as e:
            logging.info("Exception in lot_details: {}".format(type(e).__name__))
            pass
        try:
            lot_grossbudget = page_details.find_element(By.CSS_SELECTOR, 'div > p.importo').text.split("Importo a base d'asta dell'appalto:")[1].split('(')[0].strip()
            lot_grossbudget = re.sub("[^\d\.\,]", "",lot_grossbudget)
            lot_details_data.lot_grossbudget = float(lot_grossbudget.replace('.','').replace(',','.').strip())
        except Exception as e:
            logging.info("Exception in lot_grossbudget: {}".format(type(e).__name__))
            pass


        try:              
            lot_criteria_data = lot_criteria()
            lot_criteria_data.lot_criteria_title = tender_criteria_data.tender_criteria_title 
            lot_criteria_data.lot_criteria_weight = 100
            lot_criteria_data.lot_criteria_cleanup()
            lot_details_data.lot_criteria.append(lot_criteria_data)
        except Exception as e:
            logging.info("Exception in lot_criteria: {}".format(type(e).__name__)) 
            pass
        
        lot_details_data.lot_details_cleanup()
        notice_data.lot_details.append(lot_details_data)

    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass

  
    try:
        publish_date = tender_html_element.text.split('Data Pubblicazione bando: ')[1].split('\n')[0]
        publish_date = GoogleTranslator(source='it', target='en').translate(publish_date)
        try:
            publish_date = re.findall('\w+ \d+, \d{4}',publish_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date,'%B %d, %Y').strftime('%Y/%m/%d')
            logging.info(notice_data.publish_date)
        except:
            publish_date = re.findall('\d+ \w+ \d{4}',publish_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date,'%d %B %Y').strftime('%Y/%m/%d')
            
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
    logging.info(notice_data.publish_date)
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
        
    try:
        notice_deadline = tender_html_element.text.split('Termine per partecipare: ')[1].split('\n')[0]
        notice_deadline = GoogleTranslator(source='it', target='en').translate(notice_deadline)
        try:
            notice_deadline = re.findall('\w+ \d+, \d{4}',notice_deadline)[0]
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%B %d, %Y').strftime('%Y/%m/%d %H:%M:%S')
        except:
            notice_deadline = re.findall('\d+ \w+ \d{4}',notice_deadline)[0]
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d %B %Y').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_no = tender_html_element.text.split('CIG: ')[1].split(' ')[0] 
        if '\nRegione:' in notice_data.notice_no:
            notice_data.notice_no = notice_data.notice_no.replace('\nRegione:','')
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
  
    try:
        est_amount = page_details.find_element(By.CSS_SELECTOR, 'div > p.importo').text
        try:
            est_amount = re.findall(r'€ \d+.\d+,\d+',est_amount)[0].split('€')[1] 
        except:
            try:
                est_amount = re.findall(r'€ \d+.\d+,\d+',est_amount).split('€')[1]
            except:
                est_amount = re.findall(r'Euro \d+.\d+,\d+',est_amount).split('Euro')[1]
        notice_data.est_amount = float(est_amount.replace('.','').replace(',','.').strip())  
        notice_data.grossbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    

    customer_details_data = customer_details()
    customer_details_data.org_name = 'Agenzia del Demanio'
    customer_details_data.org_country = 'IT'

    try:
        customer_details_data.contact_person = page_details.find_element(By.CSS_SELECTOR, 'div > p.nominativo').text.split(':')[1]
    except Exception as e:
        logging.info("Exception in org_state: {}".format(type(e).__name__))
        pass

    try:
        customer_details_data.org_state = page_details.find_element(By.CSS_SELECTOR, 'div > p.regione').text.split('Regione:')[1]
    except Exception as e:
        logging.info("Exception in org_state: {}".format(type(e).__name__))
        pass

    try:
        customer_details_data.org_city = page_details.find_element(By.CSS_SELECTOR, 'div > p.provincia').text.split('Provincia:')[1]
    except Exception as e:
        logging.info("Exception in org_city: {}".format(type(e).__name__))
        pass
        
    try:
        customer_details_data.org_address = page_details.find_element(By.CSS_SELECTOR, 'div > p.comune').text.split('Comune:')[1]
    except Exception as e:
        logging.info("Exception in org_address: {}".format(type(e).__name__))
        pass

    try:
        customer_details_data.org_email = page_details.find_element(By.CSS_SELECTOR, 'div > p.email').text.split('Indirizzo email istituzionale del responsabile del procedimento:')[1].replace(';','').strip()
    except Exception as e:
        logging.info("Exception in org_email: {}".format(type(e).__name__))
        pass

    try:
        customer_details_data.org_description = page_details.find_element(By.CSS_SELECTOR, 'div > p.nominativo').text
    except Exception as e:
        logging.info("Exception in org_description: {}".format(type(e).__name__))
        pass
            
    customer_details_data.customer_details_cleanup()
    notice_data.customer_details.append(customer_details_data)

    try:
        notice_data.notice_text += page_details.find_element(By.XPATH, '//*[@id="contenuti"]').get_attribute('outerHTML')
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.documentigara p'):
            attachments_data = attachments()
            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'div.documentigara p > a').get_attribute('href')
            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'div.documentigara p > a').text
            attachments_data.file_description = single_record.text
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.type_of_procedure_actual = page_details.find_element(By.CSS_SELECTOR, 'div > p.tipologia').text
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    notice_data.identifier = str(notice_data.notice_no) + str(notice_data.publish_date) +  str(notice_data.notice_url) 
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
    
    urls = ['https://www.agenziademanio.it/opencms/it/gare-aste/lavori?p=',
           'https://www.agenziademanio.it/it/gare-aste/immobiliare/?p=',
           'https://www.agenziademanio.it/it/gare-aste/forniture-e-servizi/?p=',
           'https://www.agenziademanio.it/it/gare-aste/beni-mobili-e-veicoli-confiscati/?p=']
        
        
    for url2 in urls:
        for page_no in range(1,7):
            url= url2 + str(page_no)
            fn.load_page(page_main, url)
            logging.info('----------------------------------')           
            logging.info(url)

            try:
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.card-body.archivioGare'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.card-body.archivioGare')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.card-body.archivioGare')))[records]
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
