from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "ru_gazprom_pp"
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
from selenium import webdriver
from gec_common import functions as fn
from deep_translator import GoogleTranslator

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "ru_gazprom_pp"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"

def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'ru_gazprom_pp'
    
    notice_data.main_language = 'RU'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'RU'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.procurement_method = 2
    
    notice_data.currency = 'RUB'
    
    notice_data.notice_type = 3
    
    notice_data.document_type_description = "Планируемые закупки"
    
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, ' div.purchase-number > a').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.purchase-desc').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    except:
        pass
    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.purchase-number > a').get_attribute("href")
    except:
        pass

    try:
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)

        try:
            notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#lot-list > div.article._purchases > div > div.purchase-info.tender-desktop').get_attribute("outerHTML")                     
        except:
            pass

        try:
            notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Описание:")]//following::div[1]').text
            notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
        except Exception as e:
            logging.info("Exception in local_description: {}".format(type(e).__name__))
            pass

        try:#29.02.2024
            publish_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Начало приема заинтересованности:")]//following::div[1]').text
            publish_date = re.findall('\d+.\d+.\d{4}',publish_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.publish_date)
        except Exception as e:
            logging.info("Exception in publish_date: {}".format(type(e).__name__))
            pass

        if notice_data.publish_date is not None and notice_data.publish_date < threshold:
            return

        try:
            notice_deadline = page_details.find_element(By.XPATH, '//*[contains(text(),"Окончание приема заинтересованности:")]//following::div[1]').text
            notice_deadline = re.findall('\d+.\d+.\d{4}',notice_deadline)[0]
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.notice_deadline)
        except Exception as e:
            logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
            pass

        try:              
            customer_details_data = customer_details()
            customer_details_data.org_country = 'RU'
            customer_details_data.org_language = 'RU'

            customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Заказчик:")]//following::div[1]').text

            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
        except Exception as e:
            logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
            pass

        try:
            notice_data.class_title_at_source = page_details.find_element(By.XPATH, '//*[contains(text(),"Категории закупки:")]//following::div[1]').text
            notice_data.category = notice_data.class_title_at_source
        except Exception as e:
            logging.info("Exception in class_title_at_source: {}".format(type(e).__name__))
            pass

        try:              
            for single_record in page_details.find_elements(By.CSS_SELECTOR, '#lot-list > div.article._purchases > div > div.purchase-info.tender-desktop > div > div.docs-list > div.docs-wrapper > div > div'):
                attachments_data = attachments()

                attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, "a").get_attribute('href')

                attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, "a").text

                try:
                    attachments_data.file_type = attachments_data.file_name.split('.')[-1].strip()
                except Exception as e:
                    logging.info("Exception in file_type: {}".format(type(e).__name__))
                    pass

                try:
                    file_size = single_record.find_element(By.CSS_SELECTOR, "div").text
                    attachments_data.file_size = GoogleTranslator(source='auto', target='en').translate(file_size)
                except Exception as e:
                    logging.info("Exception in file_size: {}".format(type(e).__name__))
                    pass

                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
        except Exception as e:
            logging.info("Exception in attachments: {}".format(type(e).__name__)) 
            pass
        
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) + str(notice_data.publish_date) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
options = webdriver.ChromeOptions()
options.add_extension("C:/Users/Administrator/home/Urban-Free-VPN-proxy-Unblocker---Best-VPN.crx")
page_main = webdriver.Chrome(options=options)
time.sleep(20)
page_details = webdriver.Chrome(options=options)
time.sleep(20)

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["http://zakupki.gazprom-neft.ru/tenderix/index.php?FILTER%5BSORT%5D=DATE_START_DESC&LIMIT=100"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url) 
        
        sub_url = page_main.find_element(By.CSS_SELECTOR, 'body > article > div.main > div.submenu._puchases > div > a:nth-child(3)').get_attribute("href")
        fn.load_page(page_main,sub_url,80)
        logging.info(sub_url)
            
        try:
            for page_no in range(2,5):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/article/div[2]/div[3]/form[1]/div/div[2]/div/div[1]/div/div'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/article/div[2]/div[3]/form[1]/div/div[2]/div/div[1]/div/div')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/article/div[2]/div[3]/form[1]/div/div[2]/div/div[1]/div/div')))[records]
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
                    time.sleep(5)
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/article/div[2]/div[3]/form[1]/div/div[2]/div/div[1]/div/div'),page_check))
                except Exception as e:
                    logging.info("Exception in next_page: {}".format(type(e).__name__))
                    logging.info("No next page")
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
