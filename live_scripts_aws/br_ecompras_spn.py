
from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "br_ecompras_spn"
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
SCRIPT_NAME = "br_ecompras_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'br_ecompras_spn'
   
    notice_data.main_language = 'PT'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'BR'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'EUR'
    
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 4
    
    # Onsite Field -Objeto:
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
   
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td.sorting_1 > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
   
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#content-container > table').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
        
     # Onsite Field -None
    # Onsite Comment -take notice no from tender page if present else split it from notice_url

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td.sorting_1 > a').text
        if notice_data.notice_no == '':
            notice_data.notice_no = notice_data.notice_url.split('ident=')[1].strip()
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
        
     # Onsite Field -Período de Inscrição: 20/12/2023 00:00 até 21/12/2023 23:59
    # Onsite Comment -take the date which is before "até " ........grab both date and time 

    try:
        publish_date = page_details.find_element(By.XPATH, "//*[contains(text(),'Período de Inscrição:')]//following::td[1]").text
        publish_date = re.findall('\d+/\d+/\d{4} \d+:\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    # Onsite Field -Data de Abertura: 22/12/2023 08:30
    # Onsite Comment -grab both date and time

    try:
        notice_deadline = page_details.find_element(By.XPATH, "//*[contains(text(),'Data de Abertura:')]//following::td[1]").text
        notice_deadline = re.findall('\d+/\d+/\d{4} \d+:\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    try:              
        customer_details_data = customer_details()

        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text

        try:
            customer_details_data.org_phone = page_details.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(1) > ul > li:nth-child(2)').text
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass

        try:
            customer_details_data.org_email = page_details.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(1) > ul > li:nth-child(1)').text
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass

        customer_details_data.org_country = 'BR'
        customer_details_data.org_language = 'PT'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass  

    try: 
        lot_number = 1
        lot_data = page_details.find_element(By.XPATH, "(//*[contains(text(),'Objeto:')]//following::table)[2]")
        for single_record in lot_data.find_elements(By.CSS_SELECTOR, 'table > tbody > tr')[1:]:
            lot_details_data = lot_details()
            lot_details_data.lot_number = lot_number
        # Onsite Field -Descrição   
        # Onsite Comment -take from "Objeto" >>> take data from "Descrição " column 

            lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
            lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
            
            try: 
                lot_actual_number = single_record.find_element(By.CSS_SELECTOR, ' td:nth-child(1)').text
                lot_actual_number= re.findall('ID-\d{6}',lot_actual_number)[0]
                lot_details_data.lot_actual_number = lot_actual_number.replace('ID-','').strip()
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        # Onsite Field -Qtde
        # Onsite Comment -take from "Objeto" >>> take data from "Qtde" column

            try:
                lot_quantity1 = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
                lot_quantity =lot_quantity1.replace('.','').replace(',','.').strip()
                lot_details_data.lot_quantity= float(lot_quantity)
            except Exception as e:
                logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Unidade Medida
        # Onsite Comment -take from "Objeto" >>> "Unidade Medida"

            try:
                lot_details_data.lot_quantity_uom = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
            except Exception as e:
                logging.info("Exception in lot_quantity_uom: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Preço Máximo
        # Onsite Comment -take from "Objeto" >>> "Preço MáximoMedida"

            try:
                lot_grossbudget_lc = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
                lot_grossbudget_lc = re.sub("[^\d\.\,]", "",lot_grossbudget_lc)
                lot_grossbudget_lc = lot_grossbudget_lc.replace('.','').replace(',','.').strip()
                lot_details_data.lot_grossbudget_lc = float(lot_grossbudget_lc)
            except Exception as e:
                logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
                pass
        
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
            lot_number +=1
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass

    try:               
        for single_record in page_details.find_elements(By.XPATH, "(//*[@id='download'])")[1::2]:
            attachments_data = attachments()

            attachments_data.external_url = single_record.get_attribute('href')
   
            try:
                attachments_data.file_type = single_record.text.split('.')[-1].strip()
            except Exception as e:
                logging.info("Exception in file_size: {}".format(type(e).__name__))
                pass
    
            attachments_data.file_name = single_record.text.replace(attachments_data.file_type,'').strip()
            
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.notice_deadline) + str(notice_data.local_title)
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
arguments= ['ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver_vpn(arguments) 
page_details = fn.init_chrome_driver_vpn(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.e-compras.am.gov.br/publico/licitacoes_editais.asp"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)

        try:
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="tabela"]/tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="tabela"]/tbody/tr')))[records]
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
    
