
from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "us_evpnc_ca"
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
SCRIPT_NAME = "us_evpnc_ca"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'us_evpnc_ca'
    notice_data.currency = 'USD'
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'US'
    notice_data.performance_country.append(performance_country_data)

    notice_data.procurement_method = 2
    notice_data.notice_type = 7
    notice_data.main_language = 'EN'
    

    try:
        notice_data.notice_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in notice_title: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_title = notice_data.notice_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = tender_html_element.find_element(By.CSS_SELECTOR, '#EntityListControl td:nth-child(3)').text  
        notice_data.notice_summary_english = notice_data.local_description
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, ' td:nth-child(6)').text  
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(5)").text
        notice_data.publish_date = datetime.strptime(publish_date,'%m/%d/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, '#EntityListControl td:nth-child(1)>a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, '#EntityListControl   td:nth-child(1)').text   
    except:
        try:
            notice_data.notice_no = notice_data.notice_url.split('-')[-1]
        except Exception as e: 
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass

    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#EntityFormControl').get_attribute("outerHTML")    
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')

    try:
        category = page_details.find_element(By.XPATH, "//*[contains(text(),'Commodity Code')]//following::input[1]").get_attribute('value') 
        if len(category)>3:
            notice_data.category = category
            cpv_codes = fn.CPV_mapping("assets/us_evpnc_ca_cpv.csv",notice_data.category.lower())
            for cpv_code in cpv_codes:
                cpvs_data = cpvs()
                cpvs_data.cpv_code = cpv_code
                cpvs_data.cpvs_cleanup()
                notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in category: {}".format(type(e).__name__))
        pass
        
    try:              

        customer_details_data = customer_details()

        customer_details_data.org_name = page_details.find_element(By.XPATH, "//*[contains(text(),'Department')]//following::input[1]").get_attribute('value')  

        try:
            org_email = page_details.find_element(By.XPATH, "//*[contains(text(),'Special Instructions')]//following::input[1]").get_attribute('value')  
            if '@' in org_email:
                email_regex = re.compile(r"[\w\.-]+@[\w\.-]+")
                customer_details_data.org_email = email_regex.findall(org_email)[0]
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass

        customer_details_data.org_language = 'EN'
        customer_details_data.org_country = 'US'
        
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:       
        lot_number=1
        lot_details_data = lot_details()
        lot_details_data.lot_number = lot_number

        try:
            lot_details_data.lot_title = notice_data.notice_title
            notice_data.is_lot_default = True
        except Exception as e:
            logging.info("Exception in lot_title: {}".format(type(e).__name__))
            pass

        try:
            lot_details_data.lot_description = notice_data.local_description
        except Exception as e:
            logging.info("Exception in lot_description: {}".format(type(e).__name__))
            pass

        try:
            for single_record in page_details.find_elements(By.CSS_SELECTOR, '#awards_subgrid > div > div.view-grid > table > tbody > tr'):  

                award_details_data = award_details()

                award_details_data.bidder_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1) > a').text
                award_date = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3) > time').text
                award_details_data.award_date = datetime.strptime(award_date,'%m/%d/%Y').strftime('%Y/%m/%d')
                netawardvaluelc = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
                netawardvaluelc = netawardvaluelc.split('$')[1].strip()
                award_details_data.netawardvaluelc = float(netawardvaluelc.replace(',','').strip())

                award_details_data.award_details_cleanup()
                lot_details_data.award_details.append(award_details_data)
        except Exception as e:
            logging.info("Exception in award_details: {}".format(type(e).__name__))
            pass

        lot_details_data.lot_details_cleanup()
        notice_data.lot_details.append(lot_details_data)
        lot_number+=1
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'td.clearfix.cell.notes-cell > div:nth-child(2) > div > div  > div:nth-child(6) > div > div'):
            attachments_data = attachments()

            file_name = single_record.find_element(By.CSS_SELECTOR, 'div:nth-child(2) > div:nth-child(2)').text  
            attachments_data.file_name = file_name

            try:
                file_type = file_name.split('(')[0]
                attachments_data.file_type = file_type.split('.')[-1]
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
            try:
                attachments_data.file_size = file_name.split('(')[1].split(')')[0]
            except Exception as e:
                logging.info("Exception in file_size: {}".format(type(e).__name__))
                pass

            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'div:nth-child(2) > div:nth-child(2) > div > a').get_attribute('href')
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_url) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title)
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
    urls = ["https://evp.nc.gov/solicitations/"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        
        filter_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#filter-header > h2')))
        page_main.execute_script("arguments[0].click();",filter_click)
        logging.info("filter_click")        
        
        Awarded_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#filter > div > ul > li:nth-child(3) > ul > li:nth-child(3) > div > label > input[type=checkbox]')))
        page_main.execute_script("arguments[0].click();",Awarded_click)
        logging.info("Awarded_click")  
        
        Apply_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#filter > div > div > button')))
        page_main.execute_script("arguments[0].click();",Apply_click)
        logging.info("Apply_click")  
        
        
        try:
            Posted_Date_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'th:nth-child(5) > a')))
            page_main.execute_script("arguments[0].click();",Posted_Date_click)
            logging.info("Posted_Date_click")  

            Posted_Date_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'th:nth-child(5) > a')))
            page_main.execute_script("arguments[0].click();",Posted_Date_click)
            logging.info("Posted_Date_click")  
            time.sleep(5)
        except Exception as e:
            logging.info("Exception in Posted_Date_click: {}".format(type(e).__name__))
            pass                
        
        for page_no in range(2,9):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="EntityListControl"]/div/div[2]/div/div[2]/table/tbody/tr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="EntityListControl"]/div/div[2]/div/div[2]/table/tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="EntityListControl"]/div/div[2]/div/div[2]/table/tbody/tr')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break

                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
                    
                if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                    logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                    break

            if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                break

            try:   
                next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                page_main.execute_script("arguments[0].click();",next_page)
                logging.info("Next page")
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="EntityListControl"]/div/div[2]/div/div[2]/table/tbody/tr'),page_check))
            except Exception as e:
                logging.info("Exception in next_page: {}".format(type(e).__name__))
                logging.info("No next page")
                break
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit() 
    output_json_file.copyFinalJSONToServer(output_json_folder)
    
 
