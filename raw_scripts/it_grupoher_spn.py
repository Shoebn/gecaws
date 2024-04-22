from gec_common.gecclass import *
import logging
import re
import jsons
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from deep_translator import GoogleTranslator
from selenium import webdriver
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
import gec_common.web_application_properties
import functions as fn
from functions import ET

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "it_grupoher_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'it_grupoher_spn'
    
    notice_data.main_language = 'IT'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'EUR'
    
     # Onsite Comment -notice_type: if the Data di Scadenza: is replaced with keyword like Prorogato al: then notice_type will be 16 (AMD Amendment)
    notice_data.notice_type = 4  
    notice_data.procurement_method = 2
    notice_data.notice_url = url
    
    # Onsite Field -Data di Pubblicazione:
    # Onsite Comment -None
    
    if url == 'https://www.gruppohera.it/gruppo/fornitori/bandi-e-avvisi/bandi-di-gara-attivi':
        try:
            publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div.container.archivio > div > div > div > div:nth-child(1)").text
            publish_date = GoogleTranslator(source='it', target='en').translate(publish_date)
            publish_date = re.findall('\d+-\d+-\d{4}',publish_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date,'%d-%m-%Y').strftime('%Y/%m/%d')
        except:
            try:
                publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div.container.archivio > div > div > div > div:nth-child(1)").text
                publish_date = GoogleTranslator(source='it', target='en').translate(publish_date)
                publish_date = re.findall('\d{4}-\d+-\d+',publish_date)[0]
                notice_data.publish_date = datetime.strptime(publish_date,'%Y-%m-%d').strftime('%Y/%m/%d')
            except Exception as e:
                logging.info("Exception in publish_date: {}".format(type(e).__name__))
                pass
    
    else:
        try:
            publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div.container.archivio > div > div > div > div:nth-child(1)").text
            publish_date = GoogleTranslator(source='it', target='en').translate(publish_date)
            if '-' in publish_date:
                publish_date = re.findall('\d+-\d+-\d{4}',publish_date)[0]
                notice_data.publish_date = datetime.strptime(publish_date,'%d-%m-%Y').strftime('%Y/%m/%d')
            elif ',' in publish_date:
                publish_date = re.findall('\w+ \d+, \d{4}',publish_date)[0]
                notice_data.publish_date = datetime.strptime(publish_date,'%b %d, %Y').strftime('%Y/%m/%d')
            elif ' ' in publish_date:
                publish_date = re.findall('\d+ \w+ \d{4}',publish_date)[0]
                notice_data.publish_date = datetime.strptime(publish_date,'%d %b %Y').strftime('%Y/%m/%d')
            else:
                pass
        except Exception as e:
            logging.info("Exception in publish_date: {}".format(type(e).__name__))
            pass
        
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Data di Scadenza:
    # Onsite Comment -None
    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "div.container.archivio > div > div > div > div:nth-child(2)").text
        notice_deadline = GoogleTranslator(source='it', target='en').translate(notice_deadline)
        notice_deadline = re.findall('\d+-\d+-\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d-%m-%Y').strftime('%Y/%m/%d %H:%M:%S')
    except:
        try:
            notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "div.container.archivio > div > div > div > div:nth-child(2)").text
            notice_deadline = GoogleTranslator(source='it', target='en').translate(notice_deadline)
            notice_deadline = re.findall('\d{4}-\d+-\d+',notice_deadline)[0]
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%Y-%m-%d').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.notice_deadline)
        except Exception as e:
            logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
            pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.d-lg-block.greyish-brown.big > p:nth-child(1)').text
        notice_data.notice_title = GoogleTranslator(source='it', target='en').translate(notice_data.local_title)
        notice_data.local_description = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.notice_summary_english = notice_data.notice_title
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -we have added <a> tag bt take notice_no in textform from heading

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-xs-12.py-4 > a').text.split('N.')[1].strip()
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -we have added <a> tag bt take type_of_procedure_actual in textform from heading

    try:
        notice_data.type_of_procedure_actual = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-xs-12.py-4 > a').text
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += tender_html_element.find_element(By.CSS_SELECTOR, 'div.container.archivio > div> div').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -take "Bandi di gara attivi" in document_type_description for below url 'https://www.gruppohera.it/gruppo/fornitori/bandi-e-avvisi/bandi-di-gara-attivi'   and take "Gare in corso di aggiudicazione" in document_type_description for below url 'https://www.gruppohera.it/gruppo/fornitori/bandi-e-avvisi/gare-in-corso-di-aggiudicazione'

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.XPATH, '//*[@id="pagename"]').text.strip()
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = 'Sede legale Hera SpA'
        # Onsite Field -None
        # Onsite Comment -we have added <a> tag bt take org_description in textform from heading

        try:
            customer_details_data.org_description = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-xs-12.py-4 > a').text
        except Exception as e:
            logging.info("Exception in org_description: {}".format(type(e).__name__))
            pass

        customer_details_data.org_address = 'Viale Carlo Berti Pichat 2/4 40127 Bologna'
        customer_details_data.org_phone = 'Tel. 051 287111'
        customer_details_data.org_fax = 'Fax 051 287525'
        customer_details_data.org_email = 'heraspa@pec.gruppohera.it'
        customer_details_data.org_parent_id = '7797614'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        attachments_data = attachments()
        # Onsite Field -None
        # Onsite Comment -take file_name in textform from heading
        # Onsite Field -None
        # Onsite Comment -'div.col-xs-12.py-4 > div > a'  take this path for attachments from 'https://www.gruppohera.it/gruppo/fornitori/bandi-e-avvisi/gare-in-corso-di-aggiudicazione'
        attachments_data.file_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-xs-12.py-4 > a').text
        attachments_data.external_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-xs-12.py-4 > a').get_attribute('href')
        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
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
    urls = ['https://www.gruppohera.it/gruppo/fornitori/bandi-e-avvisi/bandi-di-gara-attivi', 
            'https://www.gruppohera.it/gruppo/fornitori/bandi-e-avvisi/gare-in-corso-di-aggiudicazione'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------') 
        logging.info(url)
        
        if url == 'https://www.gruppohera.it/gruppo/fornitori/bandi-e-avvisi/bandi-di-gara-attivi':
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.post-item.mb-3')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.post-item.mb-3')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break

                if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                    logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                    break

        if str(notice_data.publish_date) is not None and str(notice_data.publish_date) < threshold:
            break
            
        
        else:   
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="portlet_com_liferay_asset_publisher_web_portlet_AssetPublisherPortlet_INSTANCE_BdoYYJJxrUwW"]/div/div[2]/div/div[2]/div')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="portlet_com_liferay_asset_publisher_web_portlet_AssetPublisherPortlet_INSTANCE_BdoYYJJxrUwW"]/div/div[2]/div/div[2]/div')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break

                if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                    logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                    break

            if (notice_data.publish_date) is not None and (notice_data.publish_date) < threshold:
                break
           
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit()     
    output_json_file.copyFinalJSONToServer(output_json_folder)
