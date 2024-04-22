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
import gec_common.OutputJSON
from gec_common import functions as fn
from selenium.webdriver.support.ui import Select

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "us_txsmartbuy_pp"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"

def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'us_txsmartbuy_pp'
    
    notice_data.main_language = 'EN'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'US'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.procurement_method = 2
  
    notice_data.currency = 'USD'
        
    notice_data.notice_type = 3
    
    notice_data.class_at_source = 'CPV'
    
    notice_data.document_type_description = 'Pre-Solicitations'
    
    try:                                                                                                                      
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, ' div:nth-child(1) > p:nth-child(1)').text.split('Solicitation ID:')[1].strip()
    except Exception as e:
        logging.info("Exception in notice_no1: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, ' div.esbd-result-title > a').text
        notice_data.notice_title = notice_data.local_title
        if len(notice_data.local_title) < 5:
            return
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "div:nth-child(1) > p:nth-child(2)").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%m/%d/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    try:  
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(2) > p:nth-child(3)').text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%m/%d/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    try:
        notice_data.notice_text += tender_html_element.get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__)) 
        pass
    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.esbd-result-title > a').get_attribute("href")
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__)) 
        pass

    try:
        fn.load_page(page_details,notice_data.notice_url,90)
        logging.info(notice_data.notice_url)
        page_details.refresh()
        time.sleep(5)

        WebDriverWait(page_details, 60).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#main-container')))

        try:
            notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#main-container').get_attribute("outerHTML")                     
        except:
            pass

        try:              
            customer_details_data = customer_details()
            customer_details_data.org_country = 'US'
            customer_details_data.org_language = 'EN'

            org_name =  page_details.find_element(By.XPATH, '//*[@id="content"]/div/div/div[2]/div[2]/div[3]').text.split('Pre-Solicitation Description:')[1].strip()
            org_name1 = org_name[:50]
            if '(' in  org_name1:
                customer_details_data.org_name = org_name1.split('(')[0].strip()
            else:
                customer_details_data.org_name = 'txsmartbuy'

            try:
                customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Contact Name:")]//parent::P[1]').text.split('Contact Name:')[1].strip()
            except Exception as e:
                logging.info("Exception in customer_main_activity: {}".format(type(e).__name__)) 
                pass 

            try:
                customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Contact Number:")]//parent::P[1]').text.split('Contact Number:')[1].strip()
                notice_data.tender_contract_number = customer_details_data.org_phone
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__)) 
                pass

            try:
                customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Contact Email:")]//parent::P[1]').text.split('Contact Email:')[1].strip()
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__)) 
                pass

            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
        except Exception as e:
            logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
            pass 

        try:
            notice_data.local_description = page_details.find_element(By.XPATH, '//*[@id="content"]/div/div/div[2]/div[2]/div[3]').text.split('Pre-Solicitation Description:')[1].strip()
            notice_data.notice_summary_english = notice_data.local_description
        except Exception as e:
            logging.info("Exception in notice_summary_english: {}".format(type(e).__name__)) 
            pass 

        try:         
            for single_record in page_details.find_elements(By.XPATH, '//*[contains(text(),"Attachments")]//following::div[2]/div'):
                attachments_data = attachments()

                attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, ' p.esbd-attachment-link').text

                external_url = single_record.find_element(By.CSS_SELECTOR, ' p.esbd-attachment-link > a').get_attribute("data-href")
                attachments_data.external_url = 'https://www.txsmartbuy.com'+external_url

                try:
                    attachments_data.file_type = attachments_data.external_url.split('.')[-1].strip()
                except:
                    pass

                try:
                    attachments_data.file_description = single_record.find_element(By.CSS_SELECTOR, ' p.esbd-attachment-description.esbd-attachment-hide-mobile').text
                except:
                    pass

                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
        except Exception as e:
            logging.info("Exception in attachments_1: {}".format(type(e).__name__)) 
            pass

        try:
            cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Class/Item Code: ")]//parent::p[1]').text.split('Class/Item Code:')[1].strip()
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
            codes_at_source = page_details.find_element(By.XPATH, '//*[contains(text(),"Class/Item Code: ")]//parent::p[1]').text.split('Class/Item Code:')[1].strip()
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
        
    except Exception as e:
        logging.info("Exception in page_details: {}".format(type(e).__name__)) 
        pass
        
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_url) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title) 
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']

options = webdriver.ChromeOptions()
options.add_extension("Urban-Free-VPN-proxy-Unblocker---Best-VPN.crx")
page_main = webdriver.Chrome(options=options)
time.sleep(20)

options = webdriver.ChromeOptions()
options.add_extension("Urban-Free-VPN-proxy-Unblocker---Best-VPN.crx")
page_details = webdriver.Chrome(options=options)
time.sleep(20)

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.txsmartbuy.com/esbd-presolicitations"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        fn.load_page(page_details, url, 50)
        logging.info('----------------------------------')
        logging.info(url) 
        
        select_fr = Select(page_main.find_element(By.XPATH,'//*[@id="content"]/div/div/form/div[3]/span/select'))
        select_fr.select_by_index(1)
        time.sleep(3)
        
        click_search = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#content > div > div > form > div.browse-contract-search-actions > button:nth-child(1)')))
        page_main.execute_script("arguments[0].click();",click_search) 
        time.sleep(5)
        
        
        try:
            for page_no in range(1,5):
                page_check = WebDriverWait(page_main, 60).until(EC.presence_of_element_located((By.XPATH,'//*[@id="content"]/div/div/div[4]/div[1]/div'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="content"]/div/div/div[4]/div[1]/div')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="content"]/div/div/div[4]/div[1]/div')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break

                try:   
                    next_page = WebDriverWait(page_main, 60).until(EC.element_to_be_clickable((By.XPATH,'(//*[@id="Next"])[2]')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 60).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="content"]/div/div/div[4]/div[1]/div'),page_check))
                except Exception as e:
                    logging.info("Exception in next_page: {}".format(type(e).__name__))
                    logging.info("No next page")
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
