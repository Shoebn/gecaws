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
from gec_common import functions as fn

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "ae_adgpg_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'AE'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'AED'
    
    notice_data.main_language = 'EN'

    notice_data.script_name = 'ae_adgpg_spn'
    
    notice_data.notice_type = 4
    notice_data.procurment_method = 2
    
    notice_data.document_type_description = 'Public Tenders'
    
    try:
        notice_data.notice_url = url
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__)) 
        pass   

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR,'h4').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in notice_title: {}".format(type(e).__name__)) 
        pass
    
    clk= tender_html_element.find_element(By.CSS_SELECTOR,'span.headIcon.icon-arrow-small-right')
    page_main.execute_script("arguments[0].click();",clk)
    time.sleep(5) 
    text1 = tender_html_element.find_element(By.CSS_SELECTOR,'div.ex-tender-body').get_attribute('outerHTML')
    text2 = tender_html_element.find_element(By.CSS_SELECTOR,'div.ex-tender-body').text
    
    try:
        publish_date =  tender_html_element.find_element(By.XPATH,"//*[contains(text(),'BIDDING OPENS ON:')]//following::p[1]").get_attribute('innerHTML')
        notice_data.publish_date = datetime.strptime(publish_date, '%d %B %Y').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__)) 
        pass
    logging.info(notice_data.publish_date)
    
    try:
        notice_deadline = re.findall(r'DUE ON:\n(.+?)\n',text2)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline, '%d %B %Y').strftime('%Y/%m/%d %H:%M:%S')
    except:
        pass
    
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    try:    
        clk= tender_html_element.find_element(By.CSS_SELECTOR,'span.headIcon.icon-arrow-small-right')
        page_main.execute_script("arguments[0].click();",clk)
        clk= tender_html_element.find_element(By.CSS_SELECTOR,'span.headIcon.icon-arrow-small-right')
        page_main.execute_script("arguments[0].click();",clk)
        time.sleep(5) 
    except:
        pass
    
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR,' p.doc-number.small-text.font-weight-boldest').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__)) 
        pass  

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR,'span.mr-2.mb-2').text
        customer_details_data.org_country = 'AE'
        customer_details_data.org_language = 'EN'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    
    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
        notice_data.notice_text += text1
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__)) 
        pass
   
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.notice_deadline) + str(notice_data.local_title)
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

    urls = ["https://adgpg.gov.ae/en/For-Suppliers/Public-Tenders"]

    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        clk=page_main.find_element(By.XPATH,"/html/body/div[3]/main/div/div[3]/div/div[2]/div[8]/div/div/a")
        page_main.execute_script("arguments[0].click();",clk)
        clk=page_main.find_element(By.XPATH,"/html/body/div[3]/main/div/div[3]/div/div[2]/div[8]/div/div/a")
        page_main.execute_script("arguments[0].click();",clk)
        time.sleep(5)
        try:
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR,' #content > div.container > div > div.col-lg-9.component-tender-wrap > div.ex-tenders--listing > div ')))
            length = len(rows) 
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR,'#content > div.container > div > div.col-lg-9.component-tender-wrap > div.ex-tenders--listing > div ')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break

                if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                    logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                    break
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
            if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                break
        except:
            logging.info("No new record")
            pass 

    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)