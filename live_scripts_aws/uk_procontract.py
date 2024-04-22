from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "uk_procontract"
log_config.log(SCRIPT_NAME)
import re
import jsons
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "uk_procontract"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    
    notice_data.script_name = 'uk_procontract'
    
    notice_data.procurement_method = 2
    
    notice_data.currency = 'GBP'
    
    notice_data.main_language = 'EN'
    
        # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'GB'
    notice_data.performance_country.append(performance_country_data)
    
    
    # Onsite Field -None
    # Onsite Comment -take..... notice type --- "5" for "Expressions of Interest"
    notice_data.notice_type = 4
    
        # Onsite Field -Expression Start
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(3)").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Expression End
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
     # Onsite Field -Title
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
        notice_data.notice_title = notice_data.local_title 
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
 
    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)>a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url


    lot_details_data = lot_details()
    lot_details_data.lot_number = 1
    try:
        lot_details_data.lot_title = notice_data.notice_title
        notice_data.is_lot_default = True
    except Exception as e:
        logging.info("Exception in lot_title: {}".format(type(e).__name__))
        pass


    try:
        lot_details_data.lot_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Description")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in lot_description: {}".format(type(e).__name__))
        pass

    try:
        lot_grossbudget_lc = page_details.find_element(By.XPATH,'//*[contains(text(),"Estimated value")]//following::div[1]').text
        lot_grossbudget_lc = re.sub("[^\d\.\,]", "",lot_grossbudget_lc)
        lot_grossbudget_lc = lot_grossbudget_lc.replace(',','').strip()
        lot_details_data.lot_grossbudget_lc = float(lot_grossbudget_lc)
    except Exception as e:
        logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
        pass

    lot_details_data.lot_details_cleanup()
    notice_data.lot_details.append(lot_details_data)

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#listOfAttachments-Advert_Public > tbody > tr'):
            attachments_data = attachments()
        # Onsite Field -Attachments
        # Onsite Comment -None

            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1) > a').get_attribute('href')
            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text.split(".")[0]
        # Onsite Field -Attachments
        # Onsite Comment -None
            try:
                attachments_data.file_type = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text.split(").")[1]
            except:
                try:
                    attachments_data.file_type = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text.split(".")[1]
                except Exception as e:
                    logging.info("Exception in file_type: {}".format(type(e).__name__))
                    pass

            try:
                attachments_data.file_size = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in file_size: {}".format(type(e).__name__))
                pass

        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass

    try:
        notice_data.grossbudgetlc = lot_details_data.lot_grossbudget_lc
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass

    # Onsite Field -Description
    # Onsite Comment -None

    try:
        notice_data.notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),"Description")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Description")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass

    # Onsite Field -Opportunities
    # Onsite Comment -None

    try:
        notice_data.document_type_description = 'Opportunities'
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Estimated value
    # Onsite Comment -None

    try:
        notice_data.est_amount = notice_data.grossbudgetlc
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass

    
    # Onsite Field -Opportunity Id
    # Onsite Comment -None

    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"Opportunity Id")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#sticky-footer-helper > main').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -None

    customer_details_data = customer_details()
    customer_details_data.org_country = 'GB'
    customer_details_data.org_language = 'EN'

    try:
        customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Buyer")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in org_name: {}".format(type(e).__name__))
        pass

        # Onsite Field -Email
    # Onsite Comment -None

    try:
        customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Email")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in org_email: {}".format(type(e).__name__))
        pass
        
    # Onsite Field -Address
    # Onsite Comment -None

    try:
        customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Address")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in org_address: {}".format(type(e).__name__))
        pass

    # Onsite Field -Telephone
    # Onsite Comment -None

    try:
        customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Telephone")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in org_phone: {}".format(type(e).__name__))
        pass

    # Onsite Field -Contact
    # Onsite Comment -None

    try:
        customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Contact")]//following::div[6]').text
    except Exception as e:
        logging.info("Exception in contact_person: {}".format(type(e).__name__))
        pass

        # Onsite Field -Region(s) of supply
        # Onsite Comment -None

    try:
        customer_details_data.org_city = page_details.find_element(By.XPATH, '//*[contains(text(),"Region")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in org_city: {}".format(type(e).__name__))
        pass

    customer_details_data.customer_details_cleanup()
    notice_data.customer_details.append(customer_details_data)
 
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
page_details = fn.init_chrome_driver(arguments) 
page_main = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    for page_no in range(1,57):
        url = 'https://procontract.due-north.com/Opportunities/Index?Page='+str(page_no)+'&PageSize=10&SortColumn=ExpressionStartDate&SortDirection=Descending&ResultFilterHistoryId=00000000-0000-0000-0000-000000000000&TabName=opportunities'
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="opportunitiesGrid"]/tbody/tr')))
        length = len(rows)
        for records in range(0,length):
            tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="opportunitiesGrid"]/tbody/tr')))[records]
            extract_and_save_notice(tender_html_element)
            if notice_count >= MAX_NOTICES:
                break
                
                if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                    logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                    break

            if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                break

    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit() 
    output_json_file.copyFinalJSONToServer(output_json_folder)
    
