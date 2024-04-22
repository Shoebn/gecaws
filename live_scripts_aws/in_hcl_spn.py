from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "in_hcl_spn"
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
SCRIPT_NAME = "in_hcl_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"

def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'in_hcl_spn'
    
    notice_data.main_language = 'EN'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.procurement_method = 2
  
    notice_data.currency = 'INR'
        
    notice_data.notice_type = 4
    
    try:
        org_address = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(1)").text  
    except Exception as e:
        logging.info("Exception in notice_type: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(2)").text  
    except Exception as e:
        logging.info("Exception in notice_type: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
        notice_data.notice_title = notice_data.local_title
        if len(notice_data.local_title) < 5:
            return
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass 
    
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(3)").text 
        notice_data.publish_date = datetime.strptime(publish_date,'%d-%b-%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(5)").text
        notice_deadline = re.findall('\d+-\w+-\d{4} \d+:\d+ [PMAMpmam]+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d-%b-%Y %I:%M %p').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    try:       
        est_amount = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(6)").text  
        est_amount = re.sub("[^\d\.\,]","",est_amount).replace(',','').strip()
        notice_data.est_amount =float(est_amount)
        notice_data.netbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_text += tender_html_element.get_attribute("outerHTML")                     
    except:
        pass
    
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'IN'
        customer_details_data.org_language = 'EN'
        customer_details_data.org_name =  "HINDUSTAN COPPER LIMITED"
        customer_details_data.org_parent_id = 7527321
        customer_details_data.org_address = org_address
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass    
    
    try:
        no = tender_html_element.find_element(By.CSS_SELECTOR, " td:nth-child(2) > a").get_attribute("href").split('Details/')[1].split("')")[0].strip()
        notice_data.notice_url = "https://hindustancopper.com/Page/TenderListforDetails/"+str(no)
    except:
        pass

    try:
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)    

        try:
            notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'body > form').get_attribute("outerHTML")                     
        except:
            pass

        try:
            notice_data.earnest_money_deposit = page_details.find_element(By.XPATH, '//*[contains(text(),"EMD(Rs.)")]//following::td[1]').text
        except Exception as e:
            logging.info("Exception in earnest_money_deposit: {}".format(type(e).__name__)) 
            pass 
    except:
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
page_details =fn.init_chrome_driver(arguments)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://hindustancopper.com/Page/TenderList"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)   
        try:
            for page_no in range(2,10):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#sampleTable > tbody > tr'))).text
                rows = WebDriverWait(page_main, 80).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#sampleTable > tbody > tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#sampleTable > tbody > tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#sampleTable > tbody > tr'),page_check))
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
    page_details.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)
