from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "zm_zppa_ca"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
import gec_common.OutputJSON
from gec_common import functions as fn

#Note:"Advanced Search" >> "Tender Status" = select option "Awarded" > click on search button.
#Note:Click on this "tr > th.extra > a > img" button and click on ("Notice PDF","Award Date") ChickBox than grab the data

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "zm_zppa_ca"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'zm_zppa_ca'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'ZM'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'ZMW'
    
    notice_data.main_language = 'EN'
    
    notice_data.notice_type = 7
    
    # Onsite Field -Procedure:
    # Onsite Comment -Note:Repleace following keywords with given keywords("Open Bidding International=1","Open Selection 
    #International=1","Open Bidding National=0","Open Selection National=0","Limited Bidding International=1",
    #"Limited Selection International=1","Limited Bidding National=0","Limited Selection National=0",
    #"Simplified Bidding=2","Direct Bidding=2","Emergency Procedure=2")

    try:
        procurement_method = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(6)').text
        if 'Open Bidding International' in procurement_method or 'Open Selection International' in procurement_method or 'Limited Bidding International' in procurement_method or 'Limited Selection International' in procurement_method:
            notice_data.procurement_method =1
        elif 'Open Bidding National' in procurement_method or 'Limited Bidding National' in procurement_method or 'Limited Selection National' in procurement_method or 'Open Selection National' in procurement_method:
            notice_data.procurement_method =0
        else:
            notice_data.procurement_method =2
    except Exception as e:
        logging.info("Exception in procurement_method: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Title
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Status
    # Onsite Comment -None

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(7)').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Title
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2) a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#Content > dl').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    # Onsite Field -Tender Unique ID:
    # Onsite Comment -None

    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"Tender Unique ID:")]//following::dd[1]').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -APP Reference Number:
    # Onsite Comment -None

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

    # Onsite Field -Description:
    # Onsite Comment -None

    try:
        notice_data.notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),"Description:")]//following::dd[1]').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Procurement Type:
    # Onsite Comment -Note:Repleace following keywords with given keywords("Goods=Supply","Consulting Services=Consultancy","Non-consulting Services=Non consultancy","Works=Works")

    try:
        notice_data.contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Procurement Type:")]//following::dd[1]').text
        if 'Goods' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Supply'
        elif 'Consulting Services' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Consultancy'
        elif 'Non-consulting Services' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Non consultancy'
        elif 'Works' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Works'
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -UNSPSC Codes:
    # Onsite Comment -None
    try:
        notice_data.category = page_details.find_element(By.XPATH, '//*[contains(text(),"UNSPSC Codes:")]//following::dd[1]').text
        category = notice_data.category.split('-')[0].strip()
        cpv_codes = fn.CPV_mapping("assets/zm_zppa_ca_cpv.csv",category)
        for cpv_code in cpv_codes:
            cpvs_data = cpvs()
            cpvs_data.cpv_code = cpv_code
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in category: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Date of Publication/Invitation:
    # Onsite Comment -None 06/07/2023 17:51:59

    try:
        publish_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Date of Publication/Invitation:")]//following::dd[1]').text
        publish_date = re.findall('\d+/\d+/\d{4} \d+:\d+:\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Bid Opening Date:
    # Onsite Comment -None

    try:
        document_opening_time = page_details.find_element(By.XPATH, '//*[contains(text(),"Bid Opening Date:")]//following::dd[1]').text
        document_opening_time = re.findall('\d+/\d+/\d{4}',document_opening_time)[0]
        notice_data.document_opening_time = datetime.strptime(document_opening_time,'%d/%m/%Y').strftime('%Y-%m-%d')
    except Exception as e:
        logging.info("Exception in document_opening_time: {}".format(type(e).__name__))
        pass

    try:              
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, 'tr > td._T01_8 > a'):
            attachments_data = attachments()
            attachments_data.file_name = 'Notice'
            attachments_data.file_type = '.pdf'
        # Onsite Field -Notice PDF
        # Onsite Comment -None
            attachments_data.external_url = single_record.get_attribute('href')

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    try:
        notice_url = page_details.find_element(By.CSS_SELECTOR, 'dd > a').get_attribute("href")                     
        fn.load_page(page_details1,notice_url,80)
        logging.info(notice_url)
    except Exception as e:
        logging.info("Exception in notice_url2: {}".format(type(e).__name__))
        
    try:
        notice_data.notice_text += page_details1.find_element(By.CSS_SELECTOR, '#Content > dl').get_attribute("outerHTML")                     
    except:
        pass
# Onsite Field -None
# Onsite Comment -Note:In page_detail click "dd > a" and grab the data

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_language = 'EN'
        customer_details_data.org_country = 'ZM'
        # Onsite Field -Organisation Name
        # Onsite Comment -None

        customer_details_data.org_name = page_details1.find_element(By.XPATH, '//*[contains(text(),"Organisation Name")]//following::dd[1]').text
        
        # Onsite Field -Address:
        # Onsite Comment -None

        try:
            customer_details_data.org_address = page_details1.find_element(By.XPATH, '//*[contains(text(),"Address:")]//following::dd[1]').text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Postal Code:
        # Onsite Comment -None

        try:
            customer_details_data.postal_code = page_details1.find_element(By.XPATH, '//*[contains(text(),"Postal Code:")]//following::dd[1]').text
        except Exception as e:
            logging.info("Exception in postal_code: {}".format(type(e).__name__))
            pass

    # Onsite Field -City:
    # Onsite Comment -None

        try:
            customer_details_data.org_city = page_details1.find_element(By.XPATH, '//*[contains(text(),"City:")]//following::dd[1]').text
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass

    # Onsite Field -Email:
    # Onsite Comment -None

        try:
            customer_details_data.org_email = page_details1.find_element(By.XPATH, '//*[contains(text(),"Email:")]//following::dd[1]').text
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Phone Number:
        # Onsite Comment -None

        try:
            customer_details_data.org_phone = page_details1.find_element(By.XPATH, '//*[contains(text(),"Phone Number:")]//following::dd[1]').text
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass

    # Onsite Field -Fax:
    # Onsite Comment -None

        try:
            customer_details_data.org_fax = page_details1.find_element(By.XPATH, '//*[contains(text(),"Fax:")]//following::dd[1]').text
        except Exception as e:
            logging.info("Exception in org_fax: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Website
        # Onsite Comment -None

        try:
            customer_details_data.org_website = page_details1.find_element(By.XPATH, '//*[contains(text(),"Website")]//following::dd[1]').text
        except Exception as e:
            logging.info("Exception in org_website: {}".format(type(e).__name__))
            pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
#Ref for lot:https://eprocure.zppa.org.zm/epps/cft/prepareViewCfTWS.do?resourceId=3168327

    try: 
        lot_number=1
        for single_record in page_details.find_elements(By.XPATH, '//*[contains(text(),"Lot Name")]//following::dd[1]'):
            lot_details_data = lot_details()
            lot_details_data.lot_number= lot_number
        # Onsite Field -Lot Name
        # Onsite Comment -Note:Take both data

            lot_details_data.lot_title = single_record.text

            try:
                award_details_data = award_details()

                # Onsite Field -Award Date
                # Onsite Comment -None  tr > td:nth-child(9)
                award_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Date of Awarding:")]//following::dd[1]').text
                award_date = re.findall('\d+/\d+/\d{4}',award_date)[0]
                award_details_data.award_date = datetime.strptime(award_date,'%d/%m/%Y').strftime('%Y/%m/%d')
                
                award_details_data.award_details_cleanup()
                lot_details_data.award_details.append(award_details_data)
            except Exception as e:
                logging.info("Exception in award_details: {}".format(type(e).__name__))
                pass

            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
            lot_number +=1
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
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
page_details = fn.init_chrome_driver(arguments)
page_details1 = fn.init_chrome_driver(arguments) 
 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://eprocure.zppa.org.zm/epps/quickSearchAction.do;jsessionid=kJMwecXxj6PU7zMY+eUMiw__?searchSelect=1&selectedItem=quickSearchAction.do%3Bjsessionid%3DkJMwecXxj6PU7zMY+eUMiw__%3FsearchSelect%3D1"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        try:
            Advanced = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[contains(text(),"Advanced Search")]//following::button[1]')))
            page_main.execute_script("arguments[0].click();",Advanced)
        except:
            pass
        
        try:
            Tender_Status = Select(page_main.find_element(By.XPATH,'//*[@id="Status"]'))
            Tender_Status.select_by_index(6)
            time.sleep(5)
        except:
            pass
        
        try:
            Search = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="button_line"]/p/input[1]')))
            page_main.execute_script("arguments[0].click();",Search)
        except:
            pass
        
        try:
            click_go = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'tr > th.extra > a > img')))
            page_main.execute_script("arguments[0].click();",click_go)
        except:
            pass
        
        try:
            Notice_PDF = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//label[contains(text(),"Notice PDF  ")]')))
            page_main.execute_script("arguments[0].click();",Notice_PDF)
        except:
            pass
        
        try:
            Notice_PDF = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//label[contains(text(),"Award Date")]')))
            page_main.execute_script("arguments[0].click();",Notice_PDF)
        except:
            pass
        
        for page_no in range(1,5):
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
                    
                if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                    logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                    break

            if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                break

            try:   
                next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#CFTResults > div.Pagination > p:nth-child(2) > button:nth-child(5)')))
                page_main.execute_script("arguments[0].click();",next_page)
                logging.info("Next page")
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="T01"]/tbody/tr'),page_check))
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
