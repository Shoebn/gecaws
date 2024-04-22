from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "gt_compras_ca"
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
from selenium.webdriver.chrome.options import Options
import gec_common.OutputJSON
from gec_common import functions as fn
import gec_common.Doc_Download
from selenium.webdriver.support.ui import Select

# Urban VPN(Spain)
# captcha on side
# Open the side then first go "Estatus" and select "Adjudicado" then go down soule captcha and click "Buscar" this button then grab the data


NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "gt_compras_ca"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'gt_compras_ca'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'GT'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'EUR'
    notice_data.main_language = 'ES'
    notice_data.procurement_method = 0
    notice_data.notice_type = 7
    
    # Onsite Field -Fecha de publicación
    # Onsite Comment -None

    try:
        notice_data.related_tender_id = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1) > div > span.ValorForm').text
    except Exception as e:
        logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Descripción
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > div > div').text
        notice_data.notice_title = GoogleTranslator(source='es', target='en').translate(notice_data.local_title)
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
    time.sleep(20)
    
    # Onsite Field -Proceso de Adjudicación >> Adjudicaciones >> Proceso de Adjudicación: Listado de Proveedores Adjudicados >> NIT o país
    # Onsite Comment -Note:Click on "Proceso de Adjudicación" and grab the data
    try:
        clk1=page_details.find_element(By.LINK_TEXT,'Proceso de Adjudicación').click()
        time.sleep(5)
    except:
        pass
    
    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"NIT o país")]//following::a[1]').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

# # # Onsite Field -None
# # # Onsite Comment -Note:Click on "Proceso de Adjudicación"   and grab the data
# # # ref_url=https://www.guatecompras.gt/concursos/consultaConcurso.aspx?nog=21502625&o=4

    try:
        lot_number=1
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#MasterGC_ContentBlockHolder_wcuConsultaConcursoAdjudicaciones_h0 > table > tbody'):
            lot_details_data = lot_details()
        # Onsite Field -Descripción
        # Onsite Comment -None
            lot_details_data.lot_number=lot_number

            lot_details_data.lot_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > div > div').text
            lot_details_data.lot_title_english  = GoogleTranslator(source='es', target='en').translate(lot_details_data.lot_title)


        # Onsite Field -None
        # Onsite Comment -Note:Click on "Proceso de Adjudicación" and grab the data
        # ref_url=https://www.guatecompras.gt/concursos/consultaConcurso.aspx?nog=21502625&o=4
        try:
            for single_record in page_details.find_elements(By.CSS_SELECTOR, '#MasterGC_ContentBlockHolder_wcuConsultaConcursoAdjudicaciones_h0 > table > tbody'):
                award_details_data = award_details()

                # Onsite Field -Adjudicaciones >> Proceso de Adjudicación: Listado de Proveedores Adjudicados >> Nombre o razón social
                # Onsite Comment -None

                award_details_data.bidder_name = page_details.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(3) > div').text
                # Onsite Field -Monto
                # Onsite Comment -None

                award_details_data.grossawardvaluelc = tender_html_element.find_element(By.CSS_SELECTOR, ' td.boldTotal').text
                award_details_data.grossawardvaluelc = float(award_details_data.grossawardvaluelc.replace(',',''))
                award_details_data.grossawardvalueeuro  = award_details_data.grossawardvaluelc

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
    
    
    # Onsite Field -Fecha de publicación
    # Onsite Comment -None

    try:
        publish_date = page_details.find_element(By.XPATH, "//*[contains(text(),'Fecha de publicación')]//following::div[1]").text
        publish_date = GoogleTranslator(source='es', target='en').translate(publish_date)
        publish_date = re.findall('\d+.\w+.\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d.%B.%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
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
# Onsite Comment -None
# Ref_url=https://www.guatecompras.gt/compradores/consultaDetEnt.aspx?iEnt=62&iUnt=0&iTipo=7

    try:         
        url2=page_details.find_element(By.CSS_SELECTOR, 'div.col-xs-12.col-md-9.EtiquetaInfo > a:nth-child(1)').get_attribute('href')
        fn.load_page(page_details1,url2)

        customer_details_data = customer_details()
    # Onsite Field -Detalle de entidad compradora >> Entidad
    # Onsite Comment -None

        customer_details_data.org_name = page_details1.find_element(By.XPATH, '//*[contains(text(),"Entidad:")]//following::div[1]').text

    # Onsite Field -Teléfonos
    # Onsite Comment -None

        try:
            customer_details_data.org_phone = page_details1.find_element(By.XPATH, '//*[contains(text(),"Teléfonos")]//following::div[1]').text
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass

    # Onsite Field -Números de Fax
    # Onsite Comment -None

        try:
            org_fax = page_details1.find_element(By.XPATH, '//*[contains(text(),"Números de Fax")]//following::div[1]').text
            if 'No Especificado' in org_fax:
                pass
            else:
                customer_details_data.org_fax = org_fax
        except Exception as e:
            logging.info("Exception in org_fax: {}".format(type(e).__name__))
            pass



    # Onsite Field -Apartado Postal
    # Onsite Comment -None

        try:
            postal_code = page_details1.find_element(By.XPATH, '//*[contains(text(),"Apartado Postal")]//following::div[1]').text
            if 'No Especificado' in postal_code:
                pass
            else:
                customer_details_data.postal_code = postal_code
        except Exception as e:
            logging.info("Exception in postal_code: {}".format(type(e).__name__))
            pass


    # Onsite Field -Páginas Web
    # Onsite Comment -None

        try:
            customer_details_data.org_website = page_details1.find_element(By.XPATH, '//*[contains(text(),"Páginas Web")]//following::a[1]').text
        except Exception as e:
            logging.info("Exception in org_website: {}".format(type(e).__name__))
            pass

    # Onsite Field -Direcciones de Correo
    # Onsite Comment -None

        try:
            org_email = page_details1.find_element(By.XPATH, '//*[contains(text(),"Direcciones de Correo")]//following::div[1]').text
            if ',' in org_email:
                customer_details_data.org_email = org_email.split(',')[0].strip()
            else:
                customer_details_data.org_email = org_email
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass

    # Onsite Field -Tipo
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
    
# # Onsite Field -None
# # Onsite Comment -Note:First click on "Documentos del Proceso de contratación" and clicl the Dropdown button then grab the data
# # Ref_url=https://www.guatecompras.gt/concursos/consultaConcurso.aspx?nog=21503044&o=4
    clk2=page_details.find_element(By.XPATH,'//*[@id="MasterGC_ContentBlockHolder_RadTabStrip1"]/div/ul/li[2]/a').click()
    time.sleep(10)

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'tr.FilaTablaDetalle td:nth-child(2) > a'):

            attachments_data = attachments()
    #         # Onsite Field -Documento(s) adjunto(s) exitosamente
    #         # Onsite Comment -Note:split file_name.eg.,"21496439@Oficio Circular 9450 Departamento de Abastecimientos.pdf" don't take ".pdf" in file_name.

            attachments_data.file_name = single_record.get_attribute('innerHTML')

    #         # Onsite Field -Documento(s) adjunto(s) exitosamente
    #         # Onsite Comment -None

            attachments_data.external_url = single_record.get_attribute('href')

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    

    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
    
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
options = Options()
for argument in arguments:
    options.add_argument(argument)
page_main = webdriver.Chrome(options=options)
page_details = webdriver.Chrome(options=options)
page_details1 = webdriver.Chrome(options=options)

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.guatecompras.gt/concursos/consultaConAvanz.aspx"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        select_fr = Select(page_main.find_element(By.XPATH,'//*[@id="MasterGC_ContentBlockHolder_ddlEstatus"]'))
        select_fr.select_by_index(2)
        time.sleep(25)
        
        clk=page_main.find_element(By.CSS_SELECTOR,'#MasterGC_ContentBlockHolder_btnBuscar').click()
        time.sleep(10)
        try:
            for page_no in range(2,10):
                page_check = WebDriverWait(page_main, 10).until(EC.presence_of_element_located((By.XPATH,'//*[@id="MasterGC_ContentBlockHolder_dgResultado"]/tbody/tr'))).text
                rows = WebDriverWait(page_main, 10).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="MasterGC_ContentBlockHolder_dgResultado"]/tbody/tr')))
                length = len(rows)
                for records in range(1,length):
                    tender_html_element = WebDriverWait(page_main, 10).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="MasterGC_ContentBlockHolder_dgResultado"]/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 10).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 10).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="MasterGC_ContentBlockHolder_dgResultado"]/tbody/tr'),page_check))
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
    page_details1.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)
