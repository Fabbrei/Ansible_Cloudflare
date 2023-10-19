#!/usr/bin/python

# Copyright: (c) 2023, Fabrizio Di Cesare <terry.jones@example.org> Massimo Schembri <massimo.schembri18@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: dcs.cloudflare.zone

short_description: Retrieve/Create a zone in cloudflare

version_added: "1.0.0"

description: This module creates or retrieves a zone from cloudflare.

options:
    email:
        description: The email credential to use the CloudFlare's API
        required: true
        type: str
    api_key:
        description: The api key to use the CloudFlare's API
        required: true
        type: str
    account_id:
        description: The account ID in which you want to create the zone, if you will omit this, you will create this in you root account
        required: false
        type: str
    name:
        description: The zone name
        required: true
        type: str
# Specify this value according to your collection
# in format of namespace.collection.doc_fragment_name
# extends_documentation_fragment:
#     - my_namespace.my_collection.my_doc_fragment_name

author:
    - Fabrizio Di Cesare (@Fabbrei)
    - Massimo Schembri (@peterparser)
'''

EXAMPLES = r'''
# Create a zone called "myzone.test" in a a specific account id
- name: Test with a message
  zone:
    name: myzone.test
    api_key: myapikey
    email: myemail@mail.com
    account_id: myaccountid

# Create a zone called "myzone.test" in the root account
- name: Test with a message
  zone:
    name: myzone.test
    api_key: myapikey
    email: myemail@mail.com
'''

RETURN = r'''
# These are examples of possible return values, and in general should use other names for return values.
zone_id:
    description: The zone id that has been created or retrieved
    type: str
    returned: always
    sample: ''
'''

from ansible.module_utils.basic import AnsibleModule
import CloudFlare

    
def get_or_create_zone(cf=None, params=None):
    account_id = params['account_id']
    name = params['name']
    result = dict(
        changed=False,
        zone_id=''
    )
    

    return_status = False

    msg = ""

    if not cf:
        msg = "Object Cloudflare is None"
        return return_status, result, msg

    current_zones = None

    try:
        if account_id:
            current_zones = cf.zones.get(params={"account": {"id": account_id}})
        else:
            current_zones = cf.zones.get()

    except Exception as e:
        msg = f"Failed to retrieve zones\nError:{e}"
        return return_status, result, msg


    if not current_zones:
        msg = "Failed to retrieve zones, current_zones is None"
        return return_status, result, msg


    for zone in current_zones:
        if zone['name'] == name:
            msg = f"Zone {name} already on Cloudflare account"
            return_status = True
            result['zone_id'] = zone['id']
            return return_status, result, msg

    
    
    data = {"name": name}

    if account_id:
        data.update({"account":{"id": account_id}})

    new_zone = None

    try:
        
        new_zone = cf.zones.post(data=data)
    
    except Exception as e:
        msg = f"Failed to create zone {name}\nError:{e}"
        return return_status, result, msg

    return_status = True
    result['changed'] = True
    result['zone_id'] = new_zone['id']

    return return_status, result, msg



def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        email=dict(type='str', required=True),
        api_key=dict(type='str', required=True),
        account_id=dict(type='str', required=False),
        name=dict(type='str', required=True)
    )
    
    result = dict(
        changed=False,
        zone_id=''
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
    

    return_status, result, msg = get_or_create_zone(cf, module.params)

    if not return_status:
        module.fail_json(msg=msg, **result)
    
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
