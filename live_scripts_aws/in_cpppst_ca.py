from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "in_cpppst_ca"
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
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "in_cpppst_ca"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"

# ------------------------------------------------------------------------------------------------------------------------------------------------
# Visit the URL 'https://www.ms.gov/dfa/contract_bid_search/Bid?autoloadGrid=False', 
# click on 'ADVANCED SEARCH OPTIONS,' choose 'Open' from the 'STATUS' drop-down menu, and then click the 'SEARCH' button
# ---------------------------------------------------------------------------------------------------------------------------------------------

def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'in_cpppst_ca'
    
    notice_data.main_language = 'EN'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.procurement_method = 2
  
    notice_data.currency = 'INR'
    
    notice_data.notice_url = url
    
    notice_data.notice_type = 7
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass 
    
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        publish_date = re.findall('\d+-\w+-\d{4} \d+:\d+ [PMAMpmam]+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d-%b-%Y  %I:%M %p').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    try:
        org_state = tender_html_element.find_element(By.CSS_SELECTOR, " td:nth-child(5)").text
    except:
        pass
    
    try:
        award_date = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
    except:
        pass
    
    try:
        page_detail_click = WebDriverWait(tender_html_element, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'td:nth-child(4) > a')))
        page_main.execute_script("arguments[0].click();",page_detail_click)
        time.sleep(5)
        try:
            notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, '#tfullview > div > table:nth-child(2)').get_attribute("outerHTML")                     
        except:
            pass
        
        try:
            est_amount = page_main.find_element(By.XPATH, "//*[contains(text(),'Contract Value')]//following::td[2]").text
            est_amount = re.sub("[^\d\.\,]","",est_amount)
            notice_data.est_amount = float(est_amount.strip())
            notice_data.grossbudgetlc = notice_data.est_amount
        except Exception as e:
            logging.info("Exception in est_amount: {}".format(type(e).__name__))
            pass


        try:
            notice_data.notice_no = page_main.find_element(By.XPATH, "//*[contains(text(),'Tender Ref. No.')]//following::td[2]").text            
        except Exception as e:
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass

        try:
            notice_data.local_description = page_main.find_element(By.XPATH, "//*[contains(text(),'Tender Description')]//following::td[2]").text 
            notice_data.notice_summary_english = notice_data.local_description
        except Exception as e:
            logging.info("Exception in local_description: {}".format(type(e).__name__))
            pass

        try:
            notice_data.additional_tender_url = page_main.find_element(By.XPATH, "//*[contains(text(),'Tender Document')]//following::td[2]").text
        except Exception as e:
            logging.info("Exception in additional_tender_url: {}".format(type(e).__name__))
            pass

        try:
            notice_data.notice_contract_type = page_main.find_element(By.XPATH, "//*[contains(text(),'Tender Type')]//following::td[2]").text
        except Exception as e:
            logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
            pass

        try:              
            customer_details_data = customer_details()
            customer_details_data.org_country = 'IN'
            customer_details_data.org_language = 'EN'
            customer_details_data.org_name = page_main.find_element(By.XPATH, "//*[contains(text(),'Organisation Name')]//following::td[2]").text

            try:
                customer_details_data.org_state = org_state
            except:
                pass

            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
        except Exception as e:
            logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
            pass    

        try:              
            lot_details_data = lot_details()
            lot_details_data.lot_number = 1

            lot_details_data.lot_title = notice_data.local_title
            notice_data.is_lot_default = True

            award_details_data = award_details()

            award_details_data.bidder_name = page_main.find_element(By.XPATH, "//*[contains(text(),'Name of the selected bidder(s)')]//following::td[2]").text

            try:
                award_date1 = award_date
                award_date2 = re.findall('\d+-\w+-\d{4}',award_date1)[0]
                award_details_data.award_date = datetime.strptime(award_date2,'%d-%b-%Y').strftime('%Y/%m/%d') 
            except:
                pass

            award_details_data.award_details_cleanup()
            lot_details_data.award_details.append(award_details_data)

            if lot_details_data.award_details != []:
                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
        except Exception as e:
            logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
            pass
        
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__)) 
        pass
    
    page_main.execute_script("window.history.go(-1)")
    time.sleep(5)
    WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#table > tbody > tr')))
    
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
    urls = ["https://eprocure.gov.in/cppp/resultoftendersnew/mmpdata/byYzJWc1pXTjBBMTNoMUExM2gxQTEzaDFBMTNoMU1qQXlNZz09QTEzaDFNUT09"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url) 
        
        time.sleep(4)
        select_year = Select(page_main.find_element(By.XPATH,'//*[@id="edit-year"]'))
        select_year.select_by_value('2024')
        time.sleep(5)
        
        image = page_main.find_element(By.CSS_SELECTOR, "#resultoftendersnew-form > div.logregformback.col-md-12 > div > div.col-sm-12.col-md-12.control-wrap > div > img").get_attribute("alt")     
        
        page_main.find_element(By.XPATH,'//*[@id="edit-captcha-response"]').send_keys(image)
        time.sleep(5)
        
        Search = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#btnSearch')))
        page_main.execute_script("arguments[0].click();",Search)
        time.sleep(6)

        try:
            rows = WebDriverWait(page_main, 80).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#table > tbody > tr')))
            length = len(rows)
            for records in range(1,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#table > tbody > tr')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
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
    
