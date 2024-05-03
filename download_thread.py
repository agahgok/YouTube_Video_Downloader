import os
from PyQt6 import QtCore
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
