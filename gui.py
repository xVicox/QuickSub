import os

from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QFileDialog,
    QVBoxLayout,
    QWidget,
    QHBoxLayout, QSizePolicy,
    QMessageBox, QProgressBar
)

from translation_payload import TranslationPayload
from translation_worker import TranslationWorker

class SubtitleTranslatorGUI(QMainWindow):

    _instance = None

    @staticmethod
    def get_instance():
        """
        Retrieves the singleton instance of the SubtitleTranslatorGUI class.

        Returns:
            SubtitleTranslatorGUI: The singleton instance of the SubtitleTranslatorGUI.
        """

        if SubtitleTranslatorGUI._instance is None:
            SubtitleTranslatorGUI._instance = SubtitleTranslatorGUI()
        return SubtitleTranslatorGUI._instance

    def __init__(self):
        """
        Initializes the SubtitleTranslatorGUI window, setting up UI components and layout.
        """

        if SubtitleTranslatorGUI._instance is not None:
            return
        super().__init__()
        SubtitleTranslatorGUI._instance = self

        super().__init__()
        self._initialized = True  # Mark as initialized

        # The path the user will pick the file from
        self._users_path = ""

        super().__init__()

        self.setWindowTitle("QuickSub")
        self.setGeometry(100, 100, 600, 250)
        self.setWindowIcon(QIcon("resources/app_icon.png"))

        # Main widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layouts
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # File selection
        file_layout = QHBoxLayout()
        self._file_label = QLabel("Select Subtitle File:")
        self._file_input = QLineEdit()
        self._file_input.setReadOnly(True)
        self._file_input.setStyleSheet("background-color: #f0f0f0;")
        self._file_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._file_browse_button = QPushButton("Browse")
        self._file_browse_button.clicked.connect(self.on_file_browse_button_clicked)
        file_layout.addWidget(self._file_label)
        file_layout.addWidget(self._file_input)
        file_layout.addWidget(self._file_browse_button)
        main_layout.addLayout(file_layout)

        # Target directory
        dir_layout = QHBoxLayout()
        self._dir_label = QLabel("Select Target Directory:")
        self._dir_input = QLineEdit()
        self._dir_input.setReadOnly(True)
        self._dir_input.setStyleSheet("background-color: #f0f0f0;")

        self._dir_browse_button = QPushButton("Browse")
        self._dir_browse_button.clicked.connect(self.on_dir_browse_button_clicked)
        dir_layout.addWidget(self._dir_label)
        dir_layout.addWidget(self._dir_input)
        dir_layout.addWidget(self._dir_browse_button)
        main_layout.addLayout(dir_layout)

        # Language selection
        self._source_lang = ""
        self._target_lang = ""

        lang_layout = QHBoxLayout()
        self._source_label = QLabel("Source Language:")
        self._source_dropdown = QComboBox()
        self._source_dropdown.addItems(["(empty)", "English", "Serbian"])
        # Connecting dropdown signal
        self._source_dropdown.currentIndexChanged.connect(self.on_source_language_changed)

        self._target_label = QLabel("Target Language:")
        self._target_dropdown = QComboBox()
        self._target_dropdown.addItems(["(empty)", "English", "Српски"])
        # Connecting dropdown signal
        self._target_dropdown.currentIndexChanged.connect(self.on_target_language_changed)

        lang_layout.addWidget(self._source_label)
        lang_layout.addWidget(self._source_dropdown)
        lang_layout.addWidget(self._target_label)
        lang_layout.addWidget(self._target_dropdown)
        main_layout.addLayout(lang_layout)

        # Translate button
        self._translate_button = QPushButton("Translate")
        self._translate_button.clicked.connect(self.on_translate_button_clicked)
        main_layout.addWidget(self._translate_button)

        # Progress bar
        self._progress_bar = QProgressBar(self)
        self._progress_bar.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self._progress_bar)

        # creating a flag for finished translations
        self._translation_finished = False

    def on_file_browse_button_clicked(self):
        """
        Opens a file dialog to allow the user to select a subtitle file.

        Updates the `_file_input` field with the chosen file path and stores the file path in `_users_path`.
        """

        default_path = os.path.join(os.path.expanduser("~"), "Documents")
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Subtitle File", default_path)
        if file_path:
            self._file_input.setText(file_path)
            self._users_path = file_path

    def on_dir_browse_button_clicked(self):
        """
        Opens a directory dialog to allow the user to select the target directory.

        Updates the `_dir_input` field with the selected directory path.
        """

        default_path = os.path.dirname(self._users_path)
        dir_path = QFileDialog.getExistingDirectory(self, "Select Directory", default_path)
        if dir_path:
            self._dir_input.setText(dir_path)

    def on_source_language_changed(self):
        self._source_lang = self._source_dropdown.currentText()

    def on_target_language_changed(self):
        self._target_lang = self._target_dropdown.currentText()

    def on_translate_button_clicked(self, translation_ready=False):
        """
        Handles the action when the 'Translate' button is clicked.

        If the translation is ready, it shows a completion message.
        If the translation is not yet initiated, it performs validation
        checks on the input fields (file, directory, languages) and starts the translation process if valid.

        Args:
            translation_ready (bool): Indicates if the translation is already completed. Default is False.
        """
        file_input = self._file_input.text()
        dir_input = self._dir_input.text()
        source_lang = self._source_lang
        target_lang = self._target_lang

        # append the file name to the path. This is the full path of the file where we want to
        # save the translated document
        dir_input = PathHandler.create_output_path(file_input, dir_input,target_lang)

        if self._translation_finished is False:
            if not (file_input and dir_input):
                self.show_message_box("You have to choose both file and directory.", title="Missing Input", message_type="warning")
            elif source_lang == "" or target_lang == "":
                self.show_message_box("You have to set both source and target language.", title="Missing Language", message_type="warning")
            elif source_lang == "(empty)" or target_lang == "(empty)":
                self.show_message_box("Source and target languages cannot be (empty).", title="Invalid Language", message_type="warning")
            elif source_lang == target_lang:
                self.show_message_box("Source and target language are same. No need for translation.", title="No need for translation",
                                      message_type="warning")
            else:
                self.show_message_box(
                    f"Do you want to start the translation process?",
                    title="Translation Info", message_type="information")

                payload = TranslationPayload(file_input, dir_input, source_lang, target_lang)

                """
                self._progress_bar.setRange(0, 0)  # Indeterminate mode starts
                """

                # Create a new Thread for processing the subtitle
                self.thread = QThread()
                # Init worker
                self.worker = TranslationWorker(payload)
                # Move worker to the thread
                self.worker.moveToThread(self.thread)
                # Connect signals
                self.thread.started.connect(self.worker.run)
                self.worker.finished.connect(self.thread.quit)
                self.worker.finished.connect(self.worker.deleteLater)
                self.thread.finished.connect(self.thread.deleteLater)
                self.worker.finished.connect(self.on_translation_finished)
                # Start the thread
                self.thread.start()

                # Make buttons unresponsive while the translation is being processed
                self._file_browse_button.setEnabled(False)
                self._dir_browse_button.setEnabled(False)
                self._source_dropdown.setEnabled(False)
                self._target_dropdown.setEnabled(False)
                self._translate_button.setEnabled(False)

    def update_progress_bar(self, percent):
        self._progress_bar.setValue(percent)

    def on_translation_finished(self):
        """
        This method will be called once the translation worker finishes.
        It will stop the progress bar and show a completion message and reset the application state
        """
        # set the flag
        self._translation_finished = True

        self.show_message_box("Translation finished. Your file is ready.\n\n"
                              "The translation was powered by Lingva AI, which provides an automated translation service. "
                              "Please note that the translation might not be perfect, as it can sometimes be a bit rough. "
                              "If you're looking for a more polished translation, we recommend opening the file in your default "
                              "file editor and making any necessary adjustments.", title="Done!",
                              message_type="warning")

        # resetting the variable for the next translation
        self._translate_button.setEnabled(True)

        # Enabling functions of buttons and dropdowns
        self._file_browse_button.setEnabled(True)
        self._dir_browse_button.setEnabled(True)
        self._source_dropdown.setEnabled(True)
        self._target_dropdown.setEnabled(True)
        self._translate_button.setEnabled(True)

    def show_message_box(self, message, title="Message", message_type="information"):
        msg_box = QMessageBox(self)

        if message_type == "information":
            msg_box.setIcon(QMessageBox.Information)
        elif message_type == "warning":
            msg_box.setIcon(QMessageBox.Warning)
        elif message_type == "critical":
            msg_box.setIcon(QMessageBox.Critical)
        else:
            msg_box.setIcon(QMessageBox.NoIcon)

        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.exec_()

    @staticmethod
    def run():
        import sys
        app = QApplication(sys.argv)
        window = SubtitleTranslatorGUI()
        window.show()
        sys.exit(app.exec_())

class PathHandler:
    """
    Generates the output path for the translated subtitle file
    based on the input file path, output directory, and target language.

    Args:
        input_file_path (str): The path of the input subtitle file.
        output_dir_path (str): The directory where the translated file should be saved.
        target_lang (str): The target language for the translation. Default is "empty", which means no language suffix will be added.

    Returns:
        str: The generated output path for the translated file.
    """
    @staticmethod
    def create_output_path(input_file_path, output_dir_path, target_lang="empty"):
        base_name, extension = os.path.splitext(os.path.basename(input_file_path))
        output_path = ""
        if target_lang == "empty":
            output_path = f"{output_dir_path + '/' + base_name + extension}"
            return output_path
        else:
            output_path = f"{output_dir_path + '/' + base_name + '_' + target_lang + extension}"
            return output_path