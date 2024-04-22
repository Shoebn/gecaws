from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "it_sardegna"
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
SCRIPT_NAME = "it_sardegna"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'it_sardegna'
    
    notice_data.main_language = 'IT'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.procurement_method = 2
    
    notice_data.currency = 'EUR'
    
    notice_data.notice_type = 4
    
    # Onsite Field -Bandi e gare
    # Onsite Comment -None

    try:
        notice_data.document_type_description = page_main.find_element(By.CSS_SELECTOR, 'div.col-12.col-md-8.order-1.order-md-1.mb-3.mb-md-3.acs > h1').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(1) div > h5').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
        if 'expression of interest' in notice_data.notice_title or 'EXPRESSION OF INTEREST' in notice_data.notice_title:
            notice_data.notice_type = 5
        elif 'Notice Of contract awarded' in notice_data.notice_title or 'procedure for awarding' in notice_data.notice_title or 'Awarded contract notice' in notice_data.notice_title:
            notice_data.notice_type = 7
        else:
            pass
            
        if 'Procedura aperta' in notice_data.local_title:
            notice_data.type_of_procedure_actual = 'Procedura aperta'
            notice_data.type_of_procedure = 'Other'
        elif 'Procedura negoziata' in notice_data.local_title:
            notice_data.type_of_procedure_actual = 'Procedura negoziata'
            notice_data.type_of_procedure = 'Negotiated procedure'
        else:
            notice_data.type_of_procedure_actual = 'Other'
            notice_data.type_of_procedure = 'Other'
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass


    # Onsite Field -Data di pubblicazione
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div:nth-child(7) > div > div > div:nth-child(1) > div > div:nth-child(2) > div").text
        publish_date = GoogleTranslator(source='it', target='en').translate(publish_date)
        publish_date = re.findall('\w+ \d+, \d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%B %d, %Y').strftime('%Y/%m/%d')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Data scadenza
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "div:nth-child(2) > div > div:nth-child(2)").text
        notice_deadline = GoogleTranslator(source='auto', target='en').translate(notice_deadline)
        notice_deadline = re.findall('\w+ \d+, \d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%B %d, %Y').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Tipologia
    # Onsite Comment -for "Servizi = services, Lavori pubblici =Works, FORNITURE =SUPPLIES, LAVORI= JOBS, "  as there are various types

    try:
        notice_contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'div > div.mt-4.typology > div').text
        if 'SERVIZI' in notice_contract_type or 'LAVORI' in notice_contract_type :
            notice_data.notice_contract_type = 'Service'
        if 'LAVORI PUBBLICI' in notice_contract_type:
            notice_data.notice_contract_type = 'Works'
        if 'FORNITURE' in notice_contract_type:
            notice_data.notice_contract_type = 'Supply'
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div > h5 > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except:
        notice_data.notice_url = url
    try:
        notice_data.notice_no=notice_data.notice_url.split('amministrativi/')[1]
    except:
        pass
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.XPATH, '//*[@id="mainContent"]/div[4]').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div > div.col-12.col-md-8 > div'):
            customer_details_data = customer_details()
        # Onsite Field -Struttura di riferimento
        # Onsite Comment -None
            try:
                customer_details_data.org_name = single_record.find_element(By.CSS_SELECTOR, '#strutture-di-riferimento > section > div > a > span').text
            except:
                customer_details_data.org_name='Regione Autonoma della Sardegna'
            customer_details_data.org_language='IT'
        
            customer_details_data.org_country = 'IT'
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.document-card-line.attachment'):
            attachments_data = attachments()
            attachments_data.file_type = 'pdf'
        # Onsite Field -eg " Bando di gara", "Capitolato", "Perizia di stima"
        # Onsite Comment -None

            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'div.description > a').text.split('PDF')[0].strip()
           
        
        # Onsite Field -None
        # Onsite Comment -None

            try:
                attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'div.description > a').get_attribute('href')
            except Exception as e:
                logging.info("Exception in external_url: {}".format(type(e).__name__))
                pass
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
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
    urls = ['https://www.regione.sardegna.it/atti-bandi-archivi/atti-soggetti-esterni/bandi-e-gare?size=n_12_n&sort%5B0%5D%5Bfield%5D=dataPubblicazione&sort%5B0%5D%5Bdirection%5D=desc'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(1,5):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[1]/div/main/div/div[4]/div/div[3]/div[3]/div/div/div[1]/div'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/div/main/div/div[4]/div/div[3]/div[3]/div/div/div/div')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/div/main/div/div[4]/div/div[3]/div[3]/div/div/div/div')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
        
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="mainContent"]/div/div[4]/div/div[4]/div/div[1]/div/nav/ul/li[11]/button')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/div[1]/div/main/div/div[4]/div/div[3]/div[3]/div/div/div[1]/div'),page_check))
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
