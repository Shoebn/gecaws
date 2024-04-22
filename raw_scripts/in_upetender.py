import gec_common.common_eprocure as common_eprocure

script_name = 'in_upetender'

domain_url = 'https://etender.up.nic.in/nicgep'

org_state = 'Uttar Pradesh'

common_eprocure.eprocure(script_name,domain_url,org_state)
