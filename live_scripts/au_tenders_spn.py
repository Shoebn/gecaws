from gec_common.gecclass import *
import logging
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
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.support.ui import Select

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "au_tenders_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = "au_tenders_spn"
    notice_data.main_language = 'EN'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'AU'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'AUD'
    notice_data.procurement_method = 2
    notice_data.notice_type = 4
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-sm-4 > div > p').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-sm-8 div > div:nth-child(1) div').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div.last-updated").text
        publish_date = re.findall('\d+-\w+-\d{4} \d+:\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d-%b-%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(6) >div > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.box.boxW.listInner').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    

    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Description")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    try:
        notice_deadline = page_details.find_element(By.XPATH, '''//*[contains(text(),"Close Date & Time")]//following::div[1]''').text
        notice_deadline = re.findall('\d+-\w+-\d{4} \d+:\d+ [apAP][mM]',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d-%b-%Y %I:%M %p').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),"Description")]//following::div').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.document_type_description = page_details.find_element(By.XPATH, '//*[contains(text(),"ATM Type")]//following::div').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    try:
        est_amount = page_details.find_element(By.XPATH, '//*[contains(text(),"Estimated Value (AUD)")]//following::div[1]').text.split('to')[1].strip()
        est_amount = re.sub("[^\d\.\,]", "",est_amount)
        notice_data.est_amount = float(est_amount.replace(',','').strip())
    except Exception as e: 
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    try:
        netbudgetlc = page_details.find_element(By.XPATH, '//*[contains(text(),"Estimated Value (AUD)")]//following::div[1]').text.split('to')[1].strip()
        netbudgetlc = re.sub("[^\d\.\,]", "",netbudgetlc)
        notice_data.netbudgetlc = float(netbudgetlc.replace(',','').strip())
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'AU'
        customer_details_data.org_language = 'EN'

        customer_details_data.org_name = page_details.find_element(By.CSS_SELECTOR, 'div.box div:nth-child(2) > div').text
        

        try:
            customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Contact Details")]//following::p[1]').text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass

        try:
            customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Contact Details")]//following::a[1]').text
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass

        try:
            customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Contact Details")]//following::p[2]').text
            if('Email' in customer_details_data.org_phone):
                customer_details_data.org_phone = ''
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass


        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:
        cpv_no = page_details.find_element(By.XPATH, '//*[last()][contains(text(),"Category")]//following::div[1]').text.split(' - ')[0].strip()
        cpv_codes = fn.CPV_mapping("assets/au_tenders_spn_cpv.csv",cpv_no)
        for cpv_code in cpv_codes:
            cpvs_data = cpvs()
            cpvs_data.cpv_code = cpv_code
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in category: {}".format(type(e).__name__))
        pass
    
    try:
        cpv_no = page_details.find_element(By.XPATH, '//*[last()][contains(text(),"Category")]//following::div[1]').text.split(' - ')[0].strip()
        cpv_codes = fn.CPV_mapping("assets/au_tenders_spn_cpv.csv",cpv_no)
        cpv_at_source = ''
        for cpv_code in cpv_codes:
            cpv_at_source += cpv_code
            cpv_at_source += ',' 
        cpv_source = cpv_at_source.rstrip(',')
        notice_data.cpv_at_source = cpv_source
    except Exception as e:
        logging.info("Exception in cpv_at_source: {}".format(type(e).__name__))
        pass

    try:
        documents_btn = page_details.find_element(By.LINK_TEXT,'ATM Documents').get_attribute('href')
        logging.info('documents url: ' +documents_btn)
        fn.load_page(page_details1,documents_btn,80)
        time.sleep(5)

        email_box = page_details1.find_element(By.ID,'form-Email')
        email_box.send_keys('akanksha@globalecontent.com')
        time.sleep(2)

        psw = page_details1.find_element(By.ID,'form-Password')
        psw.send_keys('dg@1234567')
        time.sleep(2)

        login = page_details1.find_element(By.CSS_SELECTOR,'input.btn-submit')
        page_details1.execute_script("arguments[0].click();",login)
        time.sleep(5)
    except Exception as e:
        logging.info("Exception in login: {}".format(type(e).__name__)) 
        pass
    
    try:
        for single_record in page_details1.find_elements(By.CSS_SELECTOR, '#mainContent > div > div.row > div.col-sm-8 > div > ul > li > a'):
            attachments_data = attachments()

            try:
                file_type = single_record.text
                if('pdf' in file_type):
                    attachments_data.file_type = 'pdf'
                if('docx' in file_type):
                    attachments_data.file_type = 'docx'
                if('zip' in file_type):
                    attachments_data.file_type = 'zip'
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass

            try:
                attachments_data.file_size = single_record.find_element(By.CSS_SELECTOR, 'span.size').text
            except Exception as e:
                logging.info("Exception in file_size: {}".format(type(e).__name__))
                pass

            attachments_data.file_name = single_record.text.split('.')[0].strip()

            attachments_data.external_url = single_record.get_attribute('href')


            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) + str(notice_data.publish_date) +  str(notice_data.notice_url) 
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
page_details = webdriver.Chrome(options=options)
page_details1 = webdriver.Chrome(options=options)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.tenders.gov.au/atm"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        try:
            login_click =  WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#s2menu > li.menu-login'))).click()
        except:
            pass
        
        #******************************page_main login********************************************
        try:
            username = page_main.find_element(By.ID,'login-username')
            page_main.execute_script("arguments[0].click();",username)
            time.sleep(2)

            page_main.find_element(By.ID,'login-username').send_keys('akanksha@globalecontent.com')
            time.sleep(2)

            password = page_main.find_element(By.ID,'login-password')
            page_main.execute_script("arguments[0].click();",password)
            time.sleep(2)

            page_main.find_element(By.ID,'login-password').send_keys('dg@1234567')

            page_main.find_element(By.XPATH,'//*[@id="login-form"]/input[5]').click()
            login = WebDriverWait(page_main, 20).until(EC.presence_of_element_located((By.XPATH,'//*[@id="mainContent"]/div/div[4]/div'))).text
            time.sleep(4)

            sort_click = WebDriverWait(page_main, 80).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="sortForm"]/div/div/div/div[2]/div/div[2]/div/div/div/button')))
            page_main.execute_script("arguments[0].click();",sort_click)

            sort_descending = page_main.find_element(By.XPATH,'//*[@id="sortForm"]/div/div/div/div[2]/div/div[2]/div/div/div/div/ul/li[8]/a/span[1]')
            page_main.execute_script("arguments[0].click();",sort_descending)

            sort_click_selected = page_main.find_element(By.XPATH,'//*[@id="form-sort-1"]')
            page_main.execute_script("arguments[0].click();",sort_click_selected)
        except:
            pass

        try: 
            for page_no in range(2,10):#10
                page_check = WebDriverWait(page_main, 80).until(EC.presence_of_element_located((By.CSS_SELECTOR,'div.boxEQH div.row'))).text
                rows = WebDriverWait(page_main, 80).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.boxEQH div.row')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 80).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.boxEQH div.row')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
                        
                    if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                        logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                        break
    
                try:   
                    next_page = WebDriverWait(page_main, 80).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'div.boxEQH div.row'),page_check))
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
