#click on following types individual from "Estado proceso:" for spn

#In Opening - En Apertura
#Published - Publicado


from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "ar_comprar_spn"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from deep_translator import GoogleTranslator
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
import gec_common.OutputJSON
from gec_common import functions as fn
import gec_common.Doc_Download as Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 20000
notice_count = 0
tnotice_count = 0
SCRIPT_NAME = "ar_comprar_spn"
Doc_Download = Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    global tender_no
    global tnotice_count
    notice_data = tender()

    notice_data.script_name = 'ar_comprar_spn'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'AR'
    notice_data.performance_country.append(performance_country_data)

    notice_data.main_language = 'ES'
    notice_data.notice_type = 4
    

    # Onsite Field -Estado
    # Onsite Comment -None

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    # Onsite Field -Nombre proceso
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

#     notice_data.publish_date = 'take it as threshold'
    
    # Onsite Field -Fecha de apertura
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(5) > p").text
        notice_deadline = re.findall('\d+/\d+/\d{4} \d+:\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Process number
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    
    
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_language = 'ES'
        customer_details_data.org_country = 'AR'
    # Onsite Field -Unidad Ejecutora
    # Onsite Comment -None

        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, '#ctl00_CPH1_GridListaPliegos td:nth-child(7)').text

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try:
        notice_url = WebDriverWait(tender_html_element, 80).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"td:nth-child(1) a")))
        notice_url.location_once_scrolled_into_view
        details = WebDriverWait(tender_html_element, 180).until(EC.presence_of_element_located((By.CSS_SELECTOR,'td:nth-child(1) a'))).text
        while True:
            notice_url = WebDriverWait(tender_html_element, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'td:nth-child(1) a')))
            page_main.execute_script("arguments[0].click();",notice_url)
            time.sleep(4)
            break
        time.sleep(5)
        notice_url_data = page_main.current_url
        notice_data.notice_url = notice_url_data.replace('|','%7C')
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
        
    try:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, '#aspnetForm > section > div.container').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    # Onsite Field -Información del contrato
    # Onsite Comment -None

    try:
        notice_data.contract_duration = page_main.find_element(By.XPATH, '''//*[contains(text(),'Duración del contrato')]//following::span[1]''').text
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass
    
    
    try:
        publish_date = page_main.find_element(By.XPATH, '''//*[contains(text(),"estimada de publicación")]//following::span[1]''').text
        try:
            publish_date = re.findall('\d+/\d+/\d{4} \d+:\d+',publish_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.publish_date)
        except:
            publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
    
    try:  
        currency = page_main.find_element(By.XPATH, '''//*[contains(text(),'Moneda')]//following::span[1]''').text
        if 'Peso Argentino' in currency:
            notice_data.currency = 'ARS'
        elif '''Dolar Estadounidense Peso Argentino''' in currency:
            notice_data.currency = 'ARS'
        elif 'Dolar Estadounidense' in currency:
            notice_data.currency = 'USD'
    except Exception as e:
        logging.info("Exception in currency: {}".format(type(e).__name__))
        pass
    # Onsite Field -Alcance
    # Onsite Comment -None

    try:
        procurement_method = page_main.find_element(By.XPATH, '''//*[contains(text(),'Alcance')]//following::span[1]''').text
        if 'Internacional' in procurement_method:
            notice_data.procurement_method = 1
        elif 'Nacional' in procurement_method:
            notice_data.procurement_method = 0
        else:
            notice_data.procurement_method = 2
    except Exception as e:
        logging.info("Exception in procurement_method: {}".format(type(e).__name__))
        pass
    
    try:
        len_lot = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#ctl00_CPH1_UCVistaPreviaPliego_UC_DetalleProductos_gvLineaPliego > tbody > tr')))
        len_length = len(len_lot)
        id_no = 2
        for single_record in range(len_length):
            Acciones_clk = WebDriverWait(page_main, 100).until(EC.element_to_be_clickable((By.ID, 'ctl00_CPH1_UCVistaPreviaPliego_UC_DetalleProductos_gvLineaPliego_ctl0'+str(id_no)+'_lnkVerItem')))
            page_main.execute_script("arguments[0].click();",Acciones_clk)
            time.sleep(15)

            try:
                notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, '#ModVerItem > div > div > div.modal-body').get_attribute("outerHTML")                     
            except:
                pass

            try:
                description = page_main.find_element(By.CSS_SELECTOR, '#ctl00_CPH1_UCVistaPreviaPliego_UC_DetalleProductos_PopUpTableEntrega_ctl02_PlazoGrid').text
            except Exception as e:
                logging.info("Exception in description: {}".format(type(e).__name__))
                pass

            close_clk = WebDriverWait(page_main, 80).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="ModVerItem"]/div/div/div[1]/button'))).click()
            time.sleep(12)
            id_no +=1
    
    except Exception as e:
        logging.info("Exception in description: {}".format(type(e).__name__))
        pass

    try:
        for single_record in page_main.find_elements(By.CSS_SELECTOR, '#ctl00_CPH1_UCVistaPreviaPliego_UC_DetalleProductos_gvLineaPliego > tbody > tr'):
            lot_details_data = lot_details()
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
            
        # Onsite Field -Descripción
        # Onsite Comment -None

            lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
            lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
        
        # Onsite Field -Cantidad
        # Onsite Comment -None
            try:
                lot_quantity = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text.split(' ')[0].strip()
                lot_quantity1 = lot_quantity.replace('.','').replace(',','.').strip()
                lot_details_data.lot_quantity = float(lot_quantity1)
            except Exception as e:
                logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                pass

            try:
                lot_details_data.lot_quantity_uom = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text.split(' ')[1].strip()
            except Exception as e:
                logging.info("Exception in lot_quantity_uom: {}".format(type(e).__name__))
                pass
    
                
            try:
                lot_details_data.lot_description = description
                lot_details_data.lot_description_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_description)
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass

            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -Cláusulas particulares
# Onsite Comment -ref url - "https://comprar.gob.ar/PLIEGO/VistaPreviaPliegoCiudadano.aspx?qs=BQoBkoMoEhwumpMNyHQewJlcx1N|AmyJbUFIiklDVkwaD2WJncFvb6bXOaI0Zix5bxlQ6Ct701Ouh7gNgnHsB1cPgCwOwSgJW2Z7Y9lGZJz|UK0449LZc1baGTcwdDlmaucbIF0YjRE="

    try:              
        for single_record in page_main.find_elements(By.CSS_SELECTOR, '#ctl00_CPH1_UCVistaPreviaPliego_UC_Clausulas_gvActosAdministrativos > tbody > tr'):
            attachments_data = attachments()
        # Onsite Field -Documento
        # Onsite Comment -None

            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text

        # Onsite Field -Opciones
        # Onsite Comment -None
            external_url = WebDriverWait(single_record, 100).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'td:nth-child(5) > a')))
            page_main.execute_script("arguments[0].click();",external_url)
            time.sleep(5)
            file_dwn = Doc_Download.file_download()
            attachments_data.external_url = str(file_dwn[0])
            
            try:
                attachments_data.file_type = attachments_data.external_url.split('.')[-1]
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
            
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments1: {}".format(type(e).__name__)) 
        pass

    try:              
        for single_record in page_main.find_elements(By.CSS_SELECTOR, '#ctl00_CPH1_UCVistaPreviaPliego_UCAnexos_gvAnexos > tbody > tr')[1:]:
            attachments_data = attachments()
        # Onsite Field -split from"Nombre del Anexo	"
        # Onsite Comment -ref url - "https://comprar.gob.ar/PLIEGO/VistaPreviaPliegoCiudadano.aspx?qs=BQoBkoMoEhwe72B%2fIHv808CBsW0BoGkRMU6mB8qIyZQwL4F6j3YTBI1229sLpTVZt8XDRkP%2fy%7cqRJ5OvzZQejxu3Tx9W3V6%7cnezCvqARx8JkIShRNxkC5iP1%7ca7AjCRQfB9kN4fNoaM%3d"

            try:
                attachments_data.file_type = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text.split('.')[-1]
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -split from" Descripción"
        # Onsite Comment -ref url - "https://comprar.gob.ar/PLIEGO/VistaPreviaPliegoCiudadano.aspx?qs=BQoBkoMoEhwe72B%2fIHv808CBsW0BoGkRMU6mB8qIyZQwL4F6j3YTBI1229sLpTVZt8XDRkP%2fy%7cqRJ5OvzZQejxu3Tx9W3V6%7cnezCvqARx8JkIShRNxkC5iP1%7ca7AjCRQfB9kN4fNoaM%3d"

            try:
                attachments_data.file_description = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
            except Exception as e:
                logging.info("Exception in file_description: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -split from" Tipo"
        # Onsite Comment -ref url - "https://comprar.gob.ar/PLIEGO/VistaPreviaPliegoCiudadano.aspx?qs=BQoBkoMoEhwe72B%2fIHv808CBsW0BoGkRMU6mB8qIyZQwL4F6j3YTBI1229sLpTVZt8XDRkP%2fy%7cqRJ5OvzZQejxu3Tx9W3V6%7cnezCvqARx8JkIShRNxkC5iP1%7ca7AjCRQfB9kN4fNoaM%3d"

            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        
        # Onsite Field -split from" Acciones "
        # Onsite Comment -ref url - "https://comprar.gob.ar/PLIEGO/VistaPreviaPliegoCiudadano.aspx?qs=BQoBkoMoEhwe72B%2fIHv808CBsW0BoGkRMU6mB8qIyZQwL4F6j3YTBI1229sLpTVZt8XDRkP%2fy%7cqRJ5OvzZQejxu3Tx9W3V6%7cnezCvqARx8JkIShRNxkC5iP1%7ca7AjCRQfB9kN4fNoaM%3d"
            external_url = WebDriverWait(single_record, 80).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'td:nth-child(4) a')))
            page_main.execute_script("arguments[0].click();",external_url)
            time.sleep(5)
            file_dwn = Doc_Download.file_download()
            attachments_data.external_url = str(file_dwn[0])
            
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments2: {}".format(type(e).__name__)) 
        pass
    
    # Onsite Field -Actos administrativos
    # Onsite Comment -ref - "https://comprar.gob.ar/PLIEGO/VistaPreviaPliegoCiudadano.aspx?qs=BQoBkoMoEhyF3OG6iZmbWp7BaLL|IczBzAqs7RjRwQrURc2nItuCuMrdquaJd97AHBE77QFt8E74hDUi8EzJJdYeUqzaZ9MOw3BLkdA139fcLi/9FoseMN2TnrJ9lwQeXhZ2vzPTPeg="

    try:              
        for single_record in page_main.find_elements(By.CSS_SELECTOR, '#ctl00_CPH1_UCVistaPreviaPliego_UC_ActosAdministrativos_gvActosAdministrativos > tbody > tr'):
            attachments_data = attachments()
        # Onsite Field -split from "Documento"
        # Onsite Comment -ref - "https://comprar.gob.ar/PLIEGO/VistaPreviaPliegoCiudadano.aspx?qs=BQoBkoMoEhyF3OG6iZmbWp7BaLL|IczBzAqs7RjRwQrURc2nItuCuMrdquaJd97AHBE77QFt8E74hDUi8EzJJdYeUqzaZ9MOw3BLkdA139fcLi/9FoseMN2TnrJ9lwQeXhZ2vzPTPeg="

            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text

        # Onsite Field -split from "Opciones"
        # Onsite Comment -ref - "https://comprar.gob.ar/PLIEGO/VistaPreviaPliegoCiudadano.aspx?qs=BQoBkoMoEhyF3OG6iZmbWp7BaLL|IczBzAqs7RjRwQrURc2nItuCuMrdquaJd97AHBE77QFt8E74hDUi8EzJJdYeUqzaZ9MOw3BLkdA139fcLi/9FoseMN2TnrJ9lwQeXhZ2vzPTPeg="

            external_url = WebDriverWait(single_record, 80).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'td:nth-child(5) a')))
            page_main.execute_script("arguments[0].click();",external_url)
            time.sleep(5)
            file_dwn = Doc_Download.file_download()
            attachments_data.external_url = str(file_dwn[0])
            
            try:
                attachments_data.file_type = attachments_data.external_url.split('.')[-1]
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments3: {}".format(type(e).__name__)) 
        pass
    
    
    try:
        de_apertura_click = WebDriverWait(page_main, 80).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#ctl00_CPH1_UCVistaPreviaPliego_UC_VistaPreviaActasApertura_gvActasApertura_ctl02_lnkVerActaApertura')))
        page_main.execute_script("arguments[0].click();",de_apertura_click)
        time.sleep(2)
    
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, '#contenido').get_attribute("outerHTML")                     
    
        Volver_clk = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'a#ctl00_CPH1_lnkVolver.btn.btn-default'))).click()
        time.sleep(2)
    except:
        pass
    
    try:
        de_evaluacion_de_ofertas_click = WebDriverWait(page_main, 80).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#ctl00_CPH1_UCVistaPreviaPliego_UC_VistaPreviaDictamenesPreAdjudicacion_gvDictamenesPreAdjudicacion_ctl02_lnkVerDictamen')))
        page_main.execute_script("arguments[0].click();",de_evaluacion_de_ofertas_click)
        time.sleep(2)
   
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, '#aspnetForm > section > div > div.container').get_attribute("outerHTML")                     
    
        Volver_clk = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'a#ctl00_CPH1_lnkVolver.btn.btn-default'))).click()
        time.sleep(2)
    except:
        pass
    
    
    try:
        Volver_clk = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'a#ctl00_CPH1_lnkVolver.btn.btn-default'))).click()
        time.sleep(2)
    except:
        pass
    
    WebDriverWait(page_main, 150).until(EC.presence_of_element_located((By.XPATH,'//*[@id="ctl00_CPH1_GridListaPliegos"]/tbody/tr'))).text

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
    tnotice_count += 1
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
        fn.load_page(page_main, url, 80)
        logging.info('----------------------------------')
        logging.info(url)

        indx_num = [7,14]
        
        for i in indx_num:
            pp_btn = Select(page_main.find_element(By.CSS_SELECTOR,'#ctl00_CPH1_ddlEstadoProceso'))
            pp_btn.select_by_index(i)
            time.sleep(10)

            buscar = WebDriverWait(page_main, 80).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'a#ctl00_CPH1_btnListarPliegoAvanzado'))).click()
            time.sleep(10)
            try:
                tender_no = 0
                for page_no in range(2,60): #60
                    page_check = WebDriverWait(page_main, 100).until(EC.presence_of_element_located((By.XPATH,'//*[@id="ctl00_CPH1_GridListaPliegos"]/tbody/tr[2]'))).text
                    rows = WebDriverWait(page_main, 80).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="ctl00_CPH1_GridListaPliegos"]/tbody/tr')))
                    length = len(rows)
                    for records in range(tender_no,length-1):
                        tender_html_element = WebDriverWait(page_main, 100).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="ctl00_CPH1_GridListaPliegos"]/tbody/tr')))[records]
                        extract_and_save_notice(tender_html_element)
                        if tnotice_count >= MAX_NOTICES:
                            break

                        if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                            logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                            break


                        if tender_no == 1:
                            tender_no = tender_no
                        else:
                            tender_no +=1

                        if notice_count == 50:
                            output_json_file.copyFinalJSONToServer(output_json_folder)
                            output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
                            notice_count = 0

                    try:   
                        next_page = WebDriverWait(page_main, 80).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                        page_main.execute_script("arguments[0].click();",next_page)
                        logging.info("Next page")
                        WebDriverWait(page_main, 100).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="ctl00_CPH1_GridListaPliegos"]/tbody/tr[2]'),page_check))
                    except Exception as e:
                        logging.info("Exception in next_page: {}".format(type(e).__name__))
                        logging.info("No next page")
                        break
            except:
                logging.info("No new record")
                pass
                

    logging.info("Finished processing. Scraped {} notices".format(tnotice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)
