
from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "jp_choutatsujst_spn"
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
SCRIPT_NAME = "jp_choutatsujst_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'jp_choutatsujst_spn'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'JP'
    notice_data.performance_country.append(performance_country_data)
    notice_data.currency = 'JPY'
    notice_data.main_language = 'JA'
    notice_data.procurement_method = 2
    notice_data.notice_type = 4


    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass 
         
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
        notice_data.notice_title = GoogleTranslator(source='ja', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass              
    
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        publish_date = GoogleTranslator(source='ja', target='en').translate(publish_date)
        publish_date = publish_date.split('(')[0].strip()
        notice_data.publish_date = datetime.strptime(publish_date, '%Y/%m/%d').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass            
                
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return                   

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(8)').text
        notice_deadline = GoogleTranslator(source='ja', target='en').translate(notice_deadline)
        if len(notice_deadline)>4:
            notice_deadline_1 = notice_deadline.split('(')[0]
            notice_deadline_2 = notice_deadline.split(')')[1].strip()
            notice_deadline_3 = notice_deadline_1 + ' ' + notice_deadline_2
            notice_deadline_3 = re.findall('\d+/\d+/\d+ \d+:\d+', notice_deadline_3)[0]
            notice_data.notice_deadline = datetime.strptime(notice_deadline_3, '%Y/%m/%d %H:%M').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass     
    
    try:
        document_purchase_end_time = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(9)').text
        document_purchase_end_time = GoogleTranslator(source='ja', target='en').translate(document_purchase_end_time)        
        if len(document_purchase_end_time)>4:
            document_purchase_end_time = document_purchase_end_time.split('(')[0].strip()            
            notice_data.document_purchase_end_time = datetime.strptime(document_purchase_end_time, '%Y/%m/%d').strftime('%Y/%m/%d')            
    except Exception as e:
        logging.info("Exception in document_purchase_end_time: {}".format(type(e).__name__))
        pass                 
    
    try:
        notice_data.contract_type_actual = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
        if '工事' in notice_data.contract_type_actual or '作業' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Works'
        elif '設計・ｺﾝｻﾙﾃｨﾝｸ' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Consultancy'
        elif '物品の購入' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Supply'
        elif '製造・印刷' in notice_data.contract_type_actual or '研究用機器・ 研究用消耗品類' in notice_data.contract_type_actual or '役務' in notice_data.contract_type_actual or '管理・ 運営' in notice_data.contract_type_actual or '保守' in notice_data.contract_type_actual or '使用・利用' in notice_data.contract_type_actual or '借入' in notice_data.contract_type_actual or '売払' in notice_data.contract_type_actual or '貸付' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Service'
        else:
            pass
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass     
        
    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(6)').text  
    except:
        pass
        
    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML') 
    except:
        pass
        
    notice_data.notice_url = 'https://choutatsu.jst.go.jp/'      

    try:              
        customer_details_data = customer_details()
        
        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(7)').text
        customer_details_data.org_country = 'JP'
        customer_details_data.org_language = 'JA'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass      
    
    try:   
        attachment_click_open = WebDriverWait(tender_html_element, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'td:nth-child(4) > div > span > img'))).click()  
        logging.info("attachment_click_open")
        time.sleep(5)
    except Exception as e:
        logging.info("Exception in attachment_click_open: {}".format(type(e).__name__)) 
        pass
    
    selector_new = selector.split('div.name')[0]
    selector_new = selector_new + ' div:nth-child(2) > div:nth-child(2) > table > tbody > tr:nth-child(2) > td:nth-child(2) > div > a'
    
    notice_text_selector = selector.split('div.name')[0]
    notice_text_selector = notice_text_selector + ' div:nth-child(2)'
    notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR,notice_text_selector).get_attribute("outerHTML")    
    
    try:              
        for single_record in page_main.find_elements(By.CSS_SELECTOR,selector_new): 
            attachments_data = attachments()
            attachments_data.external_url = single_record.get_attribute('href') 
            attachments_data.file_name = single_record.text
            try:
                attachments_data.file_type = attachments_data.file_name.split('.')[-1]
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass          
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass        
        
    try:   
        attachment_click_close = WebDriverWait(tender_html_element, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'td:nth-child(4) > div > span > img'))).click()
        logging.info("attachment_click_close")
        time.sleep(3)
    except Exception as e:
        logging.info("Exception in attachment_click_open: {}".format(type(e).__name__)) 
        pass        

    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.notice_deadline) + str(notice_data.local_title)
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

    urls = ['https://choutatsu.jst.go.jp/'] 

    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)

        try:
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#jquery > div > div:nth-child(3) > div:nth-child(3) > div.name > table > tbody > tr')))
            length = len(rows) 

            selector = '#jquery > div > div:nth-child(3) > div.name > table > tbody > tr'
            for records in range(1,length):
                selector_parts = selector.split('>')
                selector_parts.insert(3, 'div:nth-child(3)')
                selector = ' > '.join(selector_parts)
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector)))[0]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break

                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
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
