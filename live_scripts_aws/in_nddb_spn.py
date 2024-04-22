from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "in_nddb"
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
from selenium.webdriver.support.ui import Select

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "in_nddb"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    global page_details
    notice_data = tender()
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'INR'
    notice_data.main_language = 'EN'
    notice_data.procurement_method = 2
    notice_data.script_name = 'in_nddb_spn'
    notice_data.notice_type = 4
    
    try:
        notice_data.notice_url = tender_html_element.get_attribute('onclick').split("('")[1].split("')")[0]
        fn.load_page(page_details,notice_data.notice_url,80)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__)) 
        pass
      
    username1  = page_details.find_element(By.CSS_SELECTOR,'#ctl00_PlaceHolderMain_g_ec601e0c_ea88_4eff_998e_41b537a1a5f6_txtUserName').send_keys('dgMarket')
    password1  = page_details.find_element(By.CSS_SELECTOR,'#ctl00_PlaceHolderMain_g_ec601e0c_ea88_4eff_998e_41b537a1a5f6_txtPwd').send_keys('Ak@123456')
    submit1 = page_details.find_element(By.CSS_SELECTOR,'#ctl00_PlaceHolderMain_g_ec601e0c_ea88_4eff_998e_41b537a1a5f6_btnLogin').click()
    time.sleep(20)
    
    page_check = WebDriverWait(page_details, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/form/div[8]/div[1]/div[4]/div[2]/div[2]/div/div/table/tbody/tr[1]/td/table/tbody/tr[2]/td/table/tbody/tr/td/div/div/table[2]/tbody/tr/td/table/tbody/tr[2]/td[1]/span'))).text
    
    try:
        notice_data.notice_no = page_details.find_element(By.XPATH,'//*[@id="ctl00_m_g_5772073c_5a98_4c69_a90f_a8384f10f5f5"]/table[2]/tbody/tr/td/table/tbody/tr[2]/td[2]').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__)) 
        pass

    try:
        notice_data.local_title = page_details.find_element(By.XPATH, '//*[@id="ctl00_m_g_5772073c_5a98_4c69_a90f_a8384f10f5f5_lblTenderNameValue"]').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in notice_title: {}".format(type(e).__name__)) 
        pass
       
    try:
        publish_date =  page_details.find_element(By.XPATH, '//*[@id="ctl00_m_g_5772073c_5a98_4c69_a90f_a8384f10f5f5_lblTenderSaleDateandTimeValue"]').text
        notice_data.publish_date = datetime.strptime(publish_date, '%d-%m-%Y %H:%M %p').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__)) 
        pass
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    try:
        notice_deadline = page_details.find_element(By.XPATH, '//*[@id="ctl00_m_g_5772073c_5a98_4c69_a90f_a8384f10f5f5_lblLastDateofBidReceiptandTimeValue"]').text
        notice_data.notice_deadline = datetime.strptime(notice_deadline, '%d-%m-%Y %H:%M %p').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__)) 
        pass 
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[@id="ctl00_m_g_5772073c_5a98_4c69_a90f_a8384f10f5f5_lblDescriptionValue"]').text
        notice_data.notice_summary_english = notice_data.local_description 
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__)) 
        pass 
    try:
        notice_data.category = page_details.find_element(By.XPATH, '//*[@id="ctl00_m_g_5772073c_5a98_4c69_a90f_a8384f10f5f5_lblTypeOfWorkValue"]').text
    except Exception as e:
        logging.info("Exception in category: {}".format(type(e).__name__)) 
        pass
    try:
        notice_data.document_fee = page_details.find_element(By.XPATH, '//*[@id="ctl00_m_g_5772073c_5a98_4c69_a90f_a8384f10f5f5_lblCostOfTenderDocumentValue"]').text
    except Exception as e:
        logging.info("Exception in document_fee: {}".format(type(e).__name__)) 
        pass
    try:
        document_opening_time = page_details.find_element(By.XPATH, '//*[@id="ctl00_m_g_5772073c_5a98_4c69_a90f_a8384f10f5f5_lblBidOpenigDateandTimeValue"]').text
        document_opening_time = re.findall(r'\d+-\d+-\d{4}',document_opening_time)[0]
        notice_data.document_opening_time = datetime.strptime(document_opening_time, '%d-%m-%Y').strftime('%Y-%m-%d')
    except Exception as e:
        logging.info("Exception in document_opening_time: {}".format(type(e).__name__)) 
        pass 
    try:
        document_purchase_start_time = page_details.find_element(By.XPATH, '//*[@id="ctl00_m_g_5772073c_5a98_4c69_a90f_a8384f10f5f5_lblTenderSaleDateandTimeValue"]').text
        document_purchase_start_time = re.findall(r'\d+-\d+-\d{4}',document_purchase_start_time)[0]
        notice_data.document_purchase_start_time = datetime.strptime(document_purchase_start_time,'%d-%m-%Y').strftime('%Y/%m/%d')
    except Exception as e:
        logging.info("Exception in document_purchase_start_time: {}".format(type(e).__name__))
        pass

    try:
        document_purchase_end_time = page_details.find_element(By.XPATH, '//*[@id="ctl00_m_g_5772073c_5a98_4c69_a90f_a8384f10f5f5_lblTenderCloseDateandTimeValue"]').text
        document_purchase_end_time = re.findall(r'\d+-\d+-\d{4}',document_purchase_end_time)[0]
        notice_data.document_purchase_end_time = datetime.strptime(document_purchase_end_time,'%d-%m-%Y').strftime('%Y/%m/%d')
    except Exception as e:
        logging.info("Exception in document_purchase_start_time: {}".format(type(e).__name__))
        pass
    try:
        pre_bid_meeting_date = page_details.find_element(By.XPATH, '//*[@id="ctl00_m_g_5772073c_5a98_4c69_a90f_a8384f10f5f5"]/table[2]/tbody/tr/td/table/tbody/tr[8]/td[2]').text
        pre_bid_meeting_date = re.findall(r'\d+-\d+-\d{4}',pre_bid_meeting_date)[0]
        notice_data.pre_bid_meeting_date = datetime.strptime(pre_bid_meeting_date,'%d-%m-%Y').strftime('%Y/%m/%d')
    except Exception as e:
        logging.info("Exception in pre_bid_meeting_date: {}".format(type(e).__name__))
        pass
    try:
        est_amount = page_details.find_element(By.XPATH, '//*[@id="ctl00_m_g_5772073c_5a98_4c69_a90f_a8384f10f5f5_lblEstimatedCostValue"]').text
        est_amount = est_amount.split('INR')[0]
        notice_data.est_amount = float(est_amount)
        notice_data.grossbudgetlc = float(est_amount)
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    try:
        notice_data.earnest_money_deposit = page_details.find_element(By.XPATH, '//*[@id="ctl00_m_g_5772073c_5a98_4c69_a90f_a8384f10f5f5_lblEMDValueValue"]').text
    except Exception as e:
        logging.info("Exception in earnest_money_deposit: {}".format(type(e).__name__))
        pass
    try:
        notice_data.contract_duration = page_details.find_element(By.XPATH, '//*[@id="ctl00_m_g_5772073c_5a98_4c69_a90f_a8384f10f5f5"]/table[2]/tbody/tr/td/table/tbody/tr[16]/td[2]').text
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass
    try:
        notice_data.eligibility = page_details.find_element(By.XPATH, '//*[@id="ctl00_m_g_5772073c_5a98_4c69_a90f_a8384f10f5f5_lblEligibilityValue"]').text
    except Exception as e:
        logging.info("Exception in eligibility: {}".format(type(e).__name__))
        pass

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[@id="ctl00_m_g_5772073c_5a98_4c69_a90f_a8384f10f5f5_lblIssuedByValue"]').text.split(',')[0]
        try:
            customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[@id="ctl00_m_g_5772073c_5a98_4c69_a90f_a8384f10f5f5_lblIssuedByValue"]').text
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
    
    try:
        for single_record in page_details.find_elements(By.XPATH,'//*[@id="ctl00_m_g_5772073c_5a98_4c69_a90f_a8384f10f5f5"]/table[1]/tbody/tr/td/table/tbody/tr[2]/td[2]/a'):
            attachments_data = attachments()
            try:
                single_record.click()
                time.sleep(5)
                page_details.switch_to.window(page_details.window_handles[1]) 
                time.sleep(5)
                attachments_data.external_url = page_details.current_url
                time.sleep(5)
                page_details.close()
                time.sleep(3)
                page_details.switch_to.window(page_details.window_handles[0])
                attachments_data.attachments_cleanup()
                attachments_data.file_type = attachments_data.external_url.split('.')[-1]
                attachments_data.file_name = tender_html_element.text
                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
            except:
                pass

    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass 

    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
        notice_data.notice_text += page_details.find_element(By.XPATH,'//*[@id="ctl00_m_g_5772073c_5a98_4c69_a90f_a8384f10f5f5"]').get_attribute('outerHTML')
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.notice_deadline) + str(notice_data.local_title)
    logging.info(notice_data.identifier)
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

    urls = ['http://tenders.nddb.coop/SitePages/Tenders.aspx'] 

    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
            
        try:
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/form/div[8]/div[1]/div[4]/div[2]/div[2]/div/div/table/tbody/tr[1]/td/table/tbody/tr[1]/td/table/tbody/tr/td/div/div/table/tbody/tr[7]/td/table[1]/tbody/tr/td[2]/a')))
            length = len(rows) 
            for records in range(0,length,2):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/form/div[8]/div[1]/div[4]/div[2]/div[2]/div/div/table/tbody/tr[1]/td/table/tbody/tr[1]/td/table/tbody/tr/td/div/div/table/tbody/tr[7]/td/table[1]/tbody/tr/td[2]/a')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
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
    page_details.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)
