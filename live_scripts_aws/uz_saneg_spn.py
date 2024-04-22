from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "uz_saneg_spn"
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

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "uz_saneg_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'uz_saneg_spn'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'UZ'
    notice_data.performance_country.append(performance_country_data)
   
    notice_data.currency = 'UZS'
   
    notice_data.main_language = 'RU'
    
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 4
    
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, ' div.news-one-content > p').text.split('Прямой запрос ТКП:')[1].split('Дата объявления:')[0].strip()
    except:
        try:
            notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, ' div.news-one-content > p').text.split('Тендер:')[1].split('Дата объявления:')[0].strip()
        except Exception as e:
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass
        
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div.news-one-info > span").text
        publish_date = re.findall('\d+.\d+.\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'UZ'
        customer_details_data.org_language = 'RU'
        customer_details_data.org_name =  "Sanoat Energetika Guruhi"
        customer_details_data.org_parent_id = 7772652
        customer_details_data.org_address ="Ташкент, проспект Бунедкор, 47"
        customer_details_data.org_email = "info@saneg.com"
        customer_details_data.org_phone = '+998 78 1500057'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass    

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, ' div.news-one-content > h4').text
        if len(notice_data.local_title) < 5:
            return
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
        if len(notice_data.notice_title) < 5:
            return
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, ' div.news-one-content > p').text
        if "Дата завершения приема заявок:" in notice_deadline:
            notice_deadline = notice_deadline.split('Дата завершения приема заявок:')[1]
            notice_deadline = re.findall('\d+.\d+.\d{4}',notice_deadline)[0]
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
        elif 'Дата завершения приема предложений:' in notice_deadline:
            notice_deadline = notice_deadline.split('Дата завершения приема предложений')[1].strip()
            notice_deadline = re.findall('\d+.\d+.\d{4}',notice_deadline)[0]
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    except:
        pass
    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR,  'div.news-one-content > h4 > a').get_attribute("href")
    except:
        pass
    
    try:                       
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
        
        try:
            notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#app > div.container').get_attribute("outerHTML")                     
        except:
            pass
        
        try:
            lot_details_data = lot_details()
            lot_details_data.lot_number = 1

            lot_details_data.lot_title = page_details.find_element(By.XPATH, '//*[contains(text(),"Предмет:")]//parent::p[1]').text.split('Предмет:')[1].strip()
            lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)

            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
        except Exception as e:
            logging.info("Exception in lot_details: {}".format(type(e).__name__))
            pass

        try:
            dispatch_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Дата объявления:")]//parent::p[1]').text
            dispatch_date = re.findall('\d+.\d+.\d{4}',dispatch_date)[0]
            notice_data.dispatch_date = datetime.strptime(dispatch_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
        except Exception as e:
            logging.info("Exception in dispatch_date: {}".format(type(e).__name__))
            pass
    
        try:
            attachments_data = attachments()
            attachments_data.file_name = 'Tender Documents'

            attachments_data.external_url = page_details.find_element(By.CSS_SELECTOR, "#app > div.container > div > div.col-lg-8.col-xl-9.main-block > div.mt-1 > a").get_attribute("href")

            try:
                attachments_data.file_type = attachments_data.external_url.split('.')[-1].strip()
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
            if attachments_data.external_url != '':
                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
        except Exception as e:
            logging.info("Exception in attachments: {}".format(type(e).__name__)) 
            pass

    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url

    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    data_final = output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments)
page_details =fn.init_chrome_driver(arguments)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.saneg.com/tenders"] 
    for url in urls:
        fn.load_page(page_main, url, 60)
        logging.info('----------------------------------')
        logging.info(url)
            
        for page_no in range(2,20):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#app > div.container > div.news-list.tenders-list > div'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#app > div.container > div.news-list.tenders-list > div')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#app > div.container > div.news-list.tenders-list > div')))[records]
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#app > div.container > div.news-list.tenders-list > div'),page_check))
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
