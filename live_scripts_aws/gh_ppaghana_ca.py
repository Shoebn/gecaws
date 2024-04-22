from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "gh_ppaghana_ca"
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
SCRIPT_NAME = "gh_ppaghana_ca"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.script_name = 'gh_ppaghana_ca'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'EN'
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'GH'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -Contract Currency:
    # Onsite Comment -None


    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_type = 7
    
    # Onsite Field -Tender Type:
    # Onsite Comment -if NCT then = procurment method : 0 , if ICT then = procurment method : 1 )
    

    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div > div> div.list-desc').text
        notice_data.notice_title = notice_data.local_title 
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Contract Date:
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div.list-date").text.split('Contract Date:')[1].split(' Completion Date :')[0]
        publish_date = re.findall('(\d{1,2})(st|nd|rd|th) (\w+), (\d{4})',publish_date)
        day, suffix, month, year = publish_date[0]
        month_number = datetime.strptime(month, '%B').month
        publish_date_str = f"{day}/{month_number}/{year}"
        notice_data.publish_date = datetime.strptime(publish_date_str, '%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.document_type_description = 'Contracts'
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.list-title > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url

    try:
        notice_data.currency = page_details.find_element(By.XPATH, '//*[contains(text(),"Contract Currency:")]//following::dd[1]').text.upper()
    except Exception as e:
        logging.info("Exception in currency: {}".format(type(e).__name__))
        pass
    
#     # Onsite Field -None
#     # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.col-md-9').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
#     
#     # Onsite Field -Tender Package No:
#     # Onsite Comment -None

    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"Tender Package No:")]//following::dd[1]').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Tender Description:")]//following::dd[1]').text
        notice_data.notice_summary_english = notice_data.local_description
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    

    try:
        procurement_method = page_details.find_element(By.CSS_SELECTOR, 'div.col-md-9 dl:nth-child(3) > dd').text
        if '-' in procurement_method:
            pass
        else:
            if 'NCT' in procurement_method:
                notice_data.procurement_method = 0
            elif 'ICT' in procurement_method:
                notice_data.procurement_method = 1
                
    except Exception as e:
        logging.info("Exception in procurement_method: {}".format(type(e).__name__))
        pass
    
# # Onsite Field -None
# # Onsite Comment -None

    try:              

        customer_details_data = customer_details()
    # Onsite Field -None
    # Onsite Comment -None

        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div > div.list-agency').text

        customer_details_data.org_country = 'GH'
        customer_details_data.org_language = 'EN'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# # Onsite Field -None
# # Onsite Comment -None

    try:              
        lot_details_data = lot_details()

        lot_details_data.lot_number = 1
        lot_details_data.lot_title = notice_data.local_title
        notice_data.is_lot_default = True

        try:
            award_details_data = award_details()

            # Onsite Field -Contract Awarded To:
            # Onsite Comment -None

            award_details_data.bidder_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Contract Awarded To:")]//following::dd[1]').text

        # Onsite Field -Contract Date:
        # Onsite Comment -None

            award_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Contract Date:")]//following::dd[1]').text
            award_date = re.findall('(\d{1,2})(st|nd|rd|th) (\w+), (\d{4})',award_date)
            day, suffix, month, year = award_date[0]
            month_number = datetime.strptime(month, '%B').month
            award_date = f"{day}/{month_number}/{year}"
            award_details_data.award_date  = datetime.strptime(award_date , '%d/%m/%Y').strftime('%Y/%m/%d')

        # Onsite Field -Contract Award Price:
        # Onsite Comment -None

            grossawardvaluelc = page_details.find_element(By.XPATH, '//*[contains(text(),"Contract Award Price:")]//following::dd[1]').text
            grossawardvaluelc  = re.sub("[^\d\.\,]","",grossawardvaluelc )
            award_details_data.grossawardvaluelc = float(grossawardvaluelc)

            award_details_data.award_details_cleanup()
            lot_details_data.award_details.append(award_details_data)
        except Exception as e:
            logging.info("Exception in award_details: {}".format(type(e).__name__))
            pass

        lot_details_data.lot_details_cleanup()
        notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
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
page_details = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["http://tenders.ppa.gov.gh/contracts"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(2,5):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[1]/section[2]/div/div/div/div/div[2]/div/div'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/section[2]/div/div/div/div/div[2]/div/div')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/section[2]/div/div/div/div/div[2]/div/div')))[records]
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
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/div[1]/section[2]/div/div/div/div/div[2]/div/div'),page_check))
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
