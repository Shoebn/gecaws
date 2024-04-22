#select "Licitaciones y Concursos", "Contratación Directa", "Libre Gestión", "Compras por Lineamiento", "Otros" >>>> select date - "Desde" take date of one month >>>> >>>> next click on " Búsqueda simple" >>>>>>> select "Adjudicado" >>>> Buscar


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
SCRIPT_NAME = "sv_comprasal_ca"
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
    notice_data.script_name = 'sv_comprasal_ca'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'ES'
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'SV'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'SVC'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_type = 7

     
    # Onsite Field -Código / tipo
    # Onsite Comment -just take the first part i.e. - just take data which is before "/" ....... 
    # Also if notice no is not present in the tender take it from notice url

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Nombre Proceso
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Fecha publicación
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    
    # Onsite Field -OBRA/BIEN/SERVICIO
    # Onsite Comment -None

    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),'Bien')]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -OBRA/BIEN/SERVICIO
    # Onsite Comment -None

    try:
        notice_data.notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),'Bien')]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -FUENTE DE FINANCIAMIENTO
    # Onsite Comment -ref url - 

    try:
        notice_data.funding_agencies = page_details.find_element(By.XPATH, '//*[contains(text(),'Fuente de Financiamiento')]//following::p[1]').text
    except Exception as e:
        logging.info("Exception in funding_agencies: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#ngb-nav-0-panel').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#ngb-nav-0-panel'):
            customer_details_data = customer_details()
        # Onsite Field -Institución
        # Onsite Comment -None

            try:
                customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -NOMBRE DEL CONTACTO
        # Onsite Comment -None

            try:
                customer_details_data.contact_person = page_details.find_element(By.CSS_SELECTOR, '//*[contains(text(),'Nombre del contacto')]//following::p[1]').text
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass
        
            customer_details_data.org_language = 'ES'
            customer_details_data.org_country = 'SV'
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass



    # Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in tender_html_element.find_elements(By.XPATH, '/html/body/app-root/div[1]/app-purchase-searchbox/div[5]/div/app-purchase-list2/div[2]/div[1]/table/tbody/tr'):
            lot_details_data = lot_details()
        # Onsite Field -Nombre Proceso
        # Onsite Comment -None

            try:
                lot_details_data.lot_title_english = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
            except Exception as e:
                logging.info("Exception in lot_title_english: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -OBRA/BIEN/SERVICIO
        # Onsite Comment -None

            try:
                lot_details_data.lot_description = page_details.find_element(By.XPATH, '//*[contains(text(),'Bien')]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -click on "Adjudicaciones" to get bidder

            try:
                for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.d-none.d-sm-none.d-lg-block > div'):
                    award_details_data = award_details()
		
                    # Onsite Field -PROVEEDOR
                    # Onsite Comment -click on "Adjudicaciones" to get bidder

                    award_details_data.bidder_name = page_details.find_element(By.CSS_SELECTOR, 'table > tbody > tr > td:nth-child(1) > span').text
			
                    # Onsite Field -MONTO ADJUDICADO
                    # Onsite Comment -click on "Adjudicaciones" to get bidder

                    award_details_data.grossawardvaluelc = page_details.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
			
                    # Onsite Field -Fecha resultado
                    # Onsite Comment -None

                    award_details_data.award_date = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(9)').text
			
                    award_details_data.award_details_cleanup()
                    lot_details_data.award_details.append(award_details_data)
            except Exception as e:
                logging.info("Exception in award_details: {}".format(type(e).__name__))
                pass
			
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -Documentos
# Onsite Comment -Click on "Documentos" to get attachments

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'app-purchase-documents'):
            attachments_data = attachments()
        # Onsite Field -Documentos
        # Onsite Comment -Click on "Documentos" to get attachments

            try:
                attachments_data.file_name = page_details.find_element(By.CSS_SELECTOR, 'app-purchase-documents  li > a').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
            # Onsite Field -Documentos
            # Onsite Comment -Click on "Documentos" to get attachments
            
            external_url = page_details.find_element(By.CSS_SELECTOR, 'app-purchase-documents  li > a').click()
            file_dwn = Doc_Download.file_download()
            attachments_data.external_url = str(file_dwn[0])
            
        
        # Onsite Field -Documentos
        # Onsite Comment -Click on "Documentos" to get attachments

            try:
                attachments_data.file_type = page_details.find_element(By.CSS_SELECTOR, 'app-purchase-documents  li > a').text
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass


# Onsite Field 
# Onsite Comment -Click on "Documentos" to get attachments

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, ' div.col-12.col-md-12.text-center.mt-4 > label'):
            attachments_data = attachments()
        # Onsite Field -Documentos
        # Onsite Comment -Click on "Documentos" to get attachments

            try:
                attachments_data.file_name = page_details.find_element(By.CSS_SELECTOR, ' div.col-12.col-md-12.text-center.mt-4 > label').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
            # Onsite Field -Documentos
            # Onsite Comment -Click on "Documentos" to get attachments
            
            external_url = page_details.find_element(By.CSS_SELECTOR, ' div.col-12.col-md-12.text-center.mt-4 > label').click()
            file_dwn = Doc_Download.file_download()
            attachments_data.external_url = str(file_dwn[0])
            
        
        # Onsite Field -Documentos
        # Onsite Comment -Click on "Documentos" to get attachments

            try:
                attachments_data.file_type = page_details.find_element(By.CSS_SELECTOR, ' div.col-12.col-md-12.text-center.mt-4 > label').text
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    

    
      notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title) 
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
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://unac.gob.sv/comprasalweb/procesos"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,10):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/app-root/div[1]/app-purchase-searchbox/div[5]/div/app-purchase-list2/div[2]/div[1]/table/tbody/tr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/app-root/div[1]/app-purchase-searchbox/div[5]/div/app-purchase-list2/div[2]/div[1]/table/tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/app-root/div[1]/app-purchase-searchbox/div[5]/div/app-purchase-list2/div[2]/div[1]/table/tbody/tr')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break

                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/app-root/div[1]/app-purchase-searchbox/div[5]/div/app-purchase-list2/div[2]/div[1]/table/tbody/tr'),page_check))
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
    