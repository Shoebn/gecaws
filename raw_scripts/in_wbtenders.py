import gec_common.common_eprocure as common_eprocure

script_name = 'in_wbtenders'

domain_url = 'https://wbtenders.gov.in/nicgep'

org_state = 'West Bengal'

common_eprocure.eprocure(script_name,domain_url,org_state)
