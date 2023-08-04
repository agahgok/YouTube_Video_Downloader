import sys
import os
import requests
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QFileDialog

from pytube import YouTube


class DownloadThread(QtCore.QThread):
    progress_updated = QtCore.pyqtSignal(float)

    def __init__(self, link, save_path, quality):
        super().__init__()
        self.link = link
        self.save_path = save_path
        self.quality = quality

    def run(self):
        try:
            yt = YouTube(self.link, on_progress_callback=self.on_progress)
            stream = self.get_stream_by_quality(yt)

            stream.download(output_path=os.path.dirname(self.save_path), filename=os.path.basename(self.save_path))
            self.progress_updated.emit(100.0)
        except Exception as e:
            self.progress_updated.emit(-1.0)

    def get_stream_by_quality(self, yt):
        if self.quality == 1:
            return yt.streams.get_lowest_resolution()
        elif self.quality == 2:
            return yt.streams.get_highest_resolution()
        else:
            return yt.streams.filter(progressive=True).first()

    def on_progress(self, stream, chunk, bytes_remaining):
        total_size = stream.filesize
        bytes_downloaded = total_size - bytes_remaining
        percentage = (bytes_downloaded / total_size) * 100
        self.progress_updated.emit(percentage)


class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("YouTube Video Downloader")
        self.setGeometry(100, 100, 960, 540)

       
        self.link_input = QtWidgets.QTextEdit()
        self.link_input.setMaximumHeight(70)  
        self.link_input.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)  

        self.filename_input = QtWidgets.QLineEdit()
        self.download_button = QtWidgets.QPushButton("Download")

      
        self.status_frame = QtWidgets.QFrame()
        self.status_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.status_frame.setStyleSheet("background-color: black;")
        self.status_frame.setMaximumHeight(150)
        self.status_frame.setMinimumHeight(150) 

        self.info_label = QtWidgets.QLabel(self.status_frame)
        self.info_label.setAlignment(QtCore.Qt.AlignCenter)  
        self.info_label.setStyleSheet("color: green; font-weight: bold; font-size: 18px;")

        self.progress_bar = QtWidgets.QProgressBar(self.status_frame)
        self.progress_bar.setStyleSheet("QProgressBar {border: 2px solid grey; border-radius: 5px; padding: 1px}"
                                        "QProgressBar::chunk {background-color: green;}")
        self.progress_bar.setTextVisible(False)  
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)

        self.status_layout = QtWidgets.QVBoxLayout(self.status_frame)
        self.status_layout.addWidget(self.info_label)
        self.status_layout.addWidget(self.progress_bar)

        self.low_quality_button = QtWidgets.QRadioButton("Low")
        self.medium_quality_button = QtWidgets.QRadioButton("Medium")
        self.high_quality_button = QtWidgets.QRadioButton("High")

        self.quality_group = QtWidgets.QButtonGroup()
        self.quality_group.addButton(self.low_quality_button, 1)
        self.quality_group.addButton(self.medium_quality_button, 2)
        self.quality_group.addButton(self.high_quality_button, 3)

        self.medium_quality_button.setChecked(True)

        self.download_button.clicked.connect(self.download_video)

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(self.link_input)
        self.layout.addWidget(self.filename_input)
        self.layout.addWidget(self.low_quality_button)
        self.layout.addWidget(self.medium_quality_button)
        self.layout.addWidget(self.high_quality_button)
        self.layout.addWidget(self.download_button)
        self.layout.addWidget(self.status_frame)

        self.link_input.setPlaceholderText("Please Enter Link")
        self.filename_input.setPlaceholderText("Please Enter Video Name")

        self.setLayout(self.layout)

        self.download_thread = None

    def download_progress_updated(self, percentage):
        if percentage < 0:
            self.info_label.setText("An error occurred during download.")
        elif percentage < 100:
            self.info_label.setText(f"Downloading {int(percentage)}%")
            self.progress_bar.setValue(int(percentage))
        else:
            self.info_label.setText("Downloaded.")
            self.progress_bar.setValue(100)
            self.download_button.setEnabled(True)

    def download_video(self):
        if self.download_thread and self.download_thread.isRunning():
            return

        link = self.link_input.toPlainText()
        filename = self.filename_input.text()

        if not link:
            self.info_label.setText("Please enter a valid YouTube link.")
            return

        if not filename:
            self.info_label.setText("Please enter a filename.")
            return

        quality = self.quality_group.checkedId()
        if quality not in (1, 2, 3):
            self.info_label.setText("Please select a quality.")
            return

        save_path, _ = QFileDialog.getSaveFileName(self, "Save Video", f"{filename}.mp4", "Video Files (*.mp4)")

        if not save_path:
            self.info_label.setText("Download canceled.")
            return

        try:
            try:
                requests.get('http://www.google.com', timeout=5)
            except requests.exceptions.RequestException:
                self.info_label.setText("Connection Problem.")
                return

            self.download_button.setEnabled(False)
            self.info_label.setText("Download Starting...")
            self.progress_bar.setValue(0)

            self.download_thread = DownloadThread(link, save_path, quality)
            self.download_thread.progress_updated.connect(self.download_progress_updated)
            self.download_thread.start()

        except Exception as e:
            self.info_label.setText(f"An error occurred: {str(e)}")
            self.download_button.setEnabled(True)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    main_window = MainWindow()
    main_window.show()

    sys.exit(app.exec_())
