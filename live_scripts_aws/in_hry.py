import gec_common.common_eprocure as common_eprocure

from gec_common import log_config
SCRIPT_NAME = 'in_hry'
log_config.log(SCRIPT_NAME)

domain_url = 'https://etenders.hry.nic.in/nicgep'

org_state = 'Haryana'

common_eprocure.eprocure(SCRIPT_NAME,domain_url,org_state)
