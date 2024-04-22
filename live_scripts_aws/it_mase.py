from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "it_mase"
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
SCRIPT_NAME = "it_mase"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'it_mase'

    
    notice_data.main_language = 'IT'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
    notice_data.performance_country.append(performance_country_data)
    notice_data.currency = 'EUR'
        
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 4
    

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td.views-field.views-field-title').text
        if 'Avviso di Rettifica' in notice_data.local_title or 'Avviso di rettifica' in notice_data.local_title:
            notice_data.notice_type = 16
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td.views-field.views-field-changed").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return


    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td.views-field.views-field-title > a').get_attribute("href") 
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except:
        notice_data.notice_url = url
    try:
        clk = WebDriverWait(page_details, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll"]')))
        page_details.execute_script("arguments[0].click();",clk)
    except:
        pass
        
 
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#page-default > main > div').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'IT'
        customer_details_data.org_name = "Ministero dell'Ambiente e della Sicurezza Energetica"
        customer_details_data.org_parent_id = '7797630'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    
    res= page_details.find_element(By.CSS_SELECTOR, '#it-block-italiagov-content > article > div > div.clearfix.text-formatted.field.field--name-body.field--type-text-with-summary.field--label-hidden.field__item').text
    if 'Avviso'in res or 'Allegati' in res:
        
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '.field--label-hidden.field__item > ul > li > a'):
            attachments_data = attachments()
            try:   
                attachments_data.external_url = single_record.get_attribute('href')
            except Exception as e:
                logging.info("Exception in external_url: {}".format(type(e).__name__))
                pass

            try:
                attachments_data.file_name = single_record.text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass


            try:
                attachments_data.file_type = attachments_data.external_url.split('.')[-1]
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass

            try:
                attachments_data.file_description = attachments_data.file_name
            except Exception as e:
                logging.info("Exception in file_description: {}".format(type(e).__name__))
                pass

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    else:
        pass

            
    try:
        notice_data.document_type_description = 'Bandi e Avvisi'
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    notice_data.identifier = str(notice_data.notice_no) + str(notice_data.publish_date) +  str(notice_data.notice_url) 
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
    try:
        for page_no in range(0,2):
            url = 'https://www.mase.gov.it/archivio-bandi?title=&tid_2=All&tid=All&created=&created_1=&page='+str(page_no)+''
            fn.load_page(page_main, url, 50)
            logging.info('----------------------------------')
            logging.info(url)
            
            try:
                clk = WebDriverWait(page_main, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll"]')))
                page_main.execute_script("arguments[0].click();",clk)
            except:
                pass
        
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'table.cols-2.table-borderless.table tbody tr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'table.cols-2.table-borderless.table tbody tr')))
            length = len(rows)
            for records in range(0,27):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'table.cols-2.table-borderless.table tbody tr')))[records]
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
