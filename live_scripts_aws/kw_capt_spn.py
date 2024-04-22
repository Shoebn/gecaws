
from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "kw_capt_spn"
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
SCRIPT_NAME = "kw_capt_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'kw_capt_spn'
    notice_data.main_language = 'AR'
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'KW'
    notice_data.performance_country.append(performance_country_data)
    notice_data.currency = 'KWD'
    notice_data.procurement_method = 2
    notice_data.notice_type = 4


    notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div > div > div:nth-child(2) > p:nth-child(2)').text
    notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)       
        
    notice_data.notice_text += tender_html_element.get_attribute('outerHTML') 
    notice_data.notice_url = 'https://capt.gov.kw/en/tenders/opening-tenders/'  
    
    try:
        more_click = WebDriverWait(tender_html_element, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"div > div > div:nth-child(3) > input")))
        page_main.execute_script("arguments[0].click();",more_click)
        logging.info("more_click")
        time.sleep(5)
        notice_data.notice_text += tender_html_element_2.get_attribute('outerHTML') 
    except Exception as e:
        logging.info("Exception in more_click: {}".format(type(e).__name__))
        logging.info("more_click")

    notice_data.notice_no = tender_html_element_2.find_element(By.CSS_SELECTOR, 'div:nth-child(2) > div:nth-child(1) > div:nth-child(1) > ul:nth-child(1) > li:nth-child(2)').text 
    
    try:
        publish_date = tender_html_element_2.find_element(By.CSS_SELECTOR, 'div:nth-child(2) > div:nth-child(1) > div:nth-child(1) > ul:nth-child(4) > li:nth-child(2)').text 
        notice_data.publish_date = datetime.strptime(publish_date,'%b. %d, %Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass          

    try:
        notice_deadline = tender_html_element_2.find_element(By.CSS_SELECTOR, 'div:nth-child(2) > div:nth-child(1) > div:nth-child(1) > ul:nth-child(5) > li:nth-child(2)').text 
        try:
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%b. %d, %Y').strftime('%Y/%m/%d %H:%M:%S')
        except:
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%B %d, %Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass   
    
    try:
        est_amount = tender_html_element_2.find_element(By.CSS_SELECTOR, 'div:nth-child(2) > div:nth-child(1) > div:nth-child(2) > ul:nth-child(4) > li:nth-child(2)').text  
        notice_data.est_amount = float(est_amount.split('KD')[0].strip())
        notice_data.grossbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass    

    try:
        pre_bid_meeting_date = tender_html_element_2.find_element(By.CSS_SELECTOR, 'div:nth-child(2) > div:nth-child(1) > div:nth-child(1) > ul:nth-child(6) > li:nth-child(2)').text 
        if len(pre_bid_meeting_date)>4:
            notice_data.pre_bid_meeting_date = datetime.strptime(pre_bid_meeting_date,'%b. %d, %Y').strftime('%Y/%m/%d')
            logging.info(notice_data.pre_bid_meeting_date)
    except Exception as e:
        logging.info("Exception in pre_bid_meeting_date: {}".format(type(e).__name__))
        pass  
    
    try:
        Insurance_Items_text = tender_html_element_2.find_element(By.CSS_SELECTOR, 'div:nth-child(2) > div:nth-child(1) > div:nth-child(2) > ul:nth-child(6) > li:nth-child(1)').text  
        if 'Insurance Items' in Insurance_Items_text:
            try:
                Insurance_Items_click = WebDriverWait(tender_html_element_2, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"div:nth-child(2) > div:nth-child(1) > div:nth-child(2) > ul:nth-child(6) > li:nth-child(2) > a"))).click() 
                logging.info("Insurance_Items_click")  
                time.sleep(5)
                notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, '#en > div.modal.tender-insurance-model.tenderInsuranceModal > div > div > div.modal-body').get_attribute("outerHTML") 
            except Exception as e:
                logging.info("Exception in Insurance_Items_click: {}".format(type(e).__name__))
                pass 

            try:
                notice_data.local_description = page_main.find_element(By.CSS_SELECTOR, '#en > div.modal.tender-insurance-model.tenderInsuranceModal > div > div > div.modal-body').text 
                notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
            except Exception as e:
                logging.info("Exception in local_description: {}".format(type(e).__name__))
                pass

            Insurance_Items_close_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"#en > div.modal.tender-insurance-model.tenderInsuranceModal > div > div > div.modal-header > button")))
            page_main.execute_script("arguments[0].click();",Insurance_Items_close_click)
            logging.info("Insurance_Items_close_click")  
            time.sleep(3)
    except Exception as e:
        logging.info("Exception in Insurance_Items_text: {}".format(type(e).__name__))
        pass 
    
    try:              
        customer_details_data = customer_details()
        try:
            customer_details_data.org_name = tender_html_element_2.find_element(By.CSS_SELECTOR, 'div:nth-child(2) > div:nth-child(1) > div:nth-child(1) > ul:nth-child(2) > li:nth-child(2)').text 
        except Exception as e:
            logging.info("Exception in org_name: {}".format(type(e).__name__))
            pass

        customer_details_data.org_country = 'KW'
        customer_details_data.org_language = 'AR'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:
        close_click = WebDriverWait(tender_html_element_2, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"div:nth-child(2) > div:nth-child(2) > a")))
        page_main.execute_script("arguments[0].click();",close_click)
        logging.info("close_click")  
        time.sleep(3)
    except Exception as e:
        logging.info("Exception in close_click: {}".format(type(e).__name__)) 
        pass

    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
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
    urls = ["https://capt.gov.kw/en/tenders/opening-tenders/"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)

        try:
            agree_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,"//a[contains(@class,'termsAgree btn btn-default')]")))
            page_main.execute_script("arguments[0].click();",agree_click)
            logging.info("agree_click")
        except:
            pass
            
        try:
            for page_no in range(2,7):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#en > div.main-contents.registration > div.endless_page_template.ajax-response.tenderadvertising > div.list-view.tenderslist > div'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#en > div.main-contents.registration > div.endless_page_template.ajax-response.tenderadvertising > div:nth-child(1) > div')))
                length = len(rows)
                for records in range(0,length,2):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#en > div.main-contents.registration > div.endless_page_template.ajax-response.tenderadvertising > div:nth-child(1) > div')))[records] 
                    tender_html_element_2 = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#en > div.main-contents.registration > div.endless_page_template.ajax-response.tenderadvertising > div:nth-child(1) > div')))[records+1]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
                   
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#en > div.main-contents.registration > div.endless_page_template.ajax-response.tenderadvertising > div.list-view.tenderslist > div'),page_check))
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
