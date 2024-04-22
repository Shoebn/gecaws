from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "in_apeproc"
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

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "in_apeproc"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    # Onsite Field -None
    # Onsite Comment -Note: Go to home page > "current tender" click on more And Tack also "Upcoming Tenders" click on more.
    notice_data.script_name = 'in_apeproc'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'INR'
    
    notice_data.main_language = 'EN'
    
    notice_data.procurement_method = 0
    
    notice_data.notice_type = 4
    
#     notice_data.notice_url = url
    
    # Onsite Field -IFB/Tender Notice Number
    # Onsite Comment -split notice_number

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    try:
        org_name = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(1)").text
    except:
        pass
    
    # Onsite Field -Bid Start Date & Time
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(7)").text
        publish_date = re.findall('\d+/\d+/\d{4} \d{2}:\d{2}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Bid Submission Closing Date& Time
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(8)").text
        notice_deadline = re.findall('\d+/\d+/\d{4} \d{2}:\d{2}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Tender Category
    # Onsite Comment -Relace following keywords with given keywords("WORKS=Works","PRODUCTS=Supply")

    try:
        notice_contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
        if "WORKS" in notice_contract_type:
            notice_data.notice_contract_type = "Works"
        elif "PRODUCTS" in notice_contract_type:
            notice_data.notice_contract_type = "Supply"
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
     # Onsite Field -Action
    # Onsite Comment -None
    
    try:
        notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td > a:nth-child(1)').click() 
        notice_data.notice_url = url
        page_main.switch_to.window(page_main.window_handles[1])
        time.sleep(5)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url


    try:
        notice_data.notice_text += WebDriverWait(page_main,10).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#viewTenderBean'))).get_attribute("outerHTML") 
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
#     # Onsite Field -Bid Document Download Start Date & Time
#     # Onsite Comment -None

    try:
        document_purchase_start_time = page_main.find_element(By.XPATH, '//*[@id="lblBidDocDownStartingDateValue"]').text
        document_purchase_start_time = re.findall('\d+/\d+/\d{4}',document_purchase_start_time)[0]
        notice_data.document_purchase_start_time = datetime.strptime(document_purchase_start_time,'%d/%m/%Y').strftime('%Y/%m/%d')
        logging.info(notice_data.document_purchase_start_time)
    except Exception as e:
        logging.info("Exception in document_purchase_start_time: {}".format(type(e).__name__))
        pass
    
#     # Onsite Field -Bid Document Download End Date & Time
#     # Onsite Comment -None

    try:
        document_purchase_end_time = page_main.find_element(By.XPATH, '//*[@id="viewTenderBean"]/table[8]/tbody/tr/td/table/tbody/tr[2]/td[2]').text
        document_purchase_end_time = re.findall('\d+/\d+/\d{4}',document_purchase_end_time)[0]
        notice_data.document_purchase_end_time = datetime.strptime(document_purchase_end_time,'%d/%m/%Y').strftime('%Y/%m/%d')
        logging.info(notice_data.document_purchase_end_time)
    except Exception as e:
        logging.info("Exception in document_purchase_end_time: {}".format(type(e).__name__))
        pass
    
#     # Onsite Field -Bid Submission Closing Date & Time
#     # Onsite Comment -None

    try:
        pre_bid_meeting_date = page_main.find_element(By.XPATH, '//*[@id="viewTenderBean"]/table[8]/tbody/tr/td/table/tbody/tr[3]/td[2]').text
        pre_bid_meeting_date = re.findall('\d+/\d+/\d{4}',pre_bid_meeting_date)[0]
        notice_data.pre_bid_meeting_date = datetime.strptime(pre_bid_meeting_date,'%d/%m/%Y').strftime('%Y/%m/%d')
        logging.info(notice_data.pre_bid_meeting_date)
    except Exception as e:
        logging.info("Exception in pre_bid_meeting_date: {}".format(type(e).__name__))
        pass
    
#     # Onsite Field -Estimated Contract Value
#     # Onsite Comment -None

    try:
        grossbudgetlc = page_main.find_element(By.CSS_SELECTOR, ' tr:nth-child(3) > td:nth-child(4) > span').text
        grossbudgetlc = re.sub("[^\d\.\,]", "", grossbudgetlc)
        notice_data.grossbudgetlc = float(grossbudgetlc.replace(',','').strip())
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
    
 # Onsite Field -Estimated Contract Value
# Onsite Comment -None
    
    try:
        notice_data.est_amount = notice_data.grossbudgetlc
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
#     # Onsite Field -Transaction Fee Details
#     # Onsite Comment -None

    try:
        notice_data.document_fee = page_main.find_element(By.XPATH, '//*[@id="mTransactionFee"]').text
    except Exception as e:
        logging.info("Exception in document_fee: {}".format(type(e).__name__))
        pass
    
# Onsite Field -Name of Project
    # Onsite Comment -None

    try:
        notice_data.local_title = page_main.find_element(By.XPATH, '//*[contains(text(),"Name of Project")]//following::td[1]').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_main.find_element(By.XPATH, '//*[contains(text(),"Name of Work")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
#     # Onsite Field -Name of Work
#     # Onsite Comment -None

    try:
        notice_data.notice_summary_english = notice_data.local_description
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
#     # Onsite Field -Bid Validity Period (in Days)
#     # Onsite Comment -None

    try:
        notice_data.contract_duration = page_main.find_element(By.XPATH, '//*[@id="viewTenderBean"]/table[8]/tbody/tr/td/table/tbody/tr[4]/td[2]').text
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass
    
#     # Onsite Field -Bid Security (INR)
#     # Onsite Comment -None

    try:
        notice_data.earnest_money_deposit = page_main.find_element(By.CSS_SELECTOR, 'table:nth-child(20) td.tdwhite').text
    except Exception as e:
        logging.info("Exception in earnest_money_deposit: {}".format(type(e).__name__))
        pass
    
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'IN'
        customer_details_data.org_state = 'AP'
        customer_details_data.org_language = 'EN'
        customer_details_data.org_name = org_name
        
        # Onsite Field -Department Name
        # Onsite Comment -None
        
        # Onsite Field -Address
        # Onsite Comment -None

        try:
            customer_details_data.org_address = page_main.find_element(By.XPATH, '//*[@id="viewTenderBean"]/table[10]/tbody/tr/td/table/tbody/tr[3]/td[2]').text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Email
        # Onsite Comment -None

        try:
            customer_details_data.org_email = page_main.find_element(By.XPATH, '//*[@id="viewTenderBean"]/table[10]/tbody/tr/td/table/tbody/tr[5]/td[2]').text
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Contact Details
        # Onsite Comment -None

        try:
            customer_details_data.org_phone = page_main.find_element(By.XPATH, '//*[@id="VTMSBodyContent_lblContactDetailsValue"]').text
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass
        
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    # Onsite Field -None
# Onsite Comment -Note:take lots by clicking "Schedules Details + view details "  >  "Enquiry Forms + Itemwise Formatx " tab  getting Lots details

    try: 
        clk1 = page_main.find_element(By.CSS_SELECTOR, 'td:nth-child(4) > a').click()
        page_main.switch_to.window(page_main.window_handles[1]) 
        time.sleep(5)

        for single_record in page_main.find_elements(By.CSS_SELECTOR, ' td:nth-child(7) > a')[-1:]:
            clk1 = single_record.click()
            page_main.switch_to.window(page_main.window_handles[1]) 
            time.sleep(5)
            
            try:
                notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, '#viewItemwiseFormatx').get_attribute("outerHTML")                     
            except Exception as e:
                logging.info("Exception in notice_text: {}".format(type(e).__name__))
                pass
            
            lot_number = 1
            for single_record in page_main.find_elements(By.CSS_SELECTOR, '#taTable > tbody > tr'):
                lot_details_data = lot_details()
                lot_details_data.lot_number =  lot_number
                
#         # Onsite Field -Item Name
#         # Onsite Comment -None

                lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
                lot_title_english = lot_details_data.lot_title
                lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_title_english)
            
#         # Onsite Field -Description Of Item
#         # Onsite Comment -None

                try:
                    lot_details_data.lot_description = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
                    lot_details_data.lot_description_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_description)
                except Exception as e:
                    logging.info("Exception in lot_description: {}".format(type(e).__name__))
                    pass

#         # Onsite Field -Quantity
#         # Onsite Comment -None

                try:
                    lot_quantity = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(6)').text
                    lot_details_data.lot_quantity = float(lot_quantity)
                except Exception as e:
                    logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                    pass
                
                try:
                    lot_details_data.lot_quantity_uom = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
                except Exception as e:
                    logging.info("Exception in lot_quantity_uom: {}".format(type(e).__name__))
                    pass

                lot_details_data.contract_type = notice_data.notice_contract_type
                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
                lot_number += 1

            page_main.switch_to.window(page_main.window_handles[0])
            time.sleep(5)

        page_main.switch_to.window(page_main.window_handles[0])

    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
    page_main.switch_to.window(page_main.window_handles[0])

# Onsite Field -None
# Onsite Comment -click on "Download Tender Documents" this selector on tender_html_element to get attachments data.
   
    try: 
        clk = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(9) > a:nth-child(2) > img').get_attribute("src")

        if '.PNG' in clk:
            clk1 = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(9) > a:nth-child(2) > img').click()
            page_main.switch_to.window(page_main.window_handles[1]) 
            time.sleep(5)
            
            try:
                notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, '#viewTenderDocBean').get_attribute("outerHTML")                     
            except Exception as e:
                logging.info("Exception in notice_text: {}".format(type(e).__name__))
                pass

            try:
                attachments_data = attachments()
                attachments_data.file_name = "Tender Documents"
                attachments_data.file_type = ".zip"
                external_url = page_main.find_element(By.CSS_SELECTOR, '#btnBulkDownLoad')
                page_main.execute_script("arguments[0].click();",external_url)
                time.sleep(5)
                file_dwn = Doc_Download.file_download()
                attachments_data.external_url = str(file_dwn[0])
                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
            except:
                pass

            page_main.switch_to.window(page_main.window_handles[0])

        else:
            clk = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(9) > a:nth-child(3) > img').get_attribute("src")
            if '.PNG' in clk:
                clk1 = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(9) > a:nth-child(3) > img').click()
                page_main.switch_to.window(page_main.window_handles[1]) 
                time.sleep(5)
                
            try:
                notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, '#viewTenderDocBean').get_attribute("outerHTML")                     
            except Exception as e:
                logging.info("Exception in notice_text: {}".format(type(e).__name__))
                pass

            try:
                attachments_data = attachments()
                attachments_data.file_name = "Tender Documents"
                attachments_data.file_type = ".zip"
                external_url = page_main.find_element(By.CSS_SELECTOR, '#btnBulkDownLoad')
                page_main.execute_script("arguments[0].click();",external_url)
                time.sleep(5)
                file_dwn = Doc_Download.file_download()
                attachments_data.external_url = str(file_dwn[0])
                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
            except:
                pass

            page_main.switch_to.window(page_main.window_handles[0])

    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
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
page_main = Doc_Download.page_details 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://tender.apeprocurement.gov.in/login.html"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)

        for tabs in range(2):

            try:
                click1=WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,'More...')))
                page_main.execute_script("arguments[0].click();",click1)
                time.sleep(2)
            except:
                pass
            
            try:
                WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,' th:nth-child(1)')))
            except:
                pass

            try:
                for page_no in range(2,5):
                    page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="pagetable13"]/tbody/tr'))).text
                    rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="pagetable13"]/tbody/tr')))
                    length = len(rows)
                    for records in range(0,length):
                        tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="pagetable13"]/tbody/tr')))[records]
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
                        WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="pagetable13"]/tbody/tr'),page_check))
                    except Exception as e:
                        logging.info("Exception in next_page: {}".format(type(e).__name__))
                        logging.info("No next page")
                        break
            except:
                logging.info('No new record')
                break

            fn.load_page(page_main, url, 50)
            logging.info('----------------------------------')
            logging.info(url)
            page_main.find_element(By.XPATH,'//*[@id="skipContentBox"]/label[3]/span').click()
            time.sleep(3)
            
            try:
                WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#content1 > div:nth-child(2) > div:nth-child(1) > div:nth-child(1) > span')))
            except:
                pass


    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    
    output_json_file.copyFinalJSONToServer(output_json_folder)
