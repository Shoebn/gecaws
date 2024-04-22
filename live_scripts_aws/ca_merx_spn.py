from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "ca_merx_spn"
log_config.log(SCRIPT_NAME)
import re
import time
import jsons
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "ca_merx_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"

def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'ca_merx_spn'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'CA'
    notice_data.performance_country.append(performance_country_data)
    

    notice_data.currency = 'CAD'
    
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 4

    notice_data.main_language = 'EN'
 
    
    notice_data.class_at_source = 'CPV'

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'span.rowTitle').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
   
    # Onsite Field -published
    # Onsite Comment -split the following data from this field

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, '.solicitation-link').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except:
        notice_data.notice_url = url
        
    try:
        cookie_accept = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.ID,'cookieBannerAcceptBtn')))
        page_details.execute_script("arguments[0].click();",cookie_accept)
    except:
        pass
            
    try:  
        publish_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Publication")]//following::p[1]').text
        publish_date = re.findall('\d{4}/\d+/\d+ \d+:\d+:\d+ [apAP][mM]',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%Y/%m/%d %I:%M:%S %p').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
       # Onsite Field -Closing
    # Onsite Comment -split the following data from this field

    try:
        notice_deadline = page_details.find_element(By.XPATH, '//*[contains(text(),"Closing Date")]//following::p[1]').text
        notice_deadline = re.findall('\d{4}/\d+/\d+ \d+:\d+:\d+ [apAP][mM]',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%Y/%m/%d %I:%M:%S %p').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
   
    try: 
        notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"Reference Number")]//following::p[1]').text
    except Exception as e:
        pass
    
    try:
        notice_data.related_tender_id = page_details.find_element(By.XPATH, '//*[contains(text(),"Solicitation Number")]//following::p[1]').text
    except:
        try:
            notice_data.related_tender_id = page_details.find_element(By.XPATH, '//*[contains(text(),"Project Number")]//following::p[1] ').text
        except Exception as e:
            pass
    
    try:
        see_more_clk = WebDriverWait(page_details, 20).until(EC.element_to_be_clickable((By.ID,'descriptionTextReadMore')))
        page_details.execute_script("arguments[0].click();",see_more_clk)
    except:
        pass
        
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Description")]//following::div[1]').text.replace('See more','')
        notice_data.notice_summary_english = notice_data.local_description
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass

    if (notice_data.notice_no is None or notice_data.notice_no == '') or (notice_data.notice_summary_english is None or notice_data.notice_summary_english == '') or (notice_data.local_description is None or notice_data.local_description  == ''):
        # handle login page
        page_details.delete_all_cookies()
        time.sleep(5)
        return
    
    # Onsite Field -"Solicitation Type" , "Project Type"
    # Onsite Comment -split the following data from this field, url ref :  "https://www.merx.com/mbgov/solicitations/open-bids/REQUEST-FOR-PURPOSAL-HAZARDOUS-WASTE-STORAGE-BUILDINGS/0000252652?origin=0" , "https://www.merx.com/solicitations/open-bids/Long-Term-Care-Construction-160-Beds-Orillia/0000252660?origin=0"

    try:    
        notice_data.document_type_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Solicitation Type")]//following::p[1]').text.replace('See more','')
    except:
        try:
            notice_data.document_type_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Project Type")]//following::p[1]').text.replace('See more','')
        except Exception as e:
            logging.info("Exception in document_type_description: {}".format(type(e).__name__))
            pass
    

    try:              
        customer_details_data = customer_details()
        # Onsite Field -Issuing Organization
        # Onsite Comment -split the following data from this field
        customer_details_data.org_country = 'CA'
        customer_details_data.org_language = 'EN'
        customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Issuing Organization")]//following::p[1]').text

        
        # Onsite Field -Contact Information
        # Onsite Comment -take the following data from this field, url ref : "https://www.merx.com/solicitations/open-bids/Thrombin-Generation-Analyzer-with-Consumables/0000252653?origin=0"
        
        try:
            customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Contact Information")]//following::p[1]').text
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass
    
        # Onsite Field -Contact Information
        # Onsite Comment -take the following data from this field, url ref : "https://www.merx.com/solicitations/open-bids/Thrombin-Generation-Analyzer-with-Consumables/0000252653?origin=0"
        
        try:
            org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Contact Information")]//following::p[2]').text
            if len(org_phone)>9:
                customer_details_data.org_phone = org_phone
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass
    
        # Onsite Field -Contact Information
        # Onsite Comment -take the following data from this field

        try:
            customer_details_data.org_email = fn.get_email(page_details.find_element(By.CSS_SELECTOR, '.content-block').text)
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass
        
        if customer_details_data.org_name != None:
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
 
    # Onsite Field -MERX Category (1 selected)
    # Onsite Comment -go to the "categories" tab and split the data

    try:
        noticeAbstract = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.ID,'descriptionTextReadMore')))
        page_details.execute_script("arguments[0].click();",noticeAbstract)
    except:
        pass
    
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'main > div #innerTabContent').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
        
    try:
        noticeAbstract = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'li.mets-tab.enabled:nth-child(2) > a:nth-child(1)')))
        page_details.execute_script("arguments[0].click();",noticeAbstract)
        try:
            notice_contract_type = page_details.find_element(By.XPATH, '//*[contains(text(),"MERX Categor")]//following::td[3]//span').text
        except:
            try:
                notice_contract_type = page_details.find_element(By.XPATH, '//*[contains(text(),"MERX Category")]//following::td[3]//span').text
            except:
                notice_contract_type = page_details.find_element(By.CSS_SELECTOR, '//tbody').text

                
        if 'service' in notice_contract_type.lower():
            notice_data.notice_contract_type = 'Service'
        elif 'works' in notice_contract_type.lower():
            notice_data.notice_contract_type = 'Works'
        elif 'supply' in notice_contract_type.lower():
            notice_data.notice_contract_type = 'Supply'
        elif 'consultancy' in notice_contract_type.lower():
            notice_data.notice_contract_type = 'Consultancy'
        elif 'non consultancy' in notice_contract_type.lower():
            notice_data.notice_contract_type = 'Non consultancy'
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    try:
        Catego_clk = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,'Categories')))
        page_details.execute_script("arguments[0].click();",Catego_clk)
    except:
        pass


    try:
        cpv_at_source = ''
        for single_record in WebDriverWait(page_details, 50).until(EC.presence_of_all_elements_located((By.XPATH,'//*[contains(text(),"UNSPSC Catego")]//following::tr/td[1]'))):
            category1 = single_record.text
            category = re.findall('\d{8}',category1)[0]
            cpv_codes_list = fn.CPV_mapping("assets/ca_merx_spn_unspsc_category.csv",category)
            for each_cpv in cpv_codes_list:
                cpvs_data = cpvs()
                cpv_code1 = each_cpv
                cpv_code = re.findall('\d{8}',cpv_code1)[0]                
                cpvs_data.cpv_code = cpv_code
                cpvs_data.cpvs_cleanup()
                notice_data.cpvs.append(cpvs_data)
                cpv_at_source += cpv_code
                cpv_at_source += ','
            notice_data.cpv_at_source = cpv_at_source.rstrip(',') 
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
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
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.merx.com/"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            # navbar section click on  "Canadian Tenders"
            clicked_tendersPage = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.ID,'header_btnCanadianMarket')))
            page_main.execute_script("arguments[0].click();",clicked_tendersPage)
        except:
            pass

        try:
            for page_no in range(2,10):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="solicitationsList"]/tbody/tr/td'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="solicitationsList"]/tbody/tr/td')))
                length = len(rows)
                for records in range(0,length-1):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="solicitationsList"]/tbody/tr/td')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
      
                try:   
                    fn.load_page(page_main , 'https://www.merx.com/public/solicitations/open?pageNumber='+str(page_no), 50)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="solicitationsList"]/tbody/tr/td'),page_check))
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
