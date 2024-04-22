from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "in_apeprocamd"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "in_apeprocamd"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'in_apeprocamd'
   
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'INR'
  
    notice_data.main_language = 'EN'
   
    notice_data.procurement_method = 0
   
    notice_data.notice_type = 16
    
    notice_data.notice_url = url
     
    # Onsite Field -None
    # Onsite Comment -Note: Go to home page > Corrigendums click on more.
    
    
    # Onsite Field -Enquiry/IFB/Tender Notice Number
    # Onsite Comment -Split Enquiry/IFB/Tender Notice Number

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Corrigendum Subject
    # Onsite Comment -None

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'tr td:nth-child(7)').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Latest Corrigendum Date
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "tr> td.sorting_1").text
        publish_date = re.findall('\d+/\d+/\d{4} \d+:\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'IN'
        customer_details_data.org_state = 'AP'
        customer_details_data.org_language = 'EN'
        # Onsite Field -Department Name
        # Onsite Comment -None

        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'tr td:nth-child(4)').text

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'tr td:nth-child(8) > a').get_attribute("href")                     
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    # Onsite Field -Action
    # Onsite Comment -None

    try:        
        switch_window = tender_html_element.find_element(By.CSS_SELECTOR, 'td > a:nth-child(1)').click() 
        page_main.switch_to.window(page_main.window_handles[1])
        time.sleep(5)
    except:
        pass
    
    WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'tr:nth-child(2) > td.tdwhite')))
    
    # Onsite Field -None
    # Onsite Comment -Combine both this "#tenderBean,#corrigendumDetailsForm " selector
    try:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, '#tenderBean').get_attribute("outerHTML")                     
    except:
        pass
    
    # Onsite Field -Name of Project
    # Onsite Comment -None

    try:
        notice_data.local_title = page_main.find_element(By.CSS_SELECTOR, 'tr:nth-child(2) > td.tdwhite').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Bid Submission Closing Date and Time
    # Onsite Comment -None

    try:
        notice_deadline = page_main.find_element(By.CSS_SELECTOR, "tr:nth-child(5) > td:nth-child(4)").text
        notice_deadline = re.findall('\d+/\d+/\d{4} \d+:\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Bid Document Download Start Date and Time
    # Onsite Comment -None

    try:
        document_purchase_start_time = page_main.find_element(By.CSS_SELECTOR, 'tr:nth-child(5) > td:nth-child(2)').text
        document_purchase_start_time = re.findall('\d+/\d+/\d{4}',document_purchase_start_time)[0]
        notice_data.document_purchase_start_time = datetime.strptime(document_purchase_start_time,'%d/%m/%Y').strftime('%Y/%m/%d')
    except Exception as e:
        logging.info("Exception in document_purchase_start_time: {}".format(type(e).__name__))
        pass

    
    # Onsite Field -Estimated Contract/IBM Value
    # Onsite Comment -None

    try:
        est_amount = page_main.find_element(By.CSS_SELECTOR, 'tr:nth-child(4) > td:nth-child(4)').text
        est_amount = re.sub("[^\d\.\,]","",est_amount)
        est_amount=est_amount.replace(",","")
        notice_data.est_amount=float(est_amount)
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
     
    try:      
        page_main.switch_to.window(page_main.window_handles[0])
        switch_window = page_main.find_element(By.CSS_SELECTOR, '#back').click()
        time.sleep(5)
    except:
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
    urls = ["https://tender.apeprocurement.gov.in/login.html"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        try:
            Corrigendums=page_main.find_element(By.CSS_SELECTOR, '#skipContentBox > label:nth-child(4)')
            page_main.execute_script("arguments[0].click();",Corrigendums)
            time.sleep(5)
        except:
            pass
        try:
            more_click=page_main.find_element(By.CSS_SELECTOR, '#viewCorrigendumall')
            page_main.execute_script("arguments[0].click();",more_click)
            time.sleep(5)
        except:
            pass

        try:
            for page_no in range(2,20):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="pagetable14"]/tbody/tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="pagetable14"]/tbody/tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="pagetable14"]/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
                        
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="pagetable14"]/tbody/tr'),page_check))
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
