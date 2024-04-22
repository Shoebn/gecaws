from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "us_ssldoasgpr_spn"
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
from selenium.webdriver.chrome.options import Options

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "us_ssldoasgpr_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
   
    notice_data.script_name = 'us_ssldoasgpr_spn'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'US'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'USD'
    
    notice_data.main_language = 'EN'
    
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 4
    
    
    # Onsite Field -Event ID
    # Onsite Comment -Note:If notice_no is not present than teke from notice_url in page_detail
    # https://ssl.doas.state.ga.us/gpr/eventDetails?eSourceNumber=PE-72155-NONST-2024-000000035&sourceSystemType=gpr20
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Event Title

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        notice_data.notice_title = notice_data.local_title 
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Start Date (ET)  Dec 28, 2023 @ 01:11 PM
    # Onsite Comment -Note:Grab time also

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(5)").text
        publish_date = re.findall('\w+ \d+, \d{4} @ \d+:\d+ [PMAMpmam]+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%b %d, %Y @ %I:%M %p').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -End Date (ET)
    # Onsite Comment -Note:Grab time also

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(6)").text
        notice_deadline = re.findall('\w+ \d+, \d{4} @ \d+:\d+ [PMAMpmam]+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%b %d, %Y @ %I:%M %p').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Event ID

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
        
        # Onsite Comment -Note:"along with notice text (page detail) also take data from tender_html_element (//*[@id="eventSearchTable"]/tbody/tr)."
        try:
            notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.page').get_attribute("outerHTML")                     
        except:
            notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
        
        try:
            if notice_data.notice_no !="":
                notice_data.notice_no = notice_data.notice_url.split("=")[1].split("&")[0].strip()
        except:
            pass
        
        # Onsite Field -Event Type
        try:
            notice_data.document_type_description = page_details.find_element(By.CSS_SELECTOR, 'div.tbody > div.tr > div:nth-child(2)').text
        except Exception as e:
            logging.info("Exception in document_type_description: {}".format(type(e).__name__))
            pass
    
        # Onsite Field -Category Type
        # Onsite Comment -Note:"Replace follwing keywords with given keywords ("Construction / Public Works=Works",
        #"Design Professional, General Consultant=Service","Goods=Supply","Information Technology=Service","Services / Special Projects=Service")"
        try:
            notice_data.contract_type_actual = page_details.find_element(By.CSS_SELECTOR, 'div.tbody > div.tr > div:nth-child(5)').text
            if 'Construction / Public Works' in notice_data.contract_type_actual:
                notice_data.notice_contract_type = 'Works'
            elif 'Design Professional, General Consultant' in notice_data.contract_type_actual or 'Information Technology' in notice_data.contract_type_actual or 'Services / Special Projects' in notice_data.contract_type_actual:
                notice_data.notice_contract_type = 'Service'
            elif 'Goods' in notice_data.contract_type_actual:
                notice_data.notice_contract_type = 'Supply'
        except Exception as e:
            logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Agency Site
        try:
            notice_data.additional_tender_url = page_details.find_element(By.CSS_SELECTOR, 'div.tbody > div.tr > div:nth-child(8) a').text
        except Exception as e:
            logging.info("Exception in additional_tender_url: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Description
        try:
            notice_data.local_description = page_details.find_element(By.CSS_SELECTOR, 'div:nth-child(5) > p').text
            notice_data.notice_summary_english = notice_data.local_description
        except Exception as e:
            logging.info("Exception in local_description: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -NIGP Codes
        # Onsite Comment -Note:Click on "#tab-eventDetails" this tab than grab the data............     Note:If lot is not showing than click on "<" this button than grab the data
        # Ref_url=https://ssl.doas.state.ga.us/gpr/eventDetails?eSourceNumber=PE-55214-NONST-2024-000000012&sourceSystemType=gpr20

        try:  
            lot_number = 1
            for single_record in page_details.find_elements(By.XPATH, '//*[contains(text(),"NIGP Codes")]//following::table/tbody/tr'):
                lot_details_data = lot_details()
                lot_details_data.lot_number = lot_number
                lot_details_data.lot_contract_type_actual = notice_data.contract_type_actual
                lot_details_data.contract_type = notice_data.notice_contract_type
                
                # Onsite Field -Code
                try:
                    lot_details_data.lot_actual_number = single_record.find_element(By.CSS_SELECTOR, 'td.bold').text
                except Exception as e:
                    logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                    pass

                # Onsite Field -Description
                lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text

                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
                lot_number +=1
        except Exception as e:
            logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
            pass
        
        # Onsite Comment -Note:Click on "#tab-eventDetails" this tab than grab the data
        # Ref_url=https://ssl.doas.state.ga.us/gpr/eventDetails?eSourceNumber=PE-55046-NONST-2024-000000007&sourceSystemType=gpr20

        try:              
            customer_details_data = customer_details()
            customer_details_data.org_country = 'US'
            customer_details_data.org_language = 'EN'
            # Onsite Field -Government Entity

            customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(4)').text
            # Onsite Field -Purchase Type
            try:
                customer_details_data.customer_main_activity = page_details.find_element(By.CSS_SELECTOR, 'div.tbody > div.tr > div:nth-child(4)').text
            except Exception as e:
                logging.info("Exception in customer_main_activity: {}".format(type(e).__name__))
                pass

            # Onsite Field -Buyer Contact
            try:
                org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Buyer Contact")]//following::p[1]/a').text
                email_regex = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b')
                customer_details_data.contact_email = email_regex.findall(org_email)[0]
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass

            # Onsite Field -Buyer Contact
            # Onsite Comment -Note:Splite befor the <a> tag....EX,"Joan Carter     purchasing@sccpss.com    912-395-5572" take only "Joan Carter"
            try:
                customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Buyer Contact")]//following::p[1]').text.split(customer_details_data.contact_email)[0].strip()
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass

            # Onsite Field -Buyer Contact
            # Onsite Comment -Note:Splite after the "<a>" tag
            try:
                customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Buyer Contact")]//following::p[1]').text.split(customer_details_data.contact_email)[1].strip()
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass

            try:
                Offerors_conference_click = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"#tab-Offerors")))
                page_details.execute_script("arguments[0].click();",Offerors_conference_click)
                time.sleep(8)
                WebDriverWait(page_details, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#collapse-Offerors > div > div.table.mobile-accordion')))
                
                try:
                    notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.page').get_attribute("outerHTML")                     
                except:
                    pass

            # https://ssl.doas.state.ga.us/gpr/eventDetails?eSourceNumber=PE-68660-NONST-2024-000000002&sourceSystemType=gpr20
            # Note:Click on "#tab-Offerors" this tab on page_detail than grab below the data

                # Onsite Field -Street
                try:
                    customer_details_data.org_address = page_details.find_element(By.CSS_SELECTOR, 'div.tr.alternate-highlight > div:nth-child(4)').text
                except Exception as e:
                    logging.info("Exception in org_address: {}".format(type(e).__name__))
                    pass

                # Onsite Field -City
                try:
                    customer_details_data.org_city = page_details.find_element(By.CSS_SELECTOR, 'div.tr.alternate-highlight > div:nth-child(5)').text
                except Exception as e:
                    logging.info("Exception in org_city: {}".format(type(e).__name__))
                    pass

                # Onsite Field -State
                try:
                    customer_details_data.org_state = page_details.find_element(By.CSS_SELECTOR, 'div.tr.alternate-highlight > div:nth-child(6)').text
                except Exception as e:
                    logging.info("Exception in org_state: {}".format(type(e).__name__))
                    pass

                # Onsite Field -Zip Code
                try:
                    customer_details_data.postal_code = page_details.find_element(By.CSS_SELECTOR, 'div.tr.alternate-highlight > div:nth-child(7)').text
                except Exception as e:
                    logging.info("Exception in postal_code: {}".format(type(e).__name__))
                    pass
            except:
                pass

            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
        except Exception as e:
            logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
            pass
        
        # Onsite Field -Documents
        # Onsite Comment -Note:Click on "#tab-documents" this tab than grab then data
        # Ref_url=https://ssl.doas.state.ga.us/gpr/eventDetails?eSourceNumber=PE-77548-NONST-2024-000000046&sourceSystemType=gpr20

        try:
            documents_click = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"#tab-documents")))
            page_details.execute_script("arguments[0].click();",documents_click)
            time.sleep(8)
            WebDriverWait(page_details, 50).until(EC.presence_of_element_located((By.XPATH,'(//h4)[3]')))
            
            try:
                notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.page').get_attribute("outerHTML")                     
            except:
                pass

            for single_record in page_details.find_elements(By.XPATH, '//*[contains(text(),"Documents")]//following::ul/li'):
                
                attachments_data = attachments()
            # Onsite Field -Documents
            # Onsite Comment -Note:Don't take file extention

                attachments_data.file_name = single_record.text.split('.')[0].strip()
                
                try:
                    attachments_data.file_type = single_record.text.split('.')[1].strip()
                except Exception as e:
                    logging.info("Exception in file_type: {}".format(type(e).__name__))
                    pass

                attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')

                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
        except Exception as e:
            logging.info("Exception in attachments: {}".format(type(e).__name__)) 
            pass
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_url) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title)
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
options = Options()
for argument in arguments:
    options.add_argument(argument)
page_main = webdriver.Chrome(options=options)
page_details = webdriver.Chrome(options=options) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://ssl.doas.state.ga.us/gpr/index?persisted=true"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        for page_no in range(2,5):
            page_check = WebDriverWait(page_main, 80).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[1]/div/div[1]/div/div[3]/div/div[2]/div/table/tbody/tr[1]'))).text
            rows = WebDriverWait(page_main, 80).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/div/div[1]/div/div[3]/div/div[2]/div/table/tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 80).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/div/div[1]/div/div[3]/div/div[2]/div/table/tbody/tr')))[records]
                extract_and_save_notice(tender_html_element)
                
                if notice_count >= MAX_NOTICES:
                    break
                    
                if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                    logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                    break

            try:   
                next_page = WebDriverWait(page_main, 80).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                page_main.execute_script("arguments[0].click();",next_page)
                logging.info("Next page")
                WebDriverWait(page_main, 80).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/div[1]/div/div[1]/div/div[3]/div/div[2]/div/table/tbody/tr[1]'),page_check))
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
