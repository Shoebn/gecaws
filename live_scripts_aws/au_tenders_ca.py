import logging
from gec_common import log_config
SCRIPT_NAME = "au_tenders_ca"
log_config.log(SCRIPT_NAME)
from selenium import webdriver
import jsons
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
import time
import re
import gec_common.OutputJSON
from gec_common.gecclass import *

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "au_tenders_ca"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"

# --------------------------------------------------------------------------------------------------------------------------------------------------


# to explore CA detail -------- 1) Go to url "tenders.gov.au/cn/search"
#                              2) scroll down and click on magneflying glass button (selector : "#actions > div > button")  
#           
                     
#  in the  tender_html_page if contract_notices shows "Amends:" (ex. " Amends:CN3911899 ") field, then skip that notice 

# -------------------------------------------------------------------------------------------------------------------------------------------------------------

def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'au_tenders_ca'

    notice_data.main_language = 'EN'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'AU'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'AUD'
    
    notice_data.procurement_method = 2

    notice_data.notice_type = 7
    
    # Onsite Field -CN ID:
    # Onsite Comment -split the data from tender_html page
    
    if 'Amends:' in tender_html_element.text:
        return
    
    # Onsite Field -Full Details
    # Onsite Comment -inspect url for detail_page , ref_url for detail_page : "https://www.tenders.gov.au/Cn/Show/dea386ba-7fdb-46ef-be92-ee56e49af7e1"

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'a.detail').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
        
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'article div.col-sm-8 div div:nth-child(1) > div').text
    except:
        try:
            notice_data.notice_no = page_details.find_element(By.XPATH, "//*[contains(text(),'Agency Reference ID:')]//following::div[1]").text
        except:
            try:
                notice_data.notice_no = notice_data.notice_url.split("-")[-1]
            except Exception as e:
                logging.info("Exception in notice_no: {}".format(type(e).__name__))
                pass
    
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#mainContent div.row').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')

    try:       
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div > div.last-updated").text
        publish_date = re.findall('\d+-\w+-\d{4} \d+:\d+ [PMAMpmam]+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d-%b-%Y %I:%M %p').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Description:
    # Onsite Comment -split local_title from detail_page

    try:
        notice_data.local_title = page_details.find_element(By.XPATH, '//*[contains(text(),"Description")]//following::div[1]').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    # Onsite Field -Procurement Method:
    # Onsite Comment -split the data from detail_page
    try:
        notice_data.type_of_procedure_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Procurement Method")]//following::div[1]').text
        notice_data.type_of_procedure = fn.procedure_mapping("assets/au_tenders_ca_procedure.csv",notice_data.type_of_procedure_actual)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    try:
        netbudgetlc = page_details.find_element(By.XPATH, '//*[contains(text(),"Contract Value")]//following::div[1]').text
        netbudgetlc = re.sub("[^\d\.\,]","",netbudgetlc)
        notice_data.netbudgetlc =float(netbudgetlc.replace(',','').strip())
        notice_data.est_amount = notice_data.netbudgetlc
    except:
        pass
    
    try:
        notice_data.related_tender_id = page_details.find_element(By.XPATH, '//*[contains(text(),"SON ID:")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Description")]//following::div[1]').text
        notice_data.notice_summary_english = notice_data.local_description
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass

    try:
        notice_data.related_tender_id = page_details.find_element(By.XPATH, "//*[contains(text(),'Agency Reference ID')]//following::div[1]").text
    except Exception as e:
        logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
        pass
# Onsite Field -None
# Onsite Comment -split the customer_details from detail_page

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'AU'
        customer_details_data.org_language = 'EN'
    # Onsite Field -Agency:
    # Onsite Comment -split the data from detail_page
        customer = page_details.find_element(By.CSS_SELECTOR, 'div.col-sm-4 > div.pc > div').text
        customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Agency:")]//following::div[1]').text
        # Onsite Field -Contact Name:
        # Onsite Comment -split the data from "Agency Details" field , in detail_page, ref_url : "https://www.tenders.gov.au/Cn/Show/2a334fcb-ec18-4663-a360-a27bc04dfe3c"

        try:
            customer_details_data.contact_person = customer.split('Contact Name:')[1].split("\n")[1]
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass

    # Onsite Field -Phone:
    # Onsite Comment -split the data between "Phone:" and "Email Address:" field, ref_url : "https://www.tenders.gov.au/Cn/Show/2a334fcb-ec18-4663-a360-a27bc04dfe3c"

        try:
            org_phone = customer.split('Phone:')[1].split("\n")[1]
            if 'Email Address:' not in org_phone:
                customer_details_data.org_phone = org_phone
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass

        # Onsite Field -Email Address:
        # Onsite Comment -split the data between "Email Address:" and "Division:" field, ref_url : "https://www.tenders.gov.au/Cn/Show/61afdf8f-c566-4fed-8172-bc2b8d0e1508"

        try:
            org_email = customer.split('Email Address:')[1].split("\n")[1]
            email_regex = re.compile(r"[\w\.-]+@[\w\.-]+")
            customer_details_data.org_email = email_regex.findall(org_email)[0]
        except Exception as e:
            logging.info("Exception in org_website: {}".format(type(e).__name__))
            pass

    # Onsite Field -Office Postcode:
    # Onsite Comment -ref_url : "https://www.tenders.gov.au/Cn/Show/138d0d57-fbf6-4486-8741-b7f2a1dcd875"

        try:
            customer_details_data.postal_code = customer.split('Office Postcode:')[1].split("\n")[1]
        except Exception as e:
            logging.info("Exception in postal_code: {}".format(type(e).__name__))
            pass
        try:
            customer_details_data.type_of_authority_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Agency Reference ID:")]//following::div[1]').text
        except Exception as e:
            logging.info("Exception in type_of_authority_code: {}".format(type(e).__name__))
            pass
        
        try:
            customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Email Address:")]//following::a[1]').text
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass
        try:
            customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Branch:")]/..').text.split(":")[1].strip()
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass
        
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try:
        notice_data.category  = page_details.find_element(By.XPATH, '//*[contains(text(),"Category:")]//following::div[1]').text
        cpv_codes_list = fn.CPV_mapping("assets/au_tenders_ca_category.csv",notice_data.category)
        cpv_at_source = ''
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
    
# Onsite Field -None
# Onsite Comment -split the data from detail_page

    try:              
        lot_details_data = lot_details()
        lot_details_data.lot_number = 1
        lot_details_data.lot_title = notice_data.local_title
        notice_data.is_lot_default = True
        try:
            contract_start_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Contract Period")]//following::div[1]').text.split('to')[0]
            contract_start_date = re.findall('\d+-\w+-\d{4}',contract_start_date)[0]
            lot_details_data.contract_start_date= datetime.strptime(contract_start_date,'%d-%b-%Y').strftime('%Y/%m/%d %H:%M:%S')
        except Exception as e:
            logging.info("Exception in contract_start_date: {}".format(type(e).__name__))
            pass

    # Onsite Field -Contract Period:
    # Onsite Comment -split contract_end_date for ex."7-Aug-2023 to 30-Oct-2024", here split only "30-Oct-2024" ,        ref_url : "https://www.tenders.gov.au/Cn/Show/61afdf8f-c566-4fed-8172-bc2b8d0e1508"

        try:
            contract_end_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Contract Period")]//following::div[1]').text.split("to")[1]
            contract_end_date = re.findall('\d+-\w+-\d{4}',contract_end_date)[0]
            lot_details_data.contract_end_date= datetime.strptime(contract_end_date,'%d-%b-%Y').strftime('%Y/%m/%d %H:%M:%S')
        except Exception as e:
            logging.info("Exception in contract_end_date: {}".format(type(e).__name__))
            pass
        
        try:
            award_details_data = award_details()
            # Onsite Field -Name:
            # Onsite Comment -split the "bidder_name" from "Supplier Details" field, ref_url : "https://www.tenders.gov.au/Cn/Show/80a1f195-da33-4b60-b77b-6ca184fa0bed"
            award_details_data.bidder_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Supplier Details")]//following::div[2]').text
            # Onsite Field -Postal Address:
            # Onsite Comment -split the "address" from "Postal Address:" to "country" field (i.e take "Postal Address:","Town/City:","Postcode:","State/Territory:","Country:" , all fields in address), ref_url : "https://www.tenders.gov.au/Cn/Show/80a1f195-da33-4b60-b77b-6ca184fa0bed"
            try:
                address1 = page_details.find_element(By.XPATH, '//*[contains(text(),"Postal Address:")]//following::div[1]').text
                address2 = page_details.find_element(By.XPATH, '//*[contains(text(),"Postal Address:")]//following::div[3]').text
                address3 = page_details.find_element(By.XPATH, '//*[contains(text(),"Postal Address:")]//following::div[5]').text
                address4 = page_details.find_element(By.XPATH, '//*[contains(text(),"Postal Address:")]//following::div[7]').text
                address5 = page_details.find_element(By.XPATH, '//*[contains(text(),"Postal Address:")]//following::div[9]').text
                address6 = page_details.find_element(By.XPATH, '//*[contains(text(),"Postal Address:")]//following::div[11]').text
                award_details_data.address = address1+' '+address2+' '+address3+' '+address4+' '+address5+' '+address6
            except:
                try:
                    address1 = page_details.find_element(By.XPATH, '//*[contains(text(),"Town/City:")]//following::div[1]').text
                    address2 = page_details.find_element(By.XPATH, '//*[contains(text(),"Town/City:")]//following::div[3]').text
                    address3 = page_details.find_element(By.XPATH, '//*[contains(text(),"Town/City:")]//following::div[5]').text
                    address4 = page_details.find_element(By.XPATH, '//*[contains(text(),"Town/City:")]//following::div[7]').text
                    address5 = page_details.find_element(By.XPATH, '//*[contains(text(),"Town/City:")]//following::div[9]').text
                    award_details_data.address = address1+' '+address2+' '+address3+' '+address4+' '+address5
                except:
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

    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#mainContent > div > div.row').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) + str(notice_data.publish_date) +  str(notice_data.notice_url) 
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
page_main = fn.init_chrome_driver_head(arguments) 
page_details = fn.init_chrome_driver_head(arguments) 

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.tenders.gov.au/Search/CnAdvancedSearch?SearchFrom=CnSearch&Type=Cn&AgencyStatus=-1&KeywordTypeSearch=AllWord&DateType=Publish%20Date"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url) 
        
        try:
            login_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#s2menu > li.menu-login')))
            page_main.execute_script("arguments[0].click();",login_click)
            time.sleep(2)

            mailto = page_main.find_element(By.CSS_SELECTOR,'#login-username').send_keys('akanksha@globalecontent.com')
            time.sleep(2)
            password = page_main.find_element(By.CSS_SELECTOR,'#login-password').send_keys('dg@1234567')

            submit_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#login-form > input.goLogIn')))
            page_main.execute_script("arguments[0].click();",submit_click)
            time.sleep(5)
        except Exception as e:
            logging.info("Exception in login_error: {}".format(type(e).__name__)) 
            pass
        
        try:  
            last_update_div = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="sortForm"]/div/div/div/div[2]/div/div[2]/div/div/div/button'))).click()
            time.sleep(2)
            last_update_to = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="sortForm"]/div/div/div/div[2]/div/div[2]/div/div/div/div/ul/li[2]/a'))).click()
            time.sleep(2)
            sort = page_main.find_element(By.XPATH, '//*[@id="form-sort-1"]').click()
            time.sleep(2)
        except Exception as e:
            logging.info("Exception in last_update: {}".format(type(e).__name__)) 
            pass

        try:
            for page_no in range(1,7):#7
                page_check = WebDriverWait(page_main, 80).until(EC.presence_of_element_located((By.XPATH,'//*[@id="mainContent"]/div[3]/div[2]/article/div/div[2]'))).text
                rows = WebDriverWait(page_main, 80).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="mainContent"]/div[3]/div[2]/article/div/div[2]')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 80).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="mainContent"]/div[3]/div[2]/article/div/div[2]')))[records]
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
                    next_page = WebDriverWait(page_main, 80).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="mainContent"]/div[3]/div[3]/ul/li[13]/a')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 80).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="mainContent"]/div[3]/div[2]/article/div/div[2]'),page_check))
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
