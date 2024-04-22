from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "vn_pvgas"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from selenium import webdriver
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from deep_translator import GoogleTranslator
from gec_common import functions as fn
from selenium.webdriver.common.action_chains import ActionChains

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "vn_pvgas"
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'vn_pvgas'
    
    notice_data.currency = 'VND'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'VN'
    notice_data.performance_country.append(performance_country_data)
       
    notice_data.main_language = 'VI'
    
    format_types = page_main.find_element(By.CSS_SELECTOR, '#main-container > div > div > div.main > div > div > div > div > div.col-sm-8.col-lg-9 > div > div > h3').text
    
# ************************************************vn_pvgas_spn******************************************************

    if 'THÔNG BÁO MỜI THẦU' in format_types:
        
        notice_data.script_name = 'vn_pvgas_spn'
        
        notice_data.notice_type = 4
        
        notice_data.document_type_description = "BIDDING NOTICES"
    
        try:
            notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(1) > a > span:nth-child(1)').text
            notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
        except Exception as e:
            logging.info("Exception in local_title: {}".format(type(e).__name__))
            pass

        try:  
            notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, ' div > div > div > div.margin-left-85 > div:nth-child(1) > a > span:nth-child(2)').text.split('Mã:')[1].split(')')[0].strip()
        except Exception as e:
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass

        try:
            document_purchase_time = tender_html_element.find_element(By.CSS_SELECTOR, 'div>div>p:nth-child(1)').text
            document_purchase_start_time = GoogleTranslator(source='auto', target='en').translate(document_purchase_time)
            document_purchase_start_time = re.findall('\w+ \d+, \d{4}',document_purchase_start_time)[0]
            notice_data.document_purchase_start_time = datetime.strptime(document_purchase_start_time,'%B %d, %Y').strftime('%Y/%m/%d')
        except Exception as e:
            logging.info("Exception in document_purchase_start_time: {}".format(type(e).__name__))
            pass

        try:
            document_purchase_time = tender_html_element.find_element(By.CSS_SELECTOR, 'div>div>p:nth-child(1)').text
            document_purchase_end_time = GoogleTranslator(source='auto', target='en').translate(document_purchase_time)
            document_purchase_end_time = re.findall('\w+ \d+, \d{4}',document_purchase_end_time)[-1]
            notice_data.document_purchase_end_time = datetime.strptime(document_purchase_end_time,'%B %d, %Y').strftime('%Y/%m/%d')
        except Exception as e:
            logging.info("Exception in document_purchase_end_time: {}".format(type(e).__name__))
            pass

        try:  
            org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div>div>p:nth-child(2)').text.split('Bên mời thầu:')[1].strip()
        except Exception as e:
            logging.info("Exception in org_name: {}".format(type(e).__name__))
            pass

        try:
            notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
        except:
            pass

        try:
            notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div>div>a').get_attribute("href") 
        except Exception as e:
            logging.info("Exception in notice_url: {}".format(type(e).__name__))
            pass

        try:
            fn.load_page(page_details,notice_data.notice_url,80)
            logging.info(notice_data.notice_url)

            try:
                notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#main-container > div > div > div.main > div').get_attribute("outerHTML")                     
            except:
                pass

            try:
                notice_data.category = page_details.find_element(By.XPATH, '(//*[contains(text(),"Danh mục hàng hoá, dịch vụ")]//following::span[1])[2]').text
                category = GoogleTranslator(source='auto', target='en').translate(notice_data.category).strip()
                category = category.lower()
                cpv_codes = fn.CPV_mapping("assets/vn_pvgas_category.csv",category)
                for cpv_code in cpv_codes:
                    cpvs_data = cpvs()
                    cpvs_data.cpv_code = cpv_code
                    cpvs_data.cpvs_cleanup()
                    notice_data.cpvs.append(cpvs_data)
            except Exception as e:
                logging.info("Exception in category: {}".format(type(e).__name__))
                pass

            try:
                notice_data.source_of_funds = page_details.find_element(By.XPATH, '//*[contains(text(),"Nguồn vốn")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in source_of_funds: {}".format(type(e).__name__))
                pass   

            try:
                procurement_method = page_details.find_element(By.XPATH, '//*[contains(text(),"Hình thức lựa chọn nhà thầu")]//following::span[1]').text
                if "Đấu thầu rộng rãi trong nước" in procurement_method:
                    notice_data.procurement_method = 0
                elif "Đấu thầu rộng rãi quốc tế" in procurement_method:
                    notice_data.procurement_method = 1
                else:
                    notice_data.procurement_method = 2
            except Exception as e:
                logging.info("Exception in procurement_method: {}".format(type(e).__name__))
                pass   

            try:
                document_opening_time = page_details.find_element(By.XPATH, '//*[contains(text(),"Thời điểm mở thầu")]//following::span[1]').text
                document_opening_time = re.findall('\d+/\d+/\d{4}',document_opening_time)[0]
                notice_data.document_opening_time = datetime.strptime(document_opening_time,'%d/%m/%Y').strftime('%Y-%m-%d')
            except Exception as e:
                logging.info("Exception in document_opening_time: {}".format(type(e).__name__))
                pass

            try:
                notice_data.document_fee = page_details.find_element(By.XPATH, '//*[contains(text(),"Giá bán 01 bộ HSMT/HSYC")]//following::span[1]').text.split('VNĐ (')[0].strip()
            except Exception as e:
                logging.info("Exception in document_fee: {}".format(type(e).__name__))
                pass

            try:
                earnest_money_deposit = page_details.find_element(By.XPATH, '//*[contains(text(),"Bảo đảm dự thầu")]//following::span[1]').text
                notice_data.earnest_money_deposit = earnest_money_deposit.split('VNĐ (')[0].strip()
            except Exception as e:
                logging.info("Exception in earnest_money_deposit: {}".format(type(e).__name__))
                pass
            
            try:
                currency = page_details.find_element(By.XPATH, '//*[contains(text(),"Bảo đảm dự thầu")]//following::span[1]').text.split('(')[0].strip()
                currency_code = GoogleTranslator(source='auto', target='en').translate(currency)
                currency1 = re.findall("\w+",currency_code)[-1]
                notice_data.currency = currency1.strip()
            except Exception as e:
                logging.info("Exception in currency: {}".format(type(e).__name__))
                pass

            try:
                notice_data.contract_duration = page_details.find_element(By.XPATH, '//*[contains(text(),"Thời gian thực hiện hợp đồng")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in contract_duration: {}".format(type(e).__name__))
                pass

            try:
                notice_deadline = page_details.find_element(By.XPATH, '//*[contains(text(),"Thời điểm đóng thầu")]//following::span[1]').text
                notice_deadline = re.findall('\d+:\d+ ngày \d+/\d+/\d{4}',notice_deadline)[0]
                notice_data.notice_deadline = datetime.strptime(notice_deadline,'%H:%M ngày %d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
            except Exception as e:
                logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
                pass

            try:
                publish_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Thời gian đăng tải")]//following::span[1]').text
                publish_date = re.findall('\d+:\d+ ngày \d+/\d+/\d{4}',publish_date)[0]
                notice_data.publish_date = datetime.strptime(publish_date,'%H:%M ngày %d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
                logging.info(notice_data.publish_date)
            except Exception as e:
                logging.info("Exception in publish_date: {}".format(type(e).__name__))
                pass

            if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                return

            try:
                notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Mô tả tóm tắt về nội dung gói thầu")]//following::div[1]').text
                notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
            except Exception as e:
                logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
                pass

            try:              
                customer_details_data = customer_details()
                customer_details_data.org_name = org_name
                customer_details_data.org_country = 'VN'
                customer_details_data.org_language = 'VI'

                try:
                    customer_details_data.contact_person= page_details.find_element(By.XPATH, '//*[contains(text(),"Người liên hệ")]//following::span[1]').text
                except Exception as e:
                    logging.info("Exception in contact_person: {}".format(type(e).__name__))
                    pass

                try:
                    customer_details_data.org_phone= page_details.find_element(By.XPATH, '//*[contains(text(),"Số điện thoại")]//following::span[1]').text
                except Exception as e:
                    logging.info("Exception in org_phone: {}".format(type(e).__name__))
                    pass

                try:
                    customer_details_data.org_email= page_details.find_element(By.XPATH, '//*[contains(text(),"Email")]//following::span[1]').text
                except Exception as e:
                    logging.info("Exception in org_email: {}".format(type(e).__name__))
                    pass

                try:
                    customer_details_data.org_address= page_details.find_element(By.XPATH, '//*[contains(text(),"Địa chỉ")]//following::span[1]').text
                except Exception as e:
                    logging.info("Exception in org_address: {}".format(type(e).__name__))
                    pass

                customer_details_data.customer_details_cleanup()
                notice_data.customer_details.append(customer_details_data)
            except Exception as e:
                logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
                pass

        except Exception as e:
            logging.info("Exception in notice_url: {}".format(type(e).__name__))
            pass
        
        
# *************************************************vn_pvgas_ca******************************************************
        
    elif 'KẾT QUẢ ĐẤU THẦU' in format_types:
                
        notice_data.script_name = 'vn_pvgas_ca'
        
        notice_data.notice_type = 7
        
        notice_data.document_type_description = "RESULT SELECTION OF CONTRACTORS"
        
        try:
            currency = tender_html_element.find_element(By.CSS_SELECTOR, 'p:nth-child(4) > label > span').text.split('(')[0].strip()
            currency_code = GoogleTranslator(source='auto', target='en').translate(currency)
            currency1 = re.findall("\w+",currency_code)[-1]
            notice_data.currency = currency1.strip()
        except Exception as e:
            logging.info("Exception in currency: {}".format(type(e).__name__))
            pass   
            
        try:
            notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(1) > h3 > a > span:nth-child(1)').text
            notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
        except Exception as e:
            logging.info("Exception in local_title: {}".format(type(e).__name__))
            pass

        try:  
            notice_data.related_tender_id = tender_html_element.find_element(By.CSS_SELECTOR, ' div:nth-child(1) > h3 > a > span:nth-child(2)').text.split('Mã:')[1].split(')')[0].strip()
        except Exception as e:
            logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
            pass
        
        try:
            bidder_name =tender_html_element.find_element(By.CSS_SELECTOR, 'p:nth-child(1)').text.split('Đơn vị trúng thầu:')[1].strip()
        except:
            pass
            
        try:
            contract_duration = tender_html_element.find_element(By.CSS_SELECTOR, 'p:nth-child(3)').text.split('Thời gian thực hiện hợp đông:')[1].split('\n')[0].strip()
        except Exception as e:
            logging.info("Exception in contract_duration: {}".format(type(e).__name__))
            pass

        try:
            grossawardvaluelc1 = tender_html_element.find_element(By.CSS_SELECTOR, ' p:nth-child(4) > label > span').text.split('(')[0].strip()
        except Exception as e:
            logging.info("Exception in grossawardvaluelc: {}".format(type(e).__name__))
            pass  
        
        try:
            notice_data.contract_duration = tender_html_element.find_element(By.CSS_SELECTOR, 'p:nth-child(3)').text.split('Thời gian thực hiện hợp đông:')[1].split('\n')[0].strip()
        except Exception as e:
            logging.info("Exception in contract_duration: {}".format(type(e).__name__))
            pass
        
        try:
            publish_date = tender_html_element.find_element(By.CSS_SELECTOR, ' div.row > div > div > p > label > span').text
            publish_date = re.findall('\d+:\d+ ngày \d+/\d+/\d{4}',publish_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date,'%H:%M ngày %d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.publish_date)
        except Exception as e:
            logging.info("Exception in publish_date: {}".format(type(e).__name__))
            pass
        
        if notice_data.publish_date is not None and notice_data.publish_date < threshold:
            return 
        
        try:
            notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
        except:
            pass

        try:
            notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(1) > h3 > a').get_attribute("href") 
        except Exception as e:
            logging.info("Exception in notice_url: {}".format(type(e).__name__))
            pass

        try:
            fn.load_page(page_details,notice_data.notice_url,80)
            logging.info(notice_data.notice_url)

            try:
                notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#main-container > div > div > div.main > div > div').get_attribute("outerHTML")                     
            except:
                pass 
            
            try:
                lot_details_data = lot_details()
                lot_details_data.lot_number = 1

                lot_details_data.lot_title = notice_data.local_title
                notice_data.is_lot_default = True
                lot_details_data.lot_title_english=notice_data.notice_title

                award_details_data = award_details()
                award_details_data.bidder_name =bidder_name

                try:
                    award_details_data.contract_duration = contract_duration
                except Exception as e:
                    logging.info("Exception in contract_duration: {}".format(type(e).__name__))
                    pass

                try:
                    grossawardvaluelc = grossawardvaluelc1
                    grossawardvaluelc = re.sub("[^\d\.\,]","",grossawardvaluelc)
                    award_details_data.grossawardvaluelc =float(grossawardvaluelc.replace('.','').strip())
                except Exception as e:
                    logging.info("Exception in grossawardvaluelc: {}".format(type(e).__name__))
                    pass

                try:
                    award_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Ngày phê duyệt")]//following::span[1]').text
                    award_date = re.findall('\d+/\d+/\d{4}',award_date)[0]
                    award_details_data.award_date = datetime.strptime(award_date,'%d/%m/%Y').strftime('%Y/%m/%d')
                except Exception as e:
                    logging.info("Exception in award_date: {}".format(type(e).__name__))
                    pass

                award_details_data.award_details_cleanup()
                lot_details_data.award_details.append(award_details_data)

                if lot_details_data.award_details != []:
                    lot_details_data.lot_details_cleanup()
                    notice_data.lot_details.append(lot_details_data) 
            except Exception as e:
                logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
                pass   
            
            try:  
                org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Bên mời thầu")]//following::span[1]').text.strip()
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
            
            try:
                notice_data.category = page_details.find_element(By.XPATH, '(//*[contains(text(),"Danh mục hàng hoá, dịch vụ")]//following::span[1])[2]').text
                category = GoogleTranslator(source='auto', target='en').translate(notice_data.category).strip()
                category = category.lower()
                cpv_codes = fn.CPV_mapping("assets/vn_pvgas_category.csv",category)
                for cpv_code in cpv_codes:
                    cpvs_data = cpvs()
                    cpvs_data.cpv_code = cpv_code
                    cpvs_data.cpvs_cleanup()
                    notice_data.cpvs.append(cpvs_data)
            except Exception as e:
                logging.info("Exception in category: {}".format(type(e).__name__))
                pass

            try:
                notice_url2 = page_details.find_element(By.CSS_SELECTOR, 'div.tender-detail > div > ul > li:nth-child(1) > span > a').get_attribute("href")
                fn.load_page(page_details1,notice_url2,80)
                logging.info(notice_url2)

                try:
                    notice_data.notice_text += page_details1.find_element(By.CSS_SELECTOR, '#main-container > div > div > div.main > div > div').get_attribute("outerHTML")                     
                except:
                    pass 
                
                try:
                    notice_data.source_of_funds = page_details1.find_element(By.XPATH, '//*[contains(text(),"Nguồn vốn")]//following::span[1]').text
                except Exception as e:
                    logging.info("Exception in source_of_funds: {}".format(type(e).__name__))
                    pass 
            
                try:
                    procurement_method = page_details1.find_element(By.XPATH, '//*[contains(text(),"Hình thức lựa chọn nhà thầu")]//following::span[1]').text
                    if "Đấu thầu rộng rãi trong nước" in procurement_method:
                        notice_data.procurement_method = 0
                    elif "Đấu thầu rộng rãi quốc tế" in procurement_method:
                        notice_data.procurement_method = 1
                    else:
                        notice_data.procurement_method = 2
                except Exception as e:
                    logging.info("Exception in procurement_method: {}".format(type(e).__name__))
                    pass   
            
                try:
                    document_opening_time = page_details1.find_element(By.XPATH, '//*[contains(text(),"Thời điểm mở thầu")]//following::span[1]').text
                    document_opening_time = re.findall('\d+/\d+/\d{4}',document_opening_time)[0]
                    notice_data.document_opening_time = datetime.strptime(document_opening_time,'%d/%m/%Y').strftime('%Y-%m-%d')
                except Exception as e:
                    logging.info("Exception in document_opening_time: {}".format(type(e).__name__))
                    pass
                
                try:
                    notice_data.document_fee = page_details1.find_element(By.XPATH, '//*[contains(text(),"Giá bán 01 bộ HSMT/HSYC")]//following::span[1]').text.split('VNĐ (')[0].strip()
                except Exception as e:
                    logging.info("Exception in document_fee: {}".format(type(e).__name__))
                    pass
                
                try:
                    earnest_money_deposit = page_details1.find_element(By.XPATH, '//*[contains(text(),"Bảo đảm dự thầu")]//following::span[1]').text
                    notice_data.earnest_money_deposit = earnest_money_deposit.split('VNĐ (')[0].strip()
                except Exception as e:
                    logging.info("Exception in earnest_money_deposit: {}".format(type(e).__name__))
                    pass
                
                try:
                    notice_data.contract_duration = page_details1.find_element(By.XPATH, '//*[contains(text(),"Thời gian thực hiện hợp đồng")]//following::span[1]').text
                except Exception as e:
                    logging.info("Exception in contract_duration: {}".format(type(e).__name__))
                    pass
                
                try:
                    notice_data.local_description = page_details1.find_element(By.XPATH, '//*[contains(text(),"Mô tả tóm tắt về nội dung gói thầu")]//following::div[1]').text
                    notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
                except Exception as e:
                    logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
                    pass
                
                try:
                    contact_person= page_details1.find_element(By.XPATH, '//*[contains(text(),"Người liên hệ")]//following::span[1]').text
                except Exception as e:
                    logging.info("Exception in contact_person: {}".format(type(e).__name__))
                    pass

                try:
                    org_phone= page_details1.find_element(By.XPATH, '//*[contains(text(),"Số điện thoại")]//following::span[1]').text
                except Exception as e:
                    logging.info("Exception in org_phone: {}".format(type(e).__name__))
                    pass

                try:
                    org_email= page_details1.find_element(By.XPATH, '//*[contains(text(),"Email")]//following::span[1]').text
                except Exception as e:
                    logging.info("Exception in org_email: {}".format(type(e).__name__))
                    pass

                try:
                    org_address= page_details1.find_element(By.XPATH, '//*[contains(text(),"Địa chỉ")]//following::span[1]').text
                except Exception as e:
                    logging.info("Exception in org_address: {}".format(type(e).__name__))
                    pass
               
            except Exception as e:
                logging.info("Exception in notice_url2: {}".format(type(e).__name__)) 
                pass
            
            
            try:              
                customer_details_data = customer_details()
                customer_details_data.org_name = org_name
                customer_details_data.org_country = 'VN'
                customer_details_data.org_language = 'VI'

                try:
                    customer_details_data.contact_person= contact_person
                except Exception as e:
                    logging.info("Exception in contact_person: {}".format(type(e).__name__))
                    pass

                try:
                    customer_details_data.org_phone= org_phone
                except Exception as e:
                    logging.info("Exception in org_phone: {}".format(type(e).__name__))
                    pass

                try:
                    customer_details_data.org_email= org_email
                except Exception as e:
                    logging.info("Exception in org_email: {}".format(type(e).__name__))
                    pass

                try:
                    customer_details_data.org_address= org_address
                except Exception as e:
                    logging.info("Exception in org_address: {}".format(type(e).__name__))
                    pass

                customer_details_data.customer_details_cleanup()
                notice_data.customer_details.append(customer_details_data)
            except Exception as e:
                logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
                pass
        except Exception as e:
            logging.info("Exception in notice_url: {}".format(type(e).__name__)) 
            pass
                
# ****************************************************vn_pvgas_pp******************************************************
        
    elif 'KẾ HOẠCH LỰA CHỌN NHÀ THẦU' in format_types:
        
        
        notice_data.script_name = 'vn_pvgas_pp'
        
        notice_data.notice_type = 3
        
        notice_data.document_type_description = "PLAN SELECTION OF CONTRACTORS"      
                
        try:
            notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(1) > h3 > a > span:nth-child(1)').text
            notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
        except Exception as e:
            logging.info("Exception in local_title: {}".format(type(e).__name__))
            pass      
                
        try:  
            notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, ' div:nth-child(1) > h3 > a > span:nth-child(2)').text.split('Mã:')[1].split(')')[0].strip()
        except Exception as e:
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass       
          
        try:
            est_amount = tender_html_element.find_element(By.CSS_SELECTOR, 'p:nth-child(1) > label > span').text.split('(')[0].strip()
            est_amount = re.sub("[^\d\.\,]","",est_amount)
            notice_data.est_amount =float(est_amount.replace('.','').strip())
            notice_data.grossbudgetlc = notice_data.est_amount
        except Exception as e:
            logging.info("Exception in est_amount: {}".format(type(e).__name__))
            pass
                
        try:
            currency = tender_html_element.find_element(By.CSS_SELECTOR, 'p:nth-child(1) > label > span').text.split('(')[0].strip()
            currency_code = GoogleTranslator(source='auto', target='en').translate(currency)
            currency1 = re.findall("\w{3}",currency_code)[-1]
            notice_data.currency = currency1.strip()
        except Exception as e:
            logging.info("Exception in currency: {}".format(type(e).__name__))
            pass   
        
        try:
            notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
        except:
            pass

        try:
            notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(1) > h3 > a').get_attribute("href") 
        except Exception as e:
            logging.info("Exception in notice_url: {}".format(type(e).__name__))
            pass

        try:
            fn.load_page(page_details,notice_data.notice_url,80)
            logging.info(notice_data.notice_url)
            

            try:
                notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#main-container > div > div > div.main > div > div').get_attribute("outerHTML")                     
            except:
                pass 
        
            try:
                notice_data.source_of_funds = page_details.find_element(By.XPATH, '//*[contains(text(),"Nguồn vốn")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in source_of_funds: {}".format(type(e).__name__))
                pass      
            
            try:
                notice_data.category = page_details.find_element(By.XPATH, '(//*[contains(text(),"Danh mục hàng hoá, dịch vụ")]//following::span[1])[2]').text
                category = GoogleTranslator(source='auto', target='en').translate(notice_data.category).strip()
                category = category.lower()
                cpv_codes = fn.CPV_mapping("assets/vn_pvgas_category.csv",category)
                for cpv_code in cpv_codes:
                    cpvs_data = cpvs()
                    cpvs_data.cpv_code = cpv_code
                    cpvs_data.cpvs_cleanup()
                    notice_data.cpvs.append(cpvs_data)
            except Exception as e:
                logging.info("Exception in category: {}".format(type(e).__name__))
                pass
                
            try:
                customer_details_data = customer_details()
                customer_details_data.org_country = 'VN'
                customer_details_data.org_language = 'VI'
                customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Bên mời thầu")]//following::span[1]').text.strip()
                customer_details_data.customer_details_cleanup()
                notice_data.customer_details.append(customer_details_data)
            except Exception as e:
                logging.info("Exception in customer_details: {}".format(type(e).__name__))
                pass  
                
            try:
                publish_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Thời gian đăng tải")]//following::span[1]').text
                publish_date = re.findall('\d+:\d+ ngày \d+/\d+/\d{4}',publish_date)[0]
                notice_data.publish_date = datetime.strptime(publish_date,'%H:%M ngày %d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
                logging.info(notice_data.publish_date)
            except Exception as e:
                logging.info("Exception in publish_date: {}".format(type(e).__name__))
                pass

            if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                return 
                
            try:
                procurement_method = page_details.find_element(By.XPATH, '//*[contains(text(),"Hình thức lựa chọn nhà thầu")]//following::span[1]').text
                if "Đấu thầu rộng rãi trong nước" in procurement_method:
                    notice_data.procurement_method = 0
                elif "Đấu thầu rộng rãi quốc tế" in procurement_method:
                    notice_data.procurement_method = 1
                else:
                    notice_data.procurement_method = 2
            except Exception as e:
                logging.info("Exception in procurement_method: {}".format(type(e).__name__))
                pass       
                
            try:
                notice_data.contract_duration = page_details.find_element(By.XPATH, '//*[contains(text(),"Thời gian thực hiện hợp đồng")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in contract_duration: {}".format(type(e).__name__))
                pass   
        except Exception as e:
            logging.info("Exception in notice_url: {}".format(type(e).__name__))
            pass    
        
#'*******************************************vn_pvgas_amd***************************************************************')

    elif 'THÔNG BÁO KHÁC' in format_types:
        
        notice_data.script_name = 'vn_pvgas_amd'
        
        notice_data.notice_type = 16
        
        try:
            notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'a.name-item-list').text.split('(Mã:')[0].strip()
            notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
        except Exception as e:
            logging.info("Exception in local_title: {}".format(type(e).__name__))
            pass

        try:  
            notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'a.name-item-list').text.split('Mã:')[1].split(')')[0].strip()
        except Exception as e:
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass

        try:
            document_purchase_time = tender_html_element.find_element(By.CSS_SELECTOR, 'div.item-listview-content').text.split('Thời gian phát hành:')[1].split('\n')[0].strip()
            document_purchase_start_time = GoogleTranslator(source='auto', target='en').translate(document_purchase_time)
            document_purchase_start_time = re.findall('\w+ \d+, \d{4}',document_purchase_start_time)[0]
            notice_data.document_purchase_start_time = datetime.strptime(document_purchase_start_time,'%B %d, %Y').strftime('%Y/%m/%d')
        except Exception as e:
            logging.info("Exception in document_purchase_start_time: {}".format(type(e).__name__))
            pass
        
        try:
            notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
        except:
            pass

        try:
            notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'a.name-item-list').get_attribute("href") 
        except Exception as e:
            logging.info("Exception in notice_url: {}".format(type(e).__name__))
            pass
        

        try:
            fn.load_page(page_details,notice_data.notice_url,80)
            logging.info(notice_data.notice_url)

            try:
                notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#main-container > div > div > div.main > div > div').get_attribute("outerHTML")                     
            except:
                pass 
            
            try:
                notice_data.document_type_description = page_details.find_element(By.CSS_SELECTOR, ' div.tender-name > h4').text
            except Exception as e:
                logging.info("Exception in document_type_description: {}".format(type(e).__name__))
                pass     
            
            try:
                notice_data.category = page_details.find_element(By.XPATH, '(//*[contains(text(),"Danh mục hàng hoá, dịch vụ")]//following::span[1])[2]').text
                category = GoogleTranslator(source='auto', target='en').translate(notice_data.category).strip()
                category = category.lower()
                cpv_codes = fn.CPV_mapping("assets/vn_pvgas_category.csv",category)
                for cpv_code in cpv_codes:
                    cpvs_data = cpvs()
                    cpvs_data.cpv_code = cpv_code
                    cpvs_data.cpvs_cleanup()
                    notice_data.cpvs.append(cpvs_data)
            except Exception as e:
                logging.info("Exception in category: {}".format(type(e).__name__))
                pass
        
            try:  
                org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Bên mời thầu")]//following::span[1]').text.strip()
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass  
        
            try:
                est_amount = page_details.find_element(By.XPATH, '//*[contains(text(),"Giá gói thầu")]//following::span[1]').text.split('(')[0].strip()
                est_amount = re.sub("[^\d\.\,]","",est_amount)
                notice_data.est_amount =float(est_amount.replace('.','').strip())
                notice_data.grossbudgetlc = notice_data.est_amount
            except Exception as e:
                logging.info("Exception in est_amount: {}".format(type(e).__name__))
                pass

            try:
                currency = page_details.find_element(By.XPATH, '//*[contains(text(),"Giá gói thầu")]//following::span[1]').text.split('(')[0].strip()
                currency_code = GoogleTranslator(source='auto', target='en').translate(currency)
                currency1 = re.findall("\w{3}",currency_code)[-1]
                notice_data.currency = currency1.strip()
            except Exception as e:
                logging.info("Exception in currency: {}".format(type(e).__name__))
                pass   
                
            try:
                document_opening_time = page_details.find_element(By.XPATH, '//*[contains(text(),"Thời điểm mở thầu")]//following::span[1]').text
                document_opening_time = re.findall('\d+/\d+/\d{4}',document_opening_time)[0]
                notice_data.document_opening_time = datetime.strptime(document_opening_time,'%d/%m/%Y').strftime('%Y-%m-%d')
            except Exception as e:
                logging.info("Exception in document_opening_time: {}".format(type(e).__name__))
                pass   
             
            try:
                publish_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Thời gian đăng tải")]//following::span[1]').text
                publish_date = re.findall('\d+:\d+ ngày \d+/\d+/\d{4}',publish_date)[0]
                notice_data.publish_date = datetime.strptime(publish_date,'%H:%M ngày %d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
                logging.info(notice_data.publish_date)
            except Exception as e:
                logging.info("Exception in publish_date: {}".format(type(e).__name__))
                pass

            if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                return
    
            try:               
                for single_record in page_details.find_elements(By.XPATH, '//*[contains(text(),"Quyết định")]//following::span[1]'):
                    attachments_data = attachments()
                    
                    attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'a').text

                    attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'a').get_attribute("href")

                    attachments_data.attachments_cleanup()
                    notice_data.attachments.append(attachments_data)
            except Exception as e:
                logging.info("Exception in attachments: {}".format(type(e).__name__)) 
                pass
            
            try:
                notice_url3 = page_details.find_element(By.CSS_SELECTOR, ' div.tender-detail > div > ul > li> span > a').get_attribute("href")
                fn.load_page(page_details1,notice_url3,80)
                logging.info(notice_url3)

                try:
                    notice_data.notice_text += page_details1.find_element(By.CSS_SELECTOR, '#main-container > div > div > div.main > div > div').get_attribute("outerHTML")                     
                except:
                    pass 
                
                try:
                    notice_data.source_of_funds = page_details1.find_element(By.XPATH, '//*[contains(text(),"Nguồn vốn")]//following::span[1]').text
                except Exception as e:
                    logging.info("Exception in source_of_funds: {}".format(type(e).__name__))
                    pass 
            
                try:
                    procurement_method = page_details1.find_element(By.XPATH, '//*[contains(text(),"Hình thức lựa chọn nhà thầu")]//following::span[1]').text
                    if "Đấu thầu rộng rãi trong nước" in procurement_method:
                        notice_data.procurement_method = 0
                    elif "Đấu thầu rộng rãi quốc tế" in procurement_method:
                        notice_data.procurement_method = 1
                    else:
                        notice_data.procurement_method = 2
                except Exception as e:
                    logging.info("Exception in procurement_method: {}".format(type(e).__name__))
                    pass   
                
                try:
                    notice_data.document_fee = page_details1.find_element(By.XPATH, '//*[contains(text(),"Giá bán 01 bộ HSMT/HSYC")]//following::span[1]').text.split('VNĐ (')[0].strip()
                except Exception as e:
                    logging.info("Exception in document_fee: {}".format(type(e).__name__))
                    pass
                
                try:
                    earnest_money_deposit = page_details1.find_element(By.XPATH, '//*[contains(text(),"Bảo đảm dự thầu")]//following::span[1]').text
                    notice_data.earnest_money_deposit = earnest_money_deposit.split('VNĐ (')[0].strip()
                except Exception as e:
                    logging.info("Exception in earnest_money_deposit: {}".format(type(e).__name__))
                    pass
                
                try:
                    notice_data.contract_duration = page_details1.find_element(By.XPATH, '//*[contains(text(),"Thời gian thực hiện hợp đồng")]//following::span[1]').text
                except Exception as e:
                    logging.info("Exception in contract_duration: {}".format(type(e).__name__))
                    pass
                
                try:
                    document_purchase_end_time = page_details1.find_element(By.XPATH, '//*[contains(text(),"Thời điểm đóng thầu")]//following::span[1]').text
                    document_purchase_end_time = re.findall('\d+/\d+/\d{4}',document_purchase_end_time)[0]
                    notice_data.document_purchase_end_time = datetime.strptime(document_purchase_end_time,'%d/%m/%Y').strftime('%Y/%m/%d')
                except Exception as e:
                    logging.info("Exception in document_purchase_end_time: {}".format(type(e).__name__))
                    pass  

                try: 
                    notice_deadline = page_details1.find_element(By.XPATH, '//*[contains(text(),"Thời điểm đóng thầu")]//following::span[1]').text
                    notice_deadline = re.findall('\d+:\d+ ngày \d+/\d+/\d{4}',notice_deadline)[0]
                    notice_data.notice_deadline = datetime.strptime(notice_deadline,'%H:%M ngày %d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
                except Exception as e:
                    logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
                    pass   
                        
                try:
                    contact_person= page_details1.find_element(By.XPATH, '//*[contains(text(),"Người liên hệ")]//following::span[1]').text
                except Exception as e:
                    logging.info("Exception in contact_person: {}".format(type(e).__name__))
                    pass

                try:
                    org_phone= page_details1.find_element(By.XPATH, '//*[contains(text(),"Số điện thoại")]//following::span[1]').text
                except Exception as e:
                    logging.info("Exception in org_phone: {}".format(type(e).__name__))
                    pass

                try:
                    org_email= page_details1.find_element(By.XPATH, '//*[contains(text(),"Email")]//following::span[1]').text
                except Exception as e:
                    logging.info("Exception in org_email: {}".format(type(e).__name__))
                    pass

                try:
                    org_address= page_details1.find_element(By.XPATH, '//*[contains(text(),"Địa chỉ")]//following::span[1]').text
                except Exception as e:
                    logging.info("Exception in org_address: {}".format(type(e).__name__))
                    pass

            except Exception as e:
                logging.info("Exception in notice_url3: {}".format(type(e).__name__)) 
                pass
            
            try:              
                customer_details_data = customer_details()
                customer_details_data.org_name = org_name
                customer_details_data.org_country = 'VN'
                customer_details_data.org_language = 'VI'

                try:
                    customer_details_data.contact_person= contact_person
                except Exception as e:
                    logging.info("Exception in contact_person: {}".format(type(e).__name__))
                    pass

                try:
                    customer_details_data.org_phone= org_phone
                except Exception as e:
                    logging.info("Exception in org_phone: {}".format(type(e).__name__))
                    pass

                try:
                    customer_details_data.org_email= org_email
                except Exception as e:
                    logging.info("Exception in org_email: {}".format(type(e).__name__))
                    pass

                try:
                    customer_details_data.org_address= org_address
                except Exception as e:
                    logging.info("Exception in org_address: {}".format(type(e).__name__))
                    pass

                customer_details_data.customer_details_cleanup()
                notice_data.customer_details.append(customer_details_data)
            except Exception as e:
                logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
                pass
        except Exception as e:
            logging.info("Exception in notice_url: {}".format(type(e).__name__))
            pass 
                
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_url) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title)
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
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments) 
page_details = fn.init_chrome_driver(arguments) 
page_details1 = fn.init_chrome_driver(arguments)
action = ActionChains(page_main)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://tender.pvgas.com.vn/#/tender/package?_k=3ee253","https://tender.pvgas.com.vn/#/tender/result?_k=yu36qy","https://tender.pvgas.com.vn/#/tender/plan?_k=h8kmot","https://tender.pvgas.com.vn/#/orthernotice?_k=dsw44f"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        try:
            for no in range(3,8):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,' div.row.post-detail > div > div:nth-child(1) > div'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.user-card')))
                length = len(rows)                                                                              
                for records in range(0,length):                                                                       
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.user-card')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break


                try:   
                    next_page = page_main.find_element(By.CSS_SELECTOR,"#main-container > div > div > div.main > div > div > div > div > div.col-sm-8.col-lg-9 > div > div > div.cont-paging > div > ul > li:nth-child("+str(no)+")")
                    action.move_to_element(next_page).click().perform()
                    logging.info("Next page")
                    time.sleep(5)
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,' div.row.post-detail > div > div:nth-child(1) > div'),page_check))
                except Exception as e:
                    logging.info("Exception in next_page: {}".format(type(e).__name__))
                    logging.info("No next page")
                    break
        except:
            logging.info("No new record")
            pass
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit()
    page_details1.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)    
