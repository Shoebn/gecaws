from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "es_aena_spn"
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
SCRIPT_NAME = "es_aena_spn"
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
    notice_data.script_name = 'es_aena_spn'
    
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
    notice_data.notice_type = 4
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -Fecha Publicación
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, " td.\(.web.\)").text
        publish_date = re.findall('\d+.\d+.\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Nº Expediente
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, ' td.txtLft.fondoGris').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Fecha límite presentación
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, " td:nth-child(8)").text
        notice_deadline = re.findall('\d+.\d+.\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Importe bruto licitado(€)
    # Onsite Comment -None

    try:
        grossbudgetlc = tender_html_element.find_element(By.CSS_SELECTOR, ' td:nth-child(5)').text
        grossbudgetlc = grossbudgetlc.replace('.','').replace(',','.')
        notice_data.grossbudgetlc = float(grossbudgetlc)
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Importe neto licitado(€)
    # Onsite Comment -None

    try:
        netbudgetlc = tender_html_element.find_element(By.CSS_SELECTOR, 'tr> td:nth-child(6)').text
        netbudgetlc = netbudgetlc.replace('.','').replace(',','.')
        notice_data.netbudgetlc = float(netbudgetlc)
    except Exception as e:
        logging.info("Exception in netbudgetlc: {}".format(type(e).__name__))
        pass


       # Onsite Field -Value (In Nu.)
    # Onsite Comment -None

    try:
        est_amount = tender_html_element.find_element(By.CSS_SELECTOR, 'tr> td:nth-child(7)').text
        est_amount = est_amount.replace('.','').replace(',','.')
        notice_data.est_amount = float(est_amount)
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.document_type_description = 'Tenders'
    

    
    # Onsite Field -Título
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3) a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div#cuerpo > div').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
        
    try:
        notice_data.local_title = page_details.find_element(By.XPATH,' (//*[contains(text(),"Título:")])[1]//following::td[1]').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except:
        pass
    
# # Onsite Field -Destino
# # Onsite Comment -None

    try:              
        customer_details_data = customer_details()
    # Onsite Field -Destino
    # Onsite Comment -None

        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
    # Onsite Field -Teléfono:
    # Onsite Comment -split the data after "Teléfono:"

        try:
            customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[@id="ncuadr"]/div[2]/table/tbody/tr[3]/td/ul/li[1]').text.split('Teléfono:')[1]
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass

    # Onsite Field -Fax
    # Onsite Comment -split the data after "Fax"

        try:
            customer_details_data.org_fax = page_details.find_element(By.XPATH, '//*[@id="ncuadr"]/div[2]/table/tbody/tr[3]/td/ul/li[2]').text.split('Fax:')[1]
        except Exception as e:
            logging.info("Exception in org_fax: {}".format(type(e).__name__))
            pass

    # Onsite Field -Email:
    # Onsite Comment -None

        try:
            customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[@id="ncuadr"]/div[2]/table/tbody/tr[3]/td/ul/li[3]/a').text
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass

        customer_details_data.org_country = 'ES'
        customer_details_data.org_language = 'ES'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
#     # Onsite Field -Naturaleza:
#     # Onsite Comment -Replace following keywords with given respective keywords ('OBRASOBRASOBRAS = Works' , 'Non Consultant Services = Non consultancy' , 'ASISTENCIAS   = Consultancy' , 'SERVICIOS = Service' , 'OBRAS  = 'Service' )

    try:
        notice_data.contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Naturaleza:")]//following::td[1]').text
        if 'OBRASOBRASOBRAS' in notice_data.contract_type_actual:
             notice_data.notice_contract_type = 'Works'
        elif 'Non Consultant Services' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Non consultancy'
        elif 'ASISTENCIAS' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Consultancy'
        elif 'SERVICIOS' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Service'
        elif 'OBRAS' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Service'
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    

    
#     # Onsite Field -Lugar: 
#     # Onsite Comment -None

    try:
        notice_data.additional_tender_url = page_details.find_element(By.XPATH, '//*[contains(text(),"Lugar:")]//following::td[1]/a').text
    except Exception as e:
        logging.info("Exception in additional_tender_url: {}".format(type(e).__name__))
        pass
    
# Onsite Field -Ver lotes
# Onsite Comment -for lot_details click on "Ver lotes" (#mostrarLotes)  , ref_url : "https://contratacion.aena.es/contratacion/principal?portal=infoexp&idexp=9610160362&tipoexp=400#"
    
    try:    
        clk = page_details.find_element(By.XPATH,'//a[@id="ocLotes"]').click()
        lot_number = 1
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div#tablaLotes'):
            lot_details_data = lot_details()
            lot_details_data.lot_number = lot_number
        # Onsite Field -Título:
        # Onsite Comment -ref_url : "https://contratacion.aena.es/contratacion/principal?portal=infoexp&idexp=9610160362&tipoexp=400#"

            lot_details_data.lot_title = single_record.find_element(By.XPATH, '//*[contains(text(),"Lote:")]//following::td[1]').text
           
        
        # Onsite Field -Importe bruto licitación:
        # Onsite Comment -ref_url : "https://contratacion.aena.es/contratacion/principal?portal=infoexp&idexp=9610160362&tipoexp=400#"

            try:
                lot_details_data.lot_grossbudget_lc = single_record.find_element(By.XPATH, '//*[contains(text(),"Lote:")]//following::td[2]').text
                lot_details_data.lot_grossbudget_lc = lot_details_data.lot_grossbudget_lc.replace('.','').replace(',','.').split(' €')[0]
                lot_details_data.lot_grossbudget_lc = float(lot_details_data.lot_grossbudget_lc)
            except Exception as e:
                logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Importe neto licitación:
        # Onsite Comment -ref_url : "https://contratacion.aena.es/contratacion/principal?portal=infoexp&idexp=9610160362&tipoexp=400#"

            try:
                lot_details_data.lot_netbudget_lc = single_record.find_element(By.XPATH, '//*[contains(text(),"Lote:")]//following::td[3]').text
                lot_details_data.lot_netbudget_lc = lot_details_data.lot_netbudget_lc.replace('.','').replace(',','.').split(' €')[0]
                lot_details_data.lot_netbudget_lc = float(lot_details_data.lot_netbudget_lc)
            except Exception as e:
                logging.info("Exception in lot_netbudget_lc: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Importe neto licitación:
        # Onsite Comment -ref_url : "https://contratacion.aena.es/contratacion/principal?portal=infoexp&idexp=9610160362&tipoexp=400#"

            try:
                lot_details_data.lot_netbudget = single_record.find_element(By.XPATH, '//*[contains(text(),"Lote:")]//following::td[3]').text
                lot_details_data.lot_netbudget = lot_details_data.lot_netbudget.replace('.','').replace(',','.').split(' €')[0]
                lot_details_data.lot_netbudget = float(lot_details_data.lot_netbudget)
            except Exception as e:
                logging.info("Exception in lot_netbudget: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Importe bruto licitación:
        # Onsite Comment -ref_url : "https://contratacion.aena.es/contratacion/principal?portal=infoexp&idexp=9610160362&tipoexp=400#"

            try:
                lot_details_data.lot_grossbudget = single_record.find_element(By.XPATH, '//*[contains(text(),"Lote:")]//following::td[2]').text
                lot_details_data.lot_grossbudget = lot_details_data.lot_grossbudget.replace('.','').replace(',','.').split(' €')[0]
                lot_details_data.lot_grossbudget = float(lot_details_data.lot_grossbudget)            
            
            except Exception as e:
                logging.info("Exception in lot_grossbudget: {}".format(type(e).__name__))
                pass
        
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
            lot_number += 1
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
# # Onsite Field -Descarga de pliegos:
# # Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.XPATH, '//*[contains(text(),"Presentación de ofertas")]//following::td[4]/ul/li/a'):
            attachments_data = attachments()
        # Onsite Field -Descarga de pliegos:
        # Onsite Comment -split only file_name for ex."Pliego de Cláusulas Particulares (PDF)" , here take only "Pliego de Cláusulas Particulares"

            attachments_data.file_name = single_record.text.split('(')[0]
            
        # Onsite Field -Descarga de pliegos:
        # Onsite Comment -None

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
    urls = ["https://contratacion.aena.es/contratacion/principal?portal=licitaciones"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(2,10):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="Taperturas"]/tbody/tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="Taperturas"]/tbody/tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="Taperturas"]/tbody/tr')))[records]
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
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="Taperturas"]/tbody/tr'),page_check))
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
