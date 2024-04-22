from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "bh_tenderboard"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from deep_translator import GoogleTranslator
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn
import gec_common.Doc_Download
from selenium.webdriver.common.action_chains import ActionChains

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "bh_tenderboard"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'bh_tenderboard'
   
    notice_data.main_language = "EN"
  
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'BH'
    notice_data.performance_country.append(performance_country_data)
   
    notice_data.procurement_method = 2
  
    notice_data.currency = 'BHD'
   
    notice_data.notice_type = 4
    
    # Onsite Field -No./Tender Subject
    # Onsite Comment -split the data from tender_html_page

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, '#paging-container a > span').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -No./Tender Subject
    # Onsite Comment -specified selector selects "notice_no" and "local_title"  you have to select only 1 value ---  for ex. "TPC-1930-2023 Provision of Trend Micro Support Renewal",  here split only "Provision of Trend Micro Support Renewal"

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, '#paging-container a').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Closing Date
    # Onsite Comment -split the data from tender_html_page

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "#paging-container > div > div> div:nth-child(7)").text
        notice_deadline = re.findall('\d+ \w+,\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d %b,%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -No./Tender Subject
    # Onsite Comment -inspect url for detail page , url ref = "https://www.tenderboard.gov.bh/TenderDetails/?id=110/2023/TWR%20(TPC-1930-2023)"

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, '#paging-container a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    time.sleep(6)
  
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'section.tender-details > div').get_attribute("outerHTML")                     
    except:
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Tender Description")]//following::p[1]').text
    except Exception as e:
        logging.info("Exception in Local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Tender Description
    # Onsite Comment -excluding the "Local_title /  Local_description "all fields should be in English,      split the data from detail_page

    try:
        notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),"Tender Description")]//following::p[1]').text
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_summary_english)
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Initial Bond
    # Onsite Comment -split the data from detail_page

    try:
        notice_data.earnest_money_deposit = page_details.find_element(By.XPATH, '//*[contains(text(),"Initial Bond")]//following::dd[1]').text
    except Exception as e:
        logging.info("Exception in earnest_money_deposit: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Tender Fees
    # Onsite Comment -split the data from detail_page

    try:
        notice_data.document_cost = page_details.find_element(By.XPATH, '//*[contains(text(),"Tender Fees")]//following::dd[1]').text
    except Exception as e:
        logging.info("Exception in document_cost: {}".format(type(e).__name__))
        pass

    # Onsite Field -Publish Date
    # Onsite Comment -split the publish_date from detail_page

    try:
        publish_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Publish Date")]//following::dd[1]').text.split(",")[1]
        publish_date = re.findall('\d+ \w+ \d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d %B %Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Contract Duration
    # Onsite Comment -split the data from detail_page

    try:
        notice_data.contract_duration = page_details.find_element(By.XPATH, '//*[contains(text(),"Contract Duration")]//following::dd[1]').text
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Opening Date
    # Onsite Comment -split the data from detail_page

    try:
        document_opening_time = page_details.find_element(By.XPATH, '//*[contains(text(),"Opening Date")]//following::dd[1]').text.split(",")[1]
        document_opening_time = re.findall('\d+ \w+ \d{4}',document_opening_time)[0]
        notice_data.document_opening_time = datetime.strptime(document_opening_time,'%d %B %Y').strftime('%Y-%m-%d')
    except Exception as e:
        logging.info("Exception in document_opening_time: {}".format(type(e).__name__))
        pass                                                                                            
                                                                                                 
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'BH'
        customer_details_data.org_language = 'EN'
        # Onsite Field -Issued by
        # Onsite Comment -split the data from detail_page

        customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Issued by")]//following::dd[1]').text
        
        # Onsite Field -Inquiries
        # Onsite Comment -split the data from detail_page

        try:
            customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Inquiries")]//following::strong[2]').text
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass
        
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

# Onsite Field -TECHNICAL EVALUATION (PART II): SCORING CRITERIA  //*[contains(text(),"SCORING CRITERIA")]//following::table[1]
# Onsite Comment -ref_url for page_detail : "https://www.tenderboard.gov.bh/TenderDetails/?id=111/2023/TWR%20(TPC-1907-2023)"

    try:
        notice_text=page_details.find_element(By.CSS_SELECTOR, 'section.tender-details > div').text
        data=notice_text.split('·         ')
        for data1 in data[1:]:
            tender_criteria_data = tender_criteria()

            tender_criteria_data.tender_criteria_title = data1.split("Evaluation")[0].strip()
        
            tender_criteria_weight = data1.split("(")[1].split("%")[0]
            tender_criteria_data.tender_criteria_weight=int(tender_criteria_weight)
        
            tender_criteria_data.tender_criteria_cleanup()
            notice_data.tender_criteria.append(tender_criteria_data)
    except Exception as e:
        logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
        pass

    try:              
        attachments_data = attachments()
        # Onsite Field -None
        # Onsite Comment -download the documents from detail_page

        attachments_data.file_name = "Download"

        attachments_data.file_type = "PDF"

        # Onsite Field -None
        # Onsite Comment -download the documents from detail_page

        external_url = page_details.find_element(By.CSS_SELECTOR, '#cphBaseBody_CphInnerBody_lnkBtnDwnld > i').click()
        file_dwn = Doc_Download.file_download()
        attachments_data.external_url = str(file_dwn[0])
        time.sleep(5)
        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass        
            
        
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) + str(notice_data.publish_date) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    duplicate_check_data = fn.duplicate_check_data_from_previous_scraping(SCRIPT_NAME,MAX_NOTICES_DUPLICATE,notice_data.identifier,previous_scraping_log_check)
    NOTICE_DUPLICATE_COUNT = duplicate_check_data[1]
    if duplicate_check_data[0] == False:
        return
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body  #page > header > div.nav-warp.nav-warp-h2 > div > div > div > div > nav > ul > li:nth-child(1) > a
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments) 
page_details = Doc_Download.page_details
action = ActionChains(page_main)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)

    urls = ["https://www.tenderboard.gov.bh/Tenders/Public%20Tenders/"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        time.sleep(5)
        
        try:
            element=page_main.find_element(By.CSS_SELECTOR,'div.nav-warp.nav-warp-h2 > div > div > div > div > nav > ul > li:nth-child(1) > a') # or your another selector here
            action.move_to_element(element)
            action.perform()
            page_main.find_element(By.CSS_SELECTOR, '#siteNav > li:nth-child(1) > a').click()
            time.sleep(5)
        except:
            pass

        try:
            for page_no in range(2,20):
                page_check = WebDriverWait(page_main, 80).until(EC.presence_of_element_located((By.XPATH,'//*[@id="paging-container"]/div[1]/div[3]'))).text
                rows = WebDriverWait(page_main, 80).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="paging-container"]/div[1]/div')))
                length = len(rows)
                for records in range(2,length):
                    tender_html_element = WebDriverWait(page_main, 80).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="paging-container"]/div[1]/div')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
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
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="paging-container"]/div'+str(page_no)+'/div[3]'),page_check))
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
