from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "cn_hebei_spn"
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

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "cn_hebei_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'cn_hebei_spn'
    
    notice_data.main_language = 'ZH'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'CN'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'CNY'
    
    notice_data.procurement_method = 0
    
    notice_data.notice_type = 4
    
    # Onsite Field -招标（采购）
    # Onsite Comment -None
    try:
        document_type_description ='招标（采购'
        notice_data.document_type_description = GoogleTranslator(source='auto', target='en').translate(document_type_description)
    except:
        pass
    
    # Onsite Field -None
    # Onsite Comment -take local_title in text form

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -"发布时间：" = Release time:
    # Onsite Comment -take only "发布时间：" =  Release time:

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, '#moredingannctable > tbody >tr > td > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except:
        notice_data.notice_url = url

    try:
        notice_data.notice_text += page_details.find_element(By.XPATH, '//*[@id="2020_VERSION"]').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass

    try:
        publish_date = page_details.find_element(By.CSS_SELECTOR, " tbody > tr:nth-child(9) > td > span").text
        publish_date = re.findall('\d{4}-\d+-\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%Y-%m-%d').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
#     # Onsite Field -"项目编号： " = Project number:
#     # Onsite Comment -take only "项目编号： " = Project number:

    try:
        notice_data.notice_no = page_details.find_element(By.CSS_SELECTOR, 'span.txt7 > span:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # field notice_deadline is varing unable to grap information
    
#     # Onsite Field -"提交投标文件截止时间、开标时间和地点" = Deadline for submission of tender documents, time and place of bid opening/ "响应文件提交 截止时间" = Submission of response documents Deadline:
#     # Onsite Comment -take only "提交投标文件截止时间、开标时间和地点" = Deadline for submission of tender documents, time and place of bid opening/ "响应文件提交 截止时间" = Submission of response documents Deadline:  and if the given selector is not taking the field then use the below selector 'span.inquiry' for some tenders

#     try:
#         notice_deadline = page_details.find_element(By.CSS_SELECTOR, "span.ding").text
#         notice_deadline = GoogleTranslator(source='auto', target='en').translate(notice_deadline)
#         notice_deadline = re.findall('\w+ \d+, \d{4}',notice_deadline)[0]
#         notice_deadline = datetime.strptime(notice_deadline,'%B %m, %Y').strftime('%Y/%m/%d %H:%M:%S')
# #         notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
# #         logging.info(notice_data.notice_deadline)
#     except Exception as e:
#         logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
#         pass
    
#     # Onsite Field -"预算金额：" = Budget Amount:
#     # Onsite Comment -take only "预算金额：" = Budget Amount:

    try:
        grossbudgetlc = page_details.find_element(By.CSS_SELECTOR, '#amt').text
        notice_data.grossbudgetlc =float(grossbudgetlc)
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -"预算金额：" = Budget Amount:
    # Onsite Comment -take only "预算金额：" = Budget Amount:

    try:
        notice_data.est_amount = notice_data.grossbudgetlc
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -"申请人的资格要求" = Qualification requirements for applicants/ "申请人的资格要求" = Applicant qualification requirements
    # Onsite Comment -take only "申请人的资格要求" = Qualification requirements for applicants/ "申请人的资格要求" = Applicant qualification requirements

    try:
        eligibility = page_details.find_element(By.XPATH, '//*[@id="2020_VERSION"]').text.split('申请人的资格要求')[1].split('获取招标文件')[0]
        notice_data.eligibility = GoogleTranslator(source='auto', target='en').translate(eligibility)
    except Exception as e:
        logging.info("Exception in eligibility: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -"采购方式" = Procurement Method:
    # Onsite Comment -take only "采购方式" = Procurement Method:

    try:
        notice_data.type_of_procedure_actual = page_details.find_element(By.CSS_SELECTOR, '#purchaseway').text
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'CN'
        customer_details_data.org_language = 'ZH'
        # Onsite Field -" 采购人：" = Purchaser:
        # Onsite Comment -take " 采购人：" = Purchaser: only from the given selector

        org_name = page_details.find_element(By.CSS_SELECTOR, ' span > span:nth-child(44)').text
        customer_details_data.org_name = GoogleTranslator(source='auto', target='en').translate(org_name)
        
        
        # Onsite Field -"地域：" = Region:
        # Onsite Comment -take "地域：" = Region: only from the given selector

        try:
            org_address = page_details.find_element(By.CSS_SELECTOR, ' span > span:nth-child(46)').text
            customer_details_data.org_address = GoogleTranslator(source='auto', target='en').translate(org_address)
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -"项目联系人：" = Project contact person:
        # Onsite Comment -take "项目联系人：" = Project contact person: only from the given selector

        try:
            contact_person = page_details.find_element(By.CSS_SELECTOR, 'span > span:nth-child(48)').text.split(' ')[0]
            customer_details_data.contact_person = GoogleTranslator(source='auto', target='en').translate(contact_person)
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -"电　话：" = Tel:
        # Onsite Comment -take  "电　话：" = Tel: only from the given selector

        try:
            customer_details_data.org_phone = page_details.find_element(By.CSS_SELECTOR, 'span > span:nth-child(48)').text.split(' ')[-1]
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass
            
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#fujian_2020'):
            attachments_data = attachments()
        # Onsite Field -None
        # Onsite Comment -take file_name in textform

            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'a').text
            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, ' a').get_attribute('href')
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
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
page_main = fn.init_chrome_driver(arguments) 
page_details = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['http://www.ccgp-hebei.gov.cn/province/cggg/zbgg/'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(2,20):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="moredingannctable"]/tbody/tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="moredingannctable"]/tbody/tr')))
                length = len(rows)
                for records in range(0,length,2):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="moredingannctable"]/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="moredingannctable"]/tbody/tr'),page_check))
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
    
