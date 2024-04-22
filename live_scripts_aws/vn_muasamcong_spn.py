from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "vn_muasamcong_spn"
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
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
import gec_common.Doc_Download_VPN as Doc_Download

##---------------------------------------------------------------------********************************************************************-----------------------------------------------------

#     NOTE- after clicking on "Tìm kiếm nâng cao", "div.content__search__body > a >>>>>>>> select "Thời gian đăng tải" and "Thời điểm đóng thầu" dates                                                   
#     NOTE- " select "Tìm theo :" >>>     Biên bản mở thầu   / Thông báo mời thầu ---- take as "4",   Thông báo mời sơ tuyển ---- take as "6', Thông báo mời quan tâm --- take as "5". >>>"Tìm kiếm"..... if tender page redirects to the main page click on " div > button > p","Search"

##---------------------------------------------------------------------********************************************************************-----------------------------------------------------    

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
tnotice_count = 0
SCRIPT_NAME = "vn_muasamcong_spn"
Doc_Download = gec_common.Doc_Download_VPN.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    global tnotice_count
    notice_data = tender()
    
    notice_data.script_name = 'vn_muasamcong_spn'
   
    notice_data.main_language = 'VI'
   
    notice_data.currency = 'VND'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'VN'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Comment -after clicking on "Tìm kiếm nâng cao", "div.content__search__body > a" select "Tìm theo :" >>>     Biên bản mở thầu   / Thông báo mời thầu ---- take as "4",   Thông báo mời sơ tuyển ---- take as "6', Thông báo mời quan tâm --- take as "5". >>>"Tìm kiếm"
    notice_data.notice_type = notice_type

    notice_data.document_type_description = 'Thông báo mời thầu'
    

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div > div.row > div.col-md-8.content__body__left__item__infor__contract > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
        
    # Onsite Field -Trong nước/ Quốc tế
    # Onsite Comment -if "NCB  = Trong nước = "0",    "ICB = Quốc tế = " 1 "

    try:
        procurement_method = page_details.find_element(By.XPATH, "//*[contains(text(),'Trong nước/ Quốc tế')]//following::div[1]").text
        if 'Trong nước' in procurement_method:
            notice_data.procurement_method = 0
        elif 'Quốc tế'in procurement_method:
            notice_data.procurement_method = 1
    except Exception as e:
        logging.info("Exception in procurement_method: {}".format(type(e).__name__))
        pass

    # Onsite Comment -take data which is after ":".....split data from ":" till "Procuring Entity"

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-md-8.content__body__left__item__infor__contract   h5').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -te of publishing of notice :
    # Onsite Comment -along with date also grab time

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div.row > div.col-md-8.content__body__left__item__infor__contract > div > div.col-md-8.content__body__left__item__infor__contract__other").text
        publish_date = re.findall('\d+/\d+/\d{4} - \d+:\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y - %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Bid closing time
    # Onsite Comment -along with date also grab time

    try:
        deadline = tender_html_element.find_element(By.CSS_SELECTOR, "div > div.row > div.col-md-2.content__body__right__item__infor__contract > div").text
        deadline_date = re.findall('\d+/\d+/\d{4}',deadline)[0]
        deadline_time = re.findall('\d+:\d+',deadline)[0]
        notice_deadline = deadline_date + ' ' + deadline_time
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Bid closing time
    # Onsite Comment -along with date also grab time

    # Onsite Comment -also take notice_no from notice url

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div.justify-content-between.align-items-center  p').text.split(':')[1].strip()
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Comment - Map Supply - Hàng hóa, Works - Xây lắp, Non-consulting - Phi tư vấn, Consulting - Tư vấn, 

    try:
        notice_data.contract_type_actual = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-md-4 h6:nth-child(1) > span').text
        if 'Hàng hóa' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Supply'
        elif 'Xây lắp' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Works'
        elif 'Phi tư vấn' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Non consultancy'
        elif 'Tư vấn' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Consultancy'
        else:
            pass
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Thời gian thực hiện gói thầu

    try:
        notice_data.contract_duration = page_details.find_element(By.XPATH, '''(//*[contains(text(),'Thời gian thực hiện gói thầu')]//following::div[1])[1]''').text
    except:
        try:
            notice_data.contract_duration = page_details.find_element(By.XPATH, '''(//*[contains(text(),'Thời gian thực hiện hợp đồng')]//following::div[1])[1]''').text 
        except Exception as e:
            logging.info("Exception in contract_duration: {}".format(type(e).__name__))
            pass
    
    # Onsite Field -Chi phí nộp e-HSDT

    try:
        notice_data.document_cost = page_details.find_element(By.XPATH, '''(//*[contains(text(),'Chi phí nộp e-HSDT')]//following::div[1])[1]''').text
    except Exception as e:
        logging.info("Exception in document_cost: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Số tiền đảm bảo dự thầu

    try:
        notice_data.earnest_money_deposit = page_details.find_element(By.XPATH, '''(//*[contains(text(),'Số tiền đảm bảo dự thầu')]//following::div[1])[1]''').text.split('VND')[0].strip()
    except Exception as e:
        logging.info("Exception in earnest_money_deposit: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '''//*[contains(text(),'Tên dự án')]//following::div[1]''').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Tên dự án

    try:
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Tên dự án
    
    try:
        amount_click = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.XPATH,"//*[contains(text(),'Biên bản mở thầu')]//parent::a")))
        page_details.execute_script("arguments[0].click();",amount_click)
        time.sleep(2)
    except:
        pass

    try:
        netbudgetlc = page_details.find_element(By.XPATH, '''(//*[contains(text(),'Giá gói thầu')]//following::div[1])[1]''').text.split('VND')[0].strip()
        netbudgetlc = float(netbudgetlc.replace('.','').strip())
        notice_data.netbudgetlc = netbudgetlc
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
#     # Onsite Field -Tổng mức đầu tư
#     # Onsite Comment -click on "//*[contains(text(),'Mã KHLCNT')]//following::div[1] " for detail pages1 data

    try:
        back_click = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.XPATH,"//*[contains(text(),'Thông báo mời thầu')]//parent::a")))
        page_details.execute_script("arguments[0].click();",back_click)
        time.sleep(2)
    except:
        pass

    # Onsite Field -Tổng mức đầu tư
    # Onsite Comment -click on "//*[contains(text(),'Mã KHLCNT')]//following::div[1] " for detail pages
    
    # Onsite Field -if present take data  from following tabs "Hồ sơ mời thầu",  "Làm rõ HSMT",  "Hội nghị tiền đấu thầu",  "Kiến nghị" 
    # Onsite Comment -# Onsite Comment -along with notice text (page detail) also take data from tender_html_element  (main page) ----"//*[@id="bid-closed"]/div"
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.d-flex > div.tab-content').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')

    try:              
        customer_details_data = customer_details()

        customer_details_data.org_language = 'VI'
        customer_details_data.org_country = 'VN'
    # Onsite Field -Bên mời thầu

        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-md-8.content__body__left__item__infor__contract__other').text.split('Bên mời thầu :')[1].split('\n')[0].strip()

    # Onsite Field -Địa điểm     ---------- split data from "Địa điểm :" till "-"
    # Onsite Comment -if keyword such as "Thành" is present in data then take  data in org_city
        try:
            customer_details_data.org_address = tender_html_element.find_element(By.CSS_SELECTOR,'h6.format__text__title').text.split(':')[1].strip()
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass
        
        try:
            org_city = tender_html_element.find_element(By.CSS_SELECTOR, 'h6.format__text__title').text
            if "Thành" in org_city:
                customer_details_data.org_city = "Thành"
            else:
                pass
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass

    # Onsite Field -Địa điểm
    # Onsite Comment ----------- split data from  "-"  till ";"

    # Onsite Field -Địa điểm     ---------- split data from "Địa điểm :" till "-"
    # Onsite Comment -if keyword such as "Huyện" is present in data then take  data in org_state

        try:
            org_state = tender_html_element.find_element(By.CSS_SELECTOR, 'h6.format__text__title').text
            if "Huyện" in org_city:
                customer_details_data.org_state = "Huyện"
            else:
                pass
        except Exception as e:
            logging.info("Exception in org_state: {}".format(type(e).__name__))
            pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:
        plan_no_click = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.XPATH,"(//*[contains(text(),'Mã KHLCNT')]//following::div[1])[1]")))
        page_details.execute_script("arguments[0].click();",plan_no_click)
    except:
        pass
    
    try:
        est_amount = WebDriverWait(page_details, 80).until(EC.presence_of_element_located((By.XPATH,'''(//*[contains(text(),'Dự toán mua sắm')]//following::div[1])[1]'''))).text.split('VND')[0].strip()
        est_amount = est_amount.replace('.','').strip()
        notice_data.est_amount = float(est_amount)
        notice_data.netbudgetlc = notice_data.est_amount
    except:
        try:
            est_amount = WebDriverWait(page_details, 50).until(EC.presence_of_element_located((By.XPATH,'''(//*[contains(text(),'Tổng mức đầu tư')]//following::div[1])[1]'''))).text.split('VND')[0].strip()
            est_amount = est_amount.replace('.','').strip()
            notice_data.est_amount = float(est_amount)
            notice_data.netbudgetlc = notice_data.est_amount
        except Exception as e:
            logging.info("Exception in est_amount: {}".format(type(e).__name__))
            pass
     
    try:
        if notice_data.est_amount == 0.0:
            notice_data.est_amount = notice_data.netbudgetlc
            if notice_data.est_amount == 0.0:
                notice_data.est_amount = notice_data.netbudgetlc
    except:
        pass
                        
    try: 
        page_details.find_element(By.CSS_SELECTOR, "#table-pack > tbody > tr")
        lot_number = 1
        for single_record in page_details.find_elements(By.CSS_SELECTOR, "#table-pack > tbody > tr"):
            lot_details_data = lot_details()
            lot_details_data.lot_number = lot_number
            lot_details_data.lot_contract_type_actual = notice_data.contract_type_actual
            lot_details_data.contract_type = notice_data.notice_contract_type
            
        # Onsite Comment -date data which is before ":" as notice_actual_number

            try:
                lot_details_data.lot_actual_number = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text.split(':')[0].strip()
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass
        
        # Onsite Comment -take date data which is after ":" as local_title
            try:
                lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text.split(':')[1].strip()
                lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
            except:
                lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
                lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
                
        # Onsite Field -Giá gói thầu (VND)
        
            try:
                lot_netbudget_lc = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(6)').text
                lot_netbudget_lc = float(lot_netbudget_lc.replace('.','').strip())
                lot_details_data.lot_netbudget_lc = lot_netbudget_lc
            except Exception as e:
                logging.info("Exception in lot_netbudget_lc: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Thời gian bắt đầu tổ chức LCNT

            try:
                lot_details_data.contract_duration = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(13)').text
            except Exception as e:
                logging.info("Exception in contract_duration: {}".format(type(e).__name__))
                pass
        
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
            lot_number += 1
    except:
        try:
            lot_number = 1
            for single_record in page_details.find_elements(By.CSS_SELECTOR, "#tab1 > div.card.border--none.card-expand > div.card-body.item-table > table > tbody > tr"):
                lot_details_data = lot_details()
                lot_details_data.lot_number = lot_number
                lot_details_data.lot_contract_type_actual = notice_data.contract_type_actual
                lot_details_data.contract_type = notice_data.notice_contract_type
                
            # Onsite Comment -date data which is before ":" as notice_actual_number

                try:
                    lot_details_data.lot_actual_number = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text.split(':')[0].strip()
                except Exception as e:
                    logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                    pass

            # Onsite Comment -take date data which is after ":" as local_title

                lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text.split(':')[1].strip()
                lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)

            # Onsite Field -Giá gói thầu (VND)

                try:
                    lot_netbudget_lc = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
                    lot_netbudget_lc = float(lot_netbudget_lc.replace('.','').strip())
                    lot_details_data.lot_netbudget_lc = lot_netbudget_lc
                except Exception as e:
                    logging.info("Exception in lot_netbudget_lc: {}".format(type(e).__name__))
                    pass

            # Onsite Field -Thời gian bắt đầu tổ chức LCNT

                try:
                    lot_details_data.contract_duration = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(10)').text
                except Exception as e:
                    logging.info("Exception in contract_duration: {}".format(type(e).__name__))
                    pass

                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
                lot_number += 1
        except Exception as e:
            logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
            pass

    try:
        back_click = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"#tender-notice > div > button:nth-child(1)")))
        page_details.execute_script("arguments[0].click();",back_click)
        time.sleep(6)
    except:
        pass

# Onsite Field -click on "Hồ sơ mời thầu" for attachment data  use the following selector "//*[contains(text(),'Mã KHLCNT')]//following::div[1]"
    try:
        attachment_page_click = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.XPATH,"//*[contains(text(),'Hồ sơ mời thầu')]//parent::a")))
        page_details.execute_script("arguments[0].click();",attachment_page_click)
        time.sleep(6)
    except:
        pass
    
    try: 
        WebDriverWait(page_details, 60).until(EC.presence_of_element_located((By.XPATH,"(//*[contains(text(),'Tải tất cả biểu mẫu webform')]//parent::span[1]/span)[1]"))).text
        attachments_data = attachments()
    # Onsite Field -Quyết định phê duyệt

        attachments_data.file_name = page_details.find_element(By.XPATH, "(//*[contains(text(),'Tải tất cả biểu mẫu webform')]//parent::span[1])[1]").text

        try:
            attachments_data.file_description = page_details.find_element(By.XPATH,"(//*[contains(text(),'Tải tất cả biểu mẫu webform')]//parent::span[1]/span)[1]").text
        except Exception as e:
            logging.info("Exception in file_description: {}".format(type(e).__name__))
            pass

        external_url_click = WebDriverWait(page_details, 200).until(EC.element_to_be_clickable((By.XPATH,"(//*[contains(text(),'Tải tất cả biểu mẫu webform')]//parent::span[1]/span)[1]")))
        page_details.execute_script("arguments[0].click();",external_url_click)
        page_details.switch_to.window(page_details.window_handles[1])
        if records==0:
            time.sleep(80)
        else:
            time.sleep(2)

        external_url = WebDriverWait(page_details, 150).until(EC.element_to_be_clickable((By.XPATH,'''//*[@id="egp_body"]/ebid-viewer/div[1]/div/div[2]/button[2]''')))
        page_details.execute_script("arguments[0].click();",external_url)
        time.sleep(12)
        file_dwn = Doc_Download.file_download()
        attachments_data.external_url = str(file_dwn[0])
        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
        page_details.switch_to.window(page_details.window_handles[0])
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
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
page_details = Doc_Download.page_details
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://muasamcong.mpi.gov.vn/vi/web/guest"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        close_popup = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#popup-close')))
        page_main.execute_script("arguments[0].click();",close_popup)
        
        click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'div.content__wrapper__header > div.content__search__body > a > button')))
        page_main.execute_script("arguments[0].click();",click)
        time.sleep(2)
        
        list_index = [4,5,6]
        for index in list_index:
            if index==3:
                notice_type = 4
            elif index == 4:
                notice_type = 6
            elif index == 5:
                notice_type = 5
            else:
                pass
            time.sleep(2)
                
            click = WebDriverWait(page_main, 80).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="search-advantage-haunt"]/div/div/div/div/div/div[2]/div[2]/div[2]/div/div/div/div/div')))
            page_main.execute_script("arguments[0].click();",click)
            time.sleep(2)
                                                    
            click = page_main.find_elements(By.CSS_SELECTOR, "div.ant-select-dropdown-content > ul > li")[index]
            click.click()
            time.sleep(5)
                
            Tìm_kiếm_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#search-advantage-haunt > div > div > div > div > div > div.content__footer > button:nth-child(2)')))
            page_main.execute_script("arguments[0].click();",Tìm_kiếm_click)
            time.sleep(5)
        
            for page_no in range(1,50):
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

                    if notice_count == 1:
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
                    
            try:
                click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#search-home > div > div.content__search.d-flex.gap-47 > div.content__wrapper__header > div:nth-child(2) > button')))
                page_main.execute_script("arguments[0].click();",click)
                time.sleep(5)
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="search-advantage-haunt"]/div/div/div/div/div/div[2]/div[2]/div[2]/div/div/div/div/div')))
            except:
                pass
    logging.info("Finished processing. Scraped {} notices".format(tnotice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit() 
    output_json_file.copyFinalJSONToServer(output_json_folder)
