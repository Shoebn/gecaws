from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "cn_sdicc"
log_config.log(SCRIPT_NAME)
import re
import jsons
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from deep_translator import GoogleTranslator
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "cn_sdicc"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    notice_data.script_name = 'cn_sdicc'
    
    notice_data.main_language = 'ZH'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'CN'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'CNY'
    
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 4
    
    # Onsite Field -公告名称 --- Bulletin name
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'tr td:nth-child(2) > span').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -发布时间---release time
    # Onsite Comment -None
    

    try:
        notice_data.document_type_description = '采购信息'
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "tr td:nth-child(4)").text
        publish_date = re.findall('\d{4}-\d+-\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%Y-%m-%d').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    
    # Onsite Field -招采类型 -Recruitment type
    # Onsite Comment -take " Serve - Service, Supplies- supply, Project - Work"

    try:
        notice_contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'tr td:nth-child(3)').text
        notice_data.notice_contract_type = GoogleTranslator(source='auto', target='en').translate(notice_contract_type)
        if "Serve" in notice_data.notice_contract_type:
            notice_data.notice_contract_type="Service"
        elif  "project" in notice_data.notice_contract_type:
            notice_data.notice_contract_type="Work"
        elif  "supplies" in notice_data.notice_contract_type:
            notice_data.notice_contract_type="Supply"
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -there is no url so use " on click"

    try:
        notice_data.notice_url = WebDriverWait(tender_html_element, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'tr td:nth-child(2) > span'))).click()            
        WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,' div:nth-child(1) > div > div:nth-child(1) > div:nth-child(1) > span:nth-child(2)')))
        notice_data.notice_url = page_main.current_url
        logging.info(notice_data.notice_url)
    except:
        notice_data.notice_url = url                    
    
    try:
        notice_data.notice_text += page_main.find_element(By.XPATH, '/html/body/div[4]/div/div/div/div[2]/div[1]').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    
    try:
        notice_data.local_description = page_main.find_element(By.CSS_SELECTOR, 'div:nth-child(2) > div > div:nth-child(7) > span:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
#     # Onsite Field -截标/开标时间---Bid Closing 截标/开标时间：
#     # Onsite Comment -None

    try:
        notice_deadline = page_main.find_element(By.CSS_SELECTOR, " div:nth-child(2) > div > div:nth-child(4) > div:nth-child(1) > span:nth-child(2)").text#.split('截标/开标时间：')[1]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%Y-%m-%d %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
#       # Onsite Field -招标范围 --- Bidding scope:
#     # Onsite Comment -None

    try:
        notice_summary_english = notice_data.local_description
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_summary_english)
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    
#     # Onsite Field -Item Number---项目编号
#     # Onsite Comment -None

    try:
        notice_data.notice_no = page_main.find_element(By.CSS_SELECTOR, '  div:nth-child(1) > div > div:nth-child(1) > div:nth-child(2) > span:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
#      # Onsite Field -供应商拟投入项目负责人最低要求
#     # Onsite Comment -None

    try:
        document_cost = page_main.find_element(By.CSS_SELECTOR, ' div:nth-child(2) > div > div:nth-child(3) > div:nth-child(1) > span:nth-child(2)').text
        notice_data.document_cost = float(document_cost)
    except Exception as e:
        logging.info("Exception in eligibility: {}".format(type(e).__name__))
        pass
    
    try:
        eligibility = page_main.find_element(By.CSS_SELECTOR, 'div:nth-child(12) > span:nth-child(2)').text
        notice_data.eligibility = GoogleTranslator(source='auto', target='en').translate(eligibility)
    except Exception as e:
        logging.info("Exception in eligibility: {}".format(type(e).__name__))
        pass
    

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'CN'
        customer_details_data.org_language = 'ZH'
        
        # Onsite Field -代理机构 --- Agency
        # Onsite Comment -None

        try:
            org_name = page_main.find_element(By.CSS_SELECTOR, 'div > div.dg-flex div:nth-child(1) > div > div:nth-child(4) > div:nth-child(2) > span:nth-child(2)').text
            customer_details_data.org_name = GoogleTranslator(source='auto', target='en').translate(org_name)
        except Exception as e:
            logging.info("Exception in org_name: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -联系人--- Contact
        # Onsite Comment -None

        try:
            contact_person = page_main.find_element(By.CSS_SELECTOR, 'div:nth-child(4) > div > div:nth-child(1) > div:nth-child(2) > span:nth-child(2)').text
            customer_details_data.contact_person = GoogleTranslator(source='auto', target='en').translate(contact_person)
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -手机号码 --- Phone Number
        # Onsite Comment -None

        try:
            customer_details_data.org_phone = page_main.find_element(By.XPATH, "//*[contains(text(),'手机号码')]//following::span[1]").text
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -联系地址：--- contact address
        # Onsite Comment -None

        try:
            org_address = page_main.find_element(By.XPATH, "//*[contains(text(),'联系地址：')]//following::span[1]").text
            customer_details_data.org_address = GoogleTranslator(source='auto', target='en').translate(org_address)
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -电子邮箱：--- E-mail
        # Onsite Comment -None

        try:
            customer_details_data.org_email = page_main.find_element(By.XPATH, "//*[contains(text(),'电子邮箱：')]//following::span[1]").text
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass
        
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    

    try:  
        for single_record in page_main.find_elements(By.CSS_SELECTOR, ' div:nth-child(5) > div > div:nth-child(8) > span:nth-child(2)'):
        # Onsite Field -download attachment---附件下载：
        # Onsite Comment -None
            attachments_data = attachments() 
            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'a').text
            external_url = single_record.find_element(By.CSS_SELECTOR, 'a').click()
            file_dwn = Doc_Download.file_download()
            attachments_data.external_url = str(file_dwn[0])
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass

    page_main.execute_script("window.history.go(-1)")
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) + str(notice_data.publish_date) +  str(notice_data.notice_url) 
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
page_details = fn.init_chrome_driver(arguments) 
page_main = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://www.sdicc.com.cn/cgxx/ggList'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(1,5):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="table"]/div[2]/table/tbody/tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="table"]/div[2]/table/tbody/tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="table"]/div[2]/table/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#page_btnLas')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="table"]/div[2]/table/tbody/tr'),page_check))
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
