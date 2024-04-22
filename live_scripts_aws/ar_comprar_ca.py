#click on following types individual from "Estado proceso:" for ca
#Adjudicado
#Adjudicado con doc. contractuales generados

from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "ar_comprar_ca"
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
from selenium.webdriver.support.ui import Select

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
    
    notice_data.script_name = 'ar_comprar_ca'
        
    notice_data.main_language = 'ES'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'AR'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.notice_type = 7
    
    # Onsite Field -Fecha de apertura
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "#ctl00_CPH1_GridListaPliegos  td:nth-child(5) > p").text
        publish_date = re.findall('\d+/\d+/\d{4} \d+:\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

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
    
    try:              
        customer_details_data = customer_details()
    # Onsite Field -Unidad Ejecutora
    # Onsite Comment -None

        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, '#ctl00_CPH1_GridListaPliegos td:nth-child(7)').text

        customer_details_data.org_language = 'ES'
        customer_details_data.org_country = 'AR'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    # Onsite Field -Process number
    # Onsite Comment -None

    try:
        notice_url = tender_html_element.find_element(By.CSS_SELECTOR, '#ctl00_CPH1_GridListaPliegos td:nth-child(1)').click()                       
        time.sleep(10) 
        notice_url = page_main.current_url
        notice_data.notice_url = notice_url.replace('|','%7C').strip()
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
            
    
    try:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, '#divImprimir > div:nth-child(9) > div').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')

    try:
        notice_data.notice_no = page_main.find_element(By.CSS_SELECTOR, '#ctl00_CPH1_UCVistaPreviaPliego_usrCabeceraPliego_lblNumPliego').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    
    try: 
        local_description1 = page_main.find_element(By.XPATH, '''//*[contains(text(),"Requisitos económicos y financieros")]//following::span[1]''').text
        local_description2 = page_main.find_element(By.XPATH, '''//*[contains(text(),"Requisitos técnicos")]//following::span[1]''').text
        local_description3 = page_main.find_element(By.XPATH, '''//*[contains(text(),"Requisitos administrativos")]//following::span[1]''').text
        notice_data.local_description = local_description1+local_description2+local_description3
        if len(notice_data.local_description) > 5000:
            notice_summary_1half = notice_data.local_description[:5000]
            notice_summary_english_1half =  GoogleTranslator(source='auto', target='en').translate(notice_summary_english_1half)
            notice_summary_2half = notice_data.local_description[5000:]
            notice_summary_english_2half =  GoogleTranslator(source='auto', target='en').translate(notice_summary_english_2half)
            notice_data.notice_summary_english = notice_summary_english_1half+notice_summary_english_2half
        else:
            notice_data.notice_summary_english =  GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass

    # Onsite Field -Información del contrato
    # Onsite Comment -None

    try:
        notice_data.contract_duration = page_main.find_element(By.XPATH, "//*[contains(text(),'Duración del contrato')]//following::span[1]").text
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass
    

    # Onsite Field -Alcance
    # Onsite Comment -0 - National Competitivie Bidding, 1 - International Competitive Bidding, 2 -	Others	OTHERS


    try:
        procurement_method = page_main.find_element(By.XPATH, "//*[contains(text(),'Alcance')]//following::span[1]").text
        if "Nacional" in procurement_method:
            notice_data.procurement_method = 0
        elif "Internacional" in procurement_method:
            notice_data.procurement_method = 1
        else:
            notice_data.procurement_method = 2
    except Exception as e: 
        logging.info("Exception in procurement_method: {}".format(type(e).__name__))
        pass
    
    try:
        currency = page_main.find_element(By.XPATH, "//*[contains(text(),'Moneda')]//following::span[1]").text
        if "Peso Argentino" in currency:
            notice_data.currency = 'ARS'
        elif '''Dolar Estadounidense
    Peso Argentino''' in currency:
            notice_data.currency = 'ARS'
        else:
            notice_data.currency = 'USD'
    except:
        logging.info("Exception in currency: {}".format(type(e).__name__))
        pass

    try:
        len_lot = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#ctl00_CPH1_UCVistaPreviaPliego_UC_DetalleProductos_gvLineaPliego > tbody > tr')))
        len_length = len(len_lot)
        id_no = 2
        for single_record in range(len_length):
            Acciones_clk = WebDriverWait(page_main, 100).until(EC.element_to_be_clickable((By.ID, 'ctl00_CPH1_UCVistaPreviaPliego_UC_DetalleProductos_gvLineaPliego_ctl0'+str(id_no)+'_lnkVerItem')))
            page_main.execute_script("arguments[0].click();",Acciones_clk)
            time.sleep(10)

            try:
                notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, '#ModVerItem > div > div > div.modal-body').get_attribute("outerHTML")                     
            except:
                pass
            
            try:
                lot_description = page_main.find_element(By.CSS_SELECTOR, '#ctl00_CPH1_UCVistaPreviaPliego_UC_DetalleProductos_PopUpTableEntrega_ctl02_PlazoGrid').text
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass

            try:
                close_clk = WebDriverWait(page_main, 60).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="ModVerItem"]/div/div/div[1]/button'))).click()
                time.sleep(10)
            except:
                pass
            id_no +=1
    except:
        pass
    
    try:     
        for single_record in page_main.find_elements(By.CSS_SELECTOR, '#ctl00_CPH1_UCVistaPreviaPliego_UC_DetalleProductos_gvLineaPliego > tbody > tr'):
            lot_details_data = lot_details()
            
            lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, ' td:nth-child(4)').text
            lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
        # Onsite Field -Número renglón
        # Onsite Comment -None

            try:
                lot_number = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
                lot_details_data.lot_number = int(lot_number)
            except Exception as e:
                logging.info("Exception in lot_number: {}".format(type(e).__name__))
                pass

            # Onsite Field -Descripción
            # Onsite Comment -None

            try:
                lot_details_data.lot_actual_number = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass

            # Onsite Field -Cantidad
            # Onsite Comment -None

            try:
                lot_details_data.lot_quantity_uom = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
            except Exception as e:
                logging.info("Exception in lot_quantity_uom: {}".format(type(e).__name__))
                pass

            # Onsite Field -Plazo de entrega
            # Onsite Comment -Click on "Acciones"

            try:
                lot_details_data.lot_description = lot_description
                lot_details_data.lot_description_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_description)
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass

            # Onsite Field -Descripción
            # Onsite Comment -None

            try:
                for single_record in page_main.find_elements(By.CSS_SELECTOR, '#ctl00_CPH1_UCVistaPreviaPliego_UCDetalleImputacionAdjudicacion_gvDetalleImputacion > tbody > tr'):
                    award_details_data = award_details()
                    # Onsite Field -Fecha perfeccionamiento
                    # Onsite Comment -split data from "Fecha perfeccionamiento" for award date

                    award_date = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(6)').text
                    award_date = re.findall('\d+/\d+/\d{4}',award_date)[0]
                    award_details_data.award_date = datetime.strptime(award_date,'%d/%m/%Y').strftime('%Y/%m/%d')

                    award_details_data.bidder_country = 'AR'


                    # Onsite Field -Nombre proveedor
                    # Onsite Comment -split data from "Nombre proveedor" for bidder

                    award_details_data.bidder_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
                    
                    # Onsite Field -Monto
                    # Onsite Comment -split data from "Monto" for amount

                    grossawardvaluelc = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(7)').text
                    grossawardvaluelc = re.sub("[^\d\.\,]","",grossawardvaluelc)
                    award_details_data.netawardvalueeuro =float(grossawardvaluelc.replace(',','').replace('.','').strip())
                    award_details_data.netawardvaluelc = award_details_data.netawardvalueeuro

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
        for single_record in page_main.find_elements(By.CSS_SELECTOR, '#ctl00_CPH1_UCVistaPreviaPliego_UC_Clausulas_gvActosAdministrativos > tbody > tr'):
            attachments_data = attachments()
        # Onsite Field -Documento
        # Onsite Comment -None

            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
  
        # Onsite Field -Opciones
        # Onsite Comment -None

            external_url = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(5) a').click()
            file_dwn = Doc_Download.file_download()
            attachments_data.external_url = str(file_dwn[0])

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments1: {}".format(type(e).__name__)) 
        pass
    

    try:              
        for single_record in page_main.find_elements(By.CSS_SELECTOR, '#ctl00_CPH1_UCVistaPreviaPliego_UCAnexos_gvAnexos > tbody > tr')[1:]:
            attachments_data = attachments()
        # Onsite Field -split from"Nombre del Anexo	"
        # Onsite Comment -ref url - "https://comprar.gob.ar/PLIEGO/VistaPreviaPliegoCiudadano.aspx?qs=BQoBkoMoEhxINTWoj4AYQZ4ZG2MnD7C7MKxcSIz5bPR/3rcliBpv|QLG1H0RnSvVpDKNZdDy5r3dbZKYYQinUl6L/8/2KpvdKPcl1FtWrn7V9BuzAIkx4mzFRO2ee15EHMW4CPgiiYo="
            try:
                attachments_data.file_type = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text.split(".")[1]
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -split from" Descripción"
        # Onsite Comment -ref url - "https://comprar.gob.ar/PLIEGO/VistaPreviaPliegoCiudadano.aspx?qs=BQoBkoMoEhxINTWoj4AYQZ4ZG2MnD7C7MKxcSIz5bPR/3rcliBpv|QLG1H0RnSvVpDKNZdDy5r3dbZKYYQinUl6L/8/2KpvdKPcl1FtWrn7V9BuzAIkx4mzFRO2ee15EHMW4CPgiiYo="
        
            attachments_data.file_description = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text      
        
        # Onsite Field -split from" Tipo"
        # Onsite Comment -ref url - "https://comprar.gob.ar/PLIEGO/VistaPreviaPliegoCiudadano.aspx?qs=BQoBkoMoEhxINTWoj4AYQZ4ZG2MnD7C7MKxcSIz5bPR/3rcliBpv|QLG1H0RnSvVpDKNZdDy5r3dbZKYYQinUl6L/8/2KpvdKPcl1FtWrn7V9BuzAIkx4mzFRO2ee15EHMW4CPgiiYo="
        
            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
            
        
        # Onsite Field -split from" Acciones "
        # Onsite Comment -ref url - "https://comprar.gob.ar/PLIEGO/VistaPreviaPliegoCiudadano.aspx?qs=BQoBkoMoEhxINTWoj4AYQZ4ZG2MnD7C7MKxcSIz5bPR/3rcliBpv|QLG1H0RnSvVpDKNZdDy5r3dbZKYYQinUl6L/8/2KpvdKPcl1FtWrn7V9BuzAIkx4mzFRO2ee15EHMW4CPgiiYo="
        
            external_url = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(4) a').click()
            file_dwn = Doc_Download.file_download()
            attachments_data.external_url = str(file_dwn[0])
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments2: {}".format(type(e).__name__)) 
        pass
    

# Onsite Field -Actos administrativos
# Onsite Comment -ref - "https://comprar.gob.ar/PLIEGO/VistaPreviaPliegoCiudadano.aspx?qs=BQoBkoMoEhxTORxfljW9lZZaMjsx54eLALAm3dvRIWzj3hOhssrwEe%7CE7AXGOpqNw0JcGBmJMoCU9oZVhjpxtRRcwPjTvNyixa21r/RWiPax7M7%7CeYqcbOAqQgUDKM8D4/fjHYaVUAs="
    
    try:              
        for single_record in page_main.find_elements(By.CSS_SELECTOR, '#ctl00_CPH1_UCVistaPreviaPliego_UC_ActosAdministrativos_gvActosAdministrativos > tbody > tr'):
            attachments_data = attachments()
        # Onsite Field -split from "Documento"
        # Onsite Comment -ref - "https://comprar.gob.ar/PLIEGO/VistaPreviaPliegoCiudadano.aspx?qs=BQoBkoMoEhxTORxfljW9lZZaMjsx54eLALAm3dvRIWzj3hOhssrwEe%7CE7AXGOpqNw0JcGBmJMoCU9oZVhjpxtRRcwPjTvNyixa21r/RWiPax7M7%7CeYqcbOAqQgUDKM8D4/fjHYaVUAs="
            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, ' td:nth-child(1)').text
        
        # Onsite Field -split from "Opciones"
        # Onsite Comment -ref - "https://comprar.gob.ar/PLIEGO/VistaPreviaPliegoCiudadano.aspx?qs=BQoBkoMoEhxTORxfljW9lZZaMjsx54eLALAm3dvRIWzj3hOhssrwEe%7CE7AXGOpqNw0JcGBmJMoCU9oZVhjpxtRRcwPjTvNyixa21r/RWiPax7M7%7CeYqcbOAqQgUDKM8D4/fjHYaVUAs="
        
            external_url = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(5) a').click()
            file_dwn = Doc_Download.file_download()
            attachments_data.external_url = str(file_dwn[0])
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments3: {}".format(type(e).__name__)) 
        pass

    
    try:
        Actas_Acciones_clk1 = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR, '#ctl00_CPH1_UCVistaPreviaPliego_UC_VistaPreviaActasApertura_gvActasApertura_ctl02_lnkVerActaApertura > span'))).click()
        time.sleep(10)
    except:
        pass
    
    try:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, 'div.container#contenido').get_attribute("outerHTML")                     
    except:
        pass
    
    try:
        Número_clk = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'a#ctl00_CPH1_UCVistaPreviaPliego_UCDetalleImputacionAdjudicacion_gvDetalleImputacion_ctl02_lnkOC'))).click()
        time.sleep(10)
    except:
        pass
    
    try:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, '#aspnetForm > section > div.container').get_attribute("outerHTML")                     
    except:
        pass
    
    try:
        Acciones_clk = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'span.glyphicon.glyphicon-search'))).click()
        time.sleep(10)
    except:
        pass
    
    try:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, 'table#idTabla tr > td:nth-child(2)').get_attribute("outerHTML")                     
    except:
        pass
    
    try:              
        for single_record in page_main.find_elements(By.XPATH, '//*[contains(text(),"Anexos ingresados")]//following::tr')[6:]:
            attachments_data = attachments()
        
            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text.split('.')[0].strip()
        
            external_url = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3) input').click()
            file_dwn = Doc_Download.file_download()
            attachments_data.external_url = str(file_dwn[0])
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments4: {}".format(type(e).__name__)) 
        pass
    
    try:
        try:
            back_clk = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'a#ctl00_CPH1_UCDetalleInformacionEconomica_lnkVolver'))).click()
            time.sleep(3)
        except:
            back_clk = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'td.dxpcCloseButton'))).click()
            time.sleep(3)
    except:
        pass
    
    try:
        back_clk = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR, '#ctl00_CPH1_LinkVolver'))).click()
        time.sleep(3)
    except:
        pass
    
    try:
        back_clk = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR, '#ctl00_CPH1_lnkVolver'))).click()
        time.sleep(5)
    except:
        pass
    
    try:
        back_clk = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR, '#ctl00_CPH1_lnkVolver'))).click()
        time.sleep(5)
    except:
        pass
    
    try:
        WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="ctl00_CPH1_GridListaPliegos"]/tbody/tr'))).text
    except:
        pass
        
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
        
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
page_main = Doc_Download.page_details
page_main.maximize_window()
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://comprar.gob.ar/BuscarAvanzado.aspx"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        index=[1,2]
        for i in index:
            select_fr = Select(page_main.find_element(By.CSS_SELECTOR,'#ctl00_CPH1_ddlEstadoProceso'))
            select_fr.select_by_index(i)
            time.sleep(5)
            
            click2 = WebDriverWait(page_main, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#ctl00_CPH1_btnListarPliegoAvanzado')))
            page_main.execute_script("arguments[0].click();",click2)
            time.sleep(5)
            try:
                for page_no in range(2,5):#5
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
            except:
                logging.info("No new record")
                pass
            
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)