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
SCRIPT_NAME = "es_juntadecia"
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
    notice_data.script_name = 'es_juntadecia'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'ES'
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'ES'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'EUR'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_type = 4



    # Onsite Field -FECHA FIN PRESENTACIÓN
    # Onsite Comment -split the data from tender html page

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(5)").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Número de expediente :
    # Onsite Comment -split the notice_no from page_detail

    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"Número de expediente")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Título de expediente :
    # Onsite Comment -split the title from detail page

    try:
        notice_data.local_title = page_details.find_element(By.XPATH, '//*[contains(text(),"Título de expediente")]//following::div[1]').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Descripción :")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Últimas modificaciones
    # Onsite Comment -take only date , for ex : "03/08/2023 13:26 - Anuncio de Documentación", here split only "03/08/2023", ref url : "https://www.juntadeandalucia.es/haciendayadministracionpublica/apl/pdc_sirec/perfiles-licitaciones/detalle-licitacion.jsf?idExpediente=572628"

    try:
        publish_date = page_details.find_element(By.XPATH, "//*[contains(text(),"Últimas modificaciones")]//following::p[1]").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    

    
    # Onsite Field -TIPO DE CONTRATO
    # Onsite Comment -split the data from detail page,  replace following keywords with given respective keywords ('Servicios' = 'services' , 'Suministros' = 'supply' , 'Concesión de servicios' = 'services' ,  'Administrativo especial' = 'services' , 'obras' = 'works')

    try:
        notice_data.notice_contract_type = page_details.find_element(By.XPATH, '//*[contains(text(),"Tipo de contrato ")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
# Onsite Field -Importe de licitación (CON IVA) :
    # Onsite Comment -split the data between "Importe de licitación (SIN IVA) :" and "Valor estimado : " field

    try:
        notice_data.est_amount = page_details.find_element(By.XPATH, '//*[contains(text(),"Importe de licitación (CON IVA")]//following::span').text
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Importe de licitación (CON IVA) :
    # Onsite Comment -split the data between "Importe de licitación (SIN IVA) :" and "Valor estimado : " field

    try:
        notice_data.grossbudgetlc = page_details.find_element(By.XPATH, '//*[contains(text(),"Importe de licitación (CON IVA")]//following::span').text
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
 
    # Onsite Field -Importe de licitación (SIN IVA) :
    # Onsite Comment -None

    try:
        notice_data.netbudgetlc = page_details.find_element(By.XPATH, '//*[contains(text(),"Importe de licitación (SIN IVA")]//following::span').text
    except Exception as e:
        logging.info("Exception in netbudgetlc: {}".format(type(e).__name__))
        pass
     
    # Onsite Field -Procedimiento :
    # Onsite Comment -split the data from detail page
    try:
        notice_data.type_of_procedure_actual = page_details.find_element(By.XPATH, "//*[contains(text(),"Procedimiento")]//following::div[1]").text
        notice_data.type_of_procedure = fn.procedure_mapping("assets/es_juntadecia_procedure",notice_data.type_of_procedure_actual)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Perfiles y Licitaciones
    # Onsite Comment -split the data from detail page

    try:
        notice_data.document_type_description = page_details.find_element(By.CSS_SELECTOR, '#miga > div > div > a:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Descripción :
    # Onsite Comment -split the description from detail_page

    try:
        notice_data.notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),"Descripción :")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Duración del contrato :
    # Onsite Comment -split the duration from detail page, ref url : "https://www.juntadeandalucia.es/haciendayadministracionpublica/apl/pdc_sirec/perfiles-licitaciones/detalle-licitacion.jsf?idExpediente=572536"

    try:
        notice_data.contract_duration = page_details.find_element(By.XPATH, '//*[contains(text(),"Duración del contrato")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Nº DE EXPEDIENTE Y TÍTULO
    # Onsite Comment -inspect url for detail page , url ref = 'https://www.juntadeandalucia.es/haciendayadministracionpublica/apl/pdc_sirec/perfiles-licitaciones/detalle-licitacion.jsf?idExpediente=572550'

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(1) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#j_idt21 > fieldset').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
# Onsite Field -None
# Onsite Comment -to take customer_details click on "//*[contains(text(),"Órgano de contratación :")]//following::a[1]" in page_details.  ref url  for page detail : "https://www.juntadeandalucia.es/haciendayadministracionpublica/apl/pdc_sirec/perfiles-licitaciones/detalle-licitacion.jsf?idExpediente=572257"

    try:              
        for single_record in page_details1.find_elements(By.CSS_SELECTOR, 'div.servicios_datos_basicos'):
            customer_details_data = customer_details()
        # Onsite Field -Denominación:
        # Onsite Comment -split the data from page_Detail 1

            try:
                customer_details_data.org_name = page_details1.find_element(By.XPATH, '//*[contains(text(),"Denominación:")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Dirección:
        # Onsite Comment -split the data from page_Detail 1

            try:
                customer_details_data.org_address = page_details1.find_element(By.XPATH, '//*[contains(text(),"Dirección:")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        
            customer_details_data.org_country = 'ES'
            customer_details_data.org_language = 'ES'
        # Onsite Field -Datos de contacto:
        # Onsite Comment -split only org_phone, for eg :  "Teléfono: 955 622 640 | Fax: 955 622 340", here take only "Teléfono"  value, url ref : "https://www.juntadeandalucia.es/haciendayadministracionpublica/apl/pdc_sirec/perfiles-licitaciones/detalle-perfil.jsf?perfilContratante=CHIE10"

            try:
                customer_details_data.org_phone = page_details1.find_element(By.XPATH, '//*[contains(text(),"Datos de contacto:")]//following::p[2]').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Datos de contacto:
        # Onsite Comment -split only org_fax, for eg :  "Teléfono: 955 622 640 | Fax: 955 622 340", here take only "Fax:"  value, url ref : "https://www.juntadeandalucia.es/haciendayadministracionpublica/apl/pdc_sirec/perfiles-licitaciones/detalle-perfil.jsf?perfilContratante=CHIE10"

            try:
                customer_details_data.org_fax = page_details1.find_element(By.XPATH, '//*[contains(text(),"Datos de contacto:")]//following::p[2]').text
            except Exception as e:
                logging.info("Exception in org_fax: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Email:
        # Onsite Comment -split the data from detail_page_3, url ref: "https://www.juntadeandalucia.es/haciendayadministracionpublica/apl/pdc_sirec/perfiles-licitaciones/detalle-perfil.jsf?perfilContratante=CHIE10"

            try:
                customer_details_data.org_email = page_details1.find_element(By.XPATH, '//*[contains(text(),"Email:")]//following::a[1]').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Datos de contacto:
        # Onsite Comment -split the data from detail_page 1 , ref url : "https://www.juntadeandalucia.es/haciendayadministracionpublica/apl/pdc_sirec/perfiles-licitaciones/detalle-perfil.jsf?perfilContratante=DTFATV04"

            try:
                customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Datos de contacto:")]//following::p').text
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass
        
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -Clasificación CPV :
# Onsite Comment -split the cpvs from detail_page, url ref : "https://www.juntadeandalucia.es/haciendayadministracionpublica/apl/pdc_sirec/perfiles-licitaciones/detalle-licitacion.jsf?idExpediente=571937"

    try:              
        for single_record in page_details.find_elements(By.XPATH, '//*[contains(text(),"Clasificación CPV")]//following::ul[1]'):
            cpvs_data = cpvs()
        # Onsite Field -Clasificación CPV :
        # Onsite Comment -split the cpvs from detail_page, url ref : "https://www.juntadeandalucia.es/haciendayadministracionpublica/apl/pdc_sirec/perfiles-licitaciones/detalle-licitacion.jsf?idExpediente=571937"

            try:
                cpvs_data.cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Clasificación CPV")]//following::ul[1]/li').text
            except Exception as e:
                logging.info("Exception in cpv_code: {}".format(type(e).__name__))
                pass
        
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -Requisitos, criterios y condiciones
# Onsite Comment -scroll down detail page, go to "Requisitos, criterios y condiciones"  tab and click on  "Ocultar información" for for view award details

    try:              
        for single_record in page_details.find_elements(By.XPATH, '//*[contains(text(),"Requisitos, criterios y condiciones")]'):
            tender_criteria_data = tender_criteria()
        # Onsite Field -Criterios de adjudicación
        # Onsite Comment -scroll down detail page, go to "Requisitos, criterios y condiciones"  tab and click on  "Ocultar información" for for view award details

            try:
                tender_criteria_data.tender_criteria_title = page_details.find_element(By.XPATH, '//*[contains(text(),"Criterios de adjudicación")]//following::p[1]').text
            except Exception as e:
                logging.info("Exception in tender_criteria_title: {}".format(type(e).__name__))
                pass
        
            tender_criteria_data.tender_criteria_cleanup()
            notice_data.tender_criteria.append(tender_criteria_data)
    except Exception as e:
        logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
        pass
    


# Onsite Field -Proyecto cofinanciado por la Unión Europea
# Onsite Comment -split the data between "Proyecto cofinanciado por la Unión Europea" and "Tasa de cofinanciación:" field, url ref : "https://www.juntadeandalucia.es/haciendayadministracionpublica/apl/pdc_sirec/perfiles-licitaciones/detalle-licitacion.jsf?idExpediente=572524"

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#cuerpo > div:nth-child(6)'):
            funding_agencies_data = funding_agencies()
        # Onsite Field -Financiado por :
        # Onsite Comment -None

            try:
                funding_agencies_data.funding_agency = page_details.find_element(By.XPATH, '//*[contains(text(),"Financiado por")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in funding_agency: {}".format(type(e).__name__))
                pass
        
            funding_agencies_data.funding_agencies_cleanup()
            notice_data.funding_agencies.append(funding_agencies_data)
    except Exception as e:
        logging.info("Exception in funding_agencies: {}".format(type(e).__name__)) 
        pass

    
        
# Onsite Field -Información de lotes licitados
# Onsite Comment -got to "Información de lotes licitados" tab click on " Mostrar información" to view lot details , url ref : "https://www.juntadeandalucia.es/haciendayadministracionpublica/apl/pdc_sirec/perfiles-licitaciones/detalle-licitacion.jsf?idExpediente=572173"

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#cuerpo > div:nth-child(10)'):
            lot_details_data = lot_details()
        # Onsite Field -Nº de lote :
        # Onsite Comment -url ref : "https://www.juntadeandalucia.es/haciendayadministracionpublica/apl/pdc_sirec/perfiles-licitaciones/detalle-licitacion.jsf?idExpediente=572173"

            try:
                lot_details_data.lot_actual_number = page_details.find_element(By.XPATH, '//*[contains(text(),"Nº de lote :")]//following::p[1]').text
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Título :
        # Onsite Comment -split the data from "Información de lotes licitados" field, url ref : "https://www.juntadeandalucia.es/haciendayadministracionpublica/apl/pdc_sirec/perfiles-licitaciones/detalle-licitacion.jsf?idExpediente=571737"

            try:
                lot_details_data.lot_title = page_details.find_element(By.XPATH, '//*[contains(text(),"Título :")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Título :
        # Onsite Comment -split the data from "Información de lotes licitados" field, url ref : "https://www.juntadeandalucia.es/haciendayadministracionpublica/apl/pdc_sirec/perfiles-licitaciones/detalle-licitacion.jsf?idExpediente=571737"

            try:
                lot_details_data.lot_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Título :")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Duracion :
        # Onsite Comment -split the data from "Información de lotes licitados" field, url ref : "https://www.juntadeandalucia.es/haciendayadministracionpublica/apl/pdc_sirec/perfiles-licitaciones/detalle-licitacion.jsf?idExpediente=571737"

            try:
                lot_details_data.contract_duration = page_details.find_element(By.XPATH, '//*[contains(text(),"Duracion :")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in contract_duration: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Importe lote (sin IVA)
        # Onsite Comment -split the data between "Valor estimado"  and "Importe lote (con IVA)" field, ref url : "https://www.juntadeandalucia.es/haciendayadministracionpublica/apl/pdc_sirec/perfiles-licitaciones/detalle-licitacion.jsf?idExpediente=572173"

            try:
                lot_details_data.lot_netbudget_lc = page_details.find_element(By.XPATH, '//*[contains(text(),"Importe lote (sin IVA)")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in lot_netbudget_lc: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Importe lote (con IVA)
        # Onsite Comment -ref url : "https://www.juntadeandalucia.es/haciendayadministracionpublica/apl/pdc_sirec/perfiles-licitaciones/detalle-licitacion.jsf?idExpediente=572173"

            try:
                lot_details_data.lot_grossbudget_lc = page_details.find_element(By.XPATH, '//*[contains(text(),"Importe lote (con IVA)")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
                pass


        # Onsite Field -TIPO DE CONTRATO
        # Onsite Comment -split the data from detail page, replace following keywords with given respective keywords ('Servicios' = 'services' , 'Suministros' = 'supply' , 'Concesión de servicios' = 'services' , 'Administrativo especial' = 'services' , 'obras' = 'works')

            try:
                lot_details_data.contract_type = page_details.find_element(By.XPATH, '//*[contains(text(),"Tipo de contrato ")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in contract_type: {}".format(type(e).__name__))
                pass

         # Onsite Field -Número de lotes :
        # Onsite Comment -ref url : "https://www.juntadeandalucia.es/haciendayadministracionpublica/apl/pdc_sirec/perfiles-licitaciones/detalle-licitacion.jsf?idExpediente=571749"

            try:
                lot_details_data.lot_quantity_uom = page_details.find_element(By.XPATH, '//*[contains(text(),"Número de lotes :")]//following::p[1]').text
            except Exception as e:
                logging.info("Exception in lot_quantity_uom: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Código CPV :
        # Onsite Comment -split the cpv code from "Información de lotes licitados" section , url ref : "https://www.juntadeandalucia.es/haciendayadministracionpublica/apl/pdc_sirec/perfiles-licitaciones/detalle-licitacion.jsf?idExpediente=571737"

            try:
                for single_record in page_details.find_elements(By.CSS_SELECTOR, '#cuerpo > div:nth-child(10)'):
                    lot_cpvs_data = lot_cpvs()
		
                    # Onsite Field -Código CPV :
                    # Onsite Comment -split the cpv code from "Información de lotes licitados" section , url ref : "https://www.juntadeandalucia.es/haciendayadministracionpublica/apl/pdc_sirec/perfiles-licitaciones/detalle-licitacion.jsf?idExpediente=571737" use both this selector ("//*[contains(text(),"Códigos CPV :")]//following::div[1]/p")

                    lot_cpvs_data.lot_cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Código CPV :")]//following::div[1]').text
			
                    lot_cpvs_data.lot_cpvs_cleanup()
                    lot_details_data.lot_cpvs.append(lot_cpvs_data)
            except Exception as e:
                logging.info("Exception in lot_cpvs: {}".format(type(e).__name__))
                pass
			
     
        
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -"Anuncios publicados" , "Documentación complementaria"
# Onsite Comment -for attachments  go to  "Anuncios publicados" section  and click on "Ocultar información" also go to   "Documentación complementaria" section and click on "Ocultar información"

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.pdc_datos'):
            attachments_data = attachments()
        # Onsite Field -"Anuncios publicados" , "Documentación complementaria"
        # Onsite Comment -split only file_type , for ex : "Descarga documento anuncio PDF 25/07/2023 13:32, 2023-0001281734 - Anuncio de Documentación ( Activo ). Descargar el XML del documento: 2023-0001281734" , here split only "PDF"

            try:
                attachments_data.file_type = page_details.find_element(By.CSS_SELECTOR, 'div.pdc_datos  > ul > li > p').text
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -"Anuncios publicados" , "Documentación complementaria"
        # Onsite Comment -for ex. "Descarga documento anuncio PDF 25/07/2023 13:32, 2023-0001281734 - Anuncio de Documentación ( Activo )" , here take only "2023-0001281734 - Anuncio de Documentación ( Activo )"

            try:
                attachments_data.file_name = page_details.find_element(By.CSS_SELECTOR, 'div.pdc_datos  > ul > li > p > a').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -"Anuncios publicados" , "Documentación complementaria"
        # Onsite Comment -None

            attachments_data.external_url = page_details.find_element(By.CSS_SELECTOR, 'div.pdc_datos  > ul > li > p > a').get_attribute('href')
            
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    

    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) + str(notice_data.publish_date) +  str(notice_data.notice_url) 
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
    urls = ["https://www.juntadeandalucia.es/haciendayadministracionpublica/apl/pdc_sirec/perfiles-licitaciones/licitaciones-publicadas.jsf"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,5):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="tablaLicitacionesPublicadas"]/tbody/tr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="tablaLicitacionesPublicadas"]/tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="tablaLicitacionesPublicadas"]/tbody/tr')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="tablaLicitacionesPublicadas"]/tbody/tr'),page_check))
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