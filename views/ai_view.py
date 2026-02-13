import streamlit as st
import pandas as pd
import os
from ai_assistant import ask_ai, trim_history, build_catalog_summary, build_schedule_summary, needs_catalog
from config import AVAILABLE_MODELS
from state import get_selected, save_session

def render_ai_view(df: pd.DataFrame):
    st.subheader("🤖 Smart Assistant")
    st.caption("Tanya AI tentang jadwalmu atau minta saran mata kuliah.")

    # API Key Handling (Env only)
    api_key = os.getenv("AI_API_KEY")
    if not api_key:
        st.warning("⚠️ API Key tidak ditemukan. Pastikan `AI_API_KEY` ada di file `.env`.")
        st.stop()

    # ── Controls ──
    col_model, col_clear = st.columns([3, 1])

    with col_model:
        model_options = [m[0] for m in AVAILABLE_MODELS]
        model_labels = [m[1] for m in AVAILABLE_MODELS]
        current_model = st.session_state.get("ai_model", model_options[0])
        selected_idx = model_options.index(current_model) if current_model in model_options else 0

        selected_model = st.selectbox(
            "Model AI",
            options=model_options,
            format_func=lambda x: model_labels[model_options.index(x)],
            index=selected_idx,
            key="ai_model_select"
        )
        st.session_state["ai_model"] = selected_model

    with col_clear:
        st.write("")
        st.write("")
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state["chat_history"] = []
            save_session()
            st.rerun()

    # Show message count
    history = st.session_state.get("chat_history", [])
    if history:
        st.caption(f"💬 {len(history)} pesan dalam histori")

    st.divider()

    # Init chat history
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    # Display History
    for msg in st.session_state["chat_history"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat Input
    if prompt := st.chat_input("Tanya sesuatu..."):
        # Display User Message
        st.session_state["chat_history"].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # ── Build Context (token-optimized) ──
        selected_ids = get_selected()
        schedule_ctx = build_schedule_summary(df, selected_ids)

        # Only include catalog when user asks about courses/recommendations
        catalog_section = ""
        if needs_catalog(prompt):
            catalog_section = f"\n\nSemua MK tersedia:\n{build_catalog_summary(df)}"

        system_prompt = {
            "role": "system",
            "content": (
                f"Asisten akademik mahasiswa. Jawab Bahasa Indonesia, ringkas.\n\n"
                f"Jadwal saya:\n{schedule_ctx}"
                f"{catalog_section}"
            ),
        }

        # Trim history to avoid exceeding context limits
        trimmed_history = trim_history(st.session_state["chat_history"])
        api_messages = [system_prompt] + trimmed_history

        # Call API with selected model
        model = st.session_state.get("ai_model", AVAILABLE_MODELS[0][0])
        with st.chat_message("assistant"):
            with st.spinner("Berpikir..."):
                response_text = ask_ai(api_key, api_messages, model=model)
                st.markdown(response_text)

        # Append & Trim
        st.session_state["chat_history"].append({"role": "assistant", "content": response_text})
        st.session_state["chat_history"] = trim_history(st.session_state["chat_history"])
        save_session()
