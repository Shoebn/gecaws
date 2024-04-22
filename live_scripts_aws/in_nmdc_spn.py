from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "in_nmdc_spn"
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
from deep_translator import GoogleTranslator

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
tender_no = 0
SCRIPT_NAME = "in_nmdc_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    global tender_no
    notice_data = tender()
    
    notice_data.script_name = 'in_nmdc_spn'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)
   
    notice_data.currency = 'INR'
    
    notice_data.main_language = 'EN'
    
    notice_data.notice_type = 4
    
    notice_data.procurement_method = 2
    
    notice_data.notice_url = url 

    try:
        notice_type = tender_html_element.find_element(By.CSS_SELECTOR, 'div > button').text
        if 'Corrigendum' in notice_type:
            notice_data.notice_type = 16
        else:
            notice_data.notice_type = 4
    except Exception as e:
        logging.info("Exception in notice_type: {}".format(type(e).__name__))
        pass
            
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'a > h2').text
        notice_data.notice_title =GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'a > div.location > span.tender-number').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
        
    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    except:
        pass

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "a > div:nth-child(3) > div:nth-child(1) > div > span").text
        publish_date = re.findall('\d+ \w+ \d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d %B %Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try: 
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR,'a > div:nth-child(3) > div:nth-child(2) > div > span').text
        notice_deadline = re.findall('\d+ \w+ \d{4} & \d+:\d+ \w+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d %B %Y & %H:%M %p').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    try:
        document_opening_time = tender_html_element.find_element(By.CSS_SELECTOR, 'a > div:nth-child(3) > div:nth-child(3) > div > span').text
        document_opening_time = re.findall('\d+ \w+ \d{4}',document_opening_time)[0]
        notice_data.document_opening_time = datetime.strptime(document_opening_time,'%d %B %Y').strftime('%Y-%m-%d')
        logging.info(notice_data.document_opening_time)
    except Exception as e:
        logging.info("Exception in document_opening_time: {}".format(type(e).__name__))
        pass

    try:       
        est_amount = tender_html_element.find_element(By.CSS_SELECTOR, "a > div:nth-child(3) > div:nth-child(4) > div > span").text  
        est_amount = re.sub("[^\d\.\,]","",est_amount)
        notice_data.est_amount = float(est_amount)
        notice_data.grossbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
        
    try:              
        customer_details_data = customer_details() 
        customer_details_data.org_name = "NMDC Limited"
        customer_details_data.org_parent_id = 7766905

        try:
            customer_details_data.org_city = tender_html_element.find_element(By.CSS_SELECTOR,'a > div.location > span:nth-child(3)').text
        except:
            try:
                customer_details_data.org_city = tender_html_element.find_element(By.CSS_SELECTOR,'a > div.location > span:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass
            
        customer_details_data.org_country = 'IN'
        customer_details_data.org_language = 'EN'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,100)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url

    try:
        earnest_money_deposit = page_details.find_element(By.XPATH, '//*[contains(text(),"EMD")]//following::p[1]').text
        earnest_money_deposit = re.sub("[^\d\.\,]", "", earnest_money_deposit)
        earnest_money_deposit = earnest_money_deposit.replace('.','').replace(',','').strip()
        notice_data.earnest_money_deposit = earnest_money_deposit
    except Exception as e:
        logging.info("Exception in earnest_money_deposit: {}".format(type(e).__name__))
        pass

    try:
        document_cost = page_details.find_element(By.XPATH, '//*[contains(text(),"Tender Doc Cost")]//following::p[1]').text
        document_cost = re.sub("[^\d+]",'',document_cost)
        notice_data.document_cost = float(document_cost.replace(',','').strip())
    except Exception as e:
        logging.info("Exception in document_cost: {}".format(type(e).__name__))
        pass

    try:
        document_type_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Activity Type")]//following::p[1]').text
        notice_data.document_type_description  = document_type_description
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) + str(notice_data.local_title)
    logging.info(notice_data.identifier)
    duplicate_check_data = fn.duplicate_check_data_from_previous_scraping(SCRIPT_NAME,MAX_NOTICES_DUPLICATE,notice_data.identifier,previous_scraping_log_check)
    NOTICE_DUPLICATE_COUNT = duplicate_check_data[1]
    if duplicate_check_data[0] == False:
        return
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    tender_no += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments) 
page_details = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://nmdcportals.nmdc.co.in/nmdctender"] 
    for url in urls:
        fn.load_page(page_main, url, 80)
        logging.info('----------------------------------')
        logging.info(url)
        div_no = 1
        for index in range(1,3):
            notices = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'/html/body/section/div/nav/div/button['+str(index)+']')))
            page_main.execute_script("arguments[0].click();",notices)
            time.sleep(5)
            try:
                for page_no in range(2,11):
                    page_check = WebDriverWait(page_main, 120).until(EC.presence_of_element_located((By.XPATH,'/html/body/section/div/div/div['+str(div_no)+']/div/div'))).text
                    rows = WebDriverWait(page_main, 120).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/section/div/div/div['+str(div_no)+']/div/div')))
                    length = len(rows)
                    for records in range(0,length):
                        tender_html_element = WebDriverWait(page_main, 200).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/section/div/div/div['+str(div_no)+']/div/div')))[records]
                        extract_and_save_notice(tender_html_element)
                        if notice_count >= MAX_NOTICES:
                            break
    
                    try:   
                        next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                        page_main.execute_script("arguments[0].click();",next_page)
                        logging.info("Next page")
                        WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/section/div/div/div['+str(div_no)+']/div/div'),page_check))
                    except Exception as e:
                        logging.info("Exception in next_page: {}".format(type(e).__name__))
                        logging.info("No next page")
                        break
            except:
                logging.info('No new record')
                break
            div_no += 1
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)
