from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "rw_umucyo_ca"
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
SCRIPT_NAME = "rw_umucyo_ca"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"

# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# go to URL : "https://www.umucyo.gov.rw/pt/index.do"  , go to "Annoucement" tab ( selector : "#main_R > h3:nth-child(3)" ) after that click on "Tender Awarded" tab and click on "+"   (selector : "#tabsholder2 > p > a")



# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.script_name = 'rw_umucyo_ca'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'EN'
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'RW'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -None
    # Onsite Comment -
    notice_data.notice_type = 7
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'RWF'


    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2

    # Onsite Field -Title of the tender	
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        notice_data.notice_title =  notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
   
    # Onsite Field -Status
    # Onsite Comment -None
    notice_data.document_type_description = 'List of Publication of Tender Awarded'

     # Onsite Field - Tender reference number	
     # Onsite Comment -

    try:
        notice_data.related_tender_id = tender_html_element.find_element(By.CSS_SELECTOR, ' td:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
        pass
    
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(12)").text.split('~')[0]
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass


    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return


    notice_data.notice_url = "https://www.umucyo.gov.rw/pt/index.do"

    notice_data.notice_text += tender_html_element.get_attribute('outerHTML')

#     # Onsite Field - Total Contract Amount
#     # Onsite Comment - 

    try:
        notice_data.est_amount = tender_html_element.find_element(By.CSS_SELECTOR, ' td:nth-child(10)').text.split(' (')[0]
        notice_data.est_amount  = notice_data.est_amount.replace(',','')
        notice_data.est_amount = float(notice_data.est_amount )
        notice_data.grossbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass

#     # Onsite Field -
#     # Onsite Comment -

    try:              

        customer_details_data = customer_details()
    # Onsite Field - Procuring entity
        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
        customer_details_data.org_country = 'RW'
        customer_details_data.org_language = 'EN'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# # Onsite Field -
# # Onsite Comment -

    try:              
        lot_details_data = lot_details()
        lot_details_data.lot_number=1
    #         # Onsite Field -Title of the tender	
    #         # Onsite Comment -

        lot_details_data.lot_title = tender_html_element.find_element(By.CSS_SELECTOR, ' td:nth-child(3)').text
        lot_details_data.lot_title_english = lot_details_data.lot_title

    #         # Onsite Field -Execution or Delivery period
    #         # Onsite Comment - take only "starting date" for ex."27/11/2023 ~ 27/11/2024" , here take only "27/11/2023"

        try:
            lot_details_data.contract_start_date = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(12)').text.split('~')[0]
            lot_details_data.contract_start_date  = re.findall('\d+/\d+/\d{4}',lot_details_data.contract_start_date )[0]
            lot_details_data.contract_start_date = datetime.strptime(lot_details_data.contract_start_date,'%d/%m/%Y').strftime('%Y/%m/%d')
        except Exception as e:
            logging.info("Exception in contract_start_date: {}".format(type(e).__name__))
            pass

    #         # Onsite Field -Execution or Delivery period
    #         # Onsite Comment - take only "end date" for ex."27/11/2023 ~ 27/11/2024" , here take only "27/11/2024"

        try:
            lot_details_data.contract_end_date = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(12)').text.split('~')[1]
            lot_details_data.contract_end_date  = re.findall('\d+/\d+/\d{4}',lot_details_data.contract_end_date )[0]
            lot_details_data.contract_end_date = datetime.strptime(lot_details_data.contract_end_date,'%d/%m/%Y').strftime('%Y/%m/%d')
        except Exception as e:
            logging.info("Exception in contract_end_date: {}".format(type(e).__name__))
            pass


    #         # Onsite Field -None
    #         # Onsite Comment -

        try:
            award_details_data = award_details()

            # Onsite Field -Successful bidder	
            # Onsite Comment -

            award_details_data.bidder_name = tender_html_element.find_element(By.CSS_SELECTOR, ' td:nth-child(7)').text

            # Onsite Field -Prices proposed by each bidder at the bids opening	
        #         Onsite Comment -take the amount value after  winning bidder_name ,  for ex. "PENTA MEDICALS Ltd : 70,081,100.00" , here take only "70,081,100.00" , if multiple bidders are included then take only winnning bidder "grosswardvaluelc"
            try:
                grossawardvaluelc_1 = tender_html_element.find_element(By.CSS_SELECTOR, ' td:nth-child(6)').text
                grossawardvaluelc = re.escape(award_details_data.bidder_name)
                grossawardvaluelc = re.compile(f'{grossawardvaluelc} : ([0-9,.]+)')
                award_details_data.grossawardvaluelc = grossawardvaluelc.search(grossawardvaluelc_1).group(1)
                award_details_data.grossawardvaluelc = award_details_data.grossawardvaluelc.replace(',','')
                award_details_data.grossawardvaluelc = float(award_details_data.grossawardvaluelc)
            except:
                pass
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

    notice_data.identifier = str(notice_data.script_name) + str(notice_data.related_tender_id ) +  str(notice_data.notice_type) +  str(notice_data.est_amount) 
    logging.info(notice_data.identifier)
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
    urls = ["https://www.umucyo.gov.rw/pt/index.do"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        
        page_main.switch_to.frame('main')
        main_1 = page_main.find_element(By.XPATH, '//*[@id="tab_a3"] ')
        page_main.execute_script("arguments[0].click();", main_1)    
        time.sleep(4)
        
        try:
            main_1 = page_main.find_element(By.XPATH, '//*[@id="tabsholder2"]//p//a ')
            page_main.execute_script("arguments[0].click();", main_1)
        except:
            pass
        
        try:
            for page_no in range(2,5):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="contents_R"]/div/table/tbody/tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="contents_R"]/div/table/tbody/tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="contents_R"]/div/table/tbody/tr')))[records]
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
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="contents_R"]/div/table/tbody/tr'),page_check))
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
    output_json_file.copyFinalJSONToServer(output_json_folder)
