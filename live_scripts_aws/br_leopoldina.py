from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "br_leopoldina"
log_config.log(SCRIPT_NAME)
import re
import jsons
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from deep_translator import GoogleTranslator
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "br_leopoldina"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'br_leopoldina'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'BR'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'EUR'
    notice_data.main_language = 'PT'
    notice_data.procurement_method = 2
    notice_data.notice_type = 4
    
    # Onsite Field -None
    # Onsite Comment -None
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'p.objeto').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.XPATH, '//*[@id="lbl_rotuloLocal"]').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Data de abertura
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.text.split('Data de abertura:')[1].split('\n')[0].strip()
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Data limite
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.text.split('Data limite: ')[1].split('\n')[0].strip()
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
   
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, '#h4_nmLicitacao').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, '#h4_nmLicitacao > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except:
        notice_data.notice_url = url
    
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#textos > ul').get_attribute("outerHTML")
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
     # Onsite Field -Valor estimado:
    # Onsite Comment -None

    try:
        est_amount = page_details.find_element(By.CSS_SELECTOR, '#nuValorEstimado').text
        est_amount = re.sub("[^\d\.\,]", "",est_amount)
        est_amount = est_amount.replace('.','').replace(',','.').strip()
        notice_data.est_amount = float(est_amount)
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Valor estimado:
    # Onsite Comment -None

    try:
        grossbudgetlc = page_details.find_element(By.CSS_SELECTOR, '#nuValorEstimado').text
        grossbudgetlc = re.sub("[^\d\.\,]", "",grossbudgetlc)
        grossbudgetlc = grossbudgetlc.replace('.','').replace(',','.').strip()
        notice_data.grossbudgetlc = float(grossbudgetlc)
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
    
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = 'Prefeitura Municipal Leopoldina'
        customer_details_data.org_address = 'Rua Lucas Augusto, nº 68 - Centro - Cep 36700-088 - Leopoldina-MG - Fone: (32) 3694-4200'
        customer_details_data.org_country = 'BR'
        customer_details_data.org_language = 'PT'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        lot_details_data = lot_details()
    # Onsite Field -None
    # Onsite Comment -None
        lot_details_data.lot_number = 1
        lot_details_data.lot_title = notice_data.notice_title
        notice_data.is_lot_default = True

#     # Onsite Field -None
#     # Onsite Comment -None

        try:
            lot_details_data.lot_description = notice_data.notice_title
        except Exception as e:
            logging.info("Exception in lot_description: {}".format(type(e).__name__))
            pass
        
        try:
            lot_grossbudget_lc = page_details.find_element(By.CSS_SELECTOR, '#nuValorEstimado').text
            lot_grossbudget_lc = re.sub("[^\d\.\,]", "",lot_grossbudget_lc)
            lot_grossbudget_lc = lot_grossbudget_lc.replace('.','').replace(',','.').strip()
            lot_details_data.lot_grossbudget_lc = float(lot_grossbudget_lc)
        except Exception as e:
            logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
            pass
        
        lot_details_data.lot_details_cleanup()
        notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -Editais
# Onsite Comment -click on " Editais" to get attachments
    try:
        clk= page_details.find_element(By.XPATH, '//*[@id="closeCookieConsent"]').click()
    except:
        pass

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#editais > div > div > div'):
            if 'AUTORIZAÇÃO' in single_record.text:
                pass
            else:
                attachments_data = attachments()
            
    # Onsite Field -None
    # Onsite Comment -None
                file_name = single_record.text
                attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, ' span.tit_arq').text
                attachments_data.file_type = 'doc'

#     Onsite Field -None
#     Onsite Comment -None

                try:
                    file_size = single_record.text
                    attachments_data.file_size = single_record.find_element(By.CSS_SELECTOR, ' p.tam_arq > strong').text
                    attachments_data.file_type = 'doc'
                except Exception as e:
                    logging.info("Exception in file_size: {}".format(type(e).__name__))
                    pass

         # Onsite Field -None
        # Onsite Comment -None

                external = single_record.text
                external_url = single_record.find_element(By.CSS_SELECTOR, 'span.tit_arq').click()
                file_dwn = Doc_Download.file_download()
                attachments_data.external_url = str(file_dwn[0])
                attachments_data.file_type = 'doc'
                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass

    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title) 
    logging.info(notice_data.identifier)
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
page_details = Doc_Download.page_details
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://www.leopoldina.mg.gov.br/licitacoes'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(2,5):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="listagem"]/ul'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="listagem"]/ul')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="listagem"]/ul')))[records]
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
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="listagem"]/ul'),page_check))
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
    
