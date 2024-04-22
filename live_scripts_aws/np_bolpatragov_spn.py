from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "np_bolpatragov_spn"
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
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "np_bolpatragov_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'np_bolpatragov_spn'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'NP'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'NPR'
    
    notice_data.main_language = 'EN'
    
    # Onsite Field -None
    # Onsite Comment -Note:If procurement_method is "NCB" than take 0 OR procurement_method is "ICB" than take 1 OR procurement_method is "OTHERS" than take 2

    try:
        procurement_method = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text.split("  ")[1].strip()
        if "NCB" in procurement_method:
            notice_data.procurement_method = 0
        elif "ICB" in procurement_method:
            notice_data.procurement_method = 1
        elif "OTHERS" in procurement_method:
            notice_data.procurement_method = 2
    except Exception as e:
        logging.info("Exception in procurement_method: {}".format(type(e).__name__))
        pass
    

    notice_data.notice_type = 4
    
    # Onsite Field -IFB / RFP / EOI / PQ No
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, '#dashBoardBidResult tr > td:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Notice Published Date
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(7)").text
        publish_date = re.findall('\d+-\d+-\d{4} \d+:\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d-%m-%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Last Date of Bid Submission
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, " td:nth-child(8)").text
        notice_deadline = re.findall('\d+-\d+-\d{4} \d+:\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d-%m-%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Project Title
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, ' td:nth-child(3)').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    # Onsite Field -Procurement Type
    # Onsite Comment -Note:Replace following keywords with given keywords("Goods=Supply","Works=Works","Consultancy=Consultancy","Other Services=Service")
    
    try:
        notice_data.contract_type_actual = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text.split(" ")[0].strip()
        if "Works" in notice_data.contract_type_actual:
            notice_data.notice_contract_type ="Works"
        elif "Goods" in notice_data.contract_type_actual:
            notice_data.notice_contract_type ="Supply"
        elif "Other Services" in notice_data.contract_type_actual:
            notice_data.notice_contract_type ="Service"
        elif "Consultancy" in notice_data.contract_type_actual:
            notice_data.notice_contract_type ="Consultancy Services"
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass

    
    # Onsite Field -Project Title
    # Onsite Comment -Note:click on the projec title
        
    try:
        notice_url = WebDriverWait(tender_html_element, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'td:nth-child(3) a')))
        page_main.execute_script("arguments[0].click();",notice_url)
        time.sleep(10) 
        notice_data.notice_url = page_main.current_url
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
    
    
    try:
        notice_data.local_description = page_main.find_element(By.XPATH, '//*[contains(text(),"Brief Description of Work")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Brief Description of Work
    # Onsite Comment -None

    try:
        notice_data.notice_summary_english = notice_data.local_description
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Date of Pre-Bid Meeting
    # Onsite Comment -None

    try:
        pre_bid_meeting_date = page_main.find_element(By.XPATH, '//*[contains(text(),"Date of Pre-Bid Meeting")]//following::td[1]').text
        pre_bid_meeting_date = re.findall('\d{4}/\d+/\d+',pre_bid_meeting_date)[0]
        notice_data.pre_bid_meeting_date = datetime.strptime(pre_bid_meeting_date,'%Y/%m/%d').strftime('%Y/%m/%d')
    except:
        try:
            pre_bid_meeting_date = page_main.find_element(By.XPATH, '//*[contains(text(),"Date of Pre-Bid Meeting")]//following::td[1]').text
            pre_bid_meeting_date = re.findall('\d+-\d+-\d{4}',pre_bid_meeting_date)[0]
            notice_data.pre_bid_meeting_date = datetime.strptime(pre_bid_meeting_date,'%d-%m-%Y').strftime('%Y/%m/%d')
        except Exception as e:
            logging.info("Exception in pre_bid_meeting_date: {}".format(type(e).__name__))
            pass
    
    # Onsite Field -Bid Opening Date
    # Onsite Comment -None

    try:
        document_opening_time = page_main.find_element(By.XPATH, '//*[contains(text(),"Bid Opening Date")]//following::td[1]').text
        document_opening_time = re.findall('\d{4}-\d+-\d+',document_opening_time)[0]
        notice_data.document_opening_time = datetime.strptime(document_opening_time,'%Y-%m-%d').strftime('%Y-%m-%d')
    except:
        try:
            document_opening_time = page_main.find_element(By.XPATH, '//*[contains(text(),"Bid Opening Date")]//following::td[1]').text
            document_opening_time = re.findall('\d+-\d+-\d{4}',document_opening_time)[0]
            notice_data.document_opening_time = datetime.strptime(document_opening_time,'%d-%m-%Y').strftime('%Y-%m-%d')
        except Exception as e:
            logging.info("Exception in document_opening_time: {}".format(type(e).__name__))
            pass
    
    # Onsite Field -Bid Document Fee (in NPR)
    # Onsite Comment -None

    try:
        notice_data.document_fee = page_main.find_element(By.XPATH, '//*[contains(text(),"Bid Document Fee (in NPR)")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in document_fee: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, 'body > div:nth-child(6)').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    
    # Onsite Field -Current Status
    # Onsite Comment -None

    try:
        notice_data.document_type_description = page_main.find_element(By.XPATH, '//*[contains(text(),"Current Status")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Source of Fund
    # Onsite Comment -None

    try:
        notice_data.source_of_funds = page_main.find_element(By.XPATH, '//*[contains(text(),"Source of Fund")]//following:: td[1]').text
    except Exception as e:
        logging.info("Exception in source_of_funds: {}".format(type(e).__name__))
        pass
    
# Onsite Field -Bid Document >> Download 
# Onsite Comment -None

    try:              
        for single_record in page_main.find_elements(By.CSS_SELECTOR, 'tr:nth-child(1) > td > fieldset > table > tbody'):
            attachments_data = attachments()

        # Onsite Field -Bid Document >> Document Type
        # Onsite Comment -None

            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'tr.odd > td:nth-child(1)').text
        
        # Onsite Field -Bid Document > Download
        # Onsite Comment -None
            
            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3) > a').get_attribute('href')
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass


    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'NP'
        customer_details_data.org_language = 'NE'

    # Onsite Field -Public Entity Name
    # Onsite Comment -None

        customer_details_data.org_name = page_main.find_element(By.CSS_SELECTOR, '#tenderDetailsDialog > table:nth-child(3) > tbody > tr:nth-child(1) > td:nth-child(2) > label').text


    # Onsite Field -Name of Official Inviting Bid
    # Onsite Comment -None

        try:
            customer_details_data.contact_person = page_main.find_element(By.XPATH, '//*[contains(text(),"Name of Official Inviting Bid")]//following::td[1]').text
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass            

    # Onsite Field -Address of the Official Inviting Bid
    # Onsite Comment -None

        try:
            customer_details_data.org_address = page_main.find_element(By.XPATH, '//*[contains(text(),"Address of the Official Inviting Bid")]//following::td[1]').text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass

    # Onsite Field -Contact of the Official Inviting Bid
    # Onsite Comment -None

        try:
            customer_details_data.org_phone = page_main.find_element(By.XPATH, '//*[contains(text(),"Contact of the Official Inviting Bid")]//following::td[1]').text
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    back_clk = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR, ' div:nth-child(6) > div.ui-dialog-buttonpane.ui-widget-content.ui-helper-clearfix > div > button > span'))).click()
    time.sleep(2)
    
    WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="dashBoardBidResult"]/tbody/tr'))).text
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) + str(notice_data.local_title)
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
try:
    th = date.today() #- timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://bolpatra.gov.np/egp/searchOpportunity"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        
        threshold1 = th.strftime('%d-%m-%Y')
        date=page_main.find_element(By.XPATH,'/html/body/table/tbody/tr[3]/td/div/div/form/fieldset/table/tbody/tr/td/table/tbody/tr[4]/td[2]/input').send_keys(threshold1)
        
        date=page_main.find_element(By.XPATH,'//*[@id="searchBidForm"]/fieldset/table/tbody/tr/td/table/tbody/tr[7]/td[2]/input[2]').click()
        time.sleep(5)
        
        pp_btn = Select(page_main.find_element(By.CSS_SELECTOR,'#pager > tbody > tr > td:nth-child(9) > select'))
        pp_btn.select_by_index(2)
        time.sleep(5)
        
        try:
            for page_no in range(2,5):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="dashBoardBidResult"]/tbody/tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="dashBoardBidResult"]/tbody/tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="dashBoardBidResult"]/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                try:
                    page_main.find_element(By.CSS_SELECTOR, " td:nth-child(7) > input").clear()
                    page_main.find_element(By.CSS_SELECTOR, " td:nth-child(7) > input").send_keys(page_no)
                    time.sleep(5)
                    page_main.find_element(By.CSS_SELECTOR, " td:nth-child(7) > input").send_keys(Keys.ENTER)
                    time.sleep(10)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="dashBoardBidResult"]/tbody/tr'),page_check))
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
    output_json_file.copyFinalJSONToServer(output_json_folder)
