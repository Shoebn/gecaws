from gec_common.gecclass import *
import logging
import re
import jsons
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
import gec_common.OutputJSON
from gec_common import functions as fn
from selenium.webdriver.chrome.options import Options
from deep_translator import GoogleTranslator

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "us_txsmartbuy"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.main_language = 'EN'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'US'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'USD'
    notice_data.procurement_method = 2
    notice_data.document_type_description = 'Solicitations'
    notice_data.notice_type = 4

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.esbd-result-title').text
        notice_data.notice_title = GoogleTranslator(source='es', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div.esbd-result-body-columns > div:nth-child(1) > p:nth-child(1').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
        
    try:
        notice_type = tender_html_element.find_element(By.CSS_SELECTOR, 'div.esbd-result-body-columns > div:nth-child(2) > p:nth-child(2)').text
        if "Addendum Posted" in notice_type:
            notice_data.notice_type = 16
            notice_data.script_name = 'us_txsmartbuy_amd'
        else:
            notice_data.notice_type = 4
            notice_data.script_name = 'us_txsmartbuy_spn'
    except Exception as e:
        logging.info("Exception in notice_type: {}".format(type(e).__name__))
        pass

                
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.esbd-result-title > a').get_attribute("href")                     
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url

    try: 
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, 'div.esbd-result-body-columns > div:nth-child(2) > p:nth-child(3)').text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%m/%d/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try: 
        due_date = tender_html_element.find_element(By.CSS_SELECTOR,'div.esbd-result-body-columns > div:nth-child(1) > p:nth-child(2)').text
        deadline = re.findall('\d+/\d+/\d{4}',due_date)[0]
        due_time = tender_html_element.find_element(By.CSS_SELECTOR,'div.esbd-result-body-columns > div:nth-child(1) > p:nth-child(3)').text
        deadline_time = re.findall('\d+:\d+',due_time)[0]
        notice_deadline = deadline + ' '+ deadline_time
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%m/%d/%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    try:
        fn.load_page(page_details,notice_data.notice_url,120)
        try:
            cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Class/Item Code: ")]//following::p[1]').text
            cpv_code_title = re.split("\d{5}-", cpv_code)
            class_title_at_source = ''
            for cpv_title in cpv_code_title[1:]:
    
                class_title_at_source += cpv_title.strip()
                class_title_at_source += ','
            notice_data.class_title_at_source = class_title_at_source.rstrip(',')
        except Exception as e:
            logging.info("Exception in class_title_at_source1: {}".format(type(e).__name__)) 
            pass
    
        try:
            class_codes_at_source = ''
            cpv_at_source = ''
            codes_at_source = page_details.find_element(By.XPATH, '//*[contains(text(),"Class/Item Code: ")]//following::p[1]').text
            cpv_regex = re.compile(r'\d{5}')
            code_list = cpv_regex.findall(codes_at_source)
            for cpv_codes in code_list:
                
                class_codes_at_source += cpv_codes
                class_codes_at_source += ','
        
                cpv_codes_list = fn.CPV_mapping("assets/NIGPcode.csv",cpv_codes)
                for each_cpv in cpv_codes_list:
                    cpvs_data = cpvs()
                    cpvs_data.cpv_code = each_cpv
        
                    cpv_at_source += each_cpv
                    cpv_at_source += ','
        
                    cpvs_data.cpvs_cleanup()
                    notice_data.cpvs.append(cpvs_data)
        
            notice_data.class_codes_at_source = class_codes_at_source.rstrip(',')
            notice_data.cpv_at_source = cpv_at_source.rstrip(',')
        except:
            pass
            
        try:
            notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Solicitation Description")]//parent::div[1]').text.split('Solicitation Description:')[1].strip()
            notice_data.notice_summary_english = notice_data.local_description
        except Exception as e:
            logging.info("Exception in notice_summary_english: {}".format(type(e).__name__)) 
            pass 
    
        
        try:              
            customer_details_data = customer_details()
            org_name =  page_details.find_element(By.XPATH, '//*[contains(text(),"Solicitation Description")]//parent::div[1]').text.split('Solicitation Description:')[1].strip()
            org_name1 = org_name[:50]
            if '(' in  org_name1:
                customer_details_data.org_name = org_name1.split('(')[0].strip()
            else:
                customer_details_data.org_name = 'txsmartbuy'
    
            try:
                customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Contact Number")]//following::p[1]').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
                
            try:
                customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Contact Name")]//following::p[1]').text
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass
                
            try:
                customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Contact Email")]//following::p[1]').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
    
            customer_details_data.org_country = 'US'
            customer_details_data.org_language = 'EN'
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
        except Exception as e:
            logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
            pass
    
        try:
            try:
                est_amount = page_details.find_element(By.XPATH, '//*[contains(text(),"Solicitation Description: ")]//parent::div[1]').text.split('EST. COST:')[1].strip()
            except:
                est_amount = page_details.find_element(By.XPATH, '//*[contains(text(),"ESTIMATED")]//following::td[1]').text
            est_amount = re.sub("[^\d\.\,]", "", est_amount)
            notice_data.est_amount = float(est_amount.replace(',','').strip())
            notice_data.grossbudgetlc = notice_data.est_amount
        except Exception as e:
            logging.info("Exception in est_amount: {}".format(type(e).__name__))
            pass
    
        try:
            earnest_money_deposit = page_details.find_element(By.XPATH, '//*[contains(text(),"BID GUARANTY/BID")]//following::td[1]').text
            notice_data.earnest_money_deposit = earnest_money_deposit
        except Exception as e:
            logging.info("Exception in earnest_money_deposit: {}".format(type(e).__name__))
            pass
    
        try:
            pre_bid_meeting_date = page_details.find_element(By.XPATH, '//*[contains(text(),"PRE-BID MEETING")]//following::td[1]').text
            pre_bid_meeting_date = re.findall('\w+ \d+, \d{4} \w+ \d{2}:\d{2} \w+',pre_bid_meeting_date)[0]
            notice_data.pre_bid_meeting_date = datetime.strptime(pre_bid_meeting_date,'%b %d, %Y @ %H:%M %p').strftime('%Y/%m/%d %H:%M:%S')
        except Exception as e:
            logging.info("Exception in pre_bid_meeting_date: {}".format(type(e).__name__))
            pass
    
        try:
            notice_data.tender_contract_number = page_details.find_element(By.XPATH, '//*[contains(text(),"Contact Number")]//following::p[1]').text
        except Exception as e:
            logging.info("Exception in tender_contract_number: {}".format(type(e).__name__))
            pass
            
        try: 
            for single_record in page_details.find_elements(By.CSS_SELECTOR, '#tab-1 > div:nth-child(3) > div > div > p:nth-child(2)  > a'): 
                attachments_data = attachments() 
                ext_url = single_record.get_attribute('data-href')
                attachments_data.external_url = 'https://www.txsmartbuy.com'+ext_url
                attachments_data.file_name = single_record.text
                try:
                    attachments_data.file_type = single_record.external_url.split('.')[-1].strip()
                except:
                    pass
                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
        except Exception as e:
            logging.info("Exception in attachments: {}".format(type(e).__name__)) 
            pass   
    
      
        try:
            notice_data.notice_text += page_details.find_element(By.XPATH, '//*[@id="content"]/div/div').get_attribute("outerHTML")                     
        except Exception as e:
            logging.info("Exception in notice_text: {}".format(type(e).__name__))
            pass
    except:
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) + str(notice_data.publish_date) +  str(notice_data.notice_url) 
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['−−incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver_head(arguments) 
page_details = fn.init_chrome_driver_head(arguments)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://www.txsmartbuy.com/esbd'] 
    for url in urls:
        fn.load_page_expect_xpath(page_main, url, '//*[@id="content"]/div/div/div[3]', 100)
        logging.info('----------------------------------')
        logging.info(url)
        
        select_status = Select(page_main.find_element(By.XPATH,'//*[@id="content"]/div/div/form/div[3]/span/select'))
        select_status.select_by_index(1)
        time.sleep(3)
    

        from_date = th.strftime('%m/%d/%Y')
        
        page_main.find_element(By.XPATH,'//*[@id="content"]/div/div/form/div[9]/span/input').send_keys(from_date)
        time.sleep(3)

        to_date = date.today()
        todate = to_date.strftime('%m/%d/%Y')
        
        page_main.find_element(By.XPATH,'//*[@id="content"]/div/div/form/div[10]/span/input').send_keys(todate)
        time.sleep(3)

        click_search = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#content > div > div > form > div.browse-contract-search-actions > button:nth-child(1)')))
        page_main.execute_script("arguments[0].click();",click_search) 
        time.sleep(5)

        try:
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#content > div > div > div:nth-child(5) > div.esbd-margin-top > div')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#content > div > div > div:nth-child(5) > div.esbd-margin-top > div')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
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
