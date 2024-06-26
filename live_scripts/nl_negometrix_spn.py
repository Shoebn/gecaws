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
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "nl_negometrix_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

#after opening the url unselect the "Country: United States" clicking on "span.tr-filter-clear" this selector.
    

    notice_data.script_name = 'nl_negometrix_spn'
    
    notice_data.main_language = 'NL'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'NL'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'EUR'
    
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 4
    
    # Onsite Field -No.
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(6)').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Submission Deadline
    # Onsite Comment -1.if notice_deadline is not present then take thrshold.

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(7)> span").text
        notice_deadline = re.findall('\d+ \w+ \d{4} \d+:\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d %b %Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url

    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#primary > div').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    # Onsite Field -None
    # Onsite Comment -1.split publish_date. eg., here "10 Aug 2023 10:00 — 7 Sep 2023 10:00" take "10 Aug 2023 10:00" in publish_date. 		2.reference url "https://platform.negometrix.com/PublicBuyerProfile/PublishedTenderInformation.aspx?isPublicProfile=false&tenderId=224233&tab=1&page=1&searchParam=&sortParam=Id&sortDirection=False" in this url this date take in publish_date.

    try:
        publish_date = page_details.find_element(By.XPATH, "//*[contains(text(),'Publicatiedatum:')]//following::dd[1]").text
        publish_date = re.findall('\d+ \w+ \d{4} \d+:\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d %b %Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except:
        try:
            publish_date = page_details.find_element(By.XPATH, "//*[contains(text(),'Offertefase:')]//following::dd[1]").text.split("-")[0]
            publish_date = re.findall('\d+ \w+ \d{4} \d+:\d+',publish_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date,'%d %b %Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.publish_date)
        except Exception as e:
            logging.info("Exception in publish_date: {}".format(type(e).__name__))
            pass
        
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    try:
        notice_summary_english = page_details.find_element(By.XPATH, "//*[contains(text(),' Description:')]//following::dd[1]").text
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_summary_english)
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass

    try:
        customer_details_data = customer_details()
        customer_details_data.org_country = 'NL'
        customer_details_data.org_language = 'NL'
            # Onsite Field -Agency
            # Onsite Comment -None

        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
        try:
            customer_details_data.org_website = page_details.find_element(By.CSS_SELECTOR, 'dt:nth-child(1) > a').text
        except Exception as e:
            logging.info("Exception in org_website: {}".format(type(e).__name__))
            pass

        try:
            contact_person = page_details.find_element(By.CSS_SELECTOR, 'div.personal_info > p.name').text
            customer_details_data.contact_person = GoogleTranslator(source='auto', target='en').translate(contact_person)
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass

        try:
            customer_details_data.org_phone = page_details.find_element(By.CSS_SELECTOR, 'div.personal_info > p:nth-child(3)').text
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass

        try:
            customer_details_data.org_email = page_details.find_element(By.CSS_SELECTOR, 'div.personal_info > p:nth-child(4)').text
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#ctl00_ctl00_mC_mC_descriptionAttachDocumentsReadtblAttachedDocuments > tbody > tr'):
            attachments_data = attachments()
            attachments_data.file_name = single_record.text.split(".")[0]
            attachments_data.file_description = attachments_data.file_name
            attachments_data.file_type = single_record.text.split(".")[1].split(" ")[0]
            file_size1 = single_record.text.split(".")[1].split('\n')[0].split(" ")[1]
            file_size2 = single_record.text.split(".")[1].split(' ')[2].split('\n')[0]
            attachments_data.file_size = file_size1 + file_size2
            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2) p > a').get_attribute('href')
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass

    if notice_data.publish_date is None and notice_data.notice_deadline is None:
        return
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_details = fn.init_chrome_driver(arguments) 
page_main = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://platform.negometrix.com/?page=1&tab=1&searchParam=&sortParam=Id&sortDirection=False"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            clk = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="ctl00_ctl00_mC_mC_tltPublishedTenders_publishedTendersFilters_lvAppliedFilters_ctrl0_btnClear"]')))
            page_main.execute_script("arguments[0].click();",clk)
        except:
            pass
        time.sleep(10)

        try:
            for page_no in range(1,25):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'table.mytenders_list > tbody > tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'table.mytenders_list > tbody > tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'table.mytenders_list > tbody > tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
            
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="ctl00_ctl00_mC_mC_tltPublishedTenders_btnNext"]')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'table.mytenders_list > tbody > tr'),page_check))
                except Exception as e:
                    logging.info("Exception in next_page: {}".format(type(e).__name__))
                    logging.info("No next page")
                    break
         except:
            logging.info("No new record")
            break
             
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit() 
    
    output_json_file.copyFinalJSONToServer(output_json_folder)
