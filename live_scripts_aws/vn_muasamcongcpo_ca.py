from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "vn_muasamcongcpo_ca"
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

##---------------------------------------------------------------------********************************************************************-----------------------------------------------------

#     NOTE- after clicking on "Tìm kiếm nâng cao", "div.content__search__body > a >>>>>>>> select "Thời gian đăng tải" and "Thời điểm đóng thầu" dates                                                       
#     NOTE- " select "Tìm theo :" >>>    >>>   Kết quả sơ tuyển /   Results of prequalification opening , Kết quả mời quan tâm / Results of consultant prequalification opening   -- as notice_type "7" >>>"Tìm kiếm"..... if tender page redirects to the main page click on ,"Search"

##---------------------------------------------------------------------********************************************************************-----------------------------------------------------    

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
tnotice_count = 0
SCRIPT_NAME = "vn_muasamcongcpo_ca"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    global tnotice_count
    notice_data = tender()

    notice_data.script_name = 'vn_muasamcong_ca'

    notice_data.main_language = 'VI'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'VN'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'VND'
    
    # Onsite Field -after clicking on "Tìm kiếm nâng cao", "div.content__search__body > a" select "Tìm theo :" >>>Biên bản mở hồ sơ quan tâm /  Biên bản mở sơ tuyển -- as notice_type "7"
    # Onsite Comment -in page_detail if "version /Phiên bản thay đổi" >>>> have "01" in the dropdown list then take it as notice_type = "16"
    notice_data.notice_type = 7

    notice_data.document_type_description = 'Kết quả sơ tuyển , Kết quả mời quan tâm'
    
    
    # Onsite Field -Mã TBMT : / Invitation to Bid No 
    # Onsite Comment --also take notice_no from notice url

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

    # Onsite Comment --also take notice_no from notice url
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div.d-flex.justify-content-between.align-items-center > p').text.split(':')[1].strip()
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-md-8.content__body__left__item__infor__contract   h5').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Lĩnh vực / Procurement category :
    # Onsite Comment -Map Supply - Hàng hóa, Works - Xây lắp, Non-consulting - Phi tư vấn, Consulting - Tư vấn,
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
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_language = 'VI'
        customer_details_data.org_country = 'VN'

        # Onsite Field -Bên mời thầu / Procuring Entity :
        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div.row > div.col-md-8.content__body__left__item__infor__contract > div > div.col-md-8.content__body__left__item__infor__contract__other').text.split('Bên mời thầu :')[1].strip()        
        # Onsite Field -Địa điểm / Location    ---------- split data from "Địa điểm :" till "-"
        # Onsite Comment -if keyword such as "Thành" is present in data then take  data in org_city
        try:
            org_city = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-md-4.content__body__left__item__infor__contract__other').text
            if "Thành" in org_city:
                customer_details_data.org_city = "Thành"
            else:
                pass
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass

        # Onsite Field -Địa điểm / Location :
        # Onsite Comment -if keyword such as "Huyện" is present in data then take  data in org_state
        try:
            org_state = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-md-4.content__body__left__item__infor__contract__other').text
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
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-md-8.content__body__left__item__infor__contract a').get_attribute("href")    
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
        
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
            procurement_method = page_details.find_element(By.XPATH, "//*[contains(text(),'Trong nước/ Quốc tế')]//following::div[1]").text
            if 'Trong nước' in procurement_method:
                notice_data.procurement_method = 0
            elif 'Quốc tế' in procurement_method:
                notice_data.procurement_method = 1
        except Exception as e:
            logging.info("Exception in procurement_method: {}".format(type(e).__name__))
            pass

        # Onsite Field -Thời gian thực hiện
        try:
            notice_data.contract_duration = page_details.find_element(By.XPATH, "//*[contains(text(),'Thời gian thực hiện ')]//following::div[1]").text
        except Exception as e:
            logging.info("Exception in contract_duration: {}".format(type(e).__name__))
            pass

        
        # Onsite Field -Tên dự toán mua sắm / Tên dự án
        try:
            notice_data.local_description = page_details.find_element(By.XPATH, "//*[contains(text(),'Tên dự')]//following::div[1]").text
            notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
        except Exception as e:
            logging.info("Exception in local_description: {}".format(type(e).__name__))
            pass

        try: 
            no_types = page_details.find_element(By.CSS_SELECTOR, 'div:nth-child(3) > div:nth-child(2) > span > select')
            count = 0
            for no in no_types.find_elements(By.CSS_SELECTOR, 'option'):
                count += 1
            if count > 1:
                notice_data.notice_type = 16
            else:
                notice_data.notice_type = 7
            time.sleep(5)
        except:
            pass
        
        try:
            est_amount = page_details.find_element(By.XPATH, "//*[contains(text(),' Giá gói thầu')]//following::div[1]").text
            est_amount = re.sub("[^\d\.\,]","",est_amount)
            notice_data.est_amount =float(est_amount.replace('.','').replace(',','.').strip())
            notice_data.netbudgetlc = notice_data.est_amount
        except Exception as e:
            logging.info("Exception in est_amount: {}".format(type(e).__name__))
            pass
        # Onsite Field -ref url - "https://muasamcong.mpi.gov.vn/vi/web/guest/contractor-selection?p_p_id=egpportalcontractorselectionv2_WAR_egpportalcontractorselectionv2&p_p_lifecycle=0&p_p_state=normal&p_p_mode=view&_egpportalcontractorselectionv2_WAR_egpportalcontractorselectionv2_render=detail-v2&type=es-notify-contractor&stepCode=notify-contractor-step-2-kqmt&id=ac39e99b-d497-4570-9dfc-8c32574b4083&notifyId=ac39e99b-d497-4570-9dfc-8c32574b4083&inputResultId=undefined&bidOpenId=27cd8a24-5367-481c-af71-8c21dd15303c&techReqId=undefined&bidPreNotifyResultId=undefined&bidPreOpenId=undefined&processApply=LDT&bidMode=1_MTHS&notifyNo=IB2400021229&planNo=PL2400005207&pno=undefined&step=bbmt&isInternet=1&caseKHKQ=undefined"
        # Onsite Comment -click on "Thời gian thực hiện gói thầu"  use following selector"#bidOpeningMinutes   path:nth-child(1)"         
    except:
        pass
    
    try:
        lot_details_data = lot_details()
        lot_details_data.lot_title = notice_data.local_title
        notice_data.is_lot_default = True
        lot_details_data.lot_title_english = notice_data.notice_title
        lot_details_data.contract_type = notice_data.notice_contract_type
        lot_details_data.lot_contract_type_actual = notice_data.contract_type_actual
        lot_details_data.lot_number = 1
        award_click = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.XPATH,"(//*[contains(text(),'Kết quả lựa chọn danh sách ngắn')]//parent::a[1])[1]")))
        page_details.execute_script("arguments[0].click();",award_click)
        time.sleep(6)
        WebDriverWait(page_details, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#tab3 > div.card.border--none.card-expand > div.card-body.item-table > table > tbody > tr'))).text
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#tab3 > div.card.border--none.card-expand > div.card-body.item-table > table > tbody > tr'):
            award_details_data = award_details()

            # Onsite Field -Tên nhà thầu / Bidder's name	
            # Onsite Comment -None

            award_details_data.bidder_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
            if award_details_data.bidder_name != None and award_details_data.bidder_name != '':
                award_details_data.award_details_cleanup()
                lot_details_data.award_details.append(award_details_data)

        if lot_details_data.award_details !=[]:
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except:
        pass
        
    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
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
        
        close_popup = WebDriverWait(page_main, 60).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#popup-close')))
        page_main.execute_script("arguments[0].click();",close_popup)
        
        Tìm_kiếm_nâng_ca_click = WebDriverWait(page_main, 60).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'div.content__wrapper__header > div.content__search__body > a > button')))
        page_main.execute_script("arguments[0].click();",Tìm_kiếm_nâng_ca_click)
        time.sleep(5)
        
        list_index = [9,10]
        for index in list_index:
            
            click = WebDriverWait(page_main, 100).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="search-advantage-haunt"]/div/div/div/div/div/div[2]/div[2]/div[2]/div/div/div/div/div')))
            page_main.execute_script("arguments[0].click();",click)
            time.sleep(4)
                                                    
            click = page_main.find_elements(By.CSS_SELECTOR, "div.ant-select-dropdown-content > ul > li")[index]
            click.click()
            time.sleep(5)
                
            Tìm_kiếm_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#search-advantage-haunt > div > div > div > div > div > div.content__footer > button:nth-child(2)')))
            page_main.execute_script("arguments[0].click();",Tìm_kiếm_click)
            time.sleep(5)
            
            try:
                for page_no in range(1,4):
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

                        if notice_count == 10:
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
            except:
                logging.info("No new record")
                pass
     
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
