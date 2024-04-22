from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "in_sail_spn"
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
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
tender_no = 0
SCRIPT_NAME = "in_sail_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    global tender_no
    notice_data = tender()
    
    notice_data.script_name = 'in_sail_spn'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)
   
    notice_data.currency = 'INR'
    
    notice_data.main_language = 'EN'
    
    notice_data.notice_type = 4
    
    notice_data.procurement_method = 2
    
    notice_data.notice_url = url 

    notice_data.document_type_description = 'Announcements'
    
    try:
        notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        if 'DATED' in notice_no:
            notice_data.notice_no = notice_no.split('DATED')[0].strip()
        elif 'dated' in notice_no:
            notice_data.notice_no = notice_no.split('dated')[0].strip()
        else:
            notice_data.notice_no = notice_no
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
        notice_data.notice_title =GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    except:
        pass
    
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(4)').text
        publish_date = re.findall('\w+ \d+ \d{4} \d+:\d+:\d+:\d+\w+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%b %d %Y %H:%M:%S:%f%p').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
        
    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR,'td.BidClosingDT').text
        notice_deadline = re.findall('\w+ \d+ \d{4} \d+:\d+:\d+:\d+\w+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%b %d %Y %H:%M:%S:%f%p').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    try:
        notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(6) > a').click()  
        time.sleep(3)
    except:
        pass

    page_main.switch_to.window(page_main.window_handles[1])
    WebDriverWait(page_main, 120).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#tblTendet > tbody > tr:nth-child(10)'))).text
    try:
        notice_data.contract_type_actual = page_main.find_element(By.XPATH,'(//*[contains(text(),"Tender Category")]//following::td[1])[1]').text
        if 'Goods' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = "Supply"
        elif 'Services' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = "Service"
        elif 'Works' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = "Works"
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    try:
        document_opening_time = page_main.find_element(By.XPATH, '(//*[contains(text(),"Bids Opening Date And Time")]//following::td[1])[1]').text
        document_opening_time = re.findall('\d+ \w+ \d{4}',document_opening_time)[0]
        notice_data.document_opening_time = datetime.strptime(document_opening_time,'%d %b %Y').strftime('%Y-%m-%d')
    except Exception as e:
        logging.info("Exception in document_purchase_start_time: {}".format(type(e).__name__))
        pass

    try:
        document_purchase_end_time = page_main.find_element(By.XPATH, '(//*[contains(text(),"Bid Submission Closing Date & Time")]//following::td[1])[1]').text
        document_purchase_end_time = re.findall('\d+ \w+ \d{4}',document_purchase_end_time)[0]
        notice_data.document_purchase_end_time = datetime.strptime(document_purchase_end_time,'%d %b %Y').strftime('%Y/%m/%d')
    except Exception as e:
        logging.info("Exception in document_purchase_end_time: {}".format(type(e).__name__))
        pass

    try:
        pre_bid_meeting_date = page_main.find_element(By.XPATH, '//*[contains(text(),"Pre Bid Meeting Date")]//following::td').text
        pre_bid_meeting_date = re.findall('\d+ \w+ \d{4} \d+:\d+:\d+',pre_bid_meeting_date)[0]
        notice_data.pre_bid_meeting_date = datetime.strptime(pre_bid_meeting_date,'%d %b %Y %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in pre_bid_meeting_date: {}".format(type(e).__name__))
        pass

    try:
        earnest_money_deposit = page_main.find_element(By.XPATH, '//*[contains(text(),"EMD Amount")]//following::td[1]').text
        earnest_money_deposit = re.sub("[^\d\.\,]", "", earnest_money_deposit)
        earnest_money_deposit = earnest_money_deposit.replace('.','').replace(',','').strip()
        notice_data.earnest_money_deposit = earnest_money_deposit
    except Exception as e:
        logging.info("Exception in earnest_money_deposit: {}".format(type(e).__name__))
        pass

    try:
        notice_data.document_fee = page_main.find_element(By.XPATH, "//*[contains(text(),'Bidding Document/Processing Fee (INR)')]//following::td[1]").text
    except Exception as e:
        logging.info("Exception in document_fee: {}".format(type(e).__name__))
        pass
        
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = page_main.find_element(By.XPATH, '//*[contains(text(),"Organization")]//following::td[1]').text
        customer_details_data.org_country = 'IN'
        customer_details_data.org_language = 'EN'

        try:
            customer_details_data.contact_person = page_main.find_element(By.XPATH, '//*[contains(text(),"Name")]//following::td[1]').text
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass
    
        try:
            customer_details_data.org_phone = page_main.find_element(By.XPATH, '//*[contains(text(),"Phone/Fax")]//following::td[1]').text
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass

        try:
            customer_details_data.org_fax = page_main.find_element(By.XPATH, '//*[contains(text(),"Phone/Fax")]//following::td[1]').text
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass
    
        try:
            customer_details_data.org_email = page_main.find_element(By.XPATH, '//*[contains(text(),"Email Address")]//following::td[1]').text
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass
    
        try:
            customer_details_data.org_address = page_main.find_element(By.XPATH, '(//*[contains(text(),"Address")]//following::td[1])[1]').text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, '#tblTendet').get_attribute('outerHTML')
    except:
        pass
        
    page_main.switch_to.window(page_main.window_handles[0]) 
    WebDriverWait(page_main, 120).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#tblTendet > tbody > tr'))).text
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    tender_no += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://sailtenders.co.in/Home/AdvancedSearch"] 
    for url in urls:
        fn.load_page(page_main, url, 80)
        logging.info('----------------------------------')
        logging.info(url)
        status_click = WebDriverWait(page_main, 80).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#dvTend > div:nth-child(3) > div > div > label'))).click()    
        time.sleep(5)
        
        action = ActionChains(page_main)
 
        action.send_keys(Keys.ARROW_LEFT) 
        time.sleep(2)

        action.send_keys(Keys.ENTER) 
        time.sleep(2)

        action.perform()

        status_click_2 = WebDriverWait(page_main, 80).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#dvTend > div:nth-child(4) > div > div > label > span')))
        page_main.execute_script("arguments[0].click();",status_click_2)
        time.sleep(5)
        
        action = ActionChains(page_main)
 
        action.send_keys(Keys.ENTER)
        time.sleep(2)
        
        action.send_keys(Keys.ENTER) 
        time.sleep(2)

        action.perform()
    
        search = WebDriverWait(page_main, 100).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="btnTendSrch"]')))
        page_main.execute_script("arguments[0].click();",search)
        time.sleep(2)
        try:   
            for page_no in range(1,5):
                page_check = WebDriverWait(page_main, 120).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#tblTendet > tbody > tr'))).text
                rows = WebDriverWait(page_main, 120).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#tblTendet > tbody > tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 200).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#tblTendet > tbody > tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                try:   
                    next_page = WebDriverWait(page_main, 80).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#tblTendet_next')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 80).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#tblTendet > tbody > tr'),page_check))
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
