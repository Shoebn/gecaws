from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "in_wbsedcl_spn"
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
from selenium.webdriver.support.ui import Select

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "in_wbsedcl_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    

    notice_data.script_name = 'in_wbsedcl_spn'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)
    notice_data.main_language = 'EN'
    notice_data.currency = 'INR'
    notice_data.procurement_method = 2

    notice_data.notice_type = 4
    
    try:
        date1=tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
        date1=re.findall('\d+.\d+.\d{4}',date1)[0]
        notice_data.publish_date = datetime.strptime(date1,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
    except:
        pass
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text.replace(date1,'').replace('Dated:','')
    except:
        try:
            notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
        except:
            pass

    try:
        deadline_date=tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(6)').text
        deadline_date1=deadline_date.split('up to')[0]
        deadline_date2=deadline_date.split('up to')[1]
        deadline_date3 = deadline_date1 +' '+deadline_date2
        deadline_date=re.findall(r'\d{2}.\d{2}.\d{4}\s*\n\s*\d+.\d+ [PA]\.[Mm]\.',deadline_date3)[0]
        deadline_date = deadline_date.replace('\n','')
        try:
            deadline_date = deadline_date.replace('P.M.','PM')
        except:
            deadline_date = deadline_date.replace('A.M.','AM')
        notice_data.notice_deadline = datetime.strptime(deadline_date,'%d.%m.%Y %I.%M %p').strftime('%Y/%m/%d %H:%M:%S')
    except:
        pass
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
 
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    try:
        document_purchase_end_time=tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
        document_purchase_end_time=re.findall('\d+.\d+.\d{4}',document_purchase_end_time)[0]
        notice_data.document_purchase_end_time = datetime.strptime(document_purchase_end_time,'%d.%m.%Y').strftime('%Y/%m/%d')
    except:
        pass
    try:
        document_purchase_start_time=tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
        document_purchase_start_time=re.findall('\d+.\d+.\d{4}',document_purchase_start_time)[0]
        notice_data.document_purchase_start_time = datetime.strptime(document_purchase_start_time,'%d.%m.%Y').strftime('%Y/%m/%d')
    except:
        pass
    
    try:
        attachments_data = attachments()
        attachments_data.file_name =  tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(8) a').text
        attachments_data.external_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(8) a').get_attribute('href')
        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except:
        pass
    
    try:  

        customer_details_data = customer_details()
        customer_details_data.org_name = "WEST BENGAL STATE ELECTRICITY DISTRIBUTION COMPANY LIMITED"
        customer_details_data.org_parent_id = "7563311"                                                 
        customer_details_data.org_country = 'IN'
        customer_details_data.org_language = 'EN'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    notice_data.notice_url = url

    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    except:
        pass

    try:
        est_amount1 = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        if 'Crores' in est_amount1 or 'Crore ' in est_amount1:
            est_amount= re.findall('\d[\d,\.]*\d|\d',est_amount1)[0]
            est_amount_replace = est_amount.replace('.','').strip()
            notice_data.est_amount = float(est_amount_replace) * 100000
        elif 'Lakhs ' in est_amount1:
            est_amount= re.findall('\d[\d,\.]*\d|\d+',est_amount1)[0]
            est_amount = est_amount * 1000000
        else:
            est_amount= re.findall('\d[\d,\.]*\d|\d+',est_amount1)[0]
            notice_data.est_amount = float(est_amount.replace(',',''))
        try:
            if 'excluding ' in est_amount1 or 'Excluding ' in  est_amount1:
                notice_data.netbudgetlc =  notice_data.est_amount
            else:
                notice_data.grossbudgetlc =  notice_data.est_amount
        except:
            pass
            
    except:
        pass

   
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.notice_deadline) + str(notice_data.local_title)
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver() 
page_details = fn.init_chrome_driver() 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.wbsedcl.in/irj/go/km/docs/internet/new_website/TenderBids.html"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)

        time.sleep(2)
        try:
            for page_no in range(2,5):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#tndr > tbody > tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#tndr > tbody > tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#tndr > tbody > tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
            
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
    
                try:   
                    next_page = WebDriverWait(page_main, 10).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 10).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#tndr > tbody > tr'),page_check))
                except Exception as e:
                    logging.info("Exception in next_page: {}".format(type(e).__name__))
                    logging.info("No next page")
                    break
        except:
            logging.info('No new record')
            break
    logging.info("Finished processing. Scraped {} notices".format(notice_count)
                )
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)
