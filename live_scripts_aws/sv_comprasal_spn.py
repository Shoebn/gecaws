#select "Licitaciones y Concursos", "Contratación Directa", "Libre Gestión", "Compras por Lineamiento", "Otros" >>>> select date - "Desde" take date of one month >>>> >>>> next click on " Búsqueda simple" >>>>>>> select "Declarado Desierto", "Sin Efecto", Gestión de la Compra" >>>> Buscar

from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "sv_comprasal_spn"
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
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "sv_comprasal_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.script_name = 'sv_comprasal_spn'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'ES'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'SVC'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'SV'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_type = 4
    
    # Onsite Field -Código / tipo
    # Onsite Comment -just take the first part i.e. - just take data which is before "/" ....... 
    # Also if notice no is not present in the tender take it from notice url

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Nombre Proceso
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Fecha publicación
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
#     # Onsite Field -Período para presentar ofertas
#     # Onsite Comment -select date which is after "dash", "-"

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(6)").text.split('-')[1]
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
#     # Onsite Field -OBRA/BIEN/SERVICIO
#     # Onsite Comment -None

    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Bien")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
#     # Onsite Field -OBRA/BIEN/SERVICIO
#     # Onsite Comment -None

    try:
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
#     # Onsite Field -FUENTE DE FINANCIAMIENTO
#     # Onsite Comment -ref url - "https://unac.gob.sv/comprasalweb/procesos/14811517"

    try:
        funding_agency1 = page_details.find_element(By.XPATH, "//*[contains(text(),'Fuente de Financiamiento')]//following::p[1]").text.split('(')[1].split(')')[0]
        funding_agency_1 = GoogleTranslator(source='es', target='en').translate(funding_agency1)
        funding_agencies_data = funding_agencies()
        funding_agencies_data.funding_agency = fn.procedure_mapping("assets/sv_comprasal_spn_fundingagencycode.csv",funding_agency_1)
        funding_agencies_data.funding_agencies_cleanup()
        notice_data.funding_agencies.append(funding_agencies_data)
    
    except Exception as e:
        logging.info("Exception in funding_agencies: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#ngb-nav-0-panel').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
# # Onsite Field -None
# # Onsite Comment -None

    try:              
        customer_details_data = customer_details()
    # Onsite Field -Institución
    # Onsite Comment -None


        customer_details_data.org_name = page_details.find_element(By.XPATH, "//*[contains(text(),'Institución')]//following::p[1]").text


    # Onsite Field -NOMBRE DEL CONTACTO
    # Onsite Comment -None

        try:
            customer_details_data.contact_person = page_details.find_element(By.XPATH, "//*[contains(text(),'Nombre del contacto')]//following::p[1]").text
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass

        customer_details_data.org_language = 'ES'
        customer_details_data.org_country = 'SV'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# # Onsite Field -Documentos
# # Onsite Comment -Click on "Documentos" to get attachments

    try:    
        clk=page_details.find_element(By.CSS_SELECTOR, 'a#ngb-nav-1.rounded-0.nav-link').click()
        time.sleep(10)
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#ngb-nav-1-panel > app-purchase-documents > div ul li '):
            attachments_data = attachments()
    #         # Onsite Field -Documentos
    #         # Onsite Comment -Click on "Documentos" to get attachments
            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'a').text

    #             # Onsite Field -Documentos
    #             # Onsite Comment -Click on "Documentos" to get attachments

            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')

    #         # Onsite Field -Documentos
    #         # Onsite Comment -Click on "Documentos" to get attachments

            try:
                attachments_data.file_type = page_details.find_element(By.CSS_SELECTOR, 'a').text.split('.')[1]
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass

    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_url) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title)
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
 
options = webdriver.ChromeOptions()
options.add_extension("C:/Users/Administrator/home/Urban-Free-VPN-proxy-Unblocker---Best-VPN.crx")
page_main = webdriver.Chrome(options=options)
time.sleep(20)
 
options = webdriver.ChromeOptions()
options.add_extension("C:/Users/Administrator/home/Urban-Free-VPN-proxy-Unblocker---Best-VPN.crx")
page_details = webdriver.Chrome(options=options)
time.sleep(20)

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://unac.gob.sv/comprasalweb/procesos"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        
        tendr = WebDriverWait(page_main, 10).until(EC.presence_of_element_located((By.XPATH,'/html/body/app-root/div[1]/app-purchase-searchbox/div[2]/div/div[1]/div/div[2]/app-checkbox-buttons/div/label[1]'))).click()
        tendr = WebDriverWait(page_main, 10).until(EC.presence_of_element_located((By.XPATH,'/html/body/app-root/div[1]/app-purchase-searchbox/div[2]/div/div[1]/div/div[2]/app-checkbox-buttons/div/label[2]'))).click()
        tendr = WebDriverWait(page_main, 10).until(EC.presence_of_element_located((By.XPATH,'/html/body/app-root/div[1]/app-purchase-searchbox/div[2]/div/div[1]/div/div[2]/app-checkbox-buttons/div/label[3]'))).click()
        tendr = WebDriverWait(page_main, 10).until(EC.presence_of_element_located((By.XPATH,'/html/body/app-root/div[1]/app-purchase-searchbox/div[2]/div/div[1]/div/div[2]/app-checkbox-buttons/div/label[4]'))).click()
        tendr = WebDriverWait(page_main, 10).until(EC.presence_of_element_located((By.XPATH,'/html/body/app-root/div[1]/app-purchase-searchbox/div[2]/div/div[1]/div/div[2]/app-checkbox-buttons/div/label[5]'))).click()
        
        advance_src = WebDriverWait(page_main, 10).until(EC.presence_of_element_located((By.XPATH,'/html/body/app-root/div[1]/app-purchase-searchbox/div[1]/div/button'))).click()
        advance_src = WebDriverWait(page_main, 10).until(EC.presence_of_element_located((By.XPATH,'/html/body/app-root/div[1]/app-purchase-searchbox/div[3]/div/div/div[2]/div/div[2]/app-checkbox-buttons/div/label[1]'))).click()
        advance_src = WebDriverWait(page_main, 10).until(EC.presence_of_element_located((By.XPATH,'/html/body/app-root/div[1]/app-purchase-searchbox/div[3]/div/div/div[2]/div/div[2]/app-checkbox-buttons/div/label[2]'))).click()
        
        
        
        srch = WebDriverWait(page_main, 10).until(EC.presence_of_element_located((By.XPATH,'/html/body/app-root/div[1]/app-purchase-searchbox/div[4]/div/button'))).click()
        
        time.sleep(20)

        try:
            for page_no in range(2,20):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/app-root/div[1]/app-purchase-searchbox/div[5]/div/app-purchase-list2/div[2]/div[1]/table/tbody/tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/app-root/div[1]/app-purchase-searchbox/div[5]/div/app-purchase-list2/div[2]/div[1]/table/tbody/tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/app-root/div[1]/app-purchase-searchbox/div[5]/div/app-purchase-list2/div[2]/div[1]/table/tbody/tr')))[records]
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
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/app-root/div[1]/app-purchase-searchbox/div[5]/div/app-purchase-list2/div[2]/div[1]/table/tbody/tr'),page_check))
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
    
 
