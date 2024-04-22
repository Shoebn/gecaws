import time
from gec_common.gecclass import *
import logging
import re
import time
import jsons
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from deep_translator import GoogleTranslator
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn
import gec_common.Doc_Download
from selenium.webdriver.support.ui import Select

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "us_txsmartbuy_ca"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    notice_data.script_name = "us_txsmartbuy_ca"
    
    notice_data.main_language = 'EN'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'US'
    notice_data.performance_country.append(performance_country_data)
    notice_data.currency = 'USD'
    notice_data.procurement_method = 2
    notice_data.notice_type = 7

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR,'div.esbd-result-title a').get_attribute('href') 
        fn.load_page(page_details,notice_data.notice_url,80)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, ' div.esbd-result-title').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass  
    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
        notice_data.notice_text += page_details.find_element(By.XPATH, '//*[@id="content"]/div/div/div[2]').get_attribute("outerHTML")                     
    except:
        pass
    
    if urls[0]==url2:
        try:
            notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR,' div.esbd-result-body-columns > div:nth-child(1) > p:nth-child(1)').text.split(':')[1]
        except Exception as e:
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass
        
        try:
            publish_date =tender_html_element.find_element(By.CSS_SELECTOR, 'div.esbd-result-body-columns > div:nth-child(2) > p:nth-child(3)').text.split(':')[1].strip()
            notice_data.publish_date = datetime.strptime(publish_date,'%m/%d/%Y').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.publish_date)
        except Exception as e:
            logging.info("Exception in publish_date: {}".format(type(e).__name__))
            pass
    
        if notice_data.publish_date is not None and notice_data.publish_date < threshold:
            return                
        try:
            text1 = page_details.find_element(By.XPATH, '//*[@id="content"]/div/div/div[2]').text
            notice_data.local_description = re.findall(r'Solicitation Description:\s*(.*?)\n',text1)[0]
            notice_data.notice_summary_english = notice_data.local_description
        except Exception as e:
            logging.info("Exception in local_description: {}".format(type(e).__name__))
            pass
        try:
            customer_details_data = customer_details()
            customer_details_data.org_country = 'US'
            customer_details_data.org_language = 'EN'
            try:
                org_name = notice_data.local_description
                if '(' in org_name:
                    customer_details_data.org_name=org_name.split('(')[0]
                else:
                    customer_details_data.org_name = org_name
            except:
                customer_details_data.org_name = 'txsmartbuy'
      
        
            try:
                customer_details_data.contact_person = page_details.find_element(By.XPATH,"//*[contains(text(),'Contact Name:')]//following::p[1]").text
            except:
                pass
            try:
                customer_details_data.org_email = page_details.find_element(By.XPATH,"//*[contains(text(),'Contact Email: ')]//following::p[1]").text
            except:
                pass
            try:
                customer_details_data.org_phone = page_details.find_element(By.XPATH,"//*[contains(text(),'Contact Number:')]//following::p[1]").text
            except:
                pass
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
        except Exception as e:
            logging.info("Exception in customer_details_data: {}".format(type(e).__name__))
            pass 
            
        try:
            notice_data.tender_contract_number =  page_details.find_element(By.XPATH,"//*[contains(text(),'Contact Number:')]//following::p[1]").text
        except Exception as e:
            logging.info("Exception in tender_contract_number: {}".format(type(e).__name__))
            pass
        try:              
            lot_details_data = lot_details()
            lot_details_data.lot_title = notice_data.local_title
            lot_details_data.lot_number = 1
            notice_data.is_lot_default = True
            try:
                award_details_data = award_details()
        
                award_details_data.bidder_name = page_details.find_element(By.CSS_SELECTOR, '#content > div > div > div.esbd-container > div:nth-child(4) > div.esbd-awards-row > div:nth-child(1)').text
                try:
                    grossawardvaluelc = page_details.find_element(By.CSS_SELECTOR, '#content > div > div > div.esbd-container > div:nth-child(4) > div.esbd-awards-row > div:nth-child(3)').text  
                    award_details_data.grossawardvaluelc = float(grossawardvaluelc)
                except:
                    pass
                try:
                    address = page_details.find_element(By.CSS_SELECTOR, '#content > div > div > div.esbd-container > div:nth-child(4) > div.esbd-awards-row > div:nth-child(2)').text  
                    award_details_data.address = address
                except:
                    pass
        
                try:
                    award_date = page_details.find_element(By.CSS_SELECTOR, '#content > div > div > div.esbd-container > div:nth-child(4) > div.esbd-awards-row > div:nth-child(5)').text  
                    award_details_data.award_date = datetime.strptime(award_date,'%m/%d/%Y').strftime('%Y/%m/%d')
                except:
                    pass
                
                award_details_data.award_details_cleanup()
                lot_details_data.award_details.append(award_details_data)
            except Exception as e:
                logging.info("Exception in award_details: {}".format(type(e).__name__))
                pass
        
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
        except Exception as e:
            logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
            pass

    
        try:
            for single_record in page_details.find_elements(By.CSS_SELECTOR,'#tab-1 > div:nth-child(3) > div'):
                attachments_data = attachments()
                attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR," div > p:nth-child(2)").text
                attachments_data.file_type = attachments_data.file_name.split('.')[-1]
                attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR," div > p:nth-child(2) a").get_attribute('data-href')
                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
        except Exception as e:
            logging.info("Exception in external_url: {}".format(type(e).__name__)) 
            pass


        try:
            notice_data.class_at_source = 'CPV'
            cpv_code = page_details.find_element(By.XPATH, "//*[contains(text(),'Class/Item Code:')]//following::p[1]").text
            cpv_code_title = re.split("\d{5}-", cpv_code)
            class_title_at_source = ''
            for cpv_title in cpv_code_title[1:]:
    
                class_title_at_source += cpv_title.strip()
                class_title_at_source += ','
            notice_data.class_title_at_source = class_title_at_source.rstrip(',')
        except Exception as e:
            logging.info("Exception in class_title_at_source1: {}".format(type(e).__name__)) 
            pass

        try:
            class_codes_at_source = ''
            codes_at_source = page_details.find_element(By.XPATH, "//*[contains(text(),'Class/Item Code:')]//following::p[1]").text
            cpv_regex = re.compile(r'\d{5}')
            code_list = cpv_regex.findall(codes_at_source)
            for cpv_codes in code_list:
                class_codes_at_source += cpv_codes
                class_codes_at_source += ','
            notice_data.class_codes_at_source = class_codes_at_source.rstrip(',')
        except:
            pass
        
        try:
            
            cpv_at_source = ''
            codes_at_source = page_details.find_element(By.XPATH, "//*[contains(text(),'Class/Item Code:')]//following::p[1]").text
            cpv_regex = re.compile(r'\d{5}')
            code_list = cpv_regex.findall(codes_at_source)
            for cpv_codes in code_list:
                cpv_codes_list = fn.CPV_mapping("assets/NIGPcode.csv",cpv_codes)
                for each_cpv in cpv_codes_list:
                    cpvs_data = cpvs()
                    cpvs_data.cpv_code = each_cpv
                    cpv_at_source += each_cpv
                    cpv_at_source += ','
                    cpvs_data.cpvs_cleanup()
                    notice_data.cpvs.append(cpvs_data)
            notice_data.cpv_at_source = cpv_at_source.rstrip(',')
        except:
            pass

        
    
    else:    

        try:
            notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR,' div.esbd-result-body-columns > div:nth-child(1) > p:nth-child(1)').text.split(':')[1]
        except Exception as e:
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass
        try:
            est_amount = tender_html_element.find_element(By.CSS_SELECTOR,'div:nth-child(1) > p:nth-child(2)').text.split(':')[1]
            est_amount = est_amount.replace(',','')
            notice_data.est_amount=float(est_amount)
            notice_data.grossbudgetlc = notice_data.est_amount 
        except Exception as e:
            logging.info("Exception in est_amount: {}".format(type(e).__name__))
            pass
    
        try:
            customer_details_data = customer_details()
            customer_details_data.org_country = 'US'
            customer_details_data.org_language = 'EN'
            customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR,'div:nth-child(1) > p:nth-child(4)').text.split(':')[1].split(' -')[0]
                                                                              
            try:
                customer_details_data.org_email = tender_html_element.find_element(By.CSS_SELECTOR,'div:nth-child(1) > p:nth-child(5)').text.split(':')[1]
            except:
                pass
                
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
        except Exception as e:
            logging.info("Exception in customer_details: {}".format(type(e).__name__))
            pass    
    
        try:              
            lot_details_data = lot_details()
            lot_details_data.lot_title = notice_data.local_title
            lot_details_data.lot_number =1
            notice_data.is_lot_default = True
            try:
                award_details_data = award_details()
                
                award_details_data.bidder_name = tender_html_element.find_element(By.CSS_SELECTOR,'div:nth-child(2) > p:nth-child(1)').text.split(':')[1]            
                try:
                    award_date = tender_html_element.find_element(By.CSS_SELECTOR,'div:nth-child(2) > p:nth-child(5)').text.split(':')[1].strip()
                    award_details_data.award_date = datetime.strptime(award_date,'%m/%d/%Y').strftime('%Y/%m/%d')
                except:
                    pass
                
                award_details_data.award_details_cleanup()
                lot_details_data.award_details.append(award_details_data)
            except Exception as e:
                logging.info("Exception in award_details: {}".format(type(e).__name__))
                pass
        
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
        except Exception as e:
            logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
            pass
        try:
            publish_date =tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(2) > p:nth-child(5)').text.split(':')[1].strip()
            notice_data.publish_date = datetime.strptime(publish_date,'%m/%d/%Y').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.publish_date)
        except Exception as e:
            logging.info("Exception in publish_date: {}".format(type(e).__name__))
            pass
        if notice_data.publish_date is not None and notice_data.publish_date < threshold:
            return

        try:
            notice_data.local_description = page_details.find_element(By.XPATH,"//*[contains(text(),'Description:')]//parent::p").text.split('Description:   ')[1]
            notice_data.notice_summary_english = notice_data.local_description
        except Exception as e:
            logging.info("Exception in local_description: {}".format(type(e).__name__))
            pass
        try:
            notice_data.class_at_source = 'CPV'
            cpv_code = page_details.find_element(By.XPATH, "//*[contains(text(),'NIGP Codes:')]//parent::p").text.split(':')[1].strip()
            cpv_code_title = re.split("\d{5}-", cpv_code)
            class_title_at_source = ''
            for cpv_title in cpv_code_title[1:]:
                class_title_at_source += cpv_title.strip()
                class_title_at_source += ','
            notice_data.class_title_at_source = class_title_at_source.rstrip(',')
        except Exception as e:
            logging.info("Exception in class_title_at_source1: {}".format(type(e).__name__)) 
            pass
        try:
            class_codes_at_source = ''
            cpv_at_source = ''
            codes_at_source = page_details.find_element(By.XPATH, "//*[contains(text(),'NIGP Codes:')]//parent::p").text.split(':')[1].strip()
            cpv_regex = re.compile(r'\d{5}')
            code_list = cpv_regex.findall(codes_at_source)
            for cpv_codes in code_list:
                cpv_codes_list = fn.CPV_mapping("assets/NIGPcode.csv",cpv_codes)
                for each_cpv in cpv_codes_list:
                    cpvs_data = cpvs()
                    cpvs_data.cpv_code = each_cpv
                    cpv_at_source += each_cpv
                    cpv_at_source += ','
                    class_codes_at_source += cpv_codes
                    class_codes_at_source += ','
    
                    cpvs_data.cpvs_cleanup()
                    notice_data.cpvs.append(cpvs_data)
    
            notice_data.class_codes_at_source = class_codes_at_source.rstrip(',')
            notice_data.cpv_at_source = cpv_at_source.rstrip(',')
        except Exception as e:
            logging.info("Exception in cpv_code: {}".format(type(e).__name__)) 
            pass

    notice_data.identifier =  str(notice_data.notice_no) + str(notice_data.publish_date) +  str(notice_data.notice_url) 
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments) 
page_details = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    
    urls = ['https://www.txsmartbuy.com/esbd?&page=','https://www.txsmartbuy.com/esbdawards?page='] 
    
    for url2 in urls:
        for page_no in range(1,10):
            if urls[0]:
                url= url2 + str(page_no) +'&status=2'
            else:
                url= url2 + str(page_no)
            fn.load_page(page_main, url)
            logging.info('----------------------------------')           
            logging.info(url)
    
            try:
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#content > div > div > div:nth-child(5) > div.esbd-margin-top > div'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#content > div > div > div:nth-child(5) > div.esbd-margin-top > div')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#content > div > div > div:nth-child(5) > div.esbd-margin-top > div')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
        
                    if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                        logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
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
