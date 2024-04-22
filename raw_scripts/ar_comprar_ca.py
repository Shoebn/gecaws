#click on following types individual from "Estado proceso:" for ca
#Adjudicado
#Adjudicado con doc. contractuales generados



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
SCRIPT_NAME = "ar_comprar_ca"
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
    notice_data.script_name = 'ar_comprar_ca'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'ARS'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'ES'
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'AR'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_type = 7
    
    # Onsite Field -Fecha de apertura
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "#ctl00_CPH1_GridListaPliegos  td:nth-child(5) > p").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Número proceso
    # Onsite Comment -None

    try:
        notice_data.related_tender_id = tender_html_element.find_element(By.CSS_SELECTOR, '#ctl00_CPH1_GridListaPliegos td:nth-child(1)').text
    except Exception as e:
        logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
        pass
    
    
     # Onsite Field -Estado
    # Onsite Comment -None

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, '#ctl00_CPH1_GridListaPliegos td:nth-child(6)').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    # Onsite Field -Nombre proceso
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, '#ctl00_CPH1_GridListaPliegos td:nth-child(3)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    
   
    # Onsite Field -Número	
    # Onsite Comment -None

    try:
        notice_data.notice_no = page_details.find_element(By.CSS_SELECTOR, '#ctl00_CPH1_UCVistaPreviaPliego_UCDetalleImputacionAdjudicacion_gvDetalleImputacion_ctl02_lnkOC').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass


    # Onsite Field -Información del contrato
    # Onsite Comment -None

    try:
        notice_data.contract_duration = page_details.find_element(By.XPATH, '//*[contains(text(),'Duración del contrato')]//following::span[1]').text
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass
    

    # Onsite Field -Alcance
    # Onsite Comment -0 - National Competitivie Bidding, 1 - International Competitive Bidding, 2 -	Others	OTHERS


    try:
        notice_data.procurement_method = page_details.find_element(By.XPATH, '//*[contains(text(),'Alcance')]//following::span[1]').text
    except Exception as e:
        logging.info("Exception in procurement_method: {}".format(type(e).__name__))
        pass
    
    
    # Onsite Field -Process number
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, '#ctl00_CPH1_GridListaPliegos td:nth-child(1)').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#divImprimir > div:nth-child(9) > div').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    # Onsite Field -Detalle de productos o servicios
    # Onsite Comment -click on "Acciones" to get the detail page
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#ModVerItem > div > div > div.modal-body').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    

# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#divImprimir > div:nth-child(9) > div'):
            customer_details_data = customer_details()
        # Onsite Field -Unidad Ejecutora
        # Onsite Comment -None

            try:
                customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, '#ctl00_CPH1_GridListaPliegos td:nth-child(7)').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
            customer_details_data.org_language = 'ES'
            customer_details_data.org_country = 'AR'
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
   
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#ctl00_CPH1_UCVistaPreviaPliego_UC_DetalleProductos_gvLineaPliego > tbody'):
            lot_details_data = lot_details()
        # Onsite Field -Número renglón
        # Onsite Comment -None

            try:
                lot_details_data.lot_number = page_details.find_element(By.CSS_SELECTOR, '#ctl00_CPH1_UCVistaPreviaPliego_UC_DetalleProductos_gvLineaPliego td:nth-child(1)').text
            except Exception as e:
                logging.info("Exception in lot_number: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Descripción
        # Onsite Comment -None

            try:
                lot_details_data.lot_actual_number = page_details.find_element(By.CSS_SELECTOR, '#ctl00_CPH1_UCVistaPreviaPliego_UC_DetalleProductos_gvLineaPliego td:nth-child(3)').text
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Cantidad
        # Onsite Comment -None

            try:
                lot_details_data.lot_quantity_uom = page_details.find_element(By.CSS_SELECTOR, '#ctl00_CPH1_UCVistaPreviaPliego_UC_DetalleProductos_gvLineaPliego td:nth-child(5)').text
            except Exception as e:
                logging.info("Exception in lot_quantity_uom: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Plazo de entrega
        # Onsite Comment -Click on "Acciones"

            try:
                lot_details_data.lot_description = page_main.find_element(By.CSS_SELECTOR, '#ctl00_CPH1_UCVistaPreviaPliego_UC_DetalleProductos_PopUpTableEntrega_ctl02_PlazoGrid').text
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Descripción
        # Onsite Comment -None

            try:
                lot_details_data.lot_title = page_details.find_element(By.CSS_SELECTOR, '#ctl00_CPH1_UCVistaPreviaPliego_UC_DetalleProductos_gvLineaPliego td:nth-child(4)').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass



            # Onsite Field -None
        # Onsite Comment -None

            try:
                for single_record in page_details.find_elements(By.CSS_SELECTOR, '#ctl00_CPH1_UCVistaPreviaPliego_UCDetalleImputacionAdjudicacion_gvDetalleImputacion'):
                    award_details_data = award_details()
		
                    # Onsite Field -Fecha perfeccionamiento
                    # Onsite Comment -split data from "Fecha perfeccionamiento" for award date

                    award_details_data.award_date = page_details.find_element(By.CSS_SELECTOR, '#ctl00_CPH1_UCVistaPreviaPliego_UCDetalleImputacionAdjudicacion_gvDetalleImputacion').text
			
                    award_details_data.bidder_country = 'AR'


                    # Onsite Field -Nombre proveedor
                    # Onsite Comment -split data from "Nombre proveedor" for bidder

                    award_details_data.bidder_name = page_details.find_element(By.CSS_SELECTOR, '#ctl00_CPH1_UCVistaPreviaPliego_UCDetalleImputacionAdjudicacion_gvDetalleImputacion').text
			
                    # Onsite Field -Monto
                    # Onsite Comment -split data from "Monto" for amount

                    award_details_data.grossawardvaluelc = page_details.find_element(By.CSS_SELECTOR, '#ctl00_CPH1_UCVistaPreviaPliego_UCDetalleImputacionAdjudicacion_gvDetalleImputacion').text
			
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
    
# Onsite Field -Cláusulas particulares
# Onsite Comment -ref url - "https://comprar.gob.ar/PLIEGO/VistaPreviaPliegoCiudadano.aspx?qs=BQoBkoMoEhxTORxfljW9lZZaMjsx54eLALAm3dvRIWzj3hOhssrwEe%7CE7AXGOpqNw0JcGBmJMoCU9oZVhjpxtRRcwPjTvNyixa21r/RWiPax7M7%7CeYqcbOAqQgUDKM8D4/fjHYaVUAs="
    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#ctl00_CPH1_UCVistaPreviaPliego_UC_Clausulas_gvActosAdministrativos'):
            attachments_data = attachments()
        # Onsite Field -Documento
        # Onsite Comment -None

            try:
                attachments_data.file_name = page_details.find_element(By.CSS_SELECTOR, '#ctl00_CPH1_UCVistaPreviaPliego_UC_Clausulas_gvActosAdministrativos > tbody > tr >td:nth-child(1)').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Opciones
        # Onsite Comment -None

            attachments_data.external_url = page_details.find_element(By.CSS_SELECTOR, '#ctl00_CPH1_UCVistaPreviaPliego_UC_Clausulas_gvActosAdministrativos > tbody > tr >td:nth-child(5)').get_attribute('href')
            
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass



# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#ctl00_CPH1_UCVistaPreviaPliego_UCAnexos_gvAnexos'):
            attachments_data = attachments()
        # Onsite Field -split from"Nombre del Anexo	"
        # Onsite Comment -ref url - "https://comprar.gob.ar/PLIEGO/VistaPreviaPliegoCiudadano.aspx?qs=BQoBkoMoEhxINTWoj4AYQZ4ZG2MnD7C7MKxcSIz5bPR/3rcliBpv|QLG1H0RnSvVpDKNZdDy5r3dbZKYYQinUl6L/8/2KpvdKPcl1FtWrn7V9BuzAIkx4mzFRO2ee15EHMW4CPgiiYo="
            try:
                attachments_data.file_type = page_details.find_element(By.CSS_SELECTOR, '#ctl00_CPH1_UCVistaPreviaPliego_UCAnexos_gvAnexos > tbody > tr:nth-child(2) > td:nth-child(1)').text
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -split from" Descripción"
        # Onsite Comment -ref url - "https://comprar.gob.ar/PLIEGO/VistaPreviaPliegoCiudadano.aspx?qs=BQoBkoMoEhxINTWoj4AYQZ4ZG2MnD7C7MKxcSIz5bPR/3rcliBpv|QLG1H0RnSvVpDKNZdDy5r3dbZKYYQinUl6L/8/2KpvdKPcl1FtWrn7V9BuzAIkx4mzFRO2ee15EHMW4CPgiiYo="
            try:
                attachments_data.file_description = page_details.find_element(By.CSS_SELECTOR, '#ctl00_CPH1_UCVistaPreviaPliego_UCAnexos_gvAnexos > tbody > tr:nth-child(2) > td:nth-child(3)').text
            except Exception as e:
                logging.info("Exception in file_description: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -split from" Tipo"
        # Onsite Comment -ref url - "https://comprar.gob.ar/PLIEGO/VistaPreviaPliegoCiudadano.aspx?qs=BQoBkoMoEhxINTWoj4AYQZ4ZG2MnD7C7MKxcSIz5bPR/3rcliBpv|QLG1H0RnSvVpDKNZdDy5r3dbZKYYQinUl6L/8/2KpvdKPcl1FtWrn7V9BuzAIkx4mzFRO2ee15EHMW4CPgiiYo="
            try:
                attachments_data.file_name = page_details.find_element(By.CSS_SELECTOR, '#ctl00_CPH1_UCVistaPreviaPliego_UCAnexos_gvAnexos > tbody > tr:nth-child(2) > td:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -split from" Acciones "
        # Onsite Comment -ref url - "https://comprar.gob.ar/PLIEGO/VistaPreviaPliegoCiudadano.aspx?qs=BQoBkoMoEhxINTWoj4AYQZ4ZG2MnD7C7MKxcSIz5bPR/3rcliBpv|QLG1H0RnSvVpDKNZdDy5r3dbZKYYQinUl6L/8/2KpvdKPcl1FtWrn7V9BuzAIkx4mzFRO2ee15EHMW4CPgiiYo="
            attachments_data.external_url = page_details.find_element(By.CSS_SELECTOR, '#ctl00_CPH1_UCVistaPreviaPliego_UCAnexos_gvAnexos').get_attribute('href')
            
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    

    

# Onsite Field -Actos administrativos
# Onsite Comment -ref - "https://comprar.gob.ar/PLIEGO/VistaPreviaPliegoCiudadano.aspx?qs=BQoBkoMoEhxTORxfljW9lZZaMjsx54eLALAm3dvRIWzj3hOhssrwEe%7CE7AXGOpqNw0JcGBmJMoCU9oZVhjpxtRRcwPjTvNyixa21r/RWiPax7M7%7CeYqcbOAqQgUDKM8D4/fjHYaVUAs="
    
    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#ctl00_CPH1_UCVistaPreviaPliego_UC_ActosAdministrativos_gvActosAdministrativos'):
            attachments_data = attachments()
        # Onsite Field -split from "Documento"
        # Onsite Comment -ref - "https://comprar.gob.ar/PLIEGO/VistaPreviaPliegoCiudadano.aspx?qs=BQoBkoMoEhxTORxfljW9lZZaMjsx54eLALAm3dvRIWzj3hOhssrwEe%7CE7AXGOpqNw0JcGBmJMoCU9oZVhjpxtRRcwPjTvNyixa21r/RWiPax7M7%7CeYqcbOAqQgUDKM8D4/fjHYaVUAs="
            try:
                attachments_data.file_name = page_details.find_element(By.CSS_SELECTOR, '#ctl00_CPH1_UCVistaPreviaPliego_UC_ActosAdministrativos_gvActosAdministrativos > tbody > tr > td:nth-child(1)').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -split from "Opciones"
        # Onsite Comment -ref - "https://comprar.gob.ar/PLIEGO/VistaPreviaPliegoCiudadano.aspx?qs=BQoBkoMoEhxTORxfljW9lZZaMjsx54eLALAm3dvRIWzj3hOhssrwEe%7CE7AXGOpqNw0JcGBmJMoCU9oZVhjpxtRRcwPjTvNyixa21r/RWiPax7M7%7CeYqcbOAqQgUDKM8D4/fjHYaVUAs="
            attachments_data.external_url = page_details.find_element(By.CSS_SELECTOR, '#ctl00_CPH1_UCVistaPreviaPliego_UC_ActosAdministrativos_gvActosAdministrativos > tbody > tr > td:nth-child(5)').get_attribute('href')
            
        
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
    urls = ["https://comprar.gob.ar/BuscarAvanzado.aspx"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,50):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="ctl00_CPH1_GridListaPliegos"]/tbody/tr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="ctl00_CPH1_GridListaPliegos"]/tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="ctl00_CPH1_GridListaPliegos"]/tbody/tr')))[records]
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="ctl00_CPH1_GridListaPliegos"]/tbody/tr'),page_check))
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
    