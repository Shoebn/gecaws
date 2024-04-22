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
import gec_common.OutputJSON
from gec_common import functions as fn
from deep_translator import GoogleTranslator

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "co_secop_pp"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'co_secop_pp'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'CO'
    notice_data.performance_country.append(performance_country_data)
   
    notice_data.currency = 'COP'
    
    notice_data.main_language = 'ES'
    
    notice_data.notice_type = 3
    
    notice_data.procurement_method = 2

    notice_data.notice_url = url

    org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text

    try:
        p_date = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(7)').text
        if '-' in p_date:
            publish_date = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
            publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.publish_date)
            notice_data.notice_type = 16
        else:
            publish_date = re.findall('\d+/\d+/\d{4}',p_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
        

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:
        est_amount = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
        est_amount = re.sub("[^\d\.\,]", "", est_amount) 
        notice_data.est_amount = float(est_amount.replace('.','').replace(',','.').strip())
        notice_data.grossbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in est_amount : {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    except:
        pass

    try:
        id_selector = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(9) > a').get_attribute('onclick')
        url_id = re.findall('\d{6}',id_selector)[0]
        notice_data.notice_url = 'https://community.secop.gov.co/Public/App/AnnualPurchasingPlanEditPublic/View?id='+str(url_id)                 
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url


    
    try:
        fn.load_page(page_details,notice_data.notice_url,80) 
        WebDriverWait(page_details, 120).until(EC.presence_of_element_located((By.XPATH, '(//*[contains(text(),"Misión y visión:")]//following::td/span[1])[1]'))).text
        try: 
            notice_data.notice_no = notice_data.notice_url.split("id=")[1].strip()
        except Exception as e:
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass
            
        try:
            notice_data.local_title = page_details.find_element(By.XPATH, '(//*[contains(text(),"Misión y visión:")]//following::td/span[1])[1]').text
            notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
        except Exception as e:
            logging.info("Exception in local_title: {}".format(type(e).__name__))
            pass
            
        try:
            local_description = page_details.find_element(By.XPATH,'''(//*[contains(text(),"Perspectiva estratégica:")]//following::td/span[1])[1]''').text
            notice_data.local_description = GoogleTranslator(source='auto', target='en').translate(local_description)
            notice_data.notice_summary_english = notice_data.notice_title + ',' + notice_data.local_description
        except Exception as e:
            logging.info("Exception in local_description: {}".format(type(e).__name__))
            pass
    
        try:              
            customer_details_data = customer_details()
            customer_details_data.org_name = org_name
            try:
                customer_details_data.contact_person = page_details.find_element(By.XPATH, '(//*[contains(text(),"Nombre:")]//following::td/span[1])[1]').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass 
    
            try:
                customer_details_data.org_phone = page_details.find_element(By.XPATH, '(//*[contains(text(),"Teléfono:")]//following::td/span[1])[1]').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
    
            try:
                customer_details_data.org_email = page_details.find_element(By.XPATH, '(//*[contains(text(),"Correo electrónico:")]//following::td/span[1])[1]').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
            customer_details_data.org_parent_id = 6970985
            customer_details_data.org_country = 'CO'
            customer_details_data.org_language = 'ES'
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
        except Exception as e:
            logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
            pass
    
        try:
            notice_data.notice_text += page_details.find_element(By.XPATH, '/html/body/div[2]/div[2]/table/tbody/tr/td[3]/form/table/tbody/tr[2]/td/table').get_attribute('outerHTML')
        except:
            pass
    
        try:
            lot_tr_no = 1
            cpv_at_source = ''
            for page_no in range(1,7):
                page_check = WebDriverWait(page_details, 60).until(EC.presence_of_element_located((By.XPATH,"(//tr[@style='display: table-row;'])[3]"))).text
                rows = WebDriverWait(page_details, 120).until(EC.presence_of_all_elements_located((By.XPATH, "(//tr[@style='display: table-row;'])")))
                length = len(rows)
                for lot_records in range(1,length-1):
                    lot_number = 1
                    single_record = WebDriverWait(page_details, 120).until(EC.presence_of_all_elements_located((By.XPATH, "(//tr[@style='display: table-row;'])")))[lot_records]
                    lot_details_data = lot_details()
                    lot_details_data.lot_number = lot_number
                    try:
                        lot_class_codes_at_source = ''
                        lot_cpv_at_source = ''
                        codes_at_source = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
                        if '-' not in codes_at_source:
                            cpv_regex = re.compile(r'\d{8}')
                            code_list = cpv_regex.findall(codes_at_source)
                            for cpv_codes in code_list:
                                
                                lot_class_codes_at_source += cpv_codes
                                lot_class_codes_at_source += ','
                                
                                lot_cpv_at_source += cpv_codes
                                lot_cpv_at_source += ','
            
                                cpv_at_source += cpv_codes
                                cpv_at_source += ','
                                
                                cpv_codes_list = fn.CPV_mapping("assets/co_secop_pp_unspsc_cpvmap.csv",cpv_codes)
                                for each_cpv in cpv_codes_list:
                                    cpvs_data = cpvs()
                                    cpvs_data.cpv_code = each_cpv
                                    cpvs_data.cpvs_cleanup()
                                    notice_data.cpvs.append(cpvs_data)
                                    lot_cpvs_data = lot_cpvs()
                                    lot_cpvs_data.lot_cpv_code = each_cpv
                                    lot_cpvs_data.lot_cpvs_cleanup()
                                    lot_details_data.lot_cpvs.append(lot_cpvs_data)
                                            
                            lot_details_data.lot_class_codes_at_source = lot_class_codes_at_source.rstrip(',')
                            lot_details_data.lot_cpv_at_source = lot_cpv_at_source.rstrip(',')
                    except:
                        pass
        
                    lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
                    lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
                    try:
                        lot_details_data.contract_duration = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
                    except:
                        pass
        
                    
                    try:
                        lot_netbudget_lc = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(8)').text
                        if '-' not in lot_netbudget_lc:
                            lot_netbudget_lc = re.sub("[^\d\.]", "", lot_netbudget_lc)
                            lot_details_data.lot_netbudget_lc = float(lot_netbudget_lc.replace('.','').strip()) 
                    except Exception as e:
                        logging.info("Exception in lot_netbudget_lc: {}".format(type(e).__name__))
                        pass

                    if '-' not in lot_details_data.lot_title:
                        lot_details_data.lot_details_cleanup()
                        notice_data.lot_details.append(lot_details_data)
                        lot_number += 1
        
            
                check = page_details.find_element(By.XPATH, "(//*[@class='VortalPaginatorPage'])[last()]").get_attribute('outerHTML')
                if 'display: none;' not in check:
                    next_page = WebDriverWait(page_details, 60).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#grdTempAcqGrid_Paginator_goToPage_Next')))
                    page_details.execute_script("arguments[0].click();",next_page)
                    logging.info("Lot Next page")
                    time.sleep(5)
                    WebDriverWait(page_details, 60).until_not(EC.text_to_be_present_in_element((By.XPATH,"(//tr[@style='display: table-row;'])[3]"),page_check))
                else:
                    next_page = WebDriverWait(page_details, 60).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#grdTempAcqGrid_Paginator_goToPage_MoreItems')))
                    page_details.execute_script("arguments[0].click();",next_page)
                    logging.info("Lot Next page") 
                    time.sleep(5)
                    WebDriverWait(page_details, 60).until_not(EC.text_to_be_present_in_element((By.XPATH,"(//tr[@style='display: table-row;'])[3]"),page_check))
            notice_data.cpv_at_source = cpv_at_source.rstrip(',')
        except Exception as e:
            logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
            pass  

    except:
        pass
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) + str(notice_data.local_title)
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
    urls = ["https://community.secop.gov.co/Public/App/AnnualPurchasingPlanManagementPublic/Index?currentLanguage=es-CO&Page=login&Country=CO&SkinName=CCE"] 
    for url in urls:
        fn.load_page(page_main, url, 80)
        logging.info('----------------------------------')
        logging.info(url)

        try:
            for page_no in range(1,7):
                page_check = WebDriverWait(page_main, 60).until(EC.presence_of_element_located((By.XPATH,"(//tr[@style='display: table-row;'])[3]"))).text
                rows = WebDriverWait(page_main, 120).until(EC.presence_of_all_elements_located((By.XPATH, "//tr[@style='display: table-row;']")))
                length = len(rows)
                for records in range(1,length-1):
                    tender_html_element = WebDriverWait(page_main,100).until(EC.presence_of_all_elements_located((By.XPATH, "//tr[@style='display: table-row;']")))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                try:  
                    check = page_main.find_element(By.XPATH, "(//*[@class='VortalPaginatorPage'])[last()]").get_attribute('outerHTML')
                    if 'display: none;' not in check:
                        next_page = WebDriverWait(page_main, 60).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#grdGridAPP_Paginator_goToPage_Next')))
                        page_main.execute_script("arguments[0].click();",next_page)
                        logging.info("Next page")
                        time.sleep(5)
                        WebDriverWait(page_main, 60).until_not(EC.text_to_be_present_in_element((By.XPATH,"(//tr[@style='display: table-row;'])[3]"),page_check))
                    else:
                        next_page = WebDriverWait(page_main, 60).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#grdGridAPP_Paginator_goToPage_MoreItems')))
                        page_main.execute_script("arguments[0].click();",next_page)
                        logging.info("Next page") 
                        time.sleep(5)
                        WebDriverWait(page_main, 60).until_not(EC.text_to_be_present_in_element((By.XPATH,"(//tr[@style='display: table-row;'])[3]"),page_check))  
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
    page_details.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)