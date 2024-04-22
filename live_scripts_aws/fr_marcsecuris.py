
from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "fr_marcsecuris"
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
import gec_common.Doc_Download_ingate

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "fr_marcsecuris"
Doc_Download = gec_common.Doc_Download_ingate.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'fr_marcsecuris'
    
    notice_data.main_language = 'FR'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'FR'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'EUR'
    
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 4
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td > div:nth-child(1)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'th:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    try:
        notice_contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'tr.tr_type > td:nth-child(2)').text
        notice_contract_type = GoogleTranslator(source='auto', target='en').translate(notice_contract_type)
        if('Services' in notice_contract_type):
            notice_data.notice_contract_type = 'Services'
        elif('Works' in notice_contract_type):
            notice_data.notice_contract_type = 'Works'
        elif('Stationery' in notice_contract_type):
            notice_data.notice_contract_type = 'Supply'
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td.td_pub_date").text
        publish_date = GoogleTranslator(source='auto', target='en').translate(publish_date)
        publish_date = re.findall('\w+ \d+, \d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%B %d, %Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td.td_clot_date").text
        notice_deadline = GoogleTranslator(source='auto', target='en').translate(notice_deadline)
        try:
            notice_deadline = re.findall('\w+ \d+, \d{4}',notice_deadline)[0]
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%B %d, %Y').strftime('%Y/%m/%d %H:%M:%S')
        except:
            notice_deadline = re.findall('\d+ \w+ \d{4}',notice_deadline)[0]
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d %B %Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    try:
        type_of_procedure_actual = tender_html_element.find_element(By.CSS_SELECTOR, 'tr.tr_proc > td').text
        try:
            type_of_procedure_actual = type_of_procedure_actual.split(' >')[0]
            type_of_procedure_actual = GoogleTranslator(source='auto', target='en').translate(type_of_procedure_actual)
            
        except:
            type_of_procedure_actual = type_of_procedure_actual
            type_of_procedure_actual = GoogleTranslator(source='auto', target='en').translate(type_of_procedure_actual) 
            
        notice_data.type_of_procedure = fn.procedure_mapping("assets/fr_marcsecuris_procedure.csv",type_of_procedure_actual)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    notice_data.notice_url = 'https://www.marches-securises.fr/entreprise/?module=liste_consultations&presta=%3Bservices%3Btravaux%3Bfournitures%3Bautres&date_cloture_type=0&criteres_environnementaux=1&criteres_sociaux=1&is_dume=1&'
    
    try:
        notice_data.notice_text = tender_html_element.get_attribute('outerHTML')
    except:
        pass
    
    try:              
        customer_details_data = customer_details()

        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'tbody > tr.tr_pa.tr_icone > td').text
       
        customer_details_data.org_country = 'FR'
        customer_details_data.org_language = 'FR'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

            
    attachments_data = attachments()

    try:
        attachments_data.external_url = tender_html_element.find_element(By.CSS_SELECTOR, 'tr.tr_actions > td > table > tbody > tr > td:nth-child(1) > a').get_attribute('href')
        attachments_data.file_name = tender_html_element.find_element(By.CSS_SELECTOR, 'tr.tr_actions > td > table > tbody > tr > td:nth-child(1) > a').text
        attachments_data.file_type = 'pdf'

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
page_main = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://www.marches-securises.fr/entreprise/?module=liste_consultations&presta=%3Bservices%3Btravaux%3Bfournitures%3Bautres&date_cloture_type=0&criteres_environnementaux=1&criteres_sociaux=1&is_dume=1&'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(1,3):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/div/div[4]/div[2]/table'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div/div[4]/div[2]/table')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div/div[4]/div[2]/table')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="details_avis"]/div[3]/div/div/a[11]')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/div/div[4]/div[2]/table'),page_check))
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
    output_json_file.copyFinalJSONToServer(output_json_folder)
    
