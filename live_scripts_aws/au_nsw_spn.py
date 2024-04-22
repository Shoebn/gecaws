from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "au_nsw_spn"
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

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "au_nsw_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"

def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'au_nsw_spn'
    notice_data.main_language = 'EN'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'AU'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.procurement_method = 2
    notice_data.notice_type = 4
    notice_data.currency = 'AUD'
    
    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "li > p:nth-child(2)").text
        notice_deadline = re.findall('\d+-\w+-\d{4} \d+:\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d-%b-%Y %H:%S').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'ul > li > h3').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        notice_no = tender_html_element.find_element(By.CSS_SELECTOR, '#search-results  li > ul > li').text.split('ID: ')[1]
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'li dl > dd:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.category = tender_html_element.find_element(By.CSS_SELECTOR, '#search-results  p.subcat').text
        category_name = notice_data.category.lower()
        cpv_codes_list = fn.CPV_mapping("assets/au_nsw_category_cpv.csv",category_name)
        for each_cpv in cpv_codes_list:
            cpvs_data = cpvs()
            cpvs_data.cpv_code = each_cpv
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in category: {}".format(type(e).__name__))
        pass
    
    try:
        org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'dd:nth-child(4)').text
    except:
        pass
    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'li > div > a:nth-child(2)').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    try:
        notice_data.notice_no = notice_no
    except:
        notice_data.notice_no = notice_data.notice_url.split('UUID=')[1]
    
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#main-content > div').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')

    
    try:
        publish_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Published")]//following::span[1]').text
        publish_date = re.findall('\d+-\w+-\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d-%b-%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except:
        pass
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Tender Details")]//following::div').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),"Tender Details")]//following::p').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'AU'
        customer_details_data.org_language = 'EN'

        try:
            org_name1 = page_details.find_element(By.XPATH, '//*[contains(text(),"Agency")]//following::span[1]').text
            if org_name1 != '':
                customer_details_data.org_name = org_name1
            else:
                customer_details_data.org_name = org_name
        except:
            try:
                customer_details_data.org_name = org_name
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass

        try:
            customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Contact Person")]//following::div[1]').text.split("\n")[0]
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass

        try:
            customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Contact Person")]//following::div[1]').text.split('Phone: ')[1].split('\n')[0]
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass

        try:
            customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Contact Person")]//following::div[1]/a').text
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass

        try:
            customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Agency Address")]//following::div[1]').text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass


        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#RFT-PreviewDocument > div > a'):
            attachments_data = attachments()
            
            attachments_data.external_url = single_record.get_attribute('href')
        
            attachments_data.file_name = single_record.text
            
            try:
                attachments_data.file_type = single_record.text.split('.')[-1].split(' (')[0]
            except Exception as e:
                logging.info("Exception in file_type_1: {}".format(type(e).__name__))
                pass
            
            try:
                attachments_data.file_size = single_record.text.split('.')[-1].split(' (')[1].split(')')[0]
            except Exception as e:
                logging.info("Exception in file_size_1: {}".format(type(e).__name__))
                pass
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    try:
        details1 = page_details.find_element(By.LINK_TEXT, 'Download a softcopy - free').get_attribute("href")                     
        fn.load_page(page_details1,details1,80)
        logging.info('details 1: ' +details1)

        email_box = page_details1.find_element(By.ID,'id-email-address')
        email_box.send_keys('akanksha.a@dgmarket.com')
        time.sleep(2)

        psw = page_details1.find_element(By.ID,'id-password')
        psw.send_keys('Sierrajaytom@1')
        time.sleep(2)

        login = page_details1.find_element(By.NAME,'FarcryFormsubmitButton=Log in')
        page_details1.execute_script("arguments[0].click();",login)
    except:
        pass
    
    try:              
        for single_record in page_details1.find_elements(By.CSS_SELECTOR, 'div.list-box-inner.viewDocBox a'):
            attachments_data = attachments()
            try:
                attachments_data.file_type = single_record.text.split('.')[1].split(' (')[0]
            except Exception as e:
                logging.info("Exception in file_type_2: {}".format(type(e).__name__))
                pass
        
            attachments_data.file_name = single_record.text.split('.')[0]
            
        
            try:
                attachments_data.file_size = single_record.text.split('.')[1].split(' (')[1].split(')')[0]
            except Exception as e:
                logging.info("Exception in file_size_2: {}".format(type(e).__name__))
                pass
        
            attachments_data.external_url = single_record.get_attribute('href')
            
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments_2: {}".format(type(e).__name__)) 
        pass
    
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) + str(notice_data.publish_date) +  str(notice_data.notice_url) 
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
page_details1 = fn.init_chrome_driver(arguments)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://suppliers.buy.nsw.gov.au/opportunity/search?query=&categories=&types=Expression%20of%20Interest%2CTenders&page=1"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(1,10):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="search-results"]/ul/li[1]'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="search-results"]/ul/li')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="search-results"]/ul/li')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
                        
                    if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                        logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                        break
                        
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="search-results"]/nav[2]/ul/li[9]/a')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    time.sleep(5)
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="search-results"]/ul/li[1]'),page_check))
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
    page_details1.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)
