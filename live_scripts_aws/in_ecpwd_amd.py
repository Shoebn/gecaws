from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "in_ecpwd_amd"
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
SCRIPT_NAME = "in_ecpwd_amd"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    # Onsite Field -None
    # Onsite Comment -Note:Click on " Corrigendum " Keyword Than click "View More" keyword
    notice_data.script_name = 'in_ecpwd_amd'
    
    notice_data.main_language = 'EN'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'INR'
    
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 16
    
    # Onsite Field -NIT/RFP NO
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(3) tr td:nth-child(2)').text
    except:
        try:
            notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(3) tr td:nth-child(1)').text
        except Exception as e:
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass
        
    # Onsite Field -EMD Amount
    # Onsite Comment -None

    try:
        earnest_money_deposit = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(3) td:nth-child(8)').text
        earnest_money_deposit = re.sub("[^\d\.\,]", "", earnest_money_deposit)
        earnest_money_deposit = earnest_money_deposit.replace('.','').replace(',','').strip()
        notice_data.earnest_money_deposit = earnest_money_deposit
    except Exception as e:
        logging.info("Exception in earnest_money_deposit: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Latest Corrigendum Issued Date
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div:nth-child(3) td:nth-child(6)").text
        publish_date = re.findall('\d+/\d+/\d{4} \d+:\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Latest Corrigendum Issued Date
    # Onsite Comment -None

    try:
        document_purchase_start_time = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(3) td:nth-child(6)').text
        document_purchase_start_time = re.findall('\d+/\d+/\d{4}',document_purchase_start_time)[0]
        notice_data.document_purchase_start_time = datetime.strptime(document_purchase_start_time,'%d/%m/%Y').strftime('%Y/%m/%d')
    except Exception as e:
        logging.info("Exception in document_purchase_start_time: {}".format(type(e).__name__))
        pass
    
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = 'Central Public Works Department '
        customer_details_data.org_parent_id = '7522430'            
        customer_details_data.org_country = 'IN'
        customer_details_data.org_language = 'EN'
        
        try:
            customer_details_data.org_address = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass
        
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
#     # Onsite Field -Action
#     # Onsite Comment -None

        
    try:
        notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(9) > a').click()                       
        time.sleep(10) 
        notice_data.notice_url = page_main.current_url
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
    
    
    try:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, '#content').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    # Onsite Field -Name of Work
    # Onsite Comment -None

    try:
        notice_data.local_title = page_main.find_element(By.CSS_SELECTOR, 'tr:nth-child(2) > td.tdwhite').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
#     # Onsite Field -Estimated Cost
#     # Onsite Comment -None

    try:
        est_amount = page_main.find_element(By.CSS_SELECTOR, 'tr:nth-child(4) > td:nth-child(4)').text
        est_amount = re.sub("[^\d\.\,]", "",est_amount)
        est_amount = est_amount.replace('.','').replace(',','').strip()
        notice_data.est_amount = float(est_amount)
        notice_data.grossbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
 
    
    try:
        notice_data.contract_type_actual = page_main.find_element(By.XPATH, '//*[contains(text(),"Procurement Type")]//following::td[1]').text
        if "Services" in notice_data.contract_type_actual:
            notice_data.notice_contract_type ="Service"
        elif "Works" in notice_data.contract_type_actual:
            notice_data.notice_contract_type ="Works"
        elif "Goods" in notice_data.contract_type_actual:
            notice_data.notice_contract_type ="Supply"
        else:
            pass
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass
    
#     # Onsite Field -Bid Submission Closing Date
#     # Onsite Comment -None

    try:
        notice_deadline = page_main.find_element(By.XPATH, '//*[contains(text(),"Bid Submission Closing Date")]//following::td[1]').text
        notice_deadline = re.findall('\d+/\d+/\d{4} \d+:\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
#     # Onsite Field -Bid Submission Closing Date
#     # Onsite Comment -None

    try:
        document_purchase_end_time = page_main.find_element(By.XPATH, '//*[contains(text(),"Bid Submission Closing Date")]//following::td[1]').text
        document_purchase_end_time = re.findall('\d+/\d+/\d{4}',document_purchase_end_time)[0]
        notice_data.document_purchase_end_time = datetime.strptime(document_purchase_end_time,'%d/%m/%Y').strftime('%Y/%m/%d')
    except Exception as e:
        logging.info("Exception in document_purchase_end_time: {}".format(type(e).__name__))
        pass
    
    
    # Onsite Field -Corrigendum Conditions
    # Onsite Comment -Note:Go to Action >> Action "tr > td:nth-child(5) > a" >> Corrigendum Conditions  "div:nth-child(4)" Grap thear data.
    try:
        attach = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'td:nth-child(5) > a')))
        page_main.execute_script("arguments[0].click();",attach)
        time.sleep(5)
    except:
        pass

    try:   
        attachments_data = attachments()

    # Onsite Field -Letter of Authorization
    # Onsite Comment -Note:Don't take file extention

        attachments_data.file_name = page_main.find_element(By.XPATH, '//*[contains(text(),"Letter of Authorization")]//following::a[1]').text.split(".")[0].strip()


    # Onsite Field -Letter of Authorization
    # Onsite Comment -Note:Take only file extention

        try:
            attachments_data.file_type = page_main.find_element(By.XPATH, '//*[contains(text(),"Letter of Authorization")]//following::a[1]').text.split(".")[1].strip()
        except Exception as e:
            logging.info("Exception in file_type: {}".format(type(e).__name__))
            pass

    # Onsite Field -Letter of Authorization
    # Onsite Comment -None

        external_url = page_main.find_element(By.XPATH, '//*[contains(text(),"Letter of Authorization")]//following::a[1]').click()
        time.sleep(10)
        file_dwn = Doc_Download.file_download()
        attachments_data.external_url = str(file_dwn[0])

        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    back_clk = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR, '#back'))).click()
    time.sleep(2)
    
    back_clk = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR, '#back'))).click()
    time.sleep(2)
    
    try:
        WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,' th.tdCenter.w80px.sorting_asc')))
    except:
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['−−incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']

page_main = Doc_Download.page_details
page_main.maximize_window()

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://etender.cpwd.gov.in/"]
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        time.sleep(5)

        try:
            time.sleep(3)
            page_main.find_element(By.LINK_TEXT,"OK").click()
            time.sleep(2)
            alert = page_main.switch_to.alert
            alert.dismiss()
        except:
            pass
        
        Corrigendum = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="corrigendumsDiv"]')))
        page_main.execute_script("arguments[0].click();",Corrigendum)
        time.sleep(5)

        view_more = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#viewCurrentall')))
        page_main.execute_script("arguments[0].click();",view_more)
        time.sleep(5)

        try:
            for page_no in range(2,5):#5
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="pagetable14"]/tbody/tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="pagetable14"]/tbody/tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="pagetable14"]/tbody/tr')))[records]
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
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="pagetable14"]/tbody/tr'),page_check))
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
    pass
finally:
    page_main.quit()
    
    output_json_file.copyFinalJSONToServer(output_json_folder)
