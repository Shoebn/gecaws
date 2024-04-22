#after opening the url in "Status:= #ctl01_Search_ctl00_searchCriteria_Status" select "Awarded","Amending Awards","Awards Cancelled" respectievly and take the data.Then clcik on "Search".

#check comments for additional changes
#1)for bidder name
# As discussed with shoeib added below condition .. (1) if lot avaialble than condition 
# lot_title ="blank "and award_details ="blank" []
# than lot_details =[]
# (2) if lots not avaible than
# award_details= []
# and lot_details= []

from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "ca_purchascon_ca"
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
from selenium.webdriver.support.ui import Select

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "ca_purchascon_ca"
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
    notice_data.script_name = 'ca_purchascon_ca'
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'CA'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'EN'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'USD'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -
    notice_data.notice_type = 7

    # Onsite Field -Title / Description
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3) > span.opptitle').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -1.split notice_no from local_title.

    try:
        notice_data.notice_no =notice_data.notice_title.split(':')[0]
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Posting Date
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(6)").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%m/%d/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

#     # Onsite Field -Title / Description
#     # Onsite Comment -None

    try:
        notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3) > span.opptitle > a').get_attribute("href")  
        notice_url = notice_url.split('.aspx?')[1].split('&%')[0]
        notice_data.notice_url='https://vendor.purchasingconnection.ca/Opportunity.aspx?'+str(notice_url)
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
#     # Onsite Field -None
#     # Onsite Comment -1.click on "View Award List=#body-right > div:nth-child(3) > a:nth-child(6)" in page_details and take this data also in notice_text.
    try:
        notice_data.notice_text += page_details.find_element(By.XPATH, '//*[@id="top"]').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')

#     # Onsite Field -Solicitation Number:
#     # Onsite Comment -None

    try:
        notice_data.related_tender_id = page_details.find_element(By.XPATH, '//*[contains(text(),"Solicitation")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
        pass
    
#     # Onsite Field -Solicitation Type:
#     # Onsite Comment -None

    try:
        notice_data.document_type_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Solicitation Type:")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass


#     # Onsite Field -Category
#     # Onsite Comment -1.split after "Category:".	2.repale the keywords("Goods=Supply","Construction=Works","Services=Service")

    try:
        notice_data.contract_type_actual = page_details.find_element(By.CSS_SELECTOR, '#body-right > div.first').text.split(':')[1]
        if 'Goods' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Supply'
        elif 'Construction' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Works'
        elif 'Services' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Service'
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
# # Onsite Field -None
# # Onsite Comment -None

    try:                      
        customer_details_data = customer_details()
        customer_details_data.org_country = 'CA'
        customer_details_data.org_language = 'EN'
    # Onsite Field -Title / Description
    # Onsite Comment -None


        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3) > span.opporganizationalunit').text

    # Onsite Field -Jurisdiction
    # Onsite Comment -None

        try:
            customer_details_data.org_city = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass

    # Onsite Field -Organization Address:
    # Onsite Comment -

        try:
            customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Organization Address:")]//following::td[1]').text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass


# # Onsite Field -None
# # Onsite Comment -None

    try:              
        lot_details_data = lot_details()
    # Onsite Field -Title / Description
    # Onsite Comment -None
        lot_details_data.lot_number=1
        lot_details_data.lot_title = notice_data.local_title
        notice_data.is_lot_default = True
   

    # Onsite Field -Category
    # Onsite Comment -1.split after "Category:".	2.repale the keywords("Goods=Supply","Construction=Works","Services=Service")

        try:
            lot_details_data.lot_contract_type_actual = page_details.find_element(By.CSS_SELECTOR, '#body-right > div.first').text.split(':')[1]
            if 'Goods' in lot_details_data.lot_contract_type_actual:
                lot_details_data.contract_type = 'Supply'
            elif 'Construction' in lot_details_data.lot_contract_type_actual:
                lot_details_data.contract_type = 'Works'
            elif 'Services' in lot_details_data.lot_contract_type_actual:
                lot_details_data.contract_type = 'Service'
        except Exception as e:
            logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
            pass

        try:
            notice_url1 = page_details.find_element(By.CSS_SELECTOR, '#body-right > div:nth-child(3) > a:nth-child(6)').get_attribute("href")  
            fn.load_page(page_details1,notice_url1,80)
            logging.info(notice_url1)

    # Onsite Field -None
    # Onsite Comment -click on "View Award List=#body-right > div:nth-child(3) > a:nth-child(6)" in page_details to get award_details[] data.

            award_details_data = award_details()

            # Onsite Field -Award Date:
            # Onsite Comment -1.split after "Award Date:"

            award_date = page_details1.find_element(By.XPATH, '//*[contains(text(),"Awarded Vendors")]//following::th[1]').text
            award_date = re.findall('\w+ \d+, \d{4}',award_date)[0]
            award_details_data.award_date = datetime.strptime(award_date ,'%B %d, %Y').strftime('%Y/%m/%d')
            # Onsite Field -Legal Name
            # Onsite Comment -None

            award_details_data.bidder_name = page_details1.find_element(By.CSS_SELECTOR, 'table > tbody > tr > td > table > tbody > tr:nth-child(2) > td.awardName').text

            # Onsite Field -Amount
            # Onsite Comment -None

            grossawardvaluelc = page_details1.find_element(By.CSS_SELECTOR, 'table > tbody > tr > td > table > tbody > tr:nth-child(2) > td:nth-child(2)').text
            grossawardvaluelc = grossawardvaluelc.split('$')[1].replace(',','')
            award_details_data.grossawardvaluelc = float(grossawardvaluelc)
            # Onsite Field -Vendor Address
            # Onsite Comment -None

            award_details_data.address = page_details1.find_element(By.CSS_SELECTOR, 'table > tbody > tr > td > table > tbody > tr:nth-child(2) > td:nth-child(4)').text

            # Onsite Field -Vendor Address
            # Onsite Comment -1.take country_name only

            award_details_data.bidder_country = page_details1.find_element(By.CSS_SELECTOR, 'table > tbody > tr > td > table > tbody > tr:nth-child(2) > td:nth-child(4)').text.split('\n')[2]

            award_details_data.award_details_cleanup()
            lot_details_data.award_details.append(award_details_data)
        except Exception as e:
            logging.info("Exception in award_details: {}".format(type(e).__name__))
            pass

        lot_details_data.lot_details_cleanup()
        notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass

    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_details = fn.init_chrome_driver(arguments) 
page_main = fn.init_chrome_driver(arguments) 
page_details1 = fn.init_chrome_driver(arguments)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://vendor.purchasingconnection.ca/Search.aspx"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        time.sleep(10)
        
        
        btn = Select(page_main.find_element(By.ID,'ctl01_Search_ctl00_searchCriteria_Status'))
        btn.select_by_index(5)
        time.sleep(5)
        
        srch_btn = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="ctl01_Search_ctl00_StartBrowsing"]')))
        page_main.execute_script("arguments[0].click();", srch_btn)
        
        
        try:
            for page_no in range(2,10):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="ctl01_Search_ctl00_result_Opportunities"]/tbody/tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="ctl01_Search_ctl00_result_Opportunities"]/tbody/tr')))
                length = len(rows)
                for records in range(1,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="ctl01_Search_ctl00_result_Opportunities"]/tbody/tr')))[records]
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
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="ctl01_Search_ctl00_result_Opportunities"]/tbody/tr'),page_check))
                except Exception as e:
                    logging.info("Exception in next_page: {}".format(type(e).__name__))
                    logging.info("No next page")
                    break
        except:
            logging.info('No new record')
            break
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        time.sleep(10)
        
        
        btn = Select(page_main.find_element(By.ID,'ctl01_Search_ctl00_searchCriteria_Status'))
        btn.select_by_index(6)
        time.sleep(6)
        
        srch_btn = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="ctl01_Search_ctl00_StartBrowsing"]')))
        page_main.execute_script("arguments[0].click();", srch_btn)
        
        
        
        for page_no in range(2,10):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="ctl01_Search_ctl00_result_Opportunities"]/tbody/tr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="ctl01_Search_ctl00_result_Opportunities"]/tbody/tr')))
            length = len(rows)
            for records in range(1,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="ctl01_Search_ctl00_result_Opportunities"]/tbody/tr')))[records]
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="ctl01_Search_ctl00_result_Opportunities"]/tbody/tr'),page_check))
            except Exception as e:
                logging.info("Exception in next_page: {}".format(type(e).__name__))
                logging.info("No next page")
                break
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        time.sleep(10)
        
        
        btn = Select(page_main.find_element(By.ID,'ctl01_Search_ctl00_searchCriteria_Status'))
        btn.select_by_index(7)
        time.sleep(7)
        
        srch_btn = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="ctl01_Search_ctl00_StartBrowsing"]')))
        page_main.execute_script("arguments[0].click();", srch_btn)
        
        
        
        for page_no in range(2,10):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="ctl01_Search_ctl00_result_Opportunities"]/tbody/tr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="ctl01_Search_ctl00_result_Opportunities"]/tbody/tr')))
            length = len(rows)
            for records in range(1,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="ctl01_Search_ctl00_result_Opportunities"]/tbody/tr')))[records]
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="ctl01_Search_ctl00_result_Opportunities"]/tbody/tr'),page_check))
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
    page_details1.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)
