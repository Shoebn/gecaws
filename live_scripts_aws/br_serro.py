from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "br_serro"
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

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "br_serro"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'br_serro'
    
    notice_data.main_language = 'PT'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'BR'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'BRL'
    
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 4
         
    notice_data.document_type_description = 'Editais de Licitações'
    
    

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.ed_descricao_edital').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_summary_english = notice_data.notice_title 
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = tender_html_element.find_element(By.CSS_SELECTOR, 'div.ed_descricao_edital').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    try: 
        notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div.ed_rmv > div.ed_info_edital > div:nth-child(1)').text  
        notice_data.notice_no = notice_no.split(':')[1].strip()
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div.ed_cont_postagem_edital > span.sw_lato").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "div.ed_cont_realizacao_edital > span.sw_lato").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.ed_edital > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except:
        notice_data.notice_url = url
    
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.ed_area_navegacao_edital').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass

    try:
        additional_tender_url = page_details.find_element(By.CSS_SELECTOR, "div.ed_local_edital > div.ed_descricao_detalhe.sw_lato").text 
        if 'https' in additional_tender_url:
            notice_data.additional_tender_url = additional_tender_url
        else:
            pass
    except Exception as e:
        logging.info("Exception in additional_tender_url: {}".format(type(e).__name__))
        pass

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = 'Prefeitura Municipal de Serro'
        customer_details_data.org_address = 'Praça João Pinheiro, 154 - Centro - CEP: 39150-000'
        customer_details_data.org_parent_id = '7798132'
        customer_details_data.org_country = 'BR'
        customer_details_data.org_language = 'PT'
        customer_details_data.org_phone = '(38) 3541-1368'
        customer_details_data.org_email = 'comunicacao@serro.mg.gov.br'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:
        clk1 = page_details.find_element(By.XPATH,'//*[@id="btn_vencedores_edital"]').click() 
        time.sleep(3)
    except:
        pass

    try:   
        lot_number = 1
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#ed_lista_itens_vencedores_edital > tbody > tr'):
            lot_details_data = lot_details()
            lot_details_data.lot_number = lot_number 
            try:
                lot_title = single_record.find_element(By.CSS_SELECTOR, 'td').text
                ind = lot_title.find('|',5)
                lot_details_data.lot_title = lot_title[ind:]
            except:
                lot_details_data.lot_title = notice_data.notice_title 
                notice_data.is_lot_default = True

            try:
                lot_details_data.lot_actual_number = lot_title[:ind]
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass

            try:
                lot_details_data.lot_description = lot_title
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass

            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
            lot_number+=1
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass

    try:
        clk2 = page_details.find_element(By.XPATH,'//*[@id="btn_arquivos_edital"]').click()     
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
    time.sleep(5)  

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.ed_arquivo_edital')[1:]:
            attachments_data = attachments()

            try: 
                file_name = single_record.find_element(By.CSS_SELECTOR, 'div.ed_nome_arquivo.sw_lato').text 
                attachments_data.file_name = file_name.split('PDF')[0]
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass

            try:
                attachments_data.file_description = file_name
            except Exception as e:
                logging.info("Exception in file_description: {}".format(type(e).__name__))
                pass

            try:
                attachments_data.file_type = file_name
                if 'PDF' in attachments_data.file_type:
                    attachments_data.file_type = 'PDF'
                elif 'XLSX' in attachments_data.file_type:
                    attachments_data.file_type  = 'xlsx'
                elif 'doc' in attachments_data.file_type:
                    attachments_data.file_type = 'doc'
                elif 'zip' in attachments_data.file_type:
                    attachments_data.file_type = 'zip'
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
 
            try:  
                file_size = file_name
                attachments_data.file_size = file_size.split(' - ')[1] 
            except Exception as e:
                logging.info("Exception in file_size: {}".format(type(e).__name__))
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
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
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
    for page_no in range(1,7):
        url = 'https://www.serro.mg.gov.br/portal/editais/'+str(page_no)+'/1/0/0/0/0/0/0/0/data-realizacao-decrescente/0'
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[4]/div/div/div[3]/div[4]/div')))
            length = len(rows)
            for records in range(1,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[4]/div/div/div[3]/div[4]/div')))[records]
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
    page_details.quit() 
    output_json_file.copyFinalJSONToServer(output_json_folder)
    
