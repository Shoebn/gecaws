from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "us_nebraska"
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
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "us_nebraska"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"

def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.main_language = 'EN'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'US'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.procurement_method = 2
  
    notice_data.currency = 'USD'

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(9)").text.replace(' ','')
        publish_date = re.findall('\d+/\d+/\d{2}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%m/%d/%y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
        
    if table == '22' or table=='28':
        notice_data.notice_type = 4
        notice_data.script_name = 'us_nebraska_spn'
        
        try:
            notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(7)').text
        except:
            try:
                notice_data.notice_no = notice_data.notice_url.split('.html')[0].split('/')[1].strip()
            except Exception as e:
                logging.info("Exception in notice_no: {}".format(type(e).__name__))
                pass
        
        try:
            notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a').get_attribute("href")                     
            fn.load_page(page_details,notice_data.notice_url,180)
            logging.info(notice_data.notice_url)
        except Exception as e:
            logging.info("Exception in notice_url: {}".format(type(e).__name__))
            notice_data.notice_url = url

        try:
            notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
            notice_data.notice_title = notice_data.local_title
        except Exception as e:
            logging.info("Exception in local_title: {}".format(type(e).__name__))
            pass   

        try:
            notice_data.class_codes_at_source = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text.split('-')[1].strip()
        except Exception as e:
            logging.info("Exception in class_codes_at_source: {}".format(type(e).__name__))
            pass

        try:
            notice_data.class_title_at_source = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text.split('-')[0].strip()
        except Exception as e:
            logging.info("Exception in class_title_at_source: {}".format(type(e).__name__))
            pass
        
        try: 
            notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(4) > p:nth-child(2)").text
            notice_deadline = re.findall('\d+/\d+/\d{2}',notice_deadline)[0]
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%m/%d/%y').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.notice_deadline)
        except:
            try:
                notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text
                notice_deadline = re.findall('\d+/\d+/\d{2}',notice_deadline)[0]
                notice_data.notice_deadline = datetime.strptime(notice_deadline,'%m/%d/%y').strftime('%Y/%m/%d %H:%M:%S')
                logging.info(notice_data.notice_deadline)
            except Exception as e:
                logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
                pass
        
        try:
            document_opening_time = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text
            document_opening_time = re.findall('\d+/\d+/\d{2}',document_opening_time)[0]
            notice_data.document_opening_time = datetime.strptime(document_opening_time,'%m/%d/%y').strftime('%Y-%m-%d')
        except Exception as e:
            logging.info("Exception in document_opening_time: {}".format(type(e).__name__))
            pass
        
        try:
            notice_data.document_type_decscription = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
        except Exception as e:
            logging.info("Exception in document_type_decscription: {}".format(type(e).__name__))
            pass 


    elif table == '31':
        notice_data.notice_type = 7
        notice_data.script_name = 'us_nebraska_ca'
        
        try:
            notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1) > a').get_attribute("href")                     
            fn.load_page(page_details,notice_data.notice_url,180)
            logging.info(notice_data.notice_url)
        except Exception as e:
            logging.info("Exception in notice_url: {}".format(type(e).__name__))
            notice_data.notice_url = url

        try:
            notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
            notice_data.notice_title = notice_data.local_title
        except Exception as e:
            logging.info("Exception in local_title: {}".format(type(e).__name__))
            pass   

        try:
            notice_data.class_codes_at_source = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text.split('-')[1].strip()
        except Exception as e:
            logging.info("Exception in class_codes_at_source: {}".format(type(e).__name__))
            pass

        try:
            notice_data.class_title_at_source = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text.split('-')[0].strip()
        except Exception as e:
            logging.info("Exception in class_title_at_source: {}".format(type(e).__name__))
            pass

        
        try:
            notice_data.related_tender_id = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(7)').text
        except Exception as e:
            logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
            pass
        
        try:              
            lot_details_data = lot_details()
            lot_details_data.lot_number = 1

            lot_details_data.lot_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text

            award_details_data = award_details()

            award_details_data.bidder_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text

            try: 
                award_date = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
                award_date = re.findall('\d+/\d+/\d{2}',award_date)[0]
                award_details_data.award_date = datetime.strptime(award_date,'%m/%d/%y').strftime('%Y/%m/%d') 
            except:
                pass

            award_details_data.award_details_cleanup()
            lot_details_data.award_details.append(award_details_data)

            if lot_details_data.award_details != []:
                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
        except Exception as e:
            logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
            pass
    
    
    try:
        org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(8)').text
    except:
        pass
    
    try:
        contact_person = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(6)').text
    except:
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, "//*[contains(text(),'PROJECT DESCRIPTION:')]//following::p[1]").text
        notice_data.notice_summary_english = notice_data.local_description
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass 
    
    
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'US'
        customer_details_data.org_language = 'EN'
        customer_details_data.org_name = org_name
        customer_details_data.contact_person = contact_person

        try:
            customer_details_data.org_phone = page_details.find_element(By.XPATH, "//*[contains(text(),'Phone:')]//parent::p[1]").text.split(':')[1].split('Email')[0].strip()
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass

        try:
            customer_details_data.org_email = page_details.find_element(By.XPATH, "//*[contains(text(),'Phone:')]//parent::p[1]").text.split('Email:')[1].strip()
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass    
    
    try:
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'body > div.container > main > div > section > div > table > tbody > tr')[1:]:
            try:
                for attached in single_record.find_elements(By.CSS_SELECTOR, "td:nth-child(3) > p > a"):
                    attachments_data = attachments() 
                    attachments_data.external_url = attached.get_attribute('href')
                    
                    attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, "td:nth-child(1)").text

                    try:
                        attachments_data.file_type = attachments_data.external_url.split('.')[-1]
                    except:
                        pass
                    
                    if attachments_data.external_url != None:
                        attachments_data.attachments_cleanup()
                        notice_data.attachments.append(attachments_data)
            except:
                pass
            
            try:
                for attached in single_record.find_elements(By.CSS_SELECTOR, "td:nth-child(3) > a"):
                    attachments_data = attachments() 
                    attachments_data.external_url = attached.get_attribute('href')
                    
                    attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, "td:nth-child(1)").text

                    try:
                        attachments_data.file_type = attachments_data.external_url.split('.')[-1]
                    except:
                        pass
                    
                    if attachments_data.external_url != None:
                        attachments_data.attachments_cleanup()
                        notice_data.attachments.append(attachments_data)
            except:
                pass
     
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass        
             
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'body > div.container').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
  
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
options = webdriver.ChromeOptions()
options.add_extension("C:/Users/Administrator/home/Urban-Free-VPN-proxy-Unblocker---Best-VPN.crx")
page_main = webdriver.Chrome(options=options)
page_main.maximize_window()
time.sleep(20)

options = webdriver.ChromeOptions()
options.add_extension("C:/Users/Administrator/home/Urban-Free-VPN-proxy-Unblocker---Best-VPN.crx")
page_details = webdriver.Chrome(options=options)
time.sleep(20)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://das.nebraska.gov/materiel/bidopps.html"] 
    for url in urls:
        fn.load_page(page_main, url, 150)
        logging.info('----------------------------------')
        logging.info(url)            

        table_list = ['22','28','31']
        for table in table_list:
            page_check = WebDriverWait(page_main, 100).until(EC.presence_of_element_located((By.CSS_SELECTOR,'body > div.container > table:nth-child('+str(table)+') > tbody > tr:nth-child(3)'))).text
            rows = WebDriverWait(page_main, 100).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'body > div.container > table:nth-child('+str(table)+') > tbody > tr')))
            length = len(rows)
            start_range = 0
            if table == '22' or table == '28':
                start_range = 1
            elif table == '31':
                start_range=2
            for records in range(start_range,length):
                tender_html_element = WebDriverWait(page_main, 120).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'body > div.container > table:nth-child('+str(table)+') > tbody > tr')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break

                if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                    logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                    break
            
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)
