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


# Urban VPN(Spain)
# captcha on side 
# Open the side then first go down soule captcha and click "Buscar" this button then grab the data




NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "gt_compras_spn"
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
    notice_data.script_name = 'gt_compras_spn'
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'GT'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'EUR'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'ES'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 0
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_type = 4
    
    # Onsite Field -Fecha de publicación
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(1) > div > span.ValorForm').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Fecha de publicación
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "tr > td:nth-child(1) > div > span:nth-child(2)").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Fecha de publicación
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "tr > td:nth-child(1) > div > span:nth-child(3)").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Descripción
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(2) > div > div').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Descripción
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(2) > div > div > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#aspnetForm').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    
    # Onsite Field -Tipo Proceso
    # Onsite Comment -None

    try:
        notice_data.document_type_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Tipo Proceso")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Categoría
    # Onsite Comment -None

    try:
        notice_data.category = page_details.find_element(By.XPATH, '//*[contains(text(),"Categoría")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in category: {}".format(type(e).__name__))
        pass
    
# Onsite Field -Entidad
# Onsite Comment -click on ('div.col-xs-12.col-md-9.EtiquetaInfo > a:nth-child(1)') "Entidad:" to get the data
# Ref_url=https://www.guatecompras.gt/compradores/consultaDetEnt.aspx?iEnt=32&iUnt=0&iTipo=5


    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div:nth-child(6) > div.col-xs-12.col-md-9.EtiquetaInfo > a'):
            customer_details_data = customer_details()
        # Onsite Field -Detalle de entidad compradora >> Entidad
        # Onsite Comment -None

            try:
                customer_details_data.org_name = page_details1.find_element(By.XPATH, '//*[contains(text(),"Entidad")]//following::span[8]').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Detalle de entidad compradora >> Teléfonos
        # Onsite Comment -None

            try:
                customer_details_data.org_phone = page_details1.find_element(By.XPATH, '//*[contains(text(),"Teléfonos")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Detalle de entidad compradora >> Números de Fax
        # Onsite Comment -None

            try:
                customer_details_data.org_fax = page_details1.find_element(By.XPATH, '//*[contains(text(),"Números de Fax")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in org_fax: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Detalle de entidad compradora >> Páginas Web
        # Onsite Comment -None

            try:
                customer_details_data.org_website = page_details1.find_element(By.XPATH, '//*[contains(text(),"Páginas Web")]//following::a[1]').text
            except Exception as e:
                logging.info("Exception in org_website: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Detalle de entidad compradora >> Direcciones de Correo
        # Onsite Comment -None

            try:
                customer_details_data.org_email = page_details1.find_element(By.XPATH, '//*[contains(text(),"Direcciones de Correo")]//following::a[1]').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Detalle de entidad compradora >> Tipo
        # Onsite Comment -Note:Splite org_address between this "Tipo" to this "Dirección"

            try:
                customer_details_data.org_address = page_details1.find_element(By.XPATH, '//*[contains(text(),"Tipo")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Tipo de Entidad
        # Onsite Comment -None

            try:
                customer_details_data.type_of_authority_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Tipo de Entidad")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in type_of_authority_code: {}".format(type(e).__name__))
                pass
                customer_details_data.org_country = 'GT'
                customer_details_data.org_language = 'ES'      
        
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -Note:First click on "Documentos del Proceso de contratación" and clicl the Dropdown button then grab the data
# Ref_url=https://www.guatecompras.gt/concursos/consultaConcurso.aspx?nog=21497133&o=4

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#MasterGC_ContentBlockHolder_divContenidoTab'):
            attachments_data = attachments()
        # Onsite Field -Documento(s) adjunto(s) exitosamente
        # Onsite Comment -Note:split file_name.eg.,"21496439@Oficio Circular 9450 Departamento de Abastecimientos.pdf" don't take ".pdf" in file_name.

            try:
                attachments_data.file_name = page_details.find_element(By.CSS_SELECTOR, 'tbody > tr > td:nth-child(2) a').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Documento(s) adjunto(s) exitosamente
        # Onsite Comment -None

            attachments_data.external_url = page_details.find_element(By.CSS_SELECTOR, 'tbody > tr > td:nth-child(2) a').get_attribute('href')
            
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass

# Onsite Field -None
# Onsite Comment -Note:Click on "Tipos de Producto" and grab the data

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#MasterGC_ContentBlockHolder_divContenidoTab'):
            lot_details_data = lot_details()
        # Onsite Field -Nombre
        # Onsite Comment -None

            try:
                lot_details_data.lot_title = page_details.find_element(By.CSS_SELECTOR, 'tbody > tr.FilaTablaDetalle > td:nth-child(1)').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Cantidad
        # Onsite Comment -None

            try:
                lot_details_data.lot_quantity = page_details.find_element(By.CSS_SELECTOR, 'tbody > tr.FilaTablaDetalle > td:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Unidad de Medidad
        # Onsite Comment -None

            try:
                lot_details_data.lot_quantity_uom = page_details.find_element(By.CSS_SELECTOR, 'tbody > tr.FilaTablaDetalle > td:nth-child(3)').text
            except Exception as e:
                logging.info("Exception in lot_quantity_uom: {}".format(type(e).__name__))
                pass
            
        # Onsite Field -Codigo ONU
        # Onsite Comment -Note:Click on "Acciones" and grab the data

            try:
                lot_details_data.lot_actual_number = page_main.find_element(By.XPATH, '//*[contains(text(),"Codigo ONU")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Tipo de Requisito
        # Onsite Comment -Note:Click on "Acciones" and grab the data 		Note:Replace following keyword("Bien e Insumo=Supply","Servicio=Service")

            try:
                lot_details_data.contract_type = page_main.find_element(By.XPATH, '//*[contains(text(),"Tipo de Requisito")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in contract_type: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Tipo de Requisito
        # Onsite Comment -None

            try:
                lot_details_data.lot_contract_type_actual = page_main.find_element(By.XPATH, '//*[contains(text(),"Tipo de Requisito")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in lot_contract_type_actual: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Características
        # Onsite Comment -Note:Click on "Acciones" and grab the data

            try:
                lot_details_data.lot_description = page_main.find_element(By.XPATH, '//*[contains(text(),"Características:")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass

            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
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
page_main = fn.init_chrome_driver(arguments) 
page_details = fn.init_chrome_driver(arguments) 
page_details1 = fn.init_chrome_driver(arguments)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.guatecompras.gt/concursos/consultaConAvanz.aspx"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,10):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="MasterGC_ContentBlockHolder_dgResultado"]/tbody/tr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="MasterGC_ContentBlockHolder_dgResultado"]/tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="MasterGC_ContentBlockHolder_dgResultado"]/tbody/tr')))[records]
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="MasterGC_ContentBlockHolder_dgResultado"]/tbody/tr'),page_check))
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
    
    page_details1.quit()
    
    output_json_file.copyFinalJSONToServer(output_json_folder)