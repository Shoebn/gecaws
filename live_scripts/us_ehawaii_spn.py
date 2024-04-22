from gec_common.gecclass import *
import logging
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
SCRIPT_NAME = "us_ehawaii_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    notice_data.script_name = 'us_ehawaii_spn'
    notice_data.main_language = 'EN'
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'US'
    notice_data.performance_country.append(performance_country_data)
    notice_data.currency = 'USD'
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 4


    url_num = WebDriverWait(tender_html_element, 80).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'td:nth-child(2)'))).text
    if url_num =='':
        page_main.refresh()
        time.sleep(5)
        url_num = WebDriverWait(tender_html_element, 80).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'td:nth-child(2)'))).text
    url_num = re.findall('\d+',url_num)[0]
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        notice_contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
        
        if 'Services' in notice_contract_type or 'Goods & Services' in notice_contract_type or 'Health and Human Services' in notice_contract_type or 'Professional Services' in notice_contract_type or 'Hybrid (combo of 2 or more categories)' in notice_contract_type:     
            notice_data.notice_contract_type = 'Service'
        elif 'Goods' in notice_contract_type:
            notice_data.notice_contract_type = 'Supply'
        elif 'Construction' in notice_contract_type:
            notice_data.notice_contract_type = 'Works'
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass

    try:
        notice_data.contract_type_actual = notice_contract_type
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(8)").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%m/%d/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(9)").text
        notice_deadline = re.findall('\d+/\d+/\d{4} \d+:\d+ [apAP][mM]',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%m/%d/%Y %I:%M %p').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    try:
        notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass       

    try:
        org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(6)').text  
    except Exception as e:
        logging.info("Exception in org_name: {}".format(type(e).__name__))
        pass

    try:
        org_address = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text   
    except Exception as e:
        logging.info("Exception in org_address: {}".format(type(e).__name__))
        pass

    try:
        org_city = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(7)').text  
    except Exception as e:
        logging.info("Exception in org_city: {}".format(type(e).__name__))
        pass  
    
    notice_url_click = tender_html_element
    page_main.execute_script("arguments[0].click();",notice_url_click)
    time.sleep(5)
    
    try:
        try:
            chk_data = WebDriverWait(page_main, 80).until(EC.presence_of_element_located((By.XPATH,'/html/body/app-root/dialog-holder/dialog-wrapper/div/app-modal-confirm/div/div[2]/p'))).text
        except:
            pass
        
        try:
            ok_click = page_main.find_elements(By.CSS_SELECTOR, "button.btn.btn-default").click()
        except:
            pass

        if "You are leaving HANDS and proceeding to the HIePRO State of Hawaii eProcurement website." in chk_data:
            notice_data.notice_url = "https://hiepro.ehawaii.gov/public-display-solicitation.html?rfid="+str(url_num)
            fn.load_page(page_details,notice_data.notice_url,80)
            logging.info(notice_data.notice_url)
        elif len(url_num)>=10:
            notice_data.notice_url = "https://hiepro.ehawaii.gov/public-display-solicitation.html?rfid="+str(url_num)
            fn.load_page(page_details,notice_data.notice_url,80)
            logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in ok_click: {}".format(type(e).__name__))    
        notice_url = page_main.current_url
        notice_data.notice_url = notice_url
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
        time.sleep(5)

    try:
        Bidding_Opportunities_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'(//*[contains(text(),"Bidding Opportunities")])[2]')))
        page_main.execute_script("arguments[0].click();",Bidding_Opportunities_click)
        time.sleep(15)
    except Exception as e:
        logging.info("Exception in Bidding_Opportunities_click: {}".format(type(e).__name__)) 
        pass
    
    try:
        WebDriverWait(page_main, 80).until(EC.presence_of_element_located((By.XPATH,'//*[@id="search_results"]/div/div[3]/table/tbody/tr'))).text
    except:
        pass
        
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#body-container > main').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')

    try:
        notice_data.category = page_details.find_element(By.XPATH, '//*[contains(text(),"Professional Services Category")]//following::td[1]').text  
    except Exception as e:
        logging.info("Exception in category: {}".format(type(e).__name__))
        pass

    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Solicitation Description")]//following::td[1]|(//*[contains(text(),"Description")]//following::dd)[1]').text   
        notice_data.notice_summary_english = notice_data.local_description
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass

    try:
        tender_contract_start_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Projected Start Date")]//following::td[1]').text  
        tender_contract_start_date = re.findall('\d+/\d+/\d{4}',tender_contract_start_date)[0]
        notice_data.tender_contract_start_date = datetime.strptime(tender_contract_start_date,'%m/%d/%Y').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in tender_contract_start_date: {}".format(type(e).__name__))
        pass

    try:
        tender_contract_end_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Projected End Date")]//following::td[1]').text  
        tender_contract_end_date = re.findall('\d+/\d+/\d{4}',tender_contract_end_date)[0]
        notice_data.tender_contract_end_date = datetime.strptime(tender_contract_end_date,'%m/%d/%Y').strftime('%Y/%m/%d %H:%M:%S')         
    except Exception as e:
        logging.info("Exception in tender_contract_end_date: {}".format(type(e).__name__))
        pass

    try:
        notice_data.grossbudgetlc = page_details.find_element(By.XPATH, '//*[contains(text(),"Approximate Funding Per Year")]//following::td[1]').text  
        grossbudgetlc = re.sub("[^\d\.\,]","",grossbudgetlc)
        notice_data.grossbudgetlc = float(grossbudgetlc.replace(",",'').strip())            
        notice_data.est_amount = notice_data.grossbudgetlc
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'app-opportunity-details   tab.active table:nth-child(4) > tbody > tr:nth-child(3) > td > span'):
            attachments_data = attachments()
            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'span > a').text
            try:
                attachments_data.file_type = attachments_data.file_name.split('.')[-1]
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'span > a').get_attribute('href')
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    try:              
        for single_record in page_details.find_elements(By.XPATH, '''//a[starts-with(@href, '/res')]'''):
            attachments_data = attachments()
            try:
                attachments_data.file_type = single_record.text.split('.')[-1]
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
            attachments_data.external_url = single_record.get_attribute('href')
            attachments_data.file_name = single_record.text.split(attachments_data.file_type)[0].strip()
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments2: {}".format(type(e).__name__)) 
        pass
        
    try:              
        customer_details_data = customer_details()

        customer_details_data.org_name = org_name
        customer_details_data.org_address = org_address
        customer_details_data.org_country = 'US'
        customer_details_data.org_language = 'EN'
        customer_details_data.org_city = org_city

        try:
            Contact_Information_click = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="body-container"]/main/app-opportunity-public/div/app-opportunity-details/div/div/div[2]/div/tabset/ul/li[2]/a')))
            page_details.execute_script("arguments[0].click();",Contact_Information_click)        
            time.sleep(10)
        except Exception as e:
            logging.info("Exception in Contact_Information_click: {}".format(type(e).__name__))
            pass

        try:
            customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Contact Name")]//following::td[1]|//*[contains(text(),"Contact Person")]//following::dd[1]').text   
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass

        try:
            customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Contact Phone")]//following::td[1]|//*[contains(text(),"Phone")]//following::dd[1]').text 
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass

        try:
            customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Contact Email")]//following::td[1]|//*[contains(text(),"Email")]//following::dd[1]').text 
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try:
        if notice_no is not None:
            notice_data.notice_no = notice_no
        else:
            notice_data.notice_no = notice_data.notice_url.split('/')[-1]
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    try:
        Line_Items = WebDriverWait(page_details, 80).until(EC.presence_of_element_located((By.XPATH,'(//*[contains(text(),"Line Items")])[1]'))).text
        if Line_Items !="":
            lot_url = notice_data.notice_url+"#tabs-2"
            fn.load_page(page_details1,lot_url,80)
            WebDriverWait(page_details1, 80).until(EC.presence_of_element_located((By.XPATH,'(//h4)[2]'))).text

        try:
            notice_data.notice_text += page_details1.find_element(By.CSS_SELECTOR, '#body-container > main').get_attribute("outerHTML")                     
        except:
            pass
    
        try:              
            for single_record in page_details1.find_elements(By.XPATH, '''(//*[contains(text(),"Attachments")])[1]//following::a[starts-with(@href, '/')]'''):
                attachments_data = attachments()
                try:
                    attachments_data.file_type = single_record.text.split('.')[-1]
                except Exception as e:
                    logging.info("Exception in file_type: {}".format(type(e).__name__))
                    pass
                attachments_data.external_url = single_record.get_attribute('href')
                attachments_data.file_name = single_record.text.split(attachments_data.file_type)[0].strip()
                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
        except Exception as e:
            logging.info("Exception in attachments3: {}".format(type(e).__name__)) 
            pass
    
    
        try:
            lot_data = []
            for single_record in page_details1.find_elements(By.XPATH, '//h4[@class="panel-title"]'):
                    lot_title = single_record.text
                    lot_data.append(lot_title)
                    clk_down_ar = single_record.find_element(By.CSS_SELECTOR, 'i.fa.chevron-toggler-icon').click()
                    time.sleep(5)

            try:
                for single_record in page_details1.find_elements(By.XPATH, '//*[@class="table-responsive"]//td[1]'):
                    cpv_code = single_record.text
                    cpv_codes_list = fn.procedure_mapping("assets/naics-codes.csv",cpv_code)
                    split_data = cpv_codes_list.split('#')
                    cpv_at_source = ''
                    for each_cpv in split_data:
                        cpvs_data = cpvs()
                        cpvs_data.cpv_code = each_cpv
                        cpv_at_source += each_cpv
                        cpv_at_source += ','
                        cpvs_data.cpvs_cleanup()
                        notice_data.cpvs.append(cpvs_data)
                    notice_data.cpv_at_source = cpv_at_source.rstrip(',')
                    notice_data.class_codes_at_source = notice_data.cpv_at_source
            except Exception as e:
                logging.info("Exception in cpvs: {}".format(type(e).__name__))
                pass
            
    
            lot_description_data = []
            for single_record in page_details1.find_elements(By.XPATH, '//*[@class="dl-horizontal"]')[1:]:
                lot_description = single_record.text.split("Description")[1].strip()
                lot_description_data.append(lot_description)

            lot_number = 1
            for title,description in zip(lot_data,lot_description_data):
                lot_details_data = lot_details()
                lot_details_data.lot_number = lot_number

                try:
                    lot_quantity = title.split('\n')[2].split('\n')[0].strip()
                    lot_details_data.lot_quantity = float(lot_quantity)
                except Exception as e:
                    logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                    pass

                try:
                    lot_details_data.lot_quantity_uom = title.split('\n')[3].split('\n')[0].strip()
                except Exception as e:
                    logging.info("Exception in lot_quantity_uom: {}".format(type(e).__name__))
                    pass

                lot_details_data.lot_title = title.split('\n')[1].split(lot_quantity)[0].strip()

                try:
                    lot_details_data.lot_description = description
                except:
                    pass

        
                try:
                    lot_cpv_code = title.split('\n')[4].strip()
                    for single_records in lot_cpv_code.split(','):
                        lot_cpv_code = fn.procedure_mapping("assets/naics-codes.csv",single_records.strip())
                        split_data = lot_cpv_code.split('#')
                        lot_cpv_at_source = ''
                        for each_cpv in split_data:
                            lot_cpvs_data = lot_cpvs()
                            lot_cpvs_data.lot_cpv_code = each_cpv
                            lot_cpv_at_source += each_cpv
                            lot_cpv_at_source += ','
                            lot_cpvs_data.lot_cpvs_cleanup()
                            lot_details_data.lot_cpvs.append(lot_cpvs_data)
                        lot_details_data.lot_cpv_at_source = lot_cpv_at_source.rstrip(',')
                        lot_details_data.lot_class_codes_at_source = lot_details_data.lot_cpv_at_source
                except Exception as e:
                    logging.info("Exception in lot_cpvs: {}".format(type(e).__name__))
                    pass

                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
                lot_number += 1
        except Exception as e:
            logging.info("Exception in lot_details: {}".format(type(e).__name__))
            pass
    except:
        pass
    
    try:
        page_main.refresh()
        time.sleep(5)
    except:
        pass
    try:
        WebDriverWait(page_main, 80).until(EC.presence_of_element_located((By.XPATH,'//*[@id="search_results"]/div/div[3]/table/tbody/tr[1]'))).text
    except:
        pass

    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title) 
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments) 
page_details = fn.init_chrome_driver(arguments)
page_details1 = fn.init_chrome_driver(arguments)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://hands.ehawaii.gov/hands/opportunities"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        page_main.refresh()
        
        
        drop_down = WebDriverWait(page_main, 120).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="search_results"]/div/div[2]/select'))).click()
        time.sleep(5)
        select_all = WebDriverWait(page_main, 120).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="search_results"]/div/div[2]/select/option[5]'))).click()
        time.sleep(5)
        
        rows = WebDriverWait(page_main, 120).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@class="ng-star-inserted"]//following::tr')))
        length = len(rows)

        for records in range(1,length):
            tender_html_element = WebDriverWait(page_main, 150).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@class="ng-star-inserted"]//following::tr')))[records]
            extract_and_save_notice(tender_html_element)
            if notice_count >= MAX_NOTICES:
                break

            if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                break

            if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                break

    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit()
    page_details1.quit() 
    output_json_file.copyFinalJSONToServer(output_json_folder)
