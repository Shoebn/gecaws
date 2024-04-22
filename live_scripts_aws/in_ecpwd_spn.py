from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "in_ecpwd_spn"
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
SCRIPT_NAME = "in_ecpwd_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    # Onsite Field -None
    # Onsite Comment -Note:Click on "New Tenders" Then click "View More" keyword
    notice_data.script_name = 'in_ecpwd_spn'
    notice_data.main_language = 'EN'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'INR'
    notice_data.procurement_method = 0
    notice_data.notice_type = 4
    
    # Onsite Field -NIT/RFP NO
    # Onsite Comment -None
    # Onsite Field -Tender ID
    # Onsite Comment -Note:"NIT/RFP NO" is blank than take this "Tender ID"

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
    except:
        try:
            notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
        except Exception as e:
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass
    
    # Onsite Field -Name of Work
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
     # Onsite Field -Estimated Cost
    # Onsite Comment -None

    try:
        est_amount = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
        est_amount = re.sub("[^\d\.\,]","",est_amount)
        notice_data.est_amount =float(est_amount.replace(',','').strip())
        notice_data.grossbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -EMD Amount
    # Onsite Comment -None

    try:
        earnest_money_deposit = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(6)').text
        earnest_money_deposit = re.sub("[^\d\.\,]","",earnest_money_deposit)
        notice_data.earnest_money_deposit = earnest_money_deposit.replace(',','').strip()
    except Exception as e:
        logging.info("Exception in earnest_money_deposit: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Action
    # Onsite Comment -None
    try:
        notice_url = WebDriverWait(tender_html_element, 100).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"td > a:nth-child(1)"))).click()
        time.sleep(5)
        page_main.switch_to.window(page_main.window_handles[1])
        notice_data.notice_url = page_main.current_url
        logging.info(notice_data.notice_url)
    except Exception as e:
        pass
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url   
    
    # Onsite Field -Tender Publishing Date & Time
    # Onsite Comment -None

    try:
        publish_date = page_main.find_element(By.XPATH, '''//*[contains(text(),"Tender Publishing Date & Time")]//following::td[1]''').text
        publish_date = re.findall('\d+/\d+/\d{4} \d+:\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Bid Submission Closing Date & Time
    # Onsite Comment -None

    try:
        notice_deadline = page_main.find_element(By.XPATH, '''//*[contains(text(),"Bid Submission Closing Date & Time")]//following::td[1]''').text
        notice_deadline = re.findall('\d+/\d+/\d{4} \d+:\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Tender Publishing Date & Time
    # Onsite Comment -None

    try:
        document_purchase_start_time = page_main.find_element(By.XPATH, '//*[contains(text(),"Tender Publishing Date & Time")]//following::td[1]').text
        document_purchase_start_time = re.findall('\d+/\d+/\d{4}',document_purchase_start_time)[0]
        notice_data.document_purchase_start_time = datetime.strptime(document_purchase_start_time,'%d/%m/%Y').strftime('%Y/%m/%d')
    except Exception as e:
        logging.info("Exception in document_purchase_start_time: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Bid Submission Closing Date & Time
    # Onsite Comment -None

    try:
        document_purchase_end_time = page_main.find_element(By.XPATH, '//*[contains(text(),"Bid Submission Closing Date & Time")]//following::td[1]').text
        document_purchase_end_time = re.findall('\d+/\d+/\d{4}',document_purchase_end_time)[0]
        notice_data.document_purchase_end_time = datetime.strptime(document_purchase_end_time,'%d/%m/%Y').strftime('%Y/%m/%d')
    except Exception as e:
        logging.info("Exception in document_purchase_end_time: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Bid Validity Period (in Days)
    # Onsite Comment -None 

    try:
        contract_duration_word = page_main.find_element(By.XPATH, '''//*[contains(text(),"Bid Validity Period (in Days)")]''').text.split('(')[1].split(')')[0].strip()
        contract_duration_num = page_main.find_element(By.XPATH, '''//*[contains(text(),"Bid Validity Period (in Days)")]//following::td[1]''').text
        notice_data.contract_duration = contract_duration_word + ':' + contract_duration_num
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, '#viewTenderBean').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')

    
    # Onsite Field -Procurement Type
    # Onsite Comment -None

    try:
        notice_data.contract_type_actual = page_main.find_element(By.XPATH, '//*[contains(text(),"Procurement Type")]//following::td[1]').text
        if "services" in notice_data.contract_type_actual.lower():
            notice_data.notice_contract_type ="Service"
        elif "works" in notice_data.contract_type_actual.lower():
            notice_data.notice_contract_type ="Works"
        elif "goods" in notice_data.contract_type_actual.lower():
            notice_data.notice_contract_type ="Supply"
        else:
            pass
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass

# Onsite Field -None
# Onsite Comment -None

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = 'Central Public Works Department '
        customer_details_data.org_parent_id = '7522430'       
        customer_details_data.org_country = 'IN'
        customer_details_data.org_language = 'EN'        
            
        # Onsite Field -Designation
        # Onsite Comment -None

        try:
            customer_details_data.contact_person = page_main.find_element(By.CSS_SELECTOR, 'div:nth-child(6) tr:nth-child(1) > td:nth-child(4)').text
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass
        
        
        # Onsite Field -Address
        # Onsite Comment -None

        try:
            customer_details_data.org_address = page_main.find_element(By.CSS_SELECTOR, 'div:nth-child(6) tr:nth-child(2) > td:nth-child(2)').text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass

        # Onsite Field -Email
        # Onsite Comment -None

        try:
            customer_details_data.org_email = page_main.find_element(By.CSS_SELECTOR, 'div:nth-child(6) tr:nth-child(3) > td:nth-child(2)').text
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Contact Details
        # Onsite Comment -None

        try:
            customer_details_data.org_phone = page_main.find_element(By.CSS_SELECTOR, 'div:nth-child(6) tr:nth-child(2) > td:nth-child(4)').text
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass
        
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    page_main.close()
    page_main.switch_to.window(page_main.window_handles[0])
    
    try:
        attachments_clk = WebDriverWait(tender_html_element, 100).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"td:nth-child(9)  a.a_fnviewTenderDocuments")))
        attachments_clk.location_once_scrolled_into_view
        attachments_clk.click()
        page_main.switch_to.window(page_main.window_handles[1])
        time.sleep(5)
    except Exception as e:
        pass
    
# Onsite Field -Action
# Onsite Comment -for atatchment click on (td:nth-child(8) > a.a_fnviewTenderDocuments)  in tender_html_element page

    try:              
        attachments_data = attachments()
    # Onsite Field -File Name
    # Onsite Comment -split the extention (like ".pdf") from "File Name" field

        try:
            attachments_data.file_type = page_main.find_element(By.CSS_SELECTOR, '#viewTenderDocBean  td:nth-child(2)').text.split('.')[-1].strip()
        except Exception as e:
            logging.info("Exception in file_type: {}".format(type(e).__name__))
            pass

    # Onsite Field -File Name
    # Onsite Comment -None

        attachments_data.file_name = page_main.find_element(By.CSS_SELECTOR, '#viewTenderDocBean  td:nth-child(2)').text.split('.')[0].strip()


    # Onsite Field -File Description
    # Onsite Comment -None

        try:
            attachments_data.file_description = page_main.find_element(By.CSS_SELECTOR, '#viewTenderDocBean  td:nth-child(3)').text
        except Exception as e:
            logging.info("Exception in file_description: {}".format(type(e).__name__))
            pass

        # Onsite Field -Bulk Download
        # Onsite Comment -None

        external_url = page_main.find_element(By.CSS_SELECTOR, '#btnBulkDownLoad').click()
        time.sleep(10)
        file_dwn = Doc_Download.file_download()
        attachments_data.external_url = str(file_dwn[0])
    
        # Onsite Field -File Size(in Bytes)
        # Onsite Comment -None

        try:
            attachments_data.file_size = page_main.find_element(By.CSS_SELECTOR, '#viewTenderDocBean  td:nth-child(4)').text
        except Exception as e:
            logging.info("Exception in file_size: {}".format(type(e).__name__))
            pass
        
        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    page_main.close()
    page_main.switch_to.window(page_main.window_handles[0])
    
    try:
        Close_clk2 = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,"(//input[@class='Button'])[2]"))).click()
        time.sleep(2)
        WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="pagetable13"]/tbody/tr'))).text
    except:
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = Doc_Download.page_details
page_main.maximize_window()  
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://etender.cpwd.gov.in/"] 
    for url in urls:
        fn.load_page(page_main, url, 80)
        logging.info('----------------------------------')
        logging.info(url)
        
        try:
            time.sleep(3)
            page_main.find_element(By.LINK_TEXT,"OK").click()
            time.sleep(2)
            alert = page_main.switch_to.alert
            alert.dismiss()
        except:
            pass
        
        
        New_Tenders = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="newTenderDiv"]'))).click()
        
        View_More = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="viewCurrentall"]'))).click()
        try:
            for page_no in range(2,10):
                page_check = WebDriverWait(page_main, 120).until(EC.presence_of_element_located((By.XPATH,'//*[@id="pagetable13"]/tbody/tr'))).text
                rows = WebDriverWait(page_main, 100).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="pagetable13"]/tbody/tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 80).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="pagetable13"]/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
                        
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 100).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 120).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="pagetable13"]/tbody/tr'),page_check))
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
    output_json_file.copyFinalJSONToServer(output_json_folder)
