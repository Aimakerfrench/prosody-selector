"""
واجهة رسومية احترافية للمختار العروضي
تصميم كلاسيكي بألوان رمادية - مستوحاة من main_window
نظام تحليل عروضي للشعر العربي

المعمار:
- PyQt6 للواجهة الرسومية
- معالجة متعددة الخيوط لعدم تجميد الواجهة
- تصميم كلاسيكي أنيق بألوان رمادية
- دعم كامل للنصوص العربية RTL

المطور: نظام المختار العروضي
الإصدار: 0.4
"""

import sys
import os
import sqlite3
import webbrowser
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QLabel, QSplitter,
    QListWidget, QListWidgetItem, QMessageBox,
    QApplication, QProgressBar, QGroupBox, QLineEdit
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPainter, QTextCursor

# استيراد المكونات الأساسية
from data import load_replacements_from_db
from core import PoetryMatcher
from settings import REPLACEMENTS_DB, DB_PATH, WEIGHTS_DB, TAFEELAT_DB
from app import ResultProcessor


class AnalysisWorker(QThread):
    """
    عامل معالجة في خيط منفصل لتحليل الأبيات الشعرية
    يمنع تجميد الواجهة أثناء المعالجة
    """
    finished = pyqtSignal(str, str, dict)  # original, processed, results
    error = pyqtSignal(str)
    progress = pyqtSignal(str)
    
    def __init__(self, poem: str, matcher: PoetryMatcher):
        super().__init__()
        self.poem = poem
        self.matcher = matcher
        
    def run(self):
        """تنفيذ التحليل العروضي"""
        try:
            self.progress.emit("جارٍ تحليل البيت...")
            processed, full = self.matcher.process_poem(self.poem)
            self.progress.emit("اكتمل التحليل")
            self.finished.emit(self.poem, processed, full)
        except Exception as e:
            self.error.emit(f"خطأ في التحليل: {str(e)}")


class DotsHandle(QWidget):
    """
    Widget مخصص لرسم 3 نقاط في المنتصف (مثل main_window)
    يستخدم كفاصل بصري بين الأعمدة
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(20)
        self.setMaximumWidth(20)
    
    def paintEvent(self, event):
        """رسم النقاط الثلاث"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # لون النقاط (نفس main_window)
        painter.setBrush(QColor("#888888"))
        painter.setPen(Qt.PenStyle.NoPen)
        
        # حساب المواضع (3 نقاط في المنتصف)
        width = self.width()
        height = self.height()
        dot_size = 4
        spacing = 6
        total_height = (dot_size * 3) + (spacing * 2)
        start_y = (height - total_height) / 2
        
        # رسم 3 نقاط
        for i in range(3):
            y = start_y + (i * (dot_size + spacing)) + (dot_size / 2)
            painter.drawEllipse(
                int(width / 2 - dot_size / 2), 
                int(y - dot_size / 2), 
                dot_size, 
                dot_size
            )


class ProsodyMainWindow(QMainWindow):
    """
    النافذة الرئيسية للمختار العروضي
    
    المعمار:
    - 3 أعمدة: المدخلات | النتائج | السجل
    - شريط أزرار علوي
    - معالجة متعددة الخيوط
    - تصميم كلاسيكي رمادي
    """
    
    def __init__(self):
        super().__init__()
        self.base_dir = Path(__file__).parent
        self.matcher = None
        self.processor = None
        self.analysis_worker = None
        self.results_history = []  # سجل النتائج
        self.current_result_index = -1
        
        # بناء الواجهة أولاً
        self.init_ui()
        
        # تحميل البيانات
        self.init_data()
        
        # رسالة ترحيب
        self.log_message("مرحباً بك في المختار العروضي")
        self.log_message("أدخل بيتاً شعرياً (*** بين الشطرين) ثم اضغط 'تحليل'")
    
    def init_data(self):
        """تحميل قواعد البيانات والمطابق"""
        try:
            # تحميل الاستبدالات
            reps = load_replacements_from_db(REPLACEMENTS_DB)
            
            # إنشاء المطابق
            self.matcher = PoetryMatcher(DB_PATH, reps)
            
            # إنشاء معالج النتائج
            output_file = self.base_dir / "وزن_البيت.html"
            self.processor = ResultProcessor(
                WEIGHTS_DB, 
                TAFEELAT_DB, 
                str(output_file)
            )
            
            if hasattr(self, 'log_list'):
                self.log_message("✅ تم تحميل قواعد البيانات بنجاح")
            
        except Exception as e:
            error_msg = f"فشل تحميل قواعد البيانات:\n{str(e)}"
            if hasattr(self, 'log_list'):
                self.log_message(f"❌ {error_msg}")
            QMessageBox.critical(self, "خطأ", error_msg)
            sys.exit(1)
    
    def init_ui(self):
        """تهيئة الواجهة الرسومية"""
        self.setWindowTitle("المختار العروضي - نظام التحليل العروضي للشعر العربي")
        self.setGeometry(50, 50, 1600, 900)
        
        # الخط الافتراضي
        try:
            self.default_font = QFont("Sakkal Majalla", 15)
        except:
            self.default_font = QFont("Arial", 15)
        
        # الويدجت المركزي
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # تطبيق نمط عصري جميل
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f8f9fa, stop:1 #e9ecef);
            }
            QWidget {
                background-color: transparent;
            }
        """)
        central_widget.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f8f9fa, stop:1 #e9ecef);
            }
        """)
        
        # التخطيط الرئيسي
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # ========== شريط الأزرار ==========
        buttons_container = self.create_buttons_bar()
        main_layout.addWidget(buttons_container)
        
        # ========== الأعمدة الثلاثة ==========
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(20)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #f5f5f5;
                border: none;
            }
            QSplitter::handle:hover {
                background-color: #e8e8e8;
            }
        """)
        
        # العمود الأول: المدخلات (يمين)
        inputs_widget = self.create_inputs_column()
        splitter.addWidget(inputs_widget)
        
        # العمود الثاني: النتائج (وسط)
        results_widget = self.create_results_column()
        splitter.addWidget(results_widget)
        
        # العمود الثالث: السجل (يسار)
        log_widget = self.create_log_column()
        splitter.addWidget(log_widget)
        
        # تعيين النسب
        splitter.setSizes([550, 700, 350])
        
        main_layout.addWidget(splitter, stretch=1)
        
        # شريط الحالة
        self.statusBar().showMessage("جاهز")
        self.statusBar().setFont(self.default_font)
    
    def create_buttons_bar(self) -> QWidget:
        """إنشاء شريط الأزرار العلوي"""
        container = QWidget()
        container.setStyleSheet("background-color: #e8e8e8; border-radius: 3px;")
        container.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        layout = QHBoxLayout(container)
        layout.setSpacing(8)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # زر التحليل
        self.btn_analyze = self.create_button("تحليل", self.analyze_poem)
        self.btn_analyze.setStyleSheet("""
            QPushButton {
                background-color: #a0a0a0;
                color: #ffffff;
                font-size: 16px;
                font-weight: bold;
                border: 1px solid #808080;
                border-radius: 3px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #909090;
            }
            QPushButton:pressed {
                background-color: #808080;
            }
        """)
        layout.addWidget(self.btn_analyze)
        
        # زر مسح
        self.btn_clear = self.create_button("مسح", self.clear_input)
        layout.addWidget(self.btn_clear)
        
        # زر فتح HTML
        self.btn_open_html = self.create_button("فتح HTML", self.open_html_output)
        layout.addWidget(self.btn_open_html)
        
        # زر حفظ النتائج
        self.btn_save = self.create_button("حفظ النتائج", self.save_results)
        layout.addWidget(self.btn_save)
        
        # زر تحميل عينة
        self.btn_load_sample = self.create_button("تحميل عينة", self.load_sample)
        layout.addWidget(self.btn_load_sample)
        
        # زر معلومات
        self.btn_about = self.create_button("معلومات", self.show_about)
        layout.addWidget(self.btn_about)
        
        layout.addStretch()
        
        # شريط التقدم
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumWidth(200)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #e0e0e0;
                border: 1px solid #c0c0c0;
                border-radius: 3px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #b0b0b0;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        return container
    
    def create_button(self, text: str, slot) -> QPushButton:
        """إنشاء زر بنمط موحد"""
        btn = QPushButton(text)
        btn.setFont(self.default_font)
        btn.setMinimumHeight(40)
        btn.setMinimumWidth(110)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #d0d0d0;
                color: #000000;
                font-size: 15px;
                font-weight: bold;
                border: 1px solid #b0b0b0;
                border-radius: 3px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #c0c0c0;
            }
            QPushButton:pressed {
                background-color: #b0b0b0;
            }
            QPushButton:disabled {
                background-color: #e8e8e8;
                color: #888888;
            }
        """)
        btn.clicked.connect(slot)
        return btn
    
    def create_inputs_column(self) -> QWidget:
        """إنشاء عمود المدخلات"""
        widget = QWidget()
        widget.setStyleSheet("background-color: #f5f5f5;")
        layout = QVBoxLayout(widget)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # العنوان
        title = QLabel("إدخال البيت الشعري")
        title.setFont(QFont(self.default_font.family(), 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #000000;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # مربع الإدخال
        input_label = QLabel("البيت الشعري (*** بين الشطرين):")
        input_label.setFont(self.default_font)
        input_label.setStyleSheet("color: #000000;")
        layout.addWidget(input_label)
        
        self.input_text = QTextEdit()
        self.input_text.setFont(QFont(self.default_font.family(), 18))
        self.input_text.setPlaceholderText("أدخل البيت الشعري هنا...\nمثال: قِفَا نَبْكِ مِنْ ذِكْرَى حَبِيبٍ وَمَنْزِلِ *** بِسِقْطِ اللِّوَى بَيْنَ الدَّخُولِ فَحَوْمَلِ")
        self.input_text.setStyleSheet("""
            QTextEdit {
                background-color: #ffffff;
                border: 2px solid #c0c0c0;
                border-radius: 5px;
                color: #000000;
                padding: 10px;
            }
            QTextEdit:focus {
                border: 2px solid #a0a0a0;
            }
        """)
        self.input_text.setMinimumHeight(150)
        layout.addWidget(self.input_text)
        
        # البيت المعالج
        processed_label = QLabel("البيت بعد المعالجة:")
        processed_label.setFont(self.default_font)
        processed_label.setStyleSheet("color: #000000;")
        layout.addWidget(processed_label)
        
        self.processed_text = QTextEdit()
        self.processed_text.setFont(QFont(self.default_font.family(), 16))
        self.processed_text.setReadOnly(True)
        self.processed_text.setStyleSheet("""
            QTextEdit {
                background-color: #f9f9f9;
                border: 1px solid #c0c0c0;
                border-radius: 5px;
                color: #27ae60;
                padding: 10px;
            }
        """)
        self.processed_text.setMinimumHeight(100)
        layout.addWidget(self.processed_text)
        
        # معلومات سريعة
        info_group = QGroupBox("معلومات سريعة")
        info_group.setFont(self.default_font)
        info_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #c0c0c0;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                right: 10px;
                padding: 0 5px;
            }
        """)
        info_layout = QVBoxLayout(info_group)
        
        self.info_label = QLabel("لا توجد معلومات بعد")
        self.info_label.setFont(self.default_font)
        self.info_label.setStyleSheet("color: #666666; padding: 10px;")
        self.info_label.setWordWrap(True)
        info_layout.addWidget(self.info_label)
        
        layout.addWidget(info_group)
        
        return widget
    
    def create_results_column(self) -> QWidget:
        """إنشاء عمود النتائج"""
        widget = QWidget()
        widget.setStyleSheet("background-color: #f5f5f5;")
        layout = QVBoxLayout(widget)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # العنوان
        title = QLabel("نتائج التحليل العروضي")
        title.setFont(QFont(self.default_font.family(), 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #000000;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # عرض النتائج
        self.results_text = QTextEdit()
        self.results_text.setFont(QFont(self.default_font.family(), 15))
        self.results_text.setReadOnly(True)
        self.results_text.setStyleSheet("""
            QTextEdit {
                background-color: #ffffff;
                border: 2px solid #c0c0c0;
                border-radius: 5px;
                color: #000000;
                padding: 15px;
                line-height: 1.6;
            }
        """)
        layout.addWidget(self.results_text, stretch=1)
        
        return widget
    
    def create_log_column(self) -> QWidget:
        """إنشاء عمود السجل"""
        widget = QWidget()
        widget.setStyleSheet("background-color: #f5f5f5;")
        layout = QVBoxLayout(widget)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # العنوان
        title = QLabel("سجل العمليات")
        title.setFont(QFont(self.default_font.family(), 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #000000;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # قائمة السجل
        self.log_list = QListWidget()
        self.log_list.setFont(self.default_font)
        self.log_list.setStyleSheet("""
            QListWidget {
                background-color: #ffffff;
                border: 1px solid #c0c0c0;
                border-radius: 5px;
                color: #000000;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #e8e8e8;
            }
            QListWidget::item:selected {
                background-color: #d0d0d0;
            }
        """)
        layout.addWidget(self.log_list, stretch=1)
        
        # زر مسح السجل
        clear_log_btn = self.create_button("مسح السجل", self.clear_log)
        clear_log_btn.setMinimumWidth(0)
        layout.addWidget(clear_log_btn)
        
        return widget
    
    # ========== دوال الأزرار ==========
    
    def analyze_poem(self):
        """تحليل البيت الشعري"""
        poem = self.input_text.toPlainText().strip()
        
        if not poem:
            QMessageBox.warning(self, "تحذير", "يرجى إدخال بيت شعري")
            return
        
        # التحقق من وجود الفاصل
        if "***" not in poem:
            reply = QMessageBox.question(
                self,
                "تأكيد",
                "لم يتم العثور على الفاصل (***) بين الشطرين.\nهل تريد المتابعة؟",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
        
        # تعطيل الأزرار
        self.btn_analyze.setEnabled(False)
        self.btn_clear.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # indeterminate
        
        # بدء التحليل في خيط منفصل
        self.analysis_worker = AnalysisWorker(poem, self.matcher)
        self.analysis_worker.finished.connect(self.on_analysis_finished)
        self.analysis_worker.error.connect(self.on_analysis_error)
        self.analysis_worker.progress.connect(self.log_message)
        self.analysis_worker.start()
        
        self.log_message(f"بدء تحليل: {poem[:50]}...")
    
    def on_analysis_finished(self, original: str, processed: str, results: Dict):
        """عند اكتمال التحليل"""
        # إعادة تفعيل الأزرار
        self.btn_analyze.setEnabled(True)
        self.btn_clear.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        # عرض البيت المعالج
        self.processed_text.setPlainText(processed)
        
        # حفظ في السجل
        self.results_history.append({
            'original': original,
            'processed': processed,
            'results': results,
            'timestamp': datetime.now()
        })
        self.current_result_index = len(self.results_history) - 1
        
        # عرض النتائج
        self.display_results(original, processed, results)
        
        # معالجة HTML
        try:
            self.processor.process(original, processed, results)
        except Exception as e:
            self.log_message(f"⚠️ تحذير: فشل إنشاء HTML: {str(e)}")
        
        self.log_message("✅ اكتمل التحليل بنجاح")
        self.statusBar().showMessage("اكتمل التحليل", 3000)
    
    def on_analysis_error(self, error: str):
        """عند حدوث خطأ في التحليل"""
        self.btn_analyze.setEnabled(True)
        self.btn_clear.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        QMessageBox.critical(self, "خطأ", error)
        self.log_message(f"❌ {error}")
        self.statusBar().showMessage("فشل التحليل", 3000)
    
    def display_results(self, original: str, processed: str, results: Dict):
        """عرض نتائج التحليل"""
        output = ""
        output += "=" * 60 + "\n"
        output += "نتائج التحليل العروضي\n"
        output += "=" * 60 + "\n\n"
        
        output += f"البيت الأصلي:\n{original}\n\n"
        output += f"البيت المعالج:\n{processed}\n\n"
        
        output += "─" * 60 + "\n\n"
        
        if results:
            output += f"✅ تم العثور على {len(results)} بحر مطابق:\n\n"
            
            for i, (sea, line) in enumerate(results.items(), 1):
                output += f"{'═' * 60}\n"
                output += f"البحر {i}: {sea}\n"
                output += f"{'═' * 60}\n\n"
                
                # الحصول على الوزن
                try:
                    weight = self.processor.get_weights(sea)
                    output += f"📐 الوزن الأصلي:\n{weight}\n\n"
                except:
                    pass
                
                # التفاعيل
                output += f"🎵 التفاعيل:\n{line}\n\n"
                
                # المقارنة
                try:
                    fmt, comps = self.processor.compare(sea, line)
                    
                    # معالجة التفاعيل
                    tafeelat_results = self.processor.process_comps(comps)
                    
                    output += "📊 تحليل التفاعيل:\n"
                    output += "─" * 60 + "\n"
                    for j, result in enumerate(tafeelat_results, 1):
                        output += f"{j}. {result}\n"
                    output += "\n"
                    
                except Exception as e:
                    output += f"⚠️ تعذر تحليل التفاعيل: {str(e)}\n\n"
            
            # تحديث المعلومات السريعة
            info_text = f"✅ تم تحديد البحر بنجاح\n"
            info_text += f"عدد البحور المطابقة: {len(results)}\n"
            info_text += f"البحر الأول: {list(results.keys())[0]}"
            self.info_label.setText(info_text)
            
        else:
            output += "❌ لم يتم العثور على بحر مطابق\n\n"
            output += "الأسباب المحتملة:\n"
            output += "• البيت قد يحتوي على خطأ عروضي\n"
            output += "• البحر غير موجود في قاعدة البيانات\n"
            output += "• قد يحتاج البيت إلى تشكيل أدق\n"
            
            self.info_label.setText("❌ لم يتم العثور على بحر مطابق")
        
        output += "\n" + "=" * 60 + "\n"
        output += f"وقت التحليل: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        output += "=" * 60 + "\n"
        
        self.results_text.setPlainText(output)
    
    def clear_input(self):
        """مسح المدخلات"""
        self.input_text.clear()
        self.processed_text.clear()
        self.results_text.clear()
        self.info_label.setText("لا توجد معلومات بعد")
        self.log_message("تم مسح المدخلات")
    
    def open_html_output(self):
        """فتح ملف HTML الناتج"""
        output_file = self.base_dir / "وزن_البيت.html"
        
        if not output_file.exists():
            QMessageBox.warning(
                self, 
                "تحذير", 
                "لم يتم العثور على ملف HTML.\nيرجى تحليل بيت أولاً."
            )
            return
        
        try:
            webbrowser.open(str(output_file))
            self.log_message(f"تم فتح: {output_file.name}")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل فتح الملف:\n{str(e)}")
    
    def save_results(self):
        """حفظ النتائج في ملف نصي"""
        if not self.results_history:
            QMessageBox.warning(self, "تحذير", "لا توجد نتائج لحفظها")
            return
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.base_dir / f"نتائج_التحليل_{timestamp}.txt"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write("المختار العروضي - نتائج التحليل\n")
                f.write("=" * 80 + "\n\n")
                
                for i, result in enumerate(self.results_history, 1):
                    f.write(f"\nالبيت {i}:\n")
                    f.write("─" * 80 + "\n")
                    f.write(f"الأصلي: {result['original']}\n")
                    f.write(f"المعالج: {result['processed']}\n")
                    f.write(f"الوقت: {result['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}\n")
                    
                    if result['results']:
                        f.write(f"\nالبحور المطابقة ({len(result['results'])}):\n")
                        for sea, line in result['results'].items():
                            f.write(f"  • {sea}: {line}\n")
                    else:
                        f.write("\n❌ لم يتم العثور على بحر مطابق\n")
                    
                    f.write("\n" + "=" * 80 + "\n")
            
            QMessageBox.information(
                self, 
                "نجح", 
                f"تم حفظ النتائج في:\n{output_file.name}"
            )
            self.log_message(f"تم حفظ النتائج: {output_file.name}")
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل حفظ النتائج:\n{str(e)}")
    
    def load_sample(self):
        """تحميل عينة من الأبيات"""
        sample_file = self.base_dir / "عينة كاملة.txt"
        
        if not sample_file.exists():
            QMessageBox.warning(
                self, 
                "تحذير", 
                "لم يتم العثور على ملف العينة"
            )
            return
        
        try:
            # قراءة أول 10 أبيات
            with open(sample_file, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f.readlines()[:10] if line.strip()]
            
            if lines:
                # اختيار بيت عشوائي
                import random
                sample = random.choice(lines)
                self.input_text.setPlainText(sample)
                self.log_message(f"تم تحميل عينة: {sample[:50]}...")
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل تحميل العينة:\n{str(e)}")
    
    def show_about(self):
        """عرض معلومات البرنامج"""
        about_text = """
        <div dir="rtl" style="font-family: 'Sakkal Majalla', Arial; font-size: 14pt;">
        <h2 style="text-align: center; color: #2c3e50;">المختار العروضي</h2>
        <p style="text-align: center; color: #7f8c8d;">نظام التحليل العروضي للشعر العربي</p>
        <hr>
        <p><b>الإصدار:</b> 0.4</p>
        <p><b>الوظيفة:</b> تحليل الأبيات الشعرية وتحديد البحر العروضي</p>
        <hr>
        <h3>المميزات:</h3>
        <ul>
            <li>تحليل عروضي دقيق للشعر العربي</li>
            <li>تحديد البحر والتفاعيل</li>
            <li>كشف الزحافات والعلل</li>
            <li>واجهة رسومية احترافية</li>
            <li>دعم كامل للنصوص العربية</li>
        </ul>
        <hr>
        <p style="text-align: center; color: #95a5a6;">
        © 2024 المختار العروضي - جميع الحقوق محفوظة
        </p>
        </div>
        """
        
        msg = QMessageBox(self)
        msg.setWindowTitle("معلومات البرنامج")
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setText(about_text)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()
    
    def clear_log(self):
        """مسح السجل"""
        self.log_list.clear()
        self.log_message("تم مسح السجل")
    
    def log_message(self, message: str):
        """إضافة رسالة للسجل"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        item = QListWidgetItem(f"[{timestamp}] {message}")
        if hasattr(self, 'log_list'):
            self.log_list.addItem(item)
            self.log_list.scrollToBottom()
    
    def closeEvent(self, event):
        """عند إغلاق النافذة"""
        # إيقاف العامل إن كان يعمل
        if self.analysis_worker and self.analysis_worker.isRunning():
            reply = QMessageBox.question(
                self,
                "تأكيد",
                "التحليل جارٍ. هل تريد الإغلاق؟",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return
            else:
                self.analysis_worker.terminate()
                self.analysis_worker.wait(1000)
        
        event.accept()


def main():
    """تشغيل التطبيق"""
    app = QApplication(sys.argv)
    
    # تعيين الخط الافتراضي
    try:
        font = QFont("Sakkal Majalla", 14)
    except:
        font = QFont("Arial", 14)
    app.setFont(font)
    
    # إنشاء النافذة الرئيسية
    window = ProsodyMainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

