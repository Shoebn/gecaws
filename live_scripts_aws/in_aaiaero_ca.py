from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "in_aaiaero_ca"
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

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "in_aaiaero_ca"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'in_aaiaero_ca'
    notice_data.main_language = 'EN'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'INR'
    notice_data.notice_type = 7
    notice_data.procurement_method = 2
    notice_data.notice_url =  url
    

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td.views-field.views-field-title').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    
    try: 
        publish_date = tender_html_element.find_element(By.XPATH, '(//*[contains(text(),"Date of Award")])['+str(num)+']//following::td[1]').get_attribute('innerHTML')
        publish_date = re.findall('\d+-\d+-\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d-%m-%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    try:
        single_record = tender_html_element.find_element(By.CSS_SELECTOR, 'td.views-field.views-field-field-department').text
        category1 = single_record
        category = category1.split('\n')[0].strip()
        notice_data.category = category
        cpv_codes_list = fn.CPV_mapping("assets/in_aaiaero_ca_cpv.csv",category)
        for each_cpv in cpv_codes_list:
            cpvs_data = cpvs()
            cpv_code1 = each_cpv
            cpv_code = re.findall('\d{8}',cpv_code1)[0]                
            cpvs_data.cpv_code = cpv_code
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)

    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass

    
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'IN'
        customer_details_data.org_language = 'EN'

        customer_details_data.org_name = "Airports Authority Of India"
        customer_details_data.org_parent_id = 1483743
        customer_details_data.org_phone = "91-11-24632950"
        customer_details_data.org_city = "New Delhi"
        customer_details_data.org_state  = "Uttar Pradesh"
        customer_details_data.org_address =  "Rajiv Gandhi Bhawan,Safdarjung Airport,New Delhi-110003"

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    except:
        pass

    try:
        notice_data.related_tender_id = page_main.find_element(By.XPATH, "(//*[contains(text(),'Contract Number')])["+str(num)+"]//following::td[1]").get_attribute('innerHTML')
    except Exception as e:
        logging.info("Exception in related_tender_id: {}".format(type(e).__name__)) 
        pass

    try:
        tender_contract_end_date = page_main.find_element(By.XPATH, "(//*[contains(text(),'Scheduled Completion of Supplies')])["+str(num)+"]//following::td[1]").get_attribute('innerHTML')
        tender_contract_end_date = re.findall('\d+-\d+-\d{4}',tender_contract_end_date)[0]
        notice_data.tender_contract_end_date = datetime.strptime(tender_contract_end_date,'%d-%m-%Y').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in tender_contract_end_date: {}".format(type(e).__name__)) 
        pass
    

    try:
        lot_details_data = lot_details()
        lot_details_data.lot_number = 1

        lot_details_data.lot_title = notice_data.local_title
        notice_data.is_lot_default = True
        lot_details_data.lot_title_english = lot_details_data.lot_title

        try:
            award_details_data = award_details()

            award_details_data.bidder_name = tender_html_element.find_element(By.XPATH, '(//*[contains(text(),"Name of Contractor")])['+str(num)+']//following::td[1]').get_attribute('innerHTML')

            try:
                grossawardvaluelc = tender_html_element.find_element(By.XPATH, '(//*[contains(text(),"Value of the Contract")])['+str(num)+']//following::td[1]').get_attribute('innerHTML')
                award_details_data.grossawardvaluelc = float(grossawardvaluelc)
            except Exception as e:
                logging.info("Exception in address: {}".format(type(e).__name__))
                pass

            try:  
                award_date1 = tender_html_element.find_element(By.XPATH, '(//*[contains(text(),"Date of Award")])['+str(num)+']//following::td[1]').get_attribute('innerHTML')
                award_date = re.findall('\d+-\d+-\d{4}',award_date1)[0]
                award_details_data.award_date = datetime.strptime(award_date,'%d-%m-%Y').strftime('%Y/%m/%d')
            except:
                pass

            award_details_data.award_details_cleanup()
            lot_details_data.award_details.append(award_details_data)
        except Exception as e:
            logging.info("Exception in award_details: {}".format(type(e).__name__)) 
            pass


        if lot_details_data.award_details !=[]:
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
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
    urls = ["https://www.aai.aero/en/tender/contract-award"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url) 
        try:
            for page_no in range(2,4):
                page_check = WebDriverWait(page_main, 80).until(EC.presence_of_element_located((By.XPATH,'//*[@id="block-system-main"]/div/div/div[2]/table/tbody/tr'))).text
                rows = WebDriverWait(page_main, 80).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="block-system-main"]/div/div/div[2]/table/tbody/tr')))
                length = len(rows)
                num = 1
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 80).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="block-system-main"]/div/div/div[2]/table/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    num +=1
                    if notice_count >= MAX_NOTICES:
                        break
    
                try:   
                    next_page = WebDriverWait(page_main, 80).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 80).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="block-system-main"]/div/div/div[2]/table/tbody/tr'),page_check))
                except Exception as e:
                    logging.info("Exception in next_page: {}".format(type(e).__name__))
                    logging.info("No next page")
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
    output_json_file.copyFinalJSONToServer(output_json_folder)
