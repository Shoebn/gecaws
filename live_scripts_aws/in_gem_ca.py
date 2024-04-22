from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "in_gem_ca"
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

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "in_gem_ca"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

#after opening the url select "Bid/RA Status = div.col-md-2.sidefilter > div:nth-child(6)" then select " 
#Bid /RA Awarded = div:nth-child(22) > label" then select "Sort by: 
#Bid Start Date: Latest First = div.col-md-6 > div > button"
#excluding the "Local_title /  Local_description "all fields should be in English


    # Onsite Field -None
    # Onsite Comment -None
    notice_data.script_name = 'in_gem_ca'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'EN'
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'INR'

    notice_data.procurement_method = 2

    notice_data.notice_type = 7
    
    # Onsite Field -End Date:
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div > div.col-md-3 > div:nth-child(2) > span").text
        try:
            publish_date = re.findall('\d+-\d+-\d{4} \d:\d{2}',publish_date)[0]
        except:
            publish_date = re.findall('\d+-\d+-\d{4} \d{2}:\d{2}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d-%m-%Y %H:%S').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div.block_header > p:nth-child(1)').text.split(':')[1].strip()
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass


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
                notice_data.tender_quantity = tender_html_element.find_element(By.CSS_SELECTOR, 'div.card-body > div > div.col-md-4 > div:nth-of-type(2)').text
                try:
                    local_title = fn.gem_pdf(attachments_data.external_url)
                except:
                    try:
                        local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div > div.col-md-4 > div:nth-child(1) > a').get_attribute('data-content')
                    except:
                        local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div > div.col-md-4 > div:nth-child(1)').text
                notice_data.local_title = local_title + ' ' + notice_data.tender_quantity
                notice_data.notice_title = notice_data.local_title

    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass   

    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-md-4.pull-right > p > a:nth-child(1)').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.ID, '#content').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    # Onsite Field -Bid Validity (From End Date):
    # Onsite Comment -1.split contact_duration.	2.eg., here "Bid Validity (From End Date): 180 ( Days)" only take "180 ( Days)" in contact_duration.

    try:
        notice_data.contract_duration = page_details.find_element(By.XPATH, '//*[contains(text(),"Bid Validity (From End Date):")]//following::span[1]').text.split('(')[0]
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass


    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#accordion > div:nth-child(1)'):
            customer_details_data = customer_details()
            customer_details_data.org_country = 'IN'
            customer_details_data.org_language = 'EN'
            
        # Onsite Field -Department Name And Address:
        # Onsite Comment -1.All  buyers name merge from "Department Name And Address: ", each buyer should be  "/" seperated.

            try:
                customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div.card-body > div > div.col-md-5 > div:nth-child(2)').text.replace('\n','/')
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Name:
        # Onsite Comment -1.don't take if only "*" are given.and if " *********** AGRA" is present then only take AGRA. 	 2.reference_url "https://bidplus.gem.gov.in/bidding/bid/getBidResultView/5044870"

            try:
                contact_person = single_record.find_element(By.XPATH, '//*[contains(text(),"Name:")]//following::span[1]').text
                if '***********' in contact_person:
                    pass
                else:
                    customer_details_data.contact_person = contact_person
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass
        # Onsite Field -Address:
        # Onsite Comment -1.don't take if only "*" are given.and if " *********** AGRA" is present then only take AGRA. 	2.reference_url "https://bidplus.gem.gov.in/bidding/bid/getBidResultView/5044870"

            try:
                customer_details_data.org_address = single_record.find_element(By.XPATH, '//*[contains(text(),"Address:")]//following::span[1]').text
                if '***********' in customer_details_data.org_address :
                    customer_details_data.org_address =customer_details_data.org_address.replace('***********','').strip()
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        # Onsite Field -State:
        # Onsite Comment -1.don't take if only "*" are given.

            try:
                customer_details_data.org_state = single_record.find_element(By.XPATH, '//*[contains(text(),"State:")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in org_state: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Organisation:
        # Onsite Comment -1.don't take if only "*" are given.and if " *********** AGRA" is present then only take AGRA.

            try:
                customer_details_data.org_description = single_record.find_element(By.XPATH, '//*[contains(text(),"Organisation:")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in org_description: {}".format(type(e).__name__))
                pass
        
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -1.to take lot_details click on "div:nth-child(2) > div.panel-heading > h4 > a = 2. TECHNICAL EVALUATION" in page_details.
    
    try:              
        lot_quantity = page_details.find_element(By.XPATH,'//*[contains(text(),"Quantity:")]//following::span[1]').text
        WebDriverWait(page_details, 20).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#accordion > div:nth-child(2) > div.panel-heading > h4 > a'))).click()
        time.sleep(5)
        lot_number=1
        for single_record in page_details.find_element(By.CSS_SELECTOR, '#collapseTwo > div').find_elements(By.CSS_SELECTOR, '#collapseTwo > div tr')[1:-1]:

            # Onsite Field -Offered Item
            # Onsite Comment -1.if in "Status = tr > td:nth-child(6)" column "Qualified" is given only then take 
            #lot_title from "Offered Item" column. 	  2.if lot_title is not availabel then take local_title. 	  
            #3.reference_url "https://bidplus.gem.gov.in/bidding/bid/getBidResultView/4308579".


            lot=single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(6)').text
            if 'Qualified' in lot:
                lot_details_data = lot_details()
                lot_details_data.lot_number = lot_number
                try:
                    lot_title = single_record.find_element(By.CSS_SELECTOR, ' td:nth-child(3)').text
                    if '-' in lot_title:
                        lot_details_data.lot_title = notice_data.local_title
                        notice_data.is_lot_default = True
                    else:
                        lot_details_data.lot_title = lot_title
                except Exception as e:
                    lot_details_data.lot_title = notice_data.local_title
                    notice_data.is_lot_default = True
                    logging.info("Exception in lot_title: {}".format(type(e).__name__))
                    pass

            # Onsite Field -Offered Item
            # Onsite Comment -1.if in "Status = tr > td:nth-child(6)" column "Qualified" is given only then take lot_description from "Offered Item" column. 		2.if lot_description is not availabel then take local_title.

                try:
                    lot_details_data.lot_description =notice_data.local_title
                    lot_details_data.lot_description_english =notice_data.local_title
                except Exception as e:
                    logging.info("Exception in lot_description: {}".format(type(e).__name__))
                    pass

            # Onsite Field -Bid Validity (From End Date):
            # Onsite Comment -1.split contact_duration.	      2.eg., here "Bid Validity (From End Date): 180 ( Days)" only take "180 ( Days)" in contact_duration. 	  3.to take contact_duration click on "div:nth-child(1) > div.panel-heading > h4 > a=1.  BID DETAILS" in page_details.

                try:
                    lot_details_data.contract_duration = notice_data.contract_duration 
                except Exception as e:
                    logging.info("Exception in contract_duration: {}".format(type(e).__name__))
                    pass

            # Onsite Field -Quantity:
            # Onsite Comment -1.split lot_quantity. eg., here "Quantity: 1" take only "1" in lot_quantity.

                try:
                    lot_details_data.lot_quantity = float(lot_quantity)
                except Exception as e:
                    logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                    pass

            # Onsite Field -None
            # Onsite Comment -1.to take award_details click on "div:nth-child(2) > div.panel-heading > h4 > a = 2. TECHNICAL EVALUATION" in page_details.

                try:
                    award_details_data = award_details()

                    # Onsite Field -None
                    # Onsite Comment -1.if in "Status = tr > td:nth-child(6)" column "Qualified" is given only then take bidder_name from "Seller Name" column. 	  2.reference_url "https://bidplus.gem.gov.in/bidding/bid/getBidResultView/4308579".
                    award_details_data.bidder_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
                    award_details_data.award_details_cleanup()
                    lot_details_data.award_details.append(award_details_data)
                except Exception as e:
                    logging.info("Exception in award_details: {}".format(type(e).__name__))
                    pass
                lot_number += 1
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
page_details = fn.init_chrome_driver(arguments) 
page_main = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    
    urls = ['https://bidplus.gem.gov.in/bidlists']
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)

        WebDriverWait(page_main, 180).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"div.col-md-2.sidefilter > div:nth-child(6)"))).click()
        time.sleep(5)

        WebDriverWait(page_main, 180).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"div:nth-child(22) > label"))).click()
        time.sleep(5)

        WebDriverWait(page_main, 180).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="currentSort"]'))).click()
        time.sleep(5)

        WebDriverWait(page_main, 180).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"a#Bid-Start-Date-Latest"))).click()
        time.sleep(5)

        try:
            for page_no in range(2,5):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="bidCard"]/div'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="bidCard"]/div')))
                length = len(rows)
                for records in range(1,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="bidCard"]/div')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 180).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    time.sleep(5)
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
