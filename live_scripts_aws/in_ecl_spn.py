from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "in_ecl_spn"
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
SCRIPT_NAME = "in_ecl_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    global page_no
    notice_data = tender()

    notice_data.script_name = 'in_ecl_spn'
    notice_data.main_language = 'EN'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'INR'
    notice_data.procurement_method = 2
    

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(2)').text.split(',')[0].strip()
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    try: 
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text
        publish_date = re.findall('\d+-\w+-\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d-%b-%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
        notice_deadline_date = re.findall('\d+-\w+-\d{4}',notice_deadline)[0]
        notice_deadline_time = re.findall('\d+:\d+',notice_deadline.split('upto')[1])[0]
        notice_deadline_date_time = notice_deadline_date+' '+notice_deadline_time
        notice_data.notice_deadline = datetime.strptime(notice_deadline_date_time,'%d-%b-%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    try:
        document_opening_time = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
        document_opening_time_date = re.findall('\d+-\w+-\d{4}',document_opening_time)[0]
        notice_data.document_opening_time = datetime.strptime(document_opening_time_date,'%d-%b-%Y').strftime('%Y-%m-%d')
    except Exception as e:
        logging.info("Exception in document_opening_time: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    except:
        pass
    
    try:
        notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(7) > input').get_attribute('onclick').split('=')[-1].split("'")[0].strip()
        notice_data.notice_url = 'https://tenders.secureloginecl.co.in/tender_details.php?pid=2&id='+notice_url
        fn.load_page(page_details,notice_data.notice_url,120)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    try:
        Corrigendum_data_check = page_details.find_element(By.XPATH, "//*[contains(text(),'Corrigendum(s)')]//following::td[1]").text
        if "----" in Corrigendum_data_check:
            notice_data.notice_type = 4
        else:
            notice_data.notice_type = 16
        
    except:
        pass
    
    try:
        pre_bid_meeting_date = page_details.find_element(By.XPATH, "//*[contains(text(),'Pre-Bid Meeting Date')]//following::td[1]").text
        pre_bid_meeting_date = re.findall('\d+-\w+-\d{4}',pre_bid_meeting_date)[0]
        notice_data.pre_bid_meeting_date = datetime.strptime(pre_bid_meeting_date,'%d-%b-%Y').strftime('%Y/%m/%d')
    except Exception as e:
        logging.info("Exception in pre_bid_meeting_date: {}".format(type(e).__name__))
        pass
    
    try:
        class_title_at_source = page_details.find_element(By.XPATH, "//*[contains(text(),'Tender Category')]//following::td[1]//td[1]").text
        if len(class_title_at_source)>1:
            notice_data.class_title_at_source = class_title_at_source
            notice_data.category = class_title_at_source
        else:
            pass
    except:
        pass
    
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'IN'
        customer_details_data.org_language = 'EN'
        customer_details_data.org_name = "EASTERN COALFIELDS LIMITED"
        customer_details_data.org_parent_id = 7249665
        try:
            org_city = page_details.find_element(By.XPATH, '//*[contains(text(),"Tender Area / Location")]//following::td[1]').text
            if len(org_city) >1:
                customer_details_data.org_city =org_city
            else:
                pass
        except:
            pass
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:
        document_purchase_end_time = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text
        document_purchase_end_time = re.findall('\d+-\w+-\d{4}',document_purchase_end_time)[0]
        notice_data.document_purchase_end_time = datetime.strptime(document_purchase_end_time,'%d-%b-%Y').strftime('%Y/%m/%d')
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
    
    
    try:              
        attachments_data = attachments()

        attachments_data.external_url = page_details.find_element(By.XPATH, "//*[contains(text(),'Tender / Bid Document')]//following::td/a").get_attribute('href')
        try:
            attachments_data.file_type = page_details1.find_element(By.XPATH, "//*[contains(text(),'Tender / Bid Document')]//following::td/a").text.split('.')[-1].strip()
        except:
            pass
        attachments_data.file_name = page_details.find_element(By.XPATH, "//*[contains(text(),'Tender / Bid Document')]//following::td/a").text.split(attachments_data.file_type)[0].strip()
        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    try:
        est_amount = page_details.find_element(By.XPATH, "//*[contains(text(),'Estimated Cost / Tender Value')]//following::tr[1]/td[1]").text
        est_amount = re.sub("[^\d\.\,]","",est_amount)
        notice_data.est_amount = float(est_amount.replace(',','').strip())
        notice_data.grossbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass

    try:
        notice_data.earnest_money_deposit = page_details.find_element(By.XPATH, "//*[contains(text(),'Earnest Money')]//following::td[1]").text
        notice_data.document_fee = page_details.find_element(By.XPATH, "//*[contains(text(),'Estimated Cost / Tender Value')]//following::tr[1]/td[5]").text
        document_fee = re.sub("[^\d\.\,]","",notice_data.document_fee)
        notice_data.document_cost = float(document_fee.replace(',','').strip())
    except Exception as e:
        logging.info("Exception in document_fee: {}".format(type(e).__name__))
        pass
    
    try:
        local_description = page_details.find_element(By.XPATH, "//*[contains(text(),'Other Information')]//following::td[1]").text
        if "Name of works" in local_description:
            notice_data.local_description = local_description.split('Name of works')[1].strip()
            notice_data.notice_summary_english = notice_data.local_description
        elif "Description of work" in local_description:
            notice_data.local_description = local_description.split('Description of work')[1].strip()
            notice_data.notice_summary_english = notice_data.local_description
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    try:
        Corrigendum_url = page_details.find_element(By.XPATH, '''//*[contains(text(),'Corrigendum(s)')]//following::td[1]//input''').get_attribute('onclick').split('=')[-1].split("'")[0].strip()
        attachments_url = 'https://tenders.secureloginecl.co.in/tender_corrigen_details.php?pid=3&sl='+Corrigendum_url
        fn.load_page(page_details1,attachments_url,120)
    except Exception as e:
        logging.info("Exception in Corrigendum_url: {}".format(type(e).__name__))
    
    
    try:              
        attachments_data = attachments()

        attachments_data.external_url = page_details1.find_element(By.XPATH, "//*[contains(text(),'Corrigendum Document')]//following::td/a").get_attribute('href')
        try:
            attachments_data.file_type = page_details1.find_element(By.XPATH, "//*[contains(text(),'Corrigendum Document')]//following::td/a").text.split('.')[-1].strip()
        except:
            pass
        if attachments_data.external_url != '':
            attachments_data.file_name = page_details1.find_element(By.XPATH, "//*[contains(text(),'Corrigendum Document')]//following::td/a").text.split(attachments_data.file_type)[0].strip()
        
        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments2: {}".format(type(e).__name__)) 
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
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    for page_no in range(1,50):
        urls = ["https://tenders.secureloginecl.co.in/tender_list_active.php?pid=2&strt="+str(page_no)+"0","https://tenders.secureloginecl.co.in/tender_list_corrigendum.php?pid=3&strt="+str(page_no)+"0"] 
        for url in urls:
            fn.load_page(page_main, url, 50)
            logging.info('----------------------------------')
            logging.info(url) 
        
            try:
                rows = WebDriverWait(page_main, 80).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/table/tbody/tr[3]/td/table[4]/tbody/tr')))
                length = len(rows)
                for records in range(1,length):
                    tender_html_element = WebDriverWait(page_main, 80).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/table/tbody/tr[3]/td/table[4]/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
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
