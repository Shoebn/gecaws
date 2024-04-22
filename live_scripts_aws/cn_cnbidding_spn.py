from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "cn_cnbidding_spn"
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
#import undetected_chromedriver as uc


NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "cn_cnbidding_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'cn_cnbidding_spn'
    notice_data.main_language = 'ZH'
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'CN'
    notice_data.performance_country.append(performance_country_data)
    notice_data.currency = 'CNY'
    notice_data.notice_type = 4

    if url == urls[5]:
        notice_data.procurement_method = 0
    elif url ==  urls[6]:
        notice_data.procurement_method = 1
    else:
        notice_data.procurement_method = 2
    
    try:
        notice_data.document_type_description = '招标预告'
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "tr > td:nth-child(4)").text
        publish_date = re.findall('\d{4}-\d+-\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%Y-%m-%d').strftime('%Y/%m/%d')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'h2 > a').get_attribute("href")      
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except:
        notice_data.notice_url = url
        
    try:
        notice_data.local_title = page_details.find_element(By.CSS_SELECTOR, 'div.cDetalis.clearfix > h1').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)   
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass

    try:
        notice_data.local_description = notice_data.local_title 
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
        
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div> div.fl.sidebar_w > div').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass

    try:
        notice_deadline = page_details.find_element(By.CSS_SELECTOR, "div.cDetalis > ul > li:nth-child(1)").text.split('至')[1]
        notice_deadline = re.findall('\d{4}-\d+-\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%Y-%m-%d').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    try:    
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'ul.infoUl li'):
            if '行业分类：' in single_record.text:
                category = single_record.text.split('行业分类：')[1].strip()
                category = GoogleTranslator(source='auto', target='en').translate(category)
                cpv_codes = fn.CPV_mapping('assets/cn_cnbidding_spn_cpv.csv',category)
                for cpv_code in cpv_codes:
                    cpvs_data = cpvs()
                    cpvs_data.cpv_code = cpv_code
                    cpvs_data.cpvs_cleanup()
                    notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_no = page_details.find_element(By.CSS_SELECTOR, 'div.cDetalis > ul > li:nth-child(2)').text.split('招标编号：')[1]
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'CN'
        
        try:
            org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"招标单位：")]').text.split('招标单位：')[1]
            customer_details_data.org_name = GoogleTranslator(source='auto', target='en').translate(org_name)
        except:
            try:
                org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"招标机构：")]//parent::li').text.split('招标机构：')[1]
                customer_details_data.org_name = GoogleTranslator(source='auto', target='en').translate(org_name)
            except:
                try:
                    org_name = page_details.find_element(By.CSS_SELECTOR, 'div.cDetalis.clearfix > div > p:nth-child(1)').text 
                    org_name = org_name[:100]
                    if '有限公司' in org_name:
                        org_name = org_name.split('有限公司')[0]
                        org_name = org_name[-12:]
                        org_name = org_name + '有限公司'
                        customer_details_data.org_name = GoogleTranslator(source='auto', target='en').translate(org_name)
                    else:
                        customer_details_data.org_name = 'China Bidding Information Network'
                except:
                    customer_details_data.org_name = 'China Bidding Information Network'

        try:
            customer_details_data.org_city = page_details.find_element(By.CSS_SELECTOR, 'div.cDetalis> ul > li:nth-child(4)').text.split('省 份：')[1]
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass

        try:
            customer_details_data.contact_person = page_details.find_element(By.CSS_SELECTOR, 'div.cDetalis.clearfix > div > p:nth-child(45)').text.split('联系人：')[1]
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass

        try:
            customer_details_data.org_phone = page_details.find_element(By.CSS_SELECTOR, 'div.cDetalis.clearfix > div > p:nth-child(47)').text.split('联系电话：')[1]
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass
            
        try:
            customer_details_data.org_address = page_details.find_element(By.CSS_SELECTOR, 'div.cDetalis.clearfix > div > p:nth-child(87)').text.split('联系地址：')[1]
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass
        
        try:
            customer_details_data.org_email = page_details.find_element(By.CSS_SELECTOR, 'div.cDetalis.clearfix > div > p:nth-child(85)').text.split('邮箱：')[1]
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try:              
        attachments_data = attachments()
        attachments_data.file_name = page_details.find_element(By.XPATH, '//*[contains(text(),"附件下载")]//following::a[1]').text.split('.')[0] 
        attachments_data.external_url = page_details.find_element(By.XPATH, '//*[contains(text(),"附件下载")]//following::a[1]').get_attribute('href')
        attachments_data.file_type = attachments_data.external_url.split('.')[-1]
        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
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
# page_main = uc.Chrome()
# page_details = uc.Chrome()

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['http://www.cnbidding.com/notice/search.php',
            'http://www.cnbidding.com/bforeshow/search.php',
            'http://www.cnbidding.com/notice/search.php?usetype=01',
            'http://www.cnbidding.com/notice/search.php?usetype=02',
            'http://www.cnbidding.com/notice/search.php?usetype=03',
            'http://www.cnbidding.com/notice/search.php?bidtype=01',
            'http://www.cnbidding.com/notice/search.php?bidtype=02'
           ] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(2,10):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[5]/div[1]/div/div[2]/table/tbody/tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[5]/div[1]/div/div[2]/table/tbody/tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[5]/div[1]/div/div[2]/table/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'/html/body/div[5]/div[1]/div/div[2]/div/form/a[10]')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/div[5]/div[1]/div/div[2]/table/tbody/tr'),page_check))
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
