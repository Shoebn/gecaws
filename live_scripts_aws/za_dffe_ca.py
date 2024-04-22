#check comments for additional changes
#1)for bidder name
# As discussed with shoeib added below condition .. (1) if lot avaialble than condition 
# lot_title ="blank "and award_details ="blank" []
# than lot_details =[]
# (2) if lots not avaible than
# award_details= []
# and lot_details= []


from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "za_dffe_ca"
log_config.log(SCRIPT_NAME)
import jsons
from datetime import date, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn
import gec_common.Doc_Download
import re

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "za_dffe_ca"
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
    notice_data.script_name = 'za_dffe_ca'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'EN'
    
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
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_type = 7
    
    # Onsite Field -Bid no.
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Description
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, ' td:nth-child(3)').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.publish_date = threshold
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        lot_details_data = lot_details()
    # Onsite Field -Description
    # Onsite Comment -None
        lot_details_data.lot_number=1
        lot_details_data.lot_title = tender_html_element.find_element(By.CSS_SELECTOR, ' td:nth-child(3)').text


    # Onsite Field -None
    # Onsite Comment -None

        award_details_data = award_details()

        # Onsite Field -Orgaization/Company
        # Onsite Comment -split before "Amount:"

        bidder_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
        if 'Amount' in bidder_name:
            award_details_data.bidder_name=bidder_name.split('Amount')[0]
        else:
            award_details_data.bidder_name=bidder_name

        # Onsite Field -Orgaization/Company
        # Onsite Comment -split after "Amount:"
        try:
            grossawardvaluelc = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text.split('Amount:')[1]
            award_details_data.grossawardvaluelc=re.findall('[0-9\s\,\.]+',grossawardvaluelc)[1]
            if ',' in award_details_data.grossawardvaluelc:
                award_details_data.grossawardvaluelc=award_details_data.grossawardvaluelc.replace(',','')
            if ' ' in award_details_data.grossawardvaluelc:
                award_details_data.grossawardvaluelc=award_details_data.grossawardvaluelc.replace(' ','')
            award_details_data.grossawardvaluelc = float(award_details_data.grossawardvaluelc)
        except:
            pass

        award_details_data.award_details_cleanup()
        lot_details_data.award_details.append(award_details_data)


        lot_details_data.lot_details_cleanup()
        notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
# # Onsite Field -None
# # Onsite Comment -None

    try:              
        attachments_data = attachments()
    # Onsite Field -Description
    # Onsite Comment -None

        attachments_data.file_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text

    # Onsite Field -Description
    # Onsite Comment -None

        attachments_data.external_url = tender_html_element.find_element(By.CSS_SELECTOR, ' td:nth-child(3) > a').get_attribute('href')

        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass


# # Onsite Field -None
# # Onsite Comment -None

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'ZA'
        customer_details_data.org_language = 'EN'
        customer_details_data.org_name = 'Department: Forestry, Fisheries and the Environment REPUBLIC OF SOUTH AFRICA'
        customer_details_data.org_parent_id = '7784527'
        customer_details_data.org_phone = '+27 86 111 2468'
        customer_details_data.org_email = 'callcentre@dffe.gov.za'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    notice_data.notice_url = 'https://www.dffe.gov.za/tenders'
    notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
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
    urls = ["https://www.dffe.gov.za/tenders"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,10):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#quicktabs-tabpage-tenders-1 > div:nth-child(2) > div > div > table > tbody > tr:nth-child(1)'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#quicktabs-tabpage-tenders-1 > div:nth-child(2) > div > div > table > tbody > tr:nth-child(1)')))
            length = len(rows)
            for records in range(1,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#quicktabs-tabpage-tenders-1 > div:nth-child(2) > div > div > table > tbody > tr:nth-child(1)')))[records]
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#quicktabs-tabpage-tenders-1 > div:nth-child(2) > div > div > table > tbody > tr:nth-child(1)'),page_check))
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
