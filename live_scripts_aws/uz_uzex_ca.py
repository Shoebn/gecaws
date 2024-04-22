from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "uz_uzex_ca"
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
import gec_common.Doc_Download_VPN
from selenium.webdriver.support.ui import Select

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "uz_uzex_ca"
Doc_Download = gec_common.Doc_Download_VPN.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    

    notice_data.script_name = 'uz_uzex_ca'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'UZ'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'UZS'
    notice_data.main_language = 'RU'
    notice_data.procurement_method = 2
    notice_data.notice_type = 7
    
    notice_data.notice_url = url
    notice_data.document_type_description = "Состоявшиеся"
    
    try:  
        publish_date =  tender_html_element.find_element(By.CSS_SELECTOR,'div:nth-child(1) > div.mt-2').text
        publish_date = re.findall('\d+.\d+.\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date, '%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__)) 
        pass
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(3) > div > p').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__)) 
        pass
 
    try:
        notice_data.related_tender_id = tender_html_element.find_element(By.CSS_SELECTOR, 'a.lotNumber').text
    except Exception as e:
        logging.info("Exception in related_tender_id: {}".format(type(e).__name__)) 
        pass
        
    try:              
        lot_details_data = lot_details()
        lot_details_data.lot_title = notice_data.local_title
        notice_data.is_lot_default = True
        lot_details_data.lot_title_english = notice_data.notice_title
        lot_details_data.lot_number = 1
        try:
            award_details_data = award_details()
            award_details_data.bidder_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(5) > p').text.split(",")[0]
            try:  
                award_date = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(1) > div.mt-2').text
                award_date = re.findall('\d+.\d+.\d{4}',award_date)[0]
                award_details_data.award_date = datetime.strptime(award_date,'%d.%m.%Y').strftime('%Y/%m/%d')
            except Exception as e:
                logging.info("Exception in award_date: {}".format(type(e).__name__)) 
                pass
            
            try:
                grossawardvaluelc = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(6) > div:nth-child(1) > p').text
                grossawardvaluelc = re.sub("[^\d\.\,]","",grossawardvaluelc)
                award_details_data.grossawardvaluelc =float(grossawardvaluelc.replace(',','').strip())
            except Exception as e:
                logging.info("Exception in grossawardvaluelc: {}".format(type(e).__name__)) 
                pass
            award_details_data.award_details_cleanup()
            lot_details_data.award_details.append(award_details_data)
        except:
            pass

        lot_details_data.lot_details_cleanup()
        notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
    try:
        est_amount1 = tender_html_element.find_element(By.CSS_SELECTOR,' div:nth-child(6) > div.mt-2 > p').text
        est_amount = re.sub("[^\d\.\,]","",est_amount1)
        notice_data.est_amount = float(est_amount.replace(',','').strip())
        notice_data.grossbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__)) 
        pass

    try:               
        customer_details_data = customer_details()
        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(4) > p').text
        customer_details_data.org_country = 'UZ'
        customer_details_data.org_language = 'RU'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__)) 
        pass
    
    try:
        clk = tender_html_element.click()
        time.sleep(4)
    except:
        pass
    
    try:
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, 'a.btn.btn-success.text-white'):
            attachments_data = attachments()
            attachments_data.file_name = 'Основной протокол'
            external_url = single_record.click()
            file_dwn = Doc_Download.file_download()
            time.sleep(3)
            attachments_data.external_url = str(file_dwn[0])
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass   

    try:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, 'div.panel-collapse.collapse.in.show > div').get_attribute('outerHTML')
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__)) 
        pass

    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.notice_deadline) + str(notice_data.local_title)
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
page_main = Doc_Download.page_details
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://etender.uzex.uz/deals-list"]
    for url in urls:
        fn.load_page(page_main, url, 100)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(1,20):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'body > app-root > main > app-deals-list > div > div > div > div > div.listing__content > div > div > accordion > accordion-group'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'body > app-root > main > app-deals-list > div > div > div > div > div.listing__content > div > div > accordion > accordion-group')))
                length = len(rows)                                                                              
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'body > app-root > main > app-deals-list > div > div > div > div > div.listing__content > div > div > accordion > accordion-group')))[records]
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
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'/html/body/app-root/main/app-deals-list/div/div/div/div/div[1]/div[2]/div[2]/div[2]/button')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    page_check2 = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'body > app-root > main > app-deals-list > div > div > div > div > div.listing__content > div > div > accordion > accordion-group'))).text
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'body > app-root > main > app-deals-list > div > div > div > div > div.listing__content > div > div > accordion > accordion-group'),page_check))
                except Exception as e:
                    logging.info("Exception in next_page: {}".format(type(e).__name__))
                    logging.info("No next page")
                    break
        except:
            logging.info("No new record")
            pass

    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)
