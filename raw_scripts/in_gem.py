from gec_common.gecclass import *
import logging
import re
import jsons
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from deep_translator import GoogleTranslator
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
import functions as fn

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "in_gem"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.script_name = 'in_gem'
    
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
    
    # Onsite Field -None
    # Onsite Comment -if any tender have "RA NO." selector is="div.block_header > p:nth-child(3)" then take notice_type=16. otherwise take notice_type=4.

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
        logging.info(notice_data.notice_deadline)
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

    try:
        try:
            local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.card-body > div > div.col-md-4 > div > a').get_attribute('outerHTML').split(' data-content="')[1].split('" data-original-title')[0]
            item = tender_html_element.find_element(By.CSS_SELECTOR, 'div.card-body > div > div.col-md-4 > div:nth-of-type(2)').text
            notice_data.local_title = local_title +' '+ item
            notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
        except:
            notice_data.local_title = WebDriverWait(tender_html_element, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'div.card-body > div > div.col-md-4'))).text
            notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
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
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
        
    try:
        details_page_url=  WebDriverWait(tender_html_element, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'p:nth-child(1) > a:nth-child(1)'))).get_attribute('href')
        fn.load_page(page_details, details_page_url)
        for single_record_org in page_details.find_elements(By.CSS_SELECTOR, 'div.border.block:nth-child(2) div.col-block:nth-child(4) p > span'):
            customer_details_data = customer_details()
            
            # Onsite Field -Department Name And Address:
            # Onsite Comment -All  buyers name merge from "Department Name And Address: ", each org_name should be  "/" seperated.

            try:
                if '' != single_record_org.text and single_record_org.text is not None:
                    customer_details_data.org_name = single_record_org.text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
            
            try:
                customer_details_data.contact_person = page_details.find_element(By.CSS_SELECTOR, 'div:nth-child(1) div.border.block:nth-child(2) div.col-block:nth-child(3) p:nth-child(1) > span:nth-child(2)').text
            except Exception as e:
                pass
            try:
                customer_details_data.org_address = page_details.find_element(By.CSS_SELECTOR, 'div.border.block:nth-child(2) div.col-block:nth-child(3) p:nth-child(2) > span:nth-child(2)').text
            except Exception as e:
                pass
            try:
                customer_details_data.org_email = fn.get_email(page_details.find_element(By.CSS_SELECTOR, 'div.border.block:nth-child(2) div.col-block:nth-child(3) p:nth-child(2) > span:nth-child(2)').text)
            except:
                pass
           
            customer_details_data.org_country = 'IN'
            customer_details_data.org_language = 'EN'
            
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except:
        try:              
            for single_record_org in tender_html_element.find_element(By.CSS_SELECTOR, 'div.card-body > div > div.col-md-5 > div:nth-child(2)').text.split('\n'):
                customer_details_data = customer_details()
                
                # Onsite Field -Department Name And Address:
                # Onsite Comment -All  buyers name merge from "Department Name And Address: ", each org_name should be  "/" seperated.

                try:
                    if '' != single_record_org and single_record_org is not None:
                        customer_details_data.org_name = single_record_org
                except Exception as e:
                    logging.info("Exception in org_name: {}".format(type(e).__name__))
                    pass
            
                customer_details_data.org_country = 'IN'
                customer_details_data.org_language = 'EN'
                customer_details_data.customer_details_cleanup()
                notice_data.customer_details.append(customer_details_data)
        except Exception as e:
            logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
            pass
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
    urls = ["https://bidplus.gem.gov.in/all-bids"] 
    for url in urls:
        
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,50):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'div.card'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.card')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.card')))[records]
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'div.card'),page_check))
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
