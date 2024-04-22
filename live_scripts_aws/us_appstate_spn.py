from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "us_appstate_spn"
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
from selenium.webdriver.chrome.options import Options


NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "us_appstate_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"

# -----------------------------------------------------------------------------------------------------------------------------------------------------------------

#       Go to URL : "https://appstate.az.gov/page.aspx/en/rfp/request_browse_public"  

#       in the "Status" tab select "Open for Bidding" option and click on "Search"

#       click on "Begin (UTC-7)" twice for latest details

# -----------------------------------------------------------------------------------------------------------------------------------------------------------------
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'us_appstate_spn'
    
    notice_data.main_language = 'EN'
   
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'US'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'USD'
    
    notice_data.notice_type = 4
    
    notice_data.procurement_method = 2
    
    # Onsite Field -Code
    # Onsite Comment -split the data below "Code" field

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Label
    # Onsite Comment -split the data below "Label "

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -"Commodity"
    # Onsite Comment -split the data below "Commodity"

    try:
        notice_data.category = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
        
        category = fn.CPV_mapping("assets/us_appstate_spn_UNSPSC_code.csv",notice_data.category)
        for cpv_code in category:
            cpvs_data = cpvs()
            cpvs_data.cpv_code = cpv_code
            
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except:
        pass

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(11)").text
        notice_data.publish_date = datetime.strptime(publish_date,'%m/%d/%Y %I:%M:%S %p').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
#     # Onsite Field -End (UTC-7)
    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(12)").text
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%m/%d/%Y %I:%M:%S %p').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    except:
        pass
    
    org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(6)').text

    try:
        page_details_click = WebDriverWait(tender_html_element, 90).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'td:nth-child(1) a')))
        page_main.execute_script("arguments[0].click();",page_details_click)
        time.sleep(5)
        notice_data.notice_url = page_main.current_url
        logging.info(notice_data.notice_url)
        
        try:
            cancel_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="content"]/div[1]/button')))
            page_main.execute_script("arguments[0].click();",cancel_click)
        except:
            pass
        
        i = 1
        while i < 10:
            fn.load_page(page_main,notice_data.notice_url,80)
            time.sleep(3)
            
            try:
                cancel_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="content"]/div[1]/button')))
                page_main.execute_script("arguments[0].click();",cancel_click)
            except:
                pass
                
            try:
                WebDriverWait(page_main, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#body_x > div:nth-child(2)')))
                break
            except:
                i += 1
        
            
        try:
            notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, 'div > div#content').get_attribute("outerHTML")                     
        except:
            pass
        
        # Onsite Field -Agency
        try:              
            customer_details_data = customer_details()
            customer_details_data.org_language = 'EN'
            customer_details_data.org_country = 'US'
            # Onsite Field -Agency

            customer_details_data.org_name = org_name
            
            # Onsite Field -Procurement Officer Email
            try:
                customer_details_data.org_email = page_main.find_element(By.CSS_SELECTOR, '#body_x_tabc_rfp_ext_prxrfp_ext_x_txtBpmBpmEmail_78E9FF04').get_attribute('value')
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass

            # Onsite Field -Procurement Officer Phone
            try:
                customer_details_data.org_phone = page_main.find_element(By.CSS_SELECTOR, '#body_x_tabc_rfp_ext_prxrfp_ext_x_txtBpmPmPhone_78E9FF04').get_attribute('value')
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass

            # Onsite Field -Procurement Officer
            try:
                customer_details_data.contact_person = page_main.find_element(By.CSS_SELECTOR, '#body_x_tabc_rfp_ext_prxrfp_ext_x_txtBpmPmName_78E9FF04').get_attribute('value')
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass

            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
        except Exception as e:
            logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
            pass
        
        try:
            notice_data.local_description = page_main.find_element(By.XPATH, '//*[contains(text(),"Summary")]//following::p[1]').text
            notice_data.notice_summary_english = notice_data.local_description
        except Exception as e:
            logging.info("Exception in local_description: {}".format(type(e).__name__))
            pass
        
         # Onsite Field -Solicitation Documents
        try:              
            for single_record in page_main.find_elements(By.CSS_SELECTOR, '#body_x_tabc_rfp_ext_prxrfp_ext_x_prxDoc_x_grid_grd > tbody > tr'):
                attachments_data = attachments()
                # Onsite Field -Title
                attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text

                # Onsite Field -Att.
                attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'td :nth-child(3) > div > a').get_attribute('href')
                
                try:
                    attachments_data.file_type = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').get_attribute('outerHTML').split('<span data-iv-role="label">')[1].split('</span>')[0].strip().split('.')[-1].strip()
                except Exception as e:
                    logging.info("Exception in file_type: {}".format(type(e).__name__))
                    pass

                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
        except Exception as e:
            logging.info("Exception in attachments: {}".format(type(e).__name__)) 
            pass
        try:
            clk=page_main.find_element(By.CSS_SELECTOR,'#body_x_tabc_rfp_ext_prxrfp_ext_x_btnHlRfp > span').click()
            time.sleep(5)
        except:
            pass
        
        try:        
            lot_number =1
            for single_record in page_main.find_elements(By.CSS_SELECTOR, 'table.iv-grid-table.iv-grid-view.ui.selectable.compact.table > tbody > tr ')[1:]:
                lot_details_data = lot_details()
                lot_details_data.lot_number = lot_number
            
           
                lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, ' td:nth-child(5) ').text
                
                try:
                    lot_details_data.lot_actual_number = single_record.find_element(By.CSS_SELECTOR, ' td:nth-child(3)').text
                except Exception as e:
                    logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                    pass
                
                try:
                    lot_quantity = single_record.find_element(By.CSS_SELECTOR, "td:nth-child(6)").text
                    lot_details_data.lot_quantity = float(lot_quantity)
                except Exception as e:
                    logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                    pass
                
                try:
                    lot_details_data.lot_quantity_uom = single_record.find_element(By.CSS_SELECTOR, "td:nth-child(7)").text
                except Exception as e:
                    logging.info("Exception in lot_quantity_uom: {}".format(type(e).__name__))
                    pass

                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
                lot_number +=1
        except Exception as e:
            logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
            pass
        
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
        
    back_page = WebDriverWait(page_main, 80).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="proxyActionBar_x_btnReturn"]')))
    page_main.execute_script("arguments[0].click();",back_page)
    time.sleep(5)
    WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/form[1]/div[3]/div/main/div/div[2]/div[4]/div/div[2]/div/div/div/div[2]/div/table/tbody/tr')))
    
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
# arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
# page_main = fn.init_chrome_driver(arguments) 
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
options = Options()
for argument in arguments:
    options.add_argument(argument)
page_main = webdriver.Chrome(options=options)

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://appstate.az.gov/page.aspx/en/rfp/request_browse_public"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,5):#5
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/form[1]/div[3]/div/main/div/div[2]/div[4]/div/div[2]/div/div/div/div[2]/div/table/tbody/tr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/form[1]/div[3]/div/main/div/div[2]/div[4]/div/div[2]/div/div/div/div[2]/div/table/tbody/tr')))
            length = len(rows)
            
            
            clk=page_main.find_element(By.XPATH,'//*[@id="body_x_selStatusCode_1_search"]').click()
            time.sleep(5)
            clk=page_main.find_element(By.XPATH,'//*[@id="body_x_selStatusCode_1_val"]').click()
            time.sleep(5)
            
            clk=page_main.find_element(By.XPATH,'//*[@id="body_x_prxFilterBar_x_cmdSearchBtn"]/span').click()
            time.sleep(5)
            
            clk=page_main.find_element(By.XPATH,'//*[@id="body_x_grid_grd__ctl1_btnSort_colBeginDate"]/span').click()
            time.sleep(5)
            clk=page_main.find_element(By.XPATH,'//*[@id="body_x_grid_grd__ctl1_btnSort_colBeginDate"]/span').click()
            time.sleep(5)
            
             
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/form[1]/div[3]/div/main/div/div[2]/div[4]/div/div[2]/div/div/div/div[2]/div/table/tbody/tr')))[records]
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
                next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="body_x_grid_PagerBtnNextPage"]')))
                page_main.execute_script("arguments[0].click();",next_page)
                logging.info("Next page")
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/form[1]/div[3]/div/main/div/div[2]/div[4]/div/div[2]/div/div/div/div[2]/div/table/tbody/tr'),page_check))
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
    
    output_json_file.copyFinalJSONToServer(output_json_folder)
