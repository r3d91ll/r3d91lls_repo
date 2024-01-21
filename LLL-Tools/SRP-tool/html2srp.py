import os
import openai
from bs4 import BeautifulSoup

def extract_content_and_code(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    text_content = soup.get_text()  # Extracts all text content
    code_blocks = soup.find_all('code')  # Finds all Python code blocks
    return text_content, code_blocks

def generate_spr(text, code_blocks):
    combined_content = text + '\n'.join(block.text for block in code_blocks)
    response = openai.Completion.create(
        model="asst_uiJWj3r8YLVxPFlG4ER4GzoL",  # Your custom assistant's ID
        prompt=combined_content,
        max_tokens=2048  # Adjust as needed
    )

    return response.choices[0].text

def save_spr_file(spr_content, file_name, output_dir):
    with open(os.path.join(output_dir, file_name), 'w') as file:
        file.write(spr_content)

def main(directory_path):
    openai.api_key = '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'
    output_dir = 'SRP-files'
    os.makedirs(output_dir, exist_ok=True)

    for file_name in os.listdir(directory_path):
        if file_name.endswith('.html'):
            with open(os.path.join(directory_path, file_name), 'r') as file:
                html_content = file.read()

            text_content, code_blocks = extract_content_and_code(html_content)
            spr_content = generate_spr(text_content, code_blocks)
            save_spr_file(spr_content, file_name, output_dir)

if __name__ == "__main__":
    directory_path = '/path/to/your/html/files'  # Replace with your directory path
    main(directory_path)
