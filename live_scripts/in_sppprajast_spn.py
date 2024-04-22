from gec_common.gecclass import *
import logging
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
from selenium.webdriver.support.select import Select

from selenium.webdriver.common.keys import Keys
import cv2

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "in_sppprajast_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'in_sppprajast_spn'
    
    # Onsite Field -some records are published in "HINDI" also
    # Onsite Comment -None
    notice_data.main_language = 'EN'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)

    notice_data.procurement_method = 2

    notice_data.notice_type = 4

    notice_data.currency = 'INR'
    
    notice_data.notice_url = url

    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(2)").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(3)").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        document_opening_time = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
        document_opening_time = re.findall('\d+/\d+/\d{4}',document_opening_time)[0]
        notice_data.document_opening_time = datetime.strptime(document_opening_time,'%d/%m/%Y').strftime('%Y-%m-%d')
    except Exception as e:
        logging.info("Exception in document_opening_time: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None
    
    try:
        notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(8) > a').click()                     
        time.sleep(3)
        page_main.switch_to.window(page_main.window_handles[1]) 
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
        
        
    
    try:
        notice_data.notice_no = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,"//*[contains(text(),'NIB Reference no')]//following::td[1]"))).text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    try:
        est_amount = page_main.find_element(By.XPATH, "//*[contains(text(),'Bid Amount')]//following::td[1]").text
        est_amount = re.sub("[^\d\.\,]","",est_amount)
        notice_data.est_amount = float(est_amount)
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        grossbudgetlc = page_main.find_element(By.XPATH, "//*[contains(text(),'Bid Amount')]//following::td[1]").text
        grossbudgetlc = re.sub("[^\d\.\,]","",grossbudgetlc)
        notice_data.grossbudgetlc = float(grossbudgetlc)
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_contract_type = page_main.find_element(By.XPATH, "//*[contains(text(),'Bid Type')]//following::td[1]").text
        if 'Goods' in notice_contract_type:
            notice_data.notice_contract_type = 'Supply'
        elif 'Works' in notice_contract_type:
            notice_data.notice_contract_type = 'Works'
        elif 'Services' in notice_contract_type:
            notice_data.notice_contract_type = 'Services'
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.local_title = page_main.find_element(By.XPATH, "//*[contains(text(),'Bid Title')]//following::td[1]").text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.notice_summary_english = page_main.find_element(By.XPATH, "//*[contains(text(),'Bid Title')]//following::td[1]").text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_main.find_element(By.XPATH, "//*[contains(text(),'Bid Title')]//following::td[1]").text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.document_type_description = page_main.find_element(By.XPATH, "//*[contains(text(),'Bid Pattern')]//following::td[1]").text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, '#print-this-table > tbody').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        customer_details_data = customer_details()
    # Onsite Field -also take "//*[contains(text(),'Department Type')]//following::td[1]" take this selector too in org_name  and split both the data by "comma" ","
    # Onsite Comment -None

        customer_details_data.org_name = page_main.find_element(By.XPATH, "//*[contains(text(),'Department Name')]//following::td[1]").text
        

    # Onsite Field -None
    # Onsite Comment -None

        try:
            customer_details_data.contact_person = page_main.find_element(By.XPATH, "//*[contains(text(),'Procuring Entity Name:')]//following::td[1]").text
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass

    # Onsite Field -None
    # Onsite Comment -None

        try:
            org_address = page_main.find_element(By.XPATH, "//*[contains(text(),'Office Address:')]//following::td[1]").text.split('PIN')[0].strip()
            customer_details_data.org_address = org_address.rstrip(',')
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -split "Fax No. :" from the data
        # Onsite Comment -None

        try:
            customer_details_data.org_fax = page_main.find_element(By.XPATH, "//*[contains(text(),'Office Address:')]//following::td[1]").text.split('Fax No.:')[1].strip()
        except Exception as e:
            logging.info("Exception in org_fax: {}".format(type(e).__name__))
            pass

    # Onsite Field -None
    # Onsite Comment -None

        try:
            email = page_main.find_element(By.XPATH, "//*[contains(text(),'Entity Contact')]//following::td[1]").text.split('Email:')[1].split('Mobile:')[0].strip()
            org_email = email.replace('[at]','@').replace('[dot]','.')
            customer_details_data.org_email = org_email.rstrip(',')
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass

    # Onsite Field -split "Phone No." from data
    # Onsite Comment -None

        try:
            customer_details_data.org_phone = page_main.find_element(By.XPATH, "//*[contains(text(),'Office Address:')]//following::td[1]").text.split('Phone No.:')[1].split(',')[0].strip()
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass

        customer_details_data.org_country = 'IN'
        customer_details_data.org_language = 'EN'
    # Onsite Field -split data for "Pin"
    # Onsite Comment -None

        try:
            customer_details_data.postal_code = page_main.find_element(By.XPATH, "//*[contains(text(),'Office Address:')]//following::td[1]").text.split('PIN:')[1].split(',')[0].strip()
        except Exception as e:
            logging.info("Exception in postal_code: {}".format(type(e).__name__))
            pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -None


    try:              
        attachments_data = attachments()
        attachments_data.file_type = 'pdf'
        attachments_data.file_name = 'Bid Document'
       
        attachments_data.external_url = page_main.find_element(By.XPATH, "//*[contains(text(),'Bid Document')]//following::td[1]/a").get_attribute('href')

        try:
            attachments_data.file_size = page_main.find_element(By.XPATH, "//*[contains(text(),'Bid Document')]//following::td[1]").text.split(']')[1].strip()
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
    
    WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/table/tbody/tr[2]/td/table/tbody/tr[1]/td[2]/form/table/tbody/tr[5]/td/div/div[2]/div/table/tbody/tr'))).text
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body

options = webdriver.ChromeOptions()
options.add_extension("Rumola-bypass-CAPTCHA.crx")
page_main = webdriver.Chrome(options=options)
time.sleep(2)

options = webdriver.ChromeOptions()
options.add_extension("Rumola-bypass-CAPTCHA.crx")
page_details = webdriver.Chrome(options=options)
time.sleep(2)

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://sppp.rajasthan.gov.in/bidlist.php"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        spp_click = WebDriverWait(page_main, 30).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="navbarNav"]/ul[2]/li[1]/a')))
        page_main.execute_script("arguments[0].click();",spp_click)
        
        bid_search_click = WebDriverWait(page_main, 30).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="leftpanel2"]/table/tbody/tr[5]/td/div/ul/li[5]/a')))
        page_main.execute_script("arguments[0].click();",bid_search_click)
        
        pp_btn = Select(page_main.find_element(By.XPATH,'//*[@id="ddlfinancialyear"]'))
        pp_btn.select_by_index(1)
        
        time.sleep(3)
        while True:
            time.sleep(15) #######to give time to extention to solve captcha
            check = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="btnsearch"]')))
            page_main.execute_script("arguments[0].click();",check)
            
            try:
                table_row = WebDriverWait(page_main, 20).until(EC.presence_of_element_located((By.XPATH,'//*[@id="examplesearch"]/tbody/tr[1]'))).text
                break
            except:
                try:
                    elementRefresh = page_main.find_element(By.XPATH, '//*[@id="tblformdesign"]/tbody/tr[3]/td/table/tbody/tr[15]/td[2]/a')  
                    elementRefresh.click()
                    input1 = page_main.find_element(By.XPATH,'//*[@id="txtcaptcha"]').clear()
                except:
                    pass
        time.sleep(15)
        try:
            for page_no in range(2,10):
                page_check = WebDriverWait(page_main, 80).until(EC.presence_of_element_located((By.XPATH,'/html/body/table/tbody/tr[2]/td/table/tbody/tr[1]/td[2]/form/table/tbody/tr[5]/td/div/div[2]/div/table/tbody/tr'))).text
                rows = WebDriverWait(page_main, 80).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/table/tbody/tr[2]/td/table/tbody/tr[1]/td[2]/form/table/tbody/tr[5]/td/div/div[2]/div/table/tbody/tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 80).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/table/tbody/tr[2]/td/table/tbody/tr[1]/td[2]/form/table/tbody/tr[5]/td/div/div[2]/div/table/tbody/tr')))[records]
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
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/table/tbody/tr[2]/td/table/tbody/tr[1]/td[2]/form/table/tbody/tr[5]/td/div/div[2]/div/table/tbody/tr'),page_check))
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
