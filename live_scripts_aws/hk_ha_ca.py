from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "hk_ha_ca"
log_config.log(SCRIPT_NAME)
import re
import jsons
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn
import gec_common.Doc_Download

#Note:Open the site then click on "CONTRACT AWARD NOTICE" and grab the data

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "hk_ha_ca"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'hk_ha_ca'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'HK'
    notice_data.performance_country.append(performance_country_data)

    notice_data.main_language = 'EN'
    notice_data.notice_type = 7
    
    # Onsite Field -Tender Reference
    # Onsite Comment -None

    try:
        notice_data.related_tender_id = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').get_attribute('innerHTML')
    except Exception as e:
        logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -Note:Replace following kegword("Open=1","Limited(Extreme urgency requirement to meet operational need)=0")
    
    procurement_method = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
    if 'Open' in procurement_method:
        notice_data.procurement_method = 1
    elif "Limited(Extreme urgency requirement to meet operational need)" in procurement_method:
        notice_data.procurement_method = 0
    else:
        notice_data.procurement_method = 2
    
#     # Onsite Field -Subject
#     # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
#     # Onsite Field -Contract Period
#     # Onsite Comment -None

    try:
        notice_data.contract_duration = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(7)').text
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass
    
#     # Onsite Field -Estimated Contract Amount
#     # Onsite Comment -None  

    try:
        est_amount = tender_html_element.find_element(By.CSS_SELECTOR, 'td.xl1152003').text
        currency = re.findall('^\w{3}\D|^\w{2}\D',est_amount)[0]
        notice_data.currency = currency.replace('$','D')
        if 'Mn' in est_amount:
            only_est_amount = re.sub("[^\d\.\,]","",est_amount)
            notice_data.est_amount = float(only_est_amount) * 1000000
            notice_data.grossbudgetlc = notice_data.est_amount
        else:
            only_est_amount = re.sub("[^\d\.\,]","",est_amount)
            notice_data.est_amount =float(only_est_amount)
            notice_data.grossbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass

    notice_data.notice_url = url


    notice_data.notice_text += tender_html_element.get_attribute('outerHTML')


    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'HK'
        customer_details_data.org_language = 'EN'
    # Onsite Field -Hospital
    # Onsite Comment -None

        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try:              
        lot_details_data = lot_details()
        lot_details_data.lot_number = 1
    # Onsite Field -Subject
    # Onsite Comment -None

        lot_details_data.lot_title = notice_data.local_title
        notice_data.is_lot_default = True
        lot_details_data.lot_title_english = notice_data.notice_title


        try:
            award_details_data = award_details()

            # Onsite Field -Contractor(s) & Address(es)
            # Onsite Comment -Note:Splite first line only

            award_details_data.bidder_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text.split('\n')[0].strip()
            # Onsite Field -Contractor(s) & Address(es)
            # Onsite Comment -
            try:
                award_details_data.address = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text.split('\n')[1].strip()
            except Exception as e:
                logging.info("Exception in address: {}".format(type(e).__name__)) 
                pass

            # Onsite Field -Date of Award
            # Onsite Comment -None
            
            try:
                award_date = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(9)').text
                award_date = re.findall('\d+-\w+-\d{4}',award_date)[0]
                award_details_data.award_date = datetime.strptime(award_date,'%d-%B-%Y').strftime('%Y/%m/%d')
                notice_data.publish_date = award_details_data.award_date
            except Exception as e:
                logging.info("Exception in award_date: {}".format(type(e).__name__)) 
                pass

            award_details_data.award_details_cleanup()
            lot_details_data.award_details.append(award_details_data)
        except Exception as e:
            logging.info("Exception in award_details: {}".format(type(e).__name__))
            pass
        
        if lot_details_data.award_details !=[]:
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
    if notice_data.publish_date is None:
        notice_data.publish_date = threshold
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    if notice_data.related_tender_id == 'Tender Reference' or notice_data.related_tender_id == '':
        return  


    notice_data.identifier = str(notice_data.script_name) + str(notice_data.related_tender_id) +  str(notice_data.notice_type) +  str(notice_data.local_title) 
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

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.ha.org.hk/visitor/ha_visitor_index.asp?Content_ID=2001&Lang=ENG&Dimension=100&Ver=HTML"]
    
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            iframe = page_main.find_element(By.XPATH,'//*[@id="childframe"]')
            page_main.switch_to.frame(iframe)
        except:
            pass
        
        clk=page_main.find_element(By.XPATH,'//*[@id="contentarea"]/table/tbody/tr[1]/td/p[3]/table/tbody/tr[6]/td[3]/a').click()
        page_main.switch_to.window(page_main.window_handles[1])

        try:
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'table > tbody > tr:nth-child(n)')))
            length = len(rows)
            
            for records in range(8,length - 12):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'table > tbody > tr:nth-child(n)')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break  
                    
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
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
    output_json_file.copyFinalJSONToServer(output_json_folder)
