from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "au_qld_spn"
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
SCRIPT_NAME = "au_qld_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'au_qld_spn'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'AU'
    notice_data.main_language = 'ENG'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'AUD'
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -Note:Take a third line.......Note:If this select start with , , "App. for Prequalification" take notice type -"6" 

    try:
        notice_type = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > table:nth-child(5) tr > td:nth-child(2)').text.split('\n')[2].split('\n')[0].strip()
        if 'Expression of Interest' in notice_type or 'Request for Information' in notice_type:
            notice_data.notice_type = 5
        elif 'Tender' in notice_type or 'Invitation to Offer - Other Submission' in notice_type:
            notice_data.notice_type = 4
        elif 'App. for Prequalification' in notice_type:
            notice_data.notice_type = 6
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -Note:Take a text

    try:
        try:
            notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'a#MSG').text
            notice_data.notice_title = notice_data.local_title
        except:
            notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'u.TENDERNOLINK').text
            notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Date >> released
    # Onsite Comment -Note:Grab also time. #  5 Dec, 2023

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(4) > span.SUMMARY_OPENINGDATE").text
        notice_data.publish_date = datetime.strptime(publish_date,'%I:%M %p , %d %b, %Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Date >> closing
    # Onsite Comment -Note:Grab also time 

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(4) > span:nth-child(7)").text
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%I:%M %p , %d %b, %Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    # Onsite Field -None
    # Onsite Comment -Note:Take a third line

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text.split('\n')[2].split('\n')[0].strip()
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass    

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'a#MSG').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
     # Onsite Field -Request No.
    # Onsite Comment -Note:If notice_no is blank than take from notice_url in page_detail

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > b').text
    except:
        try:
            notice_data.notice_no = notice_data.notice_url.split('id=')[1].split('&')[0].strip()
        except Exception as e:
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass
        
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div#main').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '(//*[contains(text(),"Tender Overview")])[1]//following::td[1]').text
        notice_data.notice_summary_english = notice_data.local_description
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass

    try:
        category = ''
        try:
            for single_record in page_details.find_elements(By.XPATH, '''//*[contains(text(),"UNSPSC:")]//following::td[1]|//*[contains(text(),"UNSPSC 2:")]//following::td[1]|//*[contains(text(),"UNSPSC 3:")]//following::td[1]'''):
                category += single_record.text.split('-')[0].strip()
                category += ','
        except:
            pass
        try:
            category += page_details.find_element(By.XPATH, '''//*[contains(text(),"Mega Category")]//following::td[1]''').text
            category = category.rstrip(',')
            notice_data.category = category
        except:
            pass

        for codes in notice_data.category.split(','):
            cpv_codes = fn.CPV_mapping("assets/au_qld_spn_unspscpv.csv",codes)
            for cpv_code in cpv_codes:
                cpvs_data = cpvs()
                cpvs_data.cpv_code = cpv_code
                cpvs_data.cpvs_cleanup()
                notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpv_code: {}".format(type(e).__name__))
        pass
        

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'table:nth-child(7) tr > td:nth-child(1) > table > tbody'):
            customer_details_data = customer_details()
        # Onsite Field -Status & Type	Details
        # Onsite Comment -Note:Splite after "Issued by" or "UNSPSC"


            customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3) > span').text.split("Issued by")[1].split("UNSPSC:")[0].strip()

    # Onsite Field -Still need help? Contact Us
    # Onsite Comment -None

            try:
                customer_details_data.contact_person = page_details.find_element(By.CSS_SELECTOR, 'table:nth-child(7) tr > td:nth-child(1) tr > td  tr:nth-child(1) > td:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass
        
    # Onsite Field -None
    # Onsite Comment -Note:Splite after PHONE / PHONE(icon)

            try:
                try:
                    org_phone = re.findall("\(\d{3}\)\s\d{6}",single_record.text)[0]
                except:
                    pass
                try:
                    org_phone1 = re.findall("\d{11}|\d{4} \d{4}|\d{8}",single_record.text)[0]
                except:
                    pass
                
                org_phone_data = ''
                try:
                    org_phone_data += org_phone
                except:
                    pass
                if org_phone_data !='':
                    org_phone_data += ','
                try:
                    org_phone_data += org_phone1
                except:
                    pass
                org_phone = org_phone_data.rstrip(',')
                customer_details_data.org_phone = org_phone

            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass

    # Onsite Field -None
    # Onsite Comment -Note:Splite after email(icon)

            try:
                customer_details_data.org_email = page_details.find_element(By.CSS_SELECTOR, 'table:nth-child(7) tr > td:nth-child(1) > table > tbody a').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass

            customer_details_data.org_country = 'AU'
            customer_details_data.org_language = 'EN'
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:
        lot_title=[]
        for single_record in page_details.find_elements(By.XPATH, '''//*[contains(text(),"Lot")]//following::p/strong[1]|//*[contains(text(),'Apex')]''')[::2]:
            lot_title.append(single_record.text)
            
        lot_description = []
        for single_record1 in page_details.find_elements(By.XPATH, '''//*[contains(text(),"Lot")]//following::p/strong[1]|//*[contains(text(),'Apex')]''')[1::2]:
            lot_description.append(single_record1.text)
        
        lot_number = 1
        for title,description in zip(lot_title,lot_description):
            lot_details_data = lot_details()
            lot_details_data.lot_number = lot_number
        # Onsite Field -Lot
        # Onsite Comment -Note:Splite lot_actual_number before lot_title..Ex,"Lot A – Former Station Building" take for only "Lot A"

            try:
                lot_details_data.lot_actual_number = title.split('–')[0].strip()
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass

        # Onsite Field -Lot
        # Onsite Comment -Note:Splite after "Lot" this keyword... Ex,"Lot A – Former Station Building" take for only "Former Station Building" this

            try:
                lot_details_data.lot_title = title.split('–')[1].strip()
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass

        # Onsite Field -None
        # Onsite Comment -Note:Splite after lot_title.. Ex,"Lot A – Former Station Building: 3.7W x 16L x 3.6H (Apex)" take only "3.7W x 16L x 3.6H (Apex)" this

            try:
                lot_details_data.lot_description = description
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
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
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://qtenders.epw.qld.gov.au/qtenders/tender/search/tender-search.do?action=advanced-tender-search-open-tender&orderBy=closeDate&CSRFNONCE=27F8AA73BC4D3B1C6E06AB76D6F7215A"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,6):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'(//*[@id="hcontent"]//following::tr[not(@style="display:none")])[5]'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="hcontent"]//following::tr[not(@style="display:none")]')))
            length = len(rows)
            for records in range(4,length - 3,2):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="hcontent"]//following::tr[not(@style="display:none")]')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break


                if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                    logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                    break

            try:   
                next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                page_main.execute_script("arguments[0].click();",next_page)
                logging.info("Next page")
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'(//*[@id="hcontent"]//following::tr[not(@style="display:none")])[5]'),page_check))
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
    output_json_file.copyFinalJSONToServer(output_json_folder)
