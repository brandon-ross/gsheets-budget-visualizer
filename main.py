import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection

conn = st.connection("gsheets", type=GSheetsConnection)

# Current months in spreadsheet
months = ['January', 'February', 'March']

# Read in data for each month
dfs = [conn.read(worksheet=month, skiprows=1, usecols=[0,1,2,3,4,5]) for month in months]

df_combined = pd.concat(dfs, ignore_index=True)

st.set_page_config(
    page_title="Budget Dashboard",
    page_icon=":bar_chart:",
    layout="wide"
)

st.title("Budget Breakdown Dashboard")
st.markdown("_Test Prototype v1.0_")

with st.expander("Data Preview"):
    st.dataframe(
        df_combined,
        column_config={
            "Amount": st.column_config.NumberColumn(format="dollar")
        }
    )