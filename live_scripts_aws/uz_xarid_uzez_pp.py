from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "uz_xarid_uzez_pp"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from selenium import webdriver
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn
from deep_translator import GoogleTranslator

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
tender_no = 0
SCRIPT_NAME = "uz_xarid_uzez_pp"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    global tender_no
    notice_data = tender()
    
    notice_data.script_name = 'uz_xarid_uzez_pp'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'UZ'
    notice_data.performance_country.append(performance_country_data)
   
    notice_data.currency = 'UZS'
    
    notice_data.main_language = 'UZ'
    
    notice_data.notice_type = 3
    
    notice_data.procurement_method = 2
    
    notice_data.notice_url = url 
            
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.lot-item__top.mb-0 > div.row.mb-0 > div > div:nth-child(2)').text.split('Reja-jadvalning nomi:')[1].strip()
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div.lot-item__top.mb-0 > div.row.mb-1 > div:nth-child(1) > div').text.split(':')[1].strip()
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
        
    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    except:
        pass

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div.lot-item__top.mb-0 > div.row.mb-1 > div:nth-child(2) > div").text
        publish_date = re.findall('\d+.\d+.\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:
        org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div.lot-item__top.mb-0 > div.row.mb-0 > div > div:nth-child(1)').text.split('-')[1].strip()
    except:
        pass

    try:
        org_address = tender_html_element.find_element(By.CSS_SELECTOR, 'div.lot-item__top.mb-0 > div.row.mb-0 > div > div.lot__category.mb-0.text-right').text
    except:
        pass
        
    try:
        notice_data.tender_custom_tag_company_id = tender_html_element.find_element(By.CSS_SELECTOR, 'div.lot-item__top.mb-0 > div.row.mb-0 > div > div:nth-child(1)').text.split(':')[1].split('-')[0].strip()
    except:
        pass

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.lot-item__bottom > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url

    try:              
        customer_details_data = customer_details() 
        customer_details_data.org_name = org_name
        try:
            customer_details_data.org_address = org_address
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass 
        customer_details_data.org_country = 'UZ'
        customer_details_data.org_language = 'UZ'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try:
        lot_number = 1
        class_codes_at_source = ''
        class_title_at_source = ''
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.lot__products__item'):
            lot_details_data = lot_details()
            lot_details_data.lot_number = lot_number
    
            try:
                lot_actual_no = single_record.find_element(By.CSS_SELECTOR, 'h5').text.split('\n')[1].strip()
                lot_details_data.lot_actual_no = re.findall("^\d{2}.+\d{5}",lot_actual_no)[0]
            except:
                pass
    
            lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, 'h5').text.split(lot_details_data.lot_actual_no)[1].strip()
            lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
            
            try:
                lot_quantity = single_record.find_element(By.CSS_SELECTOR, 'div.lot__products__item__table-wrap > table > tbody > tr  > td:nth-child(1)').text 
                lot_quantity = re.sub("[^\d+]",'',lot_quantity)
                lot_details_data.lot_quantity = float(lot_quantity)
            except Exception as e:
                logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                pass
    
            try:
                lot_details_data.lot_quantity_uom = single_record.find_element(By.CSS_SELECTOR, 'div.lot__products__item__table-wrap > table >tbody > tr  > td:nth-child(5)').text 
            except Exception as e:
                logging.info("Exception in lot_quantity_uom: {}".format(type(e).__name__))
                pass
    
            try:
                lot_details_data.lot_class_codes_at_source = single_record.find_element(By.CSS_SELECTOR, 'div.lot__products__item__footer > p:nth-child(1)').text.split(':')[1].split('-')[0].strip()
            except Exception as e:
                logging.info("Exception in lot_class_codes_at_source: {}".format(type(e).__name__))
                pass
    
            try:
                lot_details_data.lot_description = single_record.find_element(By.CSS_SELECTOR, 'div.lot__products__item__footer > p:nth-child(2)').text.split(':')[1].split('-')[0].strip()
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass
    
            try:
                class_codes_at_source += single_record.find_element(By.CSS_SELECTOR, 'div.lot__products__item__footer > p:nth-child(1)').text.split(':')[1].split('-')[0].strip()
                class_codes_at_source += ','
                notice_data.class_codes_at_source = class_codes_at_source.rstrip(',')
            except Exception as e:
                logging.info("Exception in class_codes_at_source: {}".format(type(e).__name__))
                pass
    
            try:
                class_title_at_source += single_record.find_element(By.CSS_SELECTOR, 'div.lot__products__item__footer > p:nth-child(1)').text.split('-')[1].strip()
                class_title_at_source += ','
                notice_data.class_title_at_source = class_title_at_source.rstrip(',')
            except Exception as e:
                logging.info("Exception in class_title_at_source: {}".format(type(e).__name__))
                pass
                
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
            lot_number += 1
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass   

    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'body > app-root > div.site-zoom-0 > app-common-plangraph-details > main > section > div').get_attribute('outerHTML')
    except:
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) + str(notice_data.local_title)
    logging.info(notice_data.identifier)
    duplicate_check_data = fn.duplicate_check_data_from_previous_scraping(SCRIPT_NAME,MAX_NOTICES_DUPLICATE,notice_data.identifier,previous_scraping_log_check)
    NOTICE_DUPLICATE_COUNT = duplicate_check_data[1]
    if duplicate_check_data[0] == False:
        return
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    tender_no += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
# page_main = fn.init_chrome_driver(arguments) 
# page_details = fn.init_chrome_driver(arguments) 

options = webdriver.ChromeOptions()
options.add_extension("C:/Users/Administrator/home/Urban-Free-VPN-proxy-Unblocker---Best-VPN.crx")
page_main = webdriver.Chrome(options=options)
time.sleep(30)
page_main.maximize_window()

options = webdriver.ChromeOptions()
options.add_extension("C:/Users/Administrator/home/Urban-Free-VPN-proxy-Unblocker---Best-VPN.crx")
page_details = webdriver.Chrome(options=options)
time.sleep(30)

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://xarid.uzex.uz/trade/plangraph-list"] 
    for url in urls:
        fn.load_page(page_main, url, 80)
        logging.info('----------------------------------')
        logging.info(url)

        try:
            rows = WebDriverWait(page_main, 120).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.lot-list > div')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 200).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.lot-list > div')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
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
