#In this script there are two formats...tender_html_elelment page , lot_details, customer_details are common for both formats
from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "cn_gzswbc_spn"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
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
SCRIPT_NAME = "cn_gzswbc_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
   
    notice_data.script_name = 'cn_gzswbc_spn'
    
    notice_data.main_language = 'ZH'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'CN'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'CNY'
    
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 4
    
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'CN'
        customer_details_data.org_language = 'ZH'
        customer_details_data.org_name = 'Guangzhou Shunwei Tendering and Procurement Co., Ltd.'
        customer_details_data.org_parent_id = '7785927'
        customer_details_data.org_address = 'Rooms B501-B505 and B512-B525, No. 205, Huanshi Middle Road, Yuexiu District, Guangzhou City, Guangdong Province'
        customer_details_data.org_phone = '020-83592216-819'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    # Onsite Field -询价/竞价公告
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.text > a > span > span').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -询价/竞价公告
    # Onsite Comment -1.split notice_no from title.

    try:
        notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div.text > a > span > span').text
        notice_data.notice_no = re.findall(r'[A-Z]+[0-9]+[A-Z]+[0-9]+', notice_no)[0]
    except:
        try:
            notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div.text > a').get_attribute("href").split("/")[-1].split(".")[0].strip()
        except Exception as e:
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass
    
    # Onsite Field -None
    # Onsite Comment -1.split notice_no from notice_url.        2.here "http://www.gzswbc.com/enquiry/20231030/903739101474193408.html" take "903739101474193408" as notice_no.

    
    # Onsite Field -日期
    # Onsite Comment -None
    
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div.time").get_attribute("outerHTML")
        publish_date = re.findall('\d{4}-\d+-\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%Y-%m-%d').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.text > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'section.list-section').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')

#format-1)after opening the url take data after clicking on "招标公告=Tender notice".

    
    # Onsite Field -None
    # Onsite Comment -1.split after "采购方式："

    try:
        notice_data.document_type_description = page_details.find_element(By.CSS_SELECTOR, 'section.list-section').text.split("采购方式：")[1].split("\n")[0].strip()
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -format1
    # Onsite Comment -1.split after "预算金额："
    
     # Onsite Field -format2
    # Onsite Comment -1.split after "2、项目预算："

    try:
        est_amount = page_details.find_element(By.CSS_SELECTOR, 'section.list-section').text.split("预算金额：")[1].split("\n")[0].strip()
        est_amount = GoogleTranslator(source='auto', target='en').translate(est_amount)
        est_amount = re.sub("[^\d\.\,]", "",est_amount)
        notice_data.est_amount = float(est_amount.replace(',','').strip())
        notice_data.grossbudgetlc = notice_data.est_amount
    except:
        try:
            est_amount = page_details.find_element(By.CSS_SELECTOR, 'section.list-section').text.split("、项目预算：")[1].split("\n")[0].strip()
            est_amount = GoogleTranslator(source='auto', target='en').translate(est_amount)
            est_amount = re.sub("[^\d\.\,]", "",est_amount)
            notice_data.est_amount = float(est_amount.replace(',','').strip())
            notice_data.grossbudgetlc = notice_data.est_amount
        except Exception as e:
            logging.info("Exception in est_amount: {}".format(type(e).__name__))
            pass
    
    # Onsite Field -format1
    # Onsite Comment -1.split between "申请人的资格要求：=2. Applicant’s qualification requirements:" and "2.落实政府采购政策需满足的资格要求：=2. Qualification requirements that need to be met to implement government procurement policies:"
    
     # Onsite Field -format2
    # Onsite Comment -1.ref_url:"http://www.gzswbc.com/enquiry/20231031/904058927606398976.html"	2.split between "二、合格竞价供应商条件=2. Conditions for qualified bidding suppliers" and "三、竞价方式和竞价时间=3. Bidding method and bidding time".

    try:
        notice_data.eligibility = page_details.find_element(By.CSS_SELECTOR, 'section.list-section').text.split("申请人的资格要求：")[1].split("2.落实政府采购政策需满足的资格要求：")[0].strip()
    except:
        try:
            notice_data.eligibility = page_details.find_element(By.CSS_SELECTOR, 'section.list-section').text.split("合格竞价供应商条件")[1].split("三、竞价方式和竞价时间")[0].strip()
        except Exception as e:
            logging.info("Exception in eligibility: {}".format(type(e).__name__))
            pass 
        
    
    
    # Onsite Field -None 报价时间：
    # Onsite Comment -1.split after "四、响应文件提交=4. Submission of response documents".	2.here "Deadline: 09:30:00 on November 14, 2023 (Beijing time)" take only "November 14, 2023" in notice_deadline.

    try:
        page_detial_text = page_details.find_element(By.CSS_SELECTOR, 'section.list-section').text
        if "报价时间" in page_detial_text:  
            notice_deadline = page_details.find_element(By.CSS_SELECTOR, "section.list-section").text.split("报价时间：")[1].split("\n")[0].strip()
            notice_deadline = GoogleTranslator(source='auto', target='en').translate(notice_deadline).split("on")[1]
            notice_deadline = re.findall('\w+ \d+, \d{4}',notice_deadline)[0]
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%B %d, %Y').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.notice_deadline)
        elif "四、响应文件提交" in page_detial_text:  
            notice_deadline = page_details.find_element(By.CSS_SELECTOR, "section.list-section").text.split("四、响应文件提交")[1].split("\n")[1].split('\n')[0].strip()
            notice_deadline = GoogleTranslator(source='auto', target='en').translate(notice_deadline)
            notice_deadline = re.findall('\w+ \d+, \d{4} \d+:\d+:\d+',notice_deadline)[0]
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%B %d, %Y %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.notice_deadline)
        else:
            pass   
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -1. split after "三、获取采购文件=3. Obtain procurement documents".	2.here "Time: November 3, 2023 to November 10, 2023, 00:00:00 to 12:00:00 in the morning," take only "November 3, 2023" in document_purchase_start_time

    try:
        document_purchase_start_time = page_details.find_element(By.CSS_SELECTOR, 'section.list-section').text.split("三、获取采购文件")[1].split("\n")[1].split("\n")[0].strip()
        document_purchase_start_time = GoogleTranslator(source='auto', target='en').translate(document_purchase_start_time).split("to")[0]
        document_purchase_start_time = re.findall('\w+ \d+, \d{4}',document_purchase_start_time)[0]
        notice_data.document_purchase_start_time = datetime.strptime(document_purchase_start_time,'%B %d, %Y').strftime('%Y/%m/%d')
    except Exception as e:
        logging.info("Exception in document_purchase_start_time: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -1. split after "三、获取采购文件=3. Obtain procurement documents".	2.here "Time: November 3, 2023 to November 10, 2023, 00:00:00 to 12:00:00 in the morning," take only "November 10, 2023" in document_purchase_end_time.

    try:
        document_purchase_end_time = page_details.find_element(By.CSS_SELECTOR, 'section.list-section').text.split("三、获取采购文件")[1].split("\n")[1].split("\n")[0].strip()
        document_purchase_end_time = GoogleTranslator(source='auto', target='en').translate(document_purchase_end_time).split("to")[1]
        document_purchase_end_time = re.findall('\w+ \d+, \d{4}',document_purchase_end_time)[0]
        notice_data.document_purchase_end_time = datetime.strptime(document_purchase_end_time,'%B %d, %Y').strftime('%Y/%m/%d')
    except Exception as e:
        logging.info("Exception in document_purchase_end_time: {}".format(type(e).__name__))
        pass

#format-2)after opening the url take data after clicking on "询价/竞价公告=Inquiry/Bidding Announcement".
     
# Onsite Field -None
# Onsite Comment -ref_url:"http://www.gzswbc.com/bid/20231103/905212428365594624.html"

    try:              
        single_record = page_details.find_element(By.XPATH, '//*[contains(text(),"采购需求：")]//following::table')
        lot_number = 1
        for table in single_record.find_elements(By.CSS_SELECTOR, 'table > tbody > tr'):
            data=table.text
            if "采购标的" not in data:
        
                lot_details_data = lot_details()
                lot_details_data.lot_number = 1

                 # Onsite Field -品目名称
            # Onsite Comment -None

                lot_details_data.lot_title = table.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
                lot_details_data.lot_title_english=GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
            # Onsite Field -品目号
            # Onsite Comment -None

                try:
                    lot_details_data.lot_actual_number = table.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
                except Exception as e:
                    logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                    pass

            # Onsite Field -采购标的
            # Onsite Comment -None

                try:
                    lot_details_data.lot_description = table.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
                    lot_details_data.lot_description_english=GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_description)
                except Exception as e:
                    logging.info("Exception in lot_description: {}".format(type(e).__name__))
                    pass

            # Onsite Field -数量（单位）
            # Onsite Comment -1.here "1(套)" take only "1" in lot_quantity.

                try:
                    lot_quantity = table.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
                    lot_quantity = re.sub("[^\d\.]", "",lot_quantity)
                    lot_details_data.lot_quantity = float(lot_quantity.strip())
                except Exception as e:
                    logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                    pass

            # Onsite Field -数量（单位）
            # Onsite Comment -1.here "1(套)" take only "套" in lot_quantity_uom.

                try:
                    lot_details_data.lot_quantity_uom = table.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
                except Exception as e:
                    logging.info("Exception in lot_quantity_uom: {}".format(type(e).__name__))
                    pass

            # Onsite Field -品目预算(元)
            # Onsite Comment -None

                try:
                    lot_grossbudget_lc = table.find_element(By.CSS_SELECTOR, 'td:nth-child(6)').get_attribute("outerHTML").split('">')[-1]
                    if "包" not in lot_grossbudget_lc:
                        lot_grossbudget_lc = re.sub("[^\d\.\,]", "",lot_grossbudget_lc)
                        lot_details_data.lot_grossbudget_lc = float(lot_grossbudget_lc.replace(',','').strip())
                except Exception as e:
                    logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
                    pass

                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
                lot_number += 1
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass

    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
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
    urls = ["http://www.gzswbc.com/bid/index.html"] 
    for url in urls:
        fn.load_page(page_main, url, 80)
        logging.info('----------------------------------')
        logging.info(url)

        try:
            for no in range(0,2):
                Click=page_main.find_elements(By.CSS_SELECTOR, '#transaction > div.classify.one > div > a > span')[no]
                Click.click()
                time.sleep(5)
                for page_no in range(2,5):
                    page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="content-ul"]/li'))).text
                    rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="content-ul"]/li')))
                    length = len(rows)
                    for records in range(0,length):
                        tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="content-ul"]/li')))[records]
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
                        WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="content-ul"]/li'),page_check))
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
    
