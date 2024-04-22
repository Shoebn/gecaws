#after opening the url "Estado" in this field select "To be awarded=Por Adjudicar","Awarded=Adjudicado" take the data.

#check comments for additional changes
#1)for bidder name
# As discussed with shoeib added below condition .. (1) if lot avaialble than condition 
# lot_title ="blank "and award_details ="blank" []
# than lot_details =[]
# (2) if lots not avaible than
# award_details= []
# and lot_details= []


from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "pa_panamacompra_ca"
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

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "pa_panamacompra_ca"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.script_name = 'pa_panamacompra_ca'
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'PA'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'ES'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'PAB'
    
    # Onsite Field -Modalidad de adjudicación
    # Onsite Comment -1.if "Global" is written then pass "1", otherwise pass "2".
    try:
        notice_data.procurement_method = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(8)').text
    except Exception as e:
        logging.info("Exception in procurement_method: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_type = 7
    
    # Onsite Field -Número
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    

    
    # Onsite Field -Estado
    # Onsite Comment -None

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass

    # Onsite Field -Descripción
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    

    # Onsite Field -Número
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.ID, '#elementToPDF').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')



# #     # Onsite Field -Objeto de la contratación:
# #     # Onsite Comment -1.repalce given keywords("Bien=Supply","Servicio=Service","Obra=Works")

    try:
        notice_data.contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Objeto de la contratación:")]//following::td[1]').text
        if 'Bien' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Supply'
        elif 'Servicio' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Service'
        elif 'Obra' in notice_data.contract_type_actual:
             notice_data.notice_contract_type = 'Works'
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    
#     # Onsite Field -Aviso de convocatoria >> Descripción:
#     # Onsite Comment -None

    try:
        notice_data.local_description =  page_details.find_element(By.XPATH, '//*[contains(text(),"Descripción:")]//following::td[1]').text
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    
    # Onsite Field -Aviso de convocatoria >> Fecha y hora de apertura de propuestas:
    # Onsite Comment -None

    try:
        notice_data.document_opening_time = page_details.find_element(By.XPATH, '//*[contains(text(),"Fecha y hora de apertura de propuestas:")]//following::td[1]').text
        notice_data.document_opening_time  = re.findall('\d+-\d+-\d{4}',notice_data.document_opening_time )[0]
        notice_data.document_opening_time  = datetime.strptime(notice_data.document_opening_time ,'%d-%m-%Y').strftime('%Y-%m-%d')
    except Exception as e:
        logging.info("Exception in document_opening_time: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Aviso de convocatoria >> Precio referencia:
#     # Onsite Comment -None

    try:
        est_amount = page_details.find_element(By.XPATH, '//*[contains(text(),"Precio referencia:")]//following::td[1]').text
        est_amount = re.findall('[\d+\.\,]+',est_amount)[1]
        est_amount  = est_amount.replace(',','')
        notice_data.est_amount  = float(est_amount)
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
#     # Onsite Field -Aviso de convocatoria >> Precio referencia:
#     # Onsite Comment -None

    try:
        notice_data.grossbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass

#     # Onsite Field -Fecha de publicación:
#     # Onsite Comment -None

    try:
        publish_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Fecha de publicación:")]//following::td[1]').text
        publish_date = re.findall('\d+-\d+-\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d-%m-%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return


# # Onsite Field -None
# # Onsite Comment -None

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'PA'
        customer_details_data.org_language = 'ES'
    # Onsite Field -Entity/Purchasing Unit
    # Onsite Comment -None


        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text

    # Onsite Field -Dependencia
    # Onsite Comment -None

        try:
            customer_details_data.org_description = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(6)').text
        except Exception as e:
            logging.info("Exception in org_description: {}".format(type(e).__name__))
            pass

        # Onsite Field -Contacto de la unidad de compra >> Nombre:
        # Onsite Comment -None

        try:
            customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Nombre:")]//following::td[1]').text
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass

        # Onsite Field -Contacto de la unidad de compra >> Teléfono:
        # Onsite Comment -None

        try:
            customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Teléfono:")]//following::td[1]').text
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass

        # Onsite Field -Contacto de la unidad de compra >> Correo electrónico:
        # Onsite Comment -None

        try:
            customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Correo electrónico:")]//following::td[1]').text
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass


# # Onsite Field -None
# # # Onsite Comment -ref_url:"https://www.panamacompra.gob.pa/Inicio/v2/#!/vistaPreviaCP?NumLc=2023-0-03-0-08-CM-059361&esap=0&nnc=1&it=1"

    try:              
        for single_record in page_details.find_elements(By.XPATH, '//*[contains(text(),"Condiciones generales")]//following::div[1]//tr//td[1]//a'):
            attachments_data = attachments()
            # Onsite Field -Condiciones generales
            # Onsite Comment -None

            attachments_data.file_name = single_record.text
        # Onsite Field -Condiciones generales
        # Onsite Comment -None

            attachments_data.external_url = single_record.get_attribute('href')
            
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass

# # Onsite Field -None
# # Onsite Comment -ref_url:"https://www.panamacompra.gob.pa/Inicio/v2/#!/vistaPreviaCP?NumLc=2023-0-03-0-08-CM-059361&esap=0&nnc=1&it=1"

    try:              
        for single_record in page_details.find_elements(By.XPATH, '//*[contains(text(),"Documentos adjuntos")]//following::div[1]//tr')[1:]:
            attachments_data = attachments()
        # Onsite Field -Documentos adjuntos >> Tipo
        # Onsite Comment -None

            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text

        
        # Onsite Field -Documentos adjuntos >> Descripción
        # Onsite Comment -None

            try:
                attachments_data.file_description =  single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
            except Exception as e:
                logging.info("Exception in file_description: {}".format(type(e).__name__))
                pass
        # Onsite Field -Documentos adjuntos >> Acciones
        # Onsite Comment -None

            attachments_data.external_url = page_details.find_element(By.CSS_SELECTOR, 'td:nth-child(4) a').get_attribute('href')
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass

    try:   
        for single_record in page_details.find_elements(By.XPATH, '//*[contains(text(),"Bien/Servicio/Obra seleccionados")]//following::div[1]/table/tbody/tr'):
            cpv_code = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
            cpv_codes = re.findall('\d{8}',cpv_code)[0]
            cpv_codes_list = fn.CPV_mapping("assets/pa_panamacompra_ca_cpv.csv",cpv_codes)
            for each_cpv in cpv_codes_list:
                cpvs_data = cpvs()
                cpvs_data.cpv_code = each_cpv
                notice_data.cpv_at_source = each_cpv
                cpvs_data.cpvs_cleanup()
                notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__))
        pass
    


# # Onsite Field -None
# # Onsite Comment -ref_url:"https://www.panamacompra.gob.pa/Inicio/v2/#!/vistaPreviaCP?NumLc=2023-0-03-0-08-CM-059361&esap=0&nnc=1&it=1"

    try:    
        lot_number=1
        for single_record in page_details.find_elements(By.XPATH, '//*[contains(text(),"Bien/Servicio/Obra seleccionados")]//following::div[1]/table/tbody/tr'):
            lot_details_data = lot_details()
            lot_details_data.lot_number=lot_number
    #     # Onsite Field -Especificaciones técnicas >> Descripción
#     # Onsite Comment -None

            lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(6)').text

    # Onsite Field -Especificaciones técnicas >> Unidad de medida
#     # Onsite Comment -None

            try:
                lot_details_data.lot_quantity = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
                lot_details_data.lot_quantity = float(lot_details_data.lot_quantity)
            except Exception as e:
                logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                pass

    #     # Onsite Field -Especificaciones técnicas >> Cantidad
    #     # Onsite Comment -None

            try:
                lot_details_data.lot_quantity_uom = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
            except Exception as e:
                logging.info("Exception in lot_quantity_uom: {}".format(type(e).__name__))
                pass

            try:
                lot_details_data.lot_contract_type_actual = page_details.find_element(By.CSS_SELECTOR, '#body-right > div.first').text.split(':')[1]
                if 'Bien' in lot_details_data.lot_contract_type_actual:
                    lot_details_data.contract_type = 'Supply'
                elif 'Servicio' in lot_details_data.lot_contract_type_actual:
                    lot_details_data.contract_type = 'Service'
                elif 'Obra' in lot_details_data.lot_contract_type_actual:
                    lot_details_data.contract_type = 'Works'
            except Exception as e:
                logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
                pass


#     # Onsite Field -None
#     # Onsite Comment -ref_url:"https://www.panamacompra.gob.pa/Inicio/v2/#!/vistaPreviaCP?NumLc=2023-0-03-0-08-CM-059361&esap=0&nnc=1&it=1"

            try:
                # Onsite Field -Especificaciones técnicas >> Código
                # Onsite Comment -csv file is pulled of mapping name as "pa_panamacompra_ca_cpv.csv".

                lot_cpv_code = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
                lot_cpv_code = re.findall('\d{8}',lot_cpv_code)[0]
                lot_cpv_code = fn.CPV_mapping("assets/pa_panamacompra_ca_cpv.csv",lot_cpv_code)
                for each_cpv in lot_cpv_code:
                    lot_cpvs_data = lot_cpvs()
                    lot_cpvs_data.lot_cpv_code = each_cpv
                    lot_details_data.lot_cpv_at_source = each_cpv
                    lot_cpvs_data.lot_cpvs_cleanup()
                    lot_details_data.lot_cpvs.append(lot_cpvs_data)
            except Exception as e:
                logging.info("Exception in lot_cpvs: {}".format(type(e).__name__))
                pass

#         # Onsite Field -None
#         # Onsite Comment -None

            try:
                award_details_data = award_details()

                # Onsite Field -Adjudicacion
                # Onsite Comment -None

                award_date = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(7)').text
                award_date = re.findall('\d+-\d+-\d{4}',award_date)[0]
                award_details_data.award_date = datetime.strptime(award_date ,'%d-%m-%Y').strftime('%Y/%m/%d')

                award_details_data.award_details_cleanup()
                lot_details_data.award_details.append(award_details_data)
            except Exception as e:
                logging.info("Exception in award_details: {}".format(type(e).__name__))
                pass
			
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
            lot_number +=1
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass

    notice_data.class_at_source = 'CPV'

    try:
        notice_data.category = page_details.find_element(By.CSS_SELECTOR, 'div.panel-body.table-responsive > div > table > tbody > tr > td:nth-child(3)').text
    except Exception as e:
        logging.info("Exception in category: {}".format(type(e).__name__))
        pass
    
#     # Onsite Field -Condiciones de la contratación >> Vigencia del contrato:
#     # Onsite Comment -ref_url:"https://www.panamacompra.gob.pa/Inicio/v2/#!/vistaPreviaCP?NumLc=2023-0-03-0-08-CM-059361&esap=0&nnc=1&it=1"

    try:
        notice_data.contract_duration = page_details.find_element(By.XPATH, '//*[contains(text(),"Vigencia del contrato:")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass

    
# # Onsite Field -None
# # Onsite Comment -ref_url:"https://www.panamacompra.gob.pa/Inicio/v2/#!/vistaPreviaCP?NumLc=2023-0-03-0-08-CM-059361&esap=0&nnc=1&it=1"



    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
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
    urls = ["https://www.panamacompra.gob.pa/Inicio/#/busqueda-avanzada-v2?q=eyJkZXNjcmlwY2lvbiI6IiIsImVzdGFkbyI6IjUiLCJwcm92aW5jaWEiOjAsInRjb21wcmEiOi0xLCJmZCI6IjIwMjMtMTAtMjdUMTg6MzA6MDAuMDAwWiIsImZoIjoiMjAyMy0xMS0yOFQxMzoyOTo1OS45OTlaIiwidWNvbXByYSI6e319"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        time.sleep(10)

	try:
	    for page_no in range(2,10):
	        page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'div.table-responsive > table > tbody > tr'))).text
	        rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.table-responsive > table > tbody > tr')))
	        length = len(rows)
	        for records in range(0,length):
	            tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.table-responsive > table > tbody > tr')))[records]
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
	            WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'div.table-responsive > table > tbody > tr'),page_check))
	        except Exception as e:
	            logging.info("Exception in next_page: {}".format(type(e).__name__))
	            logging.info("No next page")
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
    page_details.quit() 
    
    output_json_file.copyFinalJSONToServer(output_json_folder)
