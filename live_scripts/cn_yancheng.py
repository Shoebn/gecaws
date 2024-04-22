from gec_common.gecclass import *
import logging
import jsons
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from deep_translator import GoogleTranslator
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "cn_yancheng"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'cn_yancheng'
    
    notice_data.main_language = 'ZH'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'CN'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'CNY'
    
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 4
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'a').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
        notice_data.notice_summary_english = notice_data.notice_title
        notice_data.local_description = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try: #2024-02-09
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "span").text
        notice_data.publish_date = datetime.strptime(publish_date,'%Y-%m-%d').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:
        notice_data.notice_text += tender_html_element.get_attribute("outerHTML")
    except:
        pass
    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except:
        notice_data.notice_url = url
   
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.container.bt-standard16').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    # Onsite Comment -split notice_no after (Item number   项目编号:) or (Purchase number    采购编号:) keyword.
    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, "//*[contains(text(),'项目编号')]//following::span[1]").text
    except:
        try:
            notice_no = page_details.find_element(By.XPATH, "//*[contains(text(),'项目编号')]//parent::span").text
            if "项目编号" in notice_no:
                notice_data.notice_no = notice_no.split("项目编号：")[1].split('\n')[0] 
        except Exception as e:
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass
    

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'CN'
        customer_details_data.org_language = 'ZH'
                 
        # Onsite Comment -split org_name from 	(Purchaser information >> name        "采购人信息  >>  名    称：") or (Purchaser information >> Name   "采购人信息   >>   名称：")
        try:
            org_name = page_details.find_element(By.XPATH, "//*[contains(text(),'采购人信息')]//following::p[1]").text
            if '名    称：' in org_name:
                org_name1 =org_name.split("名    称：")[1].strip()
                customer_details_data.org_name = GoogleTranslator(source='auto', target='en').translate(org_name1) 
            elif '名称：' in org_name:
                org_name1 =org_name.split("名称：")[1].strip()
                customer_details_data.org_name = GoogleTranslator(source='auto', target='en').translate(org_name1) 
            else:
                customer_details_data.org_name = "Yancheng City"
        except Exception as e:
            customer_details_data.org_name = "Yancheng City"
            logging.info("Exception in org_name: {}".format(type(e).__name__))
            pass
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
        
#         in script org_phone field countinuosly varing so unable to grap. 
                
        # Onsite Field -None
        # Onsite Comment -split org_phone from 	(Purchaser information >>  Contact number	   "采购人信息  >>  联系电话：") or (Purchaser information >>  Tel   "采购人信息   >>  联系电话：" or (Purchaser information >> Tel   "采购人信息   >>   电话：" )or (Purchaser information >> Tel     "采购人信息   >>  电    话：")

#         try:
#             org_phone = page_details.find_element(By.CSS_SELECTOR, 'table:nth-child(2)').text
#             if "采购人信息" in org_phone :
#                 try:
#                     org_phone =org_phone.split("联系电话：")[1].split("\n")[0]
#                     customer_details_data.org_phone =re.sub("[^\d\-]","",org_phone)
#                 except:
#                     org_phone =org_phone.split("电    话：")[1].split("\n")[0]
#                     customer_details_data.org_phone =re.sub("[^\d\-]","",org_phone)
#                 try:
#                     org_phone =org_phone.split("电话：")[1].split("\n")[0]
#                     customer_details_data.org_phone =re.sub("[^\d\-]","",org_phone)
#                 except:
#                     pass
#                 print("org_phone : ",customer_details_data.org_phone)


#         except Exception as e:
#             logging.info("Exception in org_phone: {}".format(type(e).__name__))
#             pass

    # in script contact_person field countinuosly varing so unable to grap. 
        
        # Onsite Field -None
        # Onsite Comment -split contact_person from (Purchaser information >>  Contact:    "采购人信息  >>  联 系 人：") or (Purchaser information >>  Project Contact:   "采购人信息   >>  项目联系人：")

#         try:
#             contact_person = page_details.find_element(By.CSS_SELECTOR, 'table:nth-child(2)').text
#             if "采购人信息" in org_phone:
#                 try:
#                     customer_details_data.contact_person =contact_person.split("联 系 人：")[1].split("\n")[0]
#                 except:
#                     customer_details_data.contact_person =contact_person.split("项目联系人：")[1].split("\n")[0]
#             else:
#                 pass
#             print("contact_person : ",customer_details_data.contact_person)
#         except Exception as e:
#             logging.info("Exception in contact_person: {}".format(type(e).__name__))
#             pass
                
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments)
page_details = fn.init_chrome_driver(arguments)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)

    urls = ["http://czj.yancheng.gov.cn/col/col31689/index.html" , "http://czj.yancheng.gov.cn/col/col20142/index.html"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(1,15):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,"div.default_pgContainer > ul >li"))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.default_pgContainer > ul >li")))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.default_pgContainer > ul >li")))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR," tbody > tr > td > table > tbody > tr > td:nth-child(8) > a")))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,"div.default_pgContainer > ul >li"),page_check))
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
