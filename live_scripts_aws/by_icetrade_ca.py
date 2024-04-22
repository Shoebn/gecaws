from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "by_icetrade_ca"
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
from selenium.webdriver.support.ui import Select

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "by_icetrade_ca"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    

    notice_data.script_name = 'by_icetrade_ca'
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'BY'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'BYR'
    notice_data.main_language = 'RU'
    notice_data.procurement_method = 2
    notice_data.notice_type = 7
    
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    try:
        org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
    except:
        pass
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text
        notice_data.publish_date = datetime.strptime(publish_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(1) a").get_attribute('href')
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        pass
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Краткое описание предмета закупки")]//following::td[1]').text
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
    except:
        pass

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = org_name
        try:
            customer_details_data.org_address = page_details.find_element(By.XPATH,'//*[contains(text(),"заказчика")]//following::td[1]').text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__)) 
            pass        
        try:
            customer_details_data.org_phone = page_details.find_element(By.XPATH,'//*[contains(text(),"заказчика")]//following::td[1]').text.split('каб.')[1]
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__)) 
            pass
        try:
            org_email = page_details.find_element(By.XPATH,'//*[contains(text(),"заказчика")]//following::td[1]').text
            customer_details_data.org_email = fn.get_email(org_email)
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__)) 
            pass
        
        customer_details_data.org_country = 'BY'
        customer_details_data.org_language = 'RU'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
        
    try:             
        for single_record in page_details.find_elements(By.XPATH,'//*[contains(text(),"Файлы для информации о результатах закупок:")]//following::tr/td/p/a'):
            attachments_data = attachments()
            attachments_data.file_name = single_record.text

            attachments_data.external_url = single_record.get_attribute('href')

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
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR,'#auctBlock > div').get_attribute('outerHTML')
    except:
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.notice_deadline) + str(notice_data.local_title)
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
options = webdriver.ChromeOptions()
options.add_extension("C:/Users/Administrator/home/Urban-Free-VPN-proxy-Unblocker---Best-VPN.crx")
page_details = webdriver.Chrome(options=options)
page_main = webdriver.Chrome(options=options)

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    for page in range(1,5):
        urls = ['https://icetrade.by/search/results?sort=num%3Adesc&onPage=100&p='+str(page)+''] 

        for url in urls:
            fn.load_page(page_main, url, 50)
            time.sleep(10)
            logging.info('----------------------------------')
            logging.info(url)

            try:
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#auctions-list > tbody > tr:nth-child(1)'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#auctions-list > tbody > tr')))
                length = len(rows)                                                                              
                for records in range(1,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#auctions-list > tbody > tr')))[records]
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
