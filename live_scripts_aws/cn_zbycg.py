
from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "cn_zbycg"
log_config.log(SCRIPT_NAME)
import re
import jsons
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from deep_translator import GoogleTranslator
from selenium import webdriver
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn
import gec_common.Doc_Download
from selenium.webdriver.chrome.options import Options

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "cn_zbycg"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'cn_zbycg'
    
    notice_data.main_language = 'ZH'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'CN'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'CNY'
    
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 4
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "li > span").text
        publish_date = re.findall('\w+ \d+, \d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%b %d, %Y').strftime('%Y/%m/%d')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'li > a.title').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    logging.info(notice_data.notice_url)
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.local_title = page_details.find_element(By.CSS_SELECTOR, 'div.show_cont > h3').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.notice_summary_english = page_details.find_element(By.CSS_SELECTOR, 'div.show_cont > h3').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.CSS_SELECTOR, 'div.show_cont > h3').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -所属分类
    # Onsite Comment -None

    try:
        notice_data.document_type_description = page_details.find_element(By.CSS_SELECTOR, 'dl > p:nth-child(1) > a').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    texts = page_details.find_element(By.CSS_SELECTOR, '#container > p:nth-child(2)').text.split('\n')
    for text in texts:   
    # Onsite Field -split notice_deadline from this words "递交截止时间" or "投标文件递交的截止时间（投标截止时间，下同）为"
    # Onsite Comment -notice_deadling is not availabel then take as threshold
        if '投标截止时间：'in text or '提交投标文件截止时间：' in text or '递交投标文件截止时间:' in text or '递交截止时间' in text or '投标截止时间' in text or '招标文件获取时间为' in text:
            try:
                notice_deadline = GoogleTranslator(source='zh-CN', target='en').translate(text)
                notice_deadline = re.findall('\w+ \d+, \d{4}',notice_deadline)[0]
                notice_data.notice_deadline = datetime.strptime(notice_deadline,'%B %d, %Y').strftime('%Y/%m/%d %H:%M:%S')
            except Exception as e:
                logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
                pass
            
        elif '联系人：' in text:
            try:
                contact_person= text.split('联系人：')[1]
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass
            
        elif '手机：' in text or '电   话：' in text:
            try:
                org_phone = text.split("手机：")[1]
            except:
                try:
                    org_phone = text.split("电   话：")[1]
                except Exception as e:
                    logging.info("Exception in org_phone: {}".format(type(e).__name__))
                    pass
                
        elif '邮箱：' in text or '邮   箱：' in text:
            try:
                org_email = text.split("邮箱：")[1]
            except:
                try:
                    org_email = text.split("邮   箱：")[1]
                except Exception as e:
                    logging.info("Exception in org_email: {}".format(type(e).__name__))
                    pass
                
    #  challanges in est_amount as per research cost comes in million or billion ot thousand in words + digit 
#   thats why not feasible to convert such values.

#         elif '预算金额：' in text or '预算金额（元）：' in text:
#             try:
#                 est_amount = re.sub("[^\d\.\,]", "", text)
#                 notice_data.est_amount = float(est_amount.replace('.','').replace(',','.').strip())
#                 notice_data.grossbudgetlc = notice_data.est_amount
#                 print(notice_data.est_amount)
#             except:
#                 pass
        else:
            pass
# Onsite Field -None
# Onsite Comment -None
   
    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.inleft.fl'):
            customer_details_data = customer_details()
        # Onsite Field -None
        # Onsite Comment -None

            try:
                org_name = page_details.find_element(By.CSS_SELECTOR, 'div.showcondiv > h1').text
                customer_details_data.org_name = GoogleTranslator(source='auto', target='en').translate(org_name)
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -None
            try:
                customer_details_data.org_city = page_details.find_element(By.CSS_SELECTOR, 'dl > p:nth-child(2) > a').text
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass
            
            try:
                customer_details_data.org_country = 'CN'
            except:
                pass
            
        # Onsite Field -None
        # Onsite Comment -split contact_person from "联系人： "(Contact:)
            try:
                customer_details_data.contact_person = contact_person 
            except:
                pass
            
#         # Onsite Field -None
#         # Onsite Comment -split org_phone from "手机："(Mobile)
            try:
                customer_details_data.org_phone = org_phone
            except:
                pass

        # Onsite Field -None
        # Onsite Comment -split org_email from "邮箱："(E-mail: )
            try:
                customer_details_data.org_email = org_email
            except:
                pass
           
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.showcondiv').get_attribute("outerHTML")
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
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
options = Options()
#options.add_argument("--headless")
for argument in arguments:
    options.add_argument(argument)
page_main = webdriver.Chrome(options=options)
page_details = webdriver.Chrome(options=options)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["http://www.china-zbycg.com/category-zhaobiao/type-zbyg-12.html","http://www.china-zbycg.com/category-zhaobiao/type-jxxm-49.html",
            "http://www.china-zbycg.com/category-zhaobiao/type-nzjxm-26.html","http://www.china-zbycg.com/category-zhaobiao/type-zbgg-8.html","http://www.china-zbycg.com/category-zhaobiao/type-xmgl-35.html"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(2,5):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,' div.alllist_info.pb10 > ul > li:nth-child(1)'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ' div.alllist_info.pb10 > ul > li')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.alllist_info.pb10 > ul > li')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
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
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'div.alllist_info.pb10'),page_check))
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
