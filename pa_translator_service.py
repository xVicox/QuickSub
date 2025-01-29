import requests
import re

class PATranslatorService:

    def __init__(self, payload, ):
        # getting the payload ready for processing
        self._path = payload.get_path()
        self._dir_path = payload.get_dir_path()
        self._source_lang = payload.get_source_lang()
        self._target_lang = payload.get_target_lang()

        # Sets the maximum number of characters to be handled at once. Defaults to 2000, which is considered optimal for Lingva Translate API requests.
        self._max_chars = 2000
        # Dictionary to store sequence numbers as keys and corresponding timestamps as values
        self._sequence_numbers_and_timestamps = {}

    @staticmethod
    def read_file(file_path):
        """
        Returns:
            list: A list of strings representing the lines of the file, or an empty list in case of failure.

        Raises:
            FileNotFoundError: If the file does not exist at the specified path.
            PermissionError: If the program does not have permission to access the file.
            Exception: Any other unexpected errors during file reading.
            """
        try:
            # with open(file_path, "r", encoding="utf-8") as file:
            with open(file_path, "r", encoding="latin-1") as file:
                raw_data = file.read()  # Read the entire content at once
                content = raw_data.strip().split("\n")  # Split into lines after reading
                return content  # Returns a list of strings
        except FileNotFoundError:
            print(f"File not found: {file_path}")
            return []
        except PermissionError:
            print(f"You do not have permission to access: {file_path}")
            return []
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return []

    @staticmethod
    def remove_timestamps(subs_lines):
        """
        Removes subtitle lines that contain timestamps from the provided list of lines.
        A line is considered a timestamp if it contains the string '-->' or has 4 or more colons.

        Args:
            subs_lines (list): A list of subtitle lines, typically read from a subtitle file.

        Returns:
            list: A list of subtitle lines with timestamp lines removed.
        """
        clear_subtitles = []
        for line in subs_lines:
            if not ("-->" in line or  str(line).count(":") >= 4):
                clear_subtitles.append(line)
        return clear_subtitles

    def separate_seq_nums_and_timestamps(self, subs_lines):
        """
        Extracts sequence numbers and corresponding timestamps from the provided subtitle lines.
        Stores them in a dictionary, where sequence numbers are the keys and timestamps are the values.

        Args:
            subs_lines (list): A list of subtitle lines, where each line is a string.

        Returns:
            None: The sequence numbers and timestamps are stored in the class's
            '_sequence_numbers_and_timestamps' attribute.
        """
        seq_num = None
        timestamp = None
        for line in subs_lines:
            line = line.strip()
            # Check if the line is a seq number
            if line.isdigit():
                seq_num = line
            # Check if the line is a timestamp
            if str(line).count(":") >= 4:
                if seq_num:
                    timestamp = line
                    self._sequence_numbers_and_timestamps[seq_num] = timestamp
                    #Reseting for the next iteration
                    seq_num = None
                    timestamp = None

    def process_subtitles(self, sub_lines):
        """
        Processes subtitle lines by removing timestamps and extracting sequence numbers and timestamps.

        Args:
            sub_lines (list): A list of subtitle lines, where each line is a string.

        Returns:
            list: A list of subtitle lines with timestamps removed.
        """
        subs_without_timestamps = PATranslatorService.remove_timestamps(sub_lines)
        PATranslatorService.separate_seq_nums_and_timestamps(self, sub_lines)
        return subs_without_timestamps

    @staticmethod
    def line_cleanup(line):
        """
        Cleans up special characters and formatting in subtitle lines before processing.

        Handles the following:
            - Replaces question marks with semicolons.
            - Replaces HTML <i> tags with placeholder strings.
            - Removes URLs from the line.

        Args:
            line (str): The subtitle line to be cleaned up.

        Returns:
            str: The cleaned-up subtitle line.
        """
        # handling question marks
        line = line.replace("?", ";")
        # handling html style tags
        line = line.replace("<i>", ";;")
        line = line.replace("</i>", ";;;")
        # Removing url's
        url_pattern = r'https?://\S+|www\.\S+'
        line = re.sub(url_pattern, '', line)
        return line

    @staticmethod
    def line_reassemble(line):
        """
        Reassembles special characters and formatting in subtitle lines after processing.

        Reverses the transformations made by the `line_cleanup` method, restoring:
            - HTML <i> tags from placeholders.
            - Semicolons back to question marks.

        Args:
            line (str): The subtitle line to be reassembled.

        Returns:
            str: The reassembled subtitle line with original formatting restored.
        """
        # html style tags
        line = line.replace(";;;", "</i>")
        line = line.replace(";;", "<i>")
        # question marks
        line = line.replace(";", "?")
        return line
    
    def create_chunks(self, subs_lines):
        """
        Splits a list of subtitle lines into chunks, ensuring each chunk does not exceed the maximum character limit.

        If a chunk is near the limit, it will start a new one. Additionally, if a line contains only a sequence number,
        it will be separated with a space to ensure it's properly handled by the API.

        Args:
            subs_lines (list): A list of subtitle lines to be split into chunks.

        Returns:
            list: A list of subtitle chunks, each of which does not exceed the maximum allowed character length.
        """
        chunks = []
        chunk = ""

        for line in subs_lines:
            line = PATranslatorService.line_cleanup(line)

            if len(chunk) <= self._max_chars - len(line):
                if line.strip().isdigit():
                    line = f" {line} "
                chunk += line
            else:
                chunks.append(chunk.strip())
                chunk = line
        # Making sure the last chunk is appended to the chunks list
        if len(chunk) > 0:
            chunks.append(chunk.strip())

        return chunks

    @staticmethod
    def translate_text(source_lang, target_lang, text):
        """
        Translates a given text from source_lang to target_lang by calling a translation API.

        Args:
            source_lang (str): The language code for the source language (e.g., 'en').
            target_lang (str): The language code for the target language (e.g., 'sr').
            text (str): The text to be translated.

        Returns:
            str: The translated text or an error message if the translation fails.
        """
        url = f"http://localhost:3000/api/v1/{source_lang}/{target_lang}/{text}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json().get("translation", "Translation not found")
        else:
            return f"Error: {response.json().get('error', 'Unknown error')}"

    @staticmethod
    def translate_chunks(chunks, source_lang, target_lang):
        """
        Translates a list of chunks from source_lang to target_lang and reassembles them.

        Args:
            chunks (list): A list of subtitle chunks to be translated.
            source_lang (str): The language code for the source language (e.g., 'en').
            target_lang (str): The language code for the target language (e.g., 'sr').

        Returns:
            list: A list of translated and reassembled subtitle chunks.
        """
        translated_chunks = []

        for chunk  in chunks:
            chunk = chunk.strip().replace("\n", " ")
            translation = PATranslatorService.translate_text(source_lang, target_lang, chunk)
            translation = PATranslatorService.line_reassemble(translation)
            translated_chunks.append(translation)

        return translated_chunks

    def reassemble_subs(self, translated_chunks):
        """
        Reassembles subtitle chunks by adding sequence numbers and timestamps.

        Args:
           translated_chunks (list): List of translated subtitle chunks.

        Returns:
           list: A list of reassembled subtitle lines with sequence numbers and timestamps.
        """
        translated_subs = []
        for chunk in translated_chunks:
            while not chunk == "":
                chunk = chunk.strip()
                words = ""
                while chunk and not str.isdigit(chunk.split()[0]):
                    words += chunk.split()[0] + " "
                    chunk = " ".join(chunk.split()[1:])
                    continue

                if chunk and str.isdigit(chunk.split()[0]):
                    if not words == "":
                        # append translated line
                        words = words + "\n"
                        translated_subs.append(words)

                    line = chunk.split()[0]
                    # append sequence number
                    translated_subs.append(line)
                    #### append timestamp from dictionary
                    translated_subs.append(self._sequence_numbers_and_timestamps[line])
                    ####
                    chunk = " ".join(chunk.split()[1:])

        return translated_subs

    @staticmethod
    def write_to_file(content, file_path):
        """
        Writes the provided content to a specified file.

        Args:
            content (list): A list of strings (lines of text) to be written to the file.
            file_path (str): The path where the file should be saved, including the filename and extension.

        Raises:
           Exception: If an error occurs during the file writing process (e.g., file permission issues).
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                for line in content:
                    line = line + "\n"
                    file.write(line)
            # here we notice the user that the translation is over and the file is written
            from gui import SubtitleTranslatorGUI
            gui = SubtitleTranslatorGUI.get_instance()
            gui.on_translate_button_clicked(True)

        except Exception as e:
            print(f"Error writing to file: {e}")

    def process_translation(self):
        # get the raw subtitle lines from source file
        unprocessed_subtitle = self.read_file(self._path)
        # process subtitles, removing timestamps from subtitles + getting ready for later reassembly
        processed_subtitle = self.process_subtitles(unprocessed_subtitle)
        #create chunks
        chunks = self.create_chunks(processed_subtitle)
        translated_chunks = self.translate_chunks(chunks, self._source_lang, self._target_lang)
        reassembled_chunks = self.reassemble_subs(translated_chunks)
        self.write_to_file(reassembled_chunks, self._dir_path)