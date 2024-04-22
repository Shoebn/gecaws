import time
from gec_common.gecclass import *
import logging
import re
import jsons
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
SCRIPT_NAME = "us_ridop_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    notice_data.script_name = "us_ridop_spn"
    
    notice_data.main_language = 'EN'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'US'
    notice_data.performance_country.append(performance_country_data)
    notice_data.currency = 'USD'
    notice_data.procurement_method = 2
    notice_data.notice_type = 4

    notice_data.document_type_description = 'Competition'
    
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR,'span > a span.title.teal-text').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    notice_text = tender_html_element.get_attribute('outerHTML')
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'span > a').text.replace(notice_data.notice_no,'').strip()
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass  
    
    org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'p > span.text-small.grey-text').text

    try:
        notice_data.local_description =tender_html_element.find_element(By.CSS_SELECTOR, 'p > span.contract-desc').text
        notice_data.notice_summary_english = notice_data.local_description
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR,' li:nth-child(n) > span > a')
        page_main.execute_script("arguments[0].click();",notice_data.notice_url)
        time.sleep(5)
        notice_data.notice_url = page_main.current_url
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
    try: 
        iframe = page_main.find_element(By.CSS_SELECTOR,'#webprocureframe')
        page_main.switch_to.frame(iframe)
    except:
        pass
    

    try:
        publish_date = page_main.find_element(By.XPATH, "//*[contains(text(),'Start Date')]//following::div[1]").text
        publish_date = re.findall('\w+ \d+, \d{4} \d+:\d+:\d+ [AP][M] ',publish_date)[0]
        publish_date = publish_date.strip()
        notice_data.publish_date = datetime.strptime(publish_date,'%B %d, %Y %I:%M:%S %p').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    try:
        notice_deadline = page_main.find_element(By.XPATH, "//*[contains(text(),'End Date')]//following::div[1]").text
        notice_deadline = re.findall('\w+ \d+, \d{4} \d+:\d+:\d+ [AP][M] ',notice_deadline)[0]
        notice_deadline = notice_deadline.strip()
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%B %d, %Y %I:%M:%S %p').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    try:
        customer_details_data = customer_details()
        customer_details_data.org_country = 'US'
        customer_details_data.org_language = 'EN'
        customer_details_data.org_name = org_name
        
        try:
            contact_person = page_main.find_element(By.XPATH,'//*[@id="webprocure_public_contract_board"]/app-root/app-bid-board/app-bid-board-details/div[2]/div/div[3]/div/p').text.splitlines()
            customer_details_data.contact_person = contact_person[0]
            customer_details_data.org_address = contact_person[1]
            customer_details_data.org_email = contact_person[-1]
        except:
            pass
        try:
            customer_details_data.org_phone = page_main.find_element(By.XPATH,'//*[@id="webprocure_public_contract_board"]/app-root/app-bid-board/app-bid-board-details/div[2]/div/div[3]/div/p').text.split('Tel: ')[1].split('\n')[0]
        except:
            pass
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details_data: {}".format(type(e).__name__))
        pass
        
    try:
        cpv = page_main.find_element(By.CSS_SELECTOR, "#webprocure_public_contract_board > app-root > app-bid-board > app-bid-board-details > div:nth-child(3) > div > div:nth-child(4) > div > div > div > ngx-datatable > div > datatable-body > datatable-selection").text
        cpv=re.findall(r'\b\d{8}\b',cpv)
        for cpv1 in cpv:
            cpv_codes = fn.CPV_mapping("assets/us_ridop_spn_cpv.csv",cpv1)
            for cpv_code in cpv_codes:
                cpvs_data = cpvs()
                cpvs_data.cpv_code = cpv_code
                cpvs_data.cpvs_cleanup()
                notice_data.cpvs.append(cpvs_data)
    except:
        pass

    try:
        notice_data.notice_text += notice_text
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, '#webprocure_public_contract_board > app-root > app-bid-board > app-bid-board-details > div:nth-child(3)').get_attribute("innerHTML")                     
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR,'#webprocure_public_contract_board > app-root > app-bid-board > app-bid-board-details > div:nth-child(3) > div > div.col.m7 > div > p').get_attribute("innerHTML")
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR,'#webprocure_public_contract_board > app-root > app-bid-board > app-bid-board-details > div:nth-child(3) > div > div.col.m7 > div > div').get_attribute("innerHTML")
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
        
    page_main.execute_script("window.history.go(-1)")  
    time.sleep(5)
 


    
    notice_data.identifier =  str(notice_data.notice_no) + str(notice_data.publish_date) +  str(notice_data.notice_url) 
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
    urls = ["https://ridop.ri.gov/vendors/bidding-opportunities"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
    
        try: 
            iframe = page_main.find_element(By.XPATH,'//*[@id="webprocureframe"]')
            page_main.switch_to.frame(iframe)
        except:
            pass

        clk = page_main.find_element(By.XPATH,"((//*[contains(text(),'Status')])[2]//following::label)[3]")
        page_main.execute_script("arguments[0].click();",clk)
        clk = page_main.find_element(By.XPATH,"//button[@class='btn teal btn-flat lighten-1 white-text filter-button']")
        page_main.execute_script("arguments[0].click();",clk)
        time.sleep(2)
        try:
            for page_no in range(1,5):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#webprocure_public_contract_board > app-root > app-bid-board > app-bid-board-result > div.search-results > div > div.col.l9.s12 > ul > li'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#webprocure_public_contract_board > app-root > app-bid-board > app-bid-board-result > div.search-results > div > div.col.l9.s12 > ul > li')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#webprocure_public_contract_board > app-root > app-bid-board > app-bid-board-result > div.search-results > div > div.col.l9.s12 > ul > li')))[records]
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
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,' //*[@id="app-init-container--router-view"]/div/div/div[2]/div/div/div/div[3]/div[2]/div/div[26]/div[4]/button/span/i')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    time.sleep(5)
                    page_check2 = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#webprocure_public_contract_board > app-root > app-bid-board > app-bid-board-result > div.search-results > div > div.col.l9.s12 > ul > li'))).text
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR, '#webprocure_public_contract_board > app-root > app-bid-board > app-bid-board-result > div.search-results > div > div.col.l9.s12 > ul > li'),page_check))
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
