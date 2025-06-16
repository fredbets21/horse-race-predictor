import streamlit as st
from predictor import launch_browser_get_html, parse_racecard, score_horse

st.set_page_config(page_title="The Racing Algo", page_icon="🏇")
st.title("🏇 The Racing Algo")

url = st.text_input("Enter IrishRacing racecard URL:")

if st.button("Predict Winner") and url:
    with st.spinner("Fetching and analysing racecard..."):
        try:
            html = launch_browser_get_html(url)
            horses = parse_racecard(html)

            if not horses:
                st.error("No horses found.")
            else:
                for horse in horses:
                    horse["score"] = score_horse(horse)

                ranked = sorted(horses, key=lambda x: x["score"], reverse=True)
                st.success(f"🥇 Most Likely Winner: **{ranked[0]['name']}**")

                st.subheader("📋 Full Predicted Order:")
                for i, h in enumerate(ranked, 1):
                    st.markdown(
                        f"**{i}. {h['name']}** — Score: {h['score']:.1f}<br>"
                        f"Form: {h['form']} | CD Win: {'Yes' if h['cd_win'] else 'No'} | "
                        f"Rating: {h['rating']} | Jockey: {h['jockey']} ({h['jockey_win_pct']}%) | "
                        f"Odds: {h['odds']}",
                        unsafe_allow_html=True
                    )
        except Exception as e:
            st.error(f"❌ Error: {e}")


