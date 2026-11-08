"""Streamlit UI: paste a poem, compare OpenAI vs open-weight side by side.
Run: streamlit run app.py
"""
import streamlit as st

from analyzer import BACKENDS, analyze_poem

st.set_page_config(page_title="Poetry Style Analyzer", layout="wide")
st.title("Poetry Style Analyzer")
st.caption("Compare an OpenAI model with an open-weight model on the same poem.")

poem = st.text_area("Paste your poem", height=260)
choice = st.multiselect(
    "Models", list(BACKENDS), default=list(BACKENDS),
    format_func=lambda k: f"{BACKENDS[k]['label']} ({BACKENDS[k]['model']})",
)

if st.button("Analyze", type="primary") and poem.strip() and choice:
    cols = st.columns(len(choice))
    for col, key in zip(cols, choice):
        with col:
            with st.spinner(f"{BACKENDS[key]['label']}..."):
                r = analyze_poem(poem, key)
            st.subheader(f"{BACKENDS[key]['label']}")
            st.caption(f"{r['model']} · {r['latency_s']}s")
            if r["error"] and not r["result"]:
                st.error(r["error"])
                continue
            res = r["result"]
            st.markdown(f"**Form:** {res.get('form')}")
            st.markdown(f"**Meter:** {res.get('meter')}")
            st.markdown(f"**Rhyme scheme:** {res.get('rhyme_scheme')}")
            st.markdown(f"**Tone:** {', '.join(res.get('tone', []))}")
            st.markdown(f"**Themes:** {', '.join(res.get('themes', []))}")
            st.markdown("**Imagery**")
            for x in res.get("imagery", []):
                st.markdown(f"- {x}")
            st.markdown("**Devices**")
            for x in res.get("devices", []):
                st.markdown(f"- {x}")
            st.markdown(f"**Summary:** {res.get('summary')}")
            st.markdown("**Suggestions**")
            for x in res.get("suggestions", []):
                st.markdown(f"- {x}")
            with st.expander("Raw output"):
                st.code(r["raw"])
