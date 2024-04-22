from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "br_barueri"
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
import gec_common.Doc_Download_ingate

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "br_barueri"
Doc_Download = gec_common.Doc_Download_ingate.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.main_language = 'PT'
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'BR'
    notice_data.performance_country.append(performance_country_data)
    notice_data.currency = 'BRL'
    notice_data.script_name = 'br_barueri'
    notice_data.procurement_method = 2
    notice_data.notice_type = 4
    notice_data.notice_url = url


    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
        notice_data.notice_title  = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title )
        notice_data.notice_summary_english = notice_data.notice_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass


    try:
        notice_data.type_of_procedure_actual = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
    except Exception as e:
        logging.info("Exception in type_of_procedure: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td.areaClique').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    customer_details_data = customer_details()
    try:
        customer_details_data.org_description = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
    except Exception as e:
        logging.info("Exception in org_description: {}".format(type(e).__name__))
        pass
    customer_details_data.org_name = 'MUNICÍPIO DE BARUERI'
    customer_details_data.org_country = 'BR'
    customer_details_data.customer_details_cleanup()
    notice_data.customer_details.append(customer_details_data)
    
    try:
        notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').click()
    except:
        notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td.areaClique')
        page_main.execute_script("arguments[0].click();",notice_url)
    time.sleep(5)
    
    try:
        notice_data.notice_text =  WebDriverWait(page_main, 150).until(EC.presence_of_element_located((By.XPATH, '//*[@id="grupoResumo"]'))).get_attribute('outerHTML')   
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    try:
        publish_date = page_main.find_element(By.XPATH, '//*[contains(text(),"Date of publication: ")]//following::span[1]').text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%m/%d/%Y').strftime('%Y/%m/%d')
    except:
        try:
            publish_date = page_main.find_element(By.CSS_SELECTOR, 'span#lblDataPublicacao').text
            publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date,'%m/%d/%Y').strftime('%Y/%m/%d')
        except Exception as e:
            logging.info("Exception in publish_date: {}".format(type(e).__name__))
            pass
    logging.info(notice_data.publish_date)

    try:              
        for single_record in WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="gridAnexo"]/div[2]/table/tbody/tr'))):
            attachments_data = attachments()
            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
            external_url = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1) > div').click()
            
            file_dwn = Doc_Download.file_download()
            attachments_data.external_url = str(file_dwn[0])
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    try:
        page_main.find_element(By.XPATH, '//*[@id="areaDetalhes"]/div[1]/h1/div/a[12]').click()
        time.sleep(5)
    except:
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    notice_data.identifier = str(notice_data.notice_no) +  str(notice_data.notice_url) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title)   
    logging.info(notice_data.identifier)
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
    urls = ['https://compras.barueri.sp.gov.br/portal/Mural.aspx?nNmTela=E'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)

        try:
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="trListaMuralProcesso"]/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="trListaMuralProcesso"]/tr')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
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
    output_json_file.copyFinalJSONToServer(output_json_folder)
