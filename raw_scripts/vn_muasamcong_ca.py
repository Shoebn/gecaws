
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

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "vn_muasamcong_ca"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()


##---------------------------------------------------------------------********************************************************************-----------------------------------------------------

#     NOTE- after clicking on "Tìm kiếm nâng cao", "div.content__search__body > a >>>>>>>> select "Thời gian đăng tải" and "Thời điểm đóng thầu" dates                                                       
#     NOTE- " select "Tìm theo :" >>>    >>>Biên bản mở hồ sơ quan tâm /  Biên bản mở sơ tuyển ---- as notice_type "7" >>>"Tìm kiếm"..... if tender page redirects to the main page click on " div > button > p","Search"

##---------------------------------------------------------------------********************************************************************-----------------------------------------------------    

    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.script_name = 'vn_muasamcong_ca'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'VI'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'VND'

    # Onsite Field -None
    # Onsite Comment -None
    notice_data.document_type_description = Biên bản mở hồ sơ quan tâm ,  Biên bản mở sơ tuyển
    
    # Onsite Field -Trong nước/ Quốc tế
    # Onsite Comment -if "NCB  = Trong nước = "0",    "ICB = Quốc tế = " 1 "

    try:
        notice_data.procurement_method = page_details.find_element(By.XPATH, '//*[contains(text(),'Trong nước/ Quốc tế')]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in procurement_method: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'VN'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -after clicking on "Tìm kiếm nâng cao", "div.content__search__body > a" select "Tìm theo :" >>>Biên bản mở hồ sơ quan tâm /  Biên bản mở sơ tuyển -- as notice_type "7"
    # Onsite Comment -in page_detail if "version /Phiên bản thay đổi" >>>> have "01" in the dropdown list then take it as notice_type = "16"
    notice_data.notice_type = 7
    
    # Onsite Field -Ngày đăng tải thông báo : / Date of publishing of notice :
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
    
    # Onsite Field -Mã định danh / ID 
    # Onsite Comment -click on "Biên bản mở sơ tuyển" for notice_no

    try:
        notice_data.notice_no = page_details.find_element(By.CSS_SELECTOR, '#tab2 table > tbody > tr > td:nth-child(1)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -split till "Bên mời thầu :"

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-md-8.content__body__left__item__infor__contract   h5').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Mã TBMST / Invitation for prequalification no
    # Onsite Comment -None

    try:
        notice_data.related_tender_id = tender_html_element.find_element(By.CSS_SELECTOR, 'div.justify-content-between.align-items-center  p').text
    except Exception as e:
        logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Lĩnh vực / Procurement category :
    # Onsite Comment -Map Supply - Hàng hóa, Works - Xây lắp, Non-consulting - Phi tư vấn, Consulting - Tư vấn,

    try:
        notice_data.notice_contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-md-4 h6:nth-child(1)').text
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Lĩnh vực / Procurement category :
    # Onsite Comment -None

    try:
        notice_data.contract_type_actual = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-md-4 h6:nth-child(1)').text
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Hiệu lực HSDST / Validity of application form (Days)
    # Onsite Comment -None

    try:
        notice_data.contract_duration = page_details.find_element(By.XPATH, '//*[contains(text(),'Hiệu lực HSDST')]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass
    

    # Onsite Field -Dự toán gói thầu / Estimated price :
    # Onsite Comment -ref url "https://muasamcong.mpi.gov.vn/en/web/guest/contractor-selection?p_p_id=egpportalcontractorselectionv2_WAR_egpportalcontractorselectionv2&p_p_lifecycle=0&p_p_state=normal&p_p_mode=view&_egpportalcontractorselectionv2_WAR_egpportalcontractorselectionv2_render=detail-v2&type=es-notify-contractor&stepCode=notify-contractor-step-2-kqmt&id=4e93e3e9-771f-49fe-860a-4996e5ba9c57&notifyId=4e93e3e9-771f-49fe-860a-4996e5ba9c57&inputResultId=undefined&bidOpenId=b1e1b2cf-5324-437e-a628-24567e45c4fd&techReqId=undefined&bidPreNotifyResultId=undefined&bidPreOpenId=undefined&processApply=LDT&bidMode=1_MTHS&notifyNo=IB2400020736&planNo=PL2400012728&pno=undefined&step=bbmt&isInternet=1&caseKHKQ=undefined"

    try:
        notice_data.est_amount = page_details.find_element(By.XPATH, '//*[contains(text(),'Giá gói thầu')]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Giá gói thầu / Procurement package’s estimated price
    # Onsite Comment -None

    try:
        notice_data.netbudgetlc = page_details.find_element(By.XPATH, '//*[contains(text(),'Giá gói thầu')]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in netbudgetlc: {}".format(type(e).__name__))
        pass


    # Onsite Field -Dự toán gói thầu / Estimated price :
    # Onsite Comment -ref url "https://muasamcong.mpi.gov.vn/en/web/guest/contractor-selection?p_p_id=egpportalcontractorselectionv2_WAR_egpportalcontractorselectionv2&p_p_lifecycle=0&p_p_state=normal&p_p_mode=view&_egpportalcontractorselectionv2_WAR_egpportalcontractorselectionv2_render=detail-v2&type=es-notify-contractor&stepCode=notify-contractor-step-2-kqmt&id=4e93e3e9-771f-49fe-860a-4996e5ba9c57&notifyId=4e93e3e9-771f-49fe-860a-4996e5ba9c57&inputResultId=undefined&bidOpenId=b1e1b2cf-5324-437e-a628-24567e45c4fd&techReqId=undefined&bidPreNotifyResultId=undefined&bidPreOpenId=undefined&processApply=LDT&bidMode=1_MTHS&notifyNo=IB2400020736&planNo=PL2400012728&pno=undefined&step=bbmt&isInternet=1&caseKHKQ=undefined"

    try:
        notice_data.grossbudgetlc = page_details.find_element(By.XPATH, '//*[contains(text(),'Giá gói thầu')]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Tên dự án / Project name
    # Onsite Comment -None

    try:
        notice_data.notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),'Tên dự án')]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),'Tên dự án')]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -if present take data  from following tabs "Hồ sơ mời thầu",  "Làm rõ HSMT",  "Hội nghị tiền đấu thầu",  "Kiến nghị"
    # Onsite Comment -# Onsite Comment -along with notice text (page detail) also take data from tender_html_element  (main page) ----"//*[@id="bid-closed"]/div/div"
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.d-flex > div.tab-content').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-md-8.content__body__left__item__infor__contract a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in None.find_elements(By.None, 'None'):
            customer_details_data = customer_details()
        # Onsite Field -Bên mời thầu / Procuring Entity :
        # Onsite Comment -None

            try:
                customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-md-8.content__body__left__item__infor__contract__other > h6:nth-child(1) > span').text
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

        # Onsite Field -Địa điểm / Location :
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
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in None.find_elements(By.None, 'None'):
            lot_details_data = lot_details()
        # Onsite Field -None
        # Onsite Comment -None

            try:
                lot_details_data.lot_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-md-8.content__body__left__item__infor__contract   h5').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Tên dự án / Project name
        # Onsite Comment -None

            try:
                lot_details_data.lot_description = page_details.find_element(By.XPATH, '//*[contains(text(),'Tên dự án')]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Lĩnh vực / Procurement category :
        # Onsite Comment -Map Supply - Hàng hóa, Works - Xây lắp, Non-consulting - Phi tư vấn, Consulting - Tư vấn,

            try:
                lot_details_data.contract_type = page_details.find_element(By.CSS_SELECTOR, 'div.col-md-4 h6:nth-child(1)').text
            except Exception as e:
                logging.info("Exception in contract_type: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Lĩnh vực / Procurement category :
        # Onsite Comment -None

            try:
                lot_details_data.lot_contract_type_actual = page_details.find_element(By.CSS_SELECTOR, 'div.col-md-4 h6:nth-child(1)').text
            except Exception as e:
                logging.info("Exception in lot_contract_type_actual: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -click on "Biên bản mở sơ tuyển" for award details

            try:
                for single_record in page_details.find_elements(By.CSS_SELECTOR, '#tab2 > div.card.border--none.card-expand'):
                    award_details_data = award_details()
		
                    # Onsite Field - Tên nhà thầu	/  Bidder's name
                    # Onsite Comment -click on "Biên bản mở sơ tuyển" for award details

                    award_details_data.bidder_name = page_details.find_element(By.CSS_SELECTOR, ' tbody > tr > td:nth-child(2)').text
			
                    # Onsite Field -Hiệu lực HSDST (Ngày) / Validity of application form (Days)	
                    # Onsite Comment -click on "Biên bản mở sơ tuyển" for award details

                    award_details_data.contract_duration = page_details.find_element(By.CSS_SELECTOR, ' tbody > tr > td:nth-child(3)').text
			
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




# Onsite Field -click on "Thông báo mời thầu / Invitation to Bid ">>>>>>>>> "Hồ sơ mời thầu / Bidding Documents" for attachment data  
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.d-flex > div.tab-content'):
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

    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_url) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_details = fn.init_chrome_driver(arguments) 
page_main = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://muasamcong.mpi.gov.vn/en/web/guest/home"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,10):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="bid-closed"]/div/div'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="bid-closed"]/div/div')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="bid-closed"]/div/div')))[records]
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="bid-closed"]/div/div'),page_check))
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
    
    output_json_file.copyFinalJSONToServer(output_json_folder)
    