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
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "br_aracajuco"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'br_aracajuco'
    
    notice_data.main_language = 'PT'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'BR'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'BRL'
    
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 4
    notice_data.notice_url = url
    # Onsite Field -Situation >> Opening on
    # Onsite Comment -None
    
    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "b:nth-child(1)").text
        notice_deadline = GoogleTranslator(source='pt', target='en').translate(notice_deadline)
        notice_deadline = re.findall('\w+/\d+',notice_deadline)[0]
        th1 = threshold.split('/')[0]
        deadline = notice_deadline + '/' + th1
        notice_data.notice_deadline = datetime.strptime(deadline,'%b/%d/%Y').strftime('%Y/%m/%d %H:%M:%S')
    except:
        try:
            notice_deadline = re.findall('\d+/\w+',notice_deadline)[0]
            th1 = threshold.split('/')[0]
            deadline = notice_deadline + '/' + th1
            notice_data.notice_deadline = datetime.strptime(deadline,'%d/%b/%Y').strftime('%Y/%m/%d %H:%M:%S')
        except Exception as e:
            logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
            pass
    logging.info(notice_data.notice_deadline)
    if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
        return
    
    # Onsite Field -Modalidade
    # Onsite Comment -None

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text.strip()
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    # Onsite Field -Edital
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
        notice_data.notice_title = GoogleTranslator(source='pt', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    # Onsite Field -Edital
    # Onsite Comment -None

    try:
        cust_org_city = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5) > div:nth-child(3)').text.split(':')[1]
    except:
        pass
    # Onsite Field -Edital
    # Onsite Comment -None

    try:
        notice_url_clk = WebDriverWait(tender_html_element, 80).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'td:nth-child(4) > a'))).click()
        time.sleep(10)
        # Onsite Field -Data da publicação
        # Onsite Comment -If publish_date is not availabel then take as threshold
    
        try:
            publish_date = WebDriverWait(page_main, 30).until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(),' Data da publicação:')]//following::div[1]"))).text
            publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d')
        except Exception as e:
            logging.info("Exception in publish_date: {}".format(type(e).__name__))
            pass
        
        
        # Onsite Field -Nº do edital:
        # Onsite Comment -None
    
        try:
            notice_data.notice_no = page_main.find_element(By.XPATH, '//*[contains(text(),"Nº do edital:")]//following::div[1]').text
        except Exception as e:
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass
        
        
    # Onsite Field -None
    # Onsite Comment -None
    
        try:              
            customer_details_data = customer_details()
            # Onsite Field -Orgão responsável:
            # Onsite Comment -None
    
            try:
                customer_details_data.org_name = page_main.find_element(By.XPATH, '//*[contains(text()," Orgão responsável:")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
            
            # Onsite Field -Orgão solicitante:
            # Onsite Comment -None
    
            try:
                customer_details_data.org_description = page_main.find_element(By.XPATH, '//*[contains(text(),"Orgão solicitante:")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in org_description: {}".format(type(e).__name__))
                pass
            # Onsite Field -Local:
            # Onsite Comment -None
            
            try:                                                                                   
                customer_details_data.org_city = cust_org_city
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass
            
            customer_details_data.org_country = 'BR'
            
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
        except Exception as e:
            logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
            pass
        
    
    
        try:            
            lot_number=1
            for single_record in page_main.find_elements(By.CSS_SELECTOR, 'div.full.text-left.border-bottom-dotted'):
                lot_details_data = lot_details()
                
                lot_details_data.lot_number=lot_number
            # Onsite Field -Lote 1
            # Onsite Comment -None
    
                try:
                    lot_details_data.lot_title = single_record.text.split('Quantidade')[0]
                except:
                    lot_details_data.lot_title = notice_data.notice_title
            # Onsite Field -Quantidade:
            # Onsite Comment -None
    
                try:
                    lot_details_data.lot_quantity = float(single_record.find_element(By.XPATH, '//*[contains(text(),"Quantidade")]//following::span').text)
                except Exception as e:
                    logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                    pass
            
            # Onsite Field -take "OBRA E SERVIÇO DE ENGENHARIA" and "SERVIÇO"   as "service"...  "MATERIAL PERMANENTE" and "MATERIAL DE CONSUMO" as "supply".
            # Onsite Comment -None
    
                try:
                    contract_type = single_record.text
                    if 'SERVIÇO' in contract_type or 'OBRA E SERVIÇO DE ENGENHARIA' in contract_type:
                        lot_details_data.contract_type == 'Service'
                    elif 'MATERIAL PERMANENTE' in contract_type or 'MATERIAL DE CONSUMO' in contract_type:
                        lot_details_data.contract_type == 'Supply'
                    else:
                        pass
                except Exception as e:
                    logging.info("Exception in contract_type: {}".format(type(e).__name__))
                    pass
                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
                
                lot_number += 1
                
        except Exception as e:
            logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
            pass
        
    # Onsite Field -None
    # Onsite Comment -None
    
        try: 
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#PlaceHolder_ucConsulta_ucConsultaLicitacoes_ucCadastro_GridAnexos > tbody > tr')))
            length = len(rows)
            for k in range(0,length):
                single_record = page_main.find_elements(By.CSS_SELECTOR, '#PlaceHolder_ucConsulta_ucConsultaLicitacoes_ucCadastro_GridAnexos > tbody > tr')[k]
                attachments_data = attachments()
                # Onsite Field -Anexo(s):
                # Onsite Comment -None
    
                attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a').text    
            # Onsite Field -Anexo(s):
            # Onsite Comment -split file_size from file_name
    
                try:
                    attachments_data.file_size = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a > i').text.split('(')[1].split(')')[0]
                except Exception as e:
                    logging.info("Exception in file_size: {}".format(type(e).__name__))
                    pass
            # Onsite Field -Anexo(s):
            # Onsite Comment -None
    
                external_url = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a').click()
                time.sleep(4)
                page_main.switch_to.window(page_main.window_handles[1])
                attachments_data.external_url = page_main.current_url
                time.sleep(8)
                page_main.close()
                page_main.switch_to.window(page_main.window_handles[0])
                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
        except Exception as e:
            logging.info("Exception in attachments: {}".format(type(e).__name__)) 
            pass
        
        try:
            notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, '#PlaceHolder_ucConsulta_ucConsultaLicitacoes_ucCadastro_updPanel').get_attribute("outerHTML")                     
        except Exception as e:
            logging.info("Exception in notice_text: {}".format(type(e).__name__))
            pass
        
        try:
            notice_url_bk_clk = page_main.find_element(By.XPATH, '//*[@id="PlaceHolder_ucConsulta_ucConsultaLicitacoes_ucCadastro_cmdFechar"]').click() 
            time.sleep(5)
        except Exception as e:
            logging.info("Exception in notice_url_bk_clk: {}".format(type(e).__name__))
            pass
            
    except Exception as e:
        logging.info("Exception in notice_url_clk: {}".format(type(e).__name__))
        pass
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    duplicate_check_data = fn.duplicate_check_data_from_previous_scraping(SCRIPT_NAME,MAX_NOTICES_DUPLICATE,notice_data.identifier,previous_scraping_log_check)
    NOTICE_DUPLICATE_COUNT = duplicate_check_data[1]
    if duplicate_check_data[0] == False:
        return
    notice_data.tender_cleanup()
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
chrome_options = Options()
#chrome_options.add_argument("--headless")
for argument in arguments:
    chrome_options.add_argument(argument)
page_main = webdriver.Chrome(executable_path=ChromeDriverManager().install(), chrome_options=chrome_options)

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.aracajucompras.se.gov.br/publico/Processos.aspx?pLicit=S"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,3):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="PlaceHolder_ucConsulta_ucConsultaLicitacoes_Grid"]/tbody/tr[2]'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'tr.border-bottom-dotted')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'tr.border-bottom-dotted')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break
                
                if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                    logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                    break


            try:   
                next_page = WebDriverWait(page_main, 80).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                page_main.execute_script("arguments[0].click();",next_page)
                logging.info("Next page")
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="PlaceHolder_ucConsulta_ucConsultaLicitacoes_Grid"]/tbody/tr[2]'),page_check))
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
    
    output_json_file.copyFinalJSONToServer(output_json_folder)
