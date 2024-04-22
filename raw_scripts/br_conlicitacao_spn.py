#As some fields are given by Akanksha mam , we not getting in site.. so we keep that fields pending (like Qty , ......  ) rest of all the fileds are available in script

#login_id:fcarignano@gmail.com
#password:L2P@Tf2ATiUr6Jp

#after opening the url click on "Encontrar Licitações" to get tender data.



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
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "br_conlicitacao_spn"
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
    notice_data.script_name = 'br_conlicitacao_spn'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'PT'
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'BR'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'BRL'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_type = 4
    
    # Onsite Field -Atualizada em
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div.ml-md-auto.ml-2.text-white.mr-2 > span:nth-child(2)").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Objeto
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.tour-bidding-info.border.rounded-top.pt-2.px-2 > div:nth-child(1) > div.col-md-11').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Datas >> Abertura:
    # Onsite Comment -1.split after "Abertura:".	2.if here "Prazo: 27/11/2023 09:00" is present then don't grab that date , only grab if "Abertura: 24/11/2023 09:00" is present.

    try:
        notice_data.notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, 'div.tour-bidding-info.border.rounded-top.pt-2.px-2 > div:nth-child(2) > div.col-md-5 > div:nth-child(1) > div').text
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    
    # Onsite Field -Datas >> Abertura:
    # Onsite Comment -1.split after "Abertura:".	2.if here "Prazo: 27/11/2023 09:00" is present then don't grab that date , only grab if "Abertura: 24/11/2023 09:00" is present.

    try:
        notice_data.document_purchase_start_time = tender_html_element.find_element(By.CSS_SELECTOR, 'div.tour-bidding-info.border.rounded-top.pt-2.px-2 > div:nth-child(2) > div.col-md-5 > div:nth-child(1) > div').text
    except Exception as e:
        logging.info("Exception in document_purchase_start_time: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Datas >> Documento:
    # Onsite Comment -1.split after "Documento:".

    try:
        notice_data.document_purchase_end_time = tender_html_element.find_element(By.CSS_SELECTOR, 'div.tour-bidding-info.border.rounded-top.pt-2.px-2 > div:nth-child(2) > div.col-md-5 > div:nth-child(2) > div').text
    except Exception as e:
        logging.info("Exception in document_purchase_end_time: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Edital
    # Onsite Comment -None

    try:
        notice_data.related_tender_id = tender_html_element.find_element(By.CSS_SELECTOR, 'div.tour-bidding-info.border.rounded-top.pt-2.px-2 > div:nth-child(3) > div.col-md-5.text-secondary').text
    except Exception as e:
        logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Nº Conlicitação
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div.tour-bidding-info.border.rounded-top.pt-2.px-2 > div:nth-child(3) > div:nth-child(4)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(4) > div.col-md-11').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -*add following clicks into notice_text:1)click on "Ver menos informações da licitação" in tender_html_element	2)click on "div.row.bidding-info.my-2.d-print-none > div > button=Itens" in tender_html_element.	3)after clicking on notice_url then click on "div.col-2.table-text.text-center > a=Acessar".
    try:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, 'div.modal-body').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    # Onsite Field -Site
    # Onsite Comment -None

    try:
        notice_data.additional_tender_url = page_main.find_element(By.XPATH, '//*[contains(text(),"Órgão Público")]//following::a[1]').text
    except Exception as e:
        logging.info("Exception in additional_tender_url: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_main.find_elements(By.XPATH, 'div.modal-body'):
            customer_details_data = customer_details()
            customer_details_data.org_country = 'BR'
            customer_details_data.org_language = 'PT'
        # Onsite Field -Órgão
        # Onsite Comment -None

            try:
                customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(4) > div.col-md-11').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Cidade
        # Onsite Comment -1.split only city_name.

            try:
                customer_details_data.org_city = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(5) > div.col-md-11').text
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Tel
        # Onsite Comment -1.click on "Ver menos informações da licitação" in tender_html_element to get this data.

            try:
                customer_details_data.org_phone = tender_html_element.find_element(By.CSS_SELECTOR, 'div.bidding-hidden-info.d-print-block.d-block > div:nth-child(3) > div.col-md-5.text-secondary').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Endereço
        # Onsite Comment -1.split after "Endereço".

            try:
                customer_details_data.org_address = page_main.find_element(By.XPATH, '//*[contains(text(),"Órgão Público")]//following::p[3]').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Estado
        # Onsite Comment -1.split after "Estado".

            try:
                customer_details_data.org_state = page_main.find_element(By.XPATH, '//*[contains(text(),"Órgão Público")]//following::p[5]').text
            except Exception as e:
                logging.info("Exception in org_state: {}".format(type(e).__name__))
                pass
        
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, 'div.row.mx-1.mt-5 > div > div > div > div'):
            attachments_data = attachments()
        # Onsite Field -None
        # Onsite Comment -None

            try:
                attachments_data.file_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div.row.bidding-info.my-2.d-print-none > div > div').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -None

            attachments_data.external_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.row.bidding-info.my-2.d-print-none > div > div > a').get_attribute('href')
            
        
        # Onsite Field -None
        # Onsite Comment -1.split file_type.

            try:
                attachments_data.file_type = tender_html_element.find_element(By.CSS_SELECTOR, 'div.row.bidding-info.my-2.d-print-none > div > div > a').text
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass


#There are two formats of lots:
#               format-1)click on "div.row.bidding-info.my-2.d-print-none > div > button=Itens" in tender_html_element.	
#               format-2)click on "div:nth-child(4) > div.col-md-11" in tender_html_element.

    
# Onsite Field -None
# Onsite Comment -format-1)click on "div.row.bidding-info.my-2.d-print-none > div > button=Itens" in tender_html_element.

    try:              
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, 'div.card-body.p-3 > div:nth-child(5)'):
            lot_details_data = lot_details()
        # Onsite Field -None
        # Onsite Comment -1.split lot_actual_number.	2)take "LOTE 1" in lot actual_number.	3)there are multiple lots..so take each lot.

            try:
                lot_details_data.lot_actual_number = tender_html_element.find_element(By.CSS_SELECTOR, 'div.card-body.p-3 > div:nth-child(5)').text
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -1.take line before "Valor total estimado do lote :". 	2)here "9m3 40 R$ 1.730,84 R$ 69.233,43" take "40" in lot_quantity.

            try:
                lot_details_data.lot_quantity = tender_html_element.find_element(By.CSS_SELECTOR, 'div.card-body.p-3 > div:nth-child(5)').text
            except Exception as e:
                logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -1.take line before "Valor total estimado do lote :". 	2)here "9m3 40 R$ 1.730,84 R$ 69.233,43" take "m3" in lot_quantity_uom.

            try:
                lot_details_data.lot_quantity_uom = tender_html_element.find_element(By.CSS_SELECTOR, 'div.card-body.p-3 > div:nth-child(5)').text
            except Exception as e:
                logging.info("Exception in lot_quantity_uom: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -1.take next line after "LOTE " keyword in lot_title.

            try:
                lot_details_data.lot_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.card-body.p-3 > div:nth-child(5)').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -1.split after "Valor total estimado do lote :".

            try:
                lot_details_data.lot_grossbudget_lc = tender_html_element.find_element(By.CSS_SELECTOR, 'div.card-body.p-3 > div:nth-child(5)').text
            except Exception as e:
                logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
                pass
        
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -format-2)click on "div:nth-child(4) > div.col-md-11" in tender_html_element.

    try:              
        for single_record in page_main.find_elements(By.CSS_SELECTOR, 'div.modal-body > div:nth-child(5)'):
            lot_details_data = lot_details()
        # Onsite Field -Objeto
        # Onsite Comment -None

            try:
                lot_details_data.lot_title = page_main.find_element(By.CSS_SELECTOR, 'div.col-7.table-text').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Edital
        # Onsite Comment -None

            try:
                lot_details_data.lot_actual_number = page_main.find_element(By.CSS_SELECTOR, 'div.col-3.table-text').text
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Resultados >> Valor global
        # Onsite Comment -1.after clicking on notice_url then click on "div.col-2.table-text.text-center > a=Acessar". to get this data.

            try:
                lot_details_data.lot_grossbudget_lc = page_main.find_element(By.CSS_SELECTOR, '#resultados > div > div > div > div.mb-3 > div > table > tbody > tr > td:nth-child(3)').text
            except Exception as e:
                logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
                pass
        
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
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
page_details = fn.init_chrome_driver(arguments) 
page_main = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://consulteonline.conlicitacao.com.br/"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,55):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="windowDiv"]/div[3]/div[2]/div/div[1]/div/div[4]/div/div'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="windowDiv"]/div[3]/div[2]/div/div[1]/div/div[4]/div/div')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="windowDiv"]/div[3]/div[2]/div/div[1]/div/div[4]/div/div')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break

                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="windowDiv"]/div[3]/div[2]/div/div[1]/div/div[4]/div/div'),page_check))
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
    page_details.quit() 
    
    output_json_file.copyFinalJSONToServer(output_json_folder)