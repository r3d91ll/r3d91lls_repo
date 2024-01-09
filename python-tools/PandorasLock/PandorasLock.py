import os
import json
import re
import logging
import random
import string

class PandorasLock:
    """
    A class to sanitize sensitive information in text using regular expressions
    and to reverse the sanitization in AI responses.
    """
    def __init__(self, config_path=None):
        # Set a default path and allow override by an environment variable or direct argument
        default_path = '/home/todd6585/git/r3d91lls_repo/python-tools/PandorasLock/pandorasconfig.json'
        self.config_path = config_path or os.getenv('PANDORACONFIG_PATH', default_path)
        self.patterns = self.load_regex_patterns()
        self.sanitization_map = {}  # To keep track of original and sanitized data

    def load_regex_patterns(self):
        """
        Load regular expression patterns from a JSON configuration file.
        """
        try:
            with open(self.config_path, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            logging.error(f"Config file {self.config_path} not found.")
            return {}

    def sanitize(self, text):
        """
        Sanitize sensitive information in the given text based on loaded regex patterns.
        """
        for pattern, replacement in self.patterns.items():
            matches = re.findall(pattern, text)
            for match in matches:
                match_str = ''.join(match) if isinstance(match, tuple) else match
                sanitized = replacement  # Consistent placeholder for the same match
                self.sanitization_map[sanitized] = match_str
                text = text.replace(match_str, sanitized)
        return text

    def reverse_sanitization(self, text):
        """
        Reverse the sanitization process using the sanitization map.
        """
        for sanitized, original in self.sanitization_map.items():
            text = text.replace(sanitized, original)
        return text

class PandorasBox:
    def __init__(self, sanitizer):
        self.sanitizer = sanitizer
        self.original_order_map = {}

    def process_code_block(self, code_block):
        """
        Public function to process a code block with sanitization and deconstruction.
        """
        # Separate lines and shuffle them randomly
        lines = code_block.split("\n")
        random.shuffle(lines)

        # Apply PandorasLock and record original order
        for i in range(len(lines)):
            sanitized_line = self.sanitizer.sanitize(lines[i])
            self.original_order_map[sanitized_line] = lines[i]
            lines[i] = sanitized_line

        # Join the shuffled and sanitized lines and return
        return "\n".join(lines)

    def revert_code_order(self, sanitized_block):
        """
        Reverts the order of code lines to the original, using the original_order_map.
        """
        lines = sanitized_block.split("\n")
        reverted_lines = [self.original_order_map.get(line, line) for line in lines]
        return "\n".join(reverted_lines)

# # Example usage: PandorasLock
# # Create an instance of PandorasLock
# lock = PandorasLock()

# # Sanitize a text using the loaded regex patterns
# text = "My email is john.doe@example.com and my phone number is 123-456-7890."
# sanitized_text = lock.sanitize(text)
# print(sanitized_text)
# # Output: "My email is [EMAIL] and my phone number is [PHONE]."

# # Reverse the sanitization process
# original_text = lock.reverse_sanitization(sanitized_text)
# print(original_text)
# # Output: "My email is john.doe@example.com and my phone number is 123-456-7890."
