from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "lv_eis_pp"
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
from selenium.webdriver.support.ui import Select

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "lv_eis_pp"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"

def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'lv_eis_pp'
    
    notice_data.main_language = 'LV'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'LV'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.procurement_method = 2
  
    notice_data.currency = 'LVL'
        
    notice_data.notice_type = 3
    
    notice_data.notice_url = url
    
    notice_data.class_at_source = 'CPV'
    
    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
            
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
        notice_data.notice_title = notice_data.local_title
        if len(notice_data.local_title) < 5:
            return
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in org_name: {}".format(type(e).__name__))
        pass
    
    try:  
        notice_data.contract_type_actual = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
        if 'Pakalpojums' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Service'
        elif 'Piegāde' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Supply'
        elif 'Būvdarbi' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Works'
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
        
    try:
        cpv_code = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(6)').text
        cpv_code_title = re.findall('\d{8}-\d+',cpv_code)[0]
        title_at_source = cpv_code.split(cpv_code_title)
        class_title_at_source = ''
        for cpv_title in title_at_source[1:]:

            class_title_at_source += cpv_title.strip()
            class_title_at_source += ','
        notice_data.class_title_at_source = class_title_at_source.rstrip(',')
    except Exception as e:
        logging.info("Exception in class_title_at_source: {}".format(type(e).__name__)) 
        pass

    try:
        cpv_code = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(6)').text
        class_codes_at_source = ''
        cpv_at_source = ''
        cpv_regex = re.compile(r'\d{8}')
        cpv_code_list = cpv_regex.findall(cpv_code)
        for cpv in cpv_code_list:
            cpvs_data = cpvs()

            class_codes_at_source += cpv
            class_codes_at_source += ','

            cpv_at_source += cpv
            cpv_at_source += ','

            cpvs_data.cpv_code = cpv
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)

        notice_data.class_codes_at_source = class_codes_at_source.rstrip(',')

        notice_data.cpv_at_source = cpv_at_source.rstrip(',')       
    except Exception as e:
        logging.info("Exception in cpv_code: {}".format(type(e).__name__)) 
        pass
        
    try:
        notice_data.notice_text += tender_html_element.get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__)) 
        pass
    
    page_detail_click = WebDriverWait(tender_html_element, 60).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'td:nth-child(8) > a')))
    page_main.execute_script("arguments[0].click();",page_detail_click)
    time.sleep(5)
    
    WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#uxProcurementPlanMaintainForm > div.form-horizontal.form-col-padding')))
    
    try:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, '#uxProcurementPlanMaintainForm > div.form-horizontal.form-col-padding').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__)) 
        pass
    
    try:
        publish_date = page_main.find_element(By.XPATH, '//*[contains(text(),"Ziņu aktualizācijas datums:")]//following::div[1]').text
        publish_date = re.findall('\d+.\d+.\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
    
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'LV'
        customer_details_data.org_language = 'LV'
        customer_details_data.org_name =  org_name
        
        try:
            customer_details_data.org_website = page_main.find_element(By.CSS_SELECTOR, '//*[contains(text(),"Saite uz pircēja profilu vai sasaiste ar iepirkumu:")]//following::div[1]/span/a').get_attribute("href") 
        except:
            pass
        
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass 
    
    
    page_detail_back = WebDriverWait(page_main, 60).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="modal-container"]/div[2]/div/div[1]/button')))
    page_main.execute_script("arguments[0].click();",page_detail_back)
    time.sleep(5)
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title) 
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
    urls = ["https://www.eis.gov.lv/EKEIS/ProcurementPlan"] 
    for url in urls:
        fn.load_page(page_main, url, 80)
        logging.info('----------------------------------')
        logging.info(url)
         
        page_main.find_element(By.XPATH,'//*[@id="Year"]').clear()
        time.sleep(2)
        
        current_year = th.year
        page_main.find_element(By.XPATH,'//*[@id="Year"]').send_keys(str(current_year))
        time.sleep(3)
        
        clicks = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#select2-chosen-10'))).click()
        time.sleep(2)
        
        slect_month = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="select2-results-10"]/li[1]'))).click()
        time.sleep(3)
        
        search = WebDriverWait(page_main, 60).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="uxProcurementPlanSearchParameters"]/div[15]/button')))
        page_main.execute_script("arguments[0].click();",search)
        time.sleep(5)
        
        try:
            for page_no in range(1,20):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#ResultsRepeater > div.repeater-viewport > div.repeater-canvas > div > div > table > tbody > tr'))).text
                rows = WebDriverWait(page_main, 50).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#ResultsRepeater > div.repeater-viewport > div.repeater-canvas > div > div > table > tbody > tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 50).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#ResultsRepeater > div.repeater-viewport > div.repeater-canvas > div > div > table > tbody > tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break

                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="Resultsfooter"]/div[2]/div/button[2]')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 60).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#ResultsRepeater > div.repeater-viewport > div.repeater-canvas > div > div > table > tbody > tr'),page_check))
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
