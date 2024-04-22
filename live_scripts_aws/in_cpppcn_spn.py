from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "in_cpppcn_spn"
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

#Note:Fill the captcha in detail_page to get data
#Note:Open the site than click on "Central - Active Tenders" than grab the data

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "in_cpppcn_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'in_cpppcn_spn'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)
   
    notice_data.currency = 'INR'
  
    notice_data.main_language = 'EN'
    
    notice_data.procurement_method = 2
  
    notice_data.notice_type = 4
    
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(2)").text
        publish_date = re.findall('\d+-\w+-\d{4} \d+:\d+ \w{2}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d-%b-%Y %I:%M %p').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        notice_deadline = re.findall('\d+-\w+-\d{4} \d+:\d+ \w{2}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d-%b-%Y %I:%M %p').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass    
    
    try:
        document_opening_time = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
        document_opening_time = re.findall('\d+-\w+-\d{4} \d+:\d+',document_opening_time)[0]
        notice_data.document_opening_time = datetime.strptime(document_opening_time,'%d-%b-%Y %H:%M').strftime('%Y-%m-%d')
    except Exception as e:
        logging.info("Exception in document_fee: {}".format(type(e).__name__))
        pass

    try:
        org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(6)').text
    except:
        pass

    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5) > a').get_attribute("href")
        notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5) > a').click()
        time.sleep(2)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    try:
        image = page_main.find_element(By.CSS_SELECTOR, "#tenderfullview-tenders > div > div > div.col-sm-12.col-md-12.control-wrap > div > img").get_attribute("alt")     
            
        page_main.find_element(By.XPATH,'//*[@id="edit-captcha-response"]').send_keys(image)
        time.sleep(4)
        
        submit = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#edit-save')))
        page_main.execute_script("arguments[0].click();",submit)
        time.sleep(6)

        try:
            WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#tfullview > div'))).text
        except:
            pass

        try:
            notice_data.notice_no = page_main.find_element(By.XPATH, '(//*[contains(text(),"Tender Reference Number")]//following::td[2])[1]').text
        except Exception as e:
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass
            
        try:
            notice_data.local_title = page_main.find_element(By.XPATH, '(//*[contains(text(),"Work Description")]//following::div)[1]').text
            notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
        except Exception as e:
            logging.info("Exception in local_title: {}".format(type(e).__name__))
            pass

        try:
            document_purchase_start_time = page_main.find_element(By.XPATH, '(//*[contains(text(),"Bid Submission Start Date")]//following::td[2])[1]').text
            document_purchase_start_time = re.findall('\d+-\w+-\d{4}',document_purchase_start_time)[0]
            notice_data.document_purchase_start_time = datetime.strptime(document_purchase_start_time,'%d-%b-%Y').strftime('%Y/%m/%d')
        except Exception as e:
            logging.info("Exception in document_purchase_start_time: {}".format(type(e).__name__))
            pass
    
        try:
            document_purchase_end_time = page_main.find_element(By.XPATH, '(//*[contains(text(),"Bid Submission End Date")]//following::td[2])[1]').text
            document_purchase_end_time = re.findall('\d+-\w+-\d{4}',document_purchase_end_time)[0]
            notice_data.document_purchase_end_time = datetime.strptime(document_purchase_end_time,'%d-%b-%Y').strftime('%Y/%m/%d')
        except Exception as e:
            logging.info("Exception in document_purchase_end_time: {}".format(type(e).__name__))
            pass

        try:
            earnest_money_deposit  = page_main.find_element(By.XPATH, '(//*[contains(text(),"EMD")]//following::td[2])[1]').text 
            earnest_money_deposit = re.sub("[^\d\.\,]", "", earnest_money_deposit)
            earnest_money_deposit = earnest_money_deposit.replace('.','').replace(',','.').strip()
            notice_data.earnest_money_deposit = earnest_money_deposit
        except Exception as e:
            logging.info("Exception in earnest_money_deposit".format(type(e).__name__))
            pass
            
        try:              
            customer_details_data = customer_details()
            customer_details_data.org_name = org_name

            try:
                customer_details_data.contact_person = page_main.find_element(By.XPATH, '(//*[contains(text(),"Name")]//following::td[2]/div[1])[2]').text
            except Exception as e:
                logging.info("Exception in contact_person".format(type(e).__name__))
                pass   

            try:
                customer_details_data.org_address = page_main.find_element(By.XPATH, '(//*[contains(text(),"Address")]//following::td[2]/div[1])[1]').text
            except Exception as e:
                logging.info("Exception in org_address".format(type(e).__name__))
                pass
    
            customer_details_data.org_country = 'IN'
            customer_details_data.org_language = 'EN'
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
        except Exception as e:
            logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
            pass

        try:
            notice_data.contract_type_actual = page_main.find_element(By.XPATH,'(//*[contains(text(),"Product Category")]//following::td[2])[1]').text
            if 'Goods' in notice_data.contract_type_actual:
                notice_data.notice_contract_type = "Supply"
            elif 'Services' in notice_data.contract_type_actual:
                notice_data.notice_contract_type = "Service"
            elif 'Works' in notice_data.contract_type_actual:
                notice_data.notice_contract_type = "Works"
            else:
                pass
        except Exception as e:
            logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
            pass

        try:
            notice_data.additional_tender_url = page_main.find_element(By.XPATH,'(//*[contains(text(),"Tender Document")]//following::td[2]/div/a)[1]').get_attribute('href')
        except Exception as e:
            logging.info("Exception in additional_tender_url: {}".format(type(e).__name__))
            pass

        try:
            notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR,'#tfullview > div').get_attribute('outerHTML')
        except Exception as e:
            logging.info("Exception in notice_text: {}".format(type(e).__name__))
    except:
        pass
    page_main.execute_script("window.history.go(-1)")
    page_main.execute_script("window.history.go(-1)")
    WebDriverWait(page_main, 100).until(EC.presence_of_element_located((By.XPATH,'//*[@id="table"]/tbody/tr'))).text
    
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
    urls = ["https://eprocure.gov.in/cppp/latestactivetendersnew/cpppdata"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        time.sleep(20)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(2,500):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="table"]/tbody/tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="table"]/tbody/tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="table"]/tbody/tr')))[records]
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
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="table"]/tbody/tr'),page_check))
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
