from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "in_cspdcl_spn"
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
import gec_common.Doc_Download_ingate

#Note:take data after clicking on clicks between "(B) Region wise Tender Notices issued by" and "(C) Tender Notices issued by O/o Chief Engineer (Project), CSPDCL".

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "in_cspdcl_spn"
Doc_Download = gec_common.Doc_Download_ingate.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'in_cspdcl_spn'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'INR'

    notice_data.main_language = 'EN'

    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -Note:If "tr > td:nth-child(12) a" this selector have "Corrigendum1","Date Extension" this keyword than take notice_type 16
   
    
    # Onsite Field -Tender Notice No.
    # Onsite Comment -None
    try:
        notice_type = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(12)').text
        if "Corrigendum1" in notice_type or "Date Extension" in notice_type or 'Corrigendum01' in notice_type:
            notice_data.notice_type = 16
        else:
            notice_data.notice_type = 4
    except:
        pass
    
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Scope of Work
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Estimated Cost(Rs.)
    # Onsite Comment -None

    try:
        est_amount = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
        est_amount = re.sub("[^\d\.\,]","",est_amount)
        notice_data.est_amount = float(est_amount.strip())
        notice_data.grossbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    # Onsite Field -Closing Date & Time for Submission of Tender
    # Onsite Comment -Note:Grab time also
    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(6)").text
        notice_deadline = re.findall('\d+/\d+/\d{4} \d+:\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y  %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
        
    if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
        return
    # Onsite Field -Date & Time of Opening of Tender
    # Onsite Comment -Note:Grab time also
    try:
        document_opening_time = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(7)').text
        document_opening_time = re.findall('\d+/\d+/\d{4}',document_opening_time)[0]
        notice_data.document_opening_time = datetime.strptime(document_opening_time,'%d/%m/%Y').strftime('%Y-%m-%d')
    except Exception as e:
        logging.info("Exception in document_opening_time: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Remark/RFx ID
    # Onsite Comment -None

    try:
        related_tender_id = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(13)').text
        if related_tender_id != "" and len(related_tender_id) >1:
            notice_data.related_tender_id = related_tender_id
    except Exception as e:
        logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
        pass

    notice_data.notice_url = page_main.current_url
    
    # Onsite Field -None
    # Onsite Comment -Note:along with notice text (page detail) also take data from tender_html_element (main page) ---- give td / tbody of main pg
    notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    try:              
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, 'td:nth-child(12) a'):
            attachments_data = attachments()
        # Onsite Field -Note:Don't take file extention
        # Onsite Comment -None

            attachments_data.file_name = single_record.text
  
            external_url = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(12) a').click()
            file_dwn = Doc_Download.file_download()
            attachments_data.external_url = str(file_dwn[0])
               
        # Onsite Field -Note:Take only file extention
        # Onsite Comment -None

            try:
                attachments_data.file_type = attachments_data.external_url.split(".")[-1]
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = 'CHHATTISGARH STATE POWER DISTRIBUTION COMPANY LIMITED'
        customer_details_data.org_parent_id = '7522502'
    # Onsite Field -Issuing Office
    # Onsite Comment -None

        try:
            customer_details_data.org_address = tender_html_element.find_element(By.CSS_SELECTOR, '#MainContent_GVTenderDetails tr > td:nth-child(2)').text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass

        customer_details_data.org_country = 'IN'
        customer_details_data.org_language = 'EN'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    

    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.notice_deadline) + str(notice_data.local_title)
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
page_main = Doc_Download.page_details 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.cspdcl.co.in/cseb/frmViewTenderesNEW.aspx?paramflag=1","https://www.cspdcl.co.in/cseb/frmViewTenderesNEW.aspx?paramflag=2","https://www.cspdcl.co.in/cseb/frmViewTenderesNEW.aspx?paramflag=3","https://www.cspdcl.co.in/cseb/frmViewTenderesNEW.aspx?paramflag=4","https://www.cspdcl.co.in/cseb/frmViewTenderesNEW.aspx?paramflag=5","https://www.cspdcl.co.in/cseb/frmViewTenderesNEW.aspx?paramflag=6","https://www.cspdcl.co.in/cseb/frmViewTenderesNEW.aspx?paramflag=7","https://www.cspdcl.co.in/cseb/frmViewTenderesNEW.aspx?paramflag=12"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(2,10):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="MainContent_GVTenderDetails"]/tbody/tr[2]'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="MainContent_GVTenderDetails"]/tbody/tr')))
                length = len(rows)
                for records in range(1,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="MainContent_GVTenderDetails"]/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
                        break
            
                if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
                    break 
                try:   
                    next_page = WebDriverWait(page_main, 100).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 100).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="MainContent_GVTenderDetails"]/tbody/tr[2]'),page_check))
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
