from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "ae_esupply_spn"
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

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "ae_esupply_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"

# -------------------------------------------------------------------------------------------------------------------------------------------------------------------

# 1)   Go to URL : "https://esupply.dubai.gov.ae/esop/toolkit/opportunity/current/list.si?reset=true&resetstored=true&customLoginPage=%2Fesupply%2Fweb%2Findex.html&userAct=changeLangIndex&language=en_GB&_ncp=1697448487873.19029-1"


# 2)   click on "PUBLICATION DATE"  ( selector : " th.headLink.tdMedium.col__fixed_.js-sorting.sort-asc" )  2 Times for current  tenders data 


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'ae_esupply_spn'
   
    notice_data.main_language = 'EN'
   
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'AE'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'AED'
    
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 4
    
    org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'tr> td:nth-child(3)').text
    
    # Onsite Field -PROJECT TITLE
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'tr> td:nth-child(4)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -PUBLICATION DATE
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "tr> td:nth-child(5)").text
        publish_date = re.findall('\d+/\d+/\d{4} \d+:\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Supply Category
    # Onsite Comment -None

    try:
        notice_data.category = tender_html_element.find_element(By.CSS_SELECTOR, 'tr> td:nth-child(6)').text
    except Exception as e:
        logging.info("Exception in category: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Closing date/time
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "tr> td:nth-child(7)").text
        notice_deadline = re.findall('\d+/\d+/\d{4} \d+:\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Project Title
    # Onsite Comment -None
    try:
        No = WebDriverWait(tender_html_element, 70).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"tr> td:nth-child(4) > a"))).get_attribute("outerHTML").split("('")[1].split("',")[0].strip()
        notice_url="https://esupply.dubai.gov.ae/esop/toolkit/opportunity/current/"+str(No)+"/detail.si"
        logging.info(notice_url)
        fn.load_page(page_details,notice_url,80)
        time.sleep(5)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        pass
    try:
        No = WebDriverWait(page_details, 70).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"tr > td.tdAction.col__fixed_ > button"))).get_attribute("outerHTML").split("('")[1].split("',")[0].strip()
        notice_url2="https://esupply.dubai.gov.ae"+str(No)
        logging.info(notice_url2) 
        fn.load_page(page_details1,notice_url2,80)
        time.sleep(5)
    except Exception as e:
        logging.info("Exception in notice_url2: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#cntDetail > div').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    try:
        notice_data.notice_text += page_details1.find_element(By.CSS_SELECTOR, '#cntDetail').get_attribute("outerHTML")                     
    except:
        pass
    # Onsite Field -Project Code
    # Onsite Comment -None

    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, "//*[contains(text(),'Project Code')]//following::div[1]").text
    except:
        try:
            notice_no = notice_data.notice_url
            notice_data.notice_no=re.findall('\d{6}',notice_no)[0]
        except Exception as e:
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass
    
    # Onsite Field -None
    # Onsite Comment -if notice_no is not available in "Project Code" field then pass notice_no from notice_url

    
     # Onsite Field -Description
    # Onsite Comment -None

    try:
        notice_data.local_description = page_details.find_element(By.XPATH, "//*[contains(text(),'Description')]//following::div[1]").text
        notice_data.notice_summary_english =GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass

# Onsite Field -Buyer Details
# Onsite Comment -None

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_language = "EN"
        customer_details_data.org_country = "AE"
            
        # Onsite Field -BUYER ORGANISATION
        # Onsite Comment -None

        customer_details_data.org_name = org_name
        
        # Onsite Field -Email
        # Onsite Comment -None

        try:
            customer_details_data.org_email = page_details.find_element(By.XPATH, "//*[contains(text(),'Email')]//following::div[1]").text
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Contact
        # Onsite Comment -None

        try:
            customer_details_data.org_phone = page_details.find_element(By.XPATH, "//*[contains(text(),'Contact')]//following::div[1]").text
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass
        
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    
    try:
        lot_number=1
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#opportunityDetailFEBean > div > div:nth-child(9) > div > ul > li > table > tbody > tr')[1:]:
            lot_details_data = lot_details()
            lot_details_data.lot_number=lot_number
            
            # Onsite Field -TITLE
        # Onsite Comment -None
            lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, " tr > td:nth-child(4)").text
            lot_details_data.lot_title_english=GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
            
        # Onsite Field -CODE
        # Onsite Comment -None
            try:
                lot_details_data.lot_actual_number = single_record.find_element(By.CSS_SELECTOR, " tr > td:nth-child(3)").text
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass
            
            try:
                lot_details_data.lot_quantity_uom = page_details1.find_element(By.XPATH, "//*[contains(text(),'Unit of Measurement')]//following::td[3]").text
            except Exception as e:
                logging.info("Exception in lot_quantity_uom: {}".format(type(e).__name__))
                pass
            
            try:
                lot_quantity = page_details1.find_element(By.XPATH, "//*[contains(text(),'Quantity')]//following::tr[1]/td[4]").text
                lot_quantity = re.sub("[^\d\.\,]","",lot_quantity)
                lot_quantity =lot_quantity.replace('.','')
                lot_details_data.lot_quantity = float(lot_quantity.replace(',','.').strip())
            except Exception as e:
                logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                pass 
            
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
            lot_number+=1
    except Exception as e:
        logging.info("Exception in lot_details1: {}".format(type(e).__name__)) 
        pass

    # Onsite Field -ACTION COLUMN
# Onsite Comment -None

    try:              
        attachments_data = attachments()
        attachments_data.file_name = 'Download PDF'
        attachments_data.file_type = "PDF"

        # Onsite Field -Download PDF  
        external_url = page_details1.find_element(By.CSS_SELECTOR, "#cntDetail > input[type=button]:nth-child(4)").click()
        file_dwn = Doc_Download.file_download()
        attachments_data.external_url = str(file_dwn[0])
        time.sleep(5)
        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass  
    
    notice_data.notice_url = 'https://esupply.dubai.gov.ae/esupply/web/index.html'
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title) 
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
page_details1 = Doc_Download.page_details
page_details = fn.init_chrome_driver(arguments) 
page_main.maximize_window()
page_details.maximize_window()
page_details1.maximize_window()
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')   
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://esupply.dubai.gov.ae/esupply/web/index.html"] 
    for url in urls: 
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        fn.load_page(page_details1,url,90)
        fn.load_page(page_details,url,80)
        try:
            search = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"body > div.wrapper > section.three-elements > div > div > div:nth-child(1) > p:nth-child(8) > a"))).click()
            time.sleep(5)
        except Exception as e:
            logging.info("Exception in click: {}".format(type(e).__name__))
            pass
        
        try:
            search = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"#OpportunityListManager > div > section > div.table-root > table > tbody:nth-child(2) > tr > th:nth-child(5) > a"))).click()
            time.sleep(5)
        except Exception as e:
            logging.info("Exception in click: {}".format(type(e).__name__))
            pass
        
        try:
            search = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"#OpportunityListManager > div > section > div.table-root > table > tbody:nth-child(2) > tr > th:nth-child(5) > a"))).click()
            time.sleep(5)
        except Exception as e:
            logging.info("Exception in click: {}".format(type(e).__name__))
            pass
        
        try:
            page_details_search = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"body > div.wrapper > section.three-elements > div > div > div:nth-child(1) > p:nth-child(8) > a"))).click()
            time.sleep(5)
        except Exception as e:
            logging.info("Exception in click: {}".format(type(e).__name__))
            pass
        
        try:
            page_details1_search = WebDriverWait(page_details1, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"body > div.wrapper > section.three-elements > div > div > div:nth-child(1) > p:nth-child(8) > a"))).click()
            time.sleep(5)
        except Exception as e:
            logging.info("Exception in click: {}".format(type(e).__name__))
            pass

        try:
            for page_no in range(1,15):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="OpportunityListManager"]/div/section/div[2]/table/tbody[2]/tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="OpportunityListManager"]/div/section/div[2]/table/tbody[2]/tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="OpportunityListManager"]/div/section/div[2]/table/tbody[2]/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
                        
                    if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                        logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"#paginationId > div.toolbar-secondSide > div > button.ButtonBase.IconButton")))
                    page_main.execute_script("arguments[0].click();",next_page)
                    time.sleep(20)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="OpportunityListManager"]/div/section/div[2]/table/tbody[2]/tr'),page_check))
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
