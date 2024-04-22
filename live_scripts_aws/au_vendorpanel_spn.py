from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "au_vendorpanel_spn"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "au_vendorpanel_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'au_vendorpanel_spn'
    notice_data.main_language = 'EN'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'AU'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'AUD'
    notice_data.procurement_method = 2

    # Onsite Field -None
    # Onsite Comment -1.if "Expression of Interest" is present in local_title then take notice_type=5.
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR,'div.TenderListTenderNameInner').text
        if "Expression of Interest" in notice_data.local_title:
            notice_data.notice_type = 5
        else:
            notice_data.notice_type = 4
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    time.sleep(3)
    clk_button = tender_html_element.find_element(By.CSS_SELECTOR, ' td.TenderListTenderName > div.TenderListActionBtn > a:nth-child(1)')
    clk_button.click()
    time.sleep(5)

    # Onsite Field -None
    # Onsite Comment -1.split notice_deadline. here "19/Sep/2023 05:00 PM (UTC+10:00) Canberra, Melbourne, Sydney time" take only "19/Sep/2023" in notice_deadline.
    try: 
        notice_deadline = page_main.find_element(By.XPATH, '//div[contains(text(),"Closes")]/../div[@class="opportunityPreviewContent"]').text
        notice_deadline = re.findall('\d+ \w+ \d{4} \d+:\d+ [apAP][mM]', notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline, '%d %B %Y %I:%M %p').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass


    notice_data.notice_url = 'https://www.vendorpanel.com.au/publictenders.aspx'
  
    try:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR,'#mstrlayoutcontainerPopUp > div > div').get_attribute("outerHTML")
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')

    # Onsite Field -Buyers Reference
    # Onsite Comment -None

    try:
        notice_data.notice_no = page_main.find_element(By.XPATH,'//*[contains(text(),"Buyers Reference")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass


    # Onsite Field -Estimated Value
    # Onsite Comment -1.split est_amount. here "$1M to 3M" take only "$3M" in est_amount.

    try:
        grossbudgetlc = page_main.find_element(By.XPATH,'//*[contains(text(),"Estimated Value")]//following::div[1]').text
        if grossbudgetlc!='':
            notice_data.grossbudgetlc = float(grossbudgetlc.split('to')[-1])
            notice_data.est_amount = notice_data.grossbudgetlc
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass

    # Onsite Field -None
    # Onsite Comment -1.split publish_date. here "Tuesday 22 August 2023 (AUS Eastern Standard Time)".

    try:
        publish_date = page_main.find_element(By.XPATH, "//*[contains(text(),'Opens')]//following::div[1]").text
        publish_date = re.findall('\d+ \w+ \d{4}', publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date, '%d %B %Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
    
    
    try:
        category = ''
        for single_record in page_main.find_elements(By.XPATH, '//*[contains(text(),"Categories")]//following::ul[1]/li'):
            category1 = single_record.text
            category2 = category1.split('\n')[0].strip()
            category += category2
            category += ','

            cpv_codes_list = fn.CPV_mapping("assets/au_vendorpanel_cpv_code.csv",category2)
            for each_cpv in cpv_codes_list:
                cpvs_data = cpvs()
                cpv_code1 = each_cpv
                cpv_code = re.findall('\d{8}',cpv_code1)[0]                
                cpvs_data.cpv_code = cpv_code
                cpvs_data.cpvs_cleanup()
                notice_data.cpvs.append(cpvs_data)
        notice_data.category = category.rstrip(',')

    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass

    try:
        notice_data.local_description = page_main.find_element(By.XPATH,'//*[contains(text(),"What the buyer is requesting")]//following::div[3]').text
        notice_data.notice_summary_english = notice_data.local_description
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass

    # Onsite Field -None
    # Onsite Comment -None

    try:
        
        customer_details_data = customer_details()
        customer_details_data.org_country = 'AU'
        customer_details_data.org_language = 'EN'

        customer_details_data.org_name = tender_html_element.find_element(By.XPATH,'(//div[contains(text(),"Business Name")])[1]/following-sibling::div').text
        # Onsite Field -Buyer Details >> Location
        # Onsite Comment -None

        try:
            customer_details_data.org_address = page_main.find_element(By.XPATH,'//*[contains(text(),"Buyer Details")]//following::div[6]').text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass

        # Onsite Field -Business Info
        # Onsite Comment -None

        try:
            customer_details_data.org_description = page_main.find_element(By.XPATH,'//*[contains(text(),"Business Info")]//following::div[1]').text
        except Exception as e:
            logging.info("Exception in org_description: {}".format(type(e).__name__))
            pass

        # Onsite Field -WebSite:
        # Onsite Comment -None

        try:
            customer_details_data.org_website = page_main.find_element(By.XPATH,'//*[contains(text(),"WebSite:")]//following::div[1]').text
        except Exception as e:
            logging.info("Exception in org_website: {}".format(type(e).__name__))
            pass

        # Onsite Field -Contact Name
        # Onsite Comment -None

        try:
            customer_details_data.contact_person = page_main.find_element(By.XPATH,'//*[contains(text(),"Contact Name")]//following::div[1]').text
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass

        # Onsite Field -Mobile phone:
        # Onsite Comment -None

        try:
            customer_details_data.org_phone = page_main.find_element(By.XPATH,'//*[contains(text(),"Mobile phone:")]//following::div[1]|//*[contains(text(),"Primary phone:")]//following::div[1]').text
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass

        # Onsite Field -Fax number:
        # Onsite Comment -1.if in org_fax "None Provided" is given then take "none".

        try:
            customer_details_data.org_fax = page_main.find_element(By.XPATH,'//*[contains(text(),"Fax number:")]//following::div[1]').text
        except Exception as e:
            logging.info("Exception in org_fax: {}".format(type(e).__name__))
            pass

        # Onsite Field -Email:
        # Onsite Comment -None

        try:
            customer_details_data.org_email = page_main.find_element(By.XPATH,'//*[contains(text(),"Email:")]//following::div[1]').text
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__))
        pass

    # Onsite Field -None
    # Onsite Comment -None

    try:
        tender_criteria_data = tender_criteria()
        # Onsite Field -Desired Outcomes >> Details
        # Onsite Comment -None
        tender_criteria_data.tender_criteria_title = page_main.find_element(By.XPATH,'//*[contains(text(),"Desired Outcomes")]//following::div[3]').text

        tender_criteria_data.tender_criteria_cleanup()
        notice_data.tender_criteria.append(tender_criteria_data)
    except Exception as e:
        logging.info("Exception in tender_criteria: {}".format(type(e).__name__))
        pass

   ##################################### bcuz of input team told to commit lot_details###############################

    # try:
    #     # for single_record in page_main.find_elements(By.CSS_SELECTOR, '#mstrlayoutcontainerPopUp > div > div'):
    #     lot_number = 1
    #     lot_details_data = lot_details()
    #     lot_details_data.lot_number = lot_number
    #     # Onsite Field -None
    #     # Onsite Comment -None
    #
    #     try:
    #         lot_details_data.lot_title = page_main.find_element(By.XPATH,
    #                                                             '//*[@id="mstrlayoutcontainerPopUp"]/div/div/table/tbody/tr[1]/td').text
    #         lot_details_data.lot_title_english = lot_details_data.lot_title
    #
    #     except Exception as e:
    #         logging.info("Exception in lot_title: {}".format(type(e).__name__))
    #         pass
    #
    #     # Onsite Field -None
    #     # Onsite Comment -None
    #
    #     try:
    #         lot_details_data.lot_description = page_main.find_element(By.XPATH,
    #                                                                   '//*[contains(text(),"What the buyer is requesting")]//following::div[3]').text
    #         lot_details_data.lot_description_english = lot_details_data.lot_description
    #     except Exception as e:
    #         logging.info("Exception in lot_description: {}".format(type(e).__name__))
    #         pass
    #
    #     # Onsite Field -None
    #     # Onsite Comment -1.split lot_grossbudget_lc. here "$1M to 3M" take only "$3M" in lot_grossbudget_lc.
    #
    #     try:
    #         lot_details_data.lot_grossbudget_lc = page_main.find_element(By.XPATH,'//*[contains(text(),"Estimated Value")]//following::div[1').text
    #         if lot_details_data.lot_grossbudget_lc!='':
    #             lot_details_data.lot_grossbudget_lc=lot_details_data.lot_grossbudget_lc.split('to')[-1]
    #         else:
    #             print("Blank value")
    #     except Exception as e:
    #         logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
    #         pass
    #
    #     lot_details_data.lot_details_cleanup()
    #     notice_data.lot_details.append(lot_details_data)
    #     lot_number += 1
    # except Exception as e:
    #     logging.info("Exception in lot_details: {}".format(type(e).__name__))
    #     pass

    close_button = page_main.find_element(By.XPATH, '(//img[@title="Close"])[last()]')
    page_main.execute_script("arguments[0].click();", close_button)
    time.sleep(5)

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) + str(notice_data.notice_type) + str(notice_data.notice_url)
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
arguments = ['--incognito', 'ignore-certificate-errors', 'allow-insecure-localhost', '--start-maximized']
page_main = fn.init_chrome_driver(arguments)
page_details = fn.init_chrome_driver(arguments)

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.vendorpanel.com.au/publictenders.aspx"]
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            rows = WebDriverWait(page_main, 50).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'td.TenderListTenderName')))
            length = len((rows))
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 50).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'td.TenderListTenderName')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
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
    logging.info("Exception:" + str(e))
finally:
    page_main.quit()
    page_details.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)
