from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "jm_boj_spn"
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

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "jm_boj_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'jm_boj_spn'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'JM'
    notice_data.performance_country.append(performance_country_data)
   
    notice_data.currency = 'JMD'
   
    notice_data.main_language = 'EN'
   
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 4
    
    # Onsite Field -RFP Number
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'tr:nth-child(2) > td:nth-child(1)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Title
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'tr:nth-child(2) > td:nth-child(2)').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Closing Date Friday, 19 January 2024 at 10:00 a.m.
    # Onsite Comment -Note:Grab time also

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "tr:nth-child(2) > td:nth-child(3)").text
        notice_deadline = notice_deadline.replace('.','').strip()
        notice_deadline = re.findall('\d+ \w+ \d{4} at \d+:\d+ [aApPmM]+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d %B %Y at %I:%M %p').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "article.elementor-post > div > div").text
        publish_date = re.findall('\w+ \d+, \d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%B %d, %Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:              
        attachments_data = attachments()
        # Onsite Field -None
        # Onsite Comment -Note:Dpn't take file extention	..... Note:Splite on url

        attachments_data.file_name = tender_html_element.find_element(By.CSS_SELECTOR, 'tr:nth-child(2) > td:nth-child(2) a').text

        attachments_data.external_url = tender_html_element.find_element(By.CSS_SELECTOR, 'tr:nth-child(2) > td:nth-child(2) a').get_attribute('href')

        try:
            attachments_data.file_type = attachments_data.external_url.split('.')[-1].strip()
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
        customer_details_data.org_name = 'Bank of Jamaica'
        customer_details_data.org_parent_id = '7585956'
        customer_details_data.org_country = 'JM'
        customer_details_data.org_language = 'EN'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'article.elementor-post div > h3 > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except:
        notice_data.notice_url = url
        
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#main-content > div > div > div').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute("outerHTML")
    
    try:
        page_detail1_url = page_details.find_element(By.CSS_SELECTOR, 'nav > div > div:nth-child(1) > a').get_attribute("href")                     
        fn.load_page(page_details1,page_detail1_url,80)
        logging.info(page_detail1_url)
    except:
        pass
    
    try:
        notice_data.notice_text += page_details1.find_element(By.CSS_SELECTOR, '#main-content > div > div > div').get_attribute("outerHTML")
    except:
        pass
    
    try:              
        for single_record in page_details1.find_elements(By.CSS_SELECTOR, '#post-34980 > div > div.post-text > div > p > a'):
            attachments_data = attachments()
        
            attachments_data.file_name = "Tender Document"

            attachments_data.external_url = single_record.get_attribute("href")
            
            try:
                attachments_data.file_type = attachments_data.external_url.split('.')[-1].strip()
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
        
    try:
        page_detail2_url = page_details.find_element(By.CSS_SELECTOR, 'nav > div > div:nth-child(2) > a').get_attribute("href")                     
        fn.load_page(page_details2,page_detail2_url,80)
        logging.info(page_detail2_url)
    except:
        pass   
    
    try:
        notice_data.notice_text += page_details2.find_element(By.CSS_SELECTOR, '#main-content > div > div > div').get_attribute("outerHTML")
    except:
        pass
    
    try:
        notice_data.contract_duration = page_details2.find_element(By.XPATH, '//*[contains(text(),"Tenor:")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass
    
    try:
        est_amount = page_details2.find_element(By.XPATH, '//*[contains(text(),"Auction Amount:")]//following::td[1]').text
        est_amount = re.sub("[^\d\.\,]","",est_amount)
        notice_data.est_amount =float(est_amount.replace(',','').strip())
        notice_data.grossbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments) 
page_details = fn.init_chrome_driver(arguments) 
page_details1 = fn.init_chrome_driver(arguments) 
page_details2 = fn.init_chrome_driver(arguments)

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://boj.org.jm/about-boj/tenders/"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        try:
            for page_no in range(2,5):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="post-256"]/div/div/div/section/div/div[1]/div/div[2]/div/div/article/div'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="post-256"]/div/div/div/section/div/div[1]/div/div[2]/div/div/article/div')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="post-256"]/div/div/div/section/div/div[1]/div/div[2]/div/div/article/div')))[records]
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
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="post-256"]/div/div/div/section/div/div[1]/div/div[2]/div/div/article/div'),page_check))
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
    page_details1.quit()
    page_details2.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)
