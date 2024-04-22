
from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "us_vssky"
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
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import Select


NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "us_vssky"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.main_language = 'EN'
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'US'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'USD'
    notice_data.procurement_method = 2

    if itrator==5:
        notice_data.notice_type = 16
        notice_data.script_name = 'us_vssky_amd'
        
    elif itrator==6:
        notice_data.notice_type = 7
        notice_data.script_name = 'us_vssky_ca'
    else:
        notice_data.notice_type = 4
        notice_data.script_name = 'us_vssky_spn'
        
    
    notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(2) > div > div').text
    notice_data.notice_title  = notice_data.local_title

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(4) > div > div > div:nth-child(1)').text      
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    try:
        if itrator!=6:
            notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(4) > div > div > div:nth-child(2)').text   
        else:
            notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(5) > div > div > div:nth-child(3)').text   
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass    

    try:
        category = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(4) > div > div > div:nth-child(3)').text  
        if '-' not in category:
            notice_data.category = category
    except Exception as e:
        logging.info("Exception in category: {}".format(type(e).__name__))
        pass    
    
    try:
        cpv_codes = fn.CPV_mapping("assets/us_vssky_category.csv",notice_data.category)
        for cpv_code in cpv_codes:
            cpvs_data = cpvs()
            cpvs_data.cpv_code = cpv_code
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in category: {}".format(type(e).__name__))
        pass

    try:
        if itrator!=6:
            notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(5) > div > div > div:nth-child(1)").text  
            notice_deadline = re.findall('\d+/\d+/\d+ \d+:\d+ [apAP][mM]', notice_deadline)[0]
            notice_data.notice_deadline = datetime.strptime(notice_deadline, '%m/%d/%Y %I:%M %p').strftime('%Y/%m/%d %H:%M:%S')   
            logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
        
    try:
        org_name = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(3) > div > div > div:nth-child(1)").text  
    except Exception as e:
        logging.info("Exception in org_name: {}".format(type(e).__name__))
        pass   
          
    notice_data.notice_url = url
    try:
        notice_data.notice_text += tender_html_element.find_element(By.CSS_SELECTOR,'//*[@id="vsspageVVSSX10019gridView1group1cardGridgrid1"]/tbody/tr').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    try:
        Description_click = WebDriverWait(tender_html_element, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'td:nth-child(1) > button'))).click()  
        logging.info("Description_click")
        time.sleep(7)    
    except Exception as e:
        logging.info("Exception in Description_click: {}".format(type(e).__name__))
        pass     

    tender_html_element_2 = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="vsspageVVSSX10019gridView1group1cardGridgrid1"]/tbody/tr')))[records+1]  

    try:
        publish_date = tender_html_element_2.find_element(By.XPATH, '//*[contains(text(),"Published On")]//following::div[1]').text  
        notice_data.publish_date = datetime.strptime(publish_date,'%m/%d/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    try:
        document_opening_time = tender_html_element_2.find_element(By.XPATH, '//*[contains(text(),"Bid Opening Date")]//following::div[1]').text  
        notice_data.document_opening_time = datetime.strptime(document_opening_time,'%m/%d/%Y').strftime('%Y-%m-%d')
        logging.info(notice_data.document_opening_time)
    except Exception as e:
        logging.info("Exception in document_opening_time: {}".format(type(e).__name__))
        pass

    try:        
        Description_click = WebDriverWait(tender_html_element, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'td:nth-child(1) > button'))).click()  
        logging.info("Description_click")
        time.sleep(10)    
    except Exception as e:
        logging.info("Exception in Description_click: {}".format(type(e).__name__))
        pass    

    try:
        Solicitation_Number_click = WebDriverWait(tender_html_element, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'td:nth-child(4) > div > div > div:nth-child(1) > div > div > div'))).click()  
        logging.info("Solicitation_Number_click")
        time.sleep(7)
    except Exception as e:
        logging.info("Exception in Solicitation_Number_click: {}".format(type(e).__name__))
        pass  

    try:
        notice_data.notice_text += page_main.find_element(By.XPATH,"//div[contains(@class,'css-1cqfa28')]").get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
        
    try:
        customer_details_data = customer_details()
        customer_details_data.org_country = 'US'
        customer_details_data.org_language = 'EN'

        try:
            customer_details_data.org_name = org_name
        except Exception as e:
            logging.info("Exception in org_name: {}".format(type(e).__name__))
            pass          
                
        try:
            customer_details_data.contact_person = page_main.find_element(By.XPATH, '//*[contains(text(),"Buyer Name")]//following::div[1]').text
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass                
            
        try:
            org_email = page_main.find_element(By.XPATH, '//*[contains(text(),"Buyer Email")]//following::div[1]').text 
            if len(org_email)>3:
                customer_details_data.org_email = org_email
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass   
        
        try:
            org_phone = page_main.find_element(By.XPATH, '//*[contains(text(),"Buyer Phone")]//following::div[1]').text  
            if len(org_phone)>3:
                customer_details_data.org_phone = org_phone
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass           
            
        try:
            org_fax = page_main.find_element(By.XPATH, '//*[contains(text(),"Buyer Fax")]//following::div[1]').text  
            if len(org_fax)>3:
                customer_details_data.org_fax = org_fax
        except Exception as e:
            logging.info("Exception in org_fax: {}".format(type(e).__name__))
            pass           
            
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass    

    try:
        Commodity_lines_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[contains(text(),"Commodity Lines")]')))  
        page_main.execute_script("arguments[0].click();",Commodity_lines_click)
        logging.info("Commodity_lines_click")
        time.sleep(5)
    except Exception as e:
        logging.info("Exception in Commodity_ines_click: {}".format(type(e).__name__))
        pass          

    try:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, '#display_center_center').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    try:
        if itrator!=6:
            local_description_new ='' 
            for single_record in page_main.find_elements(By.CSS_SELECTOR, 'div.css-dph8ak > adv-detail-list > table > tbody > tr'):  
                local_description = single_record.find_element(By.CSS_SELECTOR,"td:nth-child(2)").text
                local_description_new += local_description + ", "
            notice_data.local_description = local_description_new[:-2]
            notice_data.notice_summary_english = notice_data.local_description 

        else:
            local_description_new ='' 
            for single_record in page_main.find_elements(By.CSS_SELECTOR, 'div.css-dph8ak > adv-detail-list > table > tbody > tr'):  
                local_description = single_record.find_element(By.CSS_SELECTOR,"td:nth-child(2)").text

                local_description_new += local_description + ", "

            notice_data.local_description = local_description_new[:-2]
            notice_data.notice_summary_english = notice_data.local_description 
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass    

        try:
            tender_quantity_new = ''
            for single_record in page_main.find_elements(By.CSS_SELECTOR, 'div.css-dph8ak > adv-detail-list > table > tbody > tr'):  
                tender_quantity = single_record.find_element(By.CSS_SELECTOR,"td:nth-child(4) > div  > adv-scalar-2-react > div > div:nth-child(1) > div > div > div:nth-child(2)").text
                if '/' not in tender_quantity:
                    tender_quantity_new += tender_quantity + ", "
            notice_data.tender_quantity = tender_quantity_new[:-2]
        except Exception as e:
            logging.info("Exception in tender_quantity: {}".format(type(e).__name__))
            pass    

        try:
            tender_quantity_uom_new = ''
            for single_record in page_main.find_elements(By.CSS_SELECTOR, 'div.css-dph8ak > adv-detail-list > table > tbody > tr'):  
                tender_quantity_uom = single_record.find_element(By.CSS_SELECTOR,"td:nth-child(4) > div  > adv-scalar-2-react > div > div:nth-child(2) > div > div > div:nth-child(2)").text 
                if '/' not in tender_quantity_uom:
                    tender_quantity_uom_new += tender_quantity_uom + ", "
            notice_data.tender_quantity_uom = tender_quantity_uom_new[:-2]
        except Exception as e:
            logging.info("Exception in tender_quantity_uom: {}".format(type(e).__name__))
            pass    
    
    try:
        class_codes_at_source_new = ''
        for single_record in page_main.find_elements(By.CSS_SELECTOR, 'div.css-dph8ak > adv-detail-list > table > tbody > tr'):  
            class_codes_at_source = single_record.find_element(By.CSS_SELECTOR,"td:nth-child(3) > div  > adv-scalar-2-react > div > div:nth-child(2) > div > div > div:nth-child(2)").text
            class_codes_at_source_new += class_codes_at_source + ", "
        notice_data.class_codes_at_source = class_codes_at_source_new[:-2]

    except Exception as e:
        logging.info("Exception in class_codes_at_source: {}".format(type(e).__name__))
        pass        
    
    try:
        tender_contract_start_date = page_main.find_element(By.XPATH, '//*[contains(text(),"Service From")]//following::div[1]').text.strip()   
        notice_data.tender_contract_start_date = datetime.strptime(tender_contract_start_date, '%m/%d/%Y').strftime('%Y/%m/%d %H:%M:%S')  
    except Exception as e:
        logging.info("Exception in tender_contract_start_date: {}".format(type(e).__name__))
        pass       
    
    try:
        tender_contract_end_date = page_main.find_element(By.XPATH, '//*[contains(text(),"Service To")]//following::div[1]').text.strip()   
        notice_data.tender_contract_end_date = datetime.strptime(tender_contract_end_date, '%m/%d/%Y').strftime('%Y/%m/%d %H:%M:%S')  
    except Exception as e:
        logging.info("Exception in tender_contract_end_date: {}".format(type(e).__name__))
        pass  
    
    try:
        Attachments_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[contains(text(),"Attachments")]')))  
        page_main.execute_script("arguments[0].click();",Attachments_click)
        logging.info("Attachments_click")
        time.sleep(7)
    except Exception as e:
        logging.info("Exception in Attachments_click: {}".format(type(e).__name__))
        pass          

    try:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, '#display_center_center').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    try:              
        for single_record in page_main.find_elements(By.CSS_SELECTOR, 'div:nth-child(2) > table > tbody > tr'):
            attachments_data = attachments()
            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR,'td:nth-child(1)').text
            try:
                attachments_data.file_type = attachments_data.file_name.split('.')[-1]
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass

            external_url = WebDriverWait(single_record, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"td:nth-child(1) > div > div > div > span > span > span > div > button"))) 
            page_main.execute_script("arguments[0].click();",external_url)
            time.sleep(5)
            file_dwn = Doc_Download.file_download()
            external_url = str(file_dwn[0]) 
            attachments_data.external_url = external_url.split(' ')[0]
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass  

    try:
        Solicitation_Instructions_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[contains(text(),"Solicitation Instructions")]')))  
        page_main.execute_script("arguments[0].click();",Solicitation_Instructions_click)
        logging.info("Solicitation_Instructions_click")
        time.sleep(10)
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, '#display_center_center').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in Solicitation_Instructions_click: {}".format(type(e).__name__))
        pass       
    
    try:
        Evaluation_Criteria_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[contains(text(),"Evaluation Criteria")]')))  
        page_main.execute_script("arguments[0].click();",Evaluation_Criteria_click)
        logging.info("Evaluation_Criteria_click")
        time.sleep(7)
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, '#display_center_center').get_attribute("outerHTML")  
    except Exception as e:
        logging.info("Exception in Evaluation_Criteria_click: {}".format(type(e).__name__))
        pass      
    
    try:
        Events_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[contains(text(),"Events")]')))  
        page_main.execute_script("arguments[0].click();",Events_click)
        logging.info("Events_click")
        time.sleep(7)
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, '#display_center_center').get_attribute("outerHTML")  
    except Exception as e:
        logging.info("Exception in Events_click: {}".format(type(e).__name__))
        pass      
    
    if itrator==6:
        for no_of_click in range(1,4):
            try:
                tab_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,"//i[contains(@class,'adv-svg-Single-Arrow-Right-icon css-b5bwe0')]")))  
                page_main.execute_script("arguments[0].click();",tab_click)
                logging.info("tab_click")
                time.sleep(10)
            except Exception as e:
                logging.info("Exception in tab_list_click: {}".format(type(e).__name__))
                pass      

        try:
            Amendment_History_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[contains(text(),"Amendment History")]')))  
            page_main.execute_script("arguments[0].click();",Amendment_History_click)
            logging.info("Amendment_History_click")
            time.sleep(3)
            notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, '#display_center_center').get_attribute("outerHTML")
        except Exception as e:
            logging.info("Exception in Amendment_History_click: {}".format(type(e).__name__))
            pass  
    
        try:
            Public_Bid_Reading_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[contains(text(),"Public Bid Reading")]')))  
            page_main.execute_script("arguments[0].click();",Public_Bid_Reading_click)
            logging.info("Public_Bid_Reading_click")
            time.sleep(3)
            notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, '#display_center_center').get_attribute("outerHTML")
        except Exception as e:
            logging.info("Exception in Public_Bid_Reading: {}".format(type(e).__name__))
            pass  

        try:
            Notice_of_Award_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[contains(text(),"Notice of Award")]')))  
            page_main.execute_script("arguments[0].click();",Notice_of_Award_click)
            logging.info("Notice_of_Award_click")
            time.sleep(3)
            notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, '#display_center_center').get_attribute("outerHTML")
        except Exception as e:
            logging.info("Exception in Notice_of_Award_click: {}".format(type(e).__name__))
            pass  
        
        try:
            lot_number = 1
            for single_record in page_main.find_elements(By.CSS_SELECTOR, 'div.css-nil.css-1y6j1ro > div:nth-child(2) > table > tbody > tr'):  

                lot_details_data = lot_details()
                lot_details_data.lot_number = lot_number
                lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR,"td:nth-child(3)").text  
                try:
                    grossawardvalue = single_record.find_element(By.CSS_SELECTOR,"td:nth-child(6)").text
                    lot_details_data.grossawardvalue = float(grossawardvalue.split('$')[1].strip())
                except Exception as e:
                    logging.info("Exception in grossawardvalue: {}".format(type(e).__name__))
                    pass  

                try:
                    award_details_data = award_details()
                    award_details_data.bidder_name = single_record.find_element(By.CSS_SELECTOR,"td:nth-child(2)").text
                    
                    try:
                        dropdown_open_click = single_record.find_element(By.CSS_SELECTOR," td:nth-child(1) > button").click()
                    except Exception as e:
                        logging.info("Exception in dropdown_open_click: {}".format(type(e).__name__))
                        pass  
                    
                    try:
                        award_date = page_main.find_element(By.XPATH, '//*[contains(text(),"Award Date")]//following::div[1]').text 
                        award_details_data.award_date = datetime.strptime(award_date,'%m/%d/%Y').strftime('%Y/%m/%d')
                    except Exception as e:
                        logging.info("Exception in award_date: {}".format(type(e).__name__))
                        pass  
                    
                    try:
                        dropdown_close_click = single_record.find_element(By.CSS_SELECTOR," td:nth-child(1) > button").click()
                    except Exception as e:
                        logging.info("Exception in dropdown_close_click: {}".format(type(e).__name__))
                        pass  
                    
                    award_details_data.award_details_cleanup()
                    lot_details_data.award_details.append(award_details_data)
                except Exception as e:
                    logging.info("Exception in award_details_data: {}".format(type(e).__name__))
                    pass  

                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
                lot_number +=1
        except Exception as e:
            logging.info("Exception in lot_details_data: {}".format(type(e).__name__))
            pass       
    else:
        pass
    
    if itrator==5:
        for no_of_click in range(1,4):
            try:
                tab_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,"//i[contains(@class,'adv-svg-Single-Arrow-Right-icon css-b5bwe0')]")))  
                page_main.execute_script("arguments[0].click();",tab_click)
                logging.info("tab_click")
                time.sleep(10)
            except Exception as e:
                logging.info("Exception in tab_list_click: {}".format(type(e).__name__))
                pass      

        try:
            Amendment_History_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[contains(text(),"Amendment History")]')))  
            page_main.execute_script("arguments[0].click();",Amendment_History_click)
            logging.info("Amendment_History_click")
            time.sleep(3)
            notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, '#display_center_center').get_attribute("outerHTML")
        except Exception as e:
            logging.info("Exception in Amendment_History_click: {}".format(type(e).__name__))
            pass  
        
    else:
        pass
        
    try:    
        Back_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[contains(text(),"Back")]')))  
        page_main.execute_script("arguments[0].click();",Back_click)
        time.sleep(7)
    except Exception as e:
        logging.info("Exception in Back_click: {}".format(type(e).__name__))
        pass    
    
    try:
        show_me_click = Select(page_main.find_element(By.NAME, 'vss.page.VVSSX10019.gridView1.group1.cardSearch.search1.SHOW_TXT'))
        show_me_click.select_by_index(itrator)
        time.sleep(10)
    except Exception as e:
        logging.info("Exception in show_me_click: {}".format(type(e).__name__))
        pass   

    try:
        Search_click_2 = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'(//*[contains(text(),"Search")])[3]')))  
        page_main.execute_script("arguments[0].click();",Search_click_2)
        logging.info("Search_click_2")
        time.sleep(10)
    except Exception as e:
        logging.info("Exception in Search_click_2: {}".format(type(e).__name__))
        pass 
    
    try:
        View_per_Page_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'(//*[contains(text(),"100")])[4]')))  
        page_main.execute_script("arguments[0].click();",View_per_Page_click)
        logging.info("View_per_Page_click")
        time.sleep(25)    
    except Exception as e:
        logging.info("Exception in View_per_Page_click: {}".format(type(e).__name__))
        pass 
    
    try:
        if try_next_page == 1:
            next_page_2 = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,"(//button[contains(@class,'css-114zfuz')])[1]")))
            page_main.execute_script("arguments[0].click();",next_page_2)
            logging.info("Next page 2")
            time.sleep(5)
    except Exception as e:
        logging.info("Exception in next_page_2: {}".format(type(e).__name__))
        pass        

    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) + str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title) + str(notice_data.notice_url)  
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = Doc_Download.page_details

page_main.maximize_window()

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://vss.ky.gov/vssprod-ext/Advantage4"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        View_Published_Solicitations_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[contains(text(),"View Published Solicitations")]')))  
        page_main.execute_script("arguments[0].click();",View_Published_Solicitations_click)
        logging.info("View_Published_Solicitations_click")
        time.sleep(10)
        
        index_list = [3,4,5,6,2]
        for itrator in index_list:
            show_me_click = Select(page_main.find_element(By.NAME, 'vss.page.VVSSX10019.gridView1.group1.cardSearch.search1.SHOW_TXT'))
            show_me_click.select_by_index(itrator)
            time.sleep(5)
            
            Search_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'(//*[contains(text(),"Search")])[3]')))  
            page_main.execute_script("arguments[0].click();",Search_click)
            logging.info("Search_click")
            time.sleep(7)
        
            for page_no in range(1,3):                                                                    
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/as-main-app/adv-view-mgr/div[2]/main/div[1]/div[2]/div[2]/section[2]/adv-custom-carousel-page/div[4]/carousel-component4/div[2]/adv-system-inquiry-page-2/div/div[2]/div/div/adv-system-inquiry-page-search-view-2/div/div/div/adv-common-view-panel/div/div/div[2]/div[2]/div/div[2]/div[2]/div[2]/table/tbody/tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/as-main-app/adv-view-mgr/div[2]/main/div[1]/div[2]/div[2]/section[2]/adv-custom-carousel-page/div[4]/carousel-component4/div[2]/adv-system-inquiry-page-2/div/div[2]/div/div/adv-system-inquiry-page-search-view-2/div/div/div/adv-common-view-panel/div/div/div[2]/div[2]/div/div[2]/div[2]/div[2]/table/tbody/tr')))
                length = len(rows)
                for records in range(1,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="vsspageVVSSX10019gridView1group1cardGridgrid1"]/tbody/tr')))[records]  
                     
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
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,"(//button[contains(@class,'css-114zfuz')])[1]")))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/as-main-app/adv-view-mgr/div[2]/main/div[1]/div[2]/div[2]/section[2]/adv-custom-carousel-page/div[4]/carousel-component4/div[2]/adv-system-inquiry-page-2/div/div[2]/div/div/adv-system-inquiry-page-search-view-2/div/div/div/adv-common-view-panel/div/div/div[2]/div[2]/div/div[2]/div[2]/div[2]/table/tbody/tr'),page_check))  
                    try_next_page = 1
                    time.sleep(5)
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
    output_json_file.copyFinalJSONToServer(output_json_folder)