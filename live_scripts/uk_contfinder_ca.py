from gec_common.gecclass import *
import logging
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

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "uk_contfinder_ca"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    # Onsite Field -None
    # Onsite Comment -click on "Procurement stage > Definitions >  Awarded contract" only for get records for ca
    
    notice_data.script_name = 'uk_contfinder_ca'
    
    notice_data.main_language = 'EN'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'GB'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'GBP'
    
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 7
    
    # Onsite Field -Procurement stage
    # Onsite Comment -None

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'div.search-result > div:nth-child(6)').text.split('Procurement stage')[1]
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.search-result-header > h2').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Publication date
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, " div:nth-child(n) > div:nth-child(10)").text
        publish_date = re.findall('\d+ \w+ \d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d %B %Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.search-result-header > h2 > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#standard-body').get_attribute("outerHTML") 
    except:
        try:
            notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div#standard-body.standard-body-plain').get_attribute("outerHTML") 
        except Exception as e:                                                     
            logging.info("Exception in notice_text: {}".format(type(e).__name__))
            pass
    
    # Onsite Field -Procurement reference
    # Onsite Comment -None

    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"Procurement reference")]//following::p[1]').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Contract type
    # Onsite Comment -None

    try:
        notice_data.notice_contract_type = page_details.find_element(By.XPATH, '//*[contains(text(),"Contract type")]//following::p[1]').text.split(' ')[0]
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Procedure type
    # Onsite Comment -None
    try:
        notice_data.type_of_procedure_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Procedure type")]//following::p[1]').text
        notice_data.type_of_procedure = fn.procedure_mapping("assets/uk_contfinder_procedure.csv",notice_data.type_of_procedure_actual)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Value of contract
    # Onsite Comment -None

    try:
        grossbudgetlc = page_details.find_element(By.XPATH, '//*[contains(text(),"Value of contract")]//following::p[1]').text
        grossbudgetlc = re.sub("[^\d\.\,]", "", grossbudgetlc)
        notice_data.grossbudgetlc = float(grossbudgetlc.replace(',','').strip())
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Value of contract
    # Onsite Comment -None

    try:
        notice_data.est_amount = notice_data.grossbudgetlc
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_summary_english = page_details.find_element(By.CSS_SELECTOR, 'div:nth-child(4) > p:nth-child(4)').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = notice_data.notice_summary_english
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'GB'
        customer_details_data.org_language = 'EN'
       
        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div.search-result > div:nth-child(2)').text
        # Onsite Field -Address
        # Onsite Comment -None

        try:
            org_address = page_details.find_element(By.CSS_SELECTOR, '#standard-body').text
            if 'Address' in org_address:
                try:
                    customer_details_data.org_address = org_address.split('Address')[1].split('Telephone')[0].split('Email')[0]
                except:
                    customer_details_data.org_address = org_address.split('Address')[1].split('Email')[0]
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Location of contract
        # Onsite Comment -None

        try:
            customer_details_data.org_city = page_details.find_element(By.XPATH, '//*[contains(text(),"Location of contract")]//following::p[1]').text
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Contact name
        # Onsite Comment -None

        try:
            customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Contact name")]//following::p[1]').text
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Telephone
        # Onsite Comment -None

        try:
            customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Telephone")]//following::p[1]').text
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Email
        # Onsite Comment -take only "Email" data from the given selector

        try:
            customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Email")]//following::p[1]').text
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass
        
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
        

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#content-holder-left > div:nth-child(3) > ul > li'):
            cpvs_data = cpvs()
            # Onsite Field -Industry
            # Onsite Comment -take "Industry" field data and take numeric value from the given selector only for cpv_code
            cpvs_data.cpv_code = single_record.text.split('- ')[1]
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass 

    try:              
        lot_details_data = lot_details()
        lot_details_data.lot_number = 1
        # Onsite Field -Value of contract
        # Onsite Comment -None
        lot_details_data.lot_title = notice_data.notice_title
        notice_data.is_lot_default = True
        try:
            lot_details_data.lot_grossbudget_lc = notice_data.grossbudgetlc
        except Exception as e:
            logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
            pass
                               
        # Onsite Field -Contract type
        # Onsite Comment -None

        try:
            lot_details_data.contract_type = notice_data.notice_contract_type
        except Exception as e:
            logging.info("Exception in contract_type: {}".format(type(e).__name__))
            pass
                       
        try:
            lot_cpvs_data = lot_cpvs()
            # Onsite Field -Industry
            # Onsite Comment -take "Industry" field data and take numeric value from the given selector only for cpv_code
            lot_cpvs_data.lot_cpv_code = cpvs_data.cpv_code
            lot_cpvs_data.lot_cpvs_cleanup()
            lot_details_data.lot_cpvs.append(lot_cpvs_data)
        except Exception as e:
            logging.info("Exception in lot_cpvs: {}".format(type(e).__name__))
            pass
   
        try:
            award_details_data = award_details()
            # Onsite Field -Awarded supplier
            # Onsite Comment -None

            award_details_data.bidder_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div.search-result > div:nth-child(9)').text.split('supplier')[1]
            
            # Onsite Field -Awarded value
            # Onsite Comment -None

            try:
                grossawardvaluelc = tender_html_element.find_element(By.CSS_SELECTOR, 'div.search-result > div:nth-child(8)').text
                grossawardvaluelc = re.sub("[^\d\.\,]", "", grossawardvaluelc)
                award_details_data.grossawardvaluelc = float(grossawardvaluelc.replace(',','').strip())
            except Exception as e:
                logging.info("Exception in grossawardvaluelc: {}".format(type(e).__name__))
                pass
            # Onsite Field -Awarded date
            # Onsite Comment -None

            try:
                award_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Awarded date")]//following::p[1]').text
                award_date = re.findall('\d+ \w+ \d{4}',award_date)[0]
                award_details_data.award_date = datetime.strptime(award_date,'%d %B %Y').strftime('%Y/%m/%d')
            except Exception as e:
                logging.info("Exception in award_date: {}".format(type(e).__name__))
                pass
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
    
# Onsite Field -More information
# Onsite Comment -take attachments data if the onsite field " More information" has keyword "Attachments"

    try:  
        data = page_details.find_element(By.CSS_SELECTOR, '#standard-body').text
        if 'Attachments' in data:
            for single_record in page_details.find_elements(By.CSS_SELECTOR, 'ul > li.list-no-bullets'):
                attachments_data = attachments()
            # Onsite Field -Attachments
            # Onsite Comment -split file_type from the given selector

                try:
                    attachments_data.file_type = single_record.find_element(By.CSS_SELECTOR, ' a').text.split('.')[1]
                except Exception as e:
                    logging.info("Exception in file_type: {}".format(type(e).__name__))
                    pass
        
        # Onsite Field -Attachments
        # Onsite Comment -take file_name in textform

                attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, ' a').text.split('.')[0]
        
        # Onsite Field -Attachments
        # Onsite Comment -None

                attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, ' a').get_attribute('href')
                
                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
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
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://www.contractsfinder.service.gov.uk/Search/Results'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH, '//*[contains(text(),"Early engagement")]//parent::div'))).click()
        time.sleep(5)
        
        click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH, '//*[contains(text(),"Future opportunity")]//parent::div'))).click()
        time.sleep(5)
        
        click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[contains(text(),"Opportunity")]//parent::div'))).click()
        time.sleep(5)
        
        click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH, '//*[contains(text(),"Awarded contract")]//parent::div'))).click()

        time.sleep(5)
        
        click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="adv_search_button"]')))
        page_main.execute_script("arguments[0].click();",click)
        
        try:
            WebDriverWait(page_details, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#f84b94b2-016b-4c69-9312-4be25e88e2db ')))
        except:
            pass

        try:
            for page_no in range(2,4):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="dashboard_notices"]/div[1]/div'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="dashboard_notices"]/div[1]/div')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="dashboard_notices"]/div[1]/div')))[records]
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
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="dashboard_notices"]/div[1]/div'),page_check))
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
