from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "it_edisu"
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
SCRIPT_NAME = "it_edisu"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'it_edisu'
    notice_data.main_language = 'IT'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'EUR'
    notice_data.procurement_method = 2
    

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td.views-field.views-field-title > a').text 
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
        if 'EXPRESSION OF INTEREST' in notice_data.notice_title:
            notice_data.notice_type = 5
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "tbody > tr > td.views-field.views-field-field-data-scadenza").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except:
        notice_data.notice_url = url
        
    try:
        notice_text = page_details.find_element(By.CSS_SELECTOR, '#section').text
        if 'Tutti i documenti sono accessibili a questo' in notice_text or 'La gara è consultabile sul sito istituzionale' in notice_text: 
            notice_data.additional_tender_url =  page_details.find_element(By.CSS_SELECTOR, 'div > div > p:nth-child(3) > a').get_attribute("href")  
        else:
            pass
    except Exception as e:
        logging.info("Exception in additional_tender_url: {}".format(type(e).__name__)) 
        pass
               
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#section').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass

    try:
        publish_date = page_details.find_element(By.CSS_SELECTOR, "div.field.field-name-field-date.field-type-datetime.field-label-above > div.field-items > div > span").text 
        publish_date = GoogleTranslator(source='it', target='en').translate(publish_date)
        publish_date = re.findall(' \w+ \d+, \d{4}',publish_date)[0]
        publish_date = publish_date.replace(',','')
        notice_data.publish_date = datetime.strptime(publish_date,' %B %d %Y').strftime('%Y/%m/%d')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    try:
        notice_data.notice_no = page_details.find_element(By.CSS_SELECTOR, 'div.field.field-name-field-cig > div.field-items').text 
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = 'ENTE REGIONALE PER IL DIRITTO ALLO STUDIO UNIVERSITARIO DEL PIEMONTE'
        customer_details_data.org_email = 'edisu@cert.edisu.piemonte.it'
        customer_details_data.org_address = 'Via Madama Cristina n.83 - 10126 Torino C.F. 97547570016 | P.IVA 06440290010'
        customer_details_data.org_fax = '0116531150'
        customer_details_data.org_phone = '0116531111'
        customer_details_data.org_parent_id = '7798031'
        customer_details_data.org_country = 'IT'
        customer_details_data.org_language = 'IT'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass        

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div > div.field-items > div > span.file '):
            attachments_data = attachments()
            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'a').text 
            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'a').get_attribute('href') 

            try:
                attachments_data.file_type = attachments_data.external_url 
                if '.pdf' in attachments_data.file_type:
                    attachments_data.file_type = 'pdf'
                elif 'xlsx' in attachments_data.file_type:
                    attachments_data.file_type  = 'xlsx'
                elif 'doc' in attachments_data.file_type:
                    attachments_data.file_type = 'xlsx'
                elif 'zip' in attachments_data.file_type:
                    attachments_data.file_type = 'zip'
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
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
    urls = ["https://www.edisu.piemonte.it/it/avvisi-di-gara" , "https://www.edisu.piemonte.it/it/bandi-di-gara"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(2,4):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'tbody > tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'tbody > tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'tbody > tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
                    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'tbody > tr'),page_check))
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
