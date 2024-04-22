from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "br_vendorun"
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

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "br_vendorun"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.main_language = 'PT'
    
    notice_data.currency = 'USD'
    
    performance_country_data = performance_country() 
    performance_country_data.performance_country = 'BR'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.procurement_method = 2
    
    notice_data.script_name = "br_vendorun"
    
     # Onsite Field -Objeto da Compra
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a').get_attribute("href")
        fn.load_page(page_details,notice_data.notice_url,80)
    except:
        notice_data.notice_url = url
    
    # Onsite Field -Projeto:
    # Onsite Comment -None

    try:
        notice_data.project_name = page_details.find_element(By.CSS_SELECTOR, 'div > div:nth-child(1) > ul > li:nth-child(4)').text.split('Projeto:')[1]
    except Exception as e:
        logging.info("Exception in project_name: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Nº do Processo
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td.footable-first-visible').text.split('JOF')[1].strip()
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Objeto da Compra
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        notice_data.notice_title = GoogleTranslator(source='pt', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Modalidade da Compra
    # Onsite Comment -None

    try:
        notice_data.notice_type = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
    except Exception as e:
        logging.info("Exception in notice_type: {}".format(type(e).__name__))
        pass
    
    try:
        lot_canceled = tender_html_element.find_element(By.CSS_SELECTOR, 'td.footable-last-visible').text
        if 'Cancelada' in lot_canceled:
            notice_data.notice_type = 16
    except Exception as e:
        logging.info("Exception in lot_canceled: {}".format(type(e).__name__))
        pass
        
        
    
    # Onsite Field -Objeto da Compra
    # Onsite Comment -None

    try:
        notice_summary_english = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        notice_data.notice_summary_english = GoogleTranslator(source='pt', target='en').translate(notice_summary_english)
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, 'td:nth-child(3)'):
            customer_details_data = customer_details()
        # Onsite Field -Agência
        # Onsite Comment -None

            try:
                customer_details_data.org_name = single_record.text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
            
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__))
        pass
    
    
    try:
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR,'td:nth-child(3)'):
            funding_agencies_data = funding_agencies()
            try:
                funding_agencies_data.funding_agencies = single_record.find_element(By.CSS_SELECTOR, 'a').text
            except Exception as e:
                logging.info("Exception in funding_agencies: {}".format(type(e).__name__))
                pass
            funding_agencies_data.funding_agencies_cleanup()
            notice_data.funding_agencies.append(funding_agencies_data)
    except Exception as e:
        logging.info("Exception in funding_agencies: {}".format(type(e).__name__)) 
        pass
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.notice_text = page_details.find_element(By.XPATH, '//*[@id="licitacoes"]/section/div[3]/div/div/div[2]').get_attribute('outerHTML')
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Data publicação:
    # Onsite Comment -None

    try:
        publish_date = page_details.find_element(By.CSS_SELECTOR, " div.column5.no-margin.right > ul > li:nth-child(1)").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Projeto:
    # Onsite Comment -None

    try:
        notice_data.project_name = page_details.find_element(By.CSS_SELECTOR, 'div > div:nth-child(1) > ul > li:nth-child(4)').text
    except Exception as e:
        logging.info("Exception in project_name: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div:nth-child(6) div > div > ol >li'):
            cpvs_data = cpvs()
        # Onsite Field -None
        # Onsite Comment -None
            cpvs_data.cpvs = single_record.text.split('-')[0].strip()
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__))
        pass
        
# Onsite Field -Status
# Onsite Comment -None

    try:
        lot_number = 1 
        for single_record in page_details.find_elements(By.CSS_SELECTOR, ' div:nth-child(4) > div'):
            lot_details_data = lot_details()
        # Onsite Field -Objeto da Compra
        # Onsite Comment -None

            lot_title = single_record.find_element(By.CSS_SELECTOR, 'p').text.split(':')[1]
            lot_details_data.lot_title = GoogleTranslator(source='pt', target='en').translate(lot_title)
            lot_details_data.lot_number = lot_number
        # Onsite Field -Status
        # Onsite Comment -if status is "Cancelada" than its goes under lots canceled category (update / corrigendum)
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
            lot_number += 1
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__))
        pass
        
        
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#licitacoes > section > div.full.no-padding-top.licitacao-detail > div > div'):
            attachments_data = attachments()
        # Onsite Field -None
        # Onsite Comment -None
            try:
                clk = single_record.find_element(By.CSS_SELECTOR, 'div.tabs > ul > li:nth-child(2) > a').click()
                time.sleep(6)
            except:
                pass

            
            try: 
                attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR,'td.text-right> a').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
#         # Onsite Field -Tipo de arquivo
#         # Onsite Comment -None

            try:
                attachments_data.file_type = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
#         # Onsite Field -Título
#         # Onsite Comment -None

            try:
                attachments_data.file_description = single_record.find_element(By.CSS_SELECTOR, 'td.footable-first-visible').text
            except Exception as e:
                logging.info("Exception in file_description: {}".format(type(e).__name__))
                pass
            
            try:
                attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
            except Exception as e:
                logging.info("Exception in external_url: {}".format(type(e).__name__))
                pass
            
        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
           
    
    notice_data.identifier = str(notice_data.notice_no) +  str(notice_data.notice_url) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title)
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
    urls = ['https://vendor.un.org.br/processes'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(2,7):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="licitacoes"]/section/div[2]/div/div[1]/table/tbody/tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="licitacoes"]/section/div[2]/div/div[1]/table/tbody/tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="licitacoes"]/section/div[2]/div/div[1]/table/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="licitacoes"]/section/div[2]/div/div[1]/table/tbody/tr'),page_check))
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
