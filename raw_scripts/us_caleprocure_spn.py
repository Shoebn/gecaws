# script_name:us_caleprocure_spn

# urls : "https://caleprocure.ca.gov/"

# page_no:       tender_html_element 	/html/body/div[8]/div/div[2]/div[2]/form/section[2]/div[3]/div/table/tbody/tr     5

# performance_country : 'US'

# currancy : 'USD'	

# main_language : 'EN'      

# procurement_method : 2

# notice_type : 4

# notice_no : tender_html_element > 	Event ID	            Note:If notice_no is not available then grab from notice_url

# local_title : tendr_html_element > 	Event Name

# notice_deadline : tender_html_element > End Date     Note:Grab time also

# notice_url : tender_html_element > Event Name

# notice_text : page_detail     Note:Take "tender_html_element" data also

# document_type_description : page_detail > Format/Type:

# publish_date : page_detail > Published Date       Note:Grab time also

# local_description : page_detail > Description

# notice_summary_english : page_detail > Description

# pre_bid_meeting_date : page_detail > Pre Bid Conference >> Date:          Note:Take "Time:" also

# class_at_source="CPV"

# cpv_at_source : page_detail > UNSPSC Codes >> UNSPSC Codes

# customer_detail[] : tender_html_element
#       org_name : tender_html_element  >  Department Name
#       org_country : "US"
#       org_language : "EN"
#       org_city : page_detail > Service Area >> County
#       contact_person : page_detail > Contact Information    Note:Splite between "Contact Information" and "Phone"
#       org_phone : page_detail > Contact Information >> Phone
#       org_email : page_detail > Contact Information >> Email

# cpvs[] : page_detail > UNSPSC Codes                   Ref_url='https://caleprocure.ca.gov/event/2660/07A5816'
#       cpv_code : page_detail > UNSPSC Classification

# category : page_detail > UNSPSC Codes>>UNSPSC Classification Description      File_name:us_caleprocure_spn_unspscpv.csv         Ref_url="https://caleprocure.ca.gov/event/2660/01-0H1704"
