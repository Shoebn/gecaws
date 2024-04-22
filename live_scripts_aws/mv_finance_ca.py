from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "mv_finance_ca"
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

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "mv_finance_ca"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'mv_finance_ca'
    notice_data.main_language = 'EN'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'MV'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'MVR'
    notice_data.notice_type = 7
    notice_data.document_type_description = '"Awarded Projects"'
    
    # Onsite Field -PROCUREMENT APPROACH
    # Onsite Comment -("National Competitive Bidding (NCB) = 0" , "International Competitive Bidding (ICB) = 1")

    try:
        procurement_method = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        if 'National Competitive Bidding (NCB)' in procurement_method:
            notice_data.procurement_method = 0
        elif 'International Competitive Bidding (ICB)' in procurement_method:
            notice_data.procurement_method = 1
    except Exception as e:
        logging.info("Exception in procurement_method: {}".format(type(e).__name__))
        pass

    # Onsite Field -PROJECT TYPE.
    # Onsite Comment -None

    try:
        notice_data.contract_type_actual = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
        if "Non- Consulting Services" in notice_data.contract_type_actual:
            notice_data.notice_contract_type ="Non consultancy"
        elif "Consulting Services" in notice_data.contract_type_actual:
            notice_data.notice_contract_type ="Consultancy"
        elif "Works" in notice_data.contract_type_actual:
            notice_data.notice_contract_type ="Works"
        elif "Goods" in notice_data.contract_type_actual:
            notice_data.notice_contract_type ="Supply"
        else:
            pass
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass
 
    # Onsite Field -PROCUREMENT NO
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -PROCUREMENT NAME
    # Onsite Comment -

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -PROJECT SECTOR
    # Onsite Comment -None

    try:
        notice_data.category = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
    except Exception as e:
        logging.info("Exception in category: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -AGENCY
    # Onsite Comment -None

    try:              
        customer_details_data = customer_details()
    # Onsite Field -AGENCY
    # Onsite Comment -None

        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(6)').text

        customer_details_data.org_country = 'MV'
        customer_details_data.org_language = 'EN'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    # Onsite Field -PROCUREMENT NAME
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4) a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url

            
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'body > div.flex-grow.en').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
     # Onsite Field -PUBLISHED DATE
    # Onsite Comment -None

    try:
        publish_date = page_details.find_element(By.CSS_SELECTOR, "div.container.grid.grid-cols-1.px-6.pb-24.mx-auto  span  span").text
        publish_date = re.findall('\d+ \w+ \d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d %B %Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
        
    # Onsite Field -Ref:
    # Onsite Comment -None

    try:
        notice_data.related_tender_id = page_details.find_element(By.CSS_SELECTOR, 'div.container.grid.grid-cols-1 div div.w-full.px-6.py-3 div:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
        pass

    try:
        lot_details_data = lot_details()
        lot_details_data.lot_number = 1
        # Onsite Field -PROCUREMENT NAME
        # Onsite Comment -

        lot_details_data.lot_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text

        try:
            award_details_data = award_details()

            # Onsite Field -AWARDED PARTY
            # Onsite Comment -

            award_details_data.bidder_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(7)').text

            # Onsite Field -
            # Onsite Comment -AWARDED AMOUNT
            try:
                grossawardvaluelcc = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(8)').text
                grossawardvaluelc1 = re.sub("[^\d\.\,]", "",grossawardvaluelcc)
                grossawardvaluelc = grossawardvaluelc1.replace(',','').strip()
                award_details_data.grossawardvaluelc = float(grossawardvaluelc)
            except Exception as e:
                logging.info("Exception in grossawardvaluelc: {}".format(type(e).__name__))
                pass

            # Onsite Field -
            # Onsite Comment -AWARDED DURATION	
            try:
                award_details_data.contract_duration = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(9)').text
            except Exception as e:
                logging.info("Exception in contract_duration: {}".format(type(e).__name__))
                pass
            # Onsite Field -
            # Onsite Comment -AWARDED DURATION	
            try:
                award_date = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(10)').text
                award_date = re.findall('\d+/\d+/\d{4}',award_date)[0]
                award_details_data.award_date = datetime.strptime(award_date,'%d/%m/%Y').strftime('%Y/%m/%d')
            except:
                pass
            
            
            award_details_data.award_details_cleanup()
            lot_details_data.award_details.append(award_details_data)
        except Exception as e:
            logging.info("Exception in award_details: {}".format(type(e).__name__))
            pass
        if lot_details_data.award_details != []:
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.container.grid.grid-cols-1.px-6 > div.flex.flex-col.space-y-6 div > div.flex.flex-col > a'):
            attachments_data = attachments()
        # Onsite Field -Attachments
        # Onsite Comment -take only file_name for ex."Bidding Document.docx" , here take only "Bidding Document"

            attachments_data.file_name = single_record.text.split('.')[0].strip()

            attachments_data.external_url = single_record.get_attribute("href")
            try:
                attachments_data.file_type = single_record.text.split('.')[-1].strip()
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
            
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) + str(notice_data.publish_date) +  str(notice_data.notice_url) 
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
    urls = ["https://www.finance.gov.mv/public-procurement/awarded-projects"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)

        try:
            for page_no in range(2,5):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[1]/div[2]/div/div[2]/div[2]/div[1]/table/tbody/tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/div[2]/div/div[2]/div[2]/div[1]/table/tbody/tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/div[2]/div/div[2]/div[2]/div[1]/table/tbody/tr')))[records]
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
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/div[1]/div[2]/div/div[2]/div[2]/div[1]/table/tbody/tr'),page_check))
                except Exception as e:
                    logging.info("Exception in next_page: {}".format(type(e).__name__))
                    logging.info("No next page")
                    break
        except:
            logging.info("No new record")
            break
            
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit() 
    output_json_file.copyFinalJSONToServer(output_json_folder)
