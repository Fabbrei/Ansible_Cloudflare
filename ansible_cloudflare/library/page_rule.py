#!/usr/bin/python

# Copyright: (c) 2023, Fabrizio Di Cesare <terry.jones@example.org> Massimo Schembri <massimo.schembri18@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: dcs.cloudflare.dns

short_description: This is module adds/retrieves a dns record in cloudflare.

version_added: "1.0.0"

description: This is module adds/retrieves a dns record in cloudflare in an idempotent manner. 

options:
    email:
        description: The email credential to use the CloudFlare's API
        required: true
        type: str
    api_key:
        description: The api key to use the CloudFlare's API
        required: true
        type: str
    zone_id:
        description: The zone_id in which you want to add/retrieve the record
        required: true
        type: str
    name:
        description: The name of the record
        required: true
        type: str
    type:
        description: The type of the record you want to add
        required: true
        type: str
    data:
        description: The content of the record
        required: true
        type: dict
    ttl:
        description: Time to live of the record
        required: true
        type: int
    

author:
    - Fabrizio Di Cesare (@Fabbrei)
    - Massimo Schembri (@peterparser)
'''

EXAMPLES = r'''
# Create an A record associated to myrecord.myzone with IP 100.100.100.100
- name: Test with a message
  dcs.cloudflare.dns:
    name: myrecord.myzone
    api_key: my_key
    email: mymail@mail.com
    zone_id: myzone_id
    type: A
    ttl: 3600
    data:
        content: 100.100.100.100

# Create an CNAME record associated
- name: Test with a message and changed output
  my_namespace.my_collection.my_test:
    name: hello world
    new: true

# CREATE AN SRV record
- name: Test failure of the module
  my_namespace.my_collection.my_test:
    name: fail me

# CREATE AN MX record

# CREATE A SRV RECORD
'''

RETURN = r'''
# These are examples of possible return values, and in general should use other names for return values.
record_id:
    description: The id of the record inserted
    type: str
    returned: always
    sample: 'hello world'
'''

from ansible.module_utils.basic import AnsibleModule
import CloudFlare


def create_page_rule(cf, zone_id, page_rule_data):

    current_page_rules = cf.zones.pagerules.get(zone_id)

    result = dict(
        changed=False,
        page_rule_id=''
    )

    return_status = False

    msg = ""

    # TODO Evaulate the array instead of single target/action
    
    for current_page_rule in current_page_rules:
        if current_page_rule['targets'][0]['constraint']['value'] == page_rule_data['targets'][0]['constraint']['value']:
            if current_page_rule['actions'][0] == page_rule_data['actions'][0]:
                msg = f"Rule with target with action exists"
                return_status = True
                result['page_rule_id'] = current_page_rule['id']
                return return_status, result, msg
            else:
                try:
                    new_page_rule = cf.zones.pagerules.put(zone_id, page_rule_data)
                except Exception as e:
                    msg = f"Error creating new rule\nError:{e}"
                    return return_status, result, msg

                result['changed'] = True
                return_status = True
                result['page_rule_id'] = new_page_rule['id']
                return return_status, result, msg
    
    new_page_rule = cf.zones.pagerules.post(zone_id, page_rule_data)

    result['changed'] = True
    return_status = True
    result['page_rule_id'] = new_page_rule['id']

    return return_status, result, msg

            



def run_module():
    module_args = dict(
        email=dict(type='str', required=True),
        api_key=dict(type='str', required=True, no_log=True),
        zone_id=dict(type='str', required=True),
        targets=dict(
            type='list',  
            required=True,
            elements='dict',
            options=dict(
                target=dict(type='str', required=True, choices=['url']),
                constraint=dict(
                    type='dict',
                    required=True,
                    options=dict(
                        operator=dict(
                            type='str',
                            required=True,
                            choices=['matches', 'contains', 'equals', 'not_equal', 'not_contain']
                        ),
                        value=dict(type='str', required=True)
                    )
                )
            )
        ),
        actions=dict(
            type='list',
            required=True,
            elements='dict',
            options=dict(
                id=dict(type='str', required=True),
                value=dict(type='dict', required=True)
            )
        ),
        status=dict(type='str', required=True, choices=['active', 'disabled']),
        priority=dict(type='int', required=False, default=1)

    )

    result = dict(
        changed=False,
        record_id=''
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    if module.check_mode:
        module.exit_json(**result)

    cf = None

    try:
        cf = CloudFlare.CloudFlare(email=module.params['email'], key=module.params['api_key'])
    except Exception as e:
        msg = f"Failed to initialize Cloudflare API\nError: {e}"
        module.fail_json(msg=msg, **result)


    zone_id = module.params['zone_id']

    page_rule_data = { k: module.params[k] for k in ['targets', 'actions', 'status', 'priority']}
    
    return_status, result, msg = create_page_rule(cf, zone_id, page_rule_data)

    if not return_status:
        module.fail_json(msg=msg, **result)
    
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
