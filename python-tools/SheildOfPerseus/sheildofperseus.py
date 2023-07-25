import argparse
import json
import re

def sanitize(input_file, json_file):
    patterns = {
        r'(acc-\w{8})': 'accountNum',
        r'(sg-\w{8})': 'SG',
        r'(arn:aws[^:]*:iam::)(\d{12})': 'accountNum',
        r'(arn:aws[^:]*:ec2:[^:]*:)(\d{12})(:instance/)(i-\w{8,})': 'instanceId',
        r'(arn:aws[^:]*:rds:[^:]*:)(\d{12})(:db:)(rds\w*)': 'rdsId',
        r'(arn:aws[^:]*:iam::)(\d{12})(:user/)(\w*)': 'iamUser', 
        r'(arn:aws[^:]*:iam::)(\d{12})(:role/)(\w*)': 'iamRole',
        r'(arn:aws[^:]*:iam::)(\d{12})(:policy/)(\w*)': 'iamPolicy',
        r'(arn:aws[^:]*:iam::)(\d{12})(:group/)(\w*)': 'iamGroup',
        r'\b((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b': 'IP',  
        r'\b((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\/([1-2]?[0-9]|3[0-2])\b': 'CIDR',  
    }

    sanitized_info = {}
    pattern_to_placeholder_map = {}

    with open(input_file, 'r') as file:
        input_string = file.read()

        for pattern, replacement in patterns.items():
            for match in re.findall(pattern, input_string):
                if match[1] not in pattern_to_placeholder_map:
                    account_placeholder = '{' + replacement + str(len(sanitized_info)) + '}'
                    sanitized_info[account_placeholder] = match[1]
                    pattern_to_placeholder_map[match[1]] = account_placeholder  
                else:
                    account_placeholder = pattern_to_placeholder_map[match[1]]  

                input_string = input_string.replace(match[1], account_placeholder)

                if len(match) > 3:
                    if match[3] not in pattern_to_placeholder_map:
                        id_placeholder = '{' + replacement + str(len(sanitized_info)) + '}'
                        sanitized_info[id_placeholder] = match[3]
                        pattern_to_placeholder_map[match[3]] = id_placeholder
                    else:
                        id_placeholder = pattern_to_placeholder_map[match[3]]

                    input_string = input_string.replace(match[3], id_placeholder)

    with open(json_file, 'w') as file:
        json.dump(sanitized_info, file)

    return input_string

def reverse(input_file, json_file):
    with open(json_file, 'r') as file:
        sanitized_info = json.load(file)

    with open(input_file, 'r') as file:
        input_string = file.read()

        for placeholder, original in sanitized_info.items():
            input_string = input_string.replace(placeholder, original)

    return input_string

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', required=True, help='Input file')
    parser.add_argument('-j', '--json', required=True, help='JSON file for storing/retrieving sanitized data')
    parser.add_argument('-r', '--reverse', action='store_true', help='Perform reverse operation')

    args = parser.parse_args()

    if args.reverse:
        print(reverse(args.input, args.json))
    else:
        print(sanitize(args.input, args.json))


