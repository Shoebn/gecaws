from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "bo_licitaciones_spn"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
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
SCRIPT_NAME = "bo_licitaciones_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'bo_licitaciones_spn'
    notice_data.main_language = 'ES'
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'BO'
    notice_data.performance_country.append(performance_country_data)
    notice_data.notice_no = '4'
    notice_data.procurement_method = 2
    notice_data.currency = 'BOB'

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td.celda-objeto').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

   
 
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td.celda-numero.not-mobile').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    try:
        est_amount = tender_html_element.find_element(By.CSS_SELECTOR, 'td.celda-monto').text
        notice_data.est_amount = float(est_amount.split('Bs')[0].replace('.','').replace(',','.').strip())
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass

    try:
        notice_data.grossbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
    
    
    
    try:
        notice_data.grossbudgeteuro = float(est_amount.split('$us.')[1].split('€')[0].replace('.','').replace(',','.').strip())  
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass

    try:
        notice_contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'td.celda-tipo-contratacion').text 
        if 'Bienes' in notice_contract_type:
            notice_data.notice_contract_type = 'services'
        elif 'Servicios Generales' in notice_contract_type:
            notice_data.notice_contract_type  = 'services'
        elif 'Obras' in notice_contract_type:
            notice_data.notice_contract_type  = 'others'
        elif 'Consultoria' in notice_contract_type:
            notice_data.notice_contract_type  = 'Consultancy'
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass

    try:
        notice_data.contract_type_actual = notice_contract_type
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td.celda-ver > a ').get_attribute("href")     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'section > div > div > table').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
        
    try:
        publish_date = page_details.find_element(By.XPATH, "//*[contains(text(),'Fecha de publicación:')]//following::td[1]").text
        publish_date = GoogleTranslator(source='auto', target='en').translate(publish_date)
#         publish_date = re.findall('\d+-\d+-\d{4}',publish_date)
        notice_data.publish_date = datetime.strptime(publish_date,"%B %d, %Y").strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    try:
        notice_deadline = page_details.find_element(By.XPATH, "//*[contains(text(),'Fecha de presentación:')]//following::td[1]").text
        notice_deadline = GoogleTranslator(source='auto', target='en').translate(notice_deadline)
#         notice_deadline = re.findall('\d+-\d+-\d{4}',notice_deadline)
        notice_data.notice_deadline = datetime.strptime(notice_deadline,"%B %d, %Y").strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    try:              
        customer_details_data = customer_details()

        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td.celda-entidad').text
        try:
            customer_details_data.org_city = tender_html_element.find_element(By.CSS_SELECTOR, 'tr td:nth-child(2)').text
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass

        try:
            customer_details_data.contact_person = page_details.find_element(By.XPATH, "//*[contains(text(),'Contacto:')]//following::td[1]").text  
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass

        try:
            org_phone = page_details.find_element(By.XPATH, "//*[contains(text(),'Contacto:')]//following::td[1]").text  
            customer_details_data.org_phone = org_phone.split('Telf:')[1].split(')')[0]
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass

        customer_details_data.org_country = 'BO'
        customer_details_data.org_language = 'ES'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'input.btn.btn-xs.btn-success'): 
            attachments_data = attachments()

            single_record.location_once_scrolled_into_view
            external_url = single_record.click()
            time.sleep(5)
            file_dwn = Doc_Download.file_download()
            attachments_data.external_url = str(file_dwn[0])

            attachments_data.file_name = single_record.get_attribute("value") 

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
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
page_details = Doc_Download.page_details
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
 
    for page_no in range(1,9):
        url='https://www.licitaciones.com.bo/convocatorias-nacionales-'+str(page_no)+'.html'
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[1]/main/section/div/table/tbody/tr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/main/section/div/table/tbody/tr')))
            length = len(rows)
            for records in range(1,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/main/section/div/table/tbody/tr')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
                    
                if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                    logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
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
