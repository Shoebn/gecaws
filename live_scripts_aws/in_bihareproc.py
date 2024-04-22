from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "in_bihareproc"
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



#Note : To load the more records click on "More"option which will be show after 20 recoreds 



NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "in_bihareproc"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'in_bihareproc'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)
   
    notice_data.currency = 'INR'
    
    notice_data.main_language = 'EN'
  
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 4
    
    notice_data.notice_url = url
    
    # Onsite Field -Reference No.
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, '#latestTenders td:nth-child(4)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -End Date
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "#latestTenders td:nth-child(6)").text
        notice_deadline = re.findall('\d{4}-\d+-\d+ \d+:\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%Y-%m-%d %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
     # Onsite Field -End Date
    # Onsite Comment -None

    try:
        document_purchase_end_time = tender_html_element.find_element(By.CSS_SELECTOR, "#latestTenders td:nth-child(6)").text
        document_purchase_end_time = re.findall('\d{4}-\d+-\d+',document_purchase_end_time)[0]
        notice_data.document_purchase_end_time = datetime.strptime(document_purchase_end_time,'%Y-%m-%d').strftime('%Y/%m/%d')
    except Exception as e:
        logging.info("Exception in document_purchase_end_time: {}".format(type(e).__name__))
        pass
    
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'IN'
        customer_details_data.org_language = 'EN'
        # Onsite Field -Department
        # Onsite Comment -None

        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, '#latestTenders tr > td:nth-child(5)').text
        
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    
    try:
        click = WebDriverWait(tender_html_element, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"td:nth-child(8) > button"))).click()
        time.sleep(10)
    except:
        pass
    WebDriverWait(page_main, 80).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#myModalprev div.modal-body')))
        
    try:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, '#myModalprev div.modal-body').get_attribute("outerHTML")                     
    except:
        pass
    
    
    # Onsite Field -Detailed Description
    # Onsite Comment -None  #myModalprev > div > div > div.modal-body.printabletender > div:nth-child(1) > table > tbody > tr.ng-scope > td:nth-child(2)

    try:
        notice_data.local_title = page_main.find_element(By.CSS_SELECTOR, 'div.modal-body.printabletender > div:nth-child(1) > table > tbody > tr.ng-scope > td:nth-child(2)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_main.find_element(By.XPATH, '//*[contains(text(),"Detailed Description")]//following::td[1]').text
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    # Onsite Field -Bid Submission Start Date
    # Onsite Comment -None

    try:
        publish_date = page_main.find_element(By.XPATH, '//*[contains(text(),"Bid Submission Start Date")]//following::td[1]/span[1]').text
        publish_date = re.findall('\d+-\d+-\d{4} \d+:\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d-%m-%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    
    # Onsite Field -Bid Submission Start Date
    # Onsite Comment -None

    try:
        document_purchase_start_time = page_main.find_element(By.XPATH, '//*[contains(text(),"Bid Submission Start Date")]//following::td[1]/span[1]').text
        document_purchase_start_time = re.findall('\d+-\d+-\d{4}',document_purchase_start_time)[0]
        notice_data.document_purchase_start_time = datetime.strptime(document_purchase_start_time,'%d-%m-%Y').strftime('%Y/%m/%d')
    except Exception as e:
        logging.info("Exception in document_purchase_start_time: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -pre_bid_meeting_date
    # Onsite Comment -None

    try:
        pre_bid_meeting_date = page_main.find_element(By.XPATH, '//*[contains(text(),"Pre-Bid Meeting Start Date")]//following::td[2]/span[1]').text
        pre_bid_meeting_date = re.findall('\d+-\d+-\d{4}',pre_bid_meeting_date)[0]
        notice_data.pre_bid_meeting_date = datetime.strptime(pre_bid_meeting_date,'%d-%m-%Y').strftime('%Y/%m/%d')
    except Exception as e:
        logging.info("Exception in pre_bid_meeting_date: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -EMD
    # Onsite Comment -None

    try:
        notice_data.earnest_money_deposit = page_main.find_element(By.XPATH, '//*[contains(text(),"EMD")]//following::td').text
    except Exception as e:
        logging.info("Exception in earnest_money_deposit: {}".format(type(e).__name__))
        pass
    
#     # Onsite Field -Tender Processing Fee
#     # Onsite Comment -None

    try:
        notice_data.document_fee = page_main.find_element(By.XPATH, '//*[contains(text(),"Tender Processing Fee")]//following::td').text
    except Exception as e:
        logging.info("Exception in document_fee: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.contract_duration = page_main.find_element(By.XPATH, '//*[contains(text(),"Offer Validity(In Days)")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass
    
    try:
        for single_record in page_main.find_elements(By.CSS_SELECTOR, '#myModalprev > div > div > div.modal-body.printabletender > div:nth-child(8) > table.table.table-striped.table-advance.table-bordered.tabular-print-show > tbody > tr:nth-child(n)')[1:]:

            attachments_data = attachments()
            
            attachments_data.file_name= single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3) > span.ng-binding.ng-scope').text
            
            external_url = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3) > span:nth-child(3) > i').click()
            file_dwn = Doc_Download.file_download()
            attachments_data.external_url = str(file_dwn[0])
            time.sleep(5)

            try:
                attachments_data.file_type = attachments_data.file_name.split(".")[-1]
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    try:
        lot_number=1
        for single_record in page_main.find_elements(By.CSS_SELECTOR, 'div:nth-child(10) > table.table.table-striped.table-advance.table-bordered.tabular-print-show > tbody > tr')[1:]:
            
            # Onsite Field -Name of the Work
            # Onsite Comment -None

#          Onsite Field -ITEM NAME  
            # Onsite Comment -None

            lot_title = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
            if lot_title != "":
                lot_details_data = lot_details()
                lot_details_data.lot_number=lot_number
                lot_details_data.lot_title = lot_title
                lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)

                # Onsite Field -QUANTITY
                # Onsite Comment -None

                try:
                    lot_quantity = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
                    lot_details_data.lot_quantity=float(lot_quantity)
                except Exception as e:
                    logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                    pass

        # Onsite Field -UOM
        # Onsite Comment -None

                try:
                    lot_details_data.lot_quantity_uom = single_record.find_element(By.CSS_SELECTOR, ' td:nth-child(3)').text
                except Exception as e:
                    logging.info("Exception in lot_quantity_uom: {}".format(type(e).__name__))
                    pass

                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
                lot_number+=1
            else:
                pass
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
    try:
        WebDriverWait(page_main, 80).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"#myModalprev > div > div > div.modal-footer > button:nth-child(8)"))).click()
    except:
        pass
    time.sleep(5)    
  
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) + str(notice_data.publish_date) +  str(notice_data.notice_url)
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = Doc_Download.page_details
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://eproc2.bihar.gov.in/EPSV2Web/openarea/tenderListingPage.action"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        try:
            clk = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"#PageLink_12"))).click()
            time.sleep(2)
        except:
            pass

        try:
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="myTablebyrTl"]/tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="myTablebyrTl"]/tbody/tr')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
        except:
            logging.info('No new record')
            break

#            
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))

finally:
    page_main.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)
