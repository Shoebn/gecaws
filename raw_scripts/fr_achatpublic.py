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
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "fr_achatpublic"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
        
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.script_name = 'fr_achatpublic'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'FR'
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'FR'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'EUR'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_type = 4
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.sdmCardGeneric__top > h2').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
      # Onsite Field -deadline --- Date limite
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "div.sdmCardConsult__colTime > div").text.replace('\n',' ')
        notice_deadline = GoogleTranslator(source='auto', target='en').translate(notice_deadline)
        try:
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d %B %Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        except:
            notice_deadline = re.findall('\w+ \d+, \d{4} \d+:\d+',notice_deadline)[0]
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%B %d, %Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

      
    # Onsite Field -Référence --- Reference:
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'li:nth-child(2) > span.jqShave.same-content-title').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Type de procédure --- Type of procedure
    # Onsite Comment -None
    try:
        notice_data.type_of_procedure_actual = tender_html_element.find_element(By.CSS_SELECTOR, "li:nth-child(5) > span.jqShave.same-content-title ").text
        type_of_procedure_actual = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("assets/fr_achatpublic_procedure.csv",type_of_procedure_actual)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
  
    # Onsite Field -Services--Services, Travaux--Work, Fournitures--Supplies
    # Onsite Comment -None

    try:
        notice_contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'li:nth-child(4) > span.jqShave.same-content-title').text
        if 'Travaux' in notice_contract_type:
            notice_data.notice_contract_type = 'Works'
        if 'Fournitures' in notice_contract_type:
            notice_data.notice_contract_type = 'Supply'
        if 'Services' in notice_contract_type:
            notice_data.notice_contract_type = 'Service'        
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -None
    customer_details_data = customer_details()
    customer_details_data.org_country = 'FR'
    customer_details_data.org_language = 'FR'
# Onsite Field -Organisme
# Onsite Comment -None

    try:
        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'li:nth-child(1) > span.jqShave.same-content-title').text
    except Exception as e:
        logging.info("Exception in org_name: {}".format(type(e).__name__))
        pass

# Onsite Field -Lieu d'exécution --- Place of performance
# Onsite Comment -None

    try:
        customer_details_data.org_city = tender_html_element.find_element(By.CSS_SELECTOR, 'li.jqDNRmobile.jqInfobulleTap.sdmCardConsult__listItem.infobulle').text.split("Lieu d'exécution :")[1]
    except Exception as e:
        logging.info("Exception in org_city: {}".format(type(e).__name__))
        pass

    customer_details_data.customer_details_cleanup()
    notice_data.customer_details.append(customer_details_data)

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.sdmCardGeneric__top > h2 > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except:
        notice_data.notice_url = url
    
    try:
        clk = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[2]/main/div/div[1]/button')))
        page_details.execute_script("arguments[0].click();",clk)
    except:
        clk = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[2]/main/div/div[2]/button')))
        page_details.execute_script("arguments[0].click();",clk)

    # Onsite Field -Date d'ouverture de la salle --- Opening date of the room
    # Onsite Comment -click on " Hide Description"-" Masquer la description" to get the above selector's data

    try:
        publish_date = WebDriverWait(page_details, 50).until(EC.presence_of_element_located((By.XPATH, '//*[contains(text(),"ouverture de la salle")]//following::span[1]'))).get_attribute('innerHTML').strip()
        publish_date = GoogleTranslator(source='auto', target='en').translate(publish_date)
        publish_date = re.findall('\w+ \d+, \d{4} \d+:\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%B %d, %Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Description")]//following::span[1]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
      # Onsite Field -Masquer la description
    # Onsite Comment -click on " Hide Description"-" Masquer la description" to get the above selector's data

    try:
        notice_data.notice_summary_english=GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass

    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.wrapperMain.wrapperMain--fiche > main').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    
# Onsite Field -Lots
# Onsite Comment -Click on "Lots" for detail information
    try:
        Lots_clk = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#jqTabOpener--3')))
        page_details.execute_script("arguments[0].click();",Lots_clk)
    except:
        pass
 

    try:  
        lot_number = 1
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#jqTabPanel--3 > table > tbody > tr'):
            lot_details_data = lot_details()
        # Onsite Field -Intitulé
        # Onsite Comment -None

            try:
                lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
            except:
                lot_details_data.lot_title = notice_data.notice_title
        
        # Onsite Field -N° de lot
        # Onsite Comment -None

            lot_details_data.lot_number = lot_number

        # Onsite Field -Intitulé
        # Onsite Comment -None

            try:
                lot_details_data.lot_description = lot_details_data.lot_title
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass
            
            
            try:
                lot_details_data.contract_type = notice_data.notice_contract_type
            except Exception as e:
                logging.info("Exception in contract_type: {}".format(type(e).__name__))
                pass

            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
            lot_number += 1
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -None
    
    try:
        arguments_clk = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#jqTabOpener--1')))
        page_details.execute_script("arguments[0].click();",arguments_clk)
    except:
        pass
    
    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#jqTabPanel--1 > table > tbody > tr'):
            attachments_data = attachments()
        # Onsite Field -None
        # Onsite Comment -None

            attachments_data.file_name = 'Consulter'
            external_url = single_record.find_element(By.CSS_SELECTOR, 'td.sdmBasicTable__cell.sdmBasicTable__cell--btnSingle > button').get_attribute('onclick').split("'")[1].split("'")[0]
            attachments_data.external_url = 'https://www.achatpublic.com'+ external_url
        # Onsite Field -None
        # Onsite Comment -grab the data from the given path

            try:
                file_size = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1) > p > span.textLatoReg--14').text.split(" - ")[1]
                file_size = GoogleTranslator(source='fr', target='en').translate(file_size)
                attachments_data.file_size = fn.bytes_converter(file_size)
            except Exception as e:
                logging.info("Exception in file_size: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -grab the data from the given path

            try:
                attachments_data.file_type = single_record.find_element(By.CSS_SELECTOR, ' td:nth-child(1) > p > span.textLatoReg--14').text.split(" - ")[0]
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
       
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) + str(notice_data.publish_date) +  str(notice_data.notice_url) 
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
    urls = ['https://www.achatpublic.com/sdm/ent2/gen/rechercheCsl.action?tp=1686976322458'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(1,218):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[2]/main/div/div/ul/li[1]'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[2]/main/div/div/ul/li')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[2]/main/div/div/ul/li')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break
                
                if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                    logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                    break

            if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                break

            try:   
                next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'/html/body/div[2]/main/div/div/div[2]/ul/li/span')))
                page_main.execute_script("arguments[0].click();",next_page)
                logging.info("Next page")
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/div[2]/main/div/div/ul/li[1]'),page_check))
            except Exception as e:
                logging.info("Exception in next_page: {}".format(type(e).__name__))
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
    
