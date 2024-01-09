import unittest
from PandorasLock import PandorasLock

class TestPandorasLock(unittest.TestCase):
    def setUp(self):
        self.pandoras_lock = PandorasLock('pandorasconfig.json')

    def generic_sanitization(self, test_text, expected):
        sanitized_text = self.pandoras_lock.sanitize(test_text)
        self.assertEqual(sanitized_text, expected)

    def test_ip_address(self):
        self.generic_sanitization("My IP is 192.168.1.1", "My IP is IP")

    def test_cidr(self):
        self.generic_sanitization("Network CIDR is 192.168.1.0/24", "Network CIDR is CIDR")

    def test_ssn(self):
        self.generic_sanitization("My SSN is 123-45-6789", "My SSN is S-S-N")

    def test_awsArn(self):
        self.generic_sanitization("My AWS account number is arn:aws:iam::123456789012", "My AWS account number is arn:aws:iam::arnAccountNum")

    def test_awsVolId(self):
        self.generic_sanitization("My volumeId is vol-12345678", "My volumeId is volumeId")

    def test_sgID(self):
        self.generic_sanitization("The Security group ID is sg-abcdefgh", "The Security group ID is securityGroupId")

    def test_ec2ID(self):
        self.generic_sanitization("Here is the AWS Arn for that EC2 instance arn:aws:ec2:region:123456789012:instance/i-ab365cdefgh", "Here is the AWS Arn for that EC2 instance arn:aws:ec2:region:arnAccountNum:instanceId")

    def test_rdsID(self):
        self.generic_sanitization("The RDS arn:aws:rds:region:123456789012:db:rds-db is down", "The RDS arn:aws:rds:region:arnAccountNum:db:rdsId is down")

    def test_sanitize_and_reverse(self):
        test_text = "Sensitive info: 123-45-6789"
        sanitized_text = self.pandoras_lock.sanitize(test_text)
        reversed_text = self.pandoras_lock.reverse_sanitization(sanitized_text)
        self.assertEqual(test_text, reversed_text)

    def test_sanitize_no_match(self):
        test_text = "No sensitive info here"
        sanitized_text = self.pandoras_lock.sanitize(test_text)
        self.assertEqual(test_text, sanitized_text)

if __name__ == '__main__':
    unittest.main()
