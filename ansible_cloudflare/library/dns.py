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
import os

def get_or_create_dns_record(cf, zone_id, dns_record_data):

    result = dict(
        changed=False,
        record_id=''
    )

    return_status = False

    msg = ""

    if not cf:
        msg = "Object Cloudflare is None"
        return return_status, result, msg

    dns_records = cf.zones.dns_records(zone_id)
    
    value_key = 'content' if 'content' in dns_record_data['value'] else 'data'

    for record in dns_records:
        if record['type'] == dns_record_data['type'] and \
            record['name'] == dns_record_data['name'] and \
            record[value_key] == dns_record_data['value'][value_key]:
            msg = f"Record {record['type']} - {record['name']} - {value_key} already on zone"
            return_status = True
            result['record_id'] = record['id']
            return return_status, result, msg

    keys_to_remove = ["email", "api_key", "zone_id", "file_db"]
    dns_record = {}

    for key, value in dns_record_data.items():
        if key == 'priority' and value == -1:
            continue
        if key not in keys_to_remove:
            if key == "value":
                for k,v in value.items():
                    if v is not None:
                        dns_record[k] = v
            else:
                dns_record[key] = value

    new_record = cf.zones.dns_records.post(zone_id, data=dns_record)

    return_status = True
    result['changed'] = True
    result['record_id'] = new_record['id']
    return return_status, result, msg


def import_dns_db(cf=None, db_file_path=None, zone_id=None):
    result = dict(
        changed=False,
        record_id=''
    )

    return_status = False

    msg = ""
    if not os.path.exists(db_file_path):
        msg = f"DB file {db_file_path} does not exists"
        return return_status, result, msg

    fd = open(db_file_path, 'rb')

    m = cf.zones.dns_records
    m = getattr(m, 'import_')
    
    try:
        db_import = m.post(zone_id, files={'file':fd})
    except Exception as e:
        msg = f"Error importing the DB file\nError: {e}"
        return return_status, result, msg

    return_status = True
    result['changed'] = True

    return return_status, result, msg
        


def run_module():
    module_args = dict(
        email=dict(type='str', required=True),
        api_key=dict(type='str', required=True, no_log=True),
        zone_id=dict(type='str', required=True),
        value=dict(
            type='dict',
            required=False,
            options=dict(
                content=dict(type='str', required=False),
                data=dict(type='dict',required=False),
            )
        ),
        name=dict(type='str', required=False),
        priority=dict(type='int', required=False), # TODO this could be None
        type=dict(type='str', required=False),
        comment=dict(type='str', required=False),
        tags=dict(type='list', required=False),
        ttl=dict(type='int', required=False),
        file_db=dict(type='str', required=False)
    )

    result = dict(
        changed=False,
        record_id=''
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        mutually_exclusive=[('name', 'file_db')],
        required_one_of=[('name', 'file_db')],
        required_together=[
            ('name', 'type', 'ttl')
        ]
    )

    if module.check_mode:
        module.exit_json(**result)

    cf = None

    try:
        cf = CloudFlare.CloudFlare(email=module.params['email'], key=module.params['api_key'])
    except Exception as e:
        msg = f"Failed to initialize Cloudflare API\nError: {e}"
        module.fail_json(msg=msg, **result)
    


    if module.params['file_db']:
        return_status, result, msg = import_dns_db(cf, module.params['file_db'], module.params['zone_id'])
    else:
        return_status, result, msg = get_or_create_dns_record(cf, module.params['zone_id'], module.params)

    

    if not return_status:
        module.fail_json(msg=msg, **result)
    
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
