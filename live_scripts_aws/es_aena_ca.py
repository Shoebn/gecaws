
from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "es_aena_ca"
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
from selenium.webdriver.chrome.options import Options
from selenium import webdriver

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "es_aena_ca"
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
    notice_data.script_name = 'es_aena_ca'
    
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
    notice_data.notice_type = 7
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -Fecha Adjudicación
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(1)").text
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
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, ' td:nth-child(2) ').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Título
    # Onsite Comment -for detail_page click on "tr> td:nth-child(3) a"

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, ' td:nth-child(3) a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
        
    # Onsite Field -Importe bruto licitación:
    # Onsite Comment -None

    try:
        notice_data.grossbudgetlc = page_details.find_element(By.XPATH, '//*[contains(text(),"Importe bruto licitación:")]//following::td[1]').text
        notice_data.grossbudgetlc = notice_data.grossbudgetlc.replace('.','').replace(',','.').split(' €')[0]
        notice_data.grossbudgetlc = float(notice_data.grossbudgetlc)
        notice_data.grossbudgeteuro = notice_data.grossbudgetlc
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Importe neto licitación:
    # Onsite Comment -None

    try:
        notice_data.netbudgetlc = page_details.find_element(By.XPATH, '//*[contains(text(),"Importe neto licitación:")]//following::td[1]').text
        notice_data.netbudgetlc = notice_data.netbudgetlc.replace('.','').replace(',','.').split(' €')[0]
        notice_data.netbudgetlc = float(notice_data.netbudgetlc)
        notice_data.netbudgeteuro = notice_data.netbudgetlc
    except Exception as e:
        logging.info("Exception in netbudgetlc: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div#cuerpo > div').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
#     # Onsite Field -Título:
#     # Onsite Comment -None

    try:
        notice_data.local_title = page_details.find_element(By.XPATH, '//*[contains(text(),"Título:")]//following::td[1]').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
#     # Onsite Field -Valor estimado contrato neto:
#     # Onsite Comment -None

    try:
        notice_data.est_amount = page_details.find_element(By.XPATH, '//*[contains(text(),"Valor estimado contrato neto:")]//following::td[1]').text
        notice_data.est_amount = notice_data.est_amount.replace('.','').replace(',','.').split(' €')[0]
        notice_data.est_amount = float(notice_data.est_amount)

    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
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
        elif 'SUMINISTROS' in  notice_data.contract_type_actual:
             notice_data.notice_contract_type = 'Supply'
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass

# Onsite Field -Destino
# Onsite Comment -None

    try:              
        customer_details_data = customer_details()
    # Onsite Field -Destino
    # Onsite Comment -None

        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
        
        customer_details_data.org_country = 'ES'
        customer_details_data.org_language = 'ES'
    # Onsite Field -Teléfono:
    # Onsite Comment -None

        try:
            customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[@id="ncuadr"]/div[2]/table/tbody/tr[3]/td/ul/li[1]').text.split('Teléfono: ')[1]
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass

    # Onsite Field -Fax:
    # Onsite Comment -None

        try:
            customer_details_data.org_fax = page_details.find_element(By.XPATH, '//*[@id="ncuadr"]/div[2]/table/tbody/tr[3]/td/ul/li[2]').text.split('Fax: ')[1]
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
        
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    # Onsite Field -Lugar:
    # Onsite Comment -None

    try:
        notice_data.additional_tender_url = page_details.find_element(By.XPATH, '//*[contains(text(),"Lugar:")]//following::td[1]/a').get_attribute('href')
    except Exception as e:
        logging.info("Exception in additional_tender_url: {}".format(type(e).__name__))
        pass

    
# # Onsite Field -None
# # Onsite Comment -None

    try:              
        lot_details_data = lot_details()
    # Onsite Field -Título:
    # Onsite Comment -paas local_title as a lot_title for lot_Details

        lot_details_data.lot_number=1
        lot_details_data.lot_title = page_details.find_element(By.XPATH, '//*[contains(text(),"Título:")]//following::td[1]').text

        try:
            lot_details_data.lot_contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Naturaleza:")]//following::td[1]').text
            if 'OBRASOBRASOBRAS' in lot_details_data.lot_contract_type_actual:
                lot_details_data.contract_type = 'Works'
            elif 'Non Consultant Services' in lot_details_data.lot_contract_type_actual:
                lot_details_data.contract_type = 'Non consultancy'
            elif 'ASISTENCIAS' in lot_details_data.lot_contract_type_actual:
                lot_details_data.contract_type = 'Consultancy'
            elif 'SERVICIOS' in lot_details_data.lot_contract_type_actual:
                lot_details_data.contract_type = 'Service'
            elif 'OBRAS' in lot_details_data.lot_contract_type_actual:
                lot_details_data.contract_type = 'Service'
            elif 'SUMINISTROS' in  lot_details_data.lot_contract_type_actual:
                lot_details_data.contract_type = 'Supply'
            else:
                pass
        except Exception as e:
            logging.info("Exception in contract_type: {}".format(type(e).__name__))
    #         pass
    # Onsite Field -Oferta Adjudicada
    # Onsite Comment -in tender_html_page click on "Ver ofertas" for page_detail 2

        try:
            url2 = tender_html_element.find_element(By.CSS_SELECTOR, ' td:nth-child(7) a').get_attribute("href")                     
            fn.load_page(page_details1, url2 ,80)
            logging.info(notice_data.notice_url)

            award_details_data = award_details()

            # Onsite Field -Fecha Adjudicación
            # Onsite Comment -None

            award_date = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
            award_details_data.award_date = datetime.strptime(award_date,'%d.%m.%Y').strftime('%Y/%m/%d')

            # Onsite Field -Importe bruto adjudicado(€)
            # Onsite Comment -None

            grossawardvaluelc = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
            grossawardvaluelc = grossawardvaluelc.replace('.','').replace(',','.')
            award_details_data.grossawardvaluelc =float(grossawardvaluelc)
            award_details_data.grossawardvalueeuro = award_details_data.grossawardvaluelc
            # Onsite Field -Plazo de ejecución:
            # Onsite Comment -in tender_html_page click on "Ver ofertas" for page_detail 2

            award_details_data.contract_duration = page_details1.find_element(By.XPATH, '//*[contains(text(),"Plazo de ejecución:")]//following::td[1]').text

            # Onsite Field -Importe neto adjudicado(€)
            # Onsite Comment -in tender_html_page click on "Ver ofertas" for page_detail 2

            netawardvaluelc = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(6)').text
            netawardvaluelc = netawardvaluelc.replace('.','').replace(',','.')
            award_details_data.netawardvaluelc = float(award_details_data.netawardvaluelc)
            award_details_data.netawardvalueeuro = award_details_data.netawardvaluelc
            # Onsite Field -Oferta Adjudicada >> Empresa
            # Onsite Comment -in tender_html_page click on "Ver ofertas" for page_detail 2

            award_details_data.bidder_name = page_details1.find_element(By.XPATH, '(//*[contains(text(),"Oferta Adjudicada")])[4]//following::td[3]').text

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
    
# # Onsite Field -Descarga de pliegos:
# # Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.XPATH, '//*[contains(text(),"Presentación de ofertas")]//following::td[4]/ul/li'):
            attachments_data = attachments()
        # Onsite Field -Descarga de pliegos:
        # Onsite Comment -split only file_name for ex."Pliego de Cláusulas Particulares (PDF)" , here take only "Pliego de Cláusulas Particulares"

            attachments_data.file_name = single_record.text.split('(')[0]
           
            try:
                attachments_data.file_type = single_record.text.split('(')[1].split(')')[0]
            except:
                attachments_data.file_type = single_record.text.split('.')[-1]
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
    urls = ["https://contratacion.aena.es/contratacion/principal?portal=adjudicaciones"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(2,5):
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
    
    page_details1.quit()
    
    output_json_file.copyFinalJSONToServer(output_json_folder)
