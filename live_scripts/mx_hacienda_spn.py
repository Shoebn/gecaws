from gec_common.gecclass import *
import logging
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
import gec_common.Doc_Download_ingate as Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "mx_hacienda_spn"
Doc_Download = Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    # Onsite Field -None
    # Onsite Comment -Click on "Difusión de procedimientos > Vigentes CompraNet 5.0" to get the data 
    notice_data.script_name = 'mx_hacienda_spn'
    notice_data.main_language = 'ES'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'MX'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'MXN'
    notice_data.procurement_method = 2
    notice_data.notice_type = 4
    notice_data.notice_url = url

    try:
        document_type_description = tender_html_element.find_element(By.XPATH, '//*[@id="navigationSecondLevel"]/div/div/div[1]').text
        notice_data.document_type_description = GoogleTranslator(source='auto', target='en').translate(document_type_description)
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Descripción del Expediente
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Plazo de participación o vigencia del anuncio
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(7)").text
        notice_deadline = re.findall('\d+/\d+/\d{4} \d+:\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Referencia del Expediente
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Tipo de Contratación
    # Onsite Comment -Replace following keywords with given respective keywords ('Adquisiciones = Supply','Arrendamientos = Services','Servicios = Services','Obra Pública = Work','Servicios Relacionados con la OP = Services')

    try:
        notice_contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(6)').text
        if 'Adquisiciones' in notice_contract_type:
            notice_data.notice_contract_type = 'Supply'
        elif 'Arrendamientos' in notice_contract_type or 'Servicios Relacionados con la OP' in notice_contract_type or 'Servicios' in notice_contract_type:
            notice_data.notice_contract_type = 'Service'
        elif 'Obra Pública' in notice_contract_type:
            notice_data.notice_contract_type = 'Works'
        else:
            pass
            
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Descripción del Expediente
    # Onsite Comment -None

    try:
        notice_url = WebDriverWait(tender_html_element, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'td:nth-child(5) > a'))).click()                   
    except:
        pass

    try:
        notice_data.notice_text += WebDriverWait(page_main, 40).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.bodyWrapper'))).get_attribute("outerHTML")                  
    except:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    # Onsite Field -Descripción del Anuncio
    # Onsite Comment -None

    try:                                                             
        notice_summary_english = page_main.find_element(By.XPATH, '//*[contains(text(),"Descripción del Anuncio")]//following::div[1]').text
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_summary_english)
        notice_data.local_description = notice_summary_english
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Fecha de publicación del anuncio (Convocatoria / Invitación / Adjudicación / Proyecto de Convocatoria)
    # Onsite Comment -None

    try:
        publish_date = page_main.find_element(By.XPATH, '//*[contains(text(),"Fecha de publicación del anuncio (Convocatoria / Invitación / Adjudicación / Proyecto de Convocatoria)")]//following::div[1]').text
        publish_date = re.findall('\d+/\d+/\d{4} \d+:\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    try:              
        customer_details_data = customer_details()
    # Onsite Field -Nombre de la Unidad Compradora (UC)
    # Onsite Comment -None
        try:
            customer_details_data.org_name = page_main.find_element(By.XPATH, '//*[contains(text(),"Nombre de la Unidad Compradora (UC)")]//following::div[1]').text
        except Exception as e:
            logging.info("Exception in org_name: {}".format(type(e).__name__))
            pass

    # Onsite Field -Nombre del Operador en la UC
    # Onsite Comment -None

        try:
            customer_details_data.contact_person = page_main.find_element(By.XPATH, '//*[contains(text(),"Nombre del Operador en la UC")]//following::div[1]').text
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass

    # Onsite Field -Correo Electrónico del Operador en la UC
    # Onsite Comment -None

        try:
            customer_details_data.org_email = page_main.find_element(By.XPATH, '//*[contains(text(),"Correo Electrónico del Operador en la UC")]//following::div[1]').text.split(';')[0].strip()
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass

        customer_details_data.org_country = 'MX'
        customer_details_data.org_language = 'ES'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try:              
        lot_number = 1
        lot_details_data = lot_details()
        lot_details_data.lot_number = lot_number
    # Onsite Field -Descripción del Expediente
    # Onsite Comment -None

        try:
            lot_details_data.lot_title = notice_data.notice_title
            notice_data.is_lot_default = True
        except Exception as e:
            logging.info("Exception in lot_title: {}".format(type(e).__name__))
            pass

    # Onsite Field -Descripción del Anuncio
    # Onsite Comment -None

        try:
            lot_details_data.lot_description = notice_data.notice_summary_english
        except Exception as e:
            logging.info("Exception in lot_description: {}".format(type(e).__name__))
            pass
        
    # Onsite Field -Duración del Contrato
    # Onsite Comment -None

        try:
            lot_details_data.contract_duration = page_main.find_element(By.XPATH, '//*[contains(text(),"Duración del Contrato")]//following::div[1]').text.strip()
            notice_data.contract_duration = lot_details_data.contract_duration
        except Exception as e:
            logging.info("Exception in contract_duration: {}".format(type(e).__name__))
            pass

    # Onsite Field -Fecha de Inicio del Contrato
    # Onsite Comment -None

        try:
            contract_start_date = page_main.find_element(By.XPATH, '//*[contains(text(),"Fecha de Inicio del Contrato")]//following::div[1]').text
            contract_start_date = re.findall('\d+/\d+/\d{4}',contract_start_date)[0]
            lot_details_data.contract_start_date = datetime.strptime(contract_start_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
            notice_data.tender_contract_start_date = lot_details_data.contract_start_date
        except Exception as e:
            logging.info("Exception in contract_start_date: {}".format(type(e).__name__))
            pass
        
    # Onsite Field -Fecha estimada de conclusión del contrato
    # Onsite Comment -None

        try:
            contract_end_date = page_main.find_element(By.XPATH, '//*[contains(text(),"Fecha estimada de conclusión del contrato")]//following::div[1]').text
            contract_end_date = re.findall('\d+/\d+/\d{4}',contract_end_date)[0]
            lot_details_data.contract_end_date = datetime.strptime(contract_end_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
            notice_data.tender_contract_end_date = lot_details_data.contract_end_date
        except Exception as e:
            logging.info("Exception in contract_end_date: {}".format(type(e).__name__))
            pass

        lot_details_data.lot_details_cleanup()
        notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
# # Onsite Field -None
# # Onsite Comment -'DATOS GENERALES DEL PROCEDIMIENTO DE CONTRATACIÓN' / 'Anexos adicionales'	('https://compranet.hacienda.gob.mx/esop/toolkit/opportunity/current/2231873/detail.si' use this link for ref)

    try:              
        for single_record in page_main.find_elements(By.CSS_SELECTOR, 'div.bodyWrapper  tr > td > div > div'):
            attachments_data = attachments()
        # Onsite Field -'DATOS GENERALES DEL PROCEDIMIENTO DE CONTRATACIÓN' / 'Anexos adicionales'
        # Onsite Comment -'tr> td:nth-child(2) > a'  split file_type and take file_type in textform from both the selector

            attachments_data.file_type = single_record.find_element(By.CSS_SELECTOR, 'a').text.split('.')[-1].strip()

        # Onsite Field -'DATOS GENERALES DEL PROCEDIMIENTO DE CONTRATACIÓN' / 'Anexos adicionales'
        # Onsite Comment -'tr> td:nth-child(2) > a' 	split file_name and take file_name in textform from both the selector

            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'a').text
        
        # Onsite Field -'DATOS GENERALES DEL PROCEDIMIENTO DE CONTRATACIÓN' / 'Anexos adicionales'
        # Onsite Comment -'tr> td:nth-child(2) > a' 	split file_size  and take file_name in textform from both the selector

            attachments_data.file_size = single_record.text.split('(')[1].split(')')[0]
        
        # Onsite Field -'DATOS GENERALES DEL PROCEDIMIENTO DE CONTRATACIÓN' / 'Anexos adicionales'
        # Onsite Comment -'tr> td:nth-child(2) > a '    take attachment from both the selector

            external_url = single_record.find_element(By.CSS_SELECTOR, 'a').click()
            file_dwn = Doc_Download.file_download()
            attachments_data.external_url= (str(file_dwn[0]))
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass 
    
    try:              
        for single_record in page_main.find_elements(By.CSS_SELECTOR, '#opportunityDetailFEBean > div > table:nth-child(19) > tbody > tr > td:nth-child(2)'):
            attachments_data = attachments()

            attachments_data.file_type = single_record.find_element(By.CSS_SELECTOR, 'a').text.split('.')[-1].strip()

            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'a').text

            attachments_data.file_size = single_record.text.split('(')[1].split(')')[0]

            external_url = single_record.find_element(By.CSS_SELECTOR, 'a').click()
            file_dwn = Doc_Download.file_download()
            attachments_data.external_url= (str(file_dwn[0]))

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    try:              
        for single_record in page_main.find_elements(By.XPATH, '//*[contains(text(),"Anexos adicionales")]//following::tr')[1:]:
            attachments_data = attachments()

            attachments_data.file_type = single_record.find_element(By.CSS_SELECTOR, 'a').get_attribute('title').split('.')[-1].strip()

            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'a').get_attribute('title').split(':')[1].split(attachments_data.file_type)[0]
            
            try:
                attachments_data.file_size = single_record.text.split('(')[1].split(')')[0]
            except Exception as e:
                logging.info("Exception in file_size: {}".format(type(e).__name__)) 
                pass 
            
            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass 
    
    bck = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR, '#mainToolbar > ul.leftArea > li > a > span')))
    page_main.execute_script("arguments[0].click();",bck)
    time.sleep(20)
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    WebDriverWait(page_main, 100).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="OpportunityListManager"]/div/table/tbody[2]/tr')))
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
page_main = Doc_Download.page_details
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://compranet.hacienda.gob.mx/web/login.html'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        try:
            clk = page_main.find_element(By.CSS_SELECTOR, '#navbar > ul > li:nth-child(3)').click()
        except:
            pass
        
        try:
            clk1 = page_main.find_element(By.CSS_SELECTOR, '#navbar > ul > li.dropdown.open > ul > li:nth-child(2) > a').click()
            time.sleep(10)
        except:
            pass
        
        page_main.switch_to.window(page_main.window_handles[1])

        try:
            rows = WebDriverWait(page_main, 80).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="OpportunityListManager"]/div/table/tbody[2]/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 80).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="OpportunityListManager"]/div/table/tbody[2]/tr')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break
        except:
            logging.info("No new record")
            break

    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)