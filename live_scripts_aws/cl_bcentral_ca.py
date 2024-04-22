from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "cl_bcentral_ca"
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
SCRIPT_NAME = "cl_bcentral_ca"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"

# ----------------------------------------------------------------------------------------------------------------------------------------------------

# Go to URL : "https://www.bcentral.cl/en/web/banco-central/el-banco/licitaciones-y-cotizaciones-publicas"

#  there are 3 tables for award details click on "Finalizadas" in first table , click on "En Curso" in 
# second table , click on "Finalizadas" in third table

# if " Etapa" field has "Desierto" keyword then do not take this tender details

# click on "see more" for more tender details 

# ----------------------------------------------------------------------------------------------------------------------------------------------------

def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
   
    notice_data.script_name = 'cl_bcentral_ca'
    
    notice_data.main_language = 'ES'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'CL'
    notice_data.performance_country.append(performance_country_data)
  
    notice_data.notice_type = 7

    notice_data.currency = 'CLF'
   
    notice_data.procurement_method = 2
    
    try:
        Etapa = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text
        if 'Desierto' in Etapa:
            return
    except:
        pass
    
    # Onsite Field - Fecha
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(1)").text
        notice_data.publish_date = datetime.strptime(publish_date,'%d-%m-%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    # Onsite Field -Número
    # Onsite Comment -take only text value

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    # Onsite Field -Título
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    # Onsite Field -Procurement Process
    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass

    # Onsite Field -Número
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2) a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
  
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#portlet_urlamigable  div.portlet-content-container > div').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')

    # Onsite Field -Fecha de adjudicación:
    # Onsite Comment -split the date after "Fecha de adjudicación: "

    try:
        tender_award_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Fecha de adjudicación:")]//following::dd[1]').text
        tender_award_date = GoogleTranslator(source='auto', target='en').translate(tender_award_date)
        notice_data.tender_award_date = datetime.strptime(tender_award_date,'%B %d, %Y').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in tender_award_date: {}".format(type(e).__name__))
        pass

    try:
        notice_data.local_description = page_details.find_element(By.CSS_SELECTOR, 'section > div > h3 ').text
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass  

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = 'Banco Central Chile'
        customer_details_data.org_language = 'ES'
        customer_details_data.org_country = 'CL'
        customer_details_data.org_parent_id = '7769237'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass    
    
    try:      
        lot_number = 1
        lot_details_data = lot_details()
        lot_details_data.lot_number = lot_number

        # Onsite Comment -format 2,
        lot_details_data.lot_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text

        try:
            award_details_data = award_details()

            award_details_data.bidder_name = page_details.find_element(By.CSS_SELECTOR, 'div:nth-child(7) > dl:nth-child(1) > dt > h5').text
            
            try:
                award_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Fecha de adjudicación:")]//following::dd[1]').text
                award_date = GoogleTranslator(source='auto', target='en').translate(award_date)
                award_details_data.award_date = datetime.strptime(award_date,'%B %d, %Y').strftime('%Y/%m/%d')
            except:
                pass
            
            award_details_data.award_details_cleanup()
            lot_details_data.award_details.append(award_details_data)
        except Exception as e:
            logging.info("Exception in award_details: {}".format(type(e).__name__))
            pass
        
        if lot_details_data.award_details != []:
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
            lot_number +=1
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
  
    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#portlet_urlamigable > div > div.portlet-content-container > div > div > section > div > div > div > a'):
            attachments_data = attachments()

        # Onsite Comment -ref_url : "https://www.bcentral.cl/contenido/-/detalle/servicio-corporativo-impresion-digitalizacion-copiado"

            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'div.linkdoc-coltext > p').text
            attachments_data.external_url = single_record.get_attribute('href')
            
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) + str(notice_data.publish_date) +  str(notice_data.notice_url) 
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
page_details = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.bcentral.cl/en/web/banco-central/el-banco/licitaciones-y-cotizaciones-publicas"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        time.sleep(5)
        
        lst =[21,22,23] 
        for no in lst:  
            button = page_main.find_element(By.XPATH,'//*[@id="operaciones2-tab'+str(no)+'"]').click()
            time.sleep(5)
            
            try:
                see_more = page_main.find_element(By.XPATH,'//*[@id="verMas'+str(no)+'"]').click()
                time.sleep(3)
            except:
                pass
        
        try:
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, "/html/body/div[1]/section/div/div/div/div/div/section/div/div[2]/div/form/div[2]/div[2]/div/table/tbody/tr")))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, "/html/body/div[1]/section/div/div/div/div/div/section/div/div[2]/div/form/div[2]/div[2]/div/table/tbody/tr")))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break

                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break

                if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                    logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                    break
        except:
            logging.info("No new record")
            pass

    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)
