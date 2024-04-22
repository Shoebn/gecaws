from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "tz_nestgo_ca"
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
SCRIPT_NAME = "tz_nestgo_ca"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'tz_nestgo_ca'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'TZ'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'TZS'
    notice_data.main_language = 'EN'
    notice_data.procurement_method = 2
    notice_data.notice_type = 7

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(1) > div > h2').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div.sm\:flex.sm\:space-x-4 div:nth-child(3) > div:nth-child(2)').text 
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div.sm\:flex.sm\:space-x-4 div:nth-child(2) > div:nth-child(2)").text
        notice_data.publish_date = datetime.strptime(publish_date,'%d %b %Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    notice_data.notice_url = 'https://nest.go.tz/'
    
    try:
        notice_data.notice_text += tender_html_element.find_element(By.CSS_SELECTOR, 'app-advanced-tender-search-tender-item > div > div').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div.mt-2 > div').text 
        customer_details_data.org_country = 'TZ'
        customer_details_data.org_language = 'EN'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass   

    try:              
        lot_details_data = lot_details()
        lot_details_data.lot_number = 1
        lot_details_data.lot_title = notice_data.local_title
        notice_data.is_lot_default = True
        try:
            award_details_data = award_details()

            award_details_data.bidder_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div.sm\:flex.sm\:space-x-4 div:nth-child(1) > div:nth-child(2)').text  

            award_date = tender_html_element.find_element(By.CSS_SELECTOR, 'div.sm\:flex.sm\:space-x-4 div:nth-child(2) > div:nth-child(2)').text 
            award_details_data.award_date = datetime.strptime(award_date,'%d %b %Y').strftime('%Y/%m/%d') 
            
            grossawardvaluelc = tender_html_element.find_element(By.CSS_SELECTOR, 'div.font-extrabold.mt-\[10px\].sm\:mt-0').text 
            grossawardvaluelc = grossawardvaluelc.split('TZS')[1]
            award_details_data.grossawardvaluelc = float(grossawardvaluelc.replace(',',''))            

            award_details_data.award_details_cleanup()
            lot_details_data.award_details.append(award_details_data)
        except Exception as e:
            logging.info("Exception in award_details: {}".format(type(e).__name__))
            pass

        lot_details_data.lot_details_cleanup()
        notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
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
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://nest.go.tz/"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)

        try:
            tender_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'div.hidden.md\:flex.leading-3 > div:nth-child(2)'))).click()  
            time.sleep(5)
        except:
            pass    

        awarded_contracts_click = WebDriverWait(page_main, 20).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#mat-menu-panel-3 > div > a:nth-child(8)'))).click()  
        time.sleep(5)
        logging.info("awarded_contracts_click")

        try:
            for page_no in range(1,35):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="tender-list-container"]/div[3]/app-advanced-tender-search-tender-item/div/div'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="tender-list-container"]/div[3]/app-advanced-tender-search-tender-item/div/div')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="tender-list-container"]/div[3]/app-advanced-tender-search-tender-item/div/div')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
                    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="tender_search_container"]/div/div[2]/div/parallax-container/div[2]/div[2]/div/app-advanced-tender-search/div[2]/web-page-paginator/div/div[2]/div/button[2]')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="tender-list-container"]/div[3]/app-advanced-tender-search-tender-item/div/div'),page_check))
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
    output_json_file.copyFinalJSONToServer(output_json_folder)
