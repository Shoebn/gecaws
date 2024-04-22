
from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "vn_muasamcong_pp"
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

##---------------------------------------------------------------------********************************************************************-----------------------------------------------------

#     NOTE- after clicking on "Tìm kiếm nâng cao", "div.content__search__body > a >>>>>>>> select "Thời gian đăng tải" and "Thời điểm đóng thầu" dates                                                       
#     NOTE- " select "Tìm theo :" >>>    >>>      Kế hoạch lựa chọn nhà thầu / Bidder selection plan   -- as notice_type "3" >>>"Tìm kiếm"..... if tender page redirects to the main page click on ,"Search"
#     NOTE- use vpn to load the website 
##---------------------------------------------------------------------********************************************************************-----------------------------------------------------  

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
tnotice_count = 0
SCRIPT_NAME = "vn_muasamcong_pp"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    global tnotice_count
    notice_data = tender()
    
    notice_data.script_name = 'vn_muasamcong_pp'
   
    notice_data.main_language = 'VI'
   
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'VN'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.notice_type = 3
    
    notice_data.currency = 'VND'

    notice_data.document_type_description = "Kế hoạch lựa chọn nhà thầu"
    
    # Onsite Field -Ngày đăng tải - Publication date : 09/02/2024 - 17:06
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div.col-md-8.content__body__left__item__infor__contract__other > h6:nth-child(2) > span").text
        publish_date = re.findall('\d+/\d+/\d{4} - \d+:\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y - %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
   
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-md-10.content__body__left__item__infor__contract  h5').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Mã KHLCNT / Plan No :
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div.justify-content-between.align-items-center  p').text.split('Mã KHLCNT : ')[1].strip()
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Dự toán mua sắm / Purchase estimate
    try:
        netbudgetlc = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-md-4.content__body__left__item__infor__contract__other > h6:nth-child(2) > span').text
        netbudgetlc = re.sub("[^\d\.\,]","",netbudgetlc)
        notice_data.netbudgetlc =float(netbudgetlc.replace('.','').replace(',','.').strip())
        notice_data.est_amount = notice_data.netbudgetlc
    except Exception as e:
        logging.info("Exception in netbudgetlc: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    except:
        pass
    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-md-10.content__body__left__item__infor__contract a').get_attribute("href")
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        pass

    try:                             
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
        
        # Onsite Field -if present take data  from following tabs "Hồ sơ mời thầu",  "Làm rõ HSMT",  "Hội nghị tiền đấu thầu",  "Kiến nghị" 
        # Onsite Comment -# Onsite Comment -along with notice text (page detail) also take data from tender_html_element  (main page) ----"//*[@id="bid-closed"]/div"
        try:
            notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.d-flex > div.tab-content').get_attribute("outerHTML")                     
        except:
            pass
        
        try:
            click = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="tender-notice"]/div/div/div[1]/div[1]/div[2]/ul/li[2]'))).click()
            time.sleep(10)
            
            try:
                notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.d-flex > div.tab-content').get_attribute("outerHTML")                     
            except:
                pass
            #Supply - Hàng hóa, Works - Xây lắp, Non-consulting - Phi tư vấn, Consulting - Tư vấn, Khác
            # Onsite Field -Lĩnh vực / Procurement category :
            # Onsite Comment -click on "Thông tin gói thầu" for notice_contract_type >> apply selector
            try:
                notice_data.contract_type_actual = page_details.find_element(By.XPATH, "(//*[contains(text(),'Lĩnh vực')]//following::div[1])[2]").text
                if 'Hàng hóa' in notice_data.contract_type_actual:
                    notice_data.notice_contract_type = 'Supply'
                elif 'Xây lắp' in notice_data.contract_type_actual:
                    notice_data.notice_contract_type = 'Works'
                elif 'Phi tư vấn' in notice_data.contract_type_actual:
                    notice_data.notice_contract_type = 'Non consultancy'
                elif 'Tư vấn' in notice_data.contract_type_actual or 'Tư vấn, Khác' in notice_data.contract_type_actual:
                    notice_data.notice_contract_type = 'Consultancy'
            except Exception as e:
                logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
                pass
            
            # Onsite Field -Trong nước/ Quốc tế  / Domestic/International  ------------- if "NCB  = Trong nước = "0",    "ICB = Quốc tế = " 1 "
            # Onsite Comment -click on "Thông tin gói thầu" then use the selector  to get data
            try:
                procurement_method = page_details.find_element(By.XPATH, "//*[contains(text(),'Trong nước/ Quốc tế')]//following::div[1]").text
                if 'Trong nước' in procurement_method:
                    notice_data.procurement_method = 0
                elif 'Quốc tế' in procurement_method:
                    notice_data.procurement_method = 1
            except Exception as e:
                logging.info("Exception in procurement_method: {}".format(type(e).__name__))
                pass
        

            click = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="tender-notice"]/div/div/div[1]/div[1]/div[2]/ul/li[1]'))).click()
            time.sleep(10)
        except:
            pass
        
        try: 
            no_types = page_details.find_element(By.CSS_SELECTOR, 'div:nth-child(3) > div.text-blue-4D7AE6 > select')
            count = 0
            for no in no_types.find_elements(By.CSS_SELECTOR, 'option'):
                count += 1
                if count > 1:
                    notice_data.notice_type = 16
                else:
                    notice_data.notice_type = 3
                time.sleep(5)
        except:
            pass
        
        try:              
            customer_details_data = customer_details()
            customer_details_data.org_country = 'VN'
            customer_details_data.org_language = 'VI'
            # Onsite Field -Employer / Chủ đầu tư :  Chủ đầu tư/ Bên mời thầu
            customer_details_data.org_name = page_details.find_element(By.XPATH, "(//*[contains(text(),'Chủ đầu tư')]//following::div[1])[3]").text
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
        except Exception as e:
            logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
            pass
        
        try:    
            lot_number = 1
            for single_record in page_details.find_elements(By.XPATH, "(//*[contains(text(),'Danh sách gói thầu')]//following::div/table)[1]/tbody/tr"):
                lot_details_data = lot_details()
                lot_details_data.lot_number = lot_number
                lot_details_data.contract_type = notice_data.notice_contract_type
                lot_details_data.lot_contract_type_actual = notice_data.contract_type_actual
            # Onsite Field -Tên chủ đầu tư	

                lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
                lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
            # Onsite Field -Giá gói thầu (VND)	 / Procurement package’s estimated price (VND)

                try:
                    lot_netbudget_lc = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
                    lot_netbudget_lc = re.sub("[^\d\.\,]","",lot_netbudget_lc)
                    lot_details_data.lot_netbudget_lc =float(lot_netbudget_lc.replace('.','').replace(',','.').strip())
                    lot_details_data.lot_netbudget =lot_details_data.lot_netbudget_lc
                except Exception as e:
                    logging.info("Exception in lot_netbudget_lc_1: {}".format(type(e).__name__))
                    pass
                
                try:
                    lot_netbudget_lc = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(6)').text
                    lot_netbudget_lc = re.sub("[^\d\.\,]","",lot_netbudget_lc)
                    lot_details_data.lot_netbudget_lc =float(lot_netbudget_lc.replace('.','').replace(',','.').strip())
                    lot_details_data.lot_netbudget =lot_details_data.lot_netbudget_lc
                except Exception as e:
                    logging.info("Exception in lot_netbudget_lc_2: {}".format(type(e).__name__))
                    pass
                

                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
                lot_number += 1
        except Exception as e:
            logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
            pass
        
    except:
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_url) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title)
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    tnotice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver_vpn(arguments) 
page_details = fn.init_chrome_driver_vpn(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://muasamcong.mpi.gov.vn/vi/web/guest/home"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        close_popup = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#popup-close')))
        page_main.execute_script("arguments[0].click();",close_popup)
        time.sleep(5)
        
        Tìm_kiếm_nâng_ca_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'div.content__wrapper__header > div.content__search__body > a > button')))
        page_main.execute_script("arguments[0].click();",Tìm_kiếm_nâng_ca_click)
        time.sleep(5)
    
        select_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="search-advantage-haunt"]/div/div/div/div/div/div[2]/div[2]/div[2]/div/div/div/div/div')))
        page_main.execute_script("arguments[0].click();",select_click)
        time.sleep(5)
        
        click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'div.ant-select-dropdown-content > ul > li:nth-child(2)')))
        page_main.execute_script("arguments[0].click();",click)
        time.sleep(5)
                
        Tìm_kiếm_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#search-advantage-haunt > div > div > div > div > div > div.content__footer > button:nth-child(2)')))
        page_main.execute_script("arguments[0].click();",Tìm_kiếm_click)
        time.sleep(5)
        
        for page_no in range(1,10):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="bid-closed"]/div'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="bid-closed"]/div')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="bid-closed"]/div')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break

                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
                    
                if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                    logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                    break

                if notice_count == 5:
                    output_json_file.copyFinalJSONToServer(output_json_folder)
                    output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
                    notice_count = 0

            if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                break

            try:   
                next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="search-home"]/div/div[3]/div[2]/div/div/button[2]')))
                page_main.execute_script("arguments[0].click();",next_page)
                logging.info("Next page")
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="bid-closed"]/div'),page_check))
            except Exception as e:
                logging.info("Exception in next_page: {}".format(type(e).__name__))
                logging.info("No next page")
                break
    logging.info("Finished processing. Scraped {} notices".format(tnotice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit() 
    
    output_json_file.copyFinalJSONToServer(output_json_folder)
    
