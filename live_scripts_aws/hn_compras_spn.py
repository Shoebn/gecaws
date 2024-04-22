from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "hn_compras_spn"
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
import gec_common.Doc_Download
from selenium.webdriver.support.ui import Select

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
    
    notice_data.script_name = 'hn_compras_spn'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'HN'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'HNL'
    
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
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1) ').text.split("Expediente: ")[1].split("Entidad")[0].strip()
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Objeto Compra:
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1) ').text.split("Objeto Compra:")[1].strip()
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Fecha Inicio:
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, " td:nth-child(4) ").text
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
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(4) ").text.split("Fecha Cierre:")[1].strip()
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Ver Detalle
    # Onsite Comment -Note:Click this and grab the data

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5) a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#Table_01 > tbody > tr:nth-child(3)').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    # Onsite Field -Tipo Adquisición
    # Onsite Comment -Note:Replace following keywords with given keywords("Suministro de Bienes y/o Servicios=Supply", " Obras=Services" , "Consultoriac=Consultancy")

    try:
        notice_data.contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Tipo Adquisición")]//following::td[1]').text
        if "Obras" in notice_data.contract_type_actual:
            notice_data.notice_contract_type ="Service"
        elif "Suministro de Bienes y/o Servicios" in notice_data.contract_type_actual:
            notice_data.notice_contract_type ="Supply"
        elif "Consultoriac" in notice_data.contract_type_actual or "Consultoria" in notice_data.contract_type_actual:
            notice_data.notice_contract_type = "Consultancy"
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

    try:              
        for single_record in page_details.find_elements(By.XPATH, '/html/body/form/table/tbody/tr[3]/td/table/tbody/tr/td/table/tbody[2]/tr[2]/td/div/div/div[2]/div/table/tbody/tr[1]/td/table/tbody[2]/tr/td/div[2]/table/tbody/tr'):
            attachments_data = attachments()
        # Onsite Field -Documentos >> Archivo
        # Onsite Comment -Note:Don't take file extention

            attachments_data.file_name = single_record.find_element(By.XPATH, 'td[1]').text
            
        # Onsite Field -Documentos >> Archivo
        # Onsite Comment -Note:Take only file extention

            try:
                attachments_data.file_type = single_record.find_element(By.XPATH, 'td[2]').text.split(".")[1]
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Documentos >> Archivo
        # Onsite Comment -None

            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    # Onsite Field -Productos y/o Servicios Solicitados >> UNSPSC
    # Onsite Comment -Note:Click on this "Detalle de la Compra >> Productos y/o Servicios Solicitados" tab then grab the data
    #Note:Click on this "Detalle de la Compra >> Productos y/o Servicios Solicitados" tab then grab the data
    #Ref_url=http://sicc.honducompras.gob.hn/HC/Procesos/ProcesoHistorico.aspx?Id0=NgAAADUAAAA0AAAA-wMPUtVKuLz8%3d&Id1=MQAAAA%3d%3d-OFoziWLXW%2fg%3d&Id2=TAAAAFAAAABOAAAAIAAAADEAAAA1AAAALQAAADIAAAAwAAAAMgAAADMAAAAgAAAASgAAAFUAAABaAAAARwAAAEEAAABEAAAATwAAACAAAABEAAAARQAAACAAAABQAAAAQQAAAFoAAAAgAAAARAAAAEUAAAAgAAAAQwAAAFUAAAA%3d-0oBYHCMm2to%3d

    try:
        next_page = WebDriverWait(page_details, 5).until(EC.element_to_be_clickable((By.XPATH,'/html/body/form/table/tbody/tr[3]/td/table/tbody/tr/td/table/tbody[2]/tr[2]/td/div/span/span/span[1]/span/span/span'))).click()
        time.sleep(10)
    except:
        pass
    
    try:
        notice_data.category = page_details.find_element(By.XPATH, "/html/body/form/table/tbody/tr[3]/td/table/tbody/tr/td/table/tbody[2]/tr[2]/td/div/div/div[1]/div/table/tbody/tr[1]/td/table/tbody[2]/tr/td/div[2]/table/tbody/tr/td[1]").text.strip()
        cpv_codes = fn.CPV_mapping("assets/hn_compras_spn_unspscpv.csv",notice_data.category)

        for cpv_code in cpv_codes:
            cpvs_data = cpvs()
            cpvs_data.cpv_code = cpv_code
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in category: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Productos y/o Servicios Solicitados
# Onsite Comment -Note:Click on this "Detalle de la Compra >> Productos y/o Servicios Solicitados" tab then grab the data

    try:              
        lot_number=1
        for single_record in page_details.find_elements(By.XPATH, '/html/body/form/table/tbody/tr[3]/td/table/tbody/tr/td/table/tbody[2]/tr[2]/td/div/div/div[1]/div/table/tbody/tr[1]/td/table/tbody[2]/tr/td/div[2]/table/tbody/tr'):
            lot_details_data = lot_details()
            lot_details_data.lot_number = lot_number
            lot_details_data.lot_contract_type_actual = notice_data.contract_type_actual
            lot_details_data.contract_type = notice_data.notice_contract_type
        # Onsite Field -Descripción en Español
        # Onsite Comment -None

            lot_details_data.lot_title = single_record.find_element(By.XPATH, 'td[2]').text
            lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
        
        # Onsite Field -Especificaciones
        # Onsite Comment -None

            try:
                lot_details_data.lot_description = single_record.find_element(By.XPATH, 'td[3]').text
                lot_details_data.lot_description_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_description)
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass
            
            try:
                cpvss = single_record.find_element(By.XPATH, "td[1]").text.strip()
                lot_cpv  = fn.CPV_mapping("assets/hn_compras_spn_unspscpv.csv",cpvss)

                for cpv_code in lot_cpv:
                    lot_cpvs_data = lot_cpvs()
                    lot_cpvs_data.lot_cpv_code = cpv_code
                    lot_cpvs_data.lot_cpvs_cleanup()
                    lot_details_data.lot_cpvs.append(lot_cpvs_data)
            except Exception as e:
                logging.info("Exception in lot_cpv: {}".format(type(e).__name__))
                pass
        
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
            lot_number += 1
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    

    try:              
        customer_details_data = customer_details()
    # Onsite Field -Entidad
    # Onsite Comment -None

        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text.split("Entidad:")[1].split("Unidad Compra:")[0].strip()

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
            customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Contacto")]//following::td[1]/span[2]').text.split(" ")[0]
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass

    # Onsite Field -Contacto
    # Onsite Comment -None

        try:
            org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Contacto")]//following::td[1]/a').text
            customer_details_data.org_email = re.findall(r'[\w\.-]+@[\w\.-]+', org_email)[0]
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
    logging.info(notice_data.identifier)
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
        
        index=[1,2,3,4,6,7]
        for i in index:
            select_fr = Select(page_main.find_element(By.CSS_SELECTOR,'#ctl00_cphCuerpo_wpParametros_ddlEtapas'))
            select_fr.select_by_index(i)
            time.sleep(5)

            submit = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#ctl00_cphCuerpo_wpParametros_btnBuscar')))
            page_main.execute_script("arguments[0].click();",submit)
            time.sleep(10)

            try:
                for page_no in range(2,5):
                    page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#ctl00_cphCuerpo_gvResultados > tbody > tr:nth-child(2)'))).text
                    rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#ctl00_cphCuerpo_gvResultados > tbody > tr')))
                    length = len(rows)
                    for records in range(1,length-1):
                        tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#ctl00_cphCuerpo_gvResultados > tbody > tr')))[records]
                        extract_and_save_notice(tender_html_element)
                        if notice_count >= MAX_NOTICES:
                            break
    
                        if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                            break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
    
                    try:   
                        next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                        page_main.execute_script("arguments[0].click();",next_page)
                        logging.info("Next page")
                        WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#ctl00_cphCuerpo_gvResultados > tbody > tr:nth-child(2)'),page_check))
                    except Exception as e:
                        logging.info("Exception in next_page: {}".format(type(e).__name__))
                        logging.info("No next page")
                        break
            except:
                logging.info('No new record')
                break
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit() 
    
    output_json_file.copyFinalJSONToServer(output_json_folder)
