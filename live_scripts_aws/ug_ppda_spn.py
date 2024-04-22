from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "ug_ppda_spn"
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

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "ug_ppda_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"


# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# 1) id = Notice_no

# 2) Subject Of Procurement = local_title 

# 3) Procurement Type   = notice_contract_type  ------ Supplies, Non-Consultancy Services, Consultancy Services,  Works
# Replace following keywords with given respective keywords ('Non-Consultancy Services = Non consultancy' , ' Supplies = supply' , 'Consultancy = Consultancy Services' , 'Works = Works')

# 4) Estimated Amount =  est_amount , Grossbudgetlc

# 5) deadline = notice_deadline

# 6)  Bid Document Price = document_cost

# 7) Bid Evaluation Start Date = contract_start_date

# 8) Bid Evaluation End Date  = contract_end_date

# 9) Contract Award Date =  Award Date


# 10)Procurement Reference Number = related_tender_id

# 11) Bid Document Issue Address = org_address


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'ug_ppda_spn'
    
    notice_data.main_language = 'EN'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'UG'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.notice_type = 4
    
    notice_data.currency = 'UGX'
    
    notice_data.document_type_description = 'Tender Notices'
    
    # Onsite Field -Deadline
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "div.margin-top-30 > span").text
        notice_deadline = re.findall('\w+ \d+, \d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%b %d, %Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
        return
    
    # Onsite Field -None
    # Onsite Comment -Replace following keywords with given respective keywords ('Non-Consultancy Services = Non consultancy' , ' Supplies = supply' , 'Consultancy = Consultancy Services' , 'Works = Works')

    try:
        notice_data.contract_type_actual = tender_html_element.find_element(By.CSS_SELECTOR, ' div:nth-child(2) > div:nth-child(2)  span').text
        if "Works" in notice_data.contract_type_actual:
            notice_data.notice_contract_type ="Works"
        elif "Supplies" in notice_data.contract_type_actual:
            notice_data.notice_contract_type ="Supply"
        elif "Non-Consultancy Services" in notice_data.contract_type_actual:
            notice_data.notice_contract_type ="Non consultancy"
        elif "Consultancy" in notice_data.contract_type_actual:
            notice_data.notice_contract_type ="Consultancy Services"
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -VIEW BID NOTICE
    # Onsite Comment -None

    try:              
        customer_details_data = customer_details()
  

        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(6) > div div:nth-child(2) > div.my-2 div').text

        customer_details_data.org_country = 'UG'
        customer_details_data.org_language = 'EN'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
        
    try:
        notice_url = WebDriverWait(tender_html_element, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'span.mat-mdc-button-persistent-ripple.mdc-button__ripple')))
        page_main.execute_script("arguments[0].click();",notice_url)
        time.sleep(10) 
        notice_data.notice_url = page_main.current_url
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
    
   
    try:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, 'app-bid-invitation-details').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    

    try:
        notice_data.local_title = page_main.find_element(By.CSS_SELECTOR, 'div.margin-top-30.ng-star-inserted > div > div div:nth-child(1) > div:nth-child(3)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    

    try:
        notice_data.related_tender_id = page_main.find_element(By.CSS_SELECTOR, 'div.margin-top-30.ng-star-inserted > div > div >div:nth-child(1) > span').text
    except Exception as e:
        logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
        pass
    
    try:
        notice_no = notice_data.notice_url
        notice_data.notice_no = re.findall('\d{5}',notice_no)[0]
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -ACTIVITY	>> Publish bid notice
    # Onsite Comment -None

    try:
        publish_date = page_main.find_element(By.CSS_SELECTOR, "div.margin-top-30.ng-star-inserted  div:nth-child(2)  ol > li:nth-child(8) > table > tbody > tr:nth-child(1) > td:nth-child(3)").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -ACTIVITY	>> Pre-bid meeting where applicable
    # Onsite Comment -None

    try:
        pre_bid_meeting_date = page_main.find_element(By.CSS_SELECTOR, 'div:nth-child(2)  tr:nth-child(2) > td:nth-child(3)').text
        pre_bid_meeting_date = re.findall('\w+ \d+, \d{4}',pre_bid_meeting_date)[0]
        notice_data.pre_bid_meeting_date = datetime.strptime(pre_bid_meeting_date,'%b %d, %Y').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in pre_bid_meeting_date: {}".format(type(e).__name__))
        pass
    
        # Onsite Field -Evaluation process
# Onsite Comment -split only contract_start_date for ex."From Monday, October 30, 2023 to Monday, November 27, 2023" , here take only "October 30, 2023" , ref_url : "https://gpp.ppda.go.ug/public/bid-invitations/tender-notice/87955"
    
    try:
        tender_contract_end_date = page_main.find_element(By.CSS_SELECTOR, 'td:nth-child(3) > span:nth-child(2)').text
        tender_contract_end_date = re.findall('\w+ \d+, \d{4}',tender_contract_end_date)[0]
        notice_data.tender_contract_end_date = datetime.strptime(tender_contract_end_date,'%B %d, %Y').strftime('%Y/%m/%d')
    except Exception as e:
        logging.info("Exception in tender_contract_end_date: {}".format(type(e).__name__))
        pass

# Onsite Field -Evaluation process
# Onsite Comment -split only contract_end_date for ex."From Monday, October 30, 2023 to Monday, November 27, 2023" , here take only "November 27, 2023" , ref_url : "https://gpp.ppda.go.ug/public/bid-invitations/tender-notice/87955"

    try:
        tender_contract_start_date  = page_main.find_element(By.CSS_SELECTOR, 'tr:nth-child(4) td:nth-child(3) > span:nth-child(1)').text
        tender_contract_start_date  = re.findall('\w+ \d+, \d{4}',tender_contract_start_date )[0]
        notice_data.tender_contract_start_date  = datetime.strptime(tender_contract_start_date ,'%B %d, %Y').strftime('%Y/%m/%d')
    except Exception as e:
        logging.info("Exception in contract_end_date: {}".format(type(e).__name__))
        pass


    try:   
        lot_number = 1
        for single_record in page_main.find_elements(By.CSS_SELECTOR, 'li:nth-child(1) > table > tbody > tr:nth-child(n)'):
            lot_details_data = lot_details()
            lot_details_data.lot_number = lot_number
        # Onsite Field -LOT DETAILS
        # Onsite Comment -split only lot_actual_number , for-ex."LOT 1: SUPPLY OF HIGH LIFT PUMP SETS FOR BUSOWA – BUGIRI AREA" , here split only "LOT 1" , ref_url : "https://gpp.ppda.go.ug/public/bid-invitations/tender-notice/87872"

            try:
                lot_details_data.lot_actual_number = single_record.find_element(By.CSS_SELECTOR, ' td:nth-child(2)').text.split(":")[0].strip()
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -LOT DETAILS
        # Onsite Comment -split only lot_title, for-ex."LOT 1: SUPPLY OF HIGH LIFT PUMP SETS FOR BUSOWA – BUGIRI AREA", here split only "SUPPLY OF HIGH LIFT PUMP SETS FOR BUSOWA – BUGIRI AREA" , ref_url : "https://gpp.ppda.go.ug/public/bid-invitations/tender-notice/87872"

            try:
                lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text.split(":")[1].strip()
                lot_details_data.lot_title_english = lot_details_data.lot_title
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -BID SECURITY AMOUNT
        # Onsite Comment -None

            try:
                lot_grossbudget_lc = single_record.find_element(By.CSS_SELECTOR, ' td.ng-star-inserted').text
                lot_grossbudget_lc = re.sub("[^\d\.\,]", "", lot_grossbudget_lc) 
                lot_details_data.lot_grossbudget_lc = float(lot_grossbudget_lc.replace(',','').strip())
            except Exception as e:
                logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
                pass
        
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
            lot_number += 1 
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass

    page_main.execute_script("window.history.go(-1)")
    
    WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/app-root/app-main-layout/div/div/div/div/div/app-bid-invitations/div/div/div/div/div[6]/div/div')))
    
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
    urls = ["https://gpp.ppda.go.ug/#/public/bid-invitations"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)

        try:
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/app-root/app-main-layout/div/div/div/div/div/app-bid-invitations/div/div/div/div/div[6]/div/div')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/app-root/app-main-layout/div/div/div/div/div/app-bid-invitations/div/div/div/div/div[6]/div/div')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
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
