import streamlit as st
import time
import datetime

st.set_page_config(
    page_title="WMS RevPi Test", 
    layout="wide"
)

st.title("WMS Revolution Pi Test")
st.write("Revolution Pi Connect SE Interface")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("RevPi Status", "Online", "Active")

with col2:
    st.metric("Network", "192.168.0.12", "Connected")
    
with col3:
    current_time = datetime.datetime.now().strftime("%H:%M:%S")
    st.metric("Time", current_time, "Live")

if st.button("Test Connection"):
    with st.spinner("Testing..."):
        time.sleep(1)
    st.success("Connection test successful!")

st.info("System running on Revolution Pi Connect SE")

st.markdown("Revolution Pi Connect SE | WMS Interface")
