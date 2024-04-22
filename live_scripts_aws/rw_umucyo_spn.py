from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "rw_umucyo_spn"
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
from selenium.webdriver.support.ui import Select

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "rw_umucyo_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"

# -------------------------------------------------------------------------------------------------------------------------------------------------------------
# Note : there are 4 formats for lot (format 1 = Goods , format 2 = Non Consultant Services , format 3 = Consultant Services  ,  , format 4 = Works )


# go to URL : "https://www.umucyo.gov.rw/pt/index.do"  ,   click on "+" sign (selector : "#tabsholder > p > a")  ,    tender notices >> "+""


# -------------------------------------------------------------------------------------------------------------------------------------------------------------


def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.script_name = 'rw_umucyo_spn'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'EN'
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'RW'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -None
    # Onsite Comment -if the "Status" field  has an "Amended" or "Cancelled" word then take notice_type = 16
    notice_data.notice_type = 4
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'RWF'
    

    
    # Onsite Field -Tender Name
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        notice_data.notice_title = notice_data.local_title 
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    # Onsite Field -Tender No
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Status
    # Onsite Comment -None

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
#     # Onsite Field -Advertising Date
#     # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(5)").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Deadline of Submitting
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(6)").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    

    try:
        notice_url =tender_html_element.find_element(By.CSS_SELECTOR,'#tendMstVO > table > tbody > tr> td:nth-child(2) > span > a:nth-child(2)').click()
        notice_data.notice_url=page_main.current_url
        time.sleep(5)
    except:
        notice_url =tender_html_element.find_element(By.CSS_SELECTOR,'#tendMstVO > table > tbody > tr> td:nth-child(2) > span > a:nth-child(1)').click()
        notice_data.notice_url=page_main.current_url
        time.sleep(5)


    # Onsite Field -Tender Method
    # Onsite Comment -(International Competitive Bidding = 1) (National Competitive Bidding = 0)

    try:
        procurement_method = page_main.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
        if 'International Competitive Bidding' in procurement_method:
            notice_data.procurement_method = 1
        else:
            notice_data.procurement_method = 0
    except Exception as e:
        logging.info("Exception in procurement_method: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, 'div#contents_R').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
#     # Onsite Field -Tender Type
#     # Onsite Comment -Replace following keywords with given respective keywords ('Works = Works' , 'Non Consultant Services = Non consultancy' , 'Consultant Services   = Consultancy' , 'Goods = Supply' )

    try:
        notice_data.contract_type_actual = page_main.find_element(By.CSS_SELECTOR, 'div.tableTy1   tr:nth-child(1) > td:nth-child(2)').text
        if 'Goods' in notice_data.contract_type_actual :
            notice_data.notice_contract_type='Supply'
        elif 'Works' in  notice_data.contract_type_actual :
            notice_data.notice_contract_type='Works'
        elif 'Non Consultant Services' in notice_data.contract_type_actual :
            notice_data.notice_contract_type='Non consultancy'
        elif 'Consultant Services' in notice_data.contract_type_actual :
            notice_data.notice_contract_type='Consultancy'
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass

    
    try:
        notice_data.local_description = page_main.find_element(By.CSS_SELECTOR, '.tableTy1   tr:nth-child(4) > td').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
#     # Onsite Field -*Brief Description
#     # Onsite Comment -None

    try:
        notice_data.notice_summary_english = notice_data.local_description
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
#     # Onsite Field -*Tender Fee
#     # Onsite Comment -split the data after "*Tender Fee"   , ref_url : "https://www.umucyo.gov.rw/pt/index.do"

    try:
        notice_data.document_fee = page_main.find_element(By.CSS_SELECTOR, 'tr:nth-child(9) > td').text
    except Exception as e:
        logging.info("Exception in document_fee: {}".format(type(e).__name__))
        pass
    try:
        contract_duration = page_main.find_element(By.CSS_SELECTOR, '#tendMstVO > table:nth-child(32) td:nth-child(4)').text
    except:
        pass
# Onsite Field -General Information
# Onsite Comment -None

    try:              
        customer_details_data = customer_details()
    # Onsite Field -Advertising/Procuring Entity
    # Onsite Comment -split the data after "Advertising/Procuring Entity" field

        customer_details_data.org_name = page_main.find_element(By.XPATH, '//*[contains(text(),"Advertising/Procuring Entity")]//following::td[1]').text

        customer_details_data.org_country = 'RW'
        customer_details_data.org_language = 'EN'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    
    if 'Goods' in notice_data.contract_type_actual:
        clk=page_main.find_element(By.XPATH,'//*[@id="classifi1"]/a').click()
        page_main.switch_to.window(page_main.window_handles[1])
        time.sleep(5)

        page_main.maximize_window()
        
        for single in page_main.find_elements(By.CSS_SELECTOR,'#lotMstVO > table > tbody > tr'):
            lot_details_data = lot_details()
            try:
                lot_details_data.lot_actual_number = single.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text.split('(')[0]
                print(lot_details_data.lot_actual_number)
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass

#             # Onsite Field -Classification ID
#             # Onsite Comment -lot_title for Goods, first click on  "#classifi1 > a" for lot_title and grab the data from "Classification ID" field , for ex."43231512(License management software)" , here take only bracket value i.e (License management software)

            lot_details_data.lot_title = single.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text.split('(')[1]


#             # Onsite Field -*Time Limit of Delivery
#             # Onsite Comment -contract_duration for "Goods"

            try:
                lot_details_data.contract_duration = contract_duration
            except Exception as e:
                logging.info("Exception in contract_duration: {}".format(type(e).__name__))
                pass

#             # Onsite Field - Classification Name	
#             # Onsite Comment - first click on  "#classifi1 > a" for lot_description and grab the data from "Classification Name" field

            try:
                lot_details_data.lot_description = single.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass


#             # Onsite Field -Quantity
#             # Onsite Comment -first click on  "#classifi1 > a" for lot_quantity and grab the data from "Quantity" field

            try:
                lot_details_data.lot_quantity = single.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
            except Exception as e:
                logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                pass

#             # Onsite Field -Unit
#             # Onsite Comment -first click on  "#classifi1 > a" for lot_quantity_uom and grab the data from "UOM" field

            try:
                lot_details_data.lot_quantity_uom = single.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
            except Exception as e:
                logging.info("Exception in lot_quantity_uom: {}".format(type(e).__name__))
                pass

            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
        
        
        page_main.close()
        page_main.switch_to.window(page_main.window_handles[0])
        page_main.switch_to.frame('main')
        
    if 'non_consultancy_Services' in notice_data.contract_type_actual:
        clk=page_main.find_element(By.XPATH,'//*[@id="classifi1"]/a').click()
        page_main.switch_to.window(page_main.window_handles[1])
        time.sleep(5)
        page_main.maximize_window()
 
        
        for single in page_main.find_elements(By.CSS_SELECTOR,'#lotMstVO > table > tbody > tr'):
            lot_details_data = lot_details()
            try:
                lot_details_data.lot_actual_number = single.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text.split('(')[0]
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass

#             # Onsite Field -Classification ID
#             # Onsite Comment -lot_title for Goods, first click on  "#classifi1 > a" for lot_title and grab the data from "Classification ID" field , for ex."43231512(License management software)" , here take only bracket value i.e (License management software)

            lot_details_data.lot_title = single.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text.split('(')[1]

#             # Onsite Field -*Time Limit of Delivery
#             # Onsite Comment -contract_duration for "Goods"

            try:
                lot_details_data.contract_duration = contract_duration
            except Exception as e:
                logging.info("Exception in contract_duration: {}".format(type(e).__name__))
                pass

#             # Onsite Field - Classification Name	
#             # Onsite Comment - first click on  "#classifi1 > a" for lot_description and grab the data from "Classification Name" field

            try:
                lot_details_data.lot_description = single.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass


#             # Onsite Field -Quantity
#             # Onsite Comment -first click on  "#classifi1 > a" for lot_quantity and grab the data from "Quantity" field

            try:
                lot_details_data.lot_quantity = single.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
            except Exception as e:
                logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                pass

#             # Onsite Field -Unit
#             # Onsite Comment -first click on  "#classifi1 > a" for lot_quantity_uom and grab the data from "UOM" field

            try:
                lot_details_data.lot_quantity_uom = single.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
            except Exception as e:
                logging.info("Exception in lot_quantity_uom: {}".format(type(e).__name__))
                pass

            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
        
        
        page_main.close()
        page_main.switch_to.window(page_main.window_handles[0])
        page_main.switch_to.frame('main')
        
    if 'consultant_Service' in notice_data.contract_type_actual:
        clk=page_main.find_element(By.XPATH,'//*[@id="classifi1"]/a').click()
        page_main.switch_to.window(page_main.window_handles[1])
        time.sleep(5)

        page_main.maximize_window()
 
        
        for single in page_main.find_elements(By.CSS_SELECTOR,'#lotMstVO > table > tbody > tr'):
            lot_details_data = lot_details()
            try:
                lot_details_data.lot_actual_number = single.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text.split('(')[0]
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass

#             # Onsite Field -Classification ID
#             # Onsite Comment -lot_title for Goods, first click on  "#classifi1 > a" for lot_title and grab the data from "Classification ID" field , for ex."43231512(License management software)" , here take only bracket value i.e (License management software)

            lot_details_data.lot_title = single.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text.split('(')[1]

#             # Onsite Field -*Time Limit of Delivery
#             # Onsite Comment -contract_duration for "Goods"

            try:
                lot_details_data.contract_duration = contract_duration
            except Exception as e:
                logging.info("Exception in contract_duration: {}".format(type(e).__name__))
                pass

#             # Onsite Field - Classification Name	
#             # Onsite Comment - first click on  "#classifi1 > a" for lot_description and grab the data from "Classification Name" field

            try:
                lot_details_data.lot_description = single.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass


            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
        
        
        page_main.close()
        page_main.switch_to.window(page_main.window_handles[0])
        page_main.switch_to.frame('main')
 
    if 'Works' in notice_data.contract_type_actual:
        clk=page_main.find_element(By.XPATH,'//*[@id="classifi1"]/a').click()
        page_main.switch_to.window(page_main.window_handles[1])
        time.sleep(5)

        page_main.maximize_window()
 
        lot_number=1
        for single in page_main.find_elements(By.CSS_SELECTOR,'#lotMstVO > table > tbody > tr'):
            
            lot_details_data = lot_details()
            lot_details_data.lot_number=1
            try:
                lot_details_data.lot_actual_number = single.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text.split('(')[0]
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass

#             # Onsite Field -Classification ID
#             # Onsite Comment -lot_title for Goods, first click on  "#classifi1 > a" for lot_title and grab the data from "Classification ID" field , for ex."43231512(License management software)" , here take only bracket value i.e (License management software)

            try:
                lot_details_data.lot_title = single.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text.split('(')[1]
            except:
                lot_details_data.lot_title = single.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text


#             # Onsite Field -*Time Limit of Delivery
#             # Onsite Comment -contract_duration for "Goods"

            try:
                lot_details_data.contract_duration = contract_duration
            except Exception as e:
                logging.info("Exception in contract_duration: {}".format(type(e).__name__))
                pass

#             # Onsite Field - Classification Name	
#             # Onsite Comment - first click on  "#classifi1 > a" for lot_description and grab the data from "Classification Name" field

            try:
                lot_details_data.lot_description = single.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass
            
            try:
                lot_details_data.lot_quantity = single.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
            except Exception as e:
                logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                pass

#             # Onsite Field -Unit
#             # Onsite Comment -first click on  "#classifi1 > a" for lot_quantity_uom and grab the data from "UOM" field

            try:
                lot_details_data.lot_quantity_uom = single.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
            except Exception as e:
                logging.info("Exception in lot_quantity_uom: {}".format(type(e).__name__))
                pass


            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
            lot_number +=1
        
        
        page_main.close()
        page_main.switch_to.window(page_main.window_handles[0])
        page_main.switch_to.frame('main')

 
    

# # Onsite Field -None
# # Onsite Comment -this is the attahcment for "goods"
# # 
    try:              

        if 'Goods' in notice_data.contract_type_actual:
            attachments_data = attachments()
        #         # Onsite Field -Tender Document
        #         # Onsite Comment -this is the attahcment for "goods"

            try:
                attachments_data.file_name = page_main.find_element(By.CSS_SELECTOR, '#tendMstVO > table:nth-child(36) td:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass

    #         # Onsite Field -Tender Document
    #         # Onsite Comment -this is the attahcment for "goods"
            
            external_url = page_main.find_element(By.CSS_SELECTOR, '#tendMstVO > table:nth-child(36) td:nth-child(4) a')
            page_main.execute_script("arguments[0].click();",external_url)
            time.sleep(10)

            file_dwn = Doc_Download.file_download()
            attachments_data.external_url = str(file_dwn[0]) 


            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)

#         # Onsite Field -Price Schedule  >> *Document Name
#         # Onsite Comment -this is the attahcment for "goods"
            attachments_data = attachments()
            try:
                attachments_data.file_name = page_main.find_element(By.CSS_SELECTOR, '#rfpTable > tbody > tr td:nth-child(2) a').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass

    #         # Onsite Field -Price Schedule  >> * Download
    #         # Onsite Comment -this is the attahcment for "goods"

            external_url = page_main.find_element(By.CSS_SELECTOR, '#rfpTable > tbody > tr td:nth-child(3) a').click()
            file_dwn = Doc_Download.file_download()
            attachments_data.external_url = str(file_dwn[0])      

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)


        if 'Consultant Services' in notice_data.contract_type_actual:
            attachments_data = attachments()


            attachments_data.file_name = page_main.find_element(By.CSS_SELECTOR, '#frm_detailView > table:nth-child(25) > tbody > tr > td:nth-child(2)').text

            external_url = page_main.find_element(By.CSS_SELECTOR, '#frm_detailView > table:nth-child(25)  td:nth-child(4) a').click()
            file_dwn = Doc_Download.file_download()
            attachments_data.external_url = str(file_dwn[0]) 

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)

        if 'Non Consultant Services' in notice_data.contract_type_actual:
            attachments_data = attachments()

            try:
                attachments_data.file_name = page_main.find_element(By.CSS_SELECTOR, 'table:nth-child(37) td:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass


            external_url = page_main.find_element(By.CSS_SELECTOR, 'table:nth-child(37) td:nth-child(4) a').click()
            file_dwn = Doc_Download.file_download()
            attachments_data.external_url = str(file_dwn[0]) 

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data) 

            attachments_data = attachments()
            try:
                attachments_data.file_name = page_main.find_element(By.CSS_SELECTOR, '#rfpTable td:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass


            external_url = page_main.find_element(By.CSS_SELECTOR, '#rfpTable td:nth-child(3) a').click()
            file_dwn = Doc_Download.file_download()
            attachments_data.external_url = str(file_dwn[0])

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data) 

        if 'Works' in  notice_data.contract_type_actual :

            attachments_data.attachments_cleanup()        

            try:
                attachments_data.file_name = page_main.find_element(By.CSS_SELECTOR, 'table:nth-child(36)  td:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass


            external_url = page_main.find_element(By.CSS_SELECTOR, 'table:nth-child(36)  td:nth-child(4) a').click()
            file_dwn = Doc_Download.file_download()
            attachments_data.external_url = str(file_dwn[0]) 

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)


            attachments_data.attachments_cleanup()        

            try:
                attachments_data.file_name = page_main.find_element(By.CSS_SELECTOR, '#rfpTable  td:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass


            external_url = page_main.find_element(By.CSS_SELECTOR, '#rfpTable  td:nth-child(3) a').click()
            file_dwn = Doc_Download.file_download()
            attachments_data.external_url = str(file_dwn[0]) 

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)  
            
    except:
        pass
 
    bck=page_main.find_element(By.XPATH,'(//a[@class="button sky"])[2]').click()
    time.sleep(10)
        

    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
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
    urls = ["https://www.umucyo.gov.rw/pt/index.do"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        time.sleep(4)
        
        try:
            page_main.switch_to.frame('main')
            main_1 = page_main.find_element(By.XPATH, '//*[@id="tabsholder"]//p//a')
            page_main.execute_script("arguments[0].click();", main_1)
            time.sleep(5)
        except:
            pass

        try:
            pubcatFromDt = th.strftime('%d%m%Y')
            page_main.find_element(By.CSS_SELECTOR,'#pubcatFromDt').send_keys(pubcatFromDt)
            time.sleep(2)
        except:
            pass

        try:
            drop_down = Select(page_main.find_element(By.CSS_SELECTOR,'#recordCountPerPage'))
            drop_down.select_by_index(3)
            time.sleep(4)
        except:
            pass

        try:
            for page_no in range(2,10):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="tendMstVO"]/table/tbody/tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="tendMstVO"]/table/tbody/tr')))
                length = len(rows)
    
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="tendMstVO"]/table/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                try:   
                    next_page = WebDriverWait(page_main, 10).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 10).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="tendMstVO"]/table/tbody/tr'),page_check))
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
    output_json_file.copyFinalJSONToServer(output_json_folder)
