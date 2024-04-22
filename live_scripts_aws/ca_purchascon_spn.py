#after opening the url in "Status:= #ctl01_Search_ctl00_searchCriteria_Status" select "Open","Suspended","Closed","Cancelled" respectievly and take the data.Then clcik on "Search".

from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "ca_purchascon_spn"
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
from selenium.webdriver.support.ui import Select


NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "ca_purchascon_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'ca_purchascon_spn'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'CA'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.main_language = 'EN'
    
    notice_data.currency = 'CAD'
    
    notice_data.procurement_method = 2
    
    # Onsite Comment -1.if "Status: >> Open" then notice_type=4 and if "Status: >> Suspended","Status: >> Closed","Status: >> Cancelled" then pass notice_type=16.
    
    
    # Onsite Field -Title / Description
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3) > span.opptitle').text
        notice_data.notice_title = notice_data.local_title 
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Posting Date
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(6)").text
        publish_date = publish_date.replace("\n", " ")
        publish_date = re.findall('\d+/\d+/\d{4} \d+:\d+:\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%m/%d/%Y %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Closing Date
    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(5)").text
        notice_deadline = notice_deadline.replace("\n", " ")
        notice_deadline = re.findall('\d+/\d+/\d{4} \d+:\d+:\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%m/%d/%Y %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Title / Description    
    try:
        notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3) > span.opptitle > a').get_attribute("href").split('("')[1].split("&")[0].strip()
        notice_data.notice_url = 'https://vendor.purchasingconnection.ca'+notice_url
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    try:
        notice_data.notice_text += page_details.find_element(By.XPATH, '//*[@id="top"]').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
             
    try:
        notice_type = page_details.find_element(By.XPATH, '//*[contains(text(),"Region of Opportunity:")]//following::td[1]').text
        if "Open" in notice_type:
            notice_data.notice_type = 4
        else:
            notice_data.notice_type = 16
    except Exception as e:
        logging.info("Exception in notice_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Solicitation Number:    
    # Onsite Comment -1.split notice_no from local_title.
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3) > span.opptitle').text.split(":")[0].strip()        
    except:
        try:
            notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"Solicitation")]//following::td[1]').text
        except Exception as e:
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass
        
    # Onsite Field -Solicitation Type:
    try:
        notice_data.document_type_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Solicitation Type:")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
#     # Onsite Field -Opportunity Description:
#     # Onsite Comment -1.split after "Opportunity Description:".

    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Opportunity Description:")]//parent::div[1]').text.split('Opportunity Description:')[1].strip()
        notice_data.notice_summary_english = notice_data.local_description
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Category
    # Onsite Comment -1.split after "Category:".	2.repale the keywords("Goods=Supply","Construction=Works","Services=Service")

    try:
        notice_data.contract_type_actual= page_details.find_element(By.CSS_SELECTOR, '#body-right > div.first').text.split("Category: ")[1]
        if "Goods" in notice_data.contract_type_actual:
            notice_data.notice_contract_type = "Supply"
        elif "Construction" in notice_data.contract_type_actual:
            notice_data.notice_contract_type = "Works"
        elif "Services" in notice_data.contract_type_actual:
            notice_data.notice_contract_type = "Service"
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'CA'
        customer_details_data.org_language = 'EN'
    # Onsite Field -Title / Description

        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3) > span.opporganizationalunit').text

    # Onsite Field -Jurisdiction

        try:
            customer_details_data.org_city = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass

    # Onsite Field -Response Contact:
    # Onsite Comment -1.take all text before "Tel:".

        try:
            customer_details_data.org_address = page_details.find_element(By.CSS_SELECTOR, '#details > div:nth-child(2)').text.split("Response Contact:")[1].split("Tel:")[0].strip()
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass

    # Onsite Field -Response Contact:
    # Onsite Comment -1.take only first line

        try:
            customer_details_data.contact_person = page_details.find_element(By.CSS_SELECTOR, '#details > div:nth-child(2)').text.split("Response Contact:")[1].split('\n')[1].split("\n")[0].strip()
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass

    # Onsite Field -Response Contact:
    # Onsite Comment -1.split after "Tel:".

        try:
            customer_details_data.org_phone = page_details.find_element(By.CSS_SELECTOR, '#details > div:nth-child(2)').text.split("Tel:")[1].split("\n")[0].strip()
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass

    # Onsite Field -Response Contact:
    # Onsite Comment -1.split after "Fax:".

        try:
            customer_details_data.org_fax = page_details.find_element(By.CSS_SELECTOR, '#details > div:nth-child(2)').text.split("Fax:")[1].split("Email:")[0].strip()
        except Exception as e:
            logging.info("Exception in org_fax: {}".format(type(e).__name__))
            pass

    # Onsite Field -Response Contact:
        try:
            customer_details_data.org_email = page_details.find_element(By.CSS_SELECTOR, '#details > div:nth-child(2)').text.split("Email:")[1].strip()
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
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
page_main = fn.init_chrome_driver(arguments) 
page_details = fn.init_chrome_driver(arguments)

try:
    th = date.today() - timedelta(9)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://vendor.purchasingconnection.ca/Search.aspx"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        for no in range(1,5):
            select_option = Select(page_main.find_element(By.CSS_SELECTOR,'#ctl01_Search_ctl00_searchCriteria_Status'))
            select_option.select_by_index(no)
            
            search = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#ctl01_Search_ctl00_StartBrowsing')))
            page_main.execute_script("arguments[0].click();",search)
            time.sleep(5)
            
            sort_date = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="ctl01_Search_ctl00_result_Opportunities"]/tbody/tr[1]/td[6]/a')))
            page_main.execute_script("arguments[0].click();",sort_date)
            time.sleep(5)
            
            try:
                for page_no in range(2,20):
                    page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="ctl01_Search_ctl00_result_Opportunities"]/tbody/tr[3]'))).text
                    rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="ctl01_Search_ctl00_result_Opportunities"]/tbody/tr')))
                    length = len(rows)
                    for records in range(1,length-1):
                        tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="ctl01_Search_ctl00_result_Opportunities"]/tbody/tr')))[records]
                        extract_and_save_notice(tender_html_element)
                        if notice_count >= MAX_NOTICES:
                            break
    
                        if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                            logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                            break
                    try:   
                        next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                        page_main.execute_script("arguments[0].click();",next_page)
                        logging.info("Next page")
                        WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="ctl01_Search_ctl00_result_Opportunities"]/tbody/tr[3]'),page_check))
                    except Exception as e:
                        logging.info("Exception in next_page: {}".format(type(e).__name__))
                        logging.info("No next page")
                        break
            except:
                logging.info('No new record')
                break
                            
            search = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#ctl01_Search_ctl00_ShowCriteria')))
            page_main.execute_script("arguments[0].click();",search)
            time.sleep(10)
        
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit() 
    
    output_json_file.copyFinalJSONToServer(output_json_folder)
