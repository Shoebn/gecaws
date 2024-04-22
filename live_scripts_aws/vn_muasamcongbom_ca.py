
from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "vn_muasamcongbom_ca"
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
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
import gec_common.Doc_Download_VPN

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
tnotice_count = 0
SCRIPT_NAME = "vn_muasamcongbom_ca"
Doc_Download = gec_common.Doc_Download_VPN.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    global tnotice_count
    notice_data = tender()

##---------------------------------------------------------------------********************************************************************-----------------------------------------------------

#     NOTE- after clicking on "Tìm kiếm nâng cao", "div.content__search__body > a >>>>>>>> select "Thời gian đăng tải" and "Thời điểm đóng thầu" dates                                                       
#     NOTE- " select "Tìm theo :" >>>    >>> Biên bản mở thầu -- -- as notice_type "7" >>>"Tìm kiếm"..... if tender page redirects to the main page click on " div > button > p","Search"

##---------------------------------------------------------------------********************************************************************-----------------------------------------------------    

    notice_data.script_name = 'vn_muasamcong_ca'
    
    notice_data.main_language = 'VI'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'VN'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'VND'
    
    notice_data.document_type_description ="Biên bản mở thầu"
    
    # Onsite Comment -in page_detail if "version /Phiên bản thay đổi" >>>> have "01" in the dropdown list then take it as notice_type = "16"
    notice_data.notice_type = 7
    
    # Onsite Field -Thời gian sửa TBMT :
    # Onsite Comment -along with date also grab time  02/02/2024 - 14:17  09/02/2024 - 17:06
    try:
        try:
            publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "h6:nth-child(3)").text  
        except:
            publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "h6:nth-child(2)").text
        
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
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div.justify-content-between.align-items-center  p').text.split(':')[1].strip()
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

        # Onsite Field -Bên mời thầu / Procuring Entity :  #    div.format__text > h6:nth-child(1) > span
        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-md-8 > h6:nth-child(1) > span').text
        # Onsite Field -Địa điểm / Location    ---------- split data from "Địa điểm :" till "-"
        # Onsite Comment -if keyword such as "Thành" is present in data then take  data in org_city
        try:
            customer_details_data.org_city = tender_html_element.find_element(By.CSS_SELECTOR, 'h6.format__text__title > span').text.split('-')[0].strip()
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass

        # Onsite Field -Địa điểm / Location :
        # Onsite Comment -if keyword such as "Huyện" is present in data then take  data in org_state
        try:
            customer_details_data.org_address = tender_html_element.find_element(By.CSS_SELECTOR, 'h6.format__text__title > span').text
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
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
        
        # Onsite Field -if present take data  from following tabs "Hồ sơ mời thầu",  "Làm rõ HSMT",  "Hội nghị tiền đấu thầu",  "Kiến nghị"
        # Onsite Comment -# Onsite Comment -along with notice text (page detail) also take data from tender_html_element  (main page) ----"//*[@id="bid-closed"]/div"
        try:
            notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.d-flex > div.tab-content').get_attribute("outerHTML")                     
        except:
            pass
        
        try:
            notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
        except:
            pass
        
        # Onsite Field -ref url - "https://muasamcong.mpi.gov.vn/vi/web/guest/contractor-selection?p_p_id=egpportalcontractorselectionv2_WAR_egpportalcontractorselectionv2&p_p_lifecycle=0&p_p_state=normal&p_p_mode=view&_egpportalcontractorselectionv2_WAR_egpportalcontractorselectionv2_render=detail-v2&type=es-notify-contractor&stepCode=notify-contractor-step-2-kqmt&id=ac39e99b-d497-4570-9dfc-8c32574b4083&notifyId=ac39e99b-d497-4570-9dfc-8c32574b4083&inputResultId=undefined&bidOpenId=27cd8a24-5367-481c-af71-8c21dd15303c&techReqId=undefined&bidPreNotifyResultId=undefined&bidPreOpenId=undefined&processApply=LDT&bidMode=1_MTHS&notifyNo=IB2400021229&planNo=PL2400005207&pno=undefined&step=bbmt&isInternet=1&caseKHKQ=undefined"
        # Onsite Comment -click on "Thời gian thực hiện gói thầu"  use following selector"#bidOpeningMinutes   path:nth-child(1)"

        try:
            WebDriverWait(page_details, 80).until(EC.presence_of_element_located((By.CSS_SELECTOR,'td:nth-child(9) >span >svg')))
            for single_record in page_details.find_elements(By.CSS_SELECTOR, '#bidOpeningMinutes > div.card.border--none.card-expand > div.card-body.item-table > table > tbody > tr'):            
                try:
                    #('***************** FORMAT 1 **********************')

                    # Onsite Field -Tên nhà thầu	/	Bidder's name
                    bidder_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text

                    # Onsite Field -Giá dự thầu sau giảm giá (nếu có) (VND) / Bid price after discount (if applicable) (VND)
                    # Onsite Comment -None
                    try:
                        netawardvaluelc1 = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
                        netawardvaluelc2 = re.sub("[^\d\.\,]","",netawardvaluelc1)
                        netawardvaluelc =float(netawardvaluelc2.replace('.','').replace(',','.').strip())
                    except:
                        pass
                    
                    try:
                        contract_duration = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(6)').text
                    except:
                        pass
                    
                except Exception as e:
                    logging.info("Exception in award_details: {}".format(type(e).__name__))
                    pass

                click = WebDriverWait(single_record, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'td:nth-child(9) >span >svg'))).click()
                time.sleep(5)
                page_details.switch_to.window(page_details.window_handles[1])
                time.sleep(50)
                
                try:
                    WebDriverWait(page_details, 150).until(EC.presence_of_element_located((By.XPATH,'//*[@id="nestedTableData"]')))
                    try:
                        lot_range = page_details.find_element(By.CSS_SELECTOR, 'div.d-flex.table-egp-dynamic-pagination.ng-star-inserted > div').text.split('trên')[1].strip()
                        #('^^^^^^^^^^^^^^^^^^^^^^^ FORMAT 1 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^')
                        lot_no = int(lot_range)
                        for page_no in range(1,lot_no+1):
                            lot_check = WebDriverWait(page_details, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#nestedTableData > tbody > tr'))).text
                        
                            lot_number = 1
                            for single_record_lot in page_details.find_elements(By.CSS_SELECTOR, '#nestedTableData > tbody > tr'):
                                lot_details_data = lot_details()
                                award_details_data = award_details()
                                lot_details_data.lot_number = lot_number
                                
                                # Onsite Field -Danh mục hàng hoá
                                lot_details_data.lot_title = single_record_lot.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
                                lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)

                                # Onsite Field -Đơn vị tính
                                try:
                                    lot_details_data.lot_quantity_uom = single_record_lot.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
                                except Exception as e:
                                    logging.info("Exception in lot_quantity_uom: {}".format(type(e).__name__))
                                    pass

                                try:
                                    award_details_data.bidder_name = bidder_name

                                    try:
                                        award_details_data.netawardvaluelc = netawardvaluelc
                                    except:
                                        pass
                                    
                                    try:
                                        award_details_data.contract_duration = contract_duration
                                    except:
                                        pass

                                    award_details_data.award_details_cleanup()
                                    lot_details_data.award_details.append(award_details_data)
                                except:
                                    pass
                                lot_details_data.lot_details_cleanup()
                                notice_data.lot_details.append(lot_details_data)
                                lot_number += 1
                            
                            try:
                                select_methodId = Select(page_details.find_element(By.CSS_SELECTOR,' div.d-flex.table-egp-dynamic-pagination.ng-star-inserted > div > div > select'))
                                select_methodId.select_by_index(page_no)
                                logging.info("**** next lots ****")
                                WebDriverWait(page_details, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#nestedTableData > tbody > tr'),lot_check))
                            except:
                                logging.info("No next lots")
                                break
                    except:
                        try:
                            #('^^^^^^^^^^^^^^^^^^^^^^^ FORMAT 2 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^')
                            lot_number = 1
                            for single_record_lot in page_details.find_elements(By.CSS_SELECTOR, '#nestedTableData > tbody > tr'):
                                lot_details_data = lot_details()
                                award_details_data = award_details()
                                lot_details_data.lot_number = lot_number
                                
                                # Onsite Field -Danh mục hàng hoá
                                lot_details_data.lot_title = single_record_lot.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
                                lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)

                                # Onsite Field -Đơn vị tính
                                try:
                                    lot_details_data.lot_quantity_uom = single_record_lot.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
                                except Exception as e:
                                    logging.info("Exception in lot_quantity_uom: {}".format(type(e).__name__))
                                    pass

                                try:
                                    award_details_data.bidder_name = bidder_name

                                    try:
                                        award_details_data.netawardvaluelc = netawardvaluelc
                                    except:
                                        pass
                                        
                                    try:
                                        award_details_data.contract_duration = contract_duration
                                    except:
                                        pass

                                    award_details_data.award_details_cleanup()
                                    lot_details_data.award_details.append(award_details_data)
                                except:
                                    pass
                                lot_details_data.lot_details_cleanup()
                                notice_data.lot_details.append(lot_details_data)
                                lot_number += 1
                        except:
                            pass
                except:
                    try:
                        lot_details_data = lot_details()
                        lot_details_data.lot_title = notice_data.local_title
                        notice_data.is_lot_default = True
                        lot_details_data.lot_title_english = notice_data.notice_title
                        lot_details_data.contract_type = notice_data.notice_contract_type
                        lot_details_data.lot_contract_type_actual = notice_data.contract_type_actual
                        lot_details_data.lot_number = 1
                        award_details_data = award_details()
                        award_details_data.bidder_name = bidder_name

                        try:
                            award_details_data.netawardvaluelc = netawardvaluelc
                        except:
                            pass
                        
                        try:
                            award_details_data.contract_duration = contract_duration
                        except:
                            pass

                        award_details_data.award_details_cleanup()
                        lot_details_data.award_details.append(award_details_data)
                        
                        if lot_details_data.award_details !=[]:
                            lot_details_data.lot_details_cleanup()
                            notice_data.lot_details.append(lot_details_data)
                    except:
                        pass
                page_details.close()
                time.sleep(2)
                page_details.switch_to.window(page_details.window_handles[0])
                time.sleep(10)
        except:
            try:   
                #('*********************** FORMAT 2 ***********************')
                for single_record in page_details.find_elements(By.CSS_SELECTOR, '#bidOpeningMinutes > div.card.border--none.card-expand > div.card-body.item-table > table > tbody > tr'):
                    lot_details_data = lot_details()
                    lot_details_data.lot_title = notice_data.local_title
                    notice_data.is_lot_default = True
                    lot_details_data.lot_title_english = notice_data.notice_title
                    lot_details_data.contract_type = notice_data.notice_contract_type
                    lot_details_data.lot_contract_type_actual = notice_data.contract_type_actual
                    lot_details_data.lot_number = 1
                    award_details_data = award_details()

                    # Onsite Field -Tên nhà thầu	/	Bidder's name
                    award_details_data.bidder_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
                    
                    # Onsite Field -Giá dự thầu sau giảm giá (nếu có) (VND) / Bid price after discount (if applicable) (VND)
                    try:
                        netawardvaluelc = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
                        netawardvaluelc = re.sub("[^\d\.\,]","",netawardvaluelc)
                        award_details_data.netawardvaluelc =float(netawardvaluelc.replace('.','').replace(',','.').strip())
                    except:
                        pass
                    
                    try:
                        award_details_data.contract_duration = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(6)').text
                    except:
                        pass
                    
                    award_details_data.award_details_cleanup()
                    lot_details_data.award_details.append(award_details_data)

                    if lot_details_data.award_details != []:
                        lot_details_data.lot_details_cleanup()
                        notice_data.lot_details.append(lot_details_data)
            except Exception as e:
                logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
                pass
        
#**************************************************************************************************************************
        
        try:
            click = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="tender-notice"]/div/div/div[2]/div/div[1]/div[1]/div[2]/ul/li[1]'))).click()
            time.sleep(10)

            # Onsite Field -click on "Thông báo mời thầu"  -------Trong nước/ Quốc tế
            # Onsite Comment -if "NCB  = Trong nước = "0",    "ICB = Quốc tế = " 1 "
            try:
                procurement_method = page_details.find_element(By.XPATH, "//*[contains(text(),'Trong nước/ Quốc tế')]//following::div[1]").text
                if 'Trong nước' in procurement_method:
                    notice_data.procurement_method = 0
                elif 'Quốc tế' in procurement_method:
                    notice_data.procurement_method = 1
            except Exception as e:
                logging.info("Exception in procurement_method: {}".format(type(e).__name__))
                pass

            # Onsite Field -Thời gian thực hiện gói thầu
            try:
                notice_data.contract_duration = page_details.find_element(By.XPATH, "(//*[contains(text(),'Thời gian thực hiện gói thầu')]//following::div[1])[2]").text
            except Exception as e:
                logging.info("Exception in contract_duration: {}".format(type(e).__name__))
                pass

            # Onsite Field -Chi phí nộp e-HSDT / E-bid submission fee
            try:
                document_cost = page_details.find_element(By.XPATH, "//*[contains(text(),'Chi phí nộp e-HSDT')]//following::div[1]").text.split('VND')[0].strip()
                document_cost = re.sub("[^\d\.\,]","",document_cost)
                notice_data.document_cost =float(document_cost.replace('.','').replace(',','.').strip())
            except Exception as e:
                logging.info("Exception in document_cost: {}".format(type(e).__name__))
                pass

            # Onsite Field -Số tiền đảm bảo dự thầu / Bid security amount
            try:
                notice_data.earnest_money_deposit = page_details.find_element(By.XPATH, "//*[contains(text(),'Số tiền đảm bảo dự thầu')]//following::div[1]").text.split('VND')[0].strip()
            except Exception as e:
                logging.info("Exception in earnest_money_deposit: {}".format(type(e).__name__))
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
                
        except:
            pass
        
        # Onsite Field -click on "Thông báo mời thầu / Invitation to Bid ">>>>>>>>> "Hồ sơ mời thầu / Bidding Documents" for attachment data  
        try: 
            click = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="tenderNotice"]/ul/li[2]/a'))).click()
            time.sleep(5)

            attachments_data = attachments()
            
            # Onsite Field -Quyết định phê duyệt  //*[@id="tender-notice"]/div/div/div[2]/div/div[2]/div/div[2]/div/img
            attachments_data.file_name = page_details.find_element(By.CSS_SELECTOR, 'span:nth-child(2) > span').text
            
            # Onsite Field -Quyết định phê duyệt
            try:
                attachments_data.file_description = attachments_data.file_name
            except Exception as e:
                logging.info("Exception in file_description: {}".format(type(e).__name__))
                pass

            # Onsite Field -Quyết định phê duyệt
            attach_click = WebDriverWait(page_details, 150).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'span:nth-child(2) > span')))
            page_details.execute_script("arguments[0].click();",attach_click)
            page_details.switch_to.window(page_details.window_handles[1])
            time.sleep(10)
            
            external_url = WebDriverWait(page_details, 150).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="egp_body"]/ebid-viewer/div[1]/div/div[2]/button[2]')))
            page_details.execute_script("arguments[0].click();",external_url)
            time.sleep(2)
            file_dwn = Doc_Download.file_download()
            attachments_data.external_url = str(file_dwn[0])
            time.sleep(5)
            
            try:
                attachments_data.file_type = attachments_data.external_url.split('.')[-1].strip()
            except Exception as e:
                logging.info("Exception in file_description: {}".format(type(e).__name__))
                pass
                
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
            page_details.close()
            time.sleep(2)
            page_details.switch_to.window(page_details.window_handles[0])
            time.sleep(5)
            
            click = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="tenderNotice"]/ul/li[1]/a'))).click()
            time.sleep(5)
            
        except Exception as e:
            logging.info("Exception in attachments: {}".format(type(e).__name__)) 
            pass
        
#*************************************************************************************************************************
        try:
            click = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="info-general"]/div[3]/div[2]/div[1]/div[2]'))).click()
            time.sleep(5)
            
            # Onsite Field -Dự toán mua sắm / Purchase estimate
            # Onsite Comment -click on "//*[contains(text(),'Mã KHLCNT')]//following::div[1]	" for detail pages1 data
            try:
                est_amount = page_details.find_element(By.XPATH, "//*[contains(text(),'Dự toán mua sắm')]//following::div[1]").text
                est_amount = re.sub("[^\d\.\,]","",est_amount)
                notice_data.est_amount =float(est_amount.replace('.','').replace(',','.').strip())
                notice_data.netbudgetlc = notice_data.est_amount
            except Exception as e:
                logging.info("Exception in est_amount: {}".format(type(e).__name__))
                pass
        except:
            pass
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
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
    urls = ["https://muasamcong.mpi.gov.vn/vi/web/guest/home"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        close_popup = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#popup-close')))
        page_main.execute_script("arguments[0].click();",close_popup)
        
        Tìm_kiếm_nâng_ca_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'div.content__wrapper__header > div.content__search__body > a > button')))
        page_main.execute_script("arguments[0].click();",Tìm_kiếm_nâng_ca_click)
        time.sleep(5)
    
        click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="search-advantage-haunt"]/div/div/div/div/div/div[2]/div[2]/div[2]/div/div/div/div/div')))
        page_main.execute_script("arguments[0].click();",click)
        time.sleep(5)
        
        click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'div.ant-select-dropdown-content > ul > li:nth-child(7)')))
        page_main.execute_script("arguments[0].click();",click)
        time.sleep(5)
                
        Tìm_kiếm_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#search-advantage-haunt > div > div > div > div > div > div.content__footer > button:nth-child(2)')))
        page_main.execute_script("arguments[0].click();",Tìm_kiếm_click)
        time.sleep(5)
        try:
            for page_no in range(1,50): #50
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="bid-closed"]/div[1]'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="bid-closed"]/div')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="bid-closed"]/div')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break

                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
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
                    page_check1 = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="bid-closed"]/div[1]'))).text
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="bid-closed"]/div[1]'),page_check))
                except Exception as e:
                    logging.info("Exception in next_page: {}".format(type(e).__name__))
                    logging.info("No next page")
                    break
        except:
            logging.info("No new record") 
            pass
    logging.info("Finished processing. Scraped {} notices".format(tnotice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit() 
    
    output_json_file.copyFinalJSONToServer(output_json_folder)
    
