
# *after every click there one pop-up opening you have to close that pop-up.

# *take data also from follwing tabs:
# 1)TOR, Announcement and Medium Cost >> Enquiry Method
# 2)TOR, Announcement and Medium Cost >> Special Method
# 3)TOR, Announcement and Medium Cost >> PriceAgreeing Method
# 4)TOR, Announcement and Medium Cost >> Selection Method
# 5)TOR, Announcement and Medium Cost >> Specific Method



from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "th_egat4_spn"
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
SCRIPT_NAME = "th_egat4_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'th_egat4_spn'
    
    notice_data.main_language = 'TH'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'TH'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'THB'

    notice_data.procurement_method = 2

    notice_data.notice_type = 4
    

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(3)").text
        publish_date = re.findall('\d{4}-\d+-\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%Y-%m-%d').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text
        notice_deadline = re.findall('\d{4}-\d+-\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%Y-%m-%d').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a').get_attribute("href") 
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url

    try:
        notice_data.notice_no = notice_data.notice_url[-4:]
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
        
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.twelve.wide.column').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    try:
        local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Description")]//following::td[1]').text 
        if len(local_description)>5:
            notice_data.local_description = local_description            
            notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)  
            
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    try:
        eligibility = page_details.find_element(By.XPATH, '//*[contains(text(),"Eligibility of bidder")]//following::td[1]').text  
        if len(eligibility)>5:
            notice_data.eligibility = eligibility
    except Exception as e:
        logging.info("Exception in eligibility: {}".format(type(e).__name__))
        pass

    try:
        contract_duration = page_details.find_element(By.XPATH, '//*[contains(text(),"Completion Date of Work / Delivery Time of Goods, Parts and Equipment")]//following::td[1]').text 
        if len(contract_duration)>5:
            notice_data.contract_duration = contract_duration
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass
    

    try:
        est_amount = page_details.find_element(By.XPATH, '//*[contains(text(),"Medium Cost / Starting Price")]//following::td[1]').text 
        if len(est_amount)>5:
            est_amount = est_amount.split('THB')[1].split('.-')[0].split('(')[0].strip()
            est_amount = float(est_amount.replace(',',''))
            notice_data.est_amount = est_amount
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass

    try:
        notice_data.grossbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
    
    try:              
        customer_details_data = customer_details()

        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
        customer_details_data.org_country = 'TH'
        customer_details_data.org_language = 'TH'

        try:
            customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Person Incharge")]//following::td[1]').text 
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass

        try:
            customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Email")]//following::td[1]').text  
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try:              
        attachments_data = attachments()

        try:
            attachments_data.file_name = page_details.find_element(By.XPATH, '//*[contains(text(),"File Name")]//following::td[1]').text  
        except Exception as e:
            logging.info("Exception in file_name: {}".format(type(e).__name__))
            pass

        attachments_data.external_url = page_details.find_element(By.XPATH, '//*[contains(text(),"File Name")]//following::a[1]').get_attribute('href') 

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

arguments= ['−−incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
options = webdriver.ChromeOptions()
for argument in arguments:
    options.add_argument(argument)
page_main = webdriver.Chrome(options=options)
page_details = webdriver.Chrome(options=options)


try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www4.egat.co.th/fprocurement/biddingeng/torSealedBids","https://www4.egat.co.th/fprocurement/biddingeng/torEnquiryMethod",
           "https://www4.egat.co.th/fprocurement/biddingeng/torSpecialMethod","https://www4.egat.co.th/fprocurement/biddingeng/torPriceAgreeingMethod",
           "https://www4.egat.co.th/fprocurement/biddingeng/torSelection","https://www4.egat.co.th/fprocurement/biddingeng/torSpecific"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        try:
            add_click = page_main.find_element(By.XPATH,"//button[contains(@class,'qrcodeModalButtonClose')]").click()
            time.sleep(3)
        except:
            pass
        try:
            for page_no in range(2,7):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[2]/div/div[2]/table/tbody/tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[2]/div/div[2]/table/tbody/tr')))
                length = len(rows)
                try:
                    for records in range(0,length):
                        tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[2]/div/div[2]/table/tbody/tr')))[records]
                        extract_and_save_notice(tender_html_element)
                        if notice_count >= MAX_NOTICES:
                            break
    
                        if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                            break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
                    
                except:
                    pass
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/div[2]/div/div[2]/table/tbody/tr'),page_check))
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
    page_details.quit() 
    
    output_json_file.copyFinalJSONToServer(output_json_folder) 
