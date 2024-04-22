from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "za_ecdpw_ca"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn
import gec_common.Doc_Download
from selenium.webdriver.support.ui import Select



#Note:Open site the go to "All Statuses" select to "Awarded" then grab the data



NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "za_ecdpw_ca"
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
    notice_data.script_name = 'za_ecdpw_ca'
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'ZA'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'ZAR'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'EN'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_type = 7
    
    # Onsite Field -Bid Number
    # Onsite Comment -Note:Splite notice_no after "Bid Number:" this keywords

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(2) > div').text.split('Bid Number: ')[1].split('\n')[0]
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -TENDER DETAILS
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(2) > div').text.split('Region: ')[0]
        notice_data.notice_title =  notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -TENDER DATES
    # Onsite Comment -Note:Splite publish_date after "Date Advertised:" this keyword

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "tr > td:nth-child(3)").text.split('Date Advertised: ')[1].split('\n')[0]
        publish_date = re.findall('\d{4}-\d+-\d+ \d+:\d+:\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%Y-%m-%d %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
#     # Onsite Field -None
#     # Onsite Comment -None
    notice_data.notice_url = 'https://www.ecdpw.gov.za/tenders/'
    
# # Onsite Field -None
# # Onsite Comment -None

    try:              
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, 'tr > td:nth-child(4) > a'):
            attachments_data = attachments()
            attachments_data.file_name = 'Tender Document'
    #         # Onsite Field -TENDER DOCUMENTS
    #         # Onsite Comment -None

            attachments_data.external_url = single_record.get_attribute('href')


            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
# # Onsite Field -None
# # Onsite Comment -None

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = 'EASTERN CAPE DEPARTMENT OF PUBLIC WORKS'
        customer_details_data.org_parent_id = '7680531'
        customer_details_data.org_country = 'ZA'
        customer_details_data.org_language = 'EN'
    # Onsite Field -Region
    # Onsite Comment -Note:Splite contact_person after this "Region:" keyword

        try:
            customer_details_data.contact_person = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(2) > div').text.split('Region: ')[1].split('\n')[0]
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# # Onsite Field -None
# # Onsite Comment -None

    try:                
        lot_details_data = lot_details()
    # Onsite Field -TENDER DETAILS
    # Onsite Comment -None

        lot_details_data.lot_number = 1
        lot_details_data.lot_title =  notice_data.local_title 
        lot_details_data.lot_title_english = notice_data.local_title 


        award_details_data = award_details()

        # Onsite Field -TENDER DATES
        # Onsite Comment -Note:Splite tender_award_date after "Date Awarded:" this keyword

        award_details_data.award_date = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(3)').text.split('Date Awarded:')[1].split('\n')[0]
        award_details_data.award_date = re.findall('\d{4}-\d+-\d+',award_details_data.award_date)[0]
        award_details_data.award_date = datetime.strptime(award_details_data.award_date,'%Y-%m-%d').strftime('%Y/%m/%d')
        award_details_data.award_details_cleanup()
        lot_details_data.award_details.append(award_details_data)

        lot_details_data.lot_details_cleanup()
        notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    

        
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
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
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.ecdpw.gov.za/tenders/"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        time.sleep(10)
        
        pp_btn = Select(page_main.find_element(By.CSS_SELECTOR,'select#status_filter'))
        pp_btn.select_by_index(3)
        time.sleep(20)
        
        
        for page_no in range(2,20):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="tm-tenders"]/tbody/tr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="tm-tenders"]/tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="tm-tenders"]/tbody/tr')))[records]
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="tm-tenders"]/tbody/tr'),page_check))
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
    output_json_file.copyFinalJSONToServer(output_json_folder)
