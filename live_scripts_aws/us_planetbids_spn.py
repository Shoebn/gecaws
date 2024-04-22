from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "us_planetbids_spn"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from deep_translator import GoogleTranslator
from selenium import webdriver
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn
import gec_common.th_Doc_Download as Doc_Download
from selenium.webdriver.chrome.options import Options

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "us_planetbids_spn"
Doc_Download = Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
 
# ---------------------------------------------------------------------------------------------------------------------------------------------------------
#    Login Credential : email :  akanksha.euclid@gmail.com         password : Ak@123456
 
#    Go to Url : "https://pbsystem.planetbids.com/portal/17950/bo/bo-search"
 
# click on "Stage" Drop down  and select "Bidding" for notice_type : 4 and "canceled" and "rejected" for notice_type : 16
 
#    for latest tender_details click on "Posted" twice in table arrow should be downwards for current data
 
# ---------------------------------------------------------------------------------------------------------------------------------------------------------
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    notice_data.script_name = 'us_planetbids_spn'
    notice_data.main_language = 'EN'
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'US'
    notice_data.performance_country.append(performance_country_data)
    notice_data.currency = 'USD'
    notice_data.procurement_method = 2
    # Onsite Field -None
    # Onsite Comment -in tender_html_page click on "Stage" dropdown and select "Canceled" and "Rejected" option and click on "search" for notice_type  16
 
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(1)").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%m/%d/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    # Onsite Field -Project Title
    # Onsite Comment -None
 
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    # Onsite Field -Invitation #
    # Onsite Comment -None
 
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    # Onsite Field -Due Date
    # Onsite Comment -None
 
    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%m/%d/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
 
 
    # Onsite Field -None
    # Onsite Comment -split the data after "Stage:" keyword , for ex. "Found 1 bid with Stage: Rejected" , here take only "Rejected"
 
    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(6)").text
        if 'Bidding' in notice_data.document_type_description:
            notice_data.notice_type = 4
        if 'Rejected' in notice_data.document_type_description or 'Canceled' in notice_data.document_type_description:
            notice_data.notice_type = 16
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
 
    # Onsite Field -None
    # Onsite Comment -click on tr for detail_page
 
    try:
        notice_url = tender_html_element.get_attribute("rowattribute")
        notice_data.notice_url = 'https://pbsystem.planetbids.com/portal/17950/bo/bo-detail/'+str(notice_url)                 
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
 
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Description")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    # Onsite Field -Scope of Services
    # Onsite Comment -split the data between "Scope of Services" and "Other Details" field
 
    try:
        notice_data.notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),"Description")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    # Onsite Field -None
    # Onsite Comment -in detail_page split the data from tabs as follows  "Bid information" (selector: "#detail-navigation > ul > li.bidInformation" ) , "Line Items" (selector : "#detail-navigation  li.bidLineItems") ,  "Documents" (selector : "#detail-navigation  li.bidDocs") , Line Items (selector : "#detail-navigation  li.bidLineItems")
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.bid-detail-wrapper').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    # Onsite Field -Bid information >> Estimated Bid Value
    # Onsite Comment -if the cost is like "Range between $15 Million and $20 Million" then take only 2nd value i.e "$20 Million" it will be multiplied by 1000000 = 2000000" ,           split the data after "Estimated Bid Value" , ref_url : "https://pbsystem.planetbids.com/portal/17950/bo/bo-detail/111037"
 
    try:
        est_amount = page_details.find_element(By.XPATH, '//*[contains(text(),"Bid Detail")]//following::div[70]').text
        est_amount = re.sub("[^\d\.\,]","",est_amount).replace(',','').strip()
        notice_data.est_amount =float(est_amount)
        notice_data.grossbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass

 
    # Onsite Field -Bid Detail >> Categories
    # Onsite Comment -in detail_page split the data from tab as follows  "Bid information" (selector: "#detail-navigation > ul > li.bidInformation" )
#     try:
#         notice_data.category = page_details.find_element(By.XPATH, '//*[contains(text(),"Bid Detail")]//following::div[39]').text
#         print('notice_data.category',notice_data.category)
#     except Exception as e:
#         logging.info("Exception in category: {}".format(type(e).__name__))
#         pass
    # Onsite Field -Pre-Bid Meeting Information >> Pre-Bid Meeting Date
    # Onsite Comment -split the data after "Pre-Bid Meeting Date",  for ex."11/29/2023 9:00 AM (PST)" here split only "11/29/2023" , ref_url : "https://pbsystem.planetbids.com/portal/17950/bo/bo-detail/111819"
 
    try:
        pre_bid_meeting_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Pre-Bid Meeting Information")]//following::div[8]').text
        pre_bid_meeting_date = re.findall('\d+/\d+/\d{4}',pre_bid_meeting_date)[0]
        notice_data.pre_bid_meeting_date = datetime.strptime(pre_bid_meeting_date,'%m/%d/%Y').strftime('%Y/%m/%d')
    except Exception as e:
        logging.info("Exception in pre_bid_meeting_date: {}".format(type(e).__name__))
        pass
 
 
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = 'PLANETBIDS'
        customer_details_data.org_language = 'EN'
    # Onsite Field -Bid Detail >> Address
    # Onsite Comment -go to  "Bid information" (selector: "#detail-navigation > ul > li.bidInformation" ),  split the data between "Address" and "County" field , ref url : "https://pbsystem.planetbids.com/portal/17950/bo/bo-detail/111847#"
        try:
            customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Address")]//following::div[1]').text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass
 
    # Onsite Field -Bid Detail >> County
    # Onsite Comment -go to  "Bid information" (selector: "#detail-navigation > ul > li.bidInformation" ),  split the data after "County"  , ref url : "https://pbsystem.planetbids.com/portal/17950/bo/bo-detail/111847#"
 
        customer_details_data.org_country = "US"
    # Onsite Field -Contact Information >> Contact Info
    # Onsite Comment -go to  "Bid information" (selector: "#detail-navigation > ul > li.bidInformation" ),  split the data between  "Contact Info" and "contact number" , for ex."Vanessa Delgado 619-236-6248" , here take only "Vanessa Delgado" , ref_url : "https://pbsystem.planetbids.com/portal/17950/bo/bo-detail/111329"
 
        try:
            contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Contact Info")]//following::div[1]//div[2]').text
            phone = re.findall('\d+-\d+-\d+',contact_person)[0]
            customer_details_data.contact_person = contact_person.split(phone)[0]
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass
 
    # Onsite Field -Contact Information >> Contact Info
    # Onsite Comment -go to  "Bid information" (selector: "#detail-navigation > ul > li.bidInformation" ),   split only number from "Contact Info" field, for ex."Vanessa Delgado 619-236-6248" , here take only "619-236-6248" , ref_url : "https://pbsystem.planetbids.com/portal/17950/bo/bo-detail/111329"
 
        try:#
            org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Contact Info")]//following::div[1]//div[2]').text
            customer_details_data.org_phone = re.findall('\d+-\d+-\d+',org_phone)[0]
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass
 
    # Onsite Field -Contact Information >> Contact Info
    # Onsite Comment -go to  "Bid information" (selector: "#detail-navigation > ul > li.bidInformation" ),   split only email from "Contact Info" field, grab only second line for ex. "CDelgado@sandiego.gov" , ref_url : "https://pbsystem.planetbids.com/portal/17950/bo/bo-detail/111329"
 
        try:
            org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Contact Info")]//following::div[1]//div[2]').text
            email_regex = re.compile(r"[\w\.-]+@[\w\.-]+")
            customer_details_data.org_email = email_regex.findall(org_email)[0]
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass
 
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -Go to "Line Items" tab ( selector : #detail-navigation  li.bidLineItems) for lot_details , ref_url : "https://pbsystem.planetbids.com/portal/17950/bo/bo-detail/110887#"

    try:
        Line_Items_clk =  WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'li.bidLineItems > a')))
        page_details.execute_script("arguments[0].click();",Line_Items_clk)
        time.sleep(5)
    except:
        pass
    
    try:
        lot_number = 1
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'tbody:nth-child(3) > tr')[1:]:
            lot_details_data = lot_details()
            lot_details_data.lot_number = lot_number
        # Onsite Field -Item Code
        # Onsite Comment -None
 
            try:
                lot_details_data.lot_actual_number = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass
        # Onsite Field -Description
        # Onsite Comment -None
 
            lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
            lot_details_data.lot_title_english = lot_details_data.lot_title
        # Onsite Field -UOM
        # Onsite Comment -None
 
            try:
                lot_details_data.lot_quantity_uom = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
            except Exception as e:
                logging.info("Exception in lot_quantity_uom: {}".format(type(e).__name__))
                pass
        # Onsite Field -Qty
        # Onsite Comment -None
 
            try:
                lot_quantity = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
                lot_details_data.lot_quantity = float(lot_quantity)
            except Exception as e:
                logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                pass
        # Onsite Field -Unit Price
        # Onsite Comment -None
 
            try:
                lot_grossbudget_lc = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(7)').text
                lot_grossbudget_lc = re.sub("[^\d\.\,]","",lot_grossbudget_lc).replace('.','').replace(',','').strip()
                lot_details_data.lot_grossbudget_lc =float(lot_grossbudget_lc)
            except Exception as e:
                logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
                pass
            lot_number += 1 
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -for attachments go to "Documents" tab ( selector : #detail-navigation  li.bidDocs )

    try:
        Documents_clk =  WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'li.bidDocs > a')))
        page_details.execute_script("arguments[0].click();",Documents_clk)
        time.sleep(5)
    except:
        pass
    
    try:   
 
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'tbody tr.row-highlight'):
            attachments_data = attachments()
 
            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
 
            try:
                attachments_data.file_type = single_record.find_element(By.CSS_SELECTOR, ' td:nth-child(2)').text.split(".")[1]
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
 
            try:
                attachments_data.file_size = single_record.find_element(By.CSS_SELECTOR, ' td:nth-child(3)').text
            except Exception as e:
                logging.info("Exception in file_size: {}".format(type(e).__name__))
                pass
            try:
                external_url = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(4)>div>a:nth-child(1)').click()
                time.sleep(10)
            except:
                external_url = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(5)>div>a:nth-child(1)').click()
                time.sleep(10)
            file_dwn = Doc_Download.file_download()
            attachments_data.external_url = str(file_dwn[0])
 
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
 
 
# Onsite Field -Addenda
# Onsite Comment -for attachments go to "Addenda/Emails" tab (selector : "#detail-navigation > ul > li.bidAddendaAndEmails")
    try:
        Documents_clk =  WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,' li.bidAddendaAndEmails > a')))
        page_details.execute_script("arguments[0].click();",Documents_clk)
    except:
        pass
    
    try:
        len_lot = WebDriverWait(page_details, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'svg.svg-inline--fa.fa-angle-up.arrow-button')))
        len_length = len(len_lot)
    except:
        pass
    
    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'svg.svg-inline--fa.fa-angle-up.arrow-button'):
    #     # Onsite Field -Addenda
    #     # Onsite Comment -for attachments go to "Addenda/Emails" tab (selector : "#detail-navigation > ul > li.bidAddendaAndEmails")   ,     you have to open tabs for file_name           ref_url : "https://pbsystem.planetbids.com/portal/17950/bo/bo-detail/107221#"
            single_record.click()
            time.sleep(15)
 
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.set-body.set-addendum-body'):
 
            # Onsite Field -Addenda
            # Onsite Comment -for attachments go to "Addenda/Emails" tab (selector : "#detail-navigation > ul > li.bidAddendaAndEmails")   ,     you have to open tabs for attachments        ref_url : "https://pbsystem.planetbids.com/portal/17950/bo/bo-detail/107221#"
            try:
                external_url = single_record.find_element(By.CSS_SELECTOR, 'div > button').click()
                time.sleep(5)
                file_dwn = Doc_Download.file_download()
                attachments_data = attachments()
                attachments_data.external_url = str(file_dwn[0])
            except:
                pass
 
            try:
                attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'p').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
 
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
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
options = Options()
for argument in arguments:
    options.add_argument(argument)
page_main = webdriver.Chrome(options=options)
page_details = Doc_Download.page_details
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://pbsystem.planetbids.com/portal/17950/login"] 
    
    for url in urls:
        fn.load_page(page_main, url, 50)
        fn.load_page(page_details, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        ##############login##########
        email_box = page_main.find_element(By.CSS_SELECTOR,'#username-field')
        email_box.send_keys('akanksha.euclid@gmail.com')
        time.sleep(2)
 
        psw = page_main.find_element(By.CSS_SELECTOR,'#password-field')
        psw.send_keys('Ak@123456')
        time.sleep(2)
        
        login_button_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#loginForm > div.short-form-btn > button')))
        page_main.execute_script("arguments[0].click();",login_button_click)
        time.sleep(3)
        
        bid_opportunity = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'/html/body/div[3]/div/div[2]/a[2]')))
        page_main.execute_script("arguments[0].click();",bid_opportunity)
        ##########################page_details#############
 
        
        email_box = page_details.find_element(By.CSS_SELECTOR,'#username-field')
        email_box.send_keys('akanksha.euclid@gmail.com')
        time.sleep(2)
 
        psw = page_details.find_element(By.CSS_SELECTOR,'#password-field')
        psw.send_keys('Ak@123456')
        time.sleep(2)
        
        login_button_click = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#loginForm > div.short-form-btn > button')))
        page_details.execute_script("arguments[0].click();",login_button_click)
        time.sleep(3)
        
        bid_opportunity = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.XPATH,'/html/body/div[3]/div/div[2]/a[2]')))
        page_details.execute_script("arguments[0].click();",bid_opportunity)
        ###############################
        index_no = [2,6,7]
        for i in index_no:
            pp_btn = Select(page_main.find_element(By.CSS_SELECTOR,'select#stageId-field.select-field'))
            pp_btn.select_by_index(int(i))
            time.sleep(5)
            
            search_button_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'button.search-btn')))
            page_main.execute_script("arguments[0].click();",search_button_click)
            time.sleep(5)
            
            try:
                sorted_button_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'div.table-sorter')))
                page_main.execute_script("arguments[0].click();",sorted_button_click)
                time.sleep(5)
            except:
                pass
            try:
                sorted_button_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'div.table-sorter')))
                page_main.execute_script("arguments[0].click();",sorted_button_click)
                time.sleep(5)
            except:
                pass

            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'tbody tr.row-highlight')))
            length = len(rows)
            
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'tbody tr.row-highlight')))[records]
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
 
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit() 
    output_json_file.copyFinalJSONToServer(output_json_folder)
