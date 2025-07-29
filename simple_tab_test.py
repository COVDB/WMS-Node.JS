import streamlit as st

# Zeer simpele test - alleen basis tabs
st.set_page_config(page_title="Tab Test", layout="wide")

st.title("TAB TEST - Revolution Pi")

# Test met simpele tabs
tab1, tab2, tab3, tab4 = st.tabs(["Tab 1", "AISLE CONTROL", "Tab 3", "Tab 4"])

with tab1:
    st.header("Tab 1 Content")
    st.success("Dit is tab 1")

with tab2:
    st.header("AISLE CONTROL TAB")
    st.success("✅ SUCCESS! Als je dit ziet, dan werken de 4 tabs!")
    st.balloons()

with tab3:
    st.header("Tab 3 Content") 
    st.info("Dit is tab 3")

with tab4:
    st.header("Tab 4 Content")
    st.info("Dit is tab 4")

st.markdown("---")
st.markdown("**Test:** Als je 4 tabs ziet, dan is het probleem opgelost!")
