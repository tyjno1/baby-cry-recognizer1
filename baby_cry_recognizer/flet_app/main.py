# -*- coding: utf-8 -*-
"""Baby Cry Recognizer - Flet Android App"""
import os, sys, traceback, threading
import numpy as np
import flet as ft

try:
    import sounddevice as sd
    HAS_SOUNDDEVICE = True
except ImportError:
    HAS_SOUNDDEVICE = False

SAMPLE_RATE = 16000


def record_audio(duration=5):
    if HAS_SOUNDDEVICE:
        audio = sd.rec(int(duration * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype="float32")
        sd.wait()
        return audio.flatten()
    else:
        return np.random.randn(duration * SAMPLE_RATE).astype("float32") * 0.1


def main(page: ft.Page):
    page.title = "婴儿哭声意图理解器"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 12
    page.scroll = ft.ScrollMode.AUTO
    page.window.width = 400
    page.window.height = 850

    loading_text = ft.Text("正在初始化...", size=14, color=ft.Colors.BLUE_600)
    error_text = ft.Text("", color=ft.Colors.RED, size=13, selectable=True)
    page.add(ft.SafeArea(ft.Column([loading_text, error_text], spacing=8)))
    page.update()

    try:
        from config import NEED_CATEGORIES, BEHAVIOR_PATTERNS, REFERENCE_GUIDE
        from config import MATCH_THRESHOLD as CFG_MATCH_THRESHOLD
        from database import init_db, save_feedback, get_all_feedback, get_feedback_count, get_setting, set_setting
        from audio_processor import extract_features, find_best_match, generate_feature_description
        loading_text.value = "✔ 模块加载成功"
        page.update()
    except Exception:
        loading_text.value = ""
        error_text.value = "✖ 模块加载失败:\n" + traceback.format_exc()
        page.update()
        return

    try:
        init_db()
        loading_text.value = "✔ 数据库初始化成功"
        page.update()
    except Exception:
        loading_text.value = ""
        error_text.value = "✖ 数据库初始化失败:\n" + traceback.format_exc()
        page.update()
        return

    selected_behaviors = []
    last_result = None
    last_features = None

    def section_header(text):
        return ft.Text(text, size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_700)

    def make_card(*controls):
        return ft.Card(
            content=ft.Container(
                content=ft.Column(list(controls), spacing=8, tight=True),
                padding=12
            ),
            elevation=1
        )

    api_key_field = ft.TextField(
        label="DeepSeek API Key",
        value=os.getenv("DEEPSEEK_API_KEY", ""),
        password=True, can_reveal_password=True,
        border=ft.InputBorder.OUTLINE, dense=True
    )

    default_threshold = float(get_setting("match_threshold", str(CFG_MATCH_THRESHOLD)))
    threshold_slider = ft.Slider(min=0, max=1.0, value=default_threshold, divisions=20, label="{value:.2f}")
    threshold_slider.on_change = lambda e: set_setting("match_threshold", str(e.control.value))

    count = get_feedback_count()
    feedback_count_text = ft.Text(
        f"U0001f4ca 反馈记录数: {count} 条",
        color=ft.Colors.GREEN_700 if count > 0 else ft.Colors.GREY_500
    )

    behavior_grid = ft.ResponsiveRow(spacing=4, run_spacing=4)
    for code, name in BEHAVIOR_PATTERNS.items():
        cb = ft.Checkbox(label=name, value=False, dense=True)
        cb.on_change = lambda e, c=code: (
            selected_behaviors.append(c) if e.control.value
            else (selected_behaviors.remove(c) if c in selected_behaviors else None)
        )
        behavior_grid.controls.append(
            ft.Container(content=cb, col={"xs": 6, "sm": 4, "md": 3}, padding=2)
        )

    behavior_status = ft.Text("", color=ft.Colors.BLUE_500, size=12)

    record_btn = ft.ElevatedButton(
        "U0001f3a4 开始录音（5秒）", icon=ft.Icons.MIC,
        style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_600, color=ft.Colors.WHITE, padding=16,
                            shape=ft.RoundedRectangleBorder(radius=8)),
        height=48
    )

    status_text = ft.Text("", color=ft.Colors.GREY_500)

    result_title = ft.Text("", size=18, weight=ft.FontWeight.BOLD)
    confidence_bar = ft.ProgressBar(width=300, visible=False)
    confidence_label = ft.Text("", color=ft.Colors.GREY_600, size=12)
    source_label = ft.Text("", size=12)
    reason_label = ft.Text("", size=12)
    similarity_label = ft.Text("", color=ft.Colors.GREY_500, size=11, visible=False)

    def on_correct(_):
        nonlocal last_result, last_features
        if not last_result or last_features is None:
            return
        save_feedback(feature_vector=last_features["feature_vector"],
                     predicted_need=last_result["need"], actual_need=last_result["need"],
                     confidence=last_result.get("confidence", 0),
                     audio_features=last_features, behaviors=list(selected_behaviors))
        page.snack_bar = ft.SnackBar(ft.Text("✔ 感谢反馈！正确结果已记录"))
        page.snack_bar.open = True
        refresh_history()
        page.update()

    correction_dd = ft.Dropdown(
        hint_text="纠正为...",
        options=[ft.dropdown.Option(v) for v in NEED_CATEGORIES.values()],
        dense=True, width=140
    )

    def on_correction(e):
        nonlocal last_result, last_features
        if not last_result or last_features is None:
            return
        code_map = {v: k for k, v in NEED_CATEGORIES.items()}
        actual_code = code_map.get(e.control.value)
        if not actual_code:
            return
        save_feedback(feature_vector=last_features["feature_vector"],
                     predicted_need=last_result["need"], actual_need=actual_code,
                     confidence=last_result.get("confidence", 0),
                     audio_features=last_features, behaviors=list(selected_behaviors))
        page.snack_bar = ft.SnackBar(ft.Text(f"✔ 已纠正为：{e.control.value}"))
        page.snack_bar.open = True
        correction_dd.value = None
        refresh_history()
        page.update()

    correction_dd.on_change = on_correction

    result_card = ft.Card(
        content=ft.Container(
            content=ft.Column([
                result_title, confidence_bar, confidence_label,
                source_label, similarity_label, reason_label,
                ft.Row([
                    ft.ElevatedButton("✔ 结果正确", on_click=on_correct,
                                     bgcolor=ft.Colors.GREEN_600, color=ft.Colors.WHITE, height=36),
                    correction_dd
                ], spacing=8)
            ], spacing=6, tight=True),
            padding=12
        ),
        elevation=2, visible=False
    )

    guide_tiles = []
    for code, info in REFERENCE_GUIDE.items():
        behaviors_text = "、".join([BEHAVIOR_PATTERNS.get(b, b) for b in info["behaviors"]])
        guide_tiles.append(
            ft.ExpansionTile(
                title=ft.Text(f"U0001f4c9 {info['title']}", weight=ft.FontWeight.BOLD),
                subtitle=ft.Text(info["cry_features"], size=11, max_lines=2),
                controls=[
                    ft.ListTile(title=ft.Text("哭声特征", size=12, weight=ft.FontWeight.BOLD),
                               subtitle=ft.Text(info["cry_features"], size=12)),
                    ft.ListTile(title=ft.Text("典型行为", size=12, weight=ft.FontWeight.BOLD),
                               subtitle=ft.Text(behaviors_text, size=12)),
                    ft.ListTile(title=ft.Text("解决方案", size=12, weight=ft.FontWeight.BOLD),
                               subtitle=ft.Text(info["solution"], size=12, color=ft.Colors.GREEN_700)),
                ],
                initially_expanded=False,
                shape=ft.RoundedRectangleBorder(radius=8)
            )
        )

    history_column = ft.Column(spacing=4)

    def refresh_history():
        history_column.controls.clear()
        history = get_all_feedback()
        count2 = get_feedback_count()
        feedback_count_text.value = f"U0001f4ca 反馈记录数: {count2} 条"
        feedback_count_text.color = ft.Colors.GREEN_700 if count2 > 0 else ft.Colors.GREY_500
        if not history:
            history_column.controls.append(ft.Text("暂无反馈记录", color=ft.Colors.GREY_500, size=12))
        else:
            for record in history[:10]:
                predicted = NEED_CATEGORIES.get(record["predicted_need"], record["predicted_need"])
                actual = NEED_CATEGORIES.get(record["actual_need"], record["actual_need"])
                is_correct = record["predicted_need"] == record["actual_need"]
                status_icon = "✅" if is_correct else "❌"
                status_color = ft.Colors.GREEN_700 if is_correct else ft.Colors.RED_600
                parts2 = []
                if record.get("behaviors"):
                    names = [BEHAVIOR_PATTERNS.get(b, b) for b in record["behaviors"]]
                    parts2.append(f"行为: {', '.join(names)}")
                parts2.append(f"时间: {record['created_at']}")
                history_column.controls.append(
                    ft.Card(
                        content=ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    ft.Text(f"预测: {predicted}", size=12),
                                    ft.Text(f"实际: {actual}", size=12),
                                    ft.Text(status_icon, size=12, color=status_color),
                                ], spacing=8, alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                                ft.Text(" | ".join(parts2), size=10, color=ft.Colors.GREY_600)
                            ], tight=True, spacing=2),
                            padding=8
                        ), elevation=1
                    )
                )

    def on_record(_):
        nonlocal last_result, last_features
        try:
            from ai_client import DeepSeekClient
        except Exception as e:
            page.snack_bar = ft.SnackBar(ft.Text(f"✖ 导入AI模块失败: {e}"))
            page.snack_bar.open = True
            page.update()
            return

        api_key = api_key_field.value.strip()
        if api_key:
            os.environ["DEEPSEEK_API_KEY"] = api_key

        ai_client = DeepSeekClient()
        if not ai_client.is_configured():
            page.snack_bar = ft.SnackBar(ft.Text("请先配置 DeepSeek API Key！"))
            page.snack_bar.open = True
            page.update()
            return

        record_btn.disabled = True
        record_btn.text = "⏳ 录音中..."
        status_text.value = "正在录音...请勿离开页面"
        result_card.visible = False
        page.update()

        def process():
            nonlocal last_result, last_features
            try:
                audio = record_audio(duration=5)
                features = extract_features(audio)
                last_features = features
                threshold = threshold_slider.value
                history = get_all_feedback()
                matched, matched_need, similarity = find_best_match(
                    features["feature_vector"], history, threshold=threshold)
                if matched:
                    result = {"need": matched_need, "confidence": similarity,
                             "reason": f"历史匹配相似度：{similarity:.2%}", "matched": True}
                else:
                    feature_desc = generate_feature_description(features)
                    result = ai_client.analyze_cry(feature_desc, behaviors=list(selected_behaviors))
                    result["matched"] = False
                    result["similarity"] = similarity
                last_result = result
                show_result(result)
            except Exception as e:
                status_text.value = f"✖ 错误: {e}"
                status_text.color = ft.Colors.RED_600
            finally:
                record_btn.disabled = False
                record_btn.text = "U0001f3a4 开始录音（5秒）"
            page.update()

        threading.Thread(target=process, daemon=True).start()

    record_btn.on_click = on_record

    def show_result(result):
        need_code = result["need"]
        need_name = NEED_CATEGORIES.get(need_code, need_code)
        confidence = result.get("confidence", 0)
        result_title.value = f"结果：{need_name}"
        result_title.color = ft.Colors.BLUE_700
        confidence_bar.value = min(confidence, 1.0)
        confidence_bar.visible = True
        confidence_label.value = f"置信度：{confidence:.2%}"
        if result.get("matched"):
            source_label.value = "✅ 本地历史匹配（节省API费用）"
            source_label.color = ft.Colors.GREEN_600
            similarity_label.visible = False
        else:
            source_label.value = "U0001f916 DeepSeek AI 分析"
            source_label.color = ft.Colors.BLUE_600
            sim = result.get("similarity", 0)
            similarity_label.value = f"历史最佳相似度：{sim:.2%}（未达阈值）"
            similarity_label.visible = True
        if "reason" in result:
            reason_label.value = f"分析理由：{result['reason']}"
        status_text.value = ""
        result_card.visible = True
        correction_dd.value = None
        if selected_behaviors:
            names = [BEHAVIOR_PATTERNS[b] for b in selected_behaviors if b in BEHAVIOR_PATTERNS]
            behavior_status.value = "已选行为: " + ", ".join(names) if names else ""
        refresh_history()

    # Final UI rendering with error catch
    try:
        page.controls.clear()
        page.add(
            ft.Column([
                ft.Text("U0001f476 婴儿哭声意图理解器", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_800),
                ft.Text("听懂哭声，告别猜测——让每一次回应都准确、及时、安心", size=12, color=ft.Colors.GREY_500),
                ft.Divider(),
                section_header("⚙️ 设置"),
                make_card(api_key_field,
                    ft.Row([ft.Text("匹配阈值", size=12), threshold_slider,
                           ft.Text(f"{get_setting('match_threshold', str(CFG_MATCH_THRESHOLD))}", size=12)], spacing=8),
                    feedback_count_text),
                section_header("U0001f440 行为表现（可选）"),
                make_card(behavior_grid),
                behavior_status,
                ft.Divider(),
                record_btn, status_text,
                ft.Divider(),
                result_card,
                ft.Divider(),
                section_header("U0001f4d6 资料参考"),
                ft.Column(guide_tiles, spacing=4),
                ft.Divider(),
                section_header("U0001f4dd 反馈历史"),
                history_column,
                ft.Container(height=60)
            ], spacing=8, tight=True)
        )
        refresh_history()
    except Exception:
        page.controls.clear()
        page.add(ft.SafeArea(ft.Column([
            ft.Text("✖ UI构建失败", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.RED),
            ft.Text(traceback.format_exc(), size=11, color=ft.Colors.RED, selectable=True),
        ])))
        page.update()


if __name__ == "__main__":
    ft.app(target=main)