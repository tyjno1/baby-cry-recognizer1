# -*- coding: utf-8 -*-
"""
Baby Cry Recognizer - Kivy Android App
"""

import os

import threading




from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.checkbox import CheckBox
from kivy.uix.slider import Slider
from kivy.uix.progressbar import ProgressBar
from kivy.uix.widget import Widget
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.graphics import Color, Rectangle
from kivy.utils import get_color_from_hex

import numpy as np

from config import NEED_CATEGORIES, MATCH_THRESHOLD, BEHAVIOR_PATTERNS, REFERENCE_GUIDE
from database import init_db, save_feedback, get_all_feedback, get_feedback_count, get_setting, set_setting
from audio_processor import extract_features, find_best_match, generate_feature_description
from ai_client import DeepSeekClient
from android_audio import record_audio_mobile


# ─── Color Theme ───
COLOR_PRIMARY = get_color_from_hex("#2196F3")
COLOR_SUCCESS = get_color_from_hex("#4CAF50")
COLOR_ERROR = get_color_from_hex("#F44336")
COLOR_WARNING = get_color_from_hex("#FF9800")
COLOR_BG = get_color_from_hex("#F5F5F5")
COLOR_CARD = get_color_from_hex("#FFFFFF")
COLOR_TEXT = get_color_from_hex("#212121")
COLOR_TEXT_SECONDARY = get_color_from_hex("#757575")


class ColoredLabel(Label):
    """Label with background color support"""
    def __init__(self, bg_color=None, **kwargs):
        super().__init__(**kwargs)
        if bg_color:
            with self.canvas.before:
                Color(*bg_color)
                self.rect = Rectangle(size=self.size, pos=self.pos)
            self.bind(size=self._update_rect, pos=self._update_rect)

    def _update_rect(self, *args):
        self.rect.size = self.size
        self.rect.pos = self.pos


class CardWidget(BoxLayout):
    """Card-style container"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.padding = dp(12)
        self.spacing = dp(8)
        self.size_hint_y = None
        with self.canvas.before:
            Color(*COLOR_CARD)
            self.rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_rect, pos=self._update_rect)

    def _update_rect(self, *args):
        self.rect.size = self.size
        self.rect.pos = self.pos


class BehaviorCheckBox(BoxLayout):
    """Checkbox with label for behavior patterns"""
    def __init__(self, code, name, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.height = dp(36)
        self.spacing = dp(4)
        self.code = code

        self.checkbox = CheckBox(size_hint_x=None, width=dp(30))
        self.checkbox.bind(active=self.on_active)
        self.add_widget(self.checkbox)

        self.label = Label(
            text=name,
            size_hint_x=1,
            halign="left",
            valign="middle",
            font_size=dp(12),
            color=COLOR_TEXT
        )
        self.label.bind(size=self.label.setter("text_size"))
        self.add_widget(self.label)

    def on_active(self, instance, value):
        app = App.get_running_app()
        if value:
            if self.code not in app.selected_behaviors:
                app.selected_behaviors.append(self.code)
        else:
            if self.code in app.selected_behaviors:
                app.selected_behaviors.remove(self.code)


class SectionHeader(Label):
    """Section title"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.font_size = dp(16)
        self.bold = True
        self.color = COLOR_PRIMARY
        self.size_hint_y = None
        self.height = dp(36)
        self.halign = "left"
        self.valign = "middle"
        self.bind(size=self.setter("text_size"))


class MainScreen(BoxLayout):
    """Main application screen"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.padding = dp(8)
        self.spacing = dp(8)

        # Build UI
        self._build_ui()

    def _build_ui(self):
        # Scrollable main content
        scroll = ScrollView(size_hint=(1, 1))
        self.content = BoxLayout(
            orientation="vertical",
            spacing=dp(8),
            padding=dp(8),
            size_hint_y=None
        )
        self.content.bind(minimum_height=self.content.setter("height"))

        # ─── Title ───
        title = Label(
            text="👶 婴儿哭声意图理解器",
            font_size=dp(20),
            bold=True,
            color=COLOR_PRIMARY,
            size_hint_y=None,
            height=dp(44)
        )
        self.content.add_widget(title)

        subtitle = Label(
            text="听懂哭声，告别猜测——让每一次回应都准确、及时、安心",
            font_size=dp(11),
            color=COLOR_TEXT_SECONDARY,
            size_hint_y=None,
            height=dp(24)
        )
        self.content.add_widget(subtitle)

        # ─── Settings Section ───
        self.content.add_widget(SectionHeader(text="⚙️ 设置"))

        settings_card = CardWidget()

        # API Key
        api_label = Label(
            text="DeepSeek API Key:",
            font_size=dp(12),
            color=COLOR_TEXT,
            size_hint_y=None,
            height=dp(22),
            halign="left"
        )
        api_label.bind(size=api_label.setter("text_size"))
        settings_card.add_widget(api_label)

        self.api_key_input = TextInput(
            text=os.getenv("DEEPSEEK_API_KEY", ""),
            password=True,
            multiline=False,
            size_hint_y=None,
            height=dp(36),
            font_size=dp(12)
        )
        settings_card.add_widget(self.api_key_input)

        # Match threshold
        threshold_box = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(40),
            spacing=dp(8)
        )

        threshold_label = Label(
            text="匹配阈值:",
            font_size=dp(12),
            size_hint_x=0.25,
            color=COLOR_TEXT
        )
        threshold_box.add_widget(threshold_label)

        default_threshold = float(get_setting("match_threshold", str(MATCH_THRESHOLD)))
        self.threshold_slider = Slider(
            min=0.0,
            max=1.0,
            value=default_threshold,
            step=0.05,
            size_hint_x=0.55
        )
        self.threshold_slider.bind(value=self.on_threshold_change)
        threshold_box.add_widget(self.threshold_slider)

        self.threshold_value_label = Label(
            text=f"{default_threshold:.2f}",
            font_size=dp(12),
            size_hint_x=0.2,
            color=COLOR_TEXT
        )
        threshold_box.add_widget(self.threshold_value_label)

        settings_card.add_widget(threshold_box)

        # Feedback count
        count = get_feedback_count()
        self.feedback_count_label = Label(
            text=f"📊 反馈记录数: {count} 条",
            font_size=dp(12),
            color=COLOR_SUCCESS if count > 0 else COLOR_TEXT_SECONDARY,
            size_hint_y=None,
            height=dp(22),
            halign="left"
        )
        self.feedback_count_label.bind(size=self.feedback_count_label.setter("text_size"))
        settings_card.add_widget(self.feedback_count_label)

        self.content.add_widget(settings_card)

        # ─── Behavior Selection ───
        self.content.add_widget(SectionHeader(text="👀 选择行为表现（可选）"))

        behaviors_card = CardWidget()
        behaviors_grid = GridLayout(
            cols=2,
            spacing=dp(4),
            size_hint_y=None,
            row_default_height=dp(36),
            row_force_default=True
        )

        num_behaviors = len(BEHAVIOR_PATTERNS)
        behaviors_grid.height = dp(36) * ((num_behaviors + 1) // 2)

        for code, name in BEHAVIOR_PATTERNS.items():
            cb = BehaviorCheckBox(code, name)
            behaviors_grid.add_widget(cb)

        behaviors_card.add_widget(behaviors_grid)
        self.content.add_widget(behaviors_card)

        # ─── Selected behaviors display ───
        self.selected_behaviors_label = Label(
            text="",
            font_size=dp(11),
            color=COLOR_PRIMARY,
            size_hint_y=None,
            height=dp(0),
            halign="left"
        )
        self.selected_behaviors_label.bind(size=self.selected_behaviors_label.setter("text_size"))
        self.content.add_widget(self.selected_behaviors_label)

        # ─── Record Button ───
        self.record_btn = Button(
            text="🎤 开始录音（5秒）",
            size_hint=(1, None),
            height=dp(48),
            background_color=COLOR_PRIMARY,
            color=(1, 1, 1, 1),
            font_size=dp(15),
            bold=True
        )
        self.record_btn.bind(on_press=self.on_record)
        self.content.add_widget(self.record_btn)

        # ─── Status Spinner ───
        self.status_label = Label(
            text="",
            font_size=dp(12),
            color=COLOR_TEXT_SECONDARY,
            size_hint_y=None,
            height=dp(0)
        )
        self.content.add_widget(self.status_label)

        # ─── Result Section (initially hidden) ───
        self.result_section = BoxLayout(
            orientation="vertical",
            spacing=dp(6),
            size_hint_y=None,
            height=dp(0)
        )

        self.result_card = CardWidget()
        self.result_card.size_hint_y = None
        self.result_card.height = dp(0)

        self.result_title = Label(
            text="",
            font_size=dp(16),
            bold=True,
            size_hint_y=None,
            height=dp(0)
        )
        self.result_card.add_widget(self.result_title)

        self.confidence_bar = ProgressBar(
            max=1.0,
            value=0,
            size_hint_y=None,
            height=dp(0)
        )
        self.result_card.add_widget(self.confidence_bar)

        self.confidence_label = Label(
            text="",
            font_size=dp(11),
            color=COLOR_TEXT_SECONDARY,
            size_hint_y=None,
            height=dp(0)
        )
        self.result_card.add_widget(self.confidence_label)

        self.match_source_label = Label(
            text="",
            font_size=dp(11),
            size_hint_y=None,
            height=dp(0)
        )
        self.result_card.add_widget(self.match_source_label)

        self.reason_label = Label(
            text="",
            font_size=dp(11),
            color=COLOR_TEXT,
            size_hint_y=None,
            height=dp(0),
            halign="left"
        )
        self.reason_label.bind(size=self.reason_label.setter("text_size"))
        self.result_card.add_widget(self.reason_label)

        # Feedback buttons
        feedback_box = BoxLayout(
            orientation="horizontal",
            spacing=dp(8),
            size_hint_y=None,
            height=dp(0)
        )

        self.correct_btn = Button(
            text="✅ 结果正确",
            background_color=COLOR_SUCCESS,
            color=(1, 1, 1, 1),
            size_hint_x=0.5,
            font_size=dp(12)
        )
        self.correct_btn.bind(on_press=self.on_correct_feedback)
        feedback_box.add_widget(self.correct_btn)

        # Correction spinner
        self.correction_spinner = Spinner(
            text="纠正为...",
            values=list(NEED_CATEGORIES.values()),
            size_hint_x=0.5,
            font_size=dp(11),
            background_color=COLOR_WARNING,
            color=(1, 1, 1, 1)
        )
        self.correction_spinner.bind(text=self.on_correction_select)
        feedback_box.add_widget(self.correction_spinner)

        self.result_card.add_widget(feedback_box)

        self.result_section.add_widget(self.result_card)
        self.content.add_widget(self.result_section)

        # ─── Reference Guide ───
        self.content.add_widget(SectionHeader(text="📖 资料参考"))

        for code, info in REFERENCE_GUIDE.items():
            guide_card = CardWidget()
            guide_title = Label(
                text=f"📉 {info['title']}",
                font_size=dp(14),
                bold=True,
                color=COLOR_TEXT,
                size_hint_y=None,
                height=dp(28),
                halign="left"
            )
            guide_title.bind(size=guide_title.setter("text_size"))
            guide_card.add_widget(guide_title)

            cry_label = Label(
                text=f"哭声特征: {info['cry_features']}",
                font_size=dp(11),
                color=COLOR_TEXT,
                size_hint_y=None,
                height=dp(20),
                halign="left"
            )
            cry_label.bind(size=cry_label.setter("text_size"))
            guide_card.add_widget(cry_label)

            behaviors_text = "典型行为: " + "、".join(
                [BEHAVIOR_PATTERNS.get(b, b) for b in info['behaviors']]
            )
            behavior_label = Label(
                text=behaviors_text,
                font_size=dp(11),
                color=COLOR_TEXT,
                size_hint_y=None,
                height=dp(20),
                halign="left"
            )
            behavior_label.bind(size=behavior_label.setter("text_size"))
            guide_card.add_widget(behavior_label)

            solution_label = Label(
                text=f"解决方案: {info['solution']}",
                font_size=dp(11),
                color=COLOR_SUCCESS,
                size_hint_y=None,
                height=dp(20),
                halign="left"
            )
            solution_label.bind(size=solution_label.setter("text_size"))
            guide_card.add_widget(solution_label)

            guide_card.height = dp(100)
            self.content.add_widget(guide_card)

        # ─── Feedback History ───
        self.content.add_widget(SectionHeader(text="📝 反馈历史"))

        self.history_container = BoxLayout(
            orientation="vertical",
            spacing=dp(4),
            size_hint_y=None,
            height=dp(0)
        )
        self.content.add_widget(self.history_container)

        # Refresh history
        self.refresh_history()

        # Spacer
        spacer = Widget(size_hint_y=None, height=dp(40))
        self.content.add_widget(spacer)

        scroll.add_widget(self.content)
        self.add_widget(scroll)

    def on_threshold_change(self, instance, value):
        self.threshold_value_label.text = f"{value:.2f}"
        set_setting("match_threshold", str(value))

    def update_selected_behaviors_display(self):
        app = App.get_running_app()
        selected = app.selected_behaviors
        if selected:
            names = [BEHAVIOR_PATTERNS[s] for s in selected]
            self.selected_behaviors_label.text = "已选择行为: " + ", ".join(names)
            self.selected_behaviors_label.height = dp(20)
        else:
            self.selected_behaviors_label.text = ""
            self.selected_behaviors_label.height = dp(0)

    def on_record(self, instance):
        app = App.get_running_app()
        app.selected_behaviors = [
            b for b in app.selected_behaviors
            if b in BEHAVIOR_PATTERNS
        ]

        # Update API key
        api_key = self.api_key_input.text.strip()
        if api_key:
            os.environ["DEEPSEEK_API_KEY"] = api_key

        ai_client = DeepSeekClient()
        if not ai_client.is_configured():
            popup = Popup(
                title="提示",
                content=Label(text="请先配置 DeepSeek API Key！"),
                size_hint=(0.7, 0.3)
            )
            popup.open()
            return

        # Disable button during recording
        self.record_btn.disabled = True
        self.record_btn.text = "⏳ 录音中..."
        self.status_label.text = "正在录音..."
        self.status_label.height = dp(20)

        # Hide previous results
        self.hide_result()

        # Run in background thread
        def process():
            try:
                # Record
                self.update_status("正在录音（5秒）...")
                audio = record_audio_mobile(duration=5)

                # Extract features
                self.update_status("正在提取特征...")
                features = extract_features(audio)
                app.last_features = features

                # Find match
                self.update_status("正在分析...")
                threshold = self.threshold_slider.value
                history = get_all_feedback()
                matched, matched_need, similarity = find_best_match(
                    features["feature_vector"],
                    history,
                    threshold=threshold
                )

                if matched:
                    result = {
                        "need": matched_need,
                        "confidence": similarity,
                        "reason": f"历史匹配相似度：{similarity:.2%}",
                        "matched": True
                    }
                else:
                    feature_desc = generate_feature_description(features)
                    result = ai_client.analyze_cry(
                        feature_desc,
                        behaviors=app.selected_behaviors
                    )
                    result["matched"] = False
                    result["similarity"] = similarity

                app.last_result = result

                # Update UI on main thread
                Clock.schedule_once(lambda dt: self.show_result(result))

            except Exception as e:
                Clock.schedule_once(lambda dt: self.show_error(str(e)))
            finally:
                Clock.schedule_once(lambda dt: self.reset_record_button())

        threading.Thread(target=process, daemon=True).start()

    def update_status(self, msg):
        Clock.schedule_once(lambda dt: setattr(self.status_label, "text", msg))

    def show_result(self, result):
        self.status_label.text = ""
        self.status_label.height = dp(0)

        need_code = result["need"]
        need_name = NEED_CATEGORIES.get(need_code, need_code)
        confidence = result.get("confidence", 0)

        # Title
        self.result_title.text = f"结果：{need_name}"
        self.result_title.height = dp(32)
        self.result_title.color = COLOR_PRIMARY

        # Progress bar
        self.confidence_bar.value = min(confidence, 1.0)
        self.confidence_bar.height = dp(12)

        # Confidence label
        self.confidence_label.text = f"置信度：{confidence:.2%}"
        self.confidence_label.height = dp(18)

        # Match source
        if result.get("matched"):
            self.match_source_label.text = "✅ 本地历史匹配（节省API费用）"
            self.match_source_label.color = COLOR_SUCCESS
        else:
            sim = result.get("similarity", 0)
            self.match_source_label.text = f"🤖 DeepSeek AI分析 (历史最佳相似度：{sim:.2%}，未达阈值)"
            self.match_source_label.color = COLOR_PRIMARY
        self.match_source_label.height = dp(18)

        # Reason
        if "reason" in result:
            self.reason_label.text = f"分析理由：{result['reason']}"
            self.reason_label.height = dp(40)

        # Feedback buttons
        for child in self.result_card.children:
            if isinstance(child, BoxLayout):
                child.height = dp(36)

        # Result card
        self.result_card.height = dp(160)
        self.result_section.height = dp(170)

        self.update_selected_behaviors_display()
        Clock.schedule_once(lambda dt: self.refresh_history(), 0.5)

    def hide_result(self):
        self.result_title.height = dp(0)
        self.confidence_bar.height = dp(0)
        self.confidence_label.height = dp(0)
        self.match_source_label.height = dp(0)
        self.reason_label.height = dp(0)
        for child in self.result_card.children:
            if isinstance(child, BoxLayout):
                child.height = dp(0)
        self.result_card.height = dp(0)
        self.result_section.height = dp(0)

    def show_error(self, msg):
        self.status_label.text = f"❌ 错误: {msg}"
        self.status_label.height = dp(36)
        self.status_label.color = COLOR_ERROR

    def reset_record_button(self):
        self.record_btn.disabled = False
        self.record_btn.text = "🎤 开始录音（5秒）"

    def on_correct_feedback(self, instance):
        app = App.get_running_app()
        if not app.last_result or not app.last_features:
            return

        need_code = app.last_result["need"]
        features = app.last_features
        confidence = app.last_result.get("confidence", 0)

        save_feedback(
            feature_vector=features["feature_vector"],
            predicted_need=need_code,
            actual_need=need_code,
            confidence=confidence,
            audio_features=features,
            behaviors=app.selected_behaviors
        )

        popup = Popup(
            title="感谢反馈！",
            content=Label(text="正确结果已记录。"),
            size_hint=(0.6, 0.3)
        )
        popup.open()
        self.refresh_history()

    def on_correction_select(self, spinner, text):
        if text == "纠正为...":
            return

        app = App.get_running_app()
        if not app.last_result or not app.last_features:
            return

        # Map value back to code
        code_map = {v: k for k, v in NEED_CATEGORIES.items()}
        actual_code = code_map.get(text)
        if not actual_code:
            return

        predicted_code = app.last_result["need"]
        features = app.last_features
        confidence = app.last_result.get("confidence", 0)

        save_feedback(
            feature_vector=features["feature_vector"],
            predicted_need=predicted_code,
            actual_need=actual_code,
            confidence=confidence,
            audio_features=features,
            behaviors=app.selected_behaviors
        )

        popup = Popup(
            title="感谢纠错！",
            content=Label(text=f"已纠正为：{text}"),
            size_hint=(0.6, 0.3)
        )
        popup.open()

        self.correction_spinner.text = "纠正为..."
        self.refresh_history()

    def refresh_history(self):
        self.history_container.clear_widgets()

        history = get_all_feedback()
        count = get_feedback_count()

        # Update counter
        self.feedback_count_label.text = f"📊 反馈记录数: {count} 条"
        self.feedback_count_label.color = COLOR_SUCCESS if count > 0 else COLOR_TEXT_SECONDARY

        if not history:
            no_history = Label(
                text="暂无反馈记录",
                font_size=dp(11),
                color=COLOR_TEXT_SECONDARY,
                size_hint_y=None,
                height=dp(22)
            )
            self.history_container.add_widget(no_history)
            self.history_container.height = dp(22)
            return

        total_height = dp(0)
        for record in history[:10]:
            predicted = NEED_CATEGORIES.get(record["predicted_need"], record["predicted_need"])
            actual = NEED_CATEGORIES.get(record["actual_need"], record["actual_need"])
            is_correct = record["predicted_need"] == record["actual_need"]

            item = BoxLayout(
                orientation="vertical",
                size_hint_y=None,
                height=dp(60),
                spacing=dp(2),
                padding=dp(6)
            )
            with item.canvas.before:
                Color(1, 1, 1, 1)
                Rectangle(size=item.size, pos=item.pos)
            item.bind(size=lambda i, s: i.canvas.before.children[1].size if len(i.canvas.before.children) > 1 else None,
                       pos=lambda i, p: i.canvas.before.children[1].pos if len(i.canvas.before.children) > 1 else None)

            result_line = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(18), spacing=dp(4))
            result_line.add_widget(Label(
                text=f"预测: {predicted}",
                font_size=dp(10),
                size_hint_x=0.35,
                color=COLOR_TEXT
            ))
            result_line.add_widget(Label(
                text=f"实际: {actual}",
                font_size=dp(10),
                size_hint_x=0.35,
                color=COLOR_TEXT
            ))
            status_text = "✅ 对" if is_correct else "❌ 错"
            status_color = COLOR_SUCCESS if is_correct else COLOR_ERROR
            result_line.add_widget(Label(
                text=status_text,
                font_size=dp(10),
                size_hint_x=0.3,
                color=status_color
            ))
            item.add_widget(result_line)

            if record.get("behaviors"):
                behavior_names = [BEHAVIOR_PATTERNS.get(b, b) for b in record["behaviors"]]
                item.add_widget(Label(
                    text=f"行为: {', '.join(behavior_names)}",
                    font_size=dp(9),
                    color=COLOR_TEXT_SECONDARY,
                    size_hint_y=None,
                    height=dp(14)
                ))

            item.add_widget(Label(
                text=f"时间: {record['created_at']}",
                font_size=dp(9),
                color=COLOR_TEXT_SECONDARY,
                size_hint_y=None,
                height=dp(14)
            ))

            self.history_container.add_widget(item)
            total_height += dp(64)

        self.history_container.height = total_height


class BabyCryApp(App):
    """Main Kivy Application"""

    def build(self):
        self.title = "婴儿哭声意图理解器"
        self.icon = "icon.png"
        self.selected_behaviors = []
        self.last_result = None
        self.last_features = None

        # Initialize database
        init_db()

        # Set window background
        Window.clearcolor = COLOR_BG

        return MainScreen()


if __name__ == "__main__":
    BabyCryApp().run()
