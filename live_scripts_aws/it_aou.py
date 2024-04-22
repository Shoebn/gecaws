from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "it_aou"
log_config.log(SCRIPT_NAME)
import jsons
from datetime import date, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from deep_translator import GoogleTranslator
from selenium import webdriver
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn
import dateparser
import gec_common.Doc_Download
from selenium.webdriver.chrome.options import Options

external_link_list = []

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "it_aou"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'it_aou'
    
    notice_data.main_language = 'IT'
    
    notice_data.currency = 'EUR'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 4
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div > ol > li > h3 > a').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:
        notice_data.document_type_description = 'Gare attive'
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "ol > li> span").text
        publish_date = GoogleTranslator(source='it', target='en').translate(publish_date) 
        publish_date = publish_date.split('Publication:')[1].split(' -')[0]
        publish_date = dateparser.parse(publish_date)
        notice_data.publish_date =  publish_date.strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "ol > li> span").text
        notice_deadline = GoogleTranslator(source='it', target='en').translate(notice_deadline)  
        notice_deadline = notice_deadline.split('Deadline:')[1].split('\n')[0] 
        notice_deadline = dateparser.parse(notice_deadline)
        notice_data.notice_deadline = notice_deadline.strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, ' ol > li > h3 > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except:
        notice_data.notice_url = url
        
    try:
        notice_data.notice_text = page_details.find_element(By.XPATH,'/html/body/div[7]/div/div/div[1]/div[2]/div[1]').text
    except:
        pass

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = 'Azienda Ospedaliero-Universitaria di Modena'
        customer_details_data.org_phone = '02241740360'
        customer_details_data.org_country = 'IT'
        customer_details_data.org_address = 'Elenco delle caselle di posta elettronica certificata dell’Azienda Ospedaliero – Universitaria Sede legale: via del Pozzo 71 - 41124 Modena'
        customer_details_data.org_email = 'affarigenerali@pec.aou.mo.it'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.blob-element-download.BLOBAlignLeft'):
            attachments_data = attachments()
            
            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'a').text

            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
            
            try:
                external_url = single_record.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
                if 'pdf' in external_url:
                    attachments_data.file_type = 'pdf'
                elif 'doc' in external_url:
                    attachments_data.file_type = 'doc'
                elif 'docx' in external_url:
                    attachments_data.file_type = 'docx'
                elif 'xlsx' in external_url:
                    attachments_data.file_type = 'xlsx'         
                else:
                    pass

            except Exception as e:
                logging.info("Exception in external_url: {}".format(type(e).__name__))
                pass

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['−−incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
options = Options()
for argument in arguments:
    options.add_argument(argument)
page_main = webdriver.Chrome(options=options)
page_details = webdriver.Chrome(options=options)

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://www.aou.mo.it/flex/cm/pages/ServeBLOB.php/L/IT/IDPagina/244'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(2,5):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'div.ElencoCanale.DataTitolo'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.ElencoCanale.DataTitolo')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.ElencoCanale.DataTitolo')))[records]
                    if tender_html_element.text == '':
                        continue
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/div[7]/div/div/div[1]/div[2]/div[1]/div[3]/ol/li[1]'),page_check))
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
    
