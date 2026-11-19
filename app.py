import os
import sys
import subprocess
import tempfile
import time
from PyQt6.QtCore import Qt, QUrl, QPoint, QRectF, pyqtSignal, QMimeData
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont, QLinearGradient, 
    QDrag, QKeySequence, QShortcut
)
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QFileDialog, QMessageBox, QToolTip, QFrame,
    QComboBox
)
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget


TRANSLATIONS = {
    "tr": {
        "title": "Smart Video Trimmer - Drag & Paste",
        "open_video": "📁 Video Aç...",
        "play": "▶ Oynat",
        "pause": "⏸ Duraklat",
        "no_selection": "Seçim: Yok (Timeline'da Sağ Tık / Shift ile Seç)",
        "selection_format": "✂ Seçim: {start} → {end} ({dur})",
        "copy": "📋 Kopyala (Ctrl+C)",
        "copy_tooltip": "Seçili aralığı kopyala. Herhangi bir klasöre Ctrl+V ile yapıştırabilirsin.",
        "save_as": "✂ Farklı Kaydet...",
        "clear": "✕ Temizle",
        "copied_title": "✔ Video parçası kopyalandı!",
        "copied_body": "İstediğin klasöre gidip Ctrl+V ile yapıştırabilirsin.\n({filename})",
        "no_selection_msg": "Lütfen önce timeline üzerinde mouse ile sürükleyerek bir aralık belirleyin.",
        "no_selection_title": "Seçim Yok",
        "error_title": "Hata",
        "error_cut": "Video parçası kesilirken bir sorun oluştu.",
        "save_dialog_title": "Parçayı Farklı Kaydet",
        "save_success_title": "Başarılı",
        "save_success_msg": "Yeni video parçası başarıyla kaydedildi:\n{path}",
        "video_filter": "Video Dosyaları (*.mp4 *.mkv *.avi *.mov *.wmv *.flv *.webm);;Tüm Dosyalar (*.*)"
    },
    "en": {
        "title": "Smart Video Trimmer - Drag & Paste",
        "open_video": "📁 Open Video...",
        "play": "▶ Play",
        "pause": "⏸ Pause",
        "no_selection": "Selection: None (Right Click / Shift to Select on Timeline)",
        "selection_format": "✂ Selection: {start} → {end} ({dur})",
        "copy": "📋 Copy (Ctrl+C)",
        "copy_tooltip": "Copy selected range. You can paste it into any folder with Ctrl+V.",
        "save_as": "✂ Save As...",
        "clear": "✕ Clear",
        "copied_title": "✔ Video clip copied!",
        "copied_body": "Go to any folder and paste with Ctrl+V.\n({filename})",
        "no_selection_msg": "Please select a range on the timeline first using mouse drag.",
        "no_selection_title": "No Selection",
        "error_title": "Error",
        "error_cut": "An error occurred while cutting the video clip.",
        "save_dialog_title": "Save Clip As",
        "save_success_title": "Success",
        "save_success_msg": "Video clip saved successfully:\n{path}",
        "video_filter": "Video Files (*.mp4 *.mkv *.avi *.mov *.wmv *.flv *.webm);;All Files (*.*)"
    }
}


def format_time(ms: int) -> str:
    """Milisaniyeyi mm:ss.zzz formatına dönüştürür."""
    if ms < 0:
        ms = 0
    total_seconds = ms / 1000.0
    minutes = int(total_seconds // 60)
    seconds = int(total_seconds % 60)
    millis = int((total_seconds - int(total_seconds)) * 1000)
    return f"{minutes:02d}:{seconds:02d}.{millis:03d}"


class VideoTrimWorker:
    """FFmpeg ile kayıpsız (stream copy) video kesimi yapar."""
    @staticmethod
    def trim_video(input_path: str, start_ms: int, end_ms: int, output_path: str) -> bool:
        start_sec = max(0, start_ms / 1000.0)
        duration_sec = max(0.05, (end_ms - start_ms) / 1000.0)
        
        cmd = [
            "ffmpeg",
            "-y",
            "-ss", f"{start_sec:.3f}",
            "-i", input_path,
            "-t", f"{duration_sec:.3f}",
            "-c", "copy",
            "-avoid_negative_ts", "make_zero",
            output_path
        ]
        
        try:
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                
            res = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                startupinfo=startupinfo
            )
            return res.returncode == 0
        except Exception as e:
            print(f"Trim error: {e}")
            return False


class TimelineSlider(QWidget):
    """Video timeline bileşeni."""
    seek_requested = pyqtSignal(int)
    range_changed = pyqtSignal(int, int)
    drag_started = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setFixedHeight(50)
        
        self.duration = 0
        self.position = 0
        self.start_cut = -1
        self.end_cut = -1
        
        self.dragging_playhead = False
        self.dragging_start_handle = False
        self.dragging_end_handle = False
        self.creating_range = False
        self.is_drag_source_candidate = False
        self.drag_start_pos = QPoint()
        self.hover_pos = -1

    def set_duration(self, duration_ms: int):
        self.duration = max(0, duration_ms)
        self.start_cut = -1
        self.end_cut = -1
        self.update()

    def set_position(self, pos_ms: int):
        if not self.dragging_playhead:
            self.position = pos_ms
            self.update()

    def set_range(self, start_ms: int, end_ms: int):
        if self.duration <= 0:
            return
        start_ms = max(0, min(start_ms, self.duration))
        end_ms = max(0, min(end_ms, self.duration))
        if start_ms > end_ms:
            start_ms, end_ms = end_ms, start_ms
        self.start_cut = start_ms
        self.end_cut = end_ms
        self.range_changed.emit(self.start_cut, self.end_cut)
        self.update()

    def clear_range(self):
        self.start_cut = -1
        self.end_cut = -1
        self.range_changed.emit(-1, -1)
        self.update()

    def x_to_ms(self, x: float) -> int:
        if self.width() <= 0 or self.duration <= 0:
            return 0
        ratio = max(0.0, min(1.0, x / self.width()))
        return int(ratio * self.duration)

    def ms_to_x(self, ms: int) -> float:
        if self.duration <= 0:
            return 0.0
        return (ms / self.duration) * self.width()

    def has_valid_selection(self) -> bool:
        return self.start_cut >= 0 and self.end_cut >= 0 and (self.end_cut - self.start_cut) >= 100

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        bar_y = 14
        bar_h = 22

        # 1. Timeline Arka Planı
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(30, 32, 40))
        painter.drawRoundedRect(0, bar_y, w, bar_h, 5, 5)

        if self.duration <= 0:
            return

        # 2. Oynatılan İlerleme (Mavi)
        play_x = self.ms_to_x(self.position)
        prog_grad = QLinearGradient(0, 0, play_x, 0)
        prog_grad.setColorAt(0, QColor(0, 150, 255, 160))
        prog_grad.setColorAt(1, QColor(0, 120, 215, 220))
        painter.setBrush(prog_grad)
        painter.drawRoundedRect(0, bar_y, int(play_x), bar_h, 5, 5)

        # 3. Seçilen Kesim Aralığı (Sarı Alan)
        if self.has_valid_selection():
            s_x = self.ms_to_x(self.start_cut)
            e_x = self.ms_to_x(self.end_cut)
            sel_w = max(2.0, e_x - s_x)

            painter.setBrush(QColor(255, 180, 0, 130))
            painter.setPen(QPen(QColor(255, 193, 7), 2))
            painter.drawRect(int(s_x), bar_y, int(sel_w), bar_h)

            handle_w = 8
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(255, 215, 0))
            painter.drawRoundedRect(int(s_x - handle_w / 2), bar_y - 3, handle_w, bar_h + 6, 3, 3)
            painter.drawRoundedRect(int(e_x - handle_w / 2), bar_y - 3, handle_w, bar_h + 6, 3, 3)

            dur_txt = f"✂ {format_time(self.end_cut - self.start_cut)}"
            painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            painter.setPen(QColor(255, 235, 59))
            painter.drawText(int(s_x + 6), bar_y - 3, dur_txt)

        # 4. Hover Çizgisi
        if self.hover_pos >= 0:
            painter.setPen(QPen(QColor(255, 255, 255, 100), 1, Qt.PenStyle.DashLine))
            painter.drawLine(self.hover_pos, bar_y - 3, self.hover_pos, bar_y + bar_h + 3)

        # 5. Oynatma Kafası (Playhead)
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.drawLine(int(play_x), bar_y - 4, int(play_x), bar_y + bar_h + 4)
        painter.setBrush(QColor(255, 255, 255))
        painter.drawEllipse(int(play_x - 5), bar_y + bar_h // 2 - 5, 10, 10)

    def mousePressEvent(self, event):
        if self.duration <= 0:
            return

        x = event.position().x()
        click_ms = self.x_to_ms(x)

        if event.button() == Qt.MouseButton.LeftButton:
            if self.has_valid_selection():
                s_x = self.ms_to_x(self.start_cut)
                e_x = self.ms_to_x(self.end_cut)
                if abs(x - s_x) <= 8:
                    self.dragging_start_handle = True
                    return
                elif abs(x - e_x) <= 8:
                    self.dragging_end_handle = True
                    return
                elif s_x < x < e_x:
                    self.is_drag_source_candidate = True
                    self.drag_start_pos = event.position().toPoint()
                    return

            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                if self.start_cut < 0:
                    self.start_cut = click_ms
                self.end_cut = click_ms
                self.creating_range = True
                self.range_changed.emit(self.start_cut, self.end_cut)
                self.update()
                return

            self.dragging_playhead = True
            self.position = click_ms
            self.seek_requested.emit(click_ms)
            self.update()

        elif event.button() == Qt.MouseButton.RightButton:
            self.start_cut = click_ms
            self.end_cut = click_ms
            self.creating_range = True
            self.range_changed.emit(self.start_cut, self.end_cut)
            self.update()

    def mouseMoveEvent(self, event):
        x = event.position().x()
        self.hover_pos = int(x)
        current_ms = self.x_to_ms(x)

        if self.has_valid_selection():
            s_x = self.ms_to_x(self.start_cut)
            e_x = self.ms_to_x(self.end_cut)
            if abs(x - s_x) <= 8 or abs(x - e_x) <= 8:
                self.setCursor(Qt.CursorShape.SizeHorCursor)
            elif s_x < x < e_x:
                self.setCursor(Qt.CursorShape.OpenHandCursor)
            else:
                self.setCursor(Qt.CursorShape.PointingHandCursor)
        else:
            self.setCursor(Qt.CursorShape.PointingHandCursor)

        if self.is_drag_source_candidate:
            dist = (event.position().toPoint() - self.drag_start_pos).manhattanLength()
            if dist >= QApplication.startDragDistance():
                self.is_drag_source_candidate = False
                self.setCursor(Qt.CursorShape.ClosedHandCursor)
                self.drag_started.emit()
                return

        if self.creating_range:
            self.end_cut = current_ms
            self.range_changed.emit(min(self.start_cut, self.end_cut), max(self.start_cut, self.end_cut))
            self.update()
        elif self.dragging_start_handle:
            self.start_cut = min(current_ms, self.end_cut - 100)
            self.range_changed.emit(self.start_cut, self.end_cut)
            self.update()
        elif self.dragging_end_handle:
            self.end_cut = max(current_ms, self.start_cut + 100)
            self.range_changed.emit(self.start_cut, self.end_cut)
            self.update()
        elif self.dragging_playhead:
            self.position = current_ms
            self.seek_requested.emit(current_ms)
            self.update()
        else:
            self.update()

    def mouseReleaseEvent(self, event):
        self.is_drag_source_candidate = False
        self.dragging_playhead = False
        self.dragging_start_handle = False
        self.dragging_end_handle = False
        if self.creating_range:
            self.creating_range = False
            if self.start_cut > self.end_cut:
                self.start_cut, self.end_cut = self.end_cut, self.start_cut
            if abs(self.end_cut - self.start_cut) < 100:
                self.clear_range()
            else:
                self.range_changed.emit(self.start_cut, self.end_cut)
            self.update()

    def leaveEvent(self, event):
        self.hover_pos = -1
        self.update()


class MainWindow(QMainWindow):
    """Ana Uygulama Penceresi"""
    def __init__(self):
        super().__init__()
        self.current_lang = "tr"
        self.setWindowTitle(self.t("title"))
        self.resize(1050, 680)
        self.setMinimumSize(700, 480)
        self.current_video_path = ""
        self.temp_cut_files = []

        self.setStyleSheet("""
            QMainWindow {
                background-color: #111216;
            }
            QFrame#controlBar {
                background-color: #1a1c23;
                border-top: 1px solid #2d313d;
            }
            QPushButton {
                background-color: #2b2e3b;
                color: #ffffff;
                border: 1px solid #3d4253;
                border-radius: 6px;
                padding: 7px 15px;
                font-family: 'Segoe UI';
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #383d4e;
                border-color: #535a70;
            }
            QPushButton:pressed {
                background-color: #0984e3;
            }
            QPushButton#btnSave {
                background-color: #d35400;
                border-color: #e67e22;
            }
            QPushButton#btnSave:hover {
                background-color: #e67e22;
            }
            QLabel {
                color: #dfe4ea;
                font-family: 'Consolas', 'Segoe UI';
                font-size: 13px;
            }
            QComboBox {
                background-color: #2b2e3b;
                color: #ffffff;
                border: 1px solid #3d4253;
                border-radius: 6px;
                padding: 5px 10px;
                font-family: 'Segoe UI';
                font-size: 12px;
                font-weight: bold;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #1a1c23;
                color: white;
                selection-background-color: #0984e3;
            }
        """)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Video Oynatıcı
        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.player.setAudioOutput(self.audio_output)

        self.video_widget = QVideoWidget(self)
        main_layout.addWidget(self.video_widget, stretch=1)
        self.player.setVideoOutput(self.video_widget)

        # 2. Alt Kontrol Paneli
        self.control_bar = QFrame(self)
        self.control_bar.setObjectName("controlBar")
        bar_layout = QVBoxLayout(self.control_bar)
        bar_layout.setContentsMargins(16, 10, 16, 12)
        bar_layout.setSpacing(8)

        # Timeline Slider
        self.timeline = TimelineSlider(self.control_bar)
        self.timeline.seek_requested.connect(self.on_seek_requested)
        self.timeline.range_changed.connect(self.on_range_changed)
        self.timeline.drag_started.connect(self.start_explorer_drag)
        bar_layout.addWidget(self.timeline)

        # Butonlar satırı
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.btn_open = QPushButton(self.t("open_video"))
        self.btn_open.clicked.connect(self.open_file_dialog)
        btn_layout.addWidget(self.btn_open)

        self.btn_play = QPushButton(self.t("play"))
        self.btn_play.clicked.connect(self.toggle_play)
        btn_layout.addWidget(self.btn_play)

        self.lbl_time = QLabel("00:00.000 / 00:00.000")
        btn_layout.addWidget(self.lbl_time)

        btn_layout.addStretch()

        self.lbl_selection = QLabel(self.t("no_selection"))
        self.lbl_selection.setStyleSheet("color: #ffd32a; font-weight: bold;")
        btn_layout.addWidget(self.lbl_selection)

        self.btn_copy = QPushButton(self.t("copy"))
        self.btn_copy.setToolTip(self.t("copy_tooltip"))
        self.btn_copy.clicked.connect(self.copy_selected_to_clipboard)
        btn_layout.addWidget(self.btn_copy)

        self.btn_save = QPushButton(self.t("save_as"))
        self.btn_save.setObjectName("btnSave")
        self.btn_save.clicked.connect(self.save_selection_as_file)
        btn_layout.addWidget(self.btn_save)

        self.btn_clear = QPushButton(self.t("clear"))
        self.btn_clear.clicked.connect(self.timeline.clear_range)
        btn_layout.addWidget(self.btn_clear)

        # Dil Değiştirme Butonu (Sadece bayrak: Türkçe iken 🇬🇧, İngilizce iken 🇹🇷)
        self.btn_lang = QPushButton("🇬🇧")
        self.btn_lang.setToolTip("Switch to English")
        self.btn_lang.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_lang.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                padding: 4px 10px;
                background-color: #2b2e3b;
                border: 1px solid #3d4253;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #383d4e;
                border-color: #0984e3;
            }
        """)
        self.btn_lang.clicked.connect(self.toggle_language)
        btn_layout.addWidget(self.btn_lang)

        bar_layout.addLayout(btn_layout)
        main_layout.addWidget(self.control_bar, stretch=0)

        # Sinyaller
        self.player.positionChanged.connect(self.on_position_changed)
        self.player.durationChanged.connect(self.on_duration_changed)

        # Kısayollar & Sürükle Bırak
        self.setAcceptDrops(True)
        self.video_widget.setAcceptDrops(True)

        QShortcut(QKeySequence("Ctrl+O"), self).activated.connect(self.open_file_dialog)
        QShortcut(QKeySequence.StandardKey.Copy, self).activated.connect(self.copy_selected_to_clipboard)
        QShortcut(QKeySequence(Qt.Key.Key_Space), self).activated.connect(self.toggle_play)

    def t(self, key: str) -> str:
        """Geçerli dildeki çeviri metnini getirir."""
        return TRANSLATIONS.get(self.current_lang, TRANSLATIONS["tr"]).get(key, key)

    def toggle_language(self):
        """Dili Türkçe <-> İngilizce arasında değiştirir ve karşı dilin bayrağını gösterir."""
        if self.current_lang == "tr":
            self.current_lang = "en"
            self.btn_lang.setText("🇹🇷")
            self.btn_lang.setToolTip("Türkçe'ye Geç")
        else:
            self.current_lang = "tr"
            self.btn_lang.setText("🇬🇧")
            self.btn_lang.setToolTip("Switch to English")
        self.update_ui_texts()

    def update_ui_texts(self):
        title = self.t("title")
        if self.current_video_path:
            title = f"{title} - {os.path.basename(self.current_video_path)}"
        self.setWindowTitle(title)
        
        self.btn_open.setText(self.t("open_video"))
        
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.btn_play.setText(self.t("pause"))
        else:
            self.btn_play.setText(self.t("play"))

        self.btn_copy.setText(self.t("copy"))
        self.btn_copy.setToolTip(self.t("copy_tooltip"))
        self.btn_save.setText(self.t("save_as"))
        self.btn_clear.setText(self.t("clear"))

        # Seçim etiketini güncelle
        start_ms, end_ms = self.get_selected_range()
        if start_ms is not None and end_ms is not None and end_ms > start_ms:
            dur = end_ms - start_ms
            txt = self.t("selection_format").format(
                start=format_time(start_ms),
                end=format_time(end_ms),
                dur=format_time(dur)
            )
            self.lbl_selection.setText(txt)
        else:
            self.lbl_selection.setText(self.t("no_selection"))

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            if os.path.isfile(path):
                self.load_video(path)
                event.acceptProposedAction()

    def open_file_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            self.t("open_video"),
            "",
            self.t("video_filter")
        )
        if file_path:
            self.load_video(file_path)

    def load_video(self, file_path: str):
        self.current_video_path = os.path.abspath(file_path)
        self.setWindowTitle(f"{self.t('title')} - {os.path.basename(file_path)}")
        self.player.setSource(QUrl.fromLocalFile(self.current_video_path))
        self.player.play()
        self.btn_play.setText(self.t("pause"))
        self.timeline.clear_range()

    def toggle_play(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
            self.btn_play.setText(self.t("play"))
        else:
            self.player.play()
            self.btn_play.setText(self.t("pause"))

    def on_seek_requested(self, ms: int):
        self.player.setPosition(ms)

    def on_position_changed(self, pos_ms: int):
        self.timeline.set_position(pos_ms)
        dur_ms = self.player.duration()
        self.lbl_time.setText(f"{format_time(pos_ms)} / {format_time(dur_ms)}")

    def on_duration_changed(self, dur_ms: int):
        self.timeline.set_duration(dur_ms)
        pos_ms = self.player.position()
        self.lbl_time.setText(f"{format_time(pos_ms)} / {format_time(dur_ms)}")

    def on_range_changed(self, start_ms: int, end_ms: int):
        if start_ms >= 0 and end_ms >= 0 and end_ms > start_ms:
            dur = end_ms - start_ms
            txt = self.t("selection_format").format(
                start=format_time(start_ms),
                end=format_time(end_ms),
                dur=format_time(dur)
            )
            self.lbl_selection.setText(txt)
        else:
            self.lbl_selection.setText(self.t("no_selection"))

    def get_selected_range(self):
        if not self.timeline.has_valid_selection():
            return None, None
        return self.timeline.start_cut, self.timeline.end_cut

    def prepare_cut_file(self, target_path: str = None) -> str:
        start_ms, end_ms = self.get_selected_range()
        if start_ms is None or not self.current_video_path:
            return ""

        if not target_path:
            base_name = os.path.splitext(os.path.basename(self.current_video_path))[0]
            ext = os.path.splitext(self.current_video_path)[1] or ".mp4"
            timestamp_str = f"clip_{int(start_ms/1000)}s_{int(end_ms/1000)}s_{int(time.time())}"
            temp_dir = tempfile.gettempdir()
            target_path = os.path.join(temp_dir, f"{base_name}_{timestamp_str}{ext}")
            self.temp_cut_files.append(target_path)

        success = VideoTrimWorker.trim_video(self.current_video_path, start_ms, end_ms, target_path)
        return target_path if success else ""

    def copy_selected_to_clipboard(self):
        start_ms, end_ms = self.get_selected_range()
        if start_ms is None:
            QMessageBox.information(
                self, 
                self.t("no_selection_title"), 
                self.t("no_selection_msg")
            )
            return

        cut_file = self.prepare_cut_file()
        if cut_file and os.path.exists(cut_file):
            mime = QMimeData()
            mime.setUrls([QUrl.fromLocalFile(cut_file)])
            QApplication.clipboard().setMimeData(mime)
            
            body = self.t("copied_body").format(filename=os.path.basename(cut_file))
            QToolTip.showText(
                self.cursor().pos(),
                f"{self.t('copied_title')}\n{body}",
                self,
                QRectF(0, 0, 10, 10).toRect(),
                3500
            )
        else:
            QMessageBox.warning(self, self.t("error_title"), self.t("error_cut"))

    def start_explorer_drag(self):
        start_ms, end_ms = self.get_selected_range()
        if start_ms is None:
            return

        cut_file = self.prepare_cut_file()
        if not cut_file or not os.path.exists(cut_file):
            return

        drag = QDrag(self.timeline)
        mime = QMimeData()
        mime.setUrls([QUrl.fromLocalFile(cut_file)])
        drag.setMimeData(mime)
        drag.exec(Qt.DropAction.CopyAction)

    def save_selection_as_file(self):
        start_ms, end_ms = self.get_selected_range()
        if start_ms is None:
            QMessageBox.information(
                self, 
                self.t("no_selection_title"), 
                self.t("no_selection_msg")
            )
            return

        base_dir = os.path.dirname(self.current_video_path)
        base_name, ext = os.path.splitext(os.path.basename(self.current_video_path))
        default_out = os.path.join(base_dir, f"{base_name}_cut_{int(start_ms/1000)}s_{int(end_ms/1000)}s{ext}")

        out_path, _ = QFileDialog.getSaveFileName(
            self,
            self.t("save_dialog_title"),
            default_out,
            f"Video (*{ext});;All (*.*)"
        )
        if out_path:
            res = self.prepare_cut_file(out_path)
            if res:
                QMessageBox.information(
                    self, 
                    self.t("save_success_title"), 
                    self.t("save_success_msg").format(path=out_path)
                )
            else:
                QMessageBox.critical(self, self.t("error_title"), self.t("error_cut"))


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
        window.load_video(sys.argv[1])
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
