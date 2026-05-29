# -*- coding: utf-8 -*-
"""Streamlit Main App"""
import streamlit as st
import numpy as np
import os

from config import NEED_CATEGORIES, MATCH_THRESHOLD, BEHAVIOR_PATTERNS, REFERENCE_GUIDE
from database import init_db, save_feedback, get_all_feedback, get_feedback_count, get_setting, set_setting
from audio_processor import record_audio, extract_features, find_best_match, generate_feature_description
from ai_client import DeepSeekClient

st.set_page_config(
    page_title="婴儿哭声意图理解器",
    page_icon="👶",
    layout="centered"
)

init_db()
ai_client = DeepSeekClient() if DeepSeekClient().is_configured() else None

if "recording" not in st.session_state:
    st.session_state.recording = False
if "last_result" not in st.session_state:
    st.session_state.last_result = None
if "last_features" not in st.session_state:
    st.session_state.last_features = None
if "selected_behaviors" not in st.session_state:
    st.session_state.selected_behaviors = []

st.title("👶 婴儿哭声意图理解器")
st.caption("听懂哭声，告别猜测——让每一次回应都准确、及时、安心")

with st.sidebar:
    st.header("设置")
    
    st.subheader("API配置")
    api_key = st.text_input("DeepSeek API Key", 
                           value=os.getenv("DEEPSEEK_API_KEY", ""),
                           type="password",
                           help="请输入你的DeepSeek API Key")
    
    if api_key:
        os.environ["DEEPSEEK_API_KEY"] = api_key
        ai_client = DeepSeekClient()
    
    st.subheader("匹配设置")
    threshold = st.slider("本地匹配阈值", 
                         min_value=0.0, 
                         max_value=1.0, 
                         value=float(get_setting("match_threshold", str(MATCH_THRESHOLD))),
                         step=0.05,
                         help="余弦相似度超过此阈值时，直接使用历史匹配结果")
    
    set_setting("match_threshold", str(threshold))
    
    st.subheader("统计")
    feedback_count = get_feedback_count()
    st.metric("反馈记录数", feedback_count)
    
    if feedback_count > 0:
        st.success(f"系统已学习 {feedback_count} 条记录！")
    else:
        st.info("暂无反馈记录，请开始使用并纠正错误，帮助系统学习。")

st.header("录音与识别")

st.subheader("1. 选择行为表现（可选）")
st.write("观察宝宝的行为表现，选择符合的项目：")

cols = st.columns(5)
selected = []
for idx, (code, name) in enumerate(BEHAVIOR_PATTERNS.items()):
    with cols[idx % 5]:
        if st.checkbox(name, key=f"beh_{code}"):
            selected.append(code)

st.session_state.selected_behaviors = selected

if selected:
    st.info(f"已选择行为：{', '.join([BEHAVIOR_PATTERNS[s] for s in selected])}")

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.button("开始录音（5秒）", use_container_width=True, disabled=st.session_state.recording):
        if ai_client is None or not ai_client.is_configured():
            st.error("请先配置 DeepSeek API Key！")
        else:
            st.session_state.recording = True
            
            with st.spinner("正在录音音频..."):
                audio = record_audio(duration=5)
            
            with st.spinner("正在提取特征..."):
                features = extract_features(audio)
                st.session_state.last_features = features
            
            with st.spinner("正在分析..."):
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
                    result = ai_client.analyze_cry(feature_desc, behaviors=st.session_state.selected_behaviors)
                    result["matched"] = False
                    result["similarity"] = similarity
                
                st.session_state.last_result = result
            
            st.session_state.recording = False
            st.rerun()

if st.session_state.last_result:
    result = st.session_state.last_result
    
    need_code = result["need"]
    need_name = NEED_CATEGORIES.get(need_code, need_code)
    confidence = result.get("confidence", 0)
    
    st.subheader(f"结果：{need_name}")
    
    st.progress(min(confidence, 1.0))
    st.caption(f"置信度：{confidence:.2%}")
    
    if result.get("matched"):
        st.success("本地历史匹配（节省API费用）")
    else:
        st.info("DeepSeek AI分析")
        if "similarity" in result:
            st.caption(f"历史最佳相似度：{result['similarity']:.2%}（未达阈值）")
    
    if "reason" in result:
        st.markdown(f"**分析理由：** {result['reason']}")
    
    st.header("反馈")
    st.write("结果正确吗？如不正确，请选择实际需求：")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("结果正确", use_container_width=True):
            features = st.session_state.last_features
            save_feedback(
                feature_vector=features["feature_vector"],
                predicted_need=need_code,
                actual_need=need_code,
                confidence=confidence,
                audio_features=features,
                behaviors=st.session_state.selected_behaviors
            )
            st.success("感谢反馈！正确结果已记录。")
    
    with col2:
        st.write("纠正为：")
    
    cols = st.columns(len(NEED_CATEGORIES))
    for idx, (code, name) in enumerate(NEED_CATEGORIES.items()):
        with cols[idx]:
            if st.button(name, key=f"correct_{code}", use_container_width=True):
                features = st.session_state.last_features
                save_feedback(
                    feature_vector=features["feature_vector"],
                    predicted_need=need_code,
                    actual_need=code,
                    confidence=confidence,
                    audio_features=features,
                    behaviors=st.session_state.selected_behaviors
                )
                st.success(f"已纠正为：{name}。感谢反馈！")

st.header("资料参考")
st.write("以下是各种需求的判断方法和应对措施：")

for code, info in REFERENCE_GUIDE.items():
    with st.expander(f"📖 {info['title']}"):
        st.markdown(f"**哭声特征：** {info['cry_features']}")
        st.markdown(f"**典型行为：**")
        for b in info['behaviors']:
            st.markdown(f"- {BEHAVIOR_PATTERNS.get(b, b)}")
        st.markdown(f"**解决方案：** {info['solution']}")

st.header("反馈历史")

history = get_all_feedback()
if history:
    for record in history[:10]:
        predicted = NEED_CATEGORIES.get(record["predicted_need"], record["predicted_need"])
        actual = NEED_CATEGORIES.get(record["actual_need"], record["actual_need"])
        
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            st.write(f"预测：{predicted}")
        with col2:
            st.write(f"实际：{actual}")
        with col3:
            if record["predicted_need"] == record["actual_need"]:
                st.success("对")
            else:
                st.error("错")
        
        if record.get("behaviors"):
            behavior_names = [BEHAVIOR_PATTERNS.get(b, b) for b in record["behaviors"]]
            st.caption(f"行为：{', '.join(behavior_names)}")
        
        st.caption(f"时间：{record['created_at']}")
        st.divider()
else:
    st.info("暂无反馈记录")

st.markdown("---")
st.caption("婴儿哭声意图理解器 | DeepSeek AI | 本地学习，越用越准")
