# Shield of Perseus 

This Python script is developed to sanitize sensitive information from logs, console output, or any other text input. The script provides an additional layer of security when sharing these data with outside parties or applications, like AI chatbots, to ensure that sensitive information is not inadvertently disclosed.

The ability to cleanse logs and other output is increasingly important in today's digital environment where data breaches are common, and regulations around data privacy are getting more stringent. This script, named after the shield used by the Greek hero Perseus to indirectly view Medusa and avoid her petrifying gaze, helps by replacing potentially sensitive data with placeholders, ensuring that the original information is not accessible from the sanitized output.

## Purpose

The purpose of this script is to prevent the accidental disclosure of sensitive information. It is especially valuable in scenarios where console outputs, logs, or other data containing potentially sensitive information are to be shared with third-party services or made available in public spheres.

## Requirements

- Python 3.6+

## Usage

You can run the script with the following command to sanitize:

```bash
python sheildofperseus.py -i input.txt -j sanitized.json
```

For reversing the process, use:

```bash
python sheildofperseus.py -i input.txt -j sanitized.json -r
```

## Extending the script

The script is designed to be easily extended. You can add more patterns by simply adding an entry to the `patterns` dictionary in the script:

```python
patterns = {
    # existing patterns
    r'pattern': 'placeholder_name',  # your new pattern
}
```

Here, `pattern` is a regular expression that matches the sensitive information you want to sanitize, and `placeholder_name` is the name you want to use in the placeholder for that type of information.

For example, if you wanted to add a pattern for sanitizing credit card numbers, you could add the following line:

```python
patterns = {
    # ... existing patterns ...
    r'\b\d{16}\b': 'CreditCard',  # Simple pattern for a 16-digit credit card number
}
```

This would replace any 16-digit numbers it finds with placeholders like `{CreditCard1}`, `{CreditCard2}`, etc., and store the original numbers and their replacements in the `sanitized_info` dictionary.

Remember to use regular expressions wisely to match exactly what you need without false positives.

*"For well he knew that, of the Gorgons, one alone was mortal: and he knew that she was there: he saw her in the looking glass he bore upon his arm. Her face was dreadful and obscene, a face of death, and, lest the sight should petrify him, he averted his eyes, and backward stepped, and turned his face away."* - Ovid, Metamorphoses, Book 4