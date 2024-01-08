import argparse
import json
import re
import logging
import os

class Sanitizer:
    """ 
    A class to sanitize sensitive information in text files using regular expressions.
    It can also reverse the sanitization process using a JSON file mapping.
    """

    def __init__(self):
        self.patterns = self.compile_regex_patterns()
        logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    def compile_regex_patterns(self):
        """ Compile regular expressions for better performance. """
        return {
        # Generic Patterns
        re.compile(r'\b((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'): 'IP',  
        re.compile(r'\b((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\/([1-2]?[0-9]|3[0-2])\b'): 'CIDR', 
        # AWS Patterns
        re.compile(r'(acc-\w{8})'): 'accountNumSimple',
        re.compile(r'(vol-\w{8,18})'): 'volumeId',
        re.compile(r'(sg-\w{8})'): 'securityGroupId',
        re.compile(r'(arn:aws[^:]*:iam::)(\d{12})'): 'arnAccountNum',
        re.compile(r'(arn:aws[^:]*:ec2:[^:]*:)(\d{12})(:instance/)(i-\w{8,})'): 'instanceId',
        re.compile(r'(arn:aws[^:]*:rds:[^:]*:)(\d{12})(:db:)(rds\w*)'): 'rdsId',
        re.compile(r'(arn:aws[^:]*:iam::)(\d{12})(:user/)(\w*)'): 'iamUser', 
        re.compile(r'(arn:aws[^:]*:iam::)(\d{12})(:role/)(\w*)'): 'iamRole',
        re.compile(r'(arn:aws[^:]*:iam::)(\d{12})(:policy/)(\w*)'): 'iamPolicy',
        re.compile(r'(arn:aws[^:]*:iam::)(\d{12})(:group/)(\w*)'): 'iamGroup',
        # Azure Patterns
        re.compile(r'(subscriptions/)([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})') : 'AZsubscriptionId',
        re.compile(r'(resourceGroups/)([a-zA-Z0-9-_\.]+)') : 'AZresourceGroup',
        re.compile(r'(providers/Microsoft.Compute/virtualMachines/)([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})') : 'AZvmId',
        re.compile(r'([a-z0-9]{3,24})\.blob\.core\.windows\.net') : 'AZstorageAccount',
        re.compile(r'(providers/Microsoft.Storage/storageAccounts/)([a-z0-9]{3,24})') : 'AZstorageAccount',
        re.compile(r'(providers/Microsoft.KeyVault/vaults/)([a-zA-Z0-9-]+)'): 'AZkeyVault',
        re.compile(r'(providers/Microsoft.Network/virtualNetworks/)([a-zA-Z0-9-_\.]+)') : 'AZvnet',
        re.compile(r'(providers/Microsoft.Network/networkInterfaces/)([a-zA-Z0-9-_\.]+)') : 'AZnic',
        re.compile(r'(providers/Microsoft.Sql/servers/)([a-zA-Z0-9-_]+)') : 'AZsqlServer',
        re.compile(r'(providers/Microsoft.Sql/servers/)([a-zA-Z0-9-_]+)/databases/([a-zA-Z0-9-_\.]+)') : 'AZsqlDatabase',
        re.compile(r'(providers/Microsoft.Network/networkSecurityGroups/)([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})') : 'AZnsgId',
        re.compile(r'(InstrumentationKey=)([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})') : 'AZappInsightsKey',
        re.compile(r'(providers/Microsoft.Compute/images/)([a-zA-Z0-9-_\.]+)') : 'AZimage',
        re.compile(r'(providers/Microsoft.Compute/disks/)([a-zA-Z0-9-_\.]+)') : 'AZdisk',
        re.compile(r'(providers/Microsoft.Compute/snapshots/)([a-zA-Z0-9-_\.]+)') : 'AZsnapshot',
        re.compile(r'(providers/Microsoft.Compute/virtualMachineScaleSets/)([a-zA-Z0-9-_\.]+)') : 'AZvmss',
        re.compile(r'(providers/Microsoft.Compute/virtualMachineScaleSets/)([a-zA-Z0-9-_\.]+)/virtualMachines/(\d+)') : 'AZvmssVm',
        re.compile(r'(providers/Microsoft.Compute/virtualMachineScaleSets/)([a-zA-Z0-9-_\.]+)/virtualMachines/(\d+)/networkInterfaces/(\d+)') : 'AZvmssNic',
        # GCP Patterns
        re.compile(r'(projects/)([a-zA-Z0-9-_]{6,30})'): 'GCPprojectId',
        re.compile(r'(instances/)([a-zA-Z0-9-_.]+)'): 'GCPinstanceId',
        re.compile(r'(zones/)([a-zA-Z0-9-]+)'): 'GCPzone',
        re.compile(r'(buckets/)([a-zA-Z0-9-_.]+)'): 'GCPbucket',
        re.compile(r'(serviceAccounts/)([a-zA-Z0-9-_]+@[a-zA-Z0-9-_]+\.iam\.gserviceaccount\.com)'): 'GCPserviceAccount',
        re.compile(r'(firewalls/)([a-zA-Z0-9-_.]+)'): 'GCPfirewall',
        re.compile(r'(networks/)([a-zA-Z0-9-_.]+)'): 'GCPnetwork',
        re.compile(r'(subnets/)([a-zA-Z0-9-_.]+)'): 'GCPsubnet',
        re.compile(r'(clusters/)([a-zA-Z0-9-_.]+)'): 'GCPcluster',
        re.compile(r'(functions/)([a-zA-Z0-9-_.]+)'): 'GCPfunction',
        re.compile(r'(disks/)([a-zA-Z0-9-_.]+)'): 'GCPdisk',
        re.compile(r'(snapshots/)([a-zA-Z0-9-_.]+)'): 'GCPsnapshot',
        re.compile(r'(images/)([a-zA-Z0-9-_.]+)'): 'GCPimage',
        re.compile(r'(vpcs/)([a-zA-Z0-9-_.]+)'): 'GCPvpc',
        re.compile(r'(addresses/)([a-zA-Z0-9-_.]+)'): 'GCPaddress',
        re.compile(r'(forwardingRules/)([a-zA-Z0-9-_.]+)'): 'GCPforwardingRule',
        re.compile(r'(targetPools/)([a-zA-Z0-9-_.]+)'): 'GCPtargetPool',
        re.compile(r'(targetInstances/)([a-zA-Z0-9-_.]+)'): 'GCPtargetInstance',
        re.compile(r'(targetHttpsProxies/)([a-zA-Z0-9-_.]+)'): 'GCPtargetHttpsProxy',
        re.compile(r'(targetHttpProxies/)([a-zA-Z0-9-_.]+)'): 'GCPtargetHttpProxy',
        re.compile(r'(urlMaps/)([a-zA-Z0-9-_.]+)'): 'GCPurlMap',
        re.compile(r'(backendServices/)([a-zA-Z0-9-_.]+)'): 'GCPbackendService',
        re.compile(r'(sslCertificates/)([a-zA-Z0-9-_.]+)'): 'GCPsslCertificate',
        re.compile(r'(sslPolicies/)([a-zA-Z0-9-_.]+)'): 'GCPsslPolicy',
        re.compile(r'(healthChecks/)([a-zA-Z0-9-_.]+)'): 'GCPhealthCheck',
        re.compile(r'(instanceGroups/)([a-zA-Z0-9-_.]+)'): 'GCPinstanceGroup',
        re.compile(r'(instanceTemplates/)([a-zA-Z0-9-_.]+)'): 'GCPinstanceTemplate',
        re.compile(r'(instanceGroupManagers/)([a-zA-Z0-9-_.]+)'): 'GCPinstanceGroupManager',
        re.compile(r'(instanceGroupManagers/)([a-zA-Z0-9-_.]+)/instanceTemplates/([a-zA-Z0-9-_.]+)'): 'GCPinstanceGroupManagerTemplate',
        re.compile(r'(instanceGroupManagers/)([a-zA-Z0-9-_.]+)/instanceGroupManagers/([a-zA-Z0-9-_.]+)'): 'GCPinstanceGroupManagerNested',
        re.compile(r'(instanceGroupManagers/)([a-zA-Z0-9-_.]+)/instanceGroupManagers/([a-zA-Z0-9-_.]+)/instanceTemplates/([a-zA-Z0-9-_.]+)'): 'GCPinstanceGroupManagerNestedTemplate',
        # Personal Identifiable Information (PII) Patterns
        re.compile(r'\b\d{3}-\d{2}-\d{4}\b'): 'SSN',  # SSN format: XXX-XX-XXXX
        re.compile(r'\b\d{9}\b'): 'SSN',  # SSN format without dashes
        re.compile(r'\b\d{3}-\d{3}-\d{3}-\d{3}\b'): 'BankRoutingNumber',  # Bank Routing Number
        re.compile(r'\b[0-9]{16}\b'): 'CreditCardNumber',  # Basic Credit Card Number (16 digits)
        re.compile(r'\b(4[0-9]{12}(?:[0-9]{3})?)\b'): 'VisaCreditCard',  # VISA: 13 or 16 digits starting with 4
        re.compile(r'\b(5[1-5][0-9]{14})\b'): 'MasterCard',  # MasterCard: starts with 51-55, 16 digits
        re.compile(r'\b(3[47][0-9]{13})\b'): 'AmexCard',  # AMEX: starts with 34 or 37, 15 digits
        re.compile(r'\b(6(?:011|5[0-9]{2})[0-9]{12})\b'): 'DiscoverCard',  # Discover: starts with 6011 or 65, 16 digits
        re.compile(r'\b([2-9]\d{2}-\d{2}-\d{4})\b'): 'PotentialSSN',  # Potential SSN (non-leading 0 or 1)
        re.compile(r'\b(\d{8,10})\b'): 'PhoneNumber',  # Basic US Phone Number (8-10 digits)
        re.compile(r'\b[A-Z]{2}\d{6}\b'): 'PassportNumber',  # Generic Passport Number (2 letters followed by 6 digits)
    }

    def sanitize(self, input_file, json_file):
        """ Sanitize sensitive information in the input file. """
        input_string = self.read_file(input_file)
        if input_string is None:
            return None

        sanitized_info = {}
        value_to_placeholder_map = {}  # Map to track already encountered values

        for pattern, replacement in self.patterns.items():
            for item in pattern.findall(input_string):
                if item not in value_to_placeholder_map:
                    # If the item is new, create a new placeholder
                    placeholder = f'{{{replacement}{len(sanitized_info)}}}'
                    sanitized_info[placeholder] = item
                    value_to_placeholder_map[item] = placeholder
                else:
                    # If the item is already encountered, reuse its placeholder
                    placeholder = value_to_placeholder_map[item]

                input_string = input_string.replace(item, placeholder)

        self.write_file(json_file, json.dumps(sanitized_info))
        return input_string

    def reverse(self, input_file, json_file):
        """ Reverse the sanitization process using the JSON file. """
        if not os.path.exists(json_file):
            logging.error(f"JSON file {json_file} does not exist.")
            return None

        try:
            with open(json_file, 'r') as file:
                sanitized_info = json.load(file)

            with open(input_file, 'r') as file:
                input_string = file.read()

            for placeholder, original in sanitized_info.items():
                input_string = input_string.replace(placeholder, original)

            return input_string

        except IOError as e:
            logging.error(f"Error in file operation: {e}")
            return None


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', required=True, help='Input file')
    parser.add_argument('-j', '--json', required=True, help='JSON file for storing/retrieving sanitized data')
    parser.add_argument('-r', '--reverse', action='store_true', help='Perform reverse operation')

    args = parser.parse_args()

    sanitizer = Sanitizer()

    if args.reverse:
        result = sanitizer.reverse(args.input, args.json)
    else:
        result = sanitizer.sanitize(args.input, args.json)

    if result:
        print(result)
