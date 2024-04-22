
from gec_common.gecclass import *
import logging
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
import functions as fn
from functions import ET
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "ug_ppda_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
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
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.script_name = 'ug_ppda_spn'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'EN'
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'UG'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_type = 4
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'UGX'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.document_type_description = 'Tender Notices'
    
    # Onsite Field -Deadline
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "div.margin-top-30 > span").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -Replace following keywords with given respective keywords ('Non-Consultancy Services = Non consultancy' , ' Supplies = supply' , 'Consultancy = Consultancy Services' , 'Works = Works')

    try:
        notice_data.notice_contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'div> div:nth-child(2) > div:nth-child(2)  span').text
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -VIEW BID NOTICE
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div> div > div.mt-4 > button > span.mdc-button__label').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'app-bid-invitation-details').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.local_title = page_details.find_element(By.CSS_SELECTOR, 'div.margin-top-30.ng-star-inserted > div > div div:nth-child(1) > div:nth-child(3)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.related_tender_id = page_details.find_element(By.CSS_SELECTOR, 'div.margin-top-30.ng-star-inserted > div > div >div:nth-child(1) > span').text
    except Exception as e:
        logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.related_tender_id = page_details.find_element(By.CSS_SELECTOR, 'div.margin-top-30.ng-star-inserted > div > div >div:nth-child(1) > span').text
    except Exception as e:
        logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -ACTIVITY	>> Publish bid notice
    # Onsite Comment -None

    try:
        publish_date = page_details.find_element(By.CSS_SELECTOR, "div.margin-top-30.ng-star-inserted  div:nth-child(2)  ol > li:nth-child(8) > table > tbody > tr:nth-child(1) > td:nth-child(3)").text
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
        notice_data.pre_bid_meeting_date = page_details.find_element(By.CSS_SELECTOR, 'div:nth-child(2)  tr:nth-child(2) > td:nth-child(3)').text
    except Exception as e:
        logging.info("Exception in pre_bid_meeting_date: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, 'app-bid-invitations > div > div > div > div > div:nth-child(6)'):
            customer_details_data = customer_details()
        # Onsite Field -None
        # Onsite Comment -None

            try:
                customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(6) > div div:nth-child(2) > div.my-2 div').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
            customer_details_data.org_country = 'UG'
            customer_details_data.org_language = 'EN'
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'app-main-layout  app-bid-invitation-details > div.margin-top-30.ng-star-inserted > div > div > div:nth-child(2) > div > div > ol > li:nth-child(1)'):
            lot_details_data = lot_details()
        # Onsite Field -LOT DETAILS
        # Onsite Comment -split only lot_actual_number , for-ex."LOT 1: SUPPLY OF HIGH LIFT PUMP SETS FOR BUSOWA – BUGIRI AREA" , here split only "LOT 1" , ref_url : "https://gpp.ppda.go.ug/public/bid-invitations/tender-notice/87872"

            try:
                lot_details_data.lot_actual_number = page_details.find_element(By.CSS_SELECTOR, 'div:nth-child(2) > div > div > ol > li:nth-child(1) > table > tbody > tr > td:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -LOT DETAILS
        # Onsite Comment -split only lot_title, for-ex."LOT 1: SUPPLY OF HIGH LIFT PUMP SETS FOR BUSOWA – BUGIRI AREA", here split only "SUPPLY OF HIGH LIFT PUMP SETS FOR BUSOWA – BUGIRI AREA" , ref_url : "https://gpp.ppda.go.ug/public/bid-invitations/tender-notice/87872"

            try:
                lot_details_data.lot_title = page_details.find_element(By.CSS_SELECTOR, 'div:nth-child(2) > div > div > ol > li:nth-child(1) > table > tbody > tr > td:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -BID SECURITY AMOUNT
        # Onsite Comment -None

            try:
                lot_details_data.lot_grossbudget_lc = page_details.find_element(By.CSS_SELECTOR, 'li:nth-child(1) tr> td.ng-star-inserted').text
            except Exception as e:
                logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
                pass


                    # Onsite Field -Evaluation process
        # Onsite Comment -split only contract_start_date for ex."From Monday, October 30, 2023 to Monday, November 27, 2023" , here take only "October 30, 2023" , ref_url : "https://gpp.ppda.go.ug/public/bid-invitations/tender-notice/87955"

            try:
                lot_details_data.contract_start_date = page_details.find_element(By.CSS_SELECTOR, 'tr:nth-child(4) td:nth-child(3) > span:nth-child(1)').text
            except Exception as e:
                logging.info("Exception in contract_start_date: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Evaluation process
        # Onsite Comment -split only contract_end_date for ex."From Monday, October 30, 2023 to Monday, November 27, 2023" , here take only "November 27, 2023" , ref_url : "https://gpp.ppda.go.ug/public/bid-invitations/tender-notice/87955"

            try:
                lot_details_data.contract_end_date = page_details.find_element(By.CSS_SELECTOR, 'td:nth-child(3) > span:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in contract_end_date: {}".format(type(e).__name__))
                pass
        
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -DOWNLOAD NOTICE
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'app-bid-invitation-details > div.margin-top-30.ng-star-inserted > div > div > div.mt-4 > div:nth-child(1) span.mat-mdc-button-persistent-ripple.mdc-button__ripple'):
            attachments_data = attachments()
            attachments_data.file_name = 'DOWNLOAD NOTICE'
            # Onsite Field -DOWNLOAD NOTICE
            # Onsite Comment -None
            
            external_url = page_details.find_element(By.CSS_SELECTOR, 'div.mt-4 > div:nth-child(1) span.mat-mdc-button-persistent-ripple.mdc-button__ripple').click()
            file_dwn = Doc_Download.file_download()
            attachments_data.external_url = str(file_dwn[0])
            
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    

        
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    duplicate_check_data = fn.duplicate_check_data_from_previous_scraping(SCRIPT_NAME,MAX_NOTICES_DUPLICATE,notice_data.identifier,previous_scraping_log_check)
    NOTICE_DUPLICATE_COUNT = duplicate_check_data[1]
    if duplicate_check_data[0] == False:
        return
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    duplicate_check_data = fn.duplicate_check_data_from_previous_scraping(SCRIPT_NAME,MAX_NOTICES_DUPLICATE,notice_data.identifier,previous_scraping_log_check)
    NOTICE_DUPLICATE_COUNT = duplicate_check_data[1]
    if duplicate_check_data[0] == False:
        return
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments) 
page_details = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://gpp.ppda.go.ug/#/public/bid-invitations"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,3):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/app-root/app-main-layout/div/div/div/div/div/app-bid-invitations/div/div/div/div/div[6]/div/div'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/app-root/app-main-layout/div/div/div/div/div/app-bid-invitations/div/div/div/div/div[6]/div/div')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/app-root/app-main-layout/div/div/div/div/div/app-bid-invitations/div/div/div/div/div[6]/div/div')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break

                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
                    
                if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                    logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                    break

            if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                break

            try:   
                next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                page_main.execute_script("arguments[0].click();",next_page)
                logging.info("Next page")
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/app-root/app-main-layout/div/div/div/div/div/app-bid-invitations/div/div/div/div/div[6]/div/div'),page_check))
            except Exception as e:
                logging.info("Exception in next_page: {}".format(type(e).__name__))
                logging.info("No next page")
                break
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit() 
    
    output_json_file.copyFinalJSONToServer(output_json_folder)
