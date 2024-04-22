from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "za_erwat"
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
SCRIPT_NAME = "za_erwat"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"

def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.main_language = 'DE'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'ZA'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'ZAR'
        
    notice_data.procurement_method = 2
        
    if url == urls[0] or url == urls[1] or url == urls[2]:
        notice_data.script_name = 'za_erwat_spn'
        notice_data.notice_type = 4
    elif url == urls[3]:
        notice_data.script_name = 'za_erwat_ca'
        
    if url == urls[0]:
        notice_data.document_type_description = 'GENERAL NOTICE'
    if url == urls[1]:
        notice_data.document_type_description = "GENERAL NOTICE"
    if url == urls[2]:
        notice_data.document_type_description = "Quotations"
        
    if url == urls[3]:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
        if 'In Progress' in notice_data.document_type_description or "Non-Award" in notice_data.document_type_description:
            return
        if 'Awarded' in notice_data.document_type_description:
            notice_data.notice_type = 7
        if 'Cancelled' in notice_data.document_type_description:
            notice_data.notice_type = 16
        notice_data.related_tender_id = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
        
        try:
            notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
            notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
        except Exception as e:
            logging.info("Exception in local_title: {}".format(type(e).__name__))
            pass
    
    if url != urls[3]:
        try:
            notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
            notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
        except Exception as e:
            logging.info("Exception in local_title: {}".format(type(e).__name__))
            pass

    
        try:    
            notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        except:
            pass


    if notice_data.notice_type != 7 :
        try:    
            notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
            notice_deadline = re.findall('\d{4}-\d+-\d+ \d+:\d+ [apAP][mM]',notice_deadline)[0]
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%Y-%m-%d %I:%M %p').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.notice_deadline)
        except Exception as e:
            logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
            pass
    
    try:    
        try:
            publish_date = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
            publish_date = re.findall('\d{4}-\d+-\d+',publish_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date,'%Y-%m-%d').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.publish_date)
        except:
            publish_date = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
            publish_date = re.findall('\d{4}-\d+-\d+ \d+:\d+ [apAP][mM]',publish_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date,'%Y-%m-%d %I:%M %p').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
    
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(3) > a").get_attribute("href")
        fn.load_page(page_details,notice_data.notice_url,80)
    except:
        try:
            notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(2) > a").get_attribute("href")
            fn.load_page(page_details,notice_data.notice_url,80)
            logging.info(notice_data.notice_url)
        except Exception as e:
            logging.info("Exception in notice_url: {}".format(type(e).__name__))
            notice_data.notice_url = url
            
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#main > div').get_attribute("outerHTML")
        notice_data.notice_text += tender_html_element.get_attribute("outerHTML")
    except:
        notice_data.notice_text = tender_html_element.get_attribute("outerHTML")
        
    try:
        notice_text = page_details.find_element(By.CSS_SELECTOR, '#main > div').text
    except:
        pass
    
    try: 
        customer_details_data = customer_details()
        customer_details_data.org_name = notice_text.split("Issuing Department:")[1].split("\n")[0]
        customer_details_data.org_country = 'ZA'
        customer_details_data.org_language = 'EN'

        try: 
            contact_person1 = notice_text.split('Contact Person [Supply Chain]:')[1].split("\n")[0]
            contact_person2 = notice_text.split('Contact Person [Technical]:')[1].split("\n")[0]
            customer_details_data.contact_person = contact_person1+ ',' +contact_person2
        except:
            pass
        
        try:
            org_phone1 = notice_text.split('Contact Number:')[1].split("\n")[0]
            org_phone2 = notice_text.split("Contact Person [Technical]:")[1].split('Contact Number:')[1].split("\n")[0]
            customer_details_data.org_phone = org_phone1+','+org_phone2
        except:
            pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
        
    try:
        for single_record in page_details.find_elements(By.XPATH, '//*[contains(text(),"Contact Person [Technical]:")]//following::a'):
            if 'Download Tender Document' in single_record.text:
                attachments_data = attachments()
                
                attachments_data.file_name ='Tender documents'

                attachments_data.external_url = single_record.get_attribute("href")
                
                try:
                    attachments_data.file_type = attachments_data.external_url.split(".")[-1]
                except Exception as e:
                    logging.info("Exception in file_type: {}".format(type(e).__name__))
                    pass
                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    if url != urls[3]:
        try:
            for single_record in page_details.find_elements(By.XPATH, '//*[contains(text(),"Contact Person [Technical]:")]//following::a'):
                if 'Download Tender Document' in single_record.text:
                    attachments_data = attachments()

                    attachments_data.file_name ='Tender documents'

                    attachments_data.external_url = single_record.get_attribute("href")

                    try:
                        attachments_data.file_type = attachments_data.external_url.split(".")[-1]
                    except Exception as e:
                        logging.info("Exception in file_type: {}".format(type(e).__name__))
                        pass
                    attachments_data.attachments_cleanup()
                    notice_data.attachments.append(attachments_data)
        except Exception as e:
            logging.info("Exception in attachments: {}".format(type(e).__name__)) 
            pass

    if url == urls[3]:
        
        try: 
            customer_details_data = customer_details()
            customer_details_data.org_name = 'ERWAT'
            customer_details_data.org_country = 'ZA'
            customer_details_data.org_language = 'EN'
            customer_details_data.org_parent_id = '7536917'

            customer_details_data.org_address = 'Hartebeestfontein Office Park,R25 (Bronkhorstspruit/Bapsfontein Road),Kempton Park'
         
            customer_details_data.org_phone = '+27 11 929 7000'
             

            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
        except Exception as e:
            logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
            pass
    
        try:
            attachments_data = attachments()

            attachments_data.file_name ='Submitted Bids'

            attachments_data.external_url = page_details.find_element(By.XPATH, '//*[contains(text(),"Submitted Bids:")]//following::a[1]').get_attribute("href")

            try:
                attachments_data.file_type = attachments_data.external_url.split(".")[-1]
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
        except Exception as e:
            logging.info("Exception in attachments: {}".format(type(e).__name__)) 
            pass
        
        try:
            attachments_data = attachments()

            attachments_data.file_name ='Submitted Bids'

            attachments_data.external_url = page_details.find_element(By.XPATH, '//*[contains(text(),"Awarded Bidders:")]//following::a[1]').get_attribute("href")

            try:
                attachments_data.file_type = attachments_data.external_url.split(".")[-1]
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
        except Exception as e:
            logging.info("Exception in attachments: {}".format(type(e).__name__)) 
            pass
        
        try:     

            lot_details_data = lot_details()
            lot_details_data.lot_number = 1

            lot_details_data.lot_title = notice_data.local_title
            notice_data.is_lot_default = True
            try:
                award_details_data = award_details()  
                award_details_data.bidder_name = notice_text.split('Name Of Awarded Bidder:')[1].split("\n")[0]
                try:  
                    grossawardvaluelc = notice_text.split('Bid Price:')[1].split("\n")[0]
                    grossawardvaluelc = re.sub("[^\d\.\,]","",grossawardvaluelc)
                    award_details_data.grossawardvaluelc =float(grossawardvaluelc.replace(',','').strip())
                except:
                    pass
                
                try: 
                    award_details_data.contract_duration = notice_text.split('Contract Duration:')[1].split("\n")[0]
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


    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_url) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title)
    logging.info(notice_data.identifier)
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
    urls = ["https://erwat.co.za/supply-chain-management-scm/tenders/","https://erwat.co.za/supply-chain-management-scm/quotations-r30000/",'https://erwat.co.za/supply-chain-management-scm/fpq-r30000-r200000/',"https://erwat.co.za/supply-chain-management-scm/bid-status/"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(1,4):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[1]/div[2]/main/div/section/div/div/div/div/div/div/div[2]/div/div/table/tbody/tr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/div[2]/main/div/section/div/div/div/div/div/div/div[2]/div/div/table/tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/div[2]/main/div/section/div/div/div/div/div/div/div[2]/div/div/table/tbody/tr')))[records]
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
                next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,'Next')))
                page_main.execute_script("arguments[0].click();",next_page)
                logging.info("Next page")
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/div[1]/div[2]/main/div/section/div/div/div/div/div/div/div[2]/div/div/table/tbody/tr'),page_check))
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
