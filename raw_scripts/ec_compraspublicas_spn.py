
#select "Desde" that is the previous date and after this >>>>>>  select "Hasta" the current date >>>>> fill in  the captcha  >>>>>>> click on "Buscar"

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
SCRIPT_NAME = "ec_compraspublicas_spn"
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
    notice_data.script_name = 'ec_compraspublicas_spn'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'ES'
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'EC'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'USD'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_type = 4
    
    # Onsite Field -Código
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1) > a').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Objeto del Proceso
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Fecha de Publicación
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(7)").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Fecha de Publicación
    # Onsite Comment -None

    try:
        notice_data.grossbudgeteuro = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(6)').text
    except Exception as e:
        logging.info("Exception in grossbudgeteuro: {}".format(type(e).__name__))
        pass


    # Onsite Field -Fecha Final de Puja
    # Onsite Comment -None

    try:
        notice_deadline = page_details.find_element(By.XPATH, "//*[contains(text(),'Fecha Final de Puja')]//following::td[1]").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Fecha de Publicación
    # Onsite Comment -None

    try:
        notice_data.netbudgeteuro = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(6)').text
    except Exception as e:
        logging.info("Exception in netbudgeteuro: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),'Descripción')]//following::td[15]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Descripción
    # Onsite Comment -None

    try:
        notice_data.notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),'Descripción')]//following::td[15]').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Tipo Compra:
    # Onsite Comment -Consultancy - Consultoría ,  Service - Servicio/ Seguros , Good - Bien

    try:
        notice_data.notice_contract_type = page_details.find_element(By.XPATH, '//*[contains(text(),'Tipo Compra:')]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Tipo Compra:
    # Onsite Comment -Consultancy - Consultoría ,  Service - Servicio/ Seguros , Good - Bien

    try:
        notice_data.contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),'Tipo Compra:')]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Vigencia de Oferta:
    # Onsite Comment -None

    try:
        notice_data.contract_duration = page_details.find_element(By.XPATH, '//*[contains(text(),'Vigencia de Oferta:')]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#div6').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#div6'):
            customer_details_data = customer_details()
        # Onsite Field -Entidad Contratante
        # Onsite Comment -None

            try:
                customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, '#divProcesos td:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Provincia/Cantón
        # Onsite Comment -None

            try:
                customer_details_data.org_city = tender_html_element.find_element(By.CSS_SELECTOR, '#divProcesos td:nth-child(5)').text
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass
            customer_details_data.org_language = 'ES'
            customer_details_data.org_country = 'EC'
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    

    

# Onsite Field -Productos
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#cuadro'):
            lot_details_data = lot_details()
        # Onsite Field -Bien/Obra/Servicio
        # Onsite Comment -ref url "https://www.compraspublicas.gob.ec/ProcesoContratacion/compras/PC/informacionProcesoContratacion2.cpe?idSoliCompra=4a3mgj7srqdRnIGRcXrJWRM1xfiXhD7GLVXpXulTxoM,"

            try:
                lot_details_data.lot_title = page_details.find_element(By.CSS_SELECTOR, '#rounded-corner  tr:nth-child(1) > td:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -ref url "https://www.compraspublicas.gob.ec/ProcesoContratacion/compras/PC/informacionProcesoContratacion2.cpe?idSoliCompra=aiuvHOaBRgDbJRHV2-PsEl6JeYEcRsZNCkcRqCrC-Cs,"

            try:
                lot_details_data.lot_title = page_details.find_element(By.CSS_SELECTOR, '#rounded-corner  td:nth-child(1) > font').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -ref url "https://www.compraspublicas.gob.ec/ProcesoContratacion/compras/PC/informacionProcesoContratacion2.cpe?idSoliCompra=4a3mgj7srqdRnIGRcXrJWRM1xfiXhD7GLVXpXulTxoM,"

            try:
                lot_details_data.lot_actual_number = page_details.find_element(By.CSS_SELECTOR, '#rounded-corner  tr:nth-child(1) > td:nth-child(1)').text
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -ref url "https://www.compraspublicas.gob.ec/ProcesoContratacion/compras/PC/informacionProcesoContratacion2.cpe?idSoliCompra=aiuvHOaBRgDbJRHV2-PsEl6JeYEcRsZNCkcRqCrC-Cs,"

            try:
                lot_details_data.lot_actual_number = page_details.find_element(By.XPATH, '//*[contains(text(),'Categoría')]//following::td[3]').text
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -ref url "https://www.compraspublicas.gob.ec/ProcesoContratacion/compras/PC/informacionProcesoContratacion2.cpe?idSoliCompra=4a3mgj7srqdRnIGRcXrJWRM1xfiXhD7GLVXpXulTxoM,"

            try:
                lot_details_data.lot_quantity = page_details.find_element(By.CSS_SELECTOR, '#rounded-corner  tr:nth-child(1) > td:nth-child(3)').text
            except Exception as e:
                logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -ref url "https://www.compraspublicas.gob.ec/ProcesoContratacion/compras/PC/informacionProcesoContratacion2.cpe?idSoliCompra=aiuvHOaBRgDbJRHV2-PsEl6JeYEcRsZNCkcRqCrC-Cs,"

            try:
                lot_details_data.lot_quantity = page_details.find_element(By.XPATH, '//*[contains(text(),'Categoría')]//following::td[5]').text
            except Exception as e:
                logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -ref url "https://www.compraspublicas.gob.ec/ProcesoContratacion/compras/PC/informacionProcesoContratacion2.cpe?idSoliCompra=4a3mgj7srqdRnIGRcXrJWRM1xfiXhD7GLVXpXulTxoM,"

            try:
                lot_details_data.lot_quantity_uom = page_details.find_element(By.CSS_SELECTOR, '#rounded-corner  tr:nth-child(1) > td:nth-child(4)').text
            except Exception as e:
                logging.info("Exception in lot_quantity_uom: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -ref url "https://www.compraspublicas.gob.ec/ProcesoContratacion/compras/PC/informacionProcesoContratacion2.cpe?idSoliCompra=aiuvHOaBRgDbJRHV2-PsEl6JeYEcRsZNCkcRqCrC-Cs,"

            try:
                lot_details_data.lot_quantity_uom = page_details.find_element(By.XPATH, '//*[contains(text(),'Categoría')]//following::td[6]').text
            except Exception as e:
                logging.info("Exception in lot_quantity_uom: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -ref url "https://www.compraspublicas.gob.ec/ProcesoContratacion/compras/PC/informacionProcesoContratacion2.cpe?idSoliCompra=4a3mgj7srqdRnIGRcXrJWRM1xfiXhD7GLVXpXulTxoM,"

            try:
                lot_details_data.lot_grossbudget = page_details.find_element(By.CSS_SELECTOR, '#rounded-corner  tr:nth-child(1) > td:nth-child(5)').text
            except Exception as e:
                logging.info("Exception in lot_grossbudget: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -ref url "https://www.compraspublicas.gob.ec/ProcesoContratacion/compras/PC/informacionProcesoContratacion2.cpe?idSoliCompra=4a3mgj7srqdRnIGRcXrJWRM1xfiXhD7GLVXpXulTxoM,"

            try:
                lot_details_data.lot_grossbudget_lc = page_details.find_element(By.CSS_SELECTOR, '#rounded-corner  tr:nth-child(1) > td:nth-child(5)').text
            except Exception as e:
                logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -ref url "https://www.compraspublicas.gob.ec/ProcesoContratacion/compras/PC/informacionProcesoContratacion2.cpe?idSoliCompra=aiuvHOaBRgDbJRHV2-PsEl6JeYEcRsZNCkcRqCrC-Cs,"

            try:
                lot_details_data.lot_grossbudget = page_details.find_element(By.XPATH, '//*[contains(text(),'Categoría')]//following::td[7]').text
            except Exception as e:
                logging.info("Exception in lot_grossbudget: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -ref url "https://www.compraspublicas.gob.ec/ProcesoContratacion/compras/PC/informacionProcesoContratacion2.cpe?idSoliCompra=aiuvHOaBRgDbJRHV2-PsEl6JeYEcRsZNCkcRqCrC-Cs,"

            try:
                lot_details_data.lot_grossbudget_lc = page_details.find_element(By.XPATH, '//*[contains(text(),'Categoría')]//following::td[7]').text
            except Exception as e:
                logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
                pass


         # Onsite Field -Tipo Compra:
        # Onsite Comment -Consultancy - Consultoría , Service - Servicio/ Seguros , Good - Bien

            try:
                lot_details_data.contract_type = page_details.find_element(By.XPATH, '//*[contains(text(),'Tipo Compra:')]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in contract_type: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Tipo Compra:
        # Onsite Comment -Consultancy - Consultoría , Service - Servicio/ Seguros , Good - Bien

            try:
                lot_details_data.lot_contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),'Tipo Compra:')]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in lot_contract_type_actual: {}".format(type(e).__name__))
                pass
        
        
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    

        
# Onsite Field -None
# Onsite Comment -click on "Parámetros de Calificación " for the detail page

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#cuadro'):
            tender_criteria_data = tender_criteria()
        # Onsite Field -None
        # Onsite Comment -None

            try:
                tender_criteria_data.tender_criteria_weight = page_details.find_element(By.CSS_SELECTOR, '#rounded-corner   td:nth-child(3)').text
            except Exception as e:
                logging.info("Exception in tender_criteria_weight: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -None

            try:
                tender_criteria_data.tender_criteria_title = page_details.find_element(By.CSS_SELECTOR, '#rounded-corner   td:nth-child(1)').text
            except Exception as e:
                logging.info("Exception in tender_criteria_title: {}".format(type(e).__name__))
                pass
        
            tender_criteria_data.tender_criteria_cleanup()
            notice_data.tender_criteria.append(tender_criteria_data)
    except Exception as e:
        logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -click on "Archivos" for detail page
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#cuadro'):
            attachments_data = attachments()

        # Onsite Field -Descargar Archivo
        # Onsite Comment -None

            attachments_data.external_url = page_details.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > div > a').get_attribute('href')
            
        
        # Onsite Field -Descargar Archivo
        # Onsite Comment -None

            try:
                attachments_data.file_name = page_details.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > div > a').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Descripción del Archivo
        # Onsite Comment -None

            try:
                attachments_data.file_description = page_details.find_element(By.CSS_SELECTOR, 'tr:nth-child(2) > td:nth-child(1)').text
            except Exception as e:
                logging.info("Exception in file_description: {}".format(type(e).__name__))
                pass
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
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
    urls = ["https://www.compraspublicas.gob.ec/ProcesoContratacion/compras/PC/buscarProceso.cpe?sg=1#"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,100):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="divProcesos"]/table[1]/tbody/tr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="divProcesos"]/table[1]/tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="divProcesos"]/table[1]/tbody/tr')))[records]
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="divProcesos"]/table[1]/tbody/tr'),page_check))
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
    
