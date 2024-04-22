Script
br_comprasnet
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
import functions as fn
from functions import ET
import common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "br_comprasnet"
Doc_Download = common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.main_language = 'PT'
    
    notice_data.currency = 'EUR'
    
    notice_data.performance_country = 'BR'
    
    notice_data.procurement_method = 'Other'
    
    notice_data.notice_type = '4'
    
    # Onsite Field -None
    # Onsite Comment -just take "Entrega da Proposta:" field from the body

    try:
        publish_date = page_details.find_element(By.CSS_SELECTOR, "tr:nth-child(2) > td.tex3 tbodytr:nth-child(2) > td.tex3 tbody").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: ", str(type(e)))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -None
    # Onsite Comment -Código da UASG

    try:
        notice_data.notice_no = page_details.find_element(By.CSS_SELECTOR, 'td.tex3 > table  tr:nth-child(8)').text
    except Exception as e:
        logging.info("Exception in notice_no: ", str(type(e)))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.notice_summary_english = page_details.find_element(By.CSS_SELECTOR, 'tr:nth-child(2) > td.tex3 > table').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: ", str(type(e)))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.notice_text = page_details.find_element(By.XPATH, '/html/body/table[2]/tbody/tr[2]/td/table[2]').text
    except Exception as e:
        logging.info("Exception in notice_text: ", str(type(e)))
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'tr:nth-child(2) > td > table:nth-child(2)'):
            customer_details_data = customer_details()
        # Onsite Field -None
        # Onsite Comment -None

            try:
                customer_details_data.org_name = page_details.find_element(By.CSS_SELECTOR, 'tbody > tr:nth-child(2) > td > table:nth-child(2) > tbody > tr:nth-child(1) table > tbody > tr:nth-child(1)').text
            except Exception as e:
                logging.info("Exception in org_name: ", str(type(e)))
                pass
        
        # Onsite Field -None
        # Onsite Comment -None

            try:
                customer_details_data.org_fax = page_details.find_element(By.CSS_SELECTOR, 'body > table:nth-child(3)  p > b:nth-child(12)').text
            except Exception as e:
                logging.info("Exception in org_fax: ", str(type(e)))
                pass
        
        # Onsite Field -None
        # Onsite Comment -None

            try:
                customer_details_data.org_address = page_details.find_element(By.CSS_SELECTOR, 'tbody > tr:nth-child(2) > td > table:nth-child(2) > tbody > tr:nth-child(2) > td.tex3').text
            except Exception as e:
                logging.info("Exception in org_address: ", str(type(e)))
                pass
        
        # Onsite Field -None
        # Onsite Comment -None

            try:
                customer_details_data.org_phone = page_details.find_element(By.CSS_SELECTOR, 'tr > td > p > b:nth-child(10)').text
            except Exception as e:
                logging.info("Exception in org_phone: ", str(type(e)))
                pass
        
    # Onsite Field -None
    # Onsite Comment -"Itens e Download"

    try:
        notice_data.notice_url = page_main.find_element(By.CSS_SELECTOR, 'a > table > tbody > tr.tex3 > td > input.texField2').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
    except:
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -just take "Objeto:" field from the body

    try:
        notice_data.local_title = page_details.find_element(By.CSS_SELECTOR, 'tr:nth-child(2) > td.tex3 tbody').text
    except Exception as e:
        logging.info("Exception in local_title: ", str(type(e)))
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'tbody > tr:nth-child(2) > td > table:nth-child(2) tbody tbody > tr > td:nth-child(2)'):
            lot_details_data = lot_details()
        # Onsite Field -None
        # Onsite Comment -just take "Instalação / Manutenção - Piso Geral" field from the variable path

            try:
                lot_details_data.lot_title = page_details.find_element(By.CSS_SELECTOR, 'tbody  td:nth-child(2) > span.tex3').text
            except Exception as e:
                logging.info("Exception in lot_title: ", str(type(e)))
                pass
        
        # Onsite Field -None
        # Onsite Comment -just take "Quantidade:" field from the variable path

            try:
                lot_details_data.lot_quantity = page_details.find_element(By.CSS_SELECTOR, 'tbody  td:nth-child(2) > span.tex3').text
            except Exception as e:
                logging.info("Exception in lot_quantity: ", str(type(e)))
                pass
        
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: ", str(type(e))) 
        pass
    
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: ", str(type(e))) 
        pass
    
    notice_data.identifier = str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title) 
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
page_details = fn.init_chrome_driver(arguments) 
page_main = fn.init_chrome_driver(arguments) 
page_main = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['http://comprasnet.gov.br/ConsultaLicitacoes/ConsLicitacao_Relacao.asp'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,100):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/table[2]/tbody/tr[3]/td[2]/form'))).text
            rows = WebDriverWait(driver, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/table[2]/tbody/tr[3]/td[2]/form')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/table[2]/tbody/tr[3]/td[2]/form')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break
                
                if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                    logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                    break

                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break

            try:   
                next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                page_main.execute_script("arguments[0].click();",next_page)
                logging.info("Next page")
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/table[2]/tbody/tr[3]/td[2]/form'),page_check))
            except Exception as e:
                logging.info("Exception in next_page: ", str(type(e)))
                logging.info("No next page")
                break
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit() 
    
    output_json_file.copyFinalJSONToServer(output_json_folder)
    