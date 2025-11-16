"""
المختار العروضي - واجهة بتصميم Apple
تصميم نظيف، أنيق، بسيط وجميل

مبادئ التصميم:
- البساطة أولاً
- مساحات بيضاء كافية
- ألوان هادئة ومريحة
- تركيز على المحتوى
- انتقالات سلسة
- تفاصيل دقيقة
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Tuple

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QLabel, QApplication,
    QFrame, QScrollArea, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QPropertyAnimation, QEasingCurve, QTimer
from PyQt6.QtGui import QFont, QColor, QPalette, QIcon

from data import load_replacements_from_db
from core import PoetryMatcher
from settings import REPLACEMENTS_DB, DB_PATH, WEIGHTS_DB, TAFEELAT_DB
from app import ResultProcessor


class AnalysisWorker(QThread):
    """عامل التحليل في الخلفية"""
    finished = pyqtSignal(str, str, dict)
    error = pyqtSignal(str)
    
    def __init__(self, poem: str, matcher: PoetryMatcher):
        super().__init__()
        self.poem = poem
        self.matcher = matcher
        
    def run(self):
        try:
            processed, full = self.matcher.process_poem(self.poem)
            self.finished.emit(self.poem, processed, full)
        except Exception as e:
            self.error.emit(f"خطأ في التحليل: {str(e)}")


class AppleButton(QPushButton):
    """زر بتصميم Apple"""
    def __init__(self, text: str, primary=False):
        super().__init__(text)
        self.primary = primary
        self.setup_style()
    
    def setup_style(self):
        """تطبيق نمط شعري فاخر"""
        if self.primary:
            # الزر الأساسي - عنابي فخم
            self.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #8B1538, stop:1 #6B0F2A);
                    color: white;
                    border: 2px solid #D4AF37;
                    border-radius: 12px;
                    padding: 12px 28px;
                    font-size: 16px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #A01A45, stop:1 #8B1538);
                    border: 2px solid #FFD700;
                }
                QPushButton:pressed {
                    background: #6B0F2A;
                }
                QPushButton:disabled {
                    background-color: #D3C5B8;
                    color: #8B6F47;
                    border: 2px solid #C0B5A8;
                }
            """)
        else:
            # الزر الثانوي - فيروزي أنيق
            self.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #5AB5BA, stop:1 #4A9B9F);
                    color: white;
                    border: 2px solid #D4AF37;
                    border-radius: 12px;
                    padding: 12px 24px;
                    font-size: 15px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #6AC5CA, stop:1 #5AB5BA);
                    border: 2px solid #FFD700;
                }
                QPushButton:pressed {
                    background: #3A8B8F;
                }
                QPushButton:disabled {
                    background-color: #D3C5B8;
                    color: #8B6F47;
                    border: 2px solid #C0B5A8;
                }
            """)
        
        self.setMinimumHeight(44)
        self.setCursor(Qt.CursorShape.PointingHandCursor)


class AppleCard(QFrame):
    """بطاقة بتصميم شعري فاخر"""
    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFFFFF, stop:1 #FBF8F3);
                border-radius: 20px;
                border: 2px solid #D4AF37;
            }
        """)
        
        # إضافة ظل ذهبي خفيف
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(25)
        shadow.setXOffset(0)
        shadow.setYOffset(6)
        shadow.setColor(QColor(212, 175, 55, 40))  # ذهبي شفاف
        self.setGraphicsEffect(shadow)


class AppleTextEdit(QTextEdit):
    """مربع نص بتصميم شعري"""
    def __init__(self, placeholder=""):
        super().__init__()
        self.setPlaceholderText(placeholder)
        self.setStyleSheet("""
            QTextEdit {
                background-color: #FBF8F3;
                border: 2px solid #D4AF37;
                border-radius: 14px;
                padding: 18px;
                font-size: 17px;
                color: #3E2723;
                selection-background-color: #8B1538;
                selection-color: white;
            }
            QTextEdit:focus {
                background-color: #FFFFFF;
                border: 3px solid #8B1538;
            }
        """)


class ProsodyAppleWindow(QMainWindow):
    """النافذة الرئيسية بتصميم Apple"""
    
    def __init__(self):
        super().__init__()
        self.base_dir = Path(__file__).parent
        self.matcher = None
        self.processor = None
        self.analysis_worker = None
        
        self.setup_fonts()
        self.init_ui()
        self.init_data()
    
    def setup_fonts(self):
        """إعداد الخطوط بأسلوب Apple"""
        # SF Pro Display لـ Apple (نستخدم بديل)
        try:
            self.title_font = QFont("Sakkal Majalla", 28, QFont.Weight.Bold)
            self.heading_font = QFont("Sakkal Majalla", 20, QFont.Weight.Bold)
            self.body_font = QFont("Sakkal Majalla", 16)
            self.caption_font = QFont("Sakkal Majalla", 14)
        except:
            self.title_font = QFont("Arial", 28, QFont.Weight.Bold)
            self.heading_font = QFont("Arial", 20, QFont.Weight.Bold)
            self.body_font = QFont("Arial", 16)
            self.caption_font = QFont("Arial", 14)
    
    def init_ui(self):
        """بناء الواجهة بأسلوب Apple"""
        self.setWindowTitle("المختار العروضي")
        self.setGeometry(100, 100, 1400, 900)
        
        # خلفية كريمية دافئة (ورق مخطوطة)
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FBF8F3, stop:1 #F5F0E8);
            }
        """)
        
        # الويدجت المركزي
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(24)
        main_layout.setContentsMargins(40, 40, 40, 40)
        
        # ========== الهيدر ==========
        header = self.create_header()
        main_layout.addWidget(header)
        
        # ========== المحتوى الرئيسي ==========
        content_layout = QHBoxLayout()
        content_layout.setSpacing(24)
        
        # العمود الأيمن: الإدخال
        input_card = self.create_input_section()
        content_layout.addWidget(input_card, stretch=1)
        
        # العمود الأيسر: النتائج
        results_card = self.create_results_section()
        content_layout.addWidget(results_card, stretch=1)
        
        main_layout.addLayout(content_layout, stretch=1)
        
        # شريط الحالة
        self.statusBar().setStyleSheet("""
            QStatusBar {
                background-color: transparent;
                color: #8B6F47;
                font-size: 14px;
                font-weight: 500;
            }
        """)
        self.statusBar().showMessage("🎭 جاهز للتحليل")
    
    def create_header(self) -> QWidget:
        """إنشاء الهيدر"""
        header = QWidget()
        header_layout = QVBoxLayout(header)
        header_layout.setSpacing(8)
        header_layout.setContentsMargins(0, 0, 0, 20)
        
        # العنوان الرئيسي
        title = QLabel("المختار العروضي")
        title.setFont(self.title_font)
        title.setStyleSheet("color: #6B0F2A; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title)
        
        # العنوان الفرعي
        subtitle = QLabel("نظام التحليل العروضي للشعر العربي")
        subtitle.setFont(self.caption_font)
        subtitle.setStyleSheet("color: #8B6F47;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(subtitle)
        
        return header
    
    def create_input_section(self) -> QWidget:
        """إنشاء قسم الإدخال"""
        card = AppleCard()
        layout = QVBoxLayout(card)
        layout.setSpacing(20)
        layout.setContentsMargins(32, 32, 32, 32)
        
        # العنوان
        title = QLabel("أدخل البيت الشعري")
        title.setFont(self.heading_font)
        title.setStyleSheet("color: #6B0F2A; font-weight: bold;")
        layout.addWidget(title)
        
        # مربع الإدخال
        self.input_text = AppleTextEdit(
            "أدخل البيت الشعري هنا...\n\nاستخدم *** للفصل بين الشطرين\n\nمثال:\nقِفَا نَبْكِ مِنْ ذِكْرَى حَبِيبٍ وَمَنْزِلِ *** بِسِقْطِ اللِّوَى بَيْنَ الدَّخُولِ فَحَوْمَلِ"
        )
        self.input_text.setFont(self.body_font)
        self.input_text.setMinimumHeight(200)
        layout.addWidget(self.input_text)
        
        # الأزرار
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(12)
        
        # زر تحميل عينة
        self.btn_sample = AppleButton("تحميل عينة", False)
        self.btn_sample.clicked.connect(self.load_sample)
        buttons_layout.addWidget(self.btn_sample)
        
        buttons_layout.addStretch()
        
        # زر مسح
        self.btn_clear = AppleButton("مسح", False)
        self.btn_clear.clicked.connect(self.clear_input)
        buttons_layout.addWidget(self.btn_clear)
        
        # زر تحليل (أساسي)
        self.btn_analyze = AppleButton("تحليل", True)
        self.btn_analyze.clicked.connect(self.analyze_poem)
        buttons_layout.addWidget(self.btn_analyze)
        
        layout.addLayout(buttons_layout)
        
        # البيت المعالج
        processed_label = QLabel("البيت المعالج:")
        processed_label.setFont(self.caption_font)
        processed_label.setStyleSheet("color: #8B6F47; margin-top: 12px; font-weight: 600;")
        layout.addWidget(processed_label)
        
        self.processed_text = QTextEdit()
        self.processed_text.setReadOnly(True)
        self.processed_text.setFont(QFont(self.body_font.family(), 14))
        self.processed_text.setStyleSheet("""
            QTextEdit {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #E8F5F5, stop:1 #D5EDED);
                border: 2px solid #4A9B9F;
                border-radius: 10px;
                padding: 14px;
                color: #2C6B6F;
                font-weight: 500;
            }
        """)
        self.processed_text.setMaximumHeight(80)
        layout.addWidget(self.processed_text)
        
        return card
    
    def create_results_section(self) -> QWidget:
        """إنشاء قسم النتائج"""
        card = AppleCard()
        layout = QVBoxLayout(card)
        layout.setSpacing(20)
        layout.setContentsMargins(32, 32, 32, 32)
        
        # العنوان
        title = QLabel("نتائج التحليل")
        title.setFont(self.heading_font)
        title.setStyleSheet("color: #6B0F2A; font-weight: bold;")
        layout.addWidget(title)
        
        # منطقة النتائج
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setFont(self.body_font)
        self.results_text.setStyleSheet("""
            QTextEdit {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFFEF9, stop:1 #FBF8F3);
                border: 2px solid #D4AF37;
                border-radius: 12px;
                color: #3E2723;
                padding: 20px;
                line-height: 1.8;
            }
        """)
        self.results_text.setPlaceholderText("ستظهر النتائج هنا بعد التحليل...")
        layout.addWidget(self.results_text)
        
        # أزرار إضافية
        extra_buttons = QHBoxLayout()
        extra_buttons.setSpacing(12)
        
        self.btn_save = AppleButton("حفظ", False)
        self.btn_save.clicked.connect(self.save_results)
        extra_buttons.addWidget(self.btn_save)
        
        self.btn_html = AppleButton("عرض HTML", False)
        self.btn_html.clicked.connect(self.open_html)
        extra_buttons.addWidget(self.btn_html)
        
        extra_buttons.addStretch()
        
        layout.addLayout(extra_buttons)
        
        return card
    
    def init_data(self):
        """تحميل البيانات"""
        try:
            reps = load_replacements_from_db(REPLACEMENTS_DB)
            self.matcher = PoetryMatcher(DB_PATH, reps)
            
            output_file = self.base_dir / "وزن_البيت.html"
            self.processor = ResultProcessor(WEIGHTS_DB, TAFEELAT_DB, str(output_file))
            
            self.statusBar().showMessage("✓ جاهز للتحليل", 3000)
        except Exception as e:
            self.statusBar().showMessage(f"✗ خطأ: {str(e)}")
    
    def analyze_poem(self):
        """تحليل البيت"""
        poem = self.input_text.toPlainText().strip()
        
        if not poem:
            self.show_message("يرجى إدخال بيت شعري", False)
            return
        
        # تعطيل الأزرار
        self.btn_analyze.setEnabled(False)
        self.btn_analyze.setText("جارٍ التحليل...")
        self.statusBar().showMessage("⏳ جارٍ التحليل...")
        
        # بدء التحليل
        self.analysis_worker = AnalysisWorker(poem, self.matcher)
        self.analysis_worker.finished.connect(self.on_analysis_finished)
        self.analysis_worker.error.connect(self.on_analysis_error)
        self.analysis_worker.start()
    
    def on_analysis_finished(self, original: str, processed: str, results: Dict):
        """عند اكتمال التحليل"""
        self.btn_analyze.setEnabled(True)
        self.btn_analyze.setText("تحليل")
        
        # عرض البيت المعالج
        self.processed_text.setPlainText(processed)
        
        # عرض النتائج
        self.display_results(original, processed, results)
        
        # معالجة HTML
        try:
            self.processor.process(original, processed, results)
        except:
            pass
        
        if results:
            self.statusBar().showMessage(f"✓ تم تحديد {len(results)} بحر", 5000)
        else:
            self.statusBar().showMessage("✗ لم يتم العثور على بحر مطابق", 5000)
    
    def on_analysis_error(self, error: str):
        """عند حدوث خطأ"""
        self.btn_analyze.setEnabled(True)
        self.btn_analyze.setText("تحليل")
        self.show_message(error, False)
        self.statusBar().showMessage(f"✗ {error}")
    
    def display_results(self, original: str, processed: str, results: Dict):
        """عرض النتائج بشكل جميل"""
        if not results:
            output = "❌ لم يتم العثور على بحر مطابق\n\n"
            output += "الأسباب المحتملة:\n"
            output += "• البيت قد يحتوي على خطأ عروضي\n"
            output += "• البحر غير موجود في قاعدة البيانات\n"
            output += "• قد يحتاج البيت إلى تشكيل أدق"
            self.results_text.setPlainText(output)
            return
        
        output = ""
        
        for i, (sea, line) in enumerate(results.items(), 1):
            if i > 1:
                output += "\n" + "─" * 60 + "\n\n"
            
            output += f"🎵 البحر: {sea}\n\n"
            
            # الوزن
            try:
                weight = self.processor.get_weights(sea)
                output += f"الوزن الأصلي:\n{weight}\n\n"
            except:
                pass
            
            # التفاعيل
            output += f"التفاعيل:\n{line}\n\n"
            
            # التحليل التفصيلي
            try:
                fmt, comps = self.processor.compare(sea, line)
                tafeelat_results = self.processor.process_comps(comps)
                
                output += "التحليل التفصيلي:\n"
                for j, result in enumerate(tafeelat_results, 1):
                    output += f"{j}. {result}\n"
                
            except:
                pass
        
        self.results_text.setPlainText(output)
    
    def clear_input(self):
        """مسح المدخلات"""
        self.input_text.clear()
        self.processed_text.clear()
        self.results_text.clear()
        self.statusBar().showMessage("تم المسح", 2000)
    
    def load_sample(self):
        """تحميل عينة"""
        sample_file = self.base_dir / "عينة كاملة.txt"
        
        if not sample_file.exists():
            self.show_message("ملف العينة غير موجود", False)
            return
        
        try:
            with open(sample_file, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f.readlines()[:20] if line.strip() and '***' in line]
            
            if lines:
                import random
                sample = random.choice(lines)
                self.input_text.setPlainText(sample)
                self.statusBar().showMessage("✓ تم تحميل عينة", 2000)
        except Exception as e:
            self.show_message(f"خطأ: {str(e)}", False)
    
    def save_results(self):
        """حفظ النتائج"""
        text = self.results_text.toPlainText()
        if not text:
            self.show_message("لا توجد نتائج لحفظها", False)
            return
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.base_dir / f"نتائج_{timestamp}.txt"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(text)
            
            self.statusBar().showMessage(f"✓ تم الحفظ: {output_file.name}", 3000)
        except Exception as e:
            self.show_message(f"خطأ في الحفظ: {str(e)}", False)
    
    def open_html(self):
        """فتح HTML"""
        output_file = self.base_dir / "وزن_البيت.html"
        
        if not output_file.exists():
            self.show_message("ملف HTML غير موجود. قم بالتحليل أولاً", False)
            return
        
        try:
            import webbrowser
            webbrowser.open(str(output_file))
            self.statusBar().showMessage("✓ تم فتح HTML", 2000)
        except Exception as e:
            self.show_message(f"خطأ: {str(e)}", False)
    
    def show_message(self, message: str, success=True):
        """عرض رسالة"""
        self.statusBar().showMessage(("✓ " if success else "✗ ") + message, 3000)


def main():
    """تشغيل التطبيق"""
    app = QApplication(sys.argv)
    
    # تطبيق خط النظام
    app.setFont(QFont("Sakkal Majalla", 14))
    
    # نافذة التطبيق
    window = ProsodyAppleWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

