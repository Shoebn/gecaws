from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "in_cpppcn_ca"
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
SCRIPT_NAME = "in_cpppcn_ca"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'in_cpppcn_ca'
    notice_data.main_language = 'EN'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'INR'
    notice_data.notice_type = 7
    notice_data.procurement_method = 2
    notice_data.notice_url = url
    

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4) > a').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'IN'
        customer_details_data.org_language = 'EN'
    # Onsite Field -Sponsor's company
    # Onsite Comment -None

        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text


        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        publish_date = re.findall('\d+-\w+-\d{4} \d+:\d+ [PMAMpmam]+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d-%b-%Y %I:%M %p').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold or notice_data.publish_date > today_date:
        return


    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    except:
        pass
    try:
        awarddate = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
    except:
        pass

    try:   
        notice_url = WebDriverWait(tender_html_element, 30).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'td:nth-child(4) > a'))).click()                  
        time.sleep(2)
        WebDriverWait(page_main, 80).until(EC.presence_of_element_located((By.XPATH,'//div[@class="maintext"]'))).text
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        pass
 
    
    try:
        notice_data.notice_text += page_main.find_element(By.XPATH, '//*[@class = "main_container o-hidden"]').get_attribute("outerHTML")                     
    except:
        pass
        
    try:
        notice_data.notice_no = page_main.find_element(By.XPATH, '//*[contains(text(),"Tender Ref. No.")]//following::td[2]').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
        
    try:
        notice_data.local_description = page_main.find_element(By.XPATH, '//*[contains(text(),"Tender Description")]//following::td[2]').text
        notice_data.notice_summary_english = notice_data.local_description
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
        
    try:
        notice_data.additional_tender_url = page_main.find_element(By.XPATH, '//*[contains(text(),"Tender Document")]//following::a[1]').get_attribute('href')
    except Exception as e:
        logging.info("Exception in additional_tender_url: {}".format(type(e).__name__))
        pass
    
    try:
        tender_contract_end_date = page_main.find_element(By.XPATH, '//*[contains(text(),"Date of Completion/Completion Period in Days")]//following::td[2]').text
        tender_contract_end_date = re.findall('\d+-\w+-\d{4} \d+:\d+ [PMAMpmam]+',tender_contract_end_date)[0]
        notice_data.tender_contract_end_date = datetime.strptime(tender_contract_end_date,'%d-%b-%Y %I:%M %p').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in additional_tender_url: {}".format(type(e).__name__))
        pass
    try:
        grossbudgetlc = page_main.find_element(By.XPATH, '(//*[contains(text(),"Contract Value")])[1]//following::td[2]').text.strip()
        notice_data.grossbudgetlc = float(grossbudgetlc)
        notice_data.est_amount = notice_data.grossbudgetlc
    except Exception as e:
        logging.info("Exception in additional_tender_url: {}".format(type(e).__name__))
        pass
        
    
    try:
        lot_details_data = lot_details()
        lot_details_data.lot_number = 1

        lot_details_data.lot_title = notice_data.local_title
        notice_data.is_lot_default = True
        lot_details_data.lot_title_english = lot_details_data.lot_title

        try:
            award_details_data = award_details()

            award_details_data.bidder_name = page_main.find_element(By.XPATH, '//*[contains(text(),"Name of the selected bidder(s)")]//following::td[2]').text
            try:
                award_details_data.address = page_main.find_element(By.XPATH, '//*[contains(text(),"Address of the selected bidder(s)")]//following::td[2]').text 
            except Exception as e:
                logging.info("Exception in address: {}".format(type(e).__name__))
                pass

            try:
                award_date1 = awarddate
                award_date = re.findall('\d+-\w+-\d{4}',award_date1)[0]
                award_details_data.award_date = datetime.strptime(award_date,'%d-%b-%Y').strftime('%Y/%m/%d')
            except:
                pass

            award_details_data.award_details_cleanup()
            lot_details_data.award_details.append(award_details_data)
        except Exception as e:
            logging.info("Exception in award_details: {}".format(type(e).__name__)) 
            pass
        
        
        if lot_details_data.award_details !=[]:
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass

    try:
        page_main.execute_script("window.history.go(-1)")
        time.sleep(5)
    except:
        pass
    WebDriverWait(page_main, 60).until(EC.presence_of_element_located((By.XPATH, '//*[@id="table"]/tbody/tr[1]')))
    
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments) 

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://eprocure.gov.in/cppp/resultoftendersnew/cpppdata/byYzJWc1pXTjBBMTNoMUExM2gxQTEzaDFBMTNoMU1qQXlOQT09QTEzaDFVSFZpYkdsemFHVms="] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url) 

        try:
            for page_no in range(2,5):
                page_check = WebDriverWait(page_main, 80).until(EC.presence_of_element_located((By.XPATH,'//*[@id="table"]/tbody/tr'))).text
                rows = WebDriverWait(page_main, 80).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="table"]/tbody/tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 80).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="table"]/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
                try:   
                    next_page = WebDriverWait(page_main, 80).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 80).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="table"]/tbody/tr'),page_check))
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
    output_json_file.copyFinalJSONToServer(output_json_folder)
