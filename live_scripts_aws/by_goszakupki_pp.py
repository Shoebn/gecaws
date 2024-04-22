from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "by_goszakupki_pp"
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
SCRIPT_NAME = "by_goszakupki_pp"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    global tender_no
    notice_data = tender()
    
    notice_data.script_name = 'by_goszakupki_pp'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'BY'
    notice_data.performance_country.append(performance_country_data)
   
    notice_data.currency = 'BYN'
    
    notice_data.main_language = 'RU'
    
    notice_data.notice_type = 3
    
    notice_data.procurement_method = 2
    
    notice_data.notice_url = url 
            
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
        
    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    except:
        pass
    
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(3)").text
        publish_date = re.findall('\d+.\d+.\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text


    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url

    try:              
        customer_details_data = customer_details() 
        customer_details_data.org_name = org_name
        try:
            customer_details_data.org_address = page_details.find_element(By.XPATH, '(//*[contains(text(),"Местонахождение")]//following::td[1])[1]').text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass 
        customer_details_data.org_country = 'BY'
        customer_details_data.org_language = 'RU'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try:
        notice_no = page_details.find_element(By.CSS_SELECTOR, '#w2 > table > tbody > tr:nth-child(1) > td:nth-child(1)').text
        local_title = page_details.find_element(By.CSS_SELECTOR, '#w2 > table > tbody > tr:nth-child(1) > td:nth-child(2)').text
        notice_data.local_title = notice_no + '' + local_title
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:
        local_description = ''
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#w2 > table > tbody > tr'):
            notice_number = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
            title = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
            description = notice_number + '' + title
            local_description += description + ','
        notice_data.local_description = local_description.rstrip(',')
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
    except Exception as e:
        logging.info("Exception in description: {}".format(type(e).__name__))
        pass

    try:
        lot_number = 1
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#w2 > table > tbody > tr'):
            lot_details_data = lot_details()
            lot_details_data.lot_number = lot_number
    
            try:
                lot_details_data.lot_actual_number = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
            except:
                pass
    
            lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
            lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
    
            try:
                lot_quantity = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text 
                lot_quantity = re.sub("[^\d+]",'',lot_quantity)
                lot_details_data.lot_quantity = float(lot_quantity)
            except Exception as e:
                logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                pass
    
            try:
                grossbudget_lc = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(6)').text
                if 'BYN: 0' in grossbudget_lc:
                    lot_grossbudget_lc = grossbudget_lc.split(' (оплата со счетов заказчика)')[1].split('BYN:')[1].strip()
                    lot_grossbudget_lc = re.sub("[^\d\.]", "", lot_grossbudget_lc) 
                    lot_details_data.lot_grossbudget_lc = float(lot_grossbudget_lc) 
                elif '(оплата со счетов заказчика)' in grossbudget_lc:
                    lot_grossbudget_lc = grossbudget_lc.split('(оплата со счетов казначейства)')[1].split('BYN:')[1].strip()
                    lot_grossbudget_lc = re.sub("[^\d\.]", "", lot_grossbudget_lc) 
                    lot_details_data.lot_grossbudget_lc = float(lot_grossbudget_lc) 
                else:
                    lot_grossbudget_lc = grossbudget_lc.split('BYN:')[1].strip()
                    lot_grossbudget_lc = re.sub("[^\d\.]", "", lot_grossbudget_lc) 
                    lot_details_data.lot_grossbudget_lc = float(lot_grossbudget_lc) 
            except Exception as e:
                logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
                pass
    
                
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
            lot_number += 1
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass   

    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'body > div > div').get_attribute('outerHTML')
    except:
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) + str(notice_data.local_title)
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    tender_no += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
options = webdriver.ChromeOptions()
options.add_extension("C:/Users/Administrator/home/Urban-Free-VPN-proxy-Unblocker---Best-VPN.crx")
page_main = webdriver.Chrome(options=options)
time.sleep(30)
page_main.maximize_window()

options = webdriver.ChromeOptions()
options.add_extension("C:/Users/Administrator/home/Urban-Free-VPN-proxy-Unblocker---Best-VPN.crx")
page_details = webdriver.Chrome(options=options)
time.sleep(20)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://goszakupki.by/purchases/all"] 
    for url in urls:
        fn.load_page(page_main, url, 80)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,60):
            page_check = WebDriverWait(page_main, 120).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#w0 > table > tbody > tr'))).text
            rows = WebDriverWait(page_main, 120).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#w0 > table > tbody > tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 200).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#w0 > table > tbody > tr')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break
    
            try:   
                next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                page_main.execute_script("arguments[0].click();",next_page)
                logging.info("Next page")
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#w0 > table > tbody > tr'),page_check))
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
