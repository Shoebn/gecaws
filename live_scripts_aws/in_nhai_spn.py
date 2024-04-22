from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "in_nhai_spn"
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
SCRIPT_NAME = "in_nhai_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    global tender_no
    notice_data = tender()
    
    notice_data.script_name = 'in_nhai_spn'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)
   
    notice_data.currency = 'INR'
    
    notice_data.main_language = 'EN'
    
    notice_data.notice_type = 4
    
    notice_data.procurement_method = 2
    
    notice_data.document_type_description = "CURRENT TENDERS"
        
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(3) > p').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR,'div:nth-child(1) > p:nth-child(1)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
        
    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    except:
        pass

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div:nth-child(2) > p:nth-child(1)").text
        publish_date = re.findall('\d+-\d+-\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d-%m-%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try: 
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR,'div:nth-child(4) > p').text
        notice_deadline = re.findall('\d+-\d+-\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d-%m-%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    try: 
        document_opening_time = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(1) > p:nth-child(2)').text
        document_opening_time = re.findall('\d+-\d+-\d{4}',document_opening_time)[0]
        notice_data.document_opening_time = datetime.strptime(document_opening_time,'%d-%m-%Y').strftime('%Y-%m-%d')
    except Exception as e:
        logging.info("Exception in document_opening_time: {}".format(type(e).__name__))
        pass

    try:
        notice_url = WebDriverWait(tender_html_element, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'div:nth-child(2) > p:nth-child(2) > a')))
        page_main.execute_script("arguments[0].click();",notice_url)
        time.sleep(3)
        page_main.switch_to.window(page_main.window_handles[1])
        time.sleep(3)
        notice_data.notice_url = page_main.current_url
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url

    try:
         WebDriverWait(page_main, 90).until(EC.presence_of_element_located((By.XPATH,'//*[@id="pages-wrapper"]/app-tender-detail/div[2]/div/div[2]/div[1]/div/div/table/tr[2]/td'))).text
    except:
        pass


    try:
        document_purchase_start_time = page_main.find_element(By.XPATH, '//*[contains(text(),"Tender Document Sales Start Date")]//following::td[1]').text
        document_purchase_start_time = re.findall('\d+-\d+-\d{4}',document_purchase_start_time)[0]
        notice_data.document_purchase_start_time = datetime.strptime(document_purchase_start_time,'%d-%m-%Y').strftime('%Y/%m/%d')
    except Exception as e:
        logging.info("Exception in document_purchase_start_time: {}".format(type(e).__name__))
        pass
    
    try:
        document_purchase_end_time = page_main.find_element(By.XPATH, '//*[contains(text(),"Tender Document Sales End Date")]//following::td[1]').text
        document_purchase_end_time = re.findall('\d+-\d+-\d{4}',document_purchase_end_time)[0]
        notice_data.document_purchase_end_time = datetime.strptime(document_purchase_end_time,'%d-%m-%Y').strftime('%Y/%m/%d')
    except Exception as e:
        logging.info("Exception in document_purchase_end_time: {}".format(type(e).__name__))
        pass

    try:
        pre_bid_meeting_date = page_main.find_element(By.XPATH, '//*[contains(text(),"Pre Bid Meeting Date")]//following::td[1]').text
        pre_bid_meeting_date = re.findall('\d+-\d+-\d{4}',pre_bid_meeting_date)[0]
        notice_data.pre_bid_meeting_date = datetime.strptime(pre_bid_meeting_date,'%d-%m-%Y').strftime('%Y/%m/%d')
    except Exception as e:
        logging.info("Exception in pre_bid_meeting_date: {}".format(type(e).__name__))
        pass

    try:
        document_cost = page_main.find_element(By.XPATH, '//*[contains(text(),"Application Fee")]//following::td[1]').text
        document_cost = re.sub("[^\d\.\,]","",document_cost)
        notice_data.document_cost =float(document_cost.replace('.','').replace(',','.').strip())
    except Exception as e:
        logging.info("Exception in document_cost: {}".format(type(e).__name__))
        pass

    try:
        earnest_money_deposit = page_main.find_element(By.XPATH, '//*[contains(text(),"EMD Value")]//following::td[1]').text
        if '-' not in earnest_money_deposit:
            notice_data.earnest_money_deposit = earnest_money_deposit
    except Exception as e:
        logging.info("Exception in earnest_money_deposit: {}".format(type(e).__name__))
        pass
        
    try:              
        customer_details_data = customer_details() 
        customer_details_data.org_name = "National Highways Authority of India"
        customer_details_data.org_parent_id = 6967583
        try:
            org_address = page_main.find_element(By.XPATH,'//*[contains(text(),"Department")]//following::td[1]').text
            if '-' not in org_address:
                customer_details_data.org_address
        except:
            pass
        customer_details_data.org_country = 'IN'
        customer_details_data.org_language = 'EN'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try:  
        for single_record in page_main.find_elements(By.CSS_SELECTOR,'div.tableInfoPage > div > div:nth-child(3) > div:nth-child(2) > div > div > table > tr')[2:]:
            attachments_data = attachments()
            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR,'td:nth-child(2)> a').get_attribute('href')
            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR,'td:nth-child(1)').text

            try:
                attachments_data.file_size = single_record.find_element(By.CSS_SELECTOR,'td:nth-child(2)> a > span > span').text.split('(')[1].split(')')[0].strip()
            except:
                pass
                
            try:
                attachments_data.file_type = attachments_data.external_url.split('.')[-1].strip()
            except:
                pass
                
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass

    try:
        notice_data.notice_text += page_main.find_element(By.XPATH,'/html/body/app-root/app-layout/div/app-pages/div/app-tender-detail/div[2]/div').get_attribute('outerHTML')
    except:
        pass

    try:
        back_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'btnBlue')))
        page_main.execute_script("arguments[0].click();",back_click)
    except:
        pass
        
    page_main.close()
    try:
        page_main.switch_to.window(page_main.window_handles[0])
    except:
        pass
    WebDriverWait(page_main, 120).until(EC.presence_of_element_located((By.CSS_SELECTOR,'div.homeTendersTab.ng-star-inserted > div.tendersRow'))).text
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) + str(notice_data.local_title)
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
    urls = ["https://nhai.gov.in/#/tenders"] 
    for url in urls:
        fn.load_page(page_main, url, 80)
        logging.info('----------------------------------')
        logging.info(url)

        lang_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'body > app-root > app-layout > app-inner-header > div > div > div.topStrip.cf > div > div > ul.rightLinks > li:nth-child(5) > a')))
        page_main.execute_script("arguments[0].click();",lang_click)

        for i in range(1,5):
            i = page_main.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)

        try:
            for page_no in range(1,5):
                page_check = WebDriverWait(page_main, 120).until(EC.presence_of_element_located((By.CSS_SELECTOR,'div.homeTendersTab.ng-star-inserted > div.tendersRow'))).text
                rows = WebDriverWait(page_main, 120).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.homeTendersTab.ng-star-inserted > div.tendersRow')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 200).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.homeTendersTab.ng-star-inserted > div.tendersRow')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
    
                try:   
                    next_page = WebDriverWait(page_main, 70).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'li.pagination-next.ng-star-inserted > a')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'div.homeTendersTab.ng-star-inserted > div.tendersRow'),page_check))
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