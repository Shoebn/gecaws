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

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "cn_hngp_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'cn_hngp_spn'
    
    notice_data.main_language = 'ZH'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'CN'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'CNY'
    
    notice_data.notice_type = 4
    
    notice_data.procurement_method = 2
  
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, ' ul > li a').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_summary_english =  notice_data.notice_title
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
 

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "span.Gray.Right").text
        publish_date = re.findall('\d{4}-\d+-\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%Y-%m-%d').strftime('%Y/%m/%d')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
   

    try:
        notice_data.document_type_description = "采购公告"
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
   
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.List2 > ul > li > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)      
        logging.info(notice_data.notice_url)
    except:
        notice_data.notice_url = url
    
    try:
        notice_data.project_name=page_details.find_element(By.CSS_SELECTOR, '#content > table > tbody > tr:nth-child(5) > td').text.split("：")[1]
        notice_data.project_name = GoogleTranslator(source='auto', target='en').translate(notice_data.project_name)
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#print-content').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass

    try:
       
        notice_deadline = page_details.find_element(By.CSS_SELECTOR, "tr:nth-child(28) > td").text
        notice_deadline = GoogleTranslator(source='auto', target='en').translate(notice_deadline)
        notice_deadline = re.findall('\d+:\d+, \w+ \d+, \d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%H:%M, %B %d, %Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_no = page_details.find_element(By.CSS_SELECTOR, 'tr:nth-child(4)').text.split("项目编号：")[1]
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass


    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#print-content'):
            customer_details_data = customer_details()
            customer_details_data.org_country = 'CN'

            try:
                customer_details_data.org_name = single_record.find_element(By.CSS_SELECTOR, 'span.Gray').text
                customer_details_data.org_name = GoogleTranslator(source='auto', target='en').translate(customer_details_data.org_name)
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
  

            try:
                org_description = single_record.find_element(By.CSS_SELECTOR, 'tr:nth-child(39)').text.split("名称：")[1]
                customer_details_data.org_description = GoogleTranslator(source='auto', target='en').translate(org_description)
            except Exception as e:
                logging.info("Exception in org_description: {}".format(type(e).__name__))
                pass
            

            try:
                org_address = page_details.find_element(By.CSS_SELECTOR, 'tr:nth-child(40)').text.split("地址：")[1]
                customer_details_data.org_address = GoogleTranslator(source='auto', target='en').translate(org_address)
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
       

            try:
                contact_person = page_details.find_element(By.CSS_SELECTOR, 'tr:nth-child(41)').text.split("联系人：")[1]
                customer_details_data.contact_person = GoogleTranslator(source='auto', target='en').translate(contact_person)
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass

            try:
                customer_details_data.org_phone = page_details.find_element(By.CSS_SELECTOR, 'tr:nth-child(42)').text.split("联系方式：")[1]
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
        
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass


    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.List1.Top5'):
            attachments_data = attachments()
            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'div.List1.Top5 > ul > li  > a').text
            attachments_data.file_name = GoogleTranslator(source='auto', target='en').translate(attachments_data.file_name)
            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'div.List1.Top5 > ul > li  > a').get_attribute('href')
            try:
                file_type =  attachments_data.external_url
                if '.pdf' in file_type or '.PDF' in file_type:
                    attachments_data.file_type = 'pdf'
                elif '.docx' in file_type:
                     attachments_data.file_type = 'docx'
                elif '.jpg' in file_type:
                    attachments_data.file_type = 'jpg'
                elif '.zip' in file_type:
                    attachments_data.file_type = 'zip'
                else:
                    pass
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass

    try:
        notice_data.additional_tender_url = page_details.find_element(By.CSS_SELECTOR, 'td > div > p > a').get_attribute('href')
    except Exception as e:
        logging.info("Exception in additional_tender_url: {}".format(type(e).__name__))
        pass

    try:
        type_of_procedure_actual = page_details.find_element(By.CSS_SELECTOR, 'tr:nth-child(6)').text
        notice_data.type_of_procedure_actual = GoogleTranslator(source='auto', target='en').translate(type_of_procedure_actual)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
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
page_main = fn.init_chrome_driver(arguments)
page_details1 = fn.init_chrome_driver(arguments)
page_details = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['http://www.hngp.gov.cn/henan/list2?channelCode=0101&pageNo=1&pageSize='] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,15):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[4]/div[2]/div/div[1]/ul/li[1]'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[4]/div[2]/div/div[1]/ul/li')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[4]/div[2]/div/div[1]/ul/li')))[records]
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/div[4]/div[2]/div/div[1]/ul/li[1]'),page_check))
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
    page_details1.quit()
    
    output_json_file.copyFinalJSONToServer(output_json_folder)
