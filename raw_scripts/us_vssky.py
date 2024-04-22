3 script are there
us_vssky_spn
us_vssky_ca
us_vssky_amd


***********************************************************us_vssky_spn***********************************************************
after opening the url click on "div.css-1n3kgeu > div:nth-child(5) > div > div= View Published Solicitations".
then select following kewords from "//*[contains(text(),"Show Me")]//following::div[1]" tab:-1)My Commodities	2)Open	3)Closing Soon 4)Recently Published
currently "My Commodities" tab don't have any data.

script_name:'us_vssky_spn'

urls:"https://vss.ky.gov/vssprod-ext/Advantage4"
    cmt:1)after opening the url click on "div.css-1n3kgeu > div:nth-child(5) > div > div= View Published Solicitations".
        2)then select following kewords from "//*[contains(text(),"Show Me")]//following::div[1]" tab:-1)My Commodities	2)Open	3)Closing Soon	4)Recently Published

page_no://*[@id="vsspageVVSSX10019gridView1group1cardGridgrid1"]/tbody/tr			tender_html_element		    3	

performance_country:'US'

currancy:'USD'

main_language:'EN'   

procurement_method:2

notice_type:4


        
        
                -------------------------------------------------------------------------------------------------------------
local_title:Description                                             tender_html_element
notice_no:Solicitation Number / Type / Category                     tender_html_element
        cmt:1)Grab only 1st line.
document_type_description:Solicitation Number / Type / Category     tender_html_element
        cmt:1)Grab only 2nd line.
category:Solicitation Number / Type / Category                      tender_html_element
        cmt:1)Grab only 3rd line.       2).csv file has been pushed name as "us_vssky_category.csv".        3)if code was not present then pass autocpv.
notice_deadline:Closing Date and Time/Status                        tender_html_element
        cmt:1)Grab only 1st line.       2)Grab only date and time.
        
        
        Click on "td.css-1xrqtr9 > button" this in "Description" tab in tender_html_element and grab the below data.
publish_date:Published On                                           tender_html_element
document_opening_time:Bid Opening Date                              tender_html_element


                -------------------------------------------------------------------------------------------------------------

notice_url:Solicitation Number / Type / Category        tender_html_element

notice_text:#display_center_center                      page_main
    cmt:1)In page_main grab data from following tabs in notice_text.i)General Information   ii)Commodity Lines  iii)Attachments iv)Solicitation Instructions    v)Evaluation Criteria   vi)Events
        2)grab data from tender_html_element also.Click on "td.css-1xrqtr9 > button" this in "Description" tab.
        
        
        

local_description:Commodity Lines                                                           page_main
            cmt:grab all the data in "Commodity Lines" tab in local_description
notice_summary_english:Commodity Lines                                                      page_main
            cmt:grab all the data in "Commodity Lines" tab in notice_summary_english
tender_contract_start_date:Commodity Lines >> Requested >> Service From                     page_main
tender_contract_end_date:Commodity Lines >> Requested >> Service To                         page_main



                -------------------------------------------------------------------------------------------------------------
customer_details[]
            org_country:'US'
            org_language:'EN'
            org_name:Department / Buyer             tender_html_element
                    cmt:1)Grab only 1st line.
            contact_person:Department / Buyer       tender_html_element
                        cmt:1)Grab only 2nd line.

            Click on "td.css-1xrqtr9 > button" this in "Description" tab in tender_html_element and grab the below data.
            org_email:Buyer Email                   tender_html_element
            org_phone:Buyer Phone                   tender_html_element
            org_fax:Buyer Fax                       tender_html_element


                -------------------------------------------------------------------------------------------------------------
attachments_details[]       cmt:click on "Attachments" tab from page_main.
            file_name:File Name                         page_main
                    cmt:don't take file extension
            file_description:Description                page_main
            file_type:File Name                         page_main
                    cmt:take only file extension
            external_url:File Name                      page_main
            
                -------------------------------------------------------------------------------------------------------------
          
          
          
          
            
***********************************************************us_vssky_ca***********************************************************
after opening the url click on "div.css-1n3kgeu > div:nth-child(5) > div > div= View Published Solicitations".
then select following kewords from "//*[contains(text(),"Show Me")]//following::div[1]" tab:-1)Recent Awards

script_name:'us_vssky_ca'

urls:"https://vss.ky.gov/vssprod-ext/Advantage4"
    cmt:1)after opening the url click on "div.css-1n3kgeu > div:nth-child(5) > div > div= View Published Solicitations".
        2)then select following kewords from "//*[contains(text(),"Show Me")]//following::div[1]" tab:-1)Recent Awards

page_no://*[@id="vsspageVVSSX10019gridView1group1cardGridgrid1"]/tbody/tr			tender_html_element		    3	

performance_country:'US'

currancy:'USD'

main_language:'EN'   

procurement_method:2

notice_type:7


                -------------------------------------------------------------------------------------------------------------
local_title:Description                                             tender_html_element
notice_no:Solicitation Number / Type / Category                     tender_html_element
        cmt:1)Grab only 1st line.
document_type_description:Solicitation Number / Type / Category     tender_html_element
        cmt:1)Grab only 2nd line.
category:Solicitation Number / Type / Category                      tender_html_element
        cmt:1)Grab only 3rd line.       2).csv file has been pushed name as "us_vssky_category.csv".         3)if code was not present then pass autocpv.
        
        
        
        Click on "td.css-1xrqtr9 > button" this in "Description" tab in tender_html_element and grab the below data.
publish_date:Published On                                           tender_html_element
document_opening_time:Bid Opening Date                              tender_html_element



                -------------------------------------------------------------------------------------------------------------

notice_url:Solicitation Number / Type / Category        tender_html_element

notice_text:#display_center_center                      page_main
    cmt:1)In page_main grab data from following tabs in notice_text.i)General Information   ii)Commodity Lines  iii)Attachments iv)Solicitation Instructions    v)Evaluation Criteria   vi)Events
        2)grab data from tender_html_element also.Click on "td.css-1xrqtr9 > button" this in "Description" tab.
        
        

local_description:Commodity Lines                                                           page_main
            cmt:grab all the data in "Commodity Lines" tab in local_description
notice_summary_english:Commodity Lines                                                      page_main
            cmt:grab all the data in "Commodity Lines" tab in notice_summary_english




                -------------------------------------------------------------------------------------------------------------
customer_details[]
            org_country:'US'
            org_language:'EN'
            org_name:Department / Buyer             tender_html_element
                    cmt:1)Grab only 1st line.
            contact_person:Department / Buyer       tender_html_element
                        cmt:1)Grab only 2nd line.

            Click on "td.css-1xrqtr9 > button" this in "Description" tab in tender_html_element and grab the below data.
            org_email:Buyer Email                   tender_html_element
            org_phone:Buyer Phone                   tender_html_element
            org_fax:Buyer Fax                       tender_html_element


                -------------------------------------------------------------------------------------------------------------
attachments_details[]       cmt:click on "Attachments" tab from page_main.
            file_name:File Name                         page_main
                    cmt:don't take file extension
            file_description:Description                page_main
            file_type:File Name                         page_main
                    cmt:take only file extension
            external_url:File Name                      page_main
            
                -------------------------------------------------------------------------------------------------------------
                
                
                
***********************************************************us_vssky_amd***********************************************************
after opening the url click on "div.css-1n3kgeu > div:nth-child(5) > div > div= View Published Solicitations".
then select following kewords from "//*[contains(text(),"Show Me")]//following::div[1]" tab:-1)Recent Amendments


script_name:'us_vssky_amd'

urls:"https://vss.ky.gov/vssprod-ext/Advantage4"
    cmt:1)after opening the url click on "div.css-1n3kgeu > div:nth-child(5) > div > div= View Published Solicitations".
        2)then select following kewords from "//*[contains(text(),"Show Me")]//following::div[1]" tab:-1)Recent Amendments

page_no://*[@id="vsspageVVSSX10019gridView1group1cardGridgrid1"]/tbody/tr			tender_html_element		    3	

performance_country:'US'

currancy:'USD'

main_language:'EN'   

procurement_method:2

notice_type:16


                -------------------------------------------------------------------------------------------------------------
local_title:Description                                             tender_html_element
notice_no:Solicitation Number / Type / Category                     tender_html_element
        cmt:1)Grab only 1st line.
document_type_description:Solicitation Number / Type / Category     tender_html_element
        cmt:1)Grab only 2nd line.
category:Solicitation Number / Type / Category                      tender_html_element
        cmt:1)Grab only 3rd line.       2).csv file has been pushed name as "us_vssky_category.csv".         3)if code was not present then pass autocpv.
notice_deadline:Closing Date and Time/Status                        tender_html_element
        cmt:1)Grab only 1st line.       2)Grab only date and time.
        
        
        Click on "td.css-1xrqtr9 > button" this in "Description" tab in tender_html_element and grab the below data.
publish_date:Published On                                           tender_html_element
document_opening_time:Bid Opening Date                              tender_html_element


                -------------------------------------------------------------------------------------------------------------

notice_url:Solicitation Number / Type / Category        tender_html_element

notice_text:#display_center_center                      page_main
    cmt:1)In page_main grab data from following tabs in notice_text.i)General Information   ii)Commodity Lines  iii)Attachments iv)Solicitation Instructions    v)Evaluation Criteria   vi)Events
        2)grab data from tender_html_element also.Click on "td.css-1xrqtr9 > button" this in "Description" tab.
        
        
        

local_description:Commodity Lines                                                           page_main
            cmt:grab all the data in "Commodity Lines" tab in local_description
notice_summary_english:Commodity Lines                                                      page_main
            cmt:grab all the data in "Commodity Lines" tab in notice_summary_english
tender_contract_start_date:Commodity Lines >> Requested >> Service From                     page_main
tender_contract_end_date:Commodity Lines >> Requested >> Service To                         page_main



                -------------------------------------------------------------------------------------------------------------
customer_details[]
            org_country:'US'
            org_language:'EN'
            org_name:Department / Buyer             tender_html_element
                    cmt:1)Grab only 1st line.
            contact_person:Department / Buyer       tender_html_element
                        cmt:1)Grab only 2nd line.

            Click on "td.css-1xrqtr9 > button" this in "Description" tab in tender_html_element and grab the below data.
            org_email:Buyer Email                   tender_html_element
            org_phone:Buyer Phone                   tender_html_element
            org_fax:Buyer Fax                       tender_html_element


                -------------------------------------------------------------------------------------------------------------
attachments_details[]       cmt:click on "Attachments" tab from page_main.
            file_name:File Name                         page_main
                    cmt:don't take file extension
            file_description:Description                page_main
            file_type:File Name                         page_main
                    cmt:take only file extension
            external_url:File Name                      page_main
            
                -------------------------------------------------------------------------------------------------------------

        

