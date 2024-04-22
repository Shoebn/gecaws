from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "in_devnetjobsindia_spn"
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
from selenium.webdriver.support.ui import Select

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "in_devnetjobsindia_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    

    notice_data.script_name = 'in_devnetjobsindia_spn'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'INR'

    notice_data.main_language = 'EN'

    notice_data.procurement_method = 2

    notice_data.notice_type = 4
    
    notice_text = tender_html_element.get_attribute('outerHTML')
    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'a strong').click()
        notice_data.notice_url = page_main.current_url
    except:
        pass

    try:
        notice_data.local_title = page_main.find_element(By.XPATH, '//*[@id="ContentPlaceHolder1_JD1_lblJobTitle"]').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:              
        customer_details_data = customer_details()

        customer_details_data.org_name = page_main.find_element(By.XPATH, '//*[@id="ContentPlaceHolder1_JD1_tblLive"]/tbody/tr/td/table[2]/tbody/tr[2]').text
        try:
            customer_details_data.website = page_main.find_element(By.XPATH, "//*[contains(text(),'Website:')]//following::span[1]").text
        except:
            pass
        try:
            customer_details_data.address =  page_main.find_element(By.XPATH, '//*[@id="ContentPlaceHolder1_JD1_tdDesc"]').text.split('Address:')[1].split('Email ID:')[0]
        except:
            pass
        try:
            customer_details_data.org_phone =  page_main.find_element(By.XPATH, '//*[@id="ContentPlaceHolder1_JD1_tdDesc"]').text.split('Tel: ')[1].split('\n')[0]
        except:
            pass
        try:
            customer_details_data.org_email = page_main.find_element(By.XPATH,'//*[contains(text(),"Job Email id:")]//following::td[1]/span').text
            if '(at)' in customer_details_data.org_email:
                customer_details_data.org_email = customer_details_data.org_email.replace('(at)','@')
        except:
            try:
                customer_details_data.org_email = page_main.find_element(By.XPATH,'//*[contains(text(),"Email: ")]//following::a[1]').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass

        customer_details_data.org_country = 'IN'
        customer_details_data.org_language = 'EN'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:
        notice_data.notice_no = page_main.find_element(By.XPATH,'//*[@id="form1"]/div[3]/center/table/tbody/tr/td[2]/table[1]/tbody/tr/td/table[3]/tbody/tr/td[1]').text.split('Tender No. ')[1].split(':')[0]
    except:
        try:
            notice_data.notice_no = page_main.find_element(By.XPATH,'//*[@id="form1"]/div[3]/center/table/tbody/tr/td[2]/table[1]/tbody/tr/td/table[3]/tbody/tr/td[1]').text.split('Ref No: ')[1].split('\n')[0]
        except:
            notice_data.notice_no = notice_data.notice_url.split('Job_Id=')[1]
        
    try:
        publish_date =  page_main.find_element(By.XPATH,'//*[@id="form1"]/div[3]/center/table/tbody/tr/td[2]/table[1]/tbody/tr/td/table[3]/tbody/tr/td[1]').text.split('Release Date:')[1].split('\n')[0].strip()
        notice_data.publish_date = datetime.strptime(publish_date, '%d %b %Y').strftime('%Y/%m/%d %H:%M:%S')
    except:
        pass
    
    if 'Expression of Interest' in page_main.find_element(By.XPATH,'//*[@id="form1"]/div[3]/center/table/tbody/tr/td[2]/table[1]/tbody/tr/td/table[3]/tbody/tr/td[1]').text:
        notice_data.notice_type = 5
    else:
        notice_data.notice_type = 4

    try:
        deadline_date = page_main.find_element(By.XPATH, "//*[@id='ContentPlaceHolder1_JD1_lblPostedDate']").text
        notice_data.notice_deadline = datetime.strptime(deadline_date, '%d %b %Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in deadline_date: {}".format(type(e).__name__))
        pass
    
    if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
        return
    try:
        notice_data.notice_text += notice_text
        notice_data.notice_text += page_main.find_element(By.XPATH,'//*[@id="form1"]/div[3]/center/table/tbody/tr/td[2]/table[1]/tbody/tr/td/table[3]/tbody/tr/td[1]').get_attribute('outerHTML')
    except:
        pass
    
    try:
        notice_data.local_description= page_main.find_element(By.XPATH, '//*[contains(text(),"Scope of Work:")]//following::ol[1]').text
        notice_data.notice_summary_english = notice_data.local_description
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass     
    
    try:
        notice_data.eligibility = page_main.find_element(By.XPATH,'//*[contains(text(),"Minimum Firm Eligibility:")]//following::ol[1]').text
    except:
        pass
    
    try:
        document_opening_time = (By.XPATH, '//*[@id="ContentPlaceHolder1_JD1_tdDesc"]').text.split('Bid opening: -')[1].split('\n')[0]
        notice_data.document_opening_time = datetime.strptime(document_opening_time, '%dth %B %Y').strftime('%Y/%m/%d')
    except:
        pass
    
    try:              
        for single_record in page_main.find_elements(By.CSS_SELECTOR,'#ContentPlaceHolder1_JD1_tblLive > tbody > tr > td > table:nth-child(6) > tbody tr a '):
            attachments_data = attachments()
            attachments_data.file_name = single_record.text
            external_url = single_record.click()
            file_dwn = Doc_Download.file_download()
            attachments_data.external_url= (str(file_dwn[0]))
            attachments_data.file_type = attachments_data.file_name.split('.')[-1]
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)

    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    page_main.execute_script("window.history.go(-1)")


    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.notice_deadline) + str(notice_data.local_title)
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
    urls = ["https://www.devnetjobsindia.org/rfp_assignments.aspx"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)

        try:
            for page_no in range(2,5): #5
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#ContentPlaceHolder1_grdJobs > tbody > tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#ContentPlaceHolder1_grdJobs > tbody > tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#ContentPlaceHolder1_grdJobs > tbody > tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
                try:   
                    next_page = WebDriverWait(page_main, 10).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 10).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#ContentPlaceHolder1_grdJobs > tbody > tr'),page_check))
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
