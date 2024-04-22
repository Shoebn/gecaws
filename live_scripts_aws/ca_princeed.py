from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "ca_princeed"
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
from selenium.webdriver.support.ui import Select

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "ca_princeed"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    # Onsite Field -None
    # Onsite Comment -click on "Search All Tenders" to get the data 
    notice_data.script_name = 'ca_princeed'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'EN'
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'CA'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'CAD'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_type = 4
    
    # Onsite Field -Title
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Solicitation Number
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Publication Date
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text
        publish_date = re.findall('\d{4}-\d+-\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%Y-%m-%d').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Closing Date
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(5)").text
        notice_deadline = re.findall('\d{4}-\d+-\d+ \d+:\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%Y-%m-%d %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Solicitation Number
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1) > gpei-link-v2 > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,180)
        time.sleep(5)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'ng-component > div').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    # Onsite Field -Estimated Value
    # Onsite Comment -None

    try:
        notice_data.grossbudgetlc = page_details.find_element(By.XPATH, '//*[contains(text(),"Estimated Value")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Estimated Value
    # Onsite Comment -None

    try:
        notice_data.est_amount = page_details.find_element(By.XPATH, '//*[contains(text(),"Estimated Value")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Notice Type
    # Onsite Comment -if document_type_description > "Notice Type" is not available in detail page then pass "Tender" as static

    try:
        notice_data.document_type_description = page_details.find_element(By.CSS_SELECTOR, '//*[contains(text(),"Notice Type")]//following::td[1]').text
    except:
        try:
            notice_data.document_type_description = "Tender"
        except Exception as e:
            logging.info("Exception in document_type_description: {}".format(type(e).__name__))
            pass
            
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        customer_details_data = customer_details()
        # Onsite Field -Organization
        # Onsite Comment -None

        customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Organization")]//following::td[2]').text            
        
        # Onsite Field -Procurement Contact
        # Onsite Comment -None

        try:
            customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Procurement Contact")]//following::gpei-paragraph[1]').text
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Procurement Contact
        # Onsite Comment -None

        try:
            customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Procurement Contact")]//following::a[1]').text
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Procurement Contact
        # Onsite Comment -None

        try:
            customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Procurement Contact")]//following::gpei-paragraph[2]').text
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass
        
        customer_details_data.org_country = 'CA'
        customer_details_data.org_language = 'EN'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -None

#     try:              
#         for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, 'td:nth-child(2)'):
#             lot_details_data = lot_details()
#         # Onsite Field -Title
#         # Onsite Comment -None

#             try:
#                 lot_details_data.lot_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
#             except Exception as e:
#                 logging.info("Exception in lot_title: {}".format(type(e).__name__))
#                 pass
        
#         # Onsite Field -Title
#         # Onsite Comment -None

#             try:
#                 lot_details_data.lot_description = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
#             except Exception as e:
#                 logging.info("Exception in lot_description: {}".format(type(e).__name__))
#                 pass
        
#         # Onsite Field -Estimated Value
#         # Onsite Comment -None

#             try:
#                 lot_details_data.lot_grossbudget_lc = page_details.find_element(By.XPATH, '//*[contains(text(),"Estimated Value")]//following::td[1]').text
#             except Exception as e:
#                 logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
#                 pass
        
#         # Onsite Field -Contract Duration
#         # Onsite Comment -None

#             try:
#                 lot_details_data.contract_duration  = page_details.find_element(By.XPATH, '//*[contains(text(),"Contract Duration")]//following::td[1]').text
#             except Exception as e:
#                 logging.info("Exception in contract_duration: {}".format(type(e).__name__))
#                 pass
        
#         # Onsite Field -Contract Start Date
#         # Onsite Comment -None

#             try:
#                 contract_start_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Contract Start Date")]//following::td[1]').text
#                 contract_start_date = re.findall('\d{4}-\d+-\d+',contract_start_date)[0]
#                 lot_details_data.contract_start_date = datetime.strptime(contract_start_date,'%Y-%m-%d').strftime('%Y/%m/%d %H:%M:%S')
#             except Exception as e:
#                 logging.info("Exception in contract_start_date: {}".format(type(e).__name__))
#                 pass
        
#         # Onsite Field -Contract End Date
#         # Onsite Comment -None

#             try:
#                 contract_end_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Contract End Date")]//following::td[1]').text
#                 contract_end_date = re.findall('\d{4}-\d+-\d+',contract_end_date)[0]
#                 lot_details_data.contract_end_date = datetime.strptime(contract_end_date,'%Y-%m-%d').strftime('%Y/%m/%d %H:%M:%S')
#             except Exception as e:
#                 logging.info("Exception in contract_end_date: {}".format(type(e).__name__))
#                 pass
        
#             lot_details_data.lot_details_cleanup()
#             notice_data.lot_details.append(lot_details_data)
#     except Exception as e:
#         logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
#         pass
    
# Onsite Field -Document
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.XPATH, '//*[contains(text(),"Document")]//following::td[1]'):
            attachments_data = attachments()
        # Onsite Field -Document
        # Onsite Comment -split file_name from the given selector

            attachments_data.file_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Document")]//following::a').text
        
        # Onsite Field -Document
        # Onsite Comment -split file_type from the given selector

            try:
                attachments_data.file_type = page_details.find_element(By.XPATH, '//*[contains(text(),"Document")]//following::a').text
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Document
        # Onsite Comment -None

            attachments_data.external_url = page_details.find_element(By.XPATH, '//*[contains(text(),"Document")]//following::a').get_attribute('href')
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass

    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
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
    urls = ['https://www.princeedwardisland.ca/en/tenders?f%5B0%5D=field_t_tender_status%3Aopen'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        index= "2024"
        select_fr = Select(page_main.find_element(By.CSS_SELECTOR,'#edit-submitted-publication-year--2'))
        select_fr.select_by_value(index)
        
        try:
            page_main.find_element(By.CSS_SELECTOR,' div.form-actions > button').click()
        except:
            pass
        
        try:
            WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#edit-submitted-publication--2-label > span')))
        except:
            pass
        try:
            for page_no in range(2,4):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[2]/main/section/div/section/div/div/div[3]/div[1]/div[2]/div[5]/div/div/gpei-root/div/ng-component/div/gpei-table-v2/table/tbody/tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[2]/main/section/div/section/div/div/div[3]/div[1]/div[2]/div[5]/div/div/gpei-root/div/ng-component/div/gpei-table-v2/table/tbody/tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[2]/main/section/div/section/div/div/div[3]/div[1]/div[2]/div[5]/div/div/gpei-root/div/ng-component/div/gpei-table-v2/table/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/div[2]/main/section/div/section/div/div/div[3]/div[1]/div[2]/div[5]/div/div/gpei-root/div/ng-component/div/gpei-table-v2/table/tbody/tr'),page_check))
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
    
