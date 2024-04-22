from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "om_etendering_ca"
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
SCRIPT_NAME = "om_etendering_ca"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'om_etendering_ca'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'OM'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'OMR'
    notice_data.main_language = 'AR'
    notice_data.notice_type = 7
    
    try:
        notice_data.procurement_method = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(6)').text
        if 'محلية' in notice_data.procurement_method:
            notice_data.procurement_method = 0
        elif 'عالمية' in notice_data.procurement_method:
            notice_data.procurement_method = 1
        else:
            notice_data.procurement_method = 2
    except:
        pass
    
    try:
        notice_data.related_tender_id = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(7)").text
        notice_data.publish_date = datetime.strptime(publish_date,'%d-%m-%Y %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    try:
        notice_data.contract_type_actual = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
        notice_contract_type  = GoogleTranslator(source='auto', target='en').translate(notice_data.contract_type_actual)
        if 'Business quality' in notice_contract_type or 'Supplies and services - old' in notice_contract_type or 'Urban contracting and maintenance' in notice_contract_type or 'Information technology services' in notice_contract_type or 'Contracting - old' in notice_contract_type or 'Electromechanical, communications and maintenance contracting' in notice_contract_type or 'Ports, roads, bridges, railways, dams and maintenance contracting' in notice_contract_type or 'Pipeline networks and well drilling contracting' in notice_contract_type:
            notice_data.notice_contract_type = 'Service'
        elif 'Consulting work - old' in notice_contract_type or 'Training Works - Old' in notice_contract_type:
            notice_data.notice_contract_type = 'Works'
        elif 'Supplies' in notice_contract_type:
            notice_data.notice_contract_type = 'Supply'
        elif 'Consulting offices' in notice_contract_type:
            notice_data.notice_contract_type = 'Consultancy'
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    try:              
        lot_details_data = lot_details()
        lot_details_data.lot_number=1
        lot_details_data.lot_title = notice_data.local_title
        notice_data.is_lot_default = True
        try:
            award_details_data = award_details()
            award_details_data.award_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(7)").text
            award_details_data.award_date = re.findall('\d+-\d+-\d{4}',award_details_data.award_date)[0]
            award_details_data.award_date = datetime.strptime(award_details_data.award_date,'%d-%m-%Y').strftime('%Y/%m/%d')

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
        notice_data.notice_no = tender_html_element.find_element(By.XPATH,'(//*[@class="table_icon"]//following::a[starts-with(@href, "#banner")])['+str(num)+']').get_attribute('onclick').split("('")[1].split("')")[0]
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
        customer_details_data.org_country = 'OM'
        customer_details_data.org_language = 'AR'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try:
        notice_url = WebDriverWait(tender_html_element, 100).until(EC.element_to_be_clickable((By.XPATH,'(//*[@class="table_icon"]//following::a[starts-with(@href, "#banner")])['+str(num)+']')))
        page_main.execute_script("arguments[0].click();",notice_url)
        time.sleep(5)
        page_main.switch_to.window(page_main.window_handles[1])
        time.sleep(5)
        notice_url1 = page_main.current_url
        notice_data.notice_url = notice_url1
        logging.info(notice_data.notice_url)
        try:
            notice_text = page_main.find_element(By.XPATH,'/html/body/form/div/div[3]/table').get_attribute('outerHTML')
        except:
            pass
        page_main.close()
        page_main.switch_to.window(page_main.window_handles[0])
        time.sleep(5)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
        notice_data.notice_text += notice_text
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.notice_deadline) + str(notice_data.local_title)
    logging.info(notice_data.identifier)
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
    urls = ["https://etendering.tenderboard.gov.om/product/publicDash"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url) 
        
        close_popup = WebDriverWait(page_main, 100).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'a.close.agree')))
        page_main.execute_script("arguments[0].click();",close_popup)
        time.sleep(5)
        
        predicate_clk = page_main.find_element(By.XPATH,'/html/body/form/div[6]/div/div[2]/div/div[3]/div/div')
        page_main.execute_script("arguments[0].click();",predicate_clk)
        time.sleep(10)

        try:
            clk = page_main.find_element(By.XPATH,'//*[@id="header"]/div[5]/div/div[1]/div[2]/div/table/tbody/tr[1]/td/a[3]/b').click()
            time.sleep(5)
        except:
            pass
        try:
            for page_no in range(1,5): #5
                rows = WebDriverWait(page_main, 100).until(EC.presence_of_all_elements_located((By.XPATH, '//tr[@class="even gradeA"]|//tr[@class="odd gradeA"]')))
                length = len(rows)
                num = 1
                for records in range(3,length-2):
                    tender_html_element = WebDriverWait(page_main, 100).until(EC.presence_of_all_elements_located((By.XPATH, '//tr[@class="even gradeA"]|//tr[@class="odd gradeA"]')))[records]
                    extract_and_save_notice(tender_html_element)
                    num+=1
                    
                    if notice_count >= MAX_NOTICES:
                        break

                try:   
                    next_page = WebDriverWait(page_main, 100).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"a.pageLinks.Pagination_button1")))
                    page_main.execute_script("arguments[0].click();",next_page)
                    time.sleep(10)
                    logging.info("Next page")
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
    output_json_file.copyFinalJSONToServer(output_json_folder)
