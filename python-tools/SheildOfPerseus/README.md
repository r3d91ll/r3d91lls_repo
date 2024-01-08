# Shield of Perseus 

This Python script, named after the shield used by the Greek hero Perseus to indirectly view Medusa and avoid her petrifying gaze, is developed to sanitize sensitive information from logs, console output, or any other text input. It provides an additional layer of security when sharing these data with outside parties or applications, like AI chatbots, to ensure that sensitive information is not inadvertently disclosed.

In today's digital environment where data breaches are common, and regulations around data privacy are getting more stringent, the ability to cleanse logs and other outputs is increasingly important. This script helps by replacing potentially sensitive data with placeholders, ensuring that the original information is not accessible from the sanitized output.

## Purpose

The purpose of this script is to prevent the accidental disclosure of sensitive information. It is particularly valuable in scenarios where console outputs, logs, or other data containing potentially sensitive information need to be shared with third-party services or made available in public spheres.

## Requirements

- Python 3.6 or higher

## Usage

To sanitize text input, run the script with the following command:

```bash
python shieldofperseus.py -i input.txt -j sanitized.json
```

To reverse the sanitization process:

```bash
python shieldofperseus.py -i input.txt -j sanitized.json -r
```

## Extending the script

The script is designed for easy extension. New regex patterns for identifying sensitive information can be added to the `patterns` dictionary:

```python
patterns = {
    # existing patterns
    re.compile(r'your_regex_pattern'): 'placeholder_name',
    # Add new patterns here
}
```

For instance, to add a pattern for sanitizing Social Security Numbers:

```python
patterns = {
    # ... existing patterns ...
    re.compile(r'\b\d{3}-\d{2}-\d{4}\b'): 'SSN',
}
```

This will replace detected SSNs with placeholders like `{SSN1}`, `{SSN2}`, etc., storing the original data and its corresponding placeholder in a JSON file.

**Note**: Regular expressions should be used carefully to accurately match the intended data while minimizing false positives.

## Recent Updates

- Enhanced `sanitize` function with improved error handling, logging, and file management.
- Added regex patterns for detecting and sanitizing various personal data, including SSNs, bank routing numbers, credit card numbers, and more.

---

*"For well he knew that, of the Gorgons, one alone was mortal: and he knew that she was there: he saw her in the looking glass he bore upon his arm. Her face was dreadful and obscene, a face of death, and, lest the sight should petrify him, he averted his eyes, and backward stepped, and turned his face away."* - Ovid, Metamorphoses, Book 4
