from gec_common.gecclass import *
import logging
import re
import jsons
import os
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
lot_no = 2
SCRIPT_NAME = "om_squedu_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"

def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    global lot_no
    notice_data = tender()
    
    notice_data.script_name = 'om_squedu_spn'
    
    notice_data.main_language = 'EN'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'OM'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.procurement_method = 2
  
    notice_data.currency = 'OMR'
        
    notice_data.notice_type = 4
    
    notice_data.notice_url = url
    
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td.sorting_1').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, ' tr > td:nth-child(2)').text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, " tr > td:nth-child(3)").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass 

    try:
        notice_data.notice_text += tender_html_element.get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__)) 
        pass
    
    try:
        notice_data.category = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(4)').text
        cpv_codes = fn.CPV_mapping("assets/om_squedu_spn_category.csv",notice_data.category)
        for cpv_code in cpv_codes:
            cpvs_data = cpvs()
            cpvs_data.cpv_code = cpv_code
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in category: {}".format(type(e).__name__))
        pass
    
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'OM'
        customer_details_data.org_language = 'EN'
        customer_details_data.org_name =  'SULTAN QABOOS UNIVERSITY'
        customer_details_data.org_parent_id = 7524044
        customer_details_data.org_address = 'Sultan Qaboos University Procurement Department P.O. Box: 49, Postal Code: 123 Al Khoud Sultanate of Oman' 
        customer_details_data.org_phone =  '+ 968 2414 5271 / 2414 5250' 
        customer_details_data.org_fax = '+ 968 2441 3178' 
        customer_details_data.org_email = 'mailto:procure@squ.edu.om' 
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass 

    try:         
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, 'td:nth-child(5) > a'):
            attachments_data = attachments()

            attachments_data.file_name = single_record.text

            attachments_data.external_url = single_record.get_attribute("href")

            try:
                attachments_data.file_type = attachments_data.file_name.split(' ')[-1].strip()
            except:
                pass

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments_1: {}".format(type(e).__name__)) 
        pass
    
    try:
        lot_data = page_main.find_element(By.CSS_SELECTOR, '#myDataTable > tbody > tr:nth-child('+str(lot_no)+') > td > div > table')
        lot_number = 1
        local_title = ''
        for title in lot_data.find_elements(By.CSS_SELECTOR, '#myDataTable > tbody > tr.details > td > div > table > tbody > tr'):

            try:
                local_title += title.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
                local_title += ' '
                local_title += title.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
                local_title += ','
            except Exception as e:
                logging.info("Exception in local_title: {}".format(type(e).__name__))
                pass

            try:
                lot_details_data = lot_details()
                lot_details_data.lot_number = lot_number
                
                lot_details_data.lot_title = title.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
                lot_details_data.lot_title_english = lot_details_data.lot_title

                try:
                    lot_details_data.lot_actual_number = title.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
                except Exception as e:
                    logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                    pass

                try:
                    lot_details_data.lot_quantity  = float(title.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text)
                except Exception as e:
                    logging.info("Exception in lot_quantity : {}".format(type(e).__name__))
                    pass

                try:
                    lot_details_data.lot_description  = title.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
                    lot_details_data.lot_description_english = lot_details_data.lot_description
                except Exception as e:
                    logging.info("Exception in lot_description  : {}".format(type(e).__name__))
                    pass

                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
                lot_number += 1
            except Exception as e:
                logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
                pass

        notice_data.local_title = local_title.rstrip(',')
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    if len(notice_data.local_title) < 5:
        return
                     
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title) 
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    lot_no += 2
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver_head(arguments)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://tenders.squ.edu.om/AllCategs"] 
    for url in urls:
        fn.load_page(page_main, url, 80)
        logging.info('----------------------------------')
        logging.info(url)
                
        Requisition_Number = WebDriverWait(page_main, 80).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#ref_no')))
        page_main.execute_script("arguments[0].click();",Requisition_Number)
        time.sleep(10)
        
        try:
            for page_no in range(1,4):
                page_check = WebDriverWait(page_main, 80).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#myDataTable > tbody > tr'))).text
                rows = WebDriverWait(page_main, 80).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#myDataTable > tbody > tr')))
                length = len(rows)
                num = 1
                num2 = 1
                for i in range(1, length+1):
                    check = page_main.find_element(By.XPATH, '(//*[@class="sorting_1"]//img[@alt="Expand"])['+str(num)+']').get_attribute('alt')
                    if "Expand" in check:
                        pul_Expand = WebDriverWait(page_main, 80).until(EC.element_to_be_clickable((By.XPATH, '(//*[@class="sorting_1"]//img[@alt="Expand"])['+str(num)+']'))).click()
                        time.sleep(5)
                        pul_Expand_check = '(//*[@class="sorting_1"]//img[@alt="Expand"])['+str(num)+']'
                        num += 1
                    try:
                        check_Collapse = page_main.find_element(By.XPATH, '(//*[@class="sorting_1"]//img[@alt="Collapse"])['+str(num2)+']').get_attribute('alt')
                        check_Collapse_text = '(//*[@class="sorting_1"]//img[@alt="Collapse"])['+str(num2)+']'
                        num2 += 1
                        num = 1
                    except Exception as e:
                        logging.info("Exception in check_Collapse: {}".format(type(e).__name__))
                        num2 += 1
                num += 1
                time.sleep(5)
                for records in range(0,length*2,2):
                    tender_html_element = WebDriverWait(page_main, 80).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#myDataTable > tbody > tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break

                try:   
                    next_page = WebDriverWait(page_main, 60).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#myDataTable_next')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 60).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#myDataTable > tbody > tr'),page_check))
                    lot_no = 2
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
