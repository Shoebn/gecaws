from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "sg_gebiz_ca"
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
import gec_common.Doc_Download as Doc_Download
from selenium.webdriver.support.ui import Select

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "sg_gebiz_ca"
Doc_Download = Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    notice_data.script_name = 'sg_gebiz_ca'
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'SG'
    notice_data.performance_country.append(performance_country_data)
    notice_data.main_language = 'EN'
    notice_data.currency = 'SGD'
    notice_data.procurement_method = 2
    notice_data.notice_type = 7
    
    
    try:
        local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div > div.col-md-7.formColumn_MAIN.formColumns_COLUMN-TD > div > div:nth-child(1)').text 
    except:
        local_title = None
        pass
    
    if local_title is None:
        return
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div > div.col-md-7.formColumn_MAIN.formColumns_COLUMN-TD > div > div:nth-child(1)').text 
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div > div.col-md-7.formColumn_MAIN.formColumns_COLUMN-TD > div > div:nth-child(3) > div > div > div > div:nth-child(2)").text  
        publish_date = re.findall('\d+ \w+ \d{4} \d+:\d+ [apAP][mM]',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d %b %Y %I:%M %p').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except:
        try:
            publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div > div.col-md-7.formColumn_MAIN.formColumns_COLUMN-TD > div > div:nth-child(4) > div > div > div > div:nth-child(2)").text  
            publish_date = re.findall('\d+ \w+ \d{4} \d+:\d+ [apAP][mM]',publish_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date,'%d %b %Y %I:%M %p').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.publish_date)
        except Exception as e:
            logging.info("Exception in publish_date: {}".format(type(e).__name__))
            pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    try:
        notice_contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-md-7.formColumn_MAIN.formColumns_COLUMN-TD > div > div:nth-child(4) > div > div > div > div:nth-child(2)').text  
        if publish_date not in notice_contract_type:
            notice_contract_type = notice_contract_type.split('⇒')[1].lower().strip()
            notice_data.notice_contract_type = fn.procedure_mapping("assets/sg_gebiz_ca_contracttype.csv",notice_contract_type)  
        else:
            notice_contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-md-7.formColumn_MAIN.formColumns_COLUMN-TD > div > div:nth-child(5) > div > div > div > div:nth-child(2)').text  
            notice_contract_type = notice_contract_type.split('⇒')[1].lower().strip()
            notice_data.notice_contract_type = fn.procedure_mapping("assets/sg_gebiz_ca_contracttype.csv",notice_contract_type)  
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass

    try:
        notice_data.contract_type_actual = notice_contract_type
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass

    try:
        category = notice_contract_type
        notice_data.category = notice_contract_type
        cpv_codes = fn.CPV_mapping("assets/sg_gebiz_ca_procedure.csv",notice_data.category)
        cpv_at_source = ''
        for cpv_code in cpv_codes:
            cpvs_data = cpvs()
            cpvs_data.cpv_code = cpv_code
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in category: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-md-7.formColumn_MAIN.formColumns_COLUMN-TD > div > div:nth-child(1) > div > div > div > div > div > span > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url

    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#contentForm').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')

    try:
        notice_data.notice_no = page_details.find_element(By.CSS_SELECTOR, '#contentForm\:j_idt251 > div > div > div > div.col-md-9 > div').text.strip()    
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    try:
        related_tender_id = page_details.find_element(By.CSS_SELECTOR, '#contentForm\:j_idt252 > div > div > div > div.col-md-9 > div').text.strip() 
        if len(related_tender_id)>5:
            notice_data.related_tender_id = related_tender_id
    except Exception as e:
        logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
        pass

    try:
        notice_data.document_type_description = page_details.find_element(By.CSS_SELECTOR, '#j_idt242').text.strip() 
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass

    try:              
        for single_record in page_details.find_elements(By.XPATH, '//*[contains(text(),"AWARDING AGENCY")]//following::div[1]/div/div/div/div/div/div/div/div/div/div'):  
            customer_details_data = customer_details()
            customer_details_data.org_country = 'SG'
            customer_details_data.org_language = 'EN'

            try:                                                                                   
                customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Awarding Agency")]//following::div[1]').text   
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass

            try:
                contact_person = page_details.find_element(By.XPATH, """//*[contains(text(),"WHO TO CONTACT")]//following::div[15]""").text 
                if 'PRIMARY' not in contact_person: 
                    customer_details_data.contact_person = contact_person
                else:
                    contact_person = page_details.find_element(By.XPATH, """//*[contains(text(),"WHO TO CONTACT")]//following::div[25]""").text                 
                    customer_details_data.contact_person = contact_person
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass

            try:
                customer_details_data.org_email = page_details.find_element(By.CSS_SELECTOR, '#contentForm\:j_idt483\:j_id30\:j_idt488 > div > div > div > div > div > span > div > div').text   
            except:
                try:
                    customer_details_data.org_email = page_details.find_element(By.CSS_SELECTOR, '#contentForm\:j_idt483\:j_id153\:j_idt488 > div > div > div > div > div > span > div > div').text   
                except Exception as e:
                    logging.info("Exception in org_email: {}".format(type(e).__name__))
                    pass

            try:
                customer_details_data.org_phone = page_details.find_element(By.CSS_SELECTOR, '#contentForm\:j_idt483\:j_id30\:j_idt490 > div > div > div > div > div > span > div > div').text   
            except:
                try:
                    customer_details_data.org_phone = page_details.find_element(By.CSS_SELECTOR, '#contentForm\:j_idt483\:j_id153\:j_idt490 > div > div > div > div > div > span > div > div').text   
                except Exception as e:
                    logging.info("Exception in org_phone: {}".format(type(e).__name__))
                    pass

            try:
                customer_details_data.org_address = page_details.find_element(By.CSS_SELECTOR, '#contentForm\:j_idt483\:j_id30\:j_idt494 > div > div > div > div > div > span > div > div').text  
            except:
                try:
                    customer_details_data.org_address = page_details.find_element(By.CSS_SELECTOR, '#contentForm\:j_idt483\:j_id153\:j_idt494 > div > div > div > div > div > span > div > div').text  
                except Exception as e:
                    logging.info("Exception in org_address: {}".format(type(e).__name__))
                    pass
        
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:
        Award_tab_click = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.XPATH,"//input[contains(@value,'Award (1)')]")))  
        page_details.execute_script("arguments[0].click();",Award_tab_click)    
        time.sleep(3)
    except:
        try:
            Award_tab_click = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.XPATH,"//input[contains(@value,'Award (2)')]")))  
            page_details.execute_script("arguments[0].click();",Award_tab_click)    
            time.sleep(3)     
        except Exception as e:
            logging.info("Exception in Award_tab_click: {}".format(type(e).__name__)) 
            pass
            
    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, "div.formColumns_COLUMN-TABLE"):

            lots = single_record.text
            
            if 'Item No.' in lots:
                lot_details_data = lot_details()

                try:
                    lot_details_data.lot_actual_number = lots.split('\n')[0]
                except Exception as e:
                    logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                    pass
                
                lot_details_data.lot_number = int(lot_details_data.lot_actual_number.split('Item No. ')[1].strip())
                lot_details_data.lot_title = lots.split('\n')[1]
                
                try:
                    lot_details_data.lot_quantity_uom = lots.split('Unit of Measurement')[1].split('Quantity')[0].strip() 
                except Exception as e:
                    logging.info("Exception in lot_quantity_uom: {}".format(type(e).__name__))
                    pass

                try:
                    lot_details_data.lot_quantity = float(lots.split('Quantity')[1].split('Unit Price')[0].strip())
                except Exception as e:
                    logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                    pass

                try:
                    lot_details_data.contract_type = notice_data.notice_contract_type
                except Exception as e:
                    logging.info("Exception in contract_type: {}".format(type(e).__name__))
                    pass

                try:
                    lot_details_data.lot_contract_type_actual = notice_data.contract_type_actual
                except Exception as e:
                    logging.info("Exception in lot_contract_type_actual: {}".format(type(e).__name__))
                    pass

                try:
                    award_details_data = award_details()

                    award_details_data.bidder_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Awarded to")]//following::div[1]').text

                    netawardvaluelc = lots.split('Awarded Value')[1].split('\n')[1].strip()  
                    netawardvaluelc = netawardvaluelc.split('(')[0].strip()
                    award_details_data.netawardvaluelc = float(netawardvaluelc.replace(',',''))

                    award_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Awarded Date")]//following::div[1]').text  
                    award_details_data.award_date = datetime.strptime(award_date,'%d %b %Y').strftime('%Y/%m/%d')
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
        est_amount = page_details.find_element(By.XPATH, '//*[contains(text(),"Total Awarded Value")]//following::div[1]').text   
        est_amount = est_amount.split('(')[0].strip()
        notice_data.est_amount = float(est_amount.replace(',',''))
        notice_data.netbudgetlc = notice_data.est_amount

    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    attachment_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"div.col-md-7.formColumn_MAIN.formColumns_COLUMN-TD > div > div:nth-child(1) > div > div > div > div > div > span > a"))) 
    page_main.execute_script("arguments[0].click();",attachment_click)
    time.sleep(3)    

    try:              
        attachments_data = attachments()
        attachments_data.file_name = 'Tender_documents'

        external_url = WebDriverWait(page_main, 10).until(EC.element_to_be_clickable((By.XPATH,"//input[contains(@value,'Download All')]"))) 
        page_main.execute_script("arguments[0].click();",external_url)
        time.sleep(25)
        file_dwn = Doc_Download.file_download()
        attachments_data.external_url = str(file_dwn[0]) 
        
        try:
            attachments_data.file_type = page_main.find_element(By.CSS_SELECTOR, '#contentForm\:j_idt402\:j_idt427 > div > div > div > div > div > input').text
        except Exception as e:
            logging.info("Exception in file_type: {}".format(type(e).__name__))
            pass

        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    Back_to_Search_Results_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,"//input[contains(@value,'Back to Search Results')]")))  
    page_main.execute_script("arguments[0].click();",Back_to_Search_Results_click)    
    WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/div/form[2]/div[7]/div/div/div[1]/div/div/div/div/div[2]/div/div[6]/div/div/div/div')))

    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.notice_deadline) + str(notice_data.local_title)
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = Doc_Download.page_details
page_details = fn.init_chrome_driver(arguments) 

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.gebiz.gov.sg/ptn/opportunity/BOListing.xhtml"] 
    
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        
        login_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'div.listButton2_MAIN > div')))
        page_main.execute_script("arguments[0].click();",login_click)    
        time.sleep(2)

        Foreigners_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="j_idt180_listButton2_SELECTION-MENU-DIV"]/div[3]/input')))
        page_main.execute_script("arguments[0].click();",Foreigners_click)        
        time.sleep(2)        
        
        GeBIZ_ID = page_main.find_element(By.XPATH,"(//input[contains(@class,'inputText_MAIN formInputText_MAIN')])[1]").send_keys('H0239040')        
        Password = page_main.find_element(By.XPATH,"(//input[contains(@class,'inputText_MAIN formInputText_MAIN')])[2]").send_keys('AkGEC@123456')        
        
        Submit_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,"//input[contains(@class,'commandButton_BIG commandButton_BIG-BLUE')]")))
        page_main.execute_script("arguments[0].click();",Submit_click)        
        time.sleep(2)

        Opportunities_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,"(//div[contains(@class,'headerMenu2_MENU-BUTTON-DIV')])[2]/span/a")))  
        page_main.execute_script("arguments[0].click();",Opportunities_click)        
        time.sleep(2)
      
        Closed_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,"(//input[contains(@class,'formTabBar_TAB-BUTTON')])[2]")))  
        page_main.execute_script("arguments[0].click();",Closed_click)        
        time.sleep(2)
        
        Awarded_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,"//span[contains(@id,'contentForm:j_idt1899_commandLink-SPAN')]/a")))  
        page_main.execute_script("arguments[0].click();",Awarded_click)        
        time.sleep(3)

        Sort_by_click  = Select(page_main.find_element(By.ID, 'contentForm:j_idt1804_select'))
        Sort_by_click.select_by_index(1)
        time.sleep(3)

	try:
	    for page_no in range(2,12):
		page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/div/form[2]/div[7]/div/div/div[1]/div/div/div/div/div[2]/div/div[6]/div/div/div/div'))).text
		rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div/form[2]/div[7]/div/div/div[1]/div/div/div/div/div[2]/div/div[6]/div/div/div/div')))
		length = len(rows)
		for records in range(0,length):
		    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div/form[2]/div[7]/div/div/div[1]/div/div/div/div/div[2]/div/div[6]/div/div/div/div')))[records]
		    extract_and_save_notice(tender_html_element)
		    if notice_count >= MAX_NOTICES:
			break
		    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
			break
				
		if notice_data.publish_date is not None and notice_data.publish_date < threshold:
		    break
	
		try:   
		    next_page = WebDriverWait(page_main, 10).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
		    page_main.execute_script("arguments[0].click();",next_page)
		    logging.info("Next page")
		    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/div/form[2]/div[7]/div/div/div[1]/div/div/div/div/div[2]/div/div[6]/div/div/div/div'),page_check))
		except Exception as e:
		    logging.info("Exception in next_page: {}".format(type(e).__name__))
		    logging.info("No next page")
		    break

	except:
	    logging.info("No new record")
	    break
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit() 
    output_json_file.copyFinalJSONToServer(output_json_folder)
