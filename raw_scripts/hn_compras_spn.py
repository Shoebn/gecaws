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
from gec_common import functions as fn
import gec_common.Doc_Download




#Note:First click on this "Etapa de Aquisición" tab select "Elaboración","Revisado","Recepción de Ofertas","Evaluación","Desierto" and "Fracasados" respectievely and grab the data. Than click on this "Buscar" button




NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "hn_compras_spn"
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
    notice_data.script_name = 'hn_compras_spn'
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'HN'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'HNL'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'ES'
    
    # Onsite Field -None
    # Onsite Comment -Note:If tender_html_element page in this "#ctl00_cphCuerpo_gvResultados  tr td:nth-child(3)" selector have this keywod "Licitación pública nacional" than procurement_method -"0" and "Precalificación" take procurement_method -"2" and "Concurso público nacional" take procurement_method -"0" and "Contratación directa" take procurement_method -"2" and "Compra Menor" take procurement_method -"2"
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -Note:In "Etapa de Aquisición" tab select "Elaboración","Revisado","Recepción de Ofertas","Evaluación","Desierto" and "Fracasados" respectievely and grab the data.
    notice_data.notice_type = 4
    
    # Onsite Field -Expediente
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'Label6').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Objeto Compra:
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'Label5').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Fecha Inicio:
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "Label3").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Fecha Cierre:
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "Label4").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Ver Detalle
    # Onsite Comment -Note:Click this and grab the data

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'hlGoTo').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#Table_01 > tbody > tr:nth-child(3)').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    # Onsite Field -Tipo Adquisición
    # Onsite Comment -Note:Replace following keywords with given keywords("Suministro de Bienes y/o Servicios=Supply", " Obras=Services" , "Consultoriac=Consultancy")

    try:
        notice_data.notice_contract_type = page_details.find_element(By.XPATH, '//*[contains(text(),"Tipo Adquisición")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Valor Pliegos
    # Onsite Comment -None

    try:
        notice_data.document_fee = page_details.find_element(By.XPATH, '//*[contains(text(),"Valor Pliegos")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in document_fee: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Productos y/o Servicios Solicitados >> UNSPSC
    # Onsite Comment -Note:Click on this "Detalle de la Compra >> Productos y/o Servicios Solicitados" tab then grab the data
    #Note:Click on this "Detalle de la Compra >> Productos y/o Servicios Solicitados" tab then grab the data
    #Ref_url=http://sicc.honducompras.gob.hn/HC/Procesos/ProcesoHistorico.aspx?Id0=NgAAADUAAAA0AAAA-wMPUtVKuLz8%3d&Id1=MQAAAA%3d%3d-OFoziWLXW%2fg%3d&Id2=TAAAAFAAAABOAAAAIAAAADEAAAA1AAAALQAAADIAAAAwAAAAMgAAADMAAAAgAAAASgAAAFUAAABaAAAARwAAAEEAAABEAAAATwAAACAAAABEAAAARQAAACAAAABQAAAAQQAAAFoAAAAgAAAARAAAAEUAAAAgAAAAQwAAAFUAAAA%3d-0oBYHCMm2to%3d
    try:
        notice_data.category = page_details.find_element(By.CSS_SELECTOR, "#x\:1955457169\.13\:adr\:0\:tag\: > td:nth-child(1)").text
        cpv_codes = fn.CPV_mapping("assets/hn_compras_spn_unspscpv.csv",notice_data.category)
        for cpv_code in cpv_codes:
            cpvs_data = cpvs()
            cpvs_data.cpv_code = cpv_code
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in category: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -Note:Click on this "Detalle de la Compra >> Documentos" tab then grab the data

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#Table_01 > tbody > tr:nth-child(3)'):
            attachments_data = attachments()
        # Onsite Field -Documentos >> Archivo
        # Onsite Comment -Note:Don't take file extention

            try:
                attachments_data.file_name = page_details.find_element(By.CSS_SELECTOR, 'hlDocs').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Documentos >> Archivo
        # Onsite Comment -Note:Take only file extention

            try:
                attachments_data.file_type = page_details.find_element(By.CSS_SELECTOR, 'hlDocs').text
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Documentos >> Archivo
        # Onsite Comment -None

            attachments_data.external_url = page_details.find_element(By.CSS_SELECTOR, 'hlDocs').get_attribute('href')
            
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#Table_01 > tbody > tr:nth-child(3)'):
            customer_details_data = customer_details()
        # Onsite Field -Entidad
        # Onsite Comment -None

            try:
                customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'Label1').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Contacto
        # Onsite Comment -None

            try:
                customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Contacto")]//following::td[1]/span[1]').text
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Contacto
        # Onsite Comment -None

            try:
                customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Contacto")]//following::td[1]/span[2]').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Contacto
        # Onsite Comment -None

            try:
                customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Contacto")]//following::td[1]/a').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
        
            customer_details_data.org_country = 'HN'
            customer_details_data.org_language = 'ES'
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
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
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["http://sicc.honducompras.gob.hn/HC/Procesos/BusquedaHistorico.aspx"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,3):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="ctl00_cphCuerpo_gvResultados"]/tbody/tr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="ctl00_cphCuerpo_gvResultados"]/tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="ctl00_cphCuerpo_gvResultados"]/tbody/tr')))[records]
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="ctl00_cphCuerpo_gvResultados"]/tbody/tr'),page_check))
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