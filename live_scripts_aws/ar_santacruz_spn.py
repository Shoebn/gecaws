from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "ar_santacruz_spn"
log_config.log(SCRIPT_NAME)
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
from gec_common import functions as fn

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "ar_santacruz_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'ar_santacruz_spn'
    notice_data.main_language = 'ES'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'AR'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'ARS'
    notice_data.procurement_method = 2
    notice_data.notice_type = 4
    
    # Onsite Field -APERTURA DE OFERTAS:
    # Onsite Comment -None  OCTOBER 25, 2023  DECEMBER 18

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "li:nth-child(3)").text
        notice_deadline_en = GoogleTranslator(source='auto', target='en').translate(notice_deadline)
        try:
            notice_deadline_en = notice_deadline_en.replace('AT','')
            deadline_en = re.findall('\w+ \d+, \d{4},  \d+:\d+',notice_deadline_en)[0]
            notice_data.notice_deadline = datetime.strptime(deadline_en,'%B %d, %Y,  %H:%M').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.notice_deadline)

        except:
            try:
                notice_deadline_en = notice_deadline_en.replace('AT','')
                deadsline_en = re.findall('\w+ \d+ ',notice_deadline_en)[0]
                yrs = threshold.split('/')[0].strip()
                deadline = str(deadsline_en)+'/'+str(yrs)
                deadline1 = re.findall('\d+:\d+',notice_deadline_en)[0]
                deadline = deadline +' ' +deadline1
                notice_data.notice_deadline = datetime.strptime(deadline,'%B %d /%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
                logging.info(notice_data.notice_deadline)
            except:
                deadline_en = re.findall('\w+ \d+, \d{4}',notice_deadline_en)[0]
                notice_data.notice_deadline = datetime.strptime(deadline_en,'%B %d, %Y').strftime('%Y/%m/%d %H:%M:%S')
                logging.info(notice_data.notice_deadline)
            
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
        return
    # Onsite Field -DESCRIPCIÓN:
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'li:nth-child(2)').text.split(':')[1].strip()
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -LICITACIÓN PÚBLICA Nº:
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'li:nth-child(1)').text.split(':')[1].strip()
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.titulolic > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url

    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#t3-mainbody > div').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'AR'
        customer_details_data.org_language = 'ES'
        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div.titulolic').text
        try:
            org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"CONSULTA DEL  PLIEGO:")]//following::span[1]').text
            customer_details_data.org_email = fn.get_email(org_email)
        except:
            pass
        try:
            customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"CONSULTA DEL  PLIEGO:")]//following::span[1]').text.split(customer_details_data.org_email)[0]
            if 'Tel' in customer_details_data.org_address:
                customer_details_data.org_address = customer_details_data.org_address.split('Tel')[0]
            if 'EN LA CITADA DIRECCIÓN' in  customer_details_data.org_address:
                 customer_details_data.org_address= None
        except:
            pass
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    # Onsite Field -VALOR DEL PLIEGO:
    # Onsite Comment -None

    try:
        document_cost = tender_html_element.find_element(By.CSS_SELECTOR, 'li:nth-child(5)').text.split('$')[1].split(' ')[1].strip()
        document_cost = re.sub("[^\d\.\,]","",document_cost)
        notice_data.document_cost =float(document_cost.replace('.','').replace(',','.').strip())
    except Exception as e:
        logging.info("Exception in document_cost: {}".format(type(e).__name__))
        pass

    try:              
        for single_record in page_details.find_elements(By.XPATH, '''//*[contains(text(),'DESCARGAR PLIEGO:')]//following::a[@title]'''):
            attachments_data = attachments()
        # Onsite Field -DESCARGAR PLIEGO:
        # Onsite Comment -None

            attachments_data.external_url = single_record.get_attribute('href')
            attachments_data.file_name = single_record.text.split('.')[0].strip()
        
        # Onsite Field -DESCARGAR PLIEGO:
        # Onsite Comment -just take attachment

            try:
                attachments_data.file_type = single_record.text.split('.')[-1].strip()
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title) 
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
    urls = ["https://www.santacruz.gob.ar/licitaciones"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(2,10):#10
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@class="catItemHeader"]/div/..'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@class="catItemHeader"]/div/..')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@class="catItemHeader"]/div/..')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
                        
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@class="catItemHeader"]/div/..'),page_check))
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
