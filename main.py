import logging
import os

from PySide6.QtCore import Slot, QObject, Signal, QThread
from PySide6.QtWidgets import (QApplication, QLabel, QPushButton, QVBoxLayout, QWidget, QHBoxLayout, QLineEdit,
                               QGroupBox, QFileDialog, QCheckBox, QPlainTextEdit, QGridLayout)
from scrapy.crawler import CrawlerProcess
from scrapy.utils.log import configure_logging
from scrapy.utils.project import get_project_settings


class LogSignal(QObject):
    signal = Signal(str)
    error = Signal(str)


class QtLogHandler(logging.Handler):

    def __init__(self):
        logging.Handler.__init__(self)

    log = LogSignal()

    def emit(self, log_record: logging.LogRecord):
        message = self.format(log_record)
        if log_record.levelno >= logging.ERROR:
            self.log.error.emit(message)
        else:
            self.log.signal.emit(message)


class Window(QWidget):

    def __init__(self):
        super().__init__()
        self.setStyleSheet('QGroupBox { font-size: 14px; }')
        self.setWindowTitle('Store Scrap')
        self.setMinimumWidth(500)
        main_layout = QVBoxLayout(self)

        main_layout.addWidget(QLabel('<h3>Product data scraping</h3>'))

        brands_row = QHBoxLayout()
        main_layout.addLayout(brands_row)

        self.filepath_section = QGroupBox('Save results to')
        main_layout.addWidget(self.filepath_section)
        filepath_row = QHBoxLayout(self.filepath_section)
        self.file_path_input = QLineEdit()
        self.file_path_input.setPlaceholderText('Select a file to save the results to...')
        self.file_path_input.textChanged.connect(self.save_path_is_valid)
        filepath_row.addWidget(self.file_path_input)
        browse_button = QPushButton('Browse')
        browse_button.clicked.connect(self.open_save_dialog)
        filepath_row.addWidget(browse_button)

        self.websites_config = {
            'Extra': {
                'Hisense': True,
                'Samsung': True,
                'Admiral': True,
            },
            'Almanea': {
                'Hisense': True,
                'Samsung': True,
            },
            'Carrefour KSA': {
                'Hisense': True,
                'Samsung': True,
                'Admiral': True,
                'Konka': True,
            }
        }

        self.websites_section = QGroupBox('Websites')
        websites_layout = QGridLayout(self.websites_section)
        main_layout.addWidget(self.websites_section)
        for i, name in enumerate(self.websites_config.keys()):
            website_section = QGroupBox(name)
            website_section.setCheckable(True)
            website_section.setChecked(True)
            website_section.toggled.connect(self.website_toggled)
            website_layout = QHBoxLayout(website_section)
            websites_layout.addWidget(website_section, i // 2, i % 2)
            for brand, checked in self.websites_config[name].items():
                checkbox = QCheckBox()
                checkbox.setText(brand)
                checkbox.setChecked(checked)
                checkbox.stateChanged.connect(self.category_state_changed)
                website_layout.addWidget(checkbox)

        self.run_button = QPushButton('Run')
        self.run_button.clicked.connect(self.run_spiders)
        self.run_button.setEnabled(False)
        main_layout.addWidget(self.run_button)

        logs = QGroupBox('Logs')
        logs_layout = QVBoxLayout(logs)
        self.logs_display = QPlainTextEdit()
        logs_layout.addWidget(self.logs_display)
        self.logs_display.setMinimumHeight(300)
        self.logs_display.setReadOnly(True)
        self.logs_display.setPlaceholderText('Logs will be displayed here...')
        main_layout.addWidget(logs)

        log_handler = QtLogHandler()
        log_handler.log.signal.connect(self.logs_display.appendPlainText)
        log_handler.log.error.connect(self.show_error)
        configure_logging(install_root_handler=False)
        logging.getLogger().addHandler(log_handler)

        self.crawling_thread = None

    @Slot(str)
    def show_error(self, message):
        self.logs_display.appendHtml(
            f'<pre style="color: red;">{message}</pre>'
        )

    @Slot(bool)
    def website_toggled(self, state):
        groupbox = self.sender()
        for checkbox in groupbox.findChildren(QCheckBox):
            checkbox.setChecked(state)
        self.run_button.setDisabled(
            all(not checkbox.isChecked() for checkbox in self.websites_section.findChildren(QCheckBox))
        )
        self.save_path_is_valid()

    @Slot(bool)
    def category_state_changed(self, state):
        checkbox = self.sender()
        website = checkbox.parentWidget().title()
        category = checkbox.text()
        self.websites_config[website][category] = state

    @Slot()
    def save_path_is_valid(self):
        file_input = self.file_path_input.text()
        file_dir = os.path.dirname(os.path.abspath(file_input))
        self.run_button.setEnabled(file_input != '' and os.path.isdir(file_dir) and os.access(file_dir, os.W_OK))

    @Slot()
    def open_save_dialog(self):
        home_dir = os.path.expanduser('~')
        save_file_path, _ = QFileDialog.getSaveFileName(self, 'Save results to', home_dir, 'Excel files (*.xlsx)')
        if save_file_path:
            self.file_path_input.setText(save_file_path)

    @Slot()
    def disable_ui(self):
        self.filepath_section.setEnabled(False)
        self.websites_section.setEnabled(False)
        self.run_button.setEnabled(False)
        self.logs_display.clear()

    @Slot()
    def enable_ui(self):
        self.filepath_section.setEnabled(True)
        self.websites_section.setEnabled(True)
        self.run_button.setEnabled(True)

    @Slot()
    def run_spiders(self):
        self.disable_ui()
        file_path = self.file_path_input.text()
        self.crawling_thread = CrawlingThread(self.websites_config, file_path)
        self.crawling_thread.start()
        self.crawling_thread.finished.connect(self.enable_ui)


class CrawlingThread(QThread):

    def __init__(self, website_configs, file_path):
        super().__init__()
        self.websites_config = website_configs
        self.file_path = file_path
        self.settings = get_project_settings()
        self.settings.set('EXCEL_FILE_PATH', file_path)

    def run(self):
        try:
            process = CrawlerProcess(self.settings)
            for website, categories in self.websites_config.items():
                enabled_brands = [category for category, enabled in categories.items() if enabled]
                if enabled_brands:
                    process.crawl(website.lower().replace(' ', '_'), brands=enabled_brands)
            process.start(install_signal_handlers=False)
        except Exception as e:
            logging.error(str(e))


def run():
    import sys
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    app.exec()


if __name__ == '__main__':
    run()
