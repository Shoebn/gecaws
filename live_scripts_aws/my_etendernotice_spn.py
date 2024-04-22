
from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "my_etendernotice_spn"
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
SCRIPT_NAME = "my_etendernotice_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    notice_data.script_name = 'my_etendernotice_spn'
    notice_data.main_language = 'EN'
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'MY'
    notice_data.performance_country.append(performance_country_data)
    notice_data.currency = 'MYR'
    notice_data.procurement_method = 2
    notice_data.notice_type = 4
    

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(2)").text
        notice_data.publish_date = datetime.strptime(publish_date,'%d-%m-%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(3)").text
        if 'noon' in notice_deadline:
            notice_deadline = notice_deadline.replace('noon','PM')
        notice_deadline = re.findall('\d+-\d+-\d+ at \d+:\d+ [apAP][mM]', notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline, '%d-%m-%Y at %I:%M %p').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    try:
        notice_no = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(5)").text
        notice_data.notice_no = notice_no.split('(')[1].split(')')[0]
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))

    try:
        notice_url_1 = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5) > a').get_attribute("href")  
        notice_url_2 = 'https://etendernotice.sarawak.gov.my/etender/public/public_tender_view.jsp?TenderId='
        notice_url_1 = notice_url_1.split('=')[1].split('%')[0]
        notice_data.notice_url = notice_url_2+notice_url_1
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url

    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'body > table > tbody').get_attribute("outerHTML")    
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')

    try:
        customer_details_data = customer_details()
        customer_details_data.org_country = 'MY'
        customer_details_data.org_language = 'EN'

        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text

        try:
            customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Office Address")]//following::td[2]').text  
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass

        try:
            org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Office Phone")]//following::td[2]').text  
            if len(org_phone)>5:
                customer_details_data.org_phone = org_phone
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass        

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass 

    try:
        procurement_method = page_details.find_element(By.CSS_SELECTOR, 'tr:nth-child(1) > td > table > tbody > tr:nth-child(3) > td:nth-child(3)').text  
        if 'Tender For Bumiputera Only' in procurement_method:
            notice_data.procurement_method = 0
        else:
            notice_data.procurement_method = 2
    except Exception as e:
        logging.info("Exception in procurement_method: {}".format(type(e).__name__))
        pass    

    notice_data.document_type_description = 'TENDER NOTICE'

    notice_data.local_title = page_details.find_element(By.CSS_SELECTOR, 'tr:nth-child(1) > td > table > tbody > tr:nth-child(5) > td:nth-child(3)').text   
    notice_data.notice_title = notice_data.local_title

    try:
        notice_contract_type = page_details.find_element(By.XPATH, '//*[contains(text(),"Registration Category")]//following::td[2]').text 
        if 'Work' in notice_contract_type or 'Electrical' in notice_contract_type or 'Mechanical' in notice_contract_type:
            notice_data.notice_contract_type = 'Works'
        elif 'Supply & Services' in notice_contract_type:
            notice_data.notice_contract_type = 'Service'
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass    

    try:
        notice_data.document_fee = page_details.find_element(By.XPATH, '//*[contains(text(),"Document Fee")]//following::td[2]').text
        notice_data.document_cost = float(notice_data.document_fee.split('RM')[1].strip())
    except Exception as e:
        logging.info("Exception in document_fee: {}".format(type(e).__name__))
        pass        
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) + str(notice_data.publish_date) +  str(notice_data.notice_url) 
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
    urls = ["https://etendernotice.sarawak.gov.my/etender/public/public_searchResult_new.jsp"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)

        try:
            for page_no in range(2,10):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'spacer > form > table > tbody > tr > td > table > tbody > tr:nth-child(3)'))).text  
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'spacer > form > table > tbody > tr > td > table > tbody > tr')))   
                length = len(rows)
                for records in range(1,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'spacer > form > table > tbody > tr > td > table > tbody > tr')))[records] 
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 10).until(EC.element_to_be_clickable((By.XPATH,f"(//a[contains(@class,'content')])[{page_no}]")))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 30).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'spacer > form > table > tbody > tr > td > table > tbody > tr:nth-child(3)'),page_check))
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
    
