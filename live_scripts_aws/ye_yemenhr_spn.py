from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "ye_yemenhr_spn"
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


#Note..There are lots of different format find for this source.. we have identify 10 format but if whicle scrpping thissource get more format take the data in html body


NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "ye_yemenhr_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.script_name = 'ye_yemenhr_spn'
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'YE'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'AR'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_type = 4
    
    # Onsite Field -Title
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.flex.items-baseline.col-span-7 > a > p').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Deadline
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "div > div > div > div:nth-child(4)").text
        notice_deadline = re.findall('\d+ \w+. \d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d %b. %Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    try:              
        customer_details_data = customer_details()
    # Onsite Field -Organization
    # Onsite Comment -None


        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div.flex.items-center.justify-between.col-span-2 > a > span').text



    # Onsite Field -Location
    # Onsite Comment -None

        try:
            customer_details_data.org_city = tender_html_element.find_element(By.CSS_SELECTOR, 'div > div:nth-child(3) > a > span').text
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass

        customer_details_data.org_country = 'YE'
        customer_details_data.org_language = 'AR'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.flex.items-baseline.col-span-7 > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -Posted on
    # Onsite Comment -Note:Splite after "Posted on" this keyword

    try:
        publish_date = page_details.find_element(By.CSS_SELECTOR, "div.mt-1 div:nth-child(3)").text
        publish_date = re.findall('\d+ \w+, \d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d %b, %Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
#     # Onsite Field -None
#     # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.lg\:grid-flow-col-dense.lg\:grid-cols-1').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    notice_text = page_details.find_element(By.CSS_SELECTOR, 'div.lg\:grid-flow-col-dense.lg\:grid-cols-1').text
# #Format 1.https://yemenhr.com/tenders/9a85b528-e0a4-4d12-9003-57ef1731e60f    

#     # Onsite Field -Period of Bid validity
#     # Onsite Comment -None
    if 'Period of Bid validity' in notice_text or 'صلاحية العطاء' in notice_text:

        try:
            notice_data.contract_duration = page_details.find_element(By.XPATH, '/html/body/div[2]/main/div[2]/main/div[2]/div[1]/section[1]/div/div/div[2]/span/table/tbody/tr[2]/td[4]/p[2]/span/strong/span/span').text
        except:
            try:
                notice_data.contract_duration = page_details.find_element(By.CSS_SELECTOR, 'tr:nth-child(2) > td:nth-child(5)').text
            except Exception as e:
                logging.info("Exception in contract_duration: {}".format(type(e).__name__))
                
                pass
    if 'وصف المناقصة' in notice_text :
        try:
            notice_data.local_description = page_details.find_element(By.CSS_SELECTOR, 'tr:nth-child(2) > td:nth-child(7)').text
            notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_descriptio)
        except:
            try:
                notice_data.local_description = page_details.find_element(By.CSS_SELECTOR, 'tr:nth-child(3) > td:nth-child(1)').text
                notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_descriptio)
            except:
                try:
                    notice_data.local_description = page_details.find_element(By.CSS_SELECTOR, 'tr:nth-child(2) > td:nth-child(3)').text
                    notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_descriptio)
                except Exception as e:
                    logging.info("Exception in local_description: {}".format(type(e).__name__))
                    pass



#     # Onsite Field -General Tender Number
#     # Onsite Comment -None
    try:
        if 'General Tender Number' in notice_text or 'رقم المناقصة:' in notice_text or 'REFERENCE' in notice_text or 'Tender No' in notice_text or 'Number Tender' in notice_text or 'Tender No' in notice_data.notice_text or 'مرجع المناقصة' in notice_data.notice_text : 
            try:
                notice_data.notice_no = page_details.find_element(By.CSS_SELECTOR, 'tr:nth-child(2) > td:nth-child(8)').text
            except:
                try:
                    notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"رقم المناقصة:")]').text
                except:
                    try:
                        notice_data.notice_no = norice_text.split('REFERENCE')[1].split('/n')[0]
                    except:
                        try:
                            notice_data.notice_no = page_details.find_element(By.CSS_SELECTOR,'tr:nth-child(2) > td:nth-child(10)').text
                        except:
                            try:
                                notice_data.notice_no = page_details.find_element(By.CSS_SELECTOR, 'table:nth-child(15) tr:nth-child(2) > td:nth-child(1)').text
                            except:
                                try:
                                    notice_data.notice_no = page_details.find_element(By.CSS_SELECTOR, 'table.GridTable4-Accent51 tr:nth-child(2) > td:nth-child(1)').text
                                except:
                                    try:
                                        notice_data.notice_no = page_details.find_element(By.CSS_SELECTOR, 'tr:nth-child(2) > td:nth-child(4)').text
                                    except:
                                        try:
                                            notice_data.notice_no = notice_data.otice_text.split('Tender No.')[1].split('/n')[0]
                                        except:
                                            try:
                                                notice_data.notice_no = page_details.find_element(By.CSS_SELECTOR, 'body > div.min-h-screen.bg-gray-100 > main > div.max-w-7xl.mx-auto.px-4.sm\:px-6.mb-0 > main > div.mt-1.max-w-7xl.mx-6.md\:mx-auto.grid.grid-cols-1.gap-3.sm\:px-6.lg\:max-w-7xl.lg\:grid-flow-col-dense.lg\:grid-cols-1 > div.lg\:col-start-1.lg\:col-span-1 > section.mb-2 > div > div > div.px-4.py-6.sm\:px-6 > span > p:nth-child(3)').text
                                            except:
                                                pass
        try:
            if 'Tender Number:' in notice_data.notice_text:
                notice_data.notice_no = notice_data.notice_text.split('Tender Number:')[1].split('-')[0]
        except Exception as e:
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass
    except:
        pass

    notice_data.currency = 'YER'

        
    if 'اسم المشروع' in notice_text or 'Project Name' in notice_text:
        try:
            notice_data.project_name = page_details.find_element(By.XPATH, '//*[contains(text(),"اسم المشروع")]').text
        except:
            try:
                notice_data.project_name = page_details.find_element(By.CSS_SELECTOR, 'tr:nth-child(2) > td:nth-child(9)').text
            except:
                try:
                    notice_data.project_name =notice_text.split("Project Name:")[1].split('\n')[0]
                except:
                    try:
                        notice_data.project_name = page_details.find_element(By.CSS_SELECTOR, 'table.GridTable4-Accent51 tr:nth-child(3) > td:nth-child(1)').text
                    except Exception as e:
                        logging.info("Exception in project_name: {}".format(type(e).__name__))
                        pass

    if 'مصدر التمويل' in notice_data.notice_text or 'Tendering Organization' in notice_data.notice_text or 'مصدر التمويل' in notice_data.notice_text or 'Funding source' in notice_data.notice_text or 'Donor' in notice_data.notice_text:

            # Onsite Field -Fund source
            # Onsite Comment -None
        try:
            try:
                funding_agencies_data = funding_agencies()
                funding_agency = page_details.find_element(By.CSS_SELECTOR, 'tr:nth-child(2) > td:nth-child(6)').text
                funding_agencies_data.funding_agency = fn.procedure_mapping("assets/ye_yemenhr_spn_fundingagencycode.csv",funding_agency)
            except Exception as e:
                logging.info("Exception in funding_agency: {}".format(type(e).__name__))
                pass

                funding_agencies_data.funding_agencies_cleanup()
                notice_data.funding_agencies.append(funding_agencies_data)
        except:
            try:
                try:
                    funding_agencies_data = funding_agencies()
                    funding_agency = page_details.find_element(By.XPATH, '//*[contains(text(),"Tendering Organization")]').text
                    funding_agencies_data.funding_agency = fn.procedure_mapping("assets/ye_yemenhr_spn_fundingagencycode.csv",funding_agency)
                except Exception as e:
                    logging.info("Exception in funding_agency: {}".format(type(e).__name__))
                    pass

                funding_agencies_data.funding_agencies_cleanup()
                notice_data.funding_agencies.append(funding_agencies_data)
            except:
                try:
                    funding_agencies_data = funding_agencies()
#         # Onsite Field -مصدر التمويل
#         # Onsite Comment -None

                    try:
                        funding_agency = page_details.find_element(By.CSS_SELECTOR, 'tr:nth-child(2) > td:nth-child(7)').text
                        funding_agencies_data.funding_agency = fn.procedure_mapping("assets/ye_yemenhr_spn_fundingagencycode.csv",funding_agency)
                    except Exception as e:
                        logging.info("Exception in funding_agency: {}".format(type(e).__name__))
                        pass
        
                    funding_agencies_data.funding_agencies_cleanup()
                    notice_data.funding_agencies.append(funding_agencies_data)
                except:
                    try:
                        funding_agencies_data = funding_agencies()
#         # Onsite Field -Funding source
#         # Onsite Comment -None

                        try:
                            funding_agency = page_details.find_element(By.CSS_SELECTOR, 'table:nth-child(15) tr:nth-child(2) > td:nth-child(3)').text
                            funding_agencies_data.funding_agency = fn.procedure_mapping("assets/ye_yemenhr_spn_fundingagencycode.csv",funding_agency)
                        except Exception as e:
                            logging.info("Exception in funding_agency: {}".format(type(e).__name__))
                            pass
        
                        funding_agencies_data.funding_agencies_cleanup()
                        notice_data.funding_agencies.append(funding_agencies_data)
                    except:
                        try:
                            funding_agencies_data = funding_agencies()
#         # Onsite Field -Donor
#         # Onsite Comment -None

                            try:
                                funding_agency = page_details.find_element(By.CSS_SELECTOR, 'table:nth-child(19) > tbody > tr:nth-child(2) > td:nth-child(1)').text
                                funding_agencies_data.funding_agency = fn.procedure_mapping("assets/ye_yemenhr_spn_fundingagencycode.csv",funding_agency)
                            except Exception as e:
                                logging.info("Exception in funding_agency: {}".format(type(e).__name__))
                                pass
        
                            funding_agencies_data.funding_agencies_cleanup()
                            notice_data.funding_agencies.append(funding_agencies_data)
                        except:
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
page_details = fn.init_chrome_driver(arguments) 
page_main = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://yemenhr.com/tenders"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,10):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[2]/main/div[2]/main/div/div[2]/div[2]/div/div/div'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[2]/main/div[2]/main/div/div[2]/div[2]/div/div/div')))
            length = len(rows)
            for records in range(1,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[2]/main/div[2]/main/div/div[2]/div[2]/div/div/div')))[records]
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/div[2]/main/div[2]/main/div/div[2]/div[2]/div/div/div'),page_check))
            except Exception as e:
                logging.info("Exception in next_page: {}".format(type(e).__name__))
                logging.info("No next page")
                break
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit() 
    
    output_json_file.copyFinalJSONToServer(output_json_folder)