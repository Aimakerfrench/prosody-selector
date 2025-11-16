"""
واجهة رسومية احترافية للمختار الصرفي
تصميم كلاسيكي بألوان رمادية - نفس هوية main_window
"""
import sys
import os
import ast
import json
import logging
from pathlib import Path
from datetime import datetime
from collections import defaultdict

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QFileDialog, QMessageBox,
    QScrollArea, QLabel, QProgressBar, QSplitter,
    QListWidget, QListWidgetItem, QTabWidget, QTreeWidget,
    QTreeWidgetItem, QGroupBox, QCheckBox, QRadioButton,
    QLineEdit, QDialog, QDialogButtonBox, QFormLayout,
    QSpinBox, QDoubleSpinBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize, QTimer
from PyQt6.QtGui import QFont, QColor, QPainter

# استيراد جميع الفئات من الكود الأصلي
import importlib.util
import sys

# تحميل الكود الأصلي كوحدة
core_file = os.path.join(os.path.dirname(__file__), "0.5 المختار الصرفي.py")
spec = importlib.util.spec_from_file_location("morphology_core", core_file)
morphology_core = importlib.util.module_from_spec(spec)
sys.modules['morphology_core'] = morphology_core
spec.loader.exec_module(morphology_core)

# استيراد الفئات المطلوبة
CacheManager = morphology_core.CacheManager
DatabaseManager = morphology_core.DatabaseManager
PatternRanker = morphology_core.PatternRanker
CrossValidator = morphology_core.CrossValidator
FileManager = morphology_core.FileManager
ArabicProcessor = morphology_core.ArabicProcessor
DiacriticsHandler = morphology_core.DiacriticsHandler
WordSplitter = morphology_core.WordSplitter
ReportGenerator = morphology_core.ReportGenerator
process_weight = morphology_core.process_weight
collect_corpus_words = morphology_core.collect_corpus_words
load_tags = morphology_core.load_tags


class DotsHandle(QWidget):
    """Widget مخصص لرسم 3 نقاط في المنتصف (مثل main_window)"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(20)
        self.setMaximumWidth(20)
    
    def paintEvent(self, event):
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
            painter.drawEllipse(int(width / 2 - dot_size / 2), int(y - dot_size / 2), dot_size, dot_size)


class MorphologyWorker(QThread):
    """عامل لتشغيل التحليل الصرفي في خيط منفصل"""
    finished = pyqtSignal(bool, dict, str)  # success, results, error
    progress = pyqtSignal(str, int, int)  # message, current, total
    log_message = pyqtSignal(str)  # log message
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.should_stop = False
        
    def stop(self):
        """إيقاف المعالجة"""
        self.should_stop = True
    
    def run(self):
        """تنفيذ التحليل الصرفي"""
        try:
            start_time = datetime.now()
            
            # تحميل الإعدادات
            database_folder = self.config['database_folder']
            corpus_folder = self.config['corpus_folder']
            names_weights_file = self.config['names_weights_file']
            verbs_weights_file = self.config['verbs_weights_file']
            names_affixes_file = self.config['names_affixes_file']
            verbs_affixes_file = self.config['verbs_affixes_file']
            symbols_file_path = self.config['symbols_file_path']
            tags_file_path = self.config['tags_file_path']
            names_results_dir = self.config['names_results_dir']
            verbs_results_dir = self.config['verbs_results_dir']
            
            optional_tashkeel = self.config['optional_tashkeel']
            match_whole_word = self.config['match_whole_word']
            corpus_type = self.config.get('corpus_type', 'list')
            use_cache = self.config['use_cache']
            use_database = self.config['use_database']
            use_cross_validation = self.config['use_cross_validation']
            
            file_paths = self.config['file_paths']
            
            self.log_message.emit("بدء تحميل البيانات...")
            
            # تحميل الرموز
            with open(symbols_file_path, "r", encoding="utf-8") as sf:
                symbols_map = ast.literal_eval(sf.read())
            
            # تحميل السوابق واللواحق
            if os.path.exists(names_affixes_file):
                with open(names_affixes_file, 'r', encoding='utf-8') as f:
                    names_affixes_data = ast.literal_eval(f.read())
            else:
                names_affixes_data = {'prefixes': [], 'suffixes': []}
            
            if os.path.exists(verbs_affixes_file):
                with open(verbs_affixes_file, 'r', encoding='utf-8') as f:
                    verbs_affixes_data = ast.literal_eval(f.read())
            else:
                verbs_affixes_data = {'prefixes': [], 'suffixes': []}
            
            # تحميل الوسم
            tags_map = load_tags(tags_file_path)
            
            # إنشاء المكونات
            cache_manager = CacheManager() if use_cache else None
            db_manager = DatabaseManager() if use_database else None
            pattern_ranker = PatternRanker(db_manager) if use_database else None
            cross_validator = CrossValidator() if use_cross_validation else None
            
            # إنشاء FileManager لقراءة الأوزان
            temp_file_manager = FileManager(
                corpus_type=corpus_type,
                match_whole_word=match_whole_word,
                affixes_data=names_affixes_data,
                tags_map=tags_map,
                db_manager=None,
                cache_manager=None,
                pattern_ranker=None,
                cross_validator=None
            )
            
            self.log_message.emit("تحميل أوزان الأسماء...")
            names_weights = temp_file_manager.read_weights_and_derived_words(names_weights_file)
            
            self.log_message.emit("تحميل أوزان الأفعال...")
            temp_file_manager.affixes_data = verbs_affixes_data
            verbs_weights = temp_file_manager.read_weights_and_derived_words(verbs_weights_file)
            
            all_weights = {**names_weights, **verbs_weights}
            
            self.log_message.emit(f"تم تحميل {len(all_weights)} وزن صرفي")
            self.progress.emit(f"بدء معالجة {len(all_weights)} وزن...", 0, len(all_weights))
            
            # جمع كلمات المدونة
            all_corpus_words = collect_corpus_words(file_paths, corpus_type=corpus_type)
            self.log_message.emit(f"تم جمع {len(all_corpus_words)} كلمة من المدونة")
            
            # إنشاء المهام (إضافة use_cross_validation للمهام)
            names_tasks = [
                (weight, derived_weights, file_paths, names_results_dir, corpus_type, 
                 match_whole_word, names_affixes_data, tags_map, symbols_map, optional_tashkeel, use_cross_validation)
                for weight, derived_weights in names_weights.items()
            ]
            
            verbs_tasks = [
                (weight, derived_weights, file_paths, verbs_results_dir, corpus_type,
                 match_whole_word, verbs_affixes_data, tags_map, symbols_map, optional_tashkeel, use_cross_validation)
                for weight, derived_weights in verbs_weights.items()
            ]
            
            # تحديد المهام حسب التبويب المختار
            selected_weights_tab = self.config.get('selected_weights_tab', 'all')
            if selected_weights_tab == 'names':
                all_tasks = names_tasks
                self.log_message.emit(f"معالجة أوزان الأسماء فقط ({len(names_tasks)} وزن)")
            elif selected_weights_tab == 'verbs':
                all_tasks = verbs_tasks
                self.log_message.emit(f"معالجة أوزان الأفعال فقط ({len(verbs_tasks)} وزن)")
            else:  # 'all' أو أي قيمة أخرى
                all_tasks = names_tasks + verbs_tasks
                self.log_message.emit(f"معالجة جميع الأوزان ({len(all_tasks)} وزن)")
            
            # معالجة الأوزان
            all_processing_results = []
            all_validation_results = []  # تجميع نتائج التحقق من جميع العمليات
            import concurrent.futures
            import multiprocessing
            
            with concurrent.futures.ProcessPoolExecutor(max_workers=multiprocessing.cpu_count()) as executor:
                # إنشاء جميع المهام
                futures = {executor.submit(process_weight, task): i 
                           for i, task in enumerate(all_tasks)}
                
                completed = 0
                for future in concurrent.futures.as_completed(futures):
                    if self.should_stop:
                        self.log_message.emit("جارٍ إيقاف المعالجة... إلغاء المهام المعلقة...")
                        
                        # إلغاء جميع المهام المعلقة (pending)
                        cancelled_count = 0
                        for f in futures.keys():
                            if not f.done():
                                if f.cancel():
                                    cancelled_count += 1
                        
                        if cancelled_count > 0:
                            self.log_message.emit(f"تم إلغاء {cancelled_count} مهمة معلقة")
                        
                        self.log_message.emit("انتظار انتهاء المهام الجارية...")
                        
                        # الانتظار حتى تنتهي المهام الجارية فقط
                        remaining_futures = {f: idx for f, idx in futures.items() if not f.done()}
                        for future in concurrent.futures.as_completed(remaining_futures):
                            try:
                                result_data = future.result()
                                all_processing_results.append(result_data)
                                
                                # تجميع نتائج التحقق من كل عملية
                                if result_data.get('validation_results'):
                                    all_validation_results.extend(result_data['validation_results'])
                                
                                completed += 1
                                self.log_message.emit(f"انتهت مهمة: {result_data['weight']}")
                            except Exception as e:
                                logging.warning(f"خطأ في مهمة: {e}")
                        
                        self.log_message.emit("تم إيقاف المعالجة بنجاح")
                        break
                    
                    completed += 1
                    result_data = future.result()
                    all_processing_results.append(result_data)
                    
                    # تجميع نتائج التحقق من كل عملية
                    if result_data.get('validation_results'):
                        all_validation_results.extend(result_data['validation_results'])
                    
                    self.progress.emit(
                        f"معالجة الوزن: {result_data['weight']}",
                        completed,
                        len(all_tasks)
                    )
                    self.log_message.emit(f"تم معالجة: {result_data['weight']} ({completed}/{len(all_tasks)})")
            
            # دمج نتائج التحقق من جميع العمليات
            merged_cross_validator = None
            if all_validation_results and use_cross_validation:
                merged_cross_validator = CrossValidator()
                merged_cross_validator.validation_results = all_validation_results
            
            if self.should_stop:
                self.finished.emit(False, {}, "تم إيقاف المعالجة بواسطة المستخدم")
                return
            
            # حفظ في قاعدة البيانات
            if db_manager:
                self.log_message.emit("حفظ النتائج في قاعدة البيانات...")
                diacritics_handler = DiacriticsHandler()
                word_splitter = WordSplitter(diacritics_handler)
                
                for i, result_data in enumerate(all_processing_results):
                    weight = result_data['weight']
                    results = result_data['results']
                    
                    extra_chars_count = sum(1 for c in weight if c in FileManager.EXTRA_CHARS)
                    
                    if weight in names_weights:
                        pattern_type = 'اسم'
                    elif weight in verbs_weights:
                        pattern_type = 'فعل'
                    else:
                        pattern_type = 'غير محدد'
                    
                    db_manager.insert_pattern(weight, pattern_type, extra_chars_count)
                    
                    for prefix, root, suffix in results:
                        matched_word = prefix + root + suffix
                        prefix_morph, intermediate_morph, root_morph, suffix_morph = word_splitter.split_word(
                            weight, root
                        )
                        root_without_diacritics = diacritics_handler.remove_diacritics(root_morph)
                        
                        score = 0
                        if pattern_ranker:
                            score = pattern_ranker.calculate_score(
                                weight, matched_word, prefix, suffix, 1
                            )
                        
                        db_manager.insert_result(
                            matched_word, root_without_diacritics, weight,
                            prefix, suffix, intermediate_morph, score
                        )
                    
                    self.progress.emit(f"حفظ في قاعدة البيانات...", i+1, len(all_processing_results))
            
            # حفظ الكاش
            if cache_manager:
                cache_manager.save_cache()
                self.log_message.emit("تم حفظ الكاش")
            
            # حساب النتائج
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # حساب الكلمات المتعرّف عليها
            diacritics_handler = DiacriticsHandler()
            recognized_words = set()
            for result_data in all_processing_results:
                for prefix, root, suffix in result_data['results']:
                    matched_word = prefix + root + suffix
                    matched_word = diacritics_handler.remove_diacritics(matched_word)
                    if matched_word:
                        recognized_words.add(matched_word)
            
            # إحصائيات قاعدة البيانات (قبل إغلاق الاتصال)
            stats = None
            if db_manager:
                stats = db_manager.get_statistics()
                # لا نغلق قاعدة البيانات هنا - سيتم إغلاقها لاحقاً عند الحاجة
            
            results_dict = {
                'all_processing_results': all_processing_results,
                'all_corpus_words': all_corpus_words,
                'recognized_words': recognized_words,
                'names_weights': names_weights,
                'verbs_weights': verbs_weights,
                'processing_time': processing_time,
                'db_manager': db_manager if use_database else None,
                'stats': stats,
                'cross_validator': merged_cross_validator if use_cross_validation else None,
                'pattern_ranker': pattern_ranker if use_database else None
            }
            
            self.finished.emit(True, results_dict, "")
            
        except Exception as e:
            import traceback
            error_msg = f"خطأ في المعالجة: {str(e)}\n{traceback.format_exc()}"
            self.log_message.emit(error_msg)
            self.finished.emit(False, {}, error_msg)


class SettingsDialog(QDialog):
    """نافذة الإعدادات الشاملة"""
    def __init__(self, parent=None, current_settings=None):
        super().__init__(parent)
        self.current_settings = current_settings or {}
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        """تهيئة واجهة الإعدادات"""
        self.setWindowTitle("الإعدادات - المختار الصرفي")
        self.setGeometry(200, 200, 700, 600)
        
        # تعيين اتجاه RTL للنافذة
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        try:
            self.default_font = QFont("Sakkal Majalla", 15)
        except:
            self.default_font = QFont("Arial", 15)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # قسم خيارات المعالجة
        processing_group = QGroupBox("خيارات المعالجة")
        processing_group.setFont(self.default_font)
        processing_group.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        processing_layout = QFormLayout()
        processing_layout.setSpacing(10)
        
        # التشكيل الاختياري (CheckBox بدلاً من RadioButton)
        self.optional_tashkeel = QCheckBox("التشكيل الاختياري")
        self.optional_tashkeel.setFont(self.default_font)
        self.optional_tashkeel.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        processing_layout.addRow(self.optional_tashkeel)
        
        # مطابقة الكلمة الكاملة (CheckBox بدلاً من RadioButton)
        self.match_whole_word = QCheckBox("مطابقة الكلمة الكاملة")
        self.match_whole_word.setFont(self.default_font)
        self.match_whole_word.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        processing_layout.addRow(self.match_whole_word)
        
        # نوع المدونة (RadioButton)
        corpus_type_label = QLabel("نوع المدونة:")
        corpus_type_label.setFont(self.default_font)
        corpus_type_label.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        corpus_type_container = QWidget()
        corpus_type_container.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        corpus_type_layout = QHBoxLayout(corpus_type_container)
        corpus_type_layout.setContentsMargins(0, 0, 0, 0)
        
        self.corpus_type_list = QRadioButton("قائمة (كلمة واحدة في كل سطر)")
        self.corpus_type_list.setFont(self.default_font)
        self.corpus_type_list.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        self.corpus_type_text = QRadioButton("نص (جمل متعددة)")
        self.corpus_type_text.setFont(self.default_font)
        self.corpus_type_text.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        corpus_type_layout.addWidget(self.corpus_type_text)
        corpus_type_layout.addWidget(self.corpus_type_list)
        corpus_type_layout.addStretch()
        
        processing_layout.addRow(corpus_type_label, corpus_type_container)
        
        processing_group.setLayout(processing_layout)
        layout.addWidget(processing_group)
        
        # قسم خيارات النظام
        system_group = QGroupBox("خيارات النظام")
        system_group.setFont(self.default_font)
        system_group.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        system_layout = QVBoxLayout()
        system_layout.setSpacing(8)
        
        self.use_cache = QCheckBox("استخدام الكاش")
        self.use_database = QCheckBox("استخدام قاعدة البيانات")
        self.generate_report = QCheckBox("توليد التقارير")
        self.use_cross_validation = QCheckBox("التحقق التبادلي")
        
        for checkbox in [self.use_cache, self.use_database, self.generate_report, self.use_cross_validation]:
            checkbox.setFont(self.default_font)
            checkbox.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
            system_layout.addWidget(checkbox)
        
        system_group.setLayout(system_layout)
        layout.addWidget(system_group)
        
        # قسم مسارات الملفات
        paths_group = QGroupBox("مسارات الملفات")
        paths_group.setFont(self.default_font)
        paths_group.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        paths_layout = QFormLayout()
        paths_layout.setSpacing(10)
        # محاذاة التسميات لليمين
        paths_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        self.database_folder = QLineEdit()
        self.corpus_folder = QLineEdit()
        self.names_results_dir = QLineEdit()
        self.verbs_results_dir = QLineEdit()
        
        for line_edit in [self.database_folder, self.corpus_folder, 
                         self.names_results_dir, self.verbs_results_dir]:
            line_edit.setFont(self.default_font)
            line_edit.setMinimumHeight(30)
            line_edit.setMinimumWidth(350)  # نصف عرض النافذة (700/2 = 350)
            line_edit.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        paths_layout.addRow("مجلد قاعدة البيانات:", self.database_folder)
        paths_layout.addRow("مجلد المدونة:", self.corpus_folder)
        paths_layout.addRow("مجلد نتائج الأسماء:", self.names_results_dir)
        paths_layout.addRow("مجلد نتائج الأفعال:", self.verbs_results_dir)
        
        paths_group.setLayout(paths_layout)
        layout.addWidget(paths_group)
        
        # أزرار
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # تطبيق الأنماط
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
            }
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
                left: 10px;
                padding: 0 5px;
            }
            QLineEdit {
                background-color: #ffffff;
                border: 1px solid #c0c0c0;
                border-radius: 3px;
                padding: 5px;
            }
            QCheckBox, QRadioButton {
                color: #000000;
            }
            QPushButton {
                background-color: #d0d0d0;
                color: #000000;
                border: 1px solid #b0b0b0;
                border-radius: 3px;
                padding: 8px 15px;
                font-size: 15px;
            }
            QPushButton:hover {
                background-color: #c0c0c0;
            }
        """)
    
    def load_settings(self):
        """تحميل الإعدادات الحالية"""
        settings = self.current_settings
        
        # خيارات المعالجة
        optional_tashkeel = settings.get('optional_tashkeel', False)
        self.optional_tashkeel.setChecked(optional_tashkeel)
        
        match_whole_word = settings.get('match_whole_word', True)
        self.match_whole_word.setChecked(match_whole_word)
        
        # نوع المدونة
        corpus_type = settings.get('corpus_type', 'list')
        if corpus_type == 'list':
            self.corpus_type_list.setChecked(True)
        else:
            self.corpus_type_text.setChecked(True)
        
        # خيارات النظام
        self.use_cache.setChecked(settings.get('use_cache', True))
        self.use_database.setChecked(settings.get('use_database', True))
        self.generate_report.setChecked(settings.get('generate_report', True))
        self.use_cross_validation.setChecked(settings.get('use_cross_validation', True))
        
        # مسارات الملفات
        self.database_folder.setText(settings.get('database_folder', 'قواعد البيانات'))
        self.corpus_folder.setText(settings.get('corpus_folder', 'قواعد البيانات/المدونة'))
        self.names_results_dir.setText(settings.get('names_results_dir', 'قواعد البيانات/النتائج_الأسماء'))
        self.verbs_results_dir.setText(settings.get('verbs_results_dir', 'قواعد البيانات/النتائج_الأفعال'))
    
    def get_settings(self):
        """الحصول على الإعدادات المحددة"""
        return {
            'optional_tashkeel': self.optional_tashkeel.isChecked(),
            'match_whole_word': self.match_whole_word.isChecked(),
            'corpus_type': 'list' if self.corpus_type_list.isChecked() else 'text',
            'use_cache': self.use_cache.isChecked(),
            'use_database': self.use_database.isChecked(),
            'generate_report': self.generate_report.isChecked(),
            'use_cross_validation': self.use_cross_validation.isChecked(),
            'database_folder': self.database_folder.text(),
            'corpus_folder': self.corpus_folder.text(),
            'names_results_dir': self.names_results_dir.text(),
            'verbs_results_dir': self.verbs_results_dir.text()
        }


class MorphologyMainWindow(QMainWindow):
    """النافذة الرئيسية للمختار الصرفي"""
    
    def __init__(self):
        super().__init__()
        self.base_dir = Path(__file__).parent
        self.settings = self.load_default_settings()
        self.names_weights = {}
        self.verbs_weights = {}
        self.all_weights = {}
        self.file_paths = []
        self.processing_worker = None
        self.db_manager = None
        self.last_results = None
        self.is_paused = False
        self.paused_state = None
        self.current_weights_tab = 'all'  # التبويب المختار حالياً: 'names', 'verbs', أو 'all'
        
        self.init_ui()
        self.load_default_paths()
    
    def load_default_settings(self):
        """تحميل الإعدادات الافتراضية"""
        return {
            'optional_tashkeel': False,
            'match_whole_word': True,
            # corpus_type تم إزالته - يتم الاكتشاف تلقائياً لكل ملف
            'use_cache': True,
            'use_database': True,
            'generate_report': True,
            'use_cross_validation': True,
            'database_folder': 'قواعد البيانات',
            'corpus_folder': 'قواعد البيانات/المدونة',
            'names_results_dir': 'قواعد البيانات/النتائج_الأسماء',
            'verbs_results_dir': 'قواعد البيانات/النتائج_الأفعال'
        }
    
    def load_default_paths(self):
        """تحميل المسارات الافتراضية"""
        database_folder = self.settings['database_folder']
        # تحويل المسار النسبي إلى مطلق إذا لزم الأمر
        if not os.path.isabs(database_folder):
            database_folder = os.path.join(self.base_dir, database_folder)
        self.settings['symbols_file_path'] = os.path.join(database_folder, "الخريطة.txt")
        self.settings['tags_file_path'] = os.path.join(database_folder, "0.3 الوسم.txt")
        self.settings['names_weights_file'] = os.path.join(database_folder, "0.3 أوزان_الأسماء.txt")
        self.settings['verbs_weights_file'] = os.path.join(database_folder, "0.3 أوزان_الأفعال.txt")
        self.settings['names_affixes_file'] = os.path.join(database_folder, "0.3 سوابق ولواحق_أسماء.txt")
        self.settings['verbs_affixes_file'] = os.path.join(database_folder, "0.3 سوابق ولواحق_أفعال.txt")
    
    def init_ui(self):
        """تهيئة الواجهة"""
        self.setWindowTitle("المختار الصرفي - نظام التحليل الصرفي")
        self.setGeometry(50, 50, 1600, 950)
        
        # تعيين الخط الافتراضي (Sakkal Majalla)
        try:
            self.default_font = QFont("Sakkal Majalla", 15)
            self.default_font.setBold(False)
        except:
            # استخدام خط عربي بديل
            self.default_font = QFont("Arial", 15)
            self.default_font.setBold(False)
        
        # الويدجت المركزي
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        central_widget.setStyleSheet("background-color: #f5f5f5;")
        
        # التخطيط الرئيسي (عمودي)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # ========== شريط الأزرار (صف واحد) ==========
        buttons_container = QWidget()
        buttons_container.setStyleSheet("background-color: #e8e8e8; border-radius: 3px;")
        # تعيين الاتجاه من اليمين لليسار (RTL) للـ widget
        buttons_container.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        buttons_layout = QHBoxLayout(buttons_container)
        buttons_layout.setSpacing(8)
        buttons_layout.setContentsMargins(10, 10, 10, 10)
        
        # ترتيب الأزرار (يبقى كما هو)
        # الإعدادات
        self.btn_settings = self.create_button("الإعدادات", self.open_settings)
        buttons_layout.addWidget(self.btn_settings)
        
        # استيراد الأوزان
        self.btn_import_weights = self.create_button("استيراد الأوزان", self.import_weights)
        buttons_layout.addWidget(self.btn_import_weights)
        
        # اختيار المدونة
        self.btn_select_corpus = self.create_button("اختيار المدونة", self.select_corpus)
        buttons_layout.addWidget(self.btn_select_corpus)
        
        # تحديث
        self.btn_refresh = self.create_button("تحديث", self.refresh_weights)
        buttons_layout.addWidget(self.btn_refresh)
        
        # بدء التحليل
        self.btn_start_analysis = self.create_button("بدء التحليل", self.start_analysis)
        buttons_layout.addWidget(self.btn_start_analysis)
        
        # إيقاف
        self.btn_stop = self.create_button("إيقاف", self.stop_analysis)
        self.btn_stop.setEnabled(False)
        buttons_layout.addWidget(self.btn_stop)
        
        # استئناف
        self.btn_resume = self.create_button("استئناف", self.resume_analysis)
        self.btn_resume.setEnabled(False)
        buttons_layout.addWidget(self.btn_resume)
        
        # مسح الكاش
        self.btn_clear_cache = self.create_button("مسح الكاش", self.clear_cache)
        buttons_layout.addWidget(self.btn_clear_cache)
        
        # فتح النتائج
        self.btn_open_results = self.create_button("فتح النتائج", self.open_results_folder)
        buttons_layout.addWidget(self.btn_open_results)
        
        # تقرير التحقق التبادلي
        self.btn_validation_report = self.create_button("تقرير التحقق", self.show_validation_report)
        buttons_layout.addWidget(self.btn_validation_report)
        
        main_layout.addWidget(buttons_container)
        
        # ========== الأعمدة السفلية (Splitter) ==========
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(20)
        splitter.setOpaqueResize(True)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #f5f5f5;
                border: none;
            }
            QSplitter::handle:hover {
                background-color: #e8e8e8;
            }
        """)
        
        # الترتيب المعكوس: النتائج (يمين) | المدخلات (وسط) | الأوزان (يسار)
        # العمود الأول: النتائج (على اليمين)
        results_widget = self.create_results_column()
        splitter.addWidget(results_widget)
        
        # العمود الثاني: المدخلات (في المنتصف)
        inputs_widget = self.create_inputs_column()
        splitter.addWidget(inputs_widget)
        
        # العمود الثالث: الأوزان (في الأخير/اليسار)
        weights_widget = self.create_weights_column()
        splitter.addWidget(weights_widget)
        
        # تعيين النسب (تكبير الأعمدة)
        splitter.setSizes([650, 600, 350])
        
        # الفواصل قابلة للسحب بدون إظهار النقاط
        # (الـ handles موجودة بشكل افتراضي ويمكن السحب عليها)
        
        main_layout.addWidget(splitter, stretch=1)
    
    def create_button(self, text, slot):
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
    
    def create_weights_column(self):
        """إنشاء عمود الأوزان"""
        widget = QWidget()
        widget.setStyleSheet("background-color: #f5f5f5;")
        widget.setLayoutDirection(Qt.LayoutDirection.RightToLeft)  # RTL للويدجت الرئيسي
        layout = QVBoxLayout(widget)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # السطر الأول: عدد الأوزان والتبويبات
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)
        # RTL يتم تطبيقه تلقائياً من الـ widget الرئيسي
        
        # عدد الأوزان
        self.weights_stats = QLabel("عدد الأوزان: 0")
        self.weights_stats.setFont(self.default_font)
        self.weights_stats.setLayoutDirection(Qt.LayoutDirection.RightToLeft)  # RTL للـ Label
        self.weights_stats.setStyleSheet("font-weight: bold; font-size: 15px; color: #666666;")
        header_layout.addWidget(self.weights_stats)
        
        header_layout.addStretch()
        
        # أزرار التبويبات
        self.btn_names_tab = QPushButton("الأسماء")
        self.btn_names_tab.setFont(self.default_font)
        self.btn_names_tab.setLayoutDirection(Qt.LayoutDirection.RightToLeft)  # RTL للزر
        self.btn_names_tab.setCheckable(True)
        self.btn_names_tab.setChecked(True)
        self.btn_names_tab.setMaximumHeight(30)
        self.btn_names_tab.setStyleSheet("""
            QPushButton {
                background-color: #d0d0d0;
                color: #000000;
                border: 1px solid #b0b0b0;
                border-radius: 3px;
                padding: 3px 10px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #c0c0c0;
            }
            QPushButton:checked {
                background-color: #a0a0a0;
                font-weight: bold;
            }
        """)
        self.btn_names_tab.clicked.connect(lambda: self.switch_weights_tab('names'))
        header_layout.addWidget(self.btn_names_tab)
        
        self.btn_verbs_tab = QPushButton("الأفعال")
        self.btn_verbs_tab.setFont(self.default_font)
        self.btn_verbs_tab.setLayoutDirection(Qt.LayoutDirection.RightToLeft)  # RTL للزر
        self.btn_verbs_tab.setCheckable(True)
        self.btn_verbs_tab.setMaximumHeight(30)
        self.btn_verbs_tab.setStyleSheet(self.btn_names_tab.styleSheet())
        self.btn_verbs_tab.clicked.connect(lambda: self.switch_weights_tab('verbs'))
        header_layout.addWidget(self.btn_verbs_tab)
        
        self.btn_all_tab = QPushButton("الكل")
        self.btn_all_tab.setFont(self.default_font)
        self.btn_all_tab.setLayoutDirection(Qt.LayoutDirection.RightToLeft)  # RTL للزر
        self.btn_all_tab.setCheckable(True)
        self.btn_all_tab.setMaximumHeight(30)
        self.btn_all_tab.setStyleSheet(self.btn_names_tab.styleSheet())
        self.btn_all_tab.clicked.connect(lambda: self.switch_weights_tab('all'))
        header_layout.addWidget(self.btn_all_tab)
        
        layout.addLayout(header_layout)
        
        # قائمة الأسماء
        self.names_list = QListWidget()
        self.names_list.setFont(self.default_font)
        self.names_list.setLayoutDirection(Qt.LayoutDirection.RightToLeft)  # RTL للقائمة
        self.names_list.setStyleSheet("""
            QListWidget {
                background-color: #ffffff;
                border: 1px solid #c0c0c0;
                color: #000000;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #e8e8e8;
            }
            QListWidget::item:selected {
                background-color: #d0d0d0;
            }
        """)
        self.names_list.itemClicked.connect(self.on_weight_selected)
        
        # قائمة الأفعال
        self.verbs_list = QListWidget()
        self.verbs_list.setFont(self.default_font)
        self.verbs_list.setLayoutDirection(Qt.LayoutDirection.RightToLeft)  # RTL للقائمة
        self.verbs_list.setStyleSheet(self.names_list.styleSheet())
        self.verbs_list.itemClicked.connect(self.on_weight_selected)
        
        # قائمة الكل
        self.all_list = QListWidget()
        self.all_list.setFont(self.default_font)
        self.all_list.setLayoutDirection(Qt.LayoutDirection.RightToLeft)  # RTL للقائمة
        self.all_list.setStyleSheet(self.names_list.styleSheet())
        self.all_list.itemClicked.connect(self.on_weight_selected)
        
        # إضافة القوائم مباشرة (سنستخدم show/hide)
        layout.addWidget(self.names_list, stretch=1)
        layout.addWidget(self.verbs_list, stretch=1)
        layout.addWidget(self.all_list, stretch=1)
        
        # إخفاء القوائم غير المختارة
        self.verbs_list.hide()
        self.all_list.hide()
        
        return widget
    
    def create_inputs_column(self):
        """إنشاء عمود المدخلات"""
        widget = QWidget()
        widget.setStyleSheet("background-color: #f5f5f5;")
        layout = QVBoxLayout(widget)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # العنوان
        title = QLabel("ملفات المدونة")
        title.setFont(self.default_font)
        title.setStyleSheet("font-weight: bold; font-size: 15px; color: #000000;")
        layout.addWidget(title)
        
        # قائمة الملفات
        self.files_list = QListWidget()
        self.files_list.setFont(self.default_font)
        self.files_list.setStyleSheet("""
            QListWidget {
                background-color: #ffffff;
                border: 1px solid #c0c0c0;
                color: #000000;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #e8e8e8;
            }
        """)
        layout.addWidget(self.files_list)
        
        # شريط التقدم
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
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
        
        # سجل العمليات
        log_label = QLabel("سجل العمليات")
        log_label.setFont(self.default_font)
        log_label.setStyleSheet("font-weight: bold; color: #000000;")
        layout.addWidget(log_label)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(self.default_font)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #ffffff;
                border: 1px solid #c0c0c0;
                color: #000000;
                font-size: 15px;
            }
        """)
        layout.addWidget(self.log_text, stretch=1)  # إضافة stretch factor
        
        return widget
    
    def create_results_column(self):
        """إنشاء عمود النتائج"""
        widget = QWidget()
        widget.setStyleSheet("background-color: #f5f5f5;")
        layout = QVBoxLayout(widget)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # العنوان
        title = QLabel("نتائج التحليل")
        title.setFont(self.default_font)
        title.setStyleSheet("font-weight: bold; font-size: 15px; color: #000000;")
        layout.addWidget(title)
        
        # الإحصائيات السريعة
        self.stats_label = QLabel("لا توجد نتائج بعد")
        self.stats_label.setFont(self.default_font)
        self.stats_label.setStyleSheet("""
            background-color: #ffffff;
            border: 1px solid #c0c0c0;
            padding: 10px;
            color: #000000;
        """)
        layout.addWidget(self.stats_label)
        
        # عرض النتائج
        results_label = QLabel("تفاصيل النتائج")
        results_label.setFont(self.default_font)
        results_label.setStyleSheet("font-weight: bold; color: #000000;")
        layout.addWidget(results_label)
        
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setFont(self.default_font)
        self.results_text.setStyleSheet("""
            QTextEdit {
                background-color: #ffffff;
                border: 1px solid #c0c0c0;
                color: #000000;
                font-size: 15px;
            }
        """)
        layout.addWidget(self.results_text, stretch=1)  # إضافة stretch factor
        
        return widget
    
    def create_small_button(self, text, slot):
        """إنشاء زر صغير"""
        btn = QPushButton(text)
        btn.setFont(self.default_font)
        btn.setMinimumHeight(35)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #e0e0e0;
                color: #000000;
                border: 1px solid #c0c0c0;
                border-radius: 3px;
                padding: 5px 10px;
                font-size: 15px;
            }
            QPushButton:hover {
                background-color: #d0d0d0;
            }
        """)
        btn.clicked.connect(slot)
        return btn
    
    # ========== دوال الأزرار ==========
    
    def import_weights(self):
        """استيراد الأوزان"""
        database_folder = self.settings['database_folder']
        # تحويل المسار النسبي إلى مطلق إذا لزم الأمر
        if not os.path.isabs(database_folder):
            database_folder = os.path.join(self.base_dir, database_folder)
        names_file = os.path.join(database_folder, "0.3 أوزان_الأسماء.txt")
        verbs_file = os.path.join(database_folder, "0.3 أوزان_الأفعال.txt")
        
        if not os.path.exists(names_file) or not os.path.exists(verbs_file):
            QMessageBox.warning(
                self, "تحذير",
                f"لم يتم العثور على ملفات الأوزان في:\n{database_folder}\n\n"
                "يرجى التأكد من المسار في الإعدادات."
            )
            return
        
        try:
            # إنشاء FileManager مؤقت
            # corpus_type قيمة افتراضية (لن تُستخدم - يتم الاكتشاف تلقائياً)
            temp_file_manager = FileManager(
                corpus_type=self.settings.get('corpus_type', 'list'),
                match_whole_word=self.settings['match_whole_word'],
                affixes_data={'prefixes': [], 'suffixes': []},
                tags_map={},
                db_manager=None,
                cache_manager=None,
                pattern_ranker=None,
                cross_validator=None
            )
            
            self.names_weights = temp_file_manager.read_weights_and_derived_words(names_file)
            temp_file_manager.affixes_data = {'prefixes': [], 'suffixes': []}
            self.verbs_weights = temp_file_manager.read_weights_and_derived_words(verbs_file)
            self.all_weights = {**self.names_weights, **self.verbs_weights}
            
            self.update_weights_display()
            self.log_message(f"تم تحميل {len(self.all_weights)} وزن صرفي")
            QMessageBox.information(
                self, "نجح",
                f"تم تحميل الأوزان بنجاح:\n"
                f"الأسماء: {len(self.names_weights)}\n"
                f"الأفعال: {len(self.verbs_weights)}\n"
                f"الإجمالي: {len(self.all_weights)}"
            )
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل تحميل الأوزان:\n{str(e)}")
    
    def update_weights_display(self):
        """تحديث عرض الأوزان"""
        self.names_list.clear()
        self.verbs_list.clear()
        self.all_list.clear()
        
        for weight, derived in self.names_weights.items():
            item_text = f"{weight}"
            if derived:
                item_text += f" ({len(derived)} مشتق)"
            self.names_list.addItem(item_text)
            self.all_list.addItem(f"[اسم] {item_text}")
        
        for weight, derived in self.verbs_weights.items():
            item_text = f"{weight}"
            if derived:
                item_text += f" ({len(derived)} مشتق)"
            self.verbs_list.addItem(item_text)
            self.all_list.addItem(f"[فعل] {item_text}")
        
        total = len(self.all_weights)
        names_count = len(self.names_weights)
        verbs_count = len(self.verbs_weights)
        self.weights_stats.setText(
            f"عدد الأوزان: {total} (أسماء: {names_count}, أفعال: {verbs_count})"
        )
    
    def select_corpus(self):
        """اختيار مجلد المدونة"""
        corpus_folder = self.settings['corpus_folder']
        # تحويل المسار النسبي إلى مطلق إذا لزم الأمر
        if not os.path.isabs(corpus_folder):
            corpus_folder = os.path.join(self.base_dir, corpus_folder)
        if not os.path.exists(corpus_folder):
            corpus_folder = str(self.base_dir)
        
        folder = QFileDialog.getExistingDirectory(
            self,
            "اختيار مجلد المدونة",
            corpus_folder
        )
        
        if folder:
            # قراءة جميع ملفات .txt و .docx من المجلد
            self.file_paths = []
            for file_name in os.listdir(folder):
                file_path = os.path.join(folder, file_name)
                if os.path.isfile(file_path):
                    # دعم ملفات .txt و .docx فقط
                    if file_name.lower().endswith(('.txt', '.docx')):
                        self.file_paths.append(file_path)
            
            if self.file_paths:
                self.files_list.clear()
                for file_path in self.file_paths:
                    file_name = os.path.basename(file_path)
                    file_size = os.path.getsize(file_path)
                    size_mb = file_size / (1024 * 1024)
                    file_ext = os.path.splitext(file_name)[1].lower()
                    self.files_list.addItem(f"{file_name} ({size_mb:.2f} MB) [{file_ext}]")
                
                self.log_message(f"تم اختيار مجلد المدونة: {folder}")
                self.log_message(f"تم العثور على {len(self.file_paths)} ملف (.txt و .docx)")
            else:
                QMessageBox.warning(
                    self, "تحذير",
                    f"لم يتم العثور على ملفات .txt أو .docx في المجلد:\n{folder}"
                )
    
    def start_analysis(self):
        """بدء التحليل"""
        if not self.all_weights:
            QMessageBox.warning(self, "تحذير", "يرجى استيراد الأوزان أولاً")
            return
        
        if not self.file_paths:
            QMessageBox.warning(self, "تحذير", "يرجى اختيار ملفات المدونة أولاً")
            return
        
        # تعطيل الأزرار
        self.btn_start_analysis.setEnabled(False)
        self.btn_import_weights.setEnabled(False)
        self.btn_select_corpus.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.btn_resume.setEnabled(False)
        self.btn_settings.setEnabled(False)
        self.is_paused = False
        
        # إظهار شريط التقدم
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # indeterminate
        
        # إعداد التكوين
        # تحويل المسارات النسبية إلى مطلقة
        database_folder = self.settings['database_folder']
        if not os.path.isabs(database_folder):
            database_folder = os.path.join(self.base_dir, database_folder)
        
        names_results_dir = self.settings['names_results_dir']
        if not os.path.isabs(names_results_dir):
            names_results_dir = os.path.join(self.base_dir, names_results_dir)
        
        verbs_results_dir = self.settings['verbs_results_dir']
        if not os.path.isabs(verbs_results_dir):
            verbs_results_dir = os.path.join(self.base_dir, verbs_results_dir)
        
        config = {
            **self.settings,
            'file_paths': self.file_paths,
            'names_weights_file': os.path.join(database_folder, "0.3 أوزان_الأسماء.txt"),
            'verbs_weights_file': os.path.join(database_folder, "0.3 أوزان_الأفعال.txt"),
            'names_affixes_file': os.path.join(database_folder, "0.3 سوابق ولواحق_أسماء.txt"),
            'verbs_affixes_file': os.path.join(database_folder, "0.3 سوابق ولواحق_أفعال.txt"),
            'symbols_file_path': os.path.join(database_folder, "الخريطة.txt"),
            'tags_file_path': os.path.join(database_folder, "0.3 الوسم.txt"),
            'names_results_dir': names_results_dir,
            'verbs_results_dir': verbs_results_dir,
            'selected_weights_tab': self.current_weights_tab,  # التبويب المختار: 'names', 'verbs', أو 'all'
            'corpus_type': self.settings.get('corpus_type', 'list')
        }
        
        # إنشاء Worker
        self.processing_worker = MorphologyWorker(config)
        self.processing_worker.progress.connect(self.on_progress)
        self.processing_worker.log_message.connect(self.log_message)
        self.processing_worker.finished.connect(self.on_analysis_finished)
        self.processing_worker.start()
        
        self.log_message("بدء التحليل الصرفي...")
    
    def stop_analysis(self):
        """إيقاف التحليل"""
        if self.processing_worker:
            self.processing_worker.stop()
            self.is_paused = True
            self.btn_stop.setEnabled(False)
            self.btn_resume.setEnabled(True)
            self.log_message("تم إيقاف المعالجة. يمكنك استئنافها لاحقاً.")
    
    def resume_analysis(self):
        """استئناف التحليل"""
        if self.is_paused:
            self.log_message("استئناف التحليل...")
            # إعادة تشغيل التحليل (multiprocessing لا يدعم الاستئناف الحقيقي)
            self.is_paused = False
            self.btn_resume.setEnabled(False)
            self.start_analysis()
    
    def on_progress(self, message, current, total):
        """تحديث التقدم"""
        if total > 0:
            self.progress_bar.setRange(0, total)
            self.progress_bar.setValue(current)
        else:
            self.progress_bar.setRange(0, 0)
    
    def on_analysis_finished(self, success, results, error):
        """عند انتهاء التحليل"""
        # تفعيل الأزرار
        self.btn_start_analysis.setEnabled(True)
        self.btn_import_weights.setEnabled(True)
        self.btn_select_corpus.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.btn_resume.setEnabled(False)
        self.btn_settings.setEnabled(True)
        self.is_paused = False
        
        self.progress_bar.setVisible(False)
        
        if success:
            self.log_message("✅ اكتمل التحليل بنجاح!")
            
            # حفظ النتائج
            self.last_results = results
            
            # حفظ مرجع قاعدة البيانات
            if results.get('db_manager'):
                self.db_manager = results['db_manager']
            
            # تحديث الإحصائيات
            self.update_statistics(results)
            
            # توليد التقارير إذا كان مفعلاً
            if self.settings.get('generate_report', True) and results.get('db_manager'):
                self.generate_reports(results)
        else:
            self.log_message(f"❌ فشل التحليل: {error}")
            QMessageBox.critical(self, "خطأ", f"فشل التحليل:\n{error}")
        
        # تنظيف Worker
        if self.processing_worker:
            self.processing_worker = None
    
    def update_statistics(self, results):
        """تحديث الإحصائيات"""
        stats_text = "إحصائيات سريعة:\n"
        stats_text += "─" * 30 + "\n"
        
        # استخدام الإحصائيات المحفوظة أو جلبها من قاعدة البيانات
        stats = results.get('stats')
        if not stats and results.get('db_manager'):
            try:
                stats = results['db_manager'].get_statistics()
            except:
                stats = None
        
        if stats:
            stats_text += f"إجمالي النتائج: {stats.get('total_results', 0):,}\n"
            stats_text += f"الكلمات الفريدة: {stats.get('unique_words', 0):,}\n"
            stats_text += f"عدد الأوزان: {stats.get('total_patterns', 0):,}\n"
            stats_text += f"عدد الجذور: {stats.get('total_roots', 0):,}\n"
        
        if 'processing_time' in results:
            stats_text += f"وقت المعالجة: {results['processing_time']:.2f} ثانية\n"
        
        if 'all_corpus_words' in results and 'recognized_words' in results:
            total = len(results['all_corpus_words'])
            recognized = len(results['recognized_words'])
            percent = (recognized / total * 100) if total > 0 else 0
            stats_text += f"\nالتغطية:\n"
            stats_text += f"المتعرّف عليها: {recognized:,} / {total:,} ({percent:.2f}%)\n"
        
        # إحصائيات التحقق التبادلي
        if results.get('cross_validator'):
            try:
                validation_report = results['cross_validator'].get_validation_report()
                # استخراج الأرقام من التقرير
                import re
                total_validated = re.search(r'إجمالي الكلمات المحللة: (\d+)', validation_report)
                valid_count = re.search(r'التحليلات الصحيحة: (\d+)', validation_report)
                if total_validated and valid_count:
                    total_v = int(total_validated.group(1))
                    valid_v = int(valid_count.group(1))
                    valid_percent = (valid_v / total_v * 100) if total_v > 0 else 0
                    stats_text += f"\nالتحقق التبادلي:\n"
                    stats_text += f"الصحيحة: {valid_v:,} / {total_v:,} ({valid_percent:.1f}%)\n"
            except:
                pass
        
        self.stats_label.setText(stats_text)
    
    def switch_weights_tab(self, tab_name):
        """تبديل التبويب في عمود الأوزان"""
        # حفظ التبويب المختار
        self.current_weights_tab = tab_name
        
        # إلغاء تحديد جميع الأزرار
        self.btn_names_tab.setChecked(False)
        self.btn_verbs_tab.setChecked(False)
        self.btn_all_tab.setChecked(False)
        
        # إخفاء جميع القوائم
        self.names_list.hide()
        self.verbs_list.hide()
        self.all_list.hide()
        
        # إظهار القائمة المختارة وتحديد الزر
        if tab_name == 'names':
            self.names_list.show()
            self.btn_names_tab.setChecked(True)
        elif tab_name == 'verbs':
            self.verbs_list.show()
            self.btn_verbs_tab.setChecked(True)
        elif tab_name == 'all':
            self.all_list.show()
            self.btn_all_tab.setChecked(True)
    
    def on_weight_selected(self, item):
        """عند اختيار وزن"""
        weight_text = item.text()
        # استخراج اسم الوزن (إزالة [اسم] أو [فعل] إن وجد)
        weight = weight_text.split('] ')[-1].split(' (')[0]
        
        # البحث عن النتائج لهذا الوزن
        if hasattr(self, 'last_results') and self.last_results is not None:
            results = self.last_results.get('all_processing_results', [])
            for result_data in results:
                if result_data['weight'] == weight:
                    self.display_weight_results(result_data)
                    break
        else:
            # لا توجد نتائج بعد - إظهار رسالة
            self.results_text.setPlainText(f"الوزن المحدد: {weight}\n\nلا توجد نتائج بعد.\nيرجى تشغيل التحليل أولاً.")
    
    def display_weight_results(self, result_data):
        """عرض نتائج وزن معين"""
        weight = result_data['weight']
        results = result_data['results']
        count = result_data['count']
        
        text = f"الوزن: {weight}\n"
        text += f"عدد النتائج: {count}\n"
        text += "─" * 50 + "\n\n"
        
        # عرض أول 100 نتيجة
        for i, (prefix, root, suffix) in enumerate(results[:100]):
            matched_word = prefix + root + suffix
            text += f"{i+1}. {matched_word}\n"
            text += f"   الجذر: {root} | السابق: {prefix or '#'} | اللاحق: {suffix or '#'}\n\n"
        
        if len(results) > 100:
            text += f"\n... و {len(results) - 100} نتيجة أخرى\n"
        
        self.results_text.setPlainText(text)
    
    def open_settings(self):
        """فتح نافذة الإعدادات"""
        dialog = SettingsDialog(self, self.settings)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.settings = dialog.get_settings()
            self.load_default_paths()
            self.log_message("تم حفظ الإعدادات")
    
    def open_results_folder(self):
        """فتح مجلد النتائج"""
        import subprocess
        import platform
        
        results_dir = self.settings.get('names_results_dir', 'قواعد البيانات/النتائج_الأسماء')
        # تحويل المسار النسبي إلى مطلق إذا لزم الأمر
        if not os.path.isabs(results_dir):
            results_dir = os.path.join(self.base_dir, results_dir)
        if not os.path.exists(results_dir):
            results_dir = self.base_dir
        
        try:
            if platform.system() == 'Windows':
                os.startfile(results_dir)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.Popen(['open', results_dir])
            else:  # Linux
                subprocess.Popen(['xdg-open', results_dir])
        except Exception as e:
            QMessageBox.warning(self, "تحذير", f"لم يتم فتح المجلد:\n{str(e)}")
    
    def clear_cache(self):
        """مسح الكاش"""
        reply = QMessageBox.question(
            self, "تأكيد",
            "هل أنت متأكد من مسح الكاش؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                cache_manager = CacheManager()
                cache_manager.clear()
                self.log_message("تم مسح الكاش بنجاح")
                QMessageBox.information(self, "نجح", "تم مسح الكاش بنجاح")
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"فشل مسح الكاش:\n{str(e)}")
    
    def refresh_weights(self):
        """تحديث عرض الأوزان"""
        self.import_weights()
    
    def show_validation_report(self):
        """عرض تقرير التحقق التبادلي"""
        if not hasattr(self, 'last_results') or not self.last_results:
            QMessageBox.warning(self, "تحذير", "لا توجد نتائج لعرض تقرير التحقق")
            return
        
        cross_validator = self.last_results.get('cross_validator')
        if not cross_validator:
            QMessageBox.information(
                self, "معلومة",
                "التحقق التبادلي غير مفعّل.\nيرجى تفعيله من الإعدادات."
            )
            return
        
        try:
            validation_report = cross_validator.get_validation_report()
            
            # عرض التقرير في نافذة منفصلة
            dialog = QDialog(self)
            dialog.setWindowTitle("تقرير التحقق التبادلي")
            dialog.setGeometry(200, 200, 800, 600)
            dialog.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
            
            layout = QVBoxLayout(dialog)
            
            text_edit = QTextEdit()
            text_edit.setReadOnly(True)
            text_edit.setFont(self.default_font)
            text_edit.setPlainText(validation_report)
            text_edit.setStyleSheet("""
                QTextEdit {
                    background-color: #ffffff;
                    border: 1px solid #c0c0c0;
                    color: #000000;
                    font-size: 15px;
                }
            """)
            layout.addWidget(text_edit)
            
            button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
            button_box.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
            button_box.rejected.connect(dialog.close)
            layout.addWidget(button_box)
            
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل عرض تقرير التحقق:\n{str(e)}")
    
    def generate_reports(self, results):
        """توليد التقارير"""
        if not results.get('db_manager'):
            return
        
        try:
            report_generator = ReportGenerator(results['db_manager'])
            stats = results['db_manager'].get_statistics()
            
            coverage_info = report_generator.generate_coverage_outputs(
                all_words_set=results.get('all_corpus_words', set()),
                recognized_set=results.get('recognized_words', set())
            )
            
            stats['processing_time'] = results.get('processing_time', 0)
            report_generator.generate_text_report(stats, coverage=coverage_info)
            
            self.log_message("✅ تم إنشاء التقارير بنجاح")
        except Exception as e:
            self.log_message(f"⚠️ تحذير: فشل إنشاء بعض التقارير: {str(e)}")
    
    def log_message(self, message):
        """إضافة رسالة للسجل"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        # التمرير للأسفل
        cursor = self.log_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.log_text.setTextCursor(cursor)
    
    def closeEvent(self, event):
        """عند إغلاق النافذة"""
        # إيقاف المعالجة إن كانت جارية
        if self.processing_worker and self.processing_worker.isRunning():
            reply = QMessageBox.question(
                self, "تأكيد",
                "المعالجة جارية. هل تريد الإغلاق؟",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return
            else:
                self.processing_worker.stop()
                self.processing_worker.wait(3000)  # انتظار 3 ثوان
        
        # إغلاق قاعدة البيانات
        if self.db_manager:
            try:
                self.db_manager.close()
            except:
                pass
        
        event.accept()


def main():
    """تشغيل التطبيق"""
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # تعيين الخط الافتراضي (Sakkal Majalla)
    try:
        font = QFont("Sakkal Majalla", 14)
    except:
        font = QFont("Arial", 14)
    app.setFont(font)
    
    window = MorphologyMainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

