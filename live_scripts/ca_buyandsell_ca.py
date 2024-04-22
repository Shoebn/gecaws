from gec_common.gecclass import *
import logging
import re
import jsons
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
import gec_common.OutputJSON
from gec_common import functions as fn
from selenium.webdriver.chrome.options import Options
from deep_translator import GoogleTranslator

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "ca_buyandsell_ca"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'ca_buyandsell_ca'
    notice_data.main_language = 'FR'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'CA'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'CAD'
    notice_data.procurement_method = 2
    notice_data.document_type_description = 'Tender notice'
    notice_data.notice_type = 7
    
    try:
        notice_type = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
        notice_type_date = re.findall('\d{4}/\d+/\d+',notice_type)[0]
        if notice_type_date!= '':
            notice_data.notice_type = 16
        else:
            notice_data.notice_type = 7
    except Exception as e:
        logging.info("Exception in notice_type: {}".format(type(e).__name__))
        pass

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
        publish_date = re.findall('\d{4}/\d+/\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%Y/%m/%d').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:
        est_amount = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5) > span:nth-child(2)').text
        est_amount = re.sub("[^\d\.\,]", "", est_amount)
        notice_data.est_amount = float(est_amount)
        notice_data.netbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    bidder_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1) > a').text

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url

    try:
        notice_data.local_title = page_details.find_element(By.XPATH, '//*[@id="block-eps-wxt-bootstrap-views-block-tender-details-block-1"]/div/div/div/div/article/div[1]/div[1]/h1/span').text
        notice_data.notice_title = GoogleTranslator(source='es', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass


    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.dialog-off-canvas-main-canvas > main').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass

    try:
        notice_data.contract_duration = page_details.find_element(By.XPATH, '//*[contains(text(),"Durée du contrat")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass


    try:
        codes = page_details.find_element(By.CSS_SELECTOR, "#preview-unspsc > div > ul").text
        cpv_at_source_regex = re.compile(r'\d{8}')
        cpv_list = cpv_at_source_regex.findall(codes)
        for code in cpv_list:
            cpv_codes_list = fn.CPV_mapping("assets/ca_buyandsell_ca_cpvmap.csv",code)
            for each_cpv in cpv_codes_list:
                cpvs_data = cpvs()
                cpvs_data.cpv_code = each_cpv
                cpvs_data.cpvs_cleanup()
                notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpv_code: {}".format(type(e).__name__))
        pass

    try:
        notice_data.class_at_source = 'UNSPSC'
        class_codes_at_source = ''
        codes_at_source = page_details.find_element(By.CSS_SELECTOR, '#preview-unspsc > div > ul').text
        cpv_regex = re.compile(r'\d{8}')
        code_list = cpv_regex.findall(codes_at_source)
        for codes in code_list:
            class_codes_at_source += codes
            class_codes_at_source += ','
        notice_data.class_codes_at_source = class_codes_at_source.rstrip(',')
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass

    try:
        class_title_at_source = '' 
        single_record = page_details.find_element(By.CSS_SELECTOR, '#preview-unspsc > div > ul').text.split('\n')
        for record in single_record:
            titles_at_source = re.split("\d{8}.", record)[1]
            class_title_at_source += titles_at_source
            class_title_at_source +=','
        notice_data.class_title_at_source = class_title_at_source.rstrip(',') 
    except Exception as e:
        logging.info("Exception in class_title_at_source: {}".format(type(e).__name__)) 
        pass

    try:              
        lot_details_data = lot_details()
        lot_details_data.lot_number=1
        lot_details_data.lot_title = notice_data.notice_title
        
        award_details_data = award_details()
        award_details_data.bidder_name=bidder_name
        try: 
            award_details_data.address = page_details.find_element(By.XPATH, '//*[contains(text(),"Adresse de l’entreprise")]//following::dd[1]').text
        except Exception as e:
            logging.info("Exception in address: {}".format(type(e).__name__)) 
            pass
        
        award_details_data.award_details_cleanup()
        lot_details_data.award_details.append(award_details_data)


        lot_details_data.lot_details_cleanup()
        notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = org_name
        try:
            notice_tab2_click = page_details.find_element(By.CSS_SELECTOR, '#edit-group-buyer-information-id').click()                     
            time.sleep(3)
        except Exception as e:
            logging.info("Exception in notice_tab2_click: {}".format(type(e).__name__))
            pass

        try:
            customer_details_data.org_address = page_details.find_element(By.XPATH, '(//*[contains(text(),"Adresse ")]//following::dd[1])[2]').text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass
            
        try:
            customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Autorité contractante")]//following::dd[1]').text
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass
            
        try:
            customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Adresse courriel ")]//following::dd[1]').text
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass

        customer_details_data.org_country = 'CA'
        customer_details_data.org_language = 'FR'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try:
        notice_data.notice_text += page_details.find_element(By.XPATH, '/html/body/div[1]/main/div[1]/div[2]/section').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass

  
    try:
        notice_tab3_click = page_details.find_element(By.CSS_SELECTOR, '#edit-group-related-notices-id').click()                     
        time.sleep(3)
    except Exception as e:
        logging.info("Exception in notice_tab3_click: {}".format(type(e).__name__))
        pass

    try:
        button = page_details.find_element(By.CSS_SELECTOR,'#ui-id-1 > a').click()
        time.sleep(2)
    except:
        pass

    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#ui-id-2 > div > div > div > div > table').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass

    try:
        button = page_details.find_element(By.CSS_SELECTOR,'#ui-id-3 > a').click()
        time.sleep(2)
    except:
        pass

    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#ui-id-4').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) + str(notice_data.publish_date) +  str(notice_data.notice_url) 
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
    urls = ['https://achatscanada.canada.ca/fr/occasions-de-marche'] 
    for url in urls:
        fn.load_page_expect_xpath(page_main, url, '//*[@id="ui-id-4"]/div/div[1]', 100)
        logging.info('----------------------------------')
        logging.info(url)
        
        button = page_main.find_element(By.CSS_SELECTOR,'#ui-id-4 > div > div.h4.tab-title').click()
        time.sleep(5)

        select_btn = Select(page_main.find_element(By.XPATH,'/html/body/div[1]/main/div[1]/div[2]/section/div/div[3]/div/div[1]/div/div/div[2]/div[3]/div/div/form/div/div[1]/div/select'))
        select_btn.select_by_index(2)
        time.sleep(5)
        
        try:
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#c > div > div > div.view-content > div > div > table > tbody > tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#c > div > div > div.view-content > div > div > table > tbody > tr')))[records]
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
    page_details.quit() 
    # page_details1.quit()
    # page_details2.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)