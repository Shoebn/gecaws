from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "gh_ppaghana_ppn"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from deep_translator import GoogleTranslator
from selenium import webdriver
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "gh_ppaghana_ppn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.script_name = 'gh_ppaghana_ppn'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'EN'
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'GH'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -Currency:
    # Onsite Comment -None

    try:
        notice_data.currency = page_details.find_element(By.XPATH, '//*[contains(text(),"Currency:")]//following::dd[1]').text.upper()
    except Exception as e:
        logging.info("Exception in currency: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_type = 6
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.document_type_description = 'Prequalifications'
    
    # Onsite Field -Published -
    # Onsite Comment -split the data between " Published -" and "Deadline :"

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div.list-date").text.split('Published - ')[1].split('Deadline : ')[0]
        publish_date = re.findall('(\d{1,2})(st|nd|rd|th) (\w+), (\d{4})',publish_date)
        day, suffix, month, year = publish_date[0]
        month_number = datetime.strptime(month, '%B').month
        publish_date_str = f"{day}/{month_number}/{year}"
        notice_data.publish_date = datetime.strptime(publish_date_str, '%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass


    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Deadline :
    # Onsite Comment -split the data after  "Deadline :"

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "div.list-date").text.split('Deadline : ')[1]
        notice_deadline = re.findall('(\d{1,2})(st|nd|rd|th) (\w+), (\d{4})',notice_deadline)
        day, suffix, month, year = notice_deadline[0]
        month_number = datetime.strptime(month, '%B').month
        notice_deadline = f"{day}/{month_number}/{year}"
        notice_data.notice_deadline = datetime.strptime(notice_deadline, '%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.list-title > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.col-md-9').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    # Onsite Field -PRQ Name:
    # Onsite Comment -None

    try:
        notice_data.local_title = page_details.find_element(By.XPATH, '//*[contains(text(),"PRQ Name:")]//following::dd[1]').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass


#     # Onsite Field -Tender Cat:
#     # Onsite Comment -Replace following keywords with given respective keywords ('Works = Works' , 'Non Consultant Services = Non consultancy' , 'Consultancy Services   = Consultancy' , 'Goods = Supply' , 'Technical Services = Service' )


    try:
        notice_data.contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Tender Cat:")]//following::dd[1]').text
        if 'Works' in notice_data.contract_type_actual:
             notice_data.notice_contract_type = 'Works'
        elif 'Non Consultant Services' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Non consultancy'
        elif 'Consultancy Services' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Consultancy'
        elif 'Goods' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Supply'
        elif 'Technical Services' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Service'
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass

    
#     # Onsite Field -Pack #:
#     # Onsite Comment -None

    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"Pack #:")]//following::dd[1]').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
#     # Onsite Field -Price of PRQ Document:
#     # Onsite Comment -None

    try:
        document_cost = page_details.find_element(By.XPATH, '//*[contains(text(),"Price of PRQ Document:")]//following::dd[1]').text
        document_cost = re.sub("[^\d\.\,]","",document_cost)
        notice_data.document_cost = float(document_cost)
    except Exception as e:
        logging.info("Exception in document_cost: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Description:")]//following::dd[1]').text
        notice_data.notice_summary_english = notice_data.local_description
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass

    
# # Onsite Field -None
# # Onsite Comment -None

    try:              
        customer_details_data = customer_details()
    # Onsite Field -Agency:
    # Onsite Comment -None


        customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Agency:")]//following::dd[1]').text


    # Onsite Field -Region:
    # Onsite Comment -None

        try:
            customer_details_data.org_city = page_details.find_element(By.XPATH, '//*[contains(text(),"Region:")]//following::dd[1]').text
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass

    # Onsite Field -Contact Person:
    # Onsite Comment -None

        try:
            customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Contact Person:")]//following::dd[1]').text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass

    # Onsite Field -Email :
    # Onsite Comment -None

        try:
            customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Email :")]//following::dd[1]').text
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass

    # Onsite Field -Tel :
    # Onsite Comment -None

        try:
            customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Tel :")]//following::dd[1]').text
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass

    # Onsite Field -Fax :
    # Onsite Comment -None

        try:
            customer_details_data.org_fax = page_details.find_element(By.XPATH, '//*[contains(text(),"Fax :")]//following::dd[1]').text
        except Exception as e:
            logging.info("Exception in org_fax: {}".format(type(e).__name__))
            pass

    # Onsite Field -Website:
    # Onsite Comment -None

        try:
            customer_details_data.org_website = page_details.find_element(By.XPATH, '//*[contains(text(),"Website:")]//following::dd[1]').text
        except Exception as e:
            logging.info("Exception in org_website: {}".format(type(e).__name__))
            pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# # Onsite Field -None
# # Onsite Comment -None

    try:
        lot_number = 1
        for single_record in page_details.find_elements(By.XPATH, '//*[contains(text(),"Description:")]//following::dd[1]'):
            single=single_record.text.split('\n\n')
            for i in single:
                lot_details_data = lot_details()
                lot_details_data.lot_number = lot_number
                
                lot_details_data.lot_contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Tender Cat:")]//following::dd[1]').text
                if 'Works' in lot_details_data.lot_contract_type_actual:
                    lot_details_data.contract_type = 'Works'
                elif 'Non Consultant Services' in lot_details_data.lot_contract_type_actual:
                    lot_details_data.contract_type = 'Non consultancy'
                elif 'Goods' in lot_details_data.lot_contract_type_actual:
                    lot_details_data.contract_type = 'Supply'
                elif 'Consultancy Services' in lot_details_data.lot_contract_type_actual:
                    lot_details_data.contract_type = 'Consultancy'
                elif 'Technical Services' in lot_details_data.lot_contract_type_actual:
                    lot_details_data.contract_type = 'Service'
                else:
                    pass
                
                
                lot_details_data.lot_actual_number = i.split('Lot')[1].split('\n')[0]
                lot_details_data.lot_actual_number = 'Lot' + lot_details_data.lot_actual_number 


        # Onsite Field -Description:
        # Onsite Comment -split only lot_title for ex. split the data between "Lot 1" and "• Demolition of existing damaged chambers and manholes." , ref_url : "https://tenders.ppa.gov.gh/prqs/1100"

                lot_details_data.lot_title = i.split('Lot')[1].split('\n')[1].split('\n')[0]



        # Onsite Field -Description:
        # Onsite Comment -take only round bullet values for ex."• Demolition of existing damaged chambers and manholes." as a lot_Description , ref_url : "https://tenders.ppa.gov.gh/prqs/1100"

                try:
                    lot_details_data.lot_description = i.split('Lot')[1].split('Lot')[0]
                except:
                    try:
                          lot_details_data.lot_description = i.split('Lot')[1].split('\n')[0]  
                    except Exception as e:
                        logging.info("Exception in lot_description: {}".format(type(e).__name__))
                        pass
                
                
                lot_number +=1
                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
 
    

        
# # Onsite Field -Additional Info:
# # Onsite Comment -ref_url : "https://tenders.ppa.gov.gh/prqs/1072"

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.col-md-9 > div > dl:nth-child(22)'):
            attachments_data = attachments()
            attachments_data.file_name = 'tender documents'
        # Onsite Field -Additional Info:
        # Onsite Comment -None

            attachments_data.external_url = page_details.find_element(By.CSS_SELECTOR, 'div.col-md-9 > div a').get_attribute('href')
            attachments_data.file_type = attachments_data.external_url.split('.')[-1]
        
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
    urls = ["http://tenders.ppa.gov.gh/prqs"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(2,5):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[1]/section[2]/div/div/div/div/div[2]/div/div'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/section[2]/div/div/div/div/div[2]/div/div')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/section[2]/div/div/div/div/div[2]/div/div')))[records]
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
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/div[1]/section[2]/div/div/div/div/div[2]/div/div'),page_check))
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
    
