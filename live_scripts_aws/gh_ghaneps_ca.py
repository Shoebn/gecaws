from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "gh_ghaneps_ca"
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
SCRIPT_NAME = "gh_ghaneps_ca"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'gh_ghaneps_ca'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'GH'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'GHS'

    notice_data.main_language = 'EN'

    try:
        procurement_method = page_details.find_element(By.XPATH, '//*[contains(text(),"Procurement Method:")]//following::dd[1]').text 
        if 'National' in procurement_method:
            notice_data.procurement_method = 0
        elif 'International' in procurement_method:
            notice_data.procurement_method = 1
        else:
            notice_data.procurement_method = 2
        
    except Exception as e:
        logging.info("Exception in procurement_method: {}".format(type(e).__name__))
        pass

    notice_data.notice_type = 7

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1) a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url

    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#Content > dl').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')

    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"Tender Unique ID:")]//following::dd[1]').text 
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.related_tender_id = page_details.find_element(By.XPATH, '//*[contains(text(),"APP Reference Number:")]//following::dd[1]').text  
    except Exception as e:
        logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Description:")]//following::dd[1]').text    
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_summary_english = notice_data.local_description
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass

    try:
        notice_contract_type = page_details.find_element(By.XPATH, '//*[contains(text(),"Procurement Type:")]//following::dd[1]').text
        if 'Goods' in notice_contract_type:
            notice_data.notice_contract_type = 'Supply'
        elif 'Consulting Services' in notice_contract_type:
            notice_data.notice_contract_type = 'Consultancy'
        elif 'Disposals' in notice_contract_type:
            notice_data.notice_contract_type = 'Service'
        elif 'Technical Services' in notice_contract_type:
            notice_data.notice_contract_type = 'Service'
        elif 'Works' in notice_contract_type:
            notice_data.notice_contract_type = 'Works'

    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass

    try:
        notice_data.contract_type_actual = notice_contract_type
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass

    try:
        notice_data.category = page_details.find_element(By.XPATH, '//*[contains(text(),"UNSPSC Codes:")]//following::dd[1]').text  
        notice_data.category = notice_data.category.split('-')[0]
        cpv_codes = fn.CPV_mapping("assets/gh_ghaneps_ca_unspscpv.csv",notice_data.category)
        for cpv_code in cpv_codes:
            cpvs_data = cpvs()
            cpvs_data.cpv_code = cpv_code
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in category: {}".format(type(e).__name__))
        pass
    
    try:
        publish_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Date of Publication/Invitation:")]//following::dd[1]').text  
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:
        document_opening_time = page_details.find_element(By.XPATH, '//*[contains(text(),"Bid Opening Date:")]//following::dd[1]').text  
        document_opening_time = re.findall('\d+/\d+/\d{4}',document_opening_time)[0]
        notice_data.document_opening_time = datetime.strptime(document_opening_time,'%d/%m/%Y').strftime('%Y-%m-%d')
    except Exception as e:
        logging.info("Exception in document_opening_time: {}".format(type(e).__name__))
        pass
    
    try:        
        lot_number = 1
        for single_record in page_details.find_elements(By.XPATH, '//*[contains(text(),"Lot Name")]//following::dd[1]'):
            lot_details_data = lot_details()
            lot_details_data.lot_number = lot_number
            lot_details_data.lot_title = single_record.text
            try:
                award_details_data = award_details()
                award_details_data.bidder_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
                try:
                    award_date = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
                    award_date = re.findall('\d{4}+/\d+/\d+',award_date)[0]
                    award_details_data.award_date = datetime.strptime(award_date,'%Y/%m/%d').strftime('%Y/%m/%d')
                except Exception as e:
                    logging.info("Exception in award_date: {}".format(type(e).__name__)) 
                    pass
                try:
                    grossawardvaluelc = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text  
                    award_details_data.grossawardvaluelc = float(grossawardvaluelc.split('(')[0].strip())
                except Exception as e:
                    logging.info("Exception in grossawardvaluelc: {}".format(type(e).__name__)) 
                    pass
                
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
    
    cust_details = page_details.find_element(By.XPATH,'//*[@id="Content"]/dl/dd[1]/a').get_attribute("href")
    fn.load_page(page_details1,cust_details,80)
    logging.info(notice_data.notice_url)

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        try:
            customer_details_data.org_address = page_details1.find_element(By.XPATH, '//*[contains(text(),"Address:")]//following::dd[1]').text 
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass

        try:
            customer_details_data.postal_code = page_details1.find_element(By.XPATH, '//*[contains(text(),"Postal Code:")]//following::dd[1]').text  
        except Exception as e:
            logging.info("Exception in postal_code: {}".format(type(e).__name__))
            pass

        try:
            customer_details_data.org_city = page_details1.find_element(By.XPATH, '//*[contains(text(),"City:")]//following::dd[1]').text  
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass

        try:
            customer_details_data.org_email = page_details1.find_element(By.XPATH, '//*[contains(text(),"Email:")]//following::dd[1]').text  
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass

        try:
            customer_details_data.org_phone = page_details1.find_element(By.XPATH, '//*[contains(text(),"Phone Number:")]//following::dd[1]').text  
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass

        try:
            customer_details_data.org_fax = page_details1.find_element(By.XPATH, '//*[contains(text(),"Fax:")]//following::dd[1]').text  
        except Exception as e:
            logging.info("Exception in org_fax: {}".format(type(e).__name__))
            pass

        try:
            customer_details_data.org_website = page_details1.find_element(By.XPATH, '//*[contains(text(),"Website")]//following::dd[1]').text  
        except Exception as e:
            logging.info("Exception in org_website: {}".format(type(e).__name__))
            pass

        customer_details_data.org_language = 'EN'
        customer_details_data.org_country = 'GH'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try:
        Show_Menu_clk = page_details.find_element(By.XPATH,'//*[@id="ToggleSubmenu"]').click()
        time.sleep(7)
    except Exception as e:
        logging.info("Exception in Show_Menu_clk: {}".format(type(e).__name__)) 
        pass
    try:
        Tender_Documents_clk = page_details.find_element(By.XPATH,'//*[@id="Submenu"]/div/ul[1]/li[2]/a').click()
        time.sleep(7)
    except Exception as e:
        logging.info("Exception in Tender_Documents_clk: {}".format(type(e).__name__)) 
        pass    

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR,'#T02 > tbody > tr'):
            attachments_data = attachments()
            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1) > a').text
            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1) > a').get_attribute('href')
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
page_details1 = fn.init_chrome_driver(arguments)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.ghaneps.gov.gh/epps/viewAllAwardedContracts.do?selectedItem=viewAllAwardedContracts.do"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(2,9):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="T01"]/tbody/tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="T01"]/tbody/tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="T01"]/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="Content"]/div/div/div[2]/p[2]/button[3]')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="T01"]/tbody/tr'),page_check))
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
