import openai

# Set the API key
openai.api_key = 'your-api-key'

# Example: making a request to GPT-3
response = openai.Completion.create(
  engine="text-davinci-003",
  prompt="Translate the following English text to French: '{}'",
  max_tokens=60
)

print(response.choices[0].text.strip())
