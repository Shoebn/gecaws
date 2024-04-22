from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "bh_tenderboard_ca"
log_config.log(SCRIPT_NAME)
import jsons
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "bh_tenderboard_ca"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'bh_tenderboard_ca'
    
    notice_data.main_language = 'EN'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'BH'
    notice_data.performance_country.append(performance_country_data)

    notice_data.procurement_method = 2
    
    notice_data.currency = 'BHD'

    notice_data.notice_type = 7
    
   
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(2) > span > a').get_attribute("href")     
        fn.load_page(page_details,notice_data.notice_url,180)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, '.resultstable > div a span').text
    except:
        try:
            notice_data.notice_no = notice_data.notice_url.split('(')[1].split(')')[0]
        except Exception as e:
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass
    try:
        local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(2) > span').text
        notice_data.local_title = local_title.split(notice_data.notice_no)[1]
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "#OpenedTenderDetailsBlock > div > div:nth-child(4)").text  
        notice_data.publish_date = datetime.strptime(publish_date,'%d %b,%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'section.tender-details > div').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')

    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Tender Description")]//following::p[1]').text 
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    try:
        notice_data.notice_summary_english = notice_data.local_description
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass

    try:
        notice_data.related_tender_id = page_details.find_element(By.XPATH, '//*[contains(text(),"Tender Number: ")]//following::span[1]').text
    except Exception as e:
        logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
        pass

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_language = 'EN'
        customer_details_data.org_country = 'BH'
        customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Issued by")]//following::dd[1]').text  
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:              
        lot_details_data = lot_details()
        lot_details_data.lot_number = 1
        lot_details_data.lot_title = page_details.find_element(By.CSS_SELECTOR, 'div.col-md-8 > div > h3').text
        lot_details_data.lot_title_english = lot_details_data.lot_title
        try:
            for single_record in page_details.find_elements(By.XPATH, '//*[@class="table openedtenders"]/div')[1:]:  
                
                status = single_record.find_element(By.XPATH, 'div[5]').text
                if status=='Accepted':
                    award_details_data = award_details()
            
                    award_details_data.bidder_name = single_record.find_element(By.XPATH, 'div[2]').text  

                    grossawardvaluelc = single_record.find_element(By.XPATH, 'div[3]').text
                    grossawardvaluelc = grossawardvaluelc.split('BHD')[1]
                    award_details_data.grossawardvaluelc = float(grossawardvaluelc.replace(',','').strip())

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
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments) 
page_details = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.tenderboard.gov.bh/Tenders/Opened%20Bids/"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(1,5):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="OpenedTenderDetailsBlock"]/div[2]'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="OpenedTenderDetailsBlock"]/div')))
                length = len(rows)
                for records in range(1,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="OpenedTenderDetailsBlock"]/div')))[records]
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
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,'>>'))).click()
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="OpenedTenderDetailsBlock"]/div[2]'),page_check))
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
