import os
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

class NoStopFileProcessor:
    def __init__(self, directory, mode='BooleanFree'):
        self.directory = directory
        self.mode = mode
        self.stop_words = set(stopwords.words('english'))
        if mode == 'BooleanFree':
            self.excluded_words = {'and', 'or', 'not'}
            self.stop_words -= self.excluded_words
        else:
            self.excluded_words = set()

        # Download NLTK stop words if not already downloaded
        nltk.download('punkt')
        nltk.download('stopwords')

    def set_directory(self, directory):
        self.directory = directory

    def add_excluded_word(self, word):
        if word in self.stop_words:
            self.stop_words.remove(word)
            self.excluded_words.add(word)

    def remove_excluded_word(self, word):
        if word in self.excluded_words:
            self.excluded_words.remove(word)
            self.stop_words.add(word)

    def _remove_stop_words(self, text):
        word_tokens = word_tokenize(text)
        return ' '.join([word for word in word_tokens if word.lower() not in self.stop_words])

    def process_files(self):
        for root, dirs, file_names in os.walk(self.directory):
            for file_name in file_names:
                if file_name.endswith('.txt') or file_name.endswith('.md'):
                    file_path = os.path.join(root, file_name)
                    with open(file_path, 'r') as file_obj:
                        content = file_obj.read()

                    # Create a copy with 'nostop_' prefix
                    new_file_path = os.path.join(root, f'nostop_{file_name}')
                    with open(new_file_path, 'w') as new_file_obj:
                        # Remove stop words
                        modified_content = self._remove_stop_words(content)
                        new_file_obj.write(modified_content)

# Usage
processor = NoStopFileProcessor('/path/to/directory', mode='BooleanFree')
# Optional: Add or remove words from the excluded list
# processor.add_excluded_word('example')
# processor.remove_excluded_word('not')
processor.process_files()
