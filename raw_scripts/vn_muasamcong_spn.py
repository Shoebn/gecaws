
from gec_common.gecclass import *
import logging
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

##---------------------------------------------------------------------********************************************************************-----------------------------------------------------

#     NOTE- after clicking on "Tìm kiếm nâng cao", "div.content__search__body > a >>>>>>>> select "Thời gian đăng tải" and "Thời điểm đóng thầu" dates                                                       
#     NOTE- " select "Tìm theo :" >>>     Biên bản mở thầu   / Thông báo mời thầu ---- take as "4",   Thông báo mời sơ tuyển ---- take as "6', Thông báo mời quan tâm --- take as "5". >>>"Tìm kiếm"..... if tender page redirects to the main page click on " div > button > p","Search"

##---------------------------------------------------------------------********************************************************************-----------------------------------------------------    

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "vn_muasamcong_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.script_name = 'vn_muasamcong_spn'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'VI'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'VND'
    
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'VN'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -
    # Onsite Comment -after clicking on "Tìm kiếm nâng cao", "div.content__search__body > a" select "Tìm theo :" >>>     Biên bản mở thầu   / Thông báo mời thầu ---- take as "4",   Thông báo mời sơ tuyển ---- take as "6', Thông báo mời quan tâm --- take as "5". >>>"Tìm kiếm"
    notice_data.notice_type = 4

    # Onsite Field -None
    # Onsite Comment -None
    notice_data.document_type_description = Thông báo mời thầu
    

    # Onsite Field -Trong nước/ Quốc tế
    # Onsite Comment -if "NCB  = Trong nước = "0",    "ICB = Quốc tế = " 1 "

    try:
        notice_data.procurement_method = page_details.find_element(By.XPATH, '//*[contains(text(),'Trong nước/ Quốc tế')]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in procurement_method: {}".format(type(e).__name__))
        pass

    # Onsite Field -None
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
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "h6:nth-child(3)").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Bid closing time
    # Onsite Comment -along with date also grab time

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "h5:nth-child(3)").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Bid closing time
    # Onsite Comment -along with date also grab time

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "h5:nth-child(2)").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -also take notice_no from notice url

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div.justify-content-between.align-items-center  p').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment - Map Supply - Hàng hóa, Works - Xây lắp, Non-consulting - Phi tư vấn, Consulting - Tư vấn, 


    try:
        notice_data.notice_contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-md-4 h6:nth-child(1)').text
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.contract_type_actual = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-md-4 h6:nth-child(1)').text
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Thời gian thực hiện gói thầu
    # Onsite Comment -None

    try:
        notice_data.contract_duration = page_details.find_element(By.XPATH, '//*[contains(text(),'Thời gian thực hiện gói thầu')]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Chi phí nộp e-HSDT
    # Onsite Comment -None

    try:
        notice_data.document_cost = page_details.find_element(By.XPATH, '//*[contains(text(),'Chi phí nộp e-HSDT')]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in document_cost: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Số tiền đảm bảo dự thầu
    # Onsite Comment -None

    try:
        notice_data.earnest_money_deposit = page_details.find_element(By.XPATH, '//*[contains(text(),'Số tiền đảm bảo dự thầu')]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in earnest_money_deposit: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Mã KHLCNT
    # Onsite Comment -click on "//*[contains(text(),'Mã KHLCNT')]//following::div[1]	" for detail pages1 data

    try:
        notice_data.est_amount = page_details1.find_element(By.XPATH, '//*[contains(text(),'Dự toán mua sắm')]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Mã KHLCNT
    # Onsite Comment -click on "//*[contains(text(),'Mã KHLCNT')]//following::div[1]	" for detail pages1 data

    try:
        notice_data.grossbudgetlc = page_details1.find_element(By.XPATH, '//*[contains(text(),'Dự toán mua sắm')]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),'Tên dự án')]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Tên dự án
    # Onsite Comment -None

    try:
        notice_data.notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),'Tên dự án')]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Tên dự án
    # Onsite Comment -None

    try:
        notice_data.notice_url = page_details.find_element(By.CSS_SELECTOR, 'div.col-md-8.content__body__left__item__infor__contract h5').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -Tổng mức đầu tư
    # Onsite Comment -click on "//*[contains(text(),'Mã KHLCNT')]//following::div[1] " for detail pages1 data

    try:
        notice_data.netbudget_lc = page_details.find_element(By.XPATH, '//*[contains(text(),'Tổng mức đầu tư')]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in netbudget_lc: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Tổng mức đầu tư
    # Onsite Comment -click on "//*[contains(text(),'Mã KHLCNT')]//following::div[1] " for detail pages1 data

    try:
        notice_data.netbudgeteuro = page_details.find_element(By.XPATH, '//*[contains(text(),'Tổng mức đầu tư')]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in netbudgeteuro: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -if present take data  from following tabs "Hồ sơ mời thầu",  "Làm rõ HSMT",  "Hội nghị tiền đấu thầu",  "Kiến nghị" 
    # Onsite Comment -# Onsite Comment -along with notice text (page detail) also take data from tender_html_element  (main page) ----"//*[@id="bid-closed"]/div"
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.d-flex > div.tab-content').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.d-flex > div.tab-content'):
            customer_details_data = customer_details()
        # Onsite Field -Bên mời thầu
        # Onsite Comment -None

            try:
                customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div.format__text > h6:nth-child(1)').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Địa điểm     ---------- split data from "Địa điểm :" till "-"
        # Onsite Comment -if keyword such as "Thành" is present in data then take  data in org_city

            try:
                customer_details_data.org_city = tender_html_element.find_element(By.CSS_SELECTOR, 'h6.format__text__title').text
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Địa điểm
        # Onsite Comment ----------- split data from  "-"  till ";"

            try:
                customer_details_data.org_state = tender_html_element.find_element(By.CSS_SELECTOR, 'h6.format__text__title').text
            except Exception as e:
                logging.info("Exception in org_state: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Địa điểm     ---------- split data from "Địa điểm :" till "-"
        # Onsite Comment -if keyword such as "Huyện" is present in data then take  data in org_state

            try:
                customer_details_data.org_state = tender_html_element.find_element(By.CSS_SELECTOR, 'h6.format__text__title').text
            except Exception as e:
                logging.info("Exception in org_state: {}".format(type(e).__name__))
                pass
        
            customer_details_data.org_language = 'VI'
            customer_details_data.org_country = 'VN'
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -ref url -"https://muasamcong.mpi.gov.vn/vi/web/guest/contractor-selection?p_p_id=egpportalcontractorselectionv2_WAR_egpportalcontractorselectionv2&p_p_lifecycle=0&p_p_state=normal&p_p_mode=view&_egpportalcontractorselectionv2_WAR_egpportalcontractorselectionv2_render=detail-v2&type=es-plan-project-p&stepCode=plan-step-1&id=f36e1e08-5415-4b47-9b24-270250f20c89&planNo=PL2300260565"
# Onsite Comment -click on the data to get information regarding page detail..............use following selector for such "//*[contains(text(),'Mã KHLCNT')]//following::div[1]"

    try:              
        for single_record in page_details1.find_elements(By.CSS_SELECTOR, '#tab1 div.card-body.item-table'):
            lot_details_data = lot_details()
        # Onsite Field -None
        # Onsite Comment -date data which is before ":" as notice_actual_number

            try:
                lot_details_data.lot_actual_number = page_details1.find_element(By.CSS_SELECTOR, '#tab1  td:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -take date data which is after ":" as local_title

            try:
                lot_details_data.lot_title = page_details1.find_element(By.CSS_SELECTOR, '#tab1  td:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Giá gói thầu (VND)
        # Onsite Comment -None

            try:
                lot_details_data.lot_netbudget = page_details1.find_element(By.CSS_SELECTOR, '#tab1  td:nth-child(4)').text
            except Exception as e:
                logging.info("Exception in lot_netbudget: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Giá gói thầu (VND)
        # Onsite Comment -None

            try:
                lot_details_data.lot_netbudget_lc = page_details1.find_element(By.CSS_SELECTOR, '#tab1  td:nth-child(4)').text
            except Exception as e:
                logging.info("Exception in lot_netbudget_lc: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Thời gian bắt đầu tổ chức LCNT
        # Onsite Comment -None

            try:
                lot_details_data.contract_duration = page_details1.find_element(By.CSS_SELECTOR, '#tab1  td:nth-child(8)').text
            except Exception as e:
                logging.info("Exception in contract_duration: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Lĩnh vực
        # Onsite Comment -None

            try:
                lot_details_data.lot_contract_type_actual = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-md-4 h6:nth-child(1)').text
            except Exception as e:
                logging.info("Exception in lot_contract_type_actual: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Lĩnh vực
        # Onsite Comment -None

            try:
                lot_details_data.contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-md-4 h6:nth-child(1)').text
            except Exception as e:
                logging.info("Exception in contract_type: {}".format(type(e).__name__))
                pass
        
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.d-flex > div.tab-content'):
            attachments_data = attachments()
        # Onsite Field -Quyết định phê duyệt
        # Onsite Comment -None

            try:
                attachments_data.file_name = page_details.find_element(By.XPATH, '//*[contains(text(),'Quyết định phê duyệt')]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Quyết định phê duyệt
        # Onsite Comment -None

            try:
                attachments_data.file_description = page_details.find_element(By.XPATH, '//*[contains(text(),'Quyết định phê duyệt')]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in file_description: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Quyết định phê duyệt
        # Onsite Comment -None

            attachments_data.external_url = page_details.find_element(By.XPATH, '//*[contains(text(),'Quyết định phê duyệt')]//following::div[1]').get_attribute('href')

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
            


# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.d-flex > div.tab-content'):
            attachments_data = attachments()
        # Onsite Field -Quyết định phê duyệt
        # Onsite Comment -None

            try:
                attachments_data.file_name = page_details.find_element(By.CSS_SELECTOR, '#info-general > div.mb-2 > span').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Quyết định phê duyệt
        # Onsite Comment -None

            try:
                attachments_data.file_description = page_details.find_element(By.CSS_SELECTOR, '#info-general > div.mb-2 > span').text
            except Exception as e:
                logging.info("Exception in file_description: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Quyết định phê duyệt
        # Onsite Comment -None

            attachments_data.external_url = page_details.find_element(By.CSS_SELECTOR, '#info-general > div.mb-2 > span').get_attribute('href')

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass


# Onsite Field -click on "Mã KHLCNT" from details page for attachment data  use the following selector "#tenderNotice > ul > li:nth-child(2) > a"
# Onsite Comment -from the following field "Phiên bản thay đổi" in page details1 use this xpath to find the field "//*[contains(text(),'Phiên bản thay đổi')]//following::div[1]" >>>>click on downwards arrow >>> first select"00" and take attachments, next >>>> select "01" and take attachments
# Onsite Comment - ref url -"https://muasamcong.mpi.gov.vn/en/web/guest/contractor-selection?p_p_id=egpportalcontractorselectionv2_WAR_egpportalcontractorselectionv2&p_p_lifecycle=0&p_p_state=normal&p_p_mode=view&_egpportalcontractorselectionv2_WAR_egpportalcontractorselectionv2_render=detail-v2&type=es-plan-project-p&stepCode=plan-step-1&id=b6a23c86-b17c-4041-bd35-a02f62f9eaa4&planNo=PL2400007369"
    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#tender-notice > div > div'):
            attachments_data = attachments()
        # Onsite Field -Quyết định phê duyệt
        # Onsite Comment -None

            try:
                attachments_data.file_name = page_details1.find_element(By.CSS_SELECTOR, 'div.detail__children-2__view-primary.tab1').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Quyết định phê duyệt
        # Onsite Comment -None

            try:
                attachments_data.file_description = page_details1.find_element(By.CSS_SELECTOR, 'div.detail__children-2__view-primary.tab1').text
            except Exception as e:
                logging.info("Exception in file_description: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Quyết định phê duyệt
        # Onsite Comment -None

            attachments_data.external_url = page_details1.find_element(By.CSS_SELECTOR, 'div.detail__children-2__view-primary.tab1').get_attribute('href')

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass



# Onsite Field -click on "Hồ sơ mời thầu" for attachment data  use the following selector "//*[contains(text(),'Mã KHLCNT')]//following::div[1]"
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#file-tender-invitation  div > table > tbody'):
            attachments_data = attachments()
        # Onsite Field -Quyết định phê duyệt
        # Onsite Comment -None

            try:
                attachments_data.file_name = page_details.find_element(By.CSS_SELECTOR, ' td:nth-child(2) > span ').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Quyết định phê duyệt
        # Onsite Comment -None

            try:
                attachments_data.file_description = page_details.find_element(By.CSS_SELECTOR, ' td:nth-child(2) > span ').text
            except Exception as e:
                logging.info("Exception in file_description: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Quyết định phê duyệt
        # Onsite Comment -None

            attachments_data.external_url = page_details.find_element(By.CSS_SELECTOR, ' td:nth-child(2) > span ').get_attribute('href')

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass







# Onsite Field -click on "Hồ sơ mời thầu" for attachment data  use the following selector "//*[contains(text(),'Mã KHLCNT')]//following::div[1]"
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#file-tender-invitation  div > table > tbody'):
            attachments_data = attachments()
        # Onsite Field -Quyết định phê duyệt
        # Onsite Comment -None

            try:
                attachments_data.file_name = page_details.find_element(By.CSS_SELECTOR, '  span:nth-child(2) > span ').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Quyết định phê duyệt
        # Onsite Comment -None

            try:
                attachments_data.file_description = page_details.find_element(By.CSS_SELECTOR, '  span:nth-child(2) > span ').text
            except Exception as e:
                logging.info("Exception in file_description: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Quyết định phê duyệt
        # Onsite Comment -None

            attachments_data.external_url = page_details.find_element(By.CSS_SELECTOR, '  span:nth-child(2) > span ').get_attribute('href')

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass






# Onsite Field -click on "Mã KHLCNT" from details page for attachment data  use the following selector "#tenderNotice > ul > li:nth-child(2) > a"
# Onsite Comment -from the following field "Quyết định phê duyệt" in page details1 
# Onsite Comment - ref url -"https://muasamcong.mpi.gov.vn/vi/web/guest/contractor-selection?p_p_id=egpportalcontractorselectionv2_WAR_egpportalcontractorselectionv2&p_p_lifecycle=0&p_p_state=normal&p_p_mode=view&_egpportalcontractorselectionv2_WAR_egpportalcontractorselectionv2_render=detail-v2&type=es-plan-project-p&stepCode=plan-step-1&id=b6a23c86-b17c-4041-bd35-a02f62f9eaa4&planNo=PL2400007369"
    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#tender-notice > div > div'):
            attachments_data = attachments()
        # Onsite Field -Quyết định phê duyệt
        # Onsite Comment -None

            try:
                attachments_data.file_name = page_details1.find_element(By.XPATH, '//*[contains(text(),'Quyết định phê duyệt')]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Quyết định phê duyệt
        # Onsite Comment -None

            try:
                attachments_data.file_description = page_details1.find_element(By.XPATH, '//*[contains(text(),'Quyết định phê duyệt')]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in file_description: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Quyết định phê duyệt
        # Onsite Comment -None

            attachments_data.external_url = page_details1.find_element(By.XPATH, '//*[contains(text(),'Quyết định phê duyệt')]//following::div[1]').get_attribute('href')

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass


        
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_url) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_details = fn.init_chrome_driver(arguments) 
page_details1 = fn.init_chrome_driver(arguments)
page_main = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://muasamcong.mpi.gov.vn/en/web/guest"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,50):
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

            if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                break

            try:   
                next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                page_main.execute_script("arguments[0].click();",next_page)
                logging.info("Next page")
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="bid-closed"]/div'),page_check))
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
    page_details.quit() 
    
    page_details1.quit()
    
    output_json_file.copyFinalJSONToServer(output_json_folder)