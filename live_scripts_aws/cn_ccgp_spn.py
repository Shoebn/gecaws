from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "cn_ccgp_spn"
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
from selenium.webdriver.chrome.options import Options


NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "cn_ccgp_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    notice_data.script_name = 'cn_ccgp_spn'
    notice_data.currency = 'CNY'
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'CN'
    notice_data.performance_country.append(performance_country_data)
    notice_data.procurement_method = 2
    notice_data.notice_type = 4
    notice_data.main_language = 'ZH'
    notice_data.class_at_source = 'CPV'
    notice_data.document_type_description ='公开招标公告'
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'a').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'a').get_attribute("href") 
        fn.load_page(page_details,notice_data.notice_url,280)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
        

    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.vF_detail_content_container > div').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    try:
        condition_text = page_details.find_element(By.CSS_SELECTOR, '#detail > div.main > div > div.vF_deail_maincontent > div > div.vF_detail_content_container > div > a').text 
    except:
        condition_text = ''
        
    try:
        notice_text = page_details.find_element(By.CSS_SELECTOR, '#detail > div.main > div > div.vF_deail_maincontent > div').text
    except:
        pass
        
    if '显示公告概要' in notice_text:
        clk = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.XPATH,'/html/body/div[2]/div/div[2]/div/div[1]/p/span[6]')))
        page_details.execute_script("arguments[0].click();",clk)
        
        try:  
            notice_deadline1 =  page_details.find_element(By.XPATH,"//*[contains(text(),'开标时间')]//following::td[1]").text
            notice_deadline = GoogleTranslator(source='auto', target='en').translate(notice_deadline1)
            notice_deadline = re.findall('\w+ \d+, \d{4} \d+:\d+',notice_deadline)[0]
            notice_data.notice_deadline = datetime.strptime(notice_deadline, '%B %d, %Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.notice_deadline)
        except Exception as e:
            logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
            pass
        
        try:  
            publish_date1 =  page_details.find_element(By.XPATH,"//*[contains(text(),'公告时间')]//following::td[1]").text
            publish_date = GoogleTranslator(source='auto', target='en').translate(publish_date1)
            publish_date = re.findall('\w+ \d+, \d{4} \d+:\d+',publish_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date, '%B %d, %Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.publish_date)
        except Exception as e:
            logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
            pass

        if notice_data.publish_date is not None and notice_data.publish_date < threshold:
            return
        
        try:
            notice_data.local_title = page_details.find_element(By.CSS_SELECTOR, "div.vF_deail_maincontent > div > div.vF_detail_header > h2").text
            notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
        except Exception as e:
            logging.info("Exception in local_title: {}".format(type(e).__name__))
            pass
        
        try:
            notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"品目")]//following::td[1]').text
            notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
        except Exception as e:
            logging.info("Exception in local_title: {}".format(type(e).__name__))
            pass
        
        try:
            notice_data.document_fee = page_details.find_element(By.XPATH, '//*[contains(text(),"招标文件售价")]//following::td[1]').text
        except Exception as e:
            logging.info("Exception in document_fee: {}".format(type(e).__name__))
            pass
        
        try:
            document_purchase_start_time1 = page_details.find_element(By.XPATH, '//*[contains(text(),"获取招标文件时间")]//following::td[1]').text.split("至")[0]
            document_purchase_start_time = GoogleTranslator(source='auto', target='en').translate(document_purchase_start_time1)
            document_purchase_start_time = re.findall('\w+ \d+, \d{4}',document_purchase_start_time)[0]
            notice_data.document_purchase_start_time = datetime.strptime(document_purchase_start_time,'%B %d, %Y').strftime('%Y/%m/%d')
        except Exception as e:
            logging.info("Exception in document_purchase_start_time: {}".format(type(e).__name__))
            pass
        
        try:
            document_purchase_end_time1 = page_details.find_element(By.XPATH, '//*[contains(text(),"获取招标文件时间")]//following::td[1]').text.split("至")[1]
            document_purchase_end_time = GoogleTranslator(source='auto', target='en').translate(document_purchase_end_time1)
            document_purchase_end_time = re.findall('\w+ \d+, \d{4}',document_purchase_end_time)[0]
            notice_data.document_purchase_end_time = datetime.strptime(document_purchase_end_time,'%B %d, %Y').strftime('%Y/%m/%d')
        except Exception as e:
            logging.info("Exception in document_purchase_start_time: {}".format(type(e).__name__))
            pass
        
        try:
            est_amount = page_details.find_element(By.XPATH, '//*[contains(text(),"预算金额")]//following::td[1]').text
            est_amount =re.sub("[^\d\.\,]","",est_amount)
            notice_data.est_amount = float(est_amount) * 10000
            notice_data.grossbudgetlc = notice_data.est_amount
        except Exception as e:
            logging.info("Exception in est_amount: {}".format(type(e).__name__))
            pass
        
        try:              
            customer_details_data = customer_details()
            customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"采购单位")]//following::td[1]').text
            try:
                customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"采购单位地址")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__)) 
                pass

            try:
                customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"项目联系人")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__)) 
                pass
            
            try:
                customer_details_data.org_city = page_details.find_element(By.XPATH, '//*[contains(text(),"行政区域")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__)) 
                pass

            try:
                customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"项目联系电话")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__)) 
                pass
                       
            customer_details_data.org_country = 'CN'
            customer_details_data.org_language = 'ZH'
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
        except Exception as e:
            logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
            pass
        try:
            notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, ' div.vF_deail_maincontent > div > div.table > table > tbody').get_attribute("outerHTML")                     
        except:
            notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
            
        try:
            for single_record in page_details.find_elements(By.CSS_SELECTOR, "td:nth-child(2) > a"):
                attachments_data = attachments()

                attachments_data.external_url = single_record.get_attribute('href')
                attachments_data.file_name = single_record.text
                try:
                    attachments_data.file_type = attachments_data.file_name.split('.')[-1]
                except Exception as e:
                    logging.info("Exception in file_type: {}".format(type(e).__name__))
                    pass

                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
        except Exception as e:
            logging.info("Exception in attachments: {}".format(type(e).__name__)) 
            pass  
    
    elif '下载相关附件' in condition_text:
        
        try:
            notice_data.notice_no = page_details.find_element(By.XPATH, "//*[contains(text(),'项目编号')]//following::span[1]").text
        except Exception as e:
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass

        try:
            est_amount = page_details.find_element(By.XPATH, "//span[contains(text(),'预算金额')]//following::span").text
            est_amount =re.sub("[^\d\.\,]","",est_amount)
            notice_data.est_amount = float(est_amount) * 10000
            notice_data.grossbudgetlc = notice_data.est_amount
        except Exception as e:
            logging.info("Exception in est_amount: {}".format(type(e).__name__))
            pass

        try:
            notice_data.local_description = page_details.find_element(By.XPATH, "//*[contains(text(),'采购需求')]//following::span[1]").text
            notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
        except Exception as e:
            logging.info("Exception in local_description: {}".format(type(e).__name__))
            pass

        try:
            customer_details_data = customer_details()

            customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, "em:nth-child(4)").text

            try:
                customer_details_data.org_address = page_details.find_element(By.XPATH, "//span[contains(text(),'地址：')]").text.split('：')[1]
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass

            try:
                customer_details_data.contact_person = page_details.find_element(By.XPATH, "//span[contains(text(),'联系方式：')]").text.split('：')[1]
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass

            try:
                org_phone = page_details.find_element(By.XPATH, "//span[contains(text(),'联系方式：')]").text
                customer_details_data.org_phone = re.findall('\d{3}-\d+',org_phone)[0]
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass

            try:
                postal_code = page_details.find_element(By.XPATH, "//span[contains(text(),'邮政编码：')]").text
                customer_details_data.postal_code =re.sub("[^\d\.\,]","",postal_code)
            except Exception as e:
                logging.info("Exception in postal_code: {}".format(type(e).__name__))
                pass    

            customer_details_data.org_country = 'CN'
            customer_details_data.org_language = 'ZH'
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
        except Exception as e:
            logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
            pass
        
    
    else:
        try:
            page_details.close()
            page_details2 = webdriver.Chrome(options=options)
            notice_url = notice_data.notice_url
            fn.load_page(page_details2,notice_url,280)
            logging.info('page_details2')
            time.sleep(2)
        except Exception as e:
            logging.info("Exception in page_details2: {}".format(type(e).__name__))

        try:
            customer_details_text = page_details2.find_element(By.CSS_SELECTOR, 'div.vF_deail_maincontent > div').text
            
            try:
                notice_data.notice_no = customer_details_text.split('项目编号：')[1].split('日期：')[0].split('\n')[0].strip()
            except Exception as e:
                logging.info("Exception in notice_no: {}".format(type(e).__name__))
                pass
            
            customer_details_data = customer_details()
            customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, "em:nth-child(4)").text

            try:
                customer_details_data.org_address = page_details2.find_element(By.XPATH, "//p[contains(text(),'地址：')]").text.split('：')[1] 
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass

            try:
                contact_person = page_details2.find_element(By.XPATH, "//p[contains(text(),'联系方式：')]").text.split('：')[1].split('0')[0] 
                if contact_person_2 is not None:
                    customer_details_data.contact_person = contact_person
            except:
                try:
                    customer_details_data.contact_person = page_details2.find_element(By.XPATH, "//p[contains(text(),'联系方式：')]").text.split('：')[1] 
                    if contact_person_2 is not None:
                        customer_details_data.contact_person = contact_person
                except:
                    try:
                        customer_details_data.contact_person = customer_details_text.split('名 称：')[1].split('\n')[0]

                    except Exception as e:
                        logging.info("Exception in contact_person: {}".format(type(e).__name__))
                        pass

            try:
                page_details2.close()
                time.sleep(2)
                page_details3 = webdriver.Chrome(options=options)
                notice_url = notice_data.notice_url
                fn.load_page(page_details3,notice_url,280)
                logging.info('page_details3')
                time.sleep(2)
            except Exception as e:
                logging.info("Exception in page_details3: {}".format(type(e).__name__))

            try:
                org_email = page_details3.find_element(By.XPATH, "//p[contains(text(),'联系方式：')]").text
                if '@' in org_email:
                    customer_details_data.org_email = re.search(r'[\w\.-]+@[\w\.-]+',org_email)[0]
                else:
                    customer_details_data.org_email = customer_details_text.split('项目联系人：冯宇图 吴旭 李媛')[1].split('\n')[0]
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass

            try:
                org_phone = page_details3.find_element(By.XPATH, "//p[contains(text(),'联系方式：')]").text
                customer_details_data.org_phone = re.findall('\d{3}-\d+',org_phone)[0]
            except:
                try:
                    customer_details_data.org_phone = customer_details_text.split('电 话：')[1].split('\n')[0]
                except Exception as e:
                    logging.info("Exception in contact_person: {}".format(type(e).__name__))
                    pass

            customer_details_data.org_country = 'CN'
            customer_details_data.org_language = 'ZH'
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
        except Exception as e:
            logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
            pass

        try:
            page_details3.close()
            page_details4 = webdriver.Chrome(options=options)
            notice_url = notice_data.notice_url
            fn.load_page(page_details4,notice_url,280)
            logging.info('page_details4')
            time.sleep(2)
        except Exception as e:
            logging.info("Exception in page_details4: {}".format(type(e).__name__))

        try:
            est_amount = page_details4.find_element(By.XPATH, "//span[contains(text(),'预算金额')]//following::span").text
            est_amount =re.sub("[^\d\.\,]","",est_amount)
            notice_data.est_amount = float(est_amount) * 10000
        except:
            try:
                est_amount = page_details4.find_element(By.XPATH, "//*[contains(text(),'预算金额：')]").text
                est_amount =re.sub("[^\d\.\,]","",est_amount)
                notice_data.est_amount = float(est_amount) * 10000
            except:
                try:
                    est_amount = customer_details_text.split('合同估算价')[1].split('（')[0]
                    notice_data.est_amount = float(est_amount) * 10000
                except Exception as e:
                    logging.info("Exception in est_amount: {}".format(type(e).__name__))
                    pass
            
        try:
            notice_data.grossbudgetlc = notice_data.est_amount
        except Exception as e:
            logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
            pass
            
        try:
            notice_data.local_description = page_details4.find_element(By.CSS_SELECTOR, 'div.vF_detail_content_container > div > blockquote').text  
            notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)  
        except Exception as e:
            logging.info("Exception in local_description: {}".format(type(e).__name__))
            pass

        try:
            notice_data.document_fee = page_details4.find_element(By.XPATH, "//*[contains(text(),'售价：')]").text.split('￥')[1].split('元')[0]
        except Exception as e:
            logging.info("Exception in document_fee: {}".format(type(e).__name__))
            pass
        
        try:
            page_details4.close()
            time.sleep(5)
            page_details5 = webdriver.Chrome(options=options)
            notice_url = notice_data.notice_url
            fn.load_page(page_details5,notice_url,280)
            logging.info('page_details5')
        except Exception as e:
            logging.info("Exception in page_details5: {}".format(type(e).__name__))
        
        try:
            lot_number = 1
            condition_check = page_details5.find_element(By.CSS_SELECTOR, 'div > div.vF_detail_content_container > div > table > tbody>tr:nth-child(1)').text
            condition_check_en = GoogleTranslator(source='auto', target='en').translate(condition_check)
            if 'item name' in condition_check_en or 'Procurement content' in condition_check_en or 'name' in condition_check_en or 'project name'in condition_check_en:
                for single_record in page_details5.find_elements(By.CSS_SELECTOR, 'div > div.vF_detail_content_container > div > table > tbody>tr')[1:]:
                    lot_details_data = lot_details()
                    lot_details_data.lot_number = lot_number

                    lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
                    lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)

                    try:
                        lot_quantity = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
                        lot_details_data.lot_quantity = float(lot_quantity)
                    except Exception as e:
                        logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                        pass

                    lot_details_data.lot_details_cleanup()
                    notice_data.lot_details.append(lot_details_data)
                    lot_number += 1 
        except Exception as e:
            logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
            pass

        try:              
            attachments_data = attachments()

            attachments_data.external_url = page_details5.find_element(By.XPATH, "//*[contains(text(),'附件下载')]//following::a[1]").get_attribute('href')
            
            attachments_data.file_name = page_details5.find_element(By.XPATH, "//*[contains(text(),'附件下载')]//following::a[1]").text
            
            try:
                attachments_data.file_type = attachments_data.file_name.split('.')[-1]
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
        except Exception as e:
            logging.info("Exception in attachments: {}".format(type(e).__name__)) 
            pass
            
        try:
            page_details5.close()
            time.sleep(2)
        except Exception as e:
            logging.info("Exception in page_details5.close(): {}".format(type(e).__name__)) 
            pass
        
       
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
options = Options()
for argument in arguments:
    options.add_argument(argument)
page_main = webdriver.Chrome(options=options)

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['http://www.ccgp.gov.cn/cggg/zygg/gkzb/index.htm']
    for url in urls:
        fn.load_page(page_main,url, 20)
        logging.info('----------------------------------')
        logging.info(url)

        try:
            for page_no in range(1,20):
                page_check = WebDriverWait(page_main, 20).until(EC.presence_of_element_located((By.XPATH,'//*[@id="detail"]/div[2]/div/div[1]/div/div[2]/div[1]/ul/li'))).text
                rows = WebDriverWait(page_main, 260).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="detail"]/div[2]/div/div[1]/div/div[2]/div[1]/ul/li')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 260).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="detail"]/div[2]/div/div[1]/div/div[2]/div[1]/ul/li')))[records]  
    
                    #---------------------
                    page_details = webdriver.Chrome(options=options)
                    #---------------------
    
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
    
                page_main.close()
        
                url = url.split('index')[0]
                new_url = url+f'index_{page_no}.htm'
                
                page_main = fn.init_chrome_driver(arguments) 
                fn.load_page(page_main,new_url, 20)
                logging.info("Next page")
                logging.info(new_url)
                page_main.close()
        except:
            logging.info('No new record')
            break
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)
