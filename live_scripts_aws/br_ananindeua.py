from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "br_ananindeua"
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
SCRIPT_NAME = "br_ananindeua"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = "br_ananindeua"
    
    notice_data.currency = 'BRL'
    
    notice_data.main_language = 'PT'
    
    notice_data.notice_type = 4
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'BR'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.procurement_method = 2
    
    notice_data.notice_url = 'https://www.ananindeua.pa.gov.br/licitacoes.asp'
    
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "a:nth-child(1) > div > div.col-12.col-md-5.small > div > div.col-7.ps-0.text-end").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')  
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    if notice_data.publish_date is None or notice_data.publish_date == '' :
        return
    
    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "div.col-12.col-md-auto.px-3.pt-2.pb-2").text
        notice_deadline = GoogleTranslator(source='pt', target='en').translate(notice_deadline)
        notice_deadline = notice_deadline.replace(",","")
        notice_deadline_date = re.findall('\w+ \d+ \d{4}',notice_deadline)[0]
        notice_deadline_time= re.findall('\d+:\d+',notice_deadline)[0]   
        notice_deadline_concat=notice_deadline_date+' '+notice_deadline_time
        notice_data.notice_deadline = datetime.strptime(notice_deadline_concat,'%B %d %Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    

    try:
        notice_data.notice_text = tender_html_element.get_attribute('outerHTML')
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div.item_lic_titulo').text.split('Nº')[1].split('-')[0].strip()
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    try:
        notice_data.local_title = tender_html_element.text.split('Objeto')[1].split('Abertura')[0].strip()
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'BR'
        customer_details_data.org_name = 'Ananindeua e Trabalho'
        customer_details_data.org_address = 'BR-316, 1515 - Centro, Ananindeua - PA, 67020-010 - (91) 99144-0140'
        try:
            customer_details_data.org_description = tender_html_element.text.split('Local')[1].split('\n')[1]
        except Exception as e:
            logging.info("Exception in org_description: {}".format(type(e).__name__))
            pass
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__))
        pass
        
    try:              
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, 'div.list-group.list-group-flush.bg-light.border-top a'):
            attachments_data = attachments()
            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'div > div.col-12.col-md-7.text-danger.word-break-all').text
            
            attachments_data.external_url = single_record.get_attribute('href')

            try:
                attachments_data.file_size = single_record.find_element(By.CSS_SELECTOR, 'div > div.col-12.col-md-5.small > div > div.col-5.pe-0').text.split('Tamanho:')[1].strip()
            except Exception as e: 
                logging.info("Exception in file_size: {}".format(type(e).__name__))
                pass
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__))
        pass
    

    try:
        notice_data.additional_source_name = tender_html_element.text.split('Aviso')[1].split('Objeto')[0].strip()
    except Exception as e:
        logging.info("Exception in additional_source_name: {}".format(type(e).__name__))
        pass
    

    notice_data.identifier = str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title) 
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
    urls = ['https://www.ananindeua.pa.gov.br/licitacoes'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(1,10):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'div.item_lic.shadow'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.item_lic.shadow')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.item_lic.shadow')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break

                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
                    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'div#pgnav_next a')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'div.item_lic.shadow'),page_check))
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
