from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "sg_gebiz_spn"
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

#------------------------------------------------------------------------------************************************----------------------------------------------------------------------
#NOTE: In this tender gets sessions out after few minutes
# Login credentials:
#login : H0239040 
#password : AkGEC@123456

# Follow the steps to find data.
# 1)After opening the main url click on "#listButton2_MAIN-DIV" button.Then click on "For Foreigners w/o Singpass" option in dropdown."
# 2)Then in "GeBIZ ID" and "Password" field Enter the given Id and Password. and Click on Submit button.
# 3)Then select "dgMarket International Inc" option.Then click on Next.
# 4)Then click "div.headerMenu2_MENU-BUTTON-LOGIN > div:nth-child(2)"=Opportunities tab
# 7)Then click on "//*[contains(text(),"Sort by")]//following::div[1]" dropdown button. and select "Published Date (Latest First)" option.
#------------------------------------------------------------------------------************************************----------------------------------------------------------------------


NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "sg_gebiz_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.script_name = 'sg_gebiz_spn'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'EN'
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'SG'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_type = 4
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'SGD'
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div > div.col-md-7.formColumn_MAIN.formColumns_COLUMN-TD > div > div:nth-child(1)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -split data from "Published"  till "Procurement Category"
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div > div.col-md-7.formColumn_MAIN.formColumns_COLUMN-TD").text
        publish_date = re.findall('\d+ \w+ \d{4} \d+:\d+ [AP][M]',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d %b %Y %H:%M %p').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    
#     # Onsite Field -split data from "Closing on"
#     # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "div.formOutputText_HIDDEN-LABEL.outputText_DATE-GREEN").text
        notice_deadline = re.findall('\d{2} [A-Za-z]{3} \d{4}\n\d{2}:\d{2}[AP]M',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d %b %Y\n%I:%M%p').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'a.commandLink_TITLE-BLUE').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
        
    WebDriverWait(page_details, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/div/form[2]/div[6]/div/div/div[2]/div/div/div/div/div/div/div[2]/div/div[3]/div/div[1]/div/div[1]/div/div/div/div[2]'))).text
    
 
    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"Quotation No.")]//following::div[1]').text
        notice_data.document_type_description = 'Quotation'
    except:
        try:
            notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"Tender No.")]//following::div[1]').text
            notice_data.document_type_description = 'Tender'
        except Exception as e:
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass    
  # Onsite Comment -do not take number just take document type description i.e- just take the keyword "tender/ Quotation" in document_type_description
  # Onsite Field -Quotation / Tender

    # Onsite Field -Quotation / Tender
    # Onsite Comment -1.split notice_no.Here "Quotation - RGS000ETQ24000003 / PR2024-0148" grab "PR2024-0148" no in related_tender_id.

    try:
        notice_data.related_tender_id = page_details.find_element(By.XPATH, '//*[contains(text(),"Reference No.")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
        pass
    
    try:
        notice_contract_type = page_details.find_element(By.XPATH, '//*[contains(text(),"Procurement Category")]//following::div[1]/div').text  
        notice_data.contract_type_actual = notice_contract_type.split(' ⇒ ')[1].strip()
        notice_data.contract_type_actual = notice_data.contract_type_actual.lower()
        notice_data.notice_contract_type = fn.procedure_mapping("assets/sg_gebiz_spn_contract_type.csv",notice_data.contract_type_actual)  
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass


    # Onsite Field -None
    # Onsite Comment -1.split category.Here "Administration & Training ⇒ Courses" grab only " Courses"
    try:
        notice_data.category = notice_data.contract_type_actual
        cpv_codes = fn.CPV_mapping("assets/sg_gebiz_spn_procedure.csv",notice_data.category)
        for cpv_code in cpv_codes:
            cpvs_data = cpvs()
            cpvs_data.cpv_code = cpv_code
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in category: {}".format(type(e).__name__))
        pass

#     # Onsite Field -Offer Validity Duration
#     # Onsite Comment -None

    try:
        notice_data.contract_duration = page_details.find_element(By.XPATH, '//*[contains(text(),"Offer Validity Duration")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
        notice_data.notice_text += page_details.find_element(By.XPATH, '/html/body/div/form[2]/div[6]/div/div/div[2]/div/div/div/div/div/div/div[2]').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
        
    try:              
        customer_details_data = customer_details()
    # Onsite Field -Agency
    # Onsite Comment -None
        customer_details_data.org_name =  page_details.find_element(By.XPATH, '''(//*[contains(text(),"Agency")])[2]//following::div[1]''').text
    # Onsite Field -None
    # Onsite Comment -None

        try:
            customer_details_data.contact_person = page_details.find_element(By.XPATH, '''//*[contains(text(),"CONTACT PERSON'S DETAILS")]//following::div[1]''').text
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass

    # Onsite Field -None
    # Onsite Comment -1)split the data after "CONTACT PERSON'S DETAILS".    2)grab only 2nd line in org_email.

        try:
            customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"AWARDING AGENCY")]//following::div[1]').text
            customer_details_data.org_email = fn.get_email(customer_details_data.org_email)
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass

    # Onsite Field -None
    # Onsite Comment -1)split the data after "CONTACT PERSON'S DETAILS".    2)grab only 3rd line in org_phone.

        try:
            customer_details_data.org_phone = page_details.find_element(By.XPATH, '(//*[contains(text(),"CONTACT PERSON")]//following::div//*[@class="formRow_HIDDEN-LABEL"])[2]').text
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass

    # Onsite Field -None
    # Onsite Comment -1)split the data after "CONTACT PERSON'S DETAILS".    2)grab only 5th line in org_address.

        try:
            customer_details_data.org_address = page_details.find_element(By.XPATH, '(//*[contains(text(),"CONTACT PERSON")]//following::div//*[@class="formRow_HIDDEN-LABEL"])[4]').text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass



        customer_details_data.org_country = 'SG'
        customer_details_data.org_language = 'EN'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
   
    try:             
        for single_record in page_details.find_elements(By.XPATH,'/html/body/div/form[2]/div[6]/div/div/div[2]/div/div/div/div/div/div/div[2]/div/div[4]/div/div[2]/div/div[2]/div/div/div/div/div/div/div/div/div[1]/div/div/div/div/div/div/div/div/div')[:-1]:
            attachments_data = attachments()
            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR,'span:nth-child(2) a').text

            external_url = single_record.find_element(By.CSS_SELECTOR,'span:nth-child(2)').click()
            time.sleep(15)
            file_dwn = Doc_Download.file_download()
            attachments_data.external_url = str(file_dwn[0])

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
        lot_number=1
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.col-md-11.formColumn_MAIN.formColumns_COLUMN-TD'):
            lot_details_data = lot_details()
            
            lot_details_data.lot_number = lot_number

        # Onsite Field -Unit of Measurement
        # Onsite Comment -None

            try:
                lot_details_data.lot_quantity_uom =  single_record.find_element(By.XPATH, "//*[contains(text(),'Unit of Measurement')]//following::div[1]").text
            except Exception as e:
                logging.info("Exception in lot_quantity_uom: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -skip first record

            try:
                lot_details_data.lot_title =  single_record.find_element(By.CSS_SELECTOR, 'div.formOutputText_HIDDEN-LABEL.outputText_TITLE-BLACK').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Required Quantity
        # Onsite Comment -None

            try:
                lot_details_data.lot_quantity = float(single_record.find_element(By.XPATH, "//*[contains(text(),'Required Quantity')]//following::div[1]").text)
            except Exception as e:
                logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Item No. 1
        # Onsite Comment -just take "Item No"

            try:
                lot_details_data.lot_actual_number = 'Item No.' + str(lot_details_data.lot_number)
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Procurement Type
        # Onsite Comment -None

            try:
                lot_details_data.contract_type =  notice_data.notice_contract_type 
            except Exception as e:
                logging.info("Exception in contract_type: {}".format(type(e).__name__))
                pass

            try:
                 lot_details_data.notice_contract_type =  notice_data.contract_type_actual 
            except Exception as e:
                logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
                pass

            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
            lot_number +=1
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_details = Doc_Download.page_details
page_details.maximize_window()
page_main = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.gebiz.gov.sg/ptn/opportunity/BOListing.xhtml"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        clk =page_main.find_element(By.CSS_SELECTOR,'#j_idt180_listButton2_SELECTION-BUTTON-DIV').click()
        clk =page_main.find_element(By.CSS_SELECTOR,'#j_idt180_listButton2_SELECTION-MENU-DIV > div:nth-child(3)').click()
        time.sleep(5)
        
        username  = page_main.find_element(By.XPATH,'//*[@id="contentForm:j_idt143"]/div/div/div/div[2]/div/input').send_keys('H0239040')

        password  = page_main.find_element(By.XPATH,'//*[@id="contentForm:password_inputText"]').send_keys('AkGEC@123456')

        submit = page_main.find_element(By.XPATH,'//*[@id="contentForm:buttonSubmit"]').click()
        time.sleep(20)
        
        try:
            clk=page_main.find_element(By.XPATH,'//*[@id="dialogForm:j_idt33"]/table/tbody/tr/td/input[2]').click()
        except:
            pass
        
        try:
            page_main.find_element(By.XPATH,'//table/tbody/tr/td/input[2]').click()
            time.sleep(2)
        except:
            pass
        
        select = page_main.find_element(By.CSS_SELECTOR,'#contentForm\:j_id54_commandLink-SPAN > a').click()
        
        ##########
        fn.load_page(page_details, url, 220)
        clk1 =page_details.find_element(By.CSS_SELECTOR,'#j_idt180_listButton2_SELECTION-BUTTON-DIV').click()
        clk1 =page_details.find_element(By.CSS_SELECTOR,'#j_idt180_listButton2_SELECTION-MENU-DIV > div:nth-child(3)').click()
        time.sleep(5)
        
        username1  = page_details.find_element(By.XPATH,'//*[@id="contentForm:j_idt143"]/div/div/div/div[2]/div/input').send_keys('H0239040')

        password1  = page_details.find_element(By.XPATH,'//*[@id="contentForm:password_inputText"]').send_keys('AkGEC@123456')

        submit1 = page_details.find_element(By.XPATH,'//*[@id="contentForm:buttonSubmit"]').click()
        time.sleep(20)
        
        try:
            clk=page_details.find_element(By.XPATH,'//*[@id="dialogForm:j_idt33"]/table/tbody/tr/td/input[2]').click()
        except:
            pass
        
        try:
            page_details.find_element(By.XPATH,'//table/tbody/tr/td/input[2]').click()
            time.sleep(2)
        except:
            pass

        select1 = page_details.find_element(By.CSS_SELECTOR,'#contentForm\:j_id54_commandLink-SPAN > a').click()
        try:
            for page_no in range(1,10):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/div/form[2]/div[7]/div/div/div[1]/div/div/div/div/div[2]/div/div[4]/div/div/div/div[3]'))).text
                for tender_html_element in WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR,'div.formColumns_MAIN')))[2:]:
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break

                        if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                            break

                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break

                try:           
                    next_page = WebDriverWait(page_main, 100).until(EC.element_to_be_clickable((By.XPATH,"//input[@value='Next']")))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    page_check1 = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/div/form[2]/div[7]/div/div/div[1]/div/div/div/div/div[2]/div/div[4]/div/div/div/div[3]/div/div[1]/div/div[1]/div/div/div/div/div/span/a'))).text
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/div/form[2]/div[7]/div/div/div[1]/div/div/div/div/div[2]/div/div[4]/div/div/div/div[3]/div/div[1]/div/div[1]/div/div/div/div/div/span/a'),page_check1))
                except:
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
