from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "in_gembidra_spn"
log_config.log(SCRIPT_NAME)
import re
import jsons
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn
import time

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 20000
notice_count = 0
tnotice_count = 0
SCRIPT_NAME = "in_gembidra_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    global tnotice_count
    notice_data = tender()
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.script_name = 'in_gembidra_spn'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'EN'
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'INR'
    notice_data.notice_url = url
    notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    # Onsite Field -None
    # Onsite Comment -if any tender have "RA NO." selector is="div.block_header > p:nth-child(3)" then take notice_type=16. otherwise take notice_type=4.

    try:              
        for single_record in tender_html_element.find_element(By.CSS_SELECTOR, 'div.block_header').find_elements(By.CSS_SELECTOR, 'div.block_header > p.bid_no > a'):
            attachments_data = attachments()
        # Onsite Field -None
        # Onsite Comment -None
            attachments_data.file_name = single_record.get_attribute('href').replace('https://bidplus.gem.gov.in/','').split('/')[0]   
        # Onsite Field -None
        # Onsite Comment -None
            attachments_data.external_url = single_record.get_attribute('href')
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
            if 'https://bidplus.gem.gov.in/showbidDocument' in attachments_data.external_url:
                quantity = tender_html_element.find_element(By.CSS_SELECTOR, 'div.card-body > div > div.col-md-4 > div:nth-of-type(2)').text
                try:
                    local_title = fn.gem_pdf(attachments_data.external_url)
                except:
                    try:
                        local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div > div.col-md-4 > div:nth-child(1) > a').get_attribute('data-content')
                    except:
                        local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div > div.col-md-4 > div:nth-child(1)').text
                notice_data.local_title = local_title + ' ' + quantity
                notice_data.notice_title = notice_data.local_title
                logging.info(notice_data.notice_title)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
        
    try:
        if 'RA NO' in tender_html_element.find_element(By.CSS_SELECTOR, "div.block_header > p:nth-child(3)").text:
            notice_data.notice_type = 16
        else:
            notice_data.notice_type = 4
    except:       
            notice_data.notice_type = 4
    
    # Onsite Field -Start Date:
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div > div.col-md-3 > div:nth-child(1) > span").text
        publish_date = re.findall('\d+-\d+-\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d-%m-%Y').strftime('%Y/%m/%d')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -End Date:
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "div > div.col-md-3 > div:nth-child(2) > span").text
        notice_deadline = re.findall('\d+-\d+-\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d-%m-%Y').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -BID NO:
    # Onsite Comment -None
    try:
        notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div.block_header > p:nth-child(1)').text
        if 'Bid No.' in notice_no:
            notice_data.notice_no = notice_no.split('Bid No.:')[1].strip()
        elif 'BID NO' in notice_no:
            notice_data.notice_no = notice_no.split('BID NO:')[1].strip()
        else:
            notice_data.notice_no = notice_no
       
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    
    
    # Onsite Field -None
    # Onsite Comment -add "Items:" + "Quantity:" in local_title.grab "data-content" from this attribute 


    # Onsite Field -None
    # Onsite Comment -add "Items:" + "Quantity:" in notice_summary_english.grab "data-content" from this attribute. 

    try:              
        lot_details_data = lot_details()
        lot_details_data.lot_number = 1
        # Onsite Field -None
        # Onsite Comment -    # Onsite Field -None
        # Onsite Comment -add "Items:" + "Quantity:" in lot_title.grab "data-content" from this attribute.

        try:
            lot_details_data.lot_title = notice_data.local_title
            notice_data.is_lot_default = True
        except Exception as e:
            logging.info("Exception in lot_title: {}".format(type(e).__name__))
            pass
    
        # Onsite Field -None
        # Onsite Comment -add "Items:" + "Quantity:" in lot_description.grab "data-content" from this attribute.

        try:
            lot_details_data.lot_description =  notice_data.local_title
        except Exception as e:
            logging.info("Exception in lot_description: {}".format(type(e).__name__))
            pass
        # Onsite Field -Quantity:
        # Onsite Comment -None

        try:
            lot_details_data.lot_quantity = int(tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-md-4 > div:nth-child(2)').text.replace('Quantity: ',''))
        except Exception as e:
            logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
            pass
        
        lot_details_data.lot_details_cleanup()
        notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
    # Onsite Field -None
    # Onsite Comment -None
    
        
    try:
        notice_data.notice_url =  WebDriverWait(tender_html_element, 180).until(EC.presence_of_element_located((By.CSS_SELECTOR,'div > div.col-md-4.pull-right > p > a:nth-child(1)'))).get_attribute('href')
        fn.load_page(page_details, notice_data.notice_url)
        logging.info(notice_data.notice_url)
        customer_details_data = customer_details()

        # Onsite Field -Department Name And Address:
        # Onsite Comment -All  buyers name merge from "Department Name And Address: ", each org_name should be  "/" seperated.

        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div.card-body > div > div.col-md-5 > div:nth-child(2)').text.split('\n')[0]


        try:
            customer_details_data.contact_person = page_details.find_element(By.CSS_SELECTOR, 'div:nth-child(1) div.border.block:nth-child(2) div.col-block:nth-child(3) p:nth-child(1) > span:nth-child(2)').text
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass
        try:
            customer_details_data.org_address = page_details.find_element(By.CSS_SELECTOR, 'div.border.block:nth-child(2) div.col-block:nth-child(3) p:nth-child(2) > span:nth-child(2)').text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass
        try:
            customer_details_data.org_email = fn.get_email(page_details.find_element(By.CSS_SELECTOR, 'div.border.block:nth-child(2) div.col-block:nth-child(3) p:nth-child(2) > span:nth-child(2)').text)
        except:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass

        customer_details_data.org_country = 'IN'
        customer_details_data.org_language = 'EN'

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except:
        try:
            customer_details_data = customer_details()

            # Onsite Field -Department Name And Address:
            # Onsite Comment -All  buyers name merge from "Department Name And Address: ", each org_name should be  "/" seperated.
            customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div.card-body > div > div.col-md-5 > div:nth-child(2)').text.split('\n')[0]

            customer_details_data.org_country = 'IN'
            customer_details_data.org_language = 'EN'
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
        except Exception as e:
            logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
            pass
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    tnotice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments) 
page_details = fn.init_chrome_driver(arguments) 

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://bidplus.gem.gov.in/all-bids"] 
    for url in urls:
        fn.load_page(page_main, url, 100)
        logging.info('----------------------------------')
        logging.info(url)
        WebDriverWait(page_main, 180).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="bidrastatus"]'))).click()
        time.sleep(5)
        WebDriverWait(page_main, 180).until(EC.element_to_be_clickable((By.XPATH,"//button[@id='currentSort']"))).click()
        time.sleep(5)
        WebDriverWait(page_main, 180).until(EC.element_to_be_clickable((By.XPATH,"//a[@id='Bid-Start-Date-Latest']"))).click()
        time.sleep(5)
        try:
            for page_no in range(2,500):
                page_check = WebDriverWait(page_main, 180).until(EC.presence_of_element_located((By.CSS_SELECTOR,'div.card'))).text
                rows = WebDriverWait(page_main, 180).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.card')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 180).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.card')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
    
                    if notice_count == 50:
                        output_json_file.copyFinalJSONToServer(output_json_folder)
                        output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
                        notice_count = 0
    
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 180).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 180).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'div.card'),page_check))
                except Exception as e:
                    logging.info("Exception in next_page: {}".format(type(e).__name__))
                    logging.info("No next page")
                    break
        except:
            logging.info('No new record')
            break
    logging.info("Finished processing. Scraped {} notices".format(tnotice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)
