#!/usr/bin/python

# Copyright: (c) 2018, Terry Jones <terry.jones@example.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: my_test

short_description: This is my test module

# If this is part of a collection, you need to use semantic versioning,
# i.e. the version is of the form "2.5.0" and not "2.4".
version_added: "1.0.0"

description: This is my longer description explaining my test module.

options:
    name:
        description: This is the message to send to the test module.
        required: true
        type: str
    new:
        description:
            - Control to demo if the result of this module is changed or not.
            - Parameter description can be a list as well.
        required: false
        type: bool
# Specify this value according to your collection
# in format of namespace.collection.doc_fragment_name
# extends_documentation_fragment:
#     - my_namespace.my_collection.my_doc_fragment_name

author:
    - Your Name (@yourGitHubHandle)
'''

EXAMPLES = r'''
# Pass in a message
- name: Test with a message
  my_namespace.my_collection.my_test:
    name: hello world

# pass in a message and have changed true
- name: Test with a message and changed output
  my_namespace.my_collection.my_test:
    name: hello world
    new: true

# fail the module
- name: Test failure of the module
  my_namespace.my_collection.my_test:
    name: fail me
'''

RETURN = r'''
# These are examples of possible return values, and in general should use other names for return values.
original_message:
    description: The original name param that was passed in.
    type: str
    returned: always
    sample: 'hello world'
message:
    description: The output message that the test module generates.
    type: str
    returned: always
    sample: 'goodbye'
'''

from ansible.module_utils.basic import AnsibleModule
import CloudFlare



    
def create_zone(cf=None, name=None, account_id=None):
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
    
    # seed the result dict in the object
    # we primarily care about changed and state
    # changed is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
        zone_id=''
    )

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        module.exit_json(**result)

    cf = None

    try:
        cf = CloudFlare.CloudFlare(email=module.params['email'], key=module.params['api_key'])
    except Exception as e:
        msg = f"Failed to initialize Cloudflare API\nError: {e}"
        module.fail_json(msg=msg, **result)
    

    return_status, result, msg = create_zone(cf, module.params['name'], module.params['account_id'])

    if not return_status:
        module.fail_json(msg=msg, **result)
    
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
