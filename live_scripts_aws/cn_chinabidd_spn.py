from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "cn_chinabidd_spn"
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

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "cn_chinabidd_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'cn_chinabidd_spn'

    notice_data.main_language = 'ZH'
    
    notice_data.currency = 'CNY'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'CN'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 4
    
    notice_data.document_type_description = 'Government Procurement'  
    

    # Onsite Field -日 期 --- date
    
# kept as commented as input team said as they not found tender with deadline value    
#      try:
#         notice_deadline = page_details.find_element(By.XPATH, '//*[contains(text(),"投标截止时间:")]//following::td[1]').text
#         notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
#         notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
#         logging.info(notice_data.notice_deadline)
#     except Exception as e:
#         logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
#         pass

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,380)
        logging.info(notice_data.notice_url)
    except:
        notice_data.notice_url = url
        
    try:
        publish_date = page_details.find_element(By.CSS_SELECTOR, "span#cphMain_tm").text
        notice_data.publish_date = datetime.strptime(publish_date,'%Y/%m/%d %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except:
        try:
            publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(3)").text
            publish_date = re.findall('\d{4}/\d+/\d+',publish_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date,'%Y/%m/%d').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.publish_date)
        except Exception as e:
            logging.info("Exception in publish_date: {}".format(type(e).__name__))
            pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
        
    try:
        notice_data.local_title = page_details.find_element(By.CSS_SELECTOR, '#cphMain_tle').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    
    # Onsite Field -编 号 --- serial number

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
    except:
        try:
            notice_data.notice_no =  re.sub("[^\d]", "",notice_data.notice_url)
        except Exception as e:
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass 
                
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.doutline').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    

    try:
        category = page_details.find_element(By.XPATH, '//*[contains(text(),"所属行业:")]//following::td[1]').text
        notice_data.category = GoogleTranslator(source='auto', target='en').translate(category)
        category1 = notice_data.category.replace(',','').replace(' ','')
        cpv_codes =  fn.procedure_mapping("assets/cn_chinabidd_cpv.csv",notice_data.category)
        for cpv_code in cpv_codes:
            cpvs_data = cpvs()
            cpvs_data.cpv_code = cpv_code
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in category: {}".format(type(e).__name__))
        pass
    
        
    try:
        notice_data.class_at_source = 'CPV'
        cpv_at_source = ''
        for singlerecord in cpv_codes:
            cpv_at_source += singlerecord
            cpv_at_source += ','
        notice_data.cpv_at_source = cpv_at_source.rstrip(',')
    except:
        pass


    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.doutline'):

            customer_details_data = customer_details()
            customer_details_data.org_name = 'China Government Procurement Bidding Network'
            customer_details_data.org_parent_id = '7782735'
            customer_details_data.org_country = 'CN'
            customer_details_data.org_language = 'ZH'
            
                                     
            try:
                customer_details_data.org_city = single_record.find_element(By.XPATH, '//*[contains(text(),"所在地区:")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass
        

            try:
                customer_details_data.org_email = single_record.find_element(By.XPATH, '//*[contains(text(),"详情咨询电话:")]//following::td[1]').text.split("供应商邮箱:")[1]
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
        

            try:
                customer_details_data.org_phone = single_record.find_element(By.XPATH, '//*[contains(text(),"详情咨询电话:")]//following::td[1]').text.split("客服")[1].split("(")[0].strip()
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
        
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except:
        customer_details_data = customer_details()
        customer_details_data.org_name = 'China Government Procurement Bidding Network'
        customer_details_data.org_parent_id = '7782735'
        customer_details_data.org_country = 'CN'
        customer_details_data.org_language = 'ZH'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
        
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) + str(notice_data.publish_date) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']

options = webdriver.ChromeOptions()
options.add_extension("C:/Users/Administrator/home/Urban-Free-VPN-proxy-Unblocker---Best-VPN.crx")
page_main = webdriver.Chrome(options=options)
time.sleep(20)

options = webdriver.ChromeOptions()
options.add_extension("C:/Users/Administrator/home/Urban-Free-VPN-proxy-Unblocker---Best-VPN.crx")
page_details = webdriver.Chrome(options=options)
time.sleep(20)

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = [
            'http://www.chinabidding.org.cn/PurchaseInfoList.html',
            'http://www.chinabidding.org.cn/BidInfoList_bt_1.html',
            'http://www.chinabidding.org.cn/BidInfoList_bt_2.html',
            'http://www.chinabidding.org.cn/PurchaseInfoList_pt_3.html',
            'http://www.chinabidding.org.cn/PurchaseInfoList_pt_2.html',
            'http://www.chinabidding.org.cn/PurchaseInfoList_pt_1.html',
            'http://www.chinabidding.org.cn/PurchaseInfoList_pt_0.html'
           ] 
    for url in urls:
        fn.load_page(page_main, url, 350)
        logging.info('----------------------------------')
        logging.info(url)
        
        try:
            for page_no in range(2,5):
                page_check = WebDriverWait(page_main, 350).until(EC.presence_of_element_located((By.XPATH,'//*[@id="frmHome"]/div[3]/div/div[1]/table[2]/tbody/tr/td[2]/table/tbody/tr[2]'))).text
                rows = WebDriverWait(page_main, 360).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="frmHome"]/div[3]/div/div[1]/table[2]/tbody/tr/td[2]/table/tbody/tr')))
                length = len(rows)
                for records in range(1,length):
                    tender_html_element = WebDriverWait(page_main, 360).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="frmHome"]/div[3]/div/div[1]/table[2]/tbody/tr/td[2]/table/tbody/tr')))[records]  
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break

                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break

                try:   
                    next_page = WebDriverWait(page_main, 350).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 350).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="frmHome"]/div[3]/div/div[1]/table[2]/tbody/tr/td[2]/table/tbody/tr[2]'),page_check))
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
