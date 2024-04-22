from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "zw_portalpraz_spn"
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
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "zw_portalpraz_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)

output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'zw_portalpraz_spn'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'ZW'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.main_language = 'EN'

    notice_data.procurement_method = 2

    notice_data.notice_type = 4
    
    try:
        notice_data.notice_no = WebDriverWait(tender_html_element, 100).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'td:nth-child(2)'))).text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass


    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(6)').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass


    try:  
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(7)").text
        notice_deadline = re.findall('\d{4}-\d+-\d+ \d+:\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%Y-%m-%d %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
        return

    
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
    
        customer_details_data.org_country = 'ZW'
        customer_details_data.org_language = 'EN'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(10) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.container.container--fluid').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    try:
        notice_contract_type = page_details.find_element(By.XPATH, '//*[contains(text(),"Procurement Section")]//following::td[1]').text
        if 'GOODS' in notice_contract_type:
            notice_data.notice_contract_type = "Supply"
        elif 'SERVICES' in notice_contract_type:
            notice_data.notice_contract_type = "Service"
        elif 'CONSTRUCTION' in notice_contract_type:
            notice_data.notice_contract_type = "Works"
        notice_data.contract_type_actual = notice_contract_type
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    lot_availibility_check = page_details.find_element(By.XPATH, '//*[@id="app"]/div/main/div/div/div[2]/div[2]/div/div/div/div[2]/div[2]/div/div[2]/div/div[1]/div/div/div/div/table/tbody/tr/td[1]').text
    if 'No category specified' in lot_availibility_check:
        pass

    else:
        lot_number = 1
        for single_record in page_details.find_elements(By.XPATH, '//*[@id="app"]/div/main/div/div/div[2]/div[2]/div/div/div/div[2]/div[2]/div/div[2]/div/div[1]/div/div/div/div/table/tbody/tr'):
            lot_details_data = lot_details()

            lot_details_data.lot_number = lot_number

            lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
            
            lot_details_data.lot_title_english = lot_details_data.lot_title 
            
            lot_details_data.contract_type = notice_data.notice_contract_type
            lot_details_data.lot_contract_type_actual = notice_contract_type

            try:
                lot_details_data.lot_actual_number = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass
            lot_number += 1
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
            
    
    try:
        Notice_Fees_clk = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.XPATH,"//*[contains(text(),'Notice Fees')]")))
        page_details.execute_script("arguments[0].click();",Notice_Fees_clk)
    except:
        pass
    
    try:
        currency = page_details.find_element(By.XPATH, '//*[contains(text(),"BIDBOND")]//following::td[1]').get_attribute('outerHTML')
        if 'USD' in currency:
            notice_data.currency = 'USD'
        else:
            notice_data.currency = 'ZWL'
    except Exception as e:
        notice_data.currency = 'ZWL'
        logging.info("Exception in currency: {}".format(type(e).__name__))
        pass


    try:
        earnest_money_deposit = page_details.find_element(By.XPATH, '//*[contains(text(),"BIDBOND")]//following::td[1]').get_attribute('outerHTML')
        notice_data.earnest_money_deposit = re.findall("\d+",earnest_money_deposit)[0]
    except Exception as e:
        logging.info("Exception in earnest_money_deposit: {}".format(type(e).__name__))
        pass
    

    
    try:
        document_fee = page_details.find_element(By.XPATH, '//*[contains(text(),"ESTABLISHMENT FEE")]//following::td[1]').get_attribute('outerHTML')
        notice_data.document_fee = re.findall("\d+",document_fee)[0]
    except Exception as e:
        logging.info("Exception in document_fee: {}".format(type(e).__name__))
        pass

#
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
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
    urls = ["https://portal.praz.org.zw/tenders"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        time.sleep(20)
        for page_no in range(1,10):
            page_check = WebDriverWait(page_main, 100).until(EC.presence_of_element_located((By.XPATH,'//*[@id="app"]/div[1]/main/div/div/div/div[2]/div/div[2]/div/div[3]/div[2]/div/div[1]/table/tbody/tr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="app"]/div[1]/main/div/div/div/div[2]/div/div[2]/div/div[3]/div[2]/div/div[1]/table/tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 100).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="app"]/div[1]/main/div/div/div/div[2]/div/div[2]/div/div[3]/div[2]/div/div[1]/table/tbody/tr')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break

                if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
                    break
                    
                if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                    logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                    break
    
            if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
                break

            try:   
                next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="app"]/div/main/div/div/div/div[2]/div/div[2]/div/div[3]/div[2]/div/div[2]/div[4]/button')))
                page_main.execute_script("arguments[0].click();",next_page)
                logging.info("Next page")
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="app"]/div[1]/main/div/div/div/div[2]/div/div[2]/div/div[3]/div[2]/div/div[1]/table/tbody/tr'),page_check))
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
