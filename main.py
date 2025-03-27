import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit_gsheets import GSheetsConnection

st.set_page_config(
    page_title="Budget Dashboard",
    page_icon=":bar_chart:",
    layout="wide"
)

if st.sidebar.button('Refresh Data'):
    st.cache_data.clear()  # Clear all cached data
    st.rerun()

st.markdown("""
<style>
    header {
        visibility: hidden;
        height: 0;
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        z-index: -1;
    }
    .stDeployButton {
        display: none;
    }
    .block-container {
        padding-top: 0rem;
        margin-top: -1rem;
    }
</style>
""", unsafe_allow_html=True)

# ==================== READ IN DATA AND CLEANING ====================

# Connect to private google sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Current months in spreadsheet
months = ['January', 'February', 'March']

# Read in data for each month and transform into one dataframe
dfs = [conn.read(worksheet=month, skiprows=1, usecols=[0,1,2,3,4,5]) for month in months]
df = pd.concat(dfs, ignore_index=True)

# Convert 'Date' to datetime
df['Date'] = pd.to_datetime(df['Date'])

# Extract month name for grouping
df['Month'] = df['Date'].dt.strftime('%B')

# ==================== CALCULATING LIQUID BALANCES ====================

# Separate savings transactions and calculate total savings
savings_transfers = df[df["Category"] == "Savings"]
savings_total = -savings_transfers["Amount"].sum()  # Convert to positive for savings total

# Filter out 'Credit' transactions from the DataFrame
df_filtered = df[df["Method"] != "Credit"]

# Calculate running balance for each method
def calculate_running_balance(method):
    method_transactions = df_filtered[df_filtered["Method"] == method]
    return method_transactions["Amount"].sum()

# Get running balances for each method
cash_balance = calculate_running_balance("Cash")
debit_balance = calculate_running_balance("Debit")
savings_balance = savings_total  # From previous calculation

# Balance correction
cash_balance += 229
debit_balance += 5597.14

# Create a dictionary of balances
balance_summary = {
    "Cash": cash_balance,
    "Debit": debit_balance,
    "Savings": savings_balance
}

# Calculate total liquid balance
total_liquid_balance = sum(balance_summary.values())

# Custom CSS for centered, dark-background cards
st.markdown("""
<style>
.stMetric {
    background-color: #333333;
    border-radius: 10px;
    padding: 20px;
    text-align: center;
    color: white;
    display: flex;
    flex-direction: column;
    align-items: center;
}
.stMetric > div {
    width: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
}
.liquid-balance-header {
    text-align: center;
    font-size: 1.85rem;
    font-weight: bold;
    margin-bottom: 20px;
    color: white;
}
</style>
""", unsafe_allow_html=True)

# Centered Liquid Balance Header
st.markdown('<div class="liquid-balance-header">Liquid Balances</div>', unsafe_allow_html=True)

# Create a row of four cards to display balance summary
col1, col2, col3, col4 = st.columns(4)

def custom_metric(label, value):
    return f"""
    <div style="
        background-color: #222222; 
        border-radius: 10px; 
        padding: 10px; 
        text-align: center; 
        color: white; 
        width: 100%;
    ">
        <div style="
            font-size: 1.75rem; 
            font-weight: bold; 
            margin-bottom: 10px;
        ">{label}</div>
        <div style="
            font-size: 1.5rem;
        ">${value:,.2f}</div>
    </div>
    """

# Display the cards
with col1:
    st.markdown(custom_metric("Cash", balance_summary["Cash"]), unsafe_allow_html=True)

with col2:
    st.markdown(custom_metric("Debit", balance_summary["Debit"]), unsafe_allow_html=True)

with col3:
    st.markdown(custom_metric("Savings", balance_summary["Savings"]), unsafe_allow_html=True)

with col4:
    st.markdown(custom_metric("Total", total_liquid_balance), unsafe_allow_html=True)

# st.divider()

# ==================== SPENDING BREAKDOWN ====================

# Spending Breakdown Section
st.markdown('<div class="liquid-balance-header" style="margin-top: 20px;">Spending Breakdown</div>', unsafe_allow_html=True)

# Custom CSS for month selector
st.markdown("""
<style>
.stButton > button {
    background-color: #333333;
    color: white;
    border: none;
    border-radius: 10px;
    width: 100%;
}
.stButton > button:hover {
    background-color: #702963;
    color: white;
}
.stButton > button:focus {
    color: white !important; /* Force white text color when focused */
    background-color: #702963 !important;
    outline: none; /* Remove the default focus outline if desired */
}            
.stButton > button:active {
    color: white; /* Ensure text stays white when clicked/active */
}
.stButton > button:disabled {
    background-color: #222222;
    color: #666666;
    cursor: not-allowed;
}
</style>
""", unsafe_allow_html=True)

# Define all 12 months
all_months = [
    'January', 'February', 'March', 'April', 
    'May', 'June', 'July', 'August', 
    'September', 'October', 'November', 'December'
]

# Create columns for month selection (6 columns in first row, 6 in second)
col1, col2, col3, col4, col5, col6 = st.columns(6)
col7, col8, col9, col10, col11, col12 = st.columns(6)

# Function to create month buttons in a column
def create_month_buttons(columns, month_list):
    for i, month in enumerate(month_list):
        with columns[i]:
            is_available = month in months
            month_button = st.button(
                month, 
                disabled=not is_available, 
                key=month,
                use_container_width=True
            )
            if month_button:
                st.session_state.selected_month = month

# Group months into two lists
month_groups = [
    all_months[:6],
    all_months[6:]
]

# Column groups
column_groups = [
    [col1, col2, col3, col4, col5, col6],
    [col7, col8, col9, col10, col11, col12]
]

# Initialize selected month in session state if not already set
if 'selected_month' not in st.session_state:
    st.session_state.selected_month = months[0] if months else None

# Create month buttons for each group
for group, columns in zip(month_groups, column_groups):
    create_month_buttons(columns, group)

# Get the selected month
selected_month = st.session_state.selected_month

# If a month is selected, proceed with the analysis
if selected_month:
    # Filter data for selected month
    month_data = df[df['Month'] == selected_month]

    # Group spending by category (negative amounts only, excluding Savings)
    category_spending = month_data[
        (month_data['Amount'] < 0) & 
        (month_data['Category'] != 'Savings')
    ].groupby('Category')['Amount'].sum().abs().sort_values(ascending=False)

    # Only create and display the pie chart if there are spending categories
    if not category_spending.empty:
        # Create two columns
        col1, col2 = st.columns([1, 1])  # Adjust ratio as needed

        with col1:
            # Custom color palette
            custom_colors = [
                '#1F77B4', '#FF7F0E', '#2CA02C', '#D62728', '#9467BD', 
                '#8C564B', '#E377C2', '#7F7F7F', '#BCBD22', '#17BECF'
            ]

            # Create a pie chart
            fig = px.pie(
                values=category_spending.values, 
                names=category_spending.index, 
                title=f'Spending Categories for {selected_month}',
                color_discrete_sequence=custom_colors
            )

            # Customize the chart
            fig.update_traces(
                textposition='inside', 
                textinfo='percent+label',
                textfont=dict(color='white', size=12)
            )
            fig.update_layout(
                title={
                    'text': f'Spending Categories for {selected_month}',
                    'y':0.95,
                    'x':0.5,
                    'xanchor': 'center',
                    'yanchor': 'top',
                    'font': dict(size=24)
                },
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                showlegend=False
            )

            # Display the chart
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Create spending breakdown table
            spending_breakdown = category_spending.to_frame()
            spending_breakdown.columns = ['Total Spent']
            spending_breakdown['Total Spent'] = spending_breakdown['Total Spent'].map('${:,.2f}'.format)
            
            # Centered title with consistent styling
            st.markdown(
                f'<div style="text-align: center; font-size: 1.5rem; font-weight: bold; margin-bottom: 20px;">'
                f'Spending Breakdown - {selected_month}'
                f'</div>', 
                unsafe_allow_html=True
            )
            # More comprehensive CSS to center table text
            st.markdown("""
            <style>
            .stTable {
                margin: 0 auto;  /* Center the entire table */
                width: auto;     /* Adjust width to content */
                text-align: center;
            }
            .stTable th {
                text-align: center !important;
                color: white;
            }
            .stTable td {
                text-align: center !important;
            }
            .stTable tr:nth-child(even) {
                background-color: #222222;
            }
            .stTable tr:nth-child(odd) {
                background-color: #1a1a1a;
            }
            </style>
            """, unsafe_allow_html=True)

            st.table(spending_breakdown)
    else:
        st.warning(f"No spending data available for {selected_month}")
else:
    st.warning("No months with data are currently available")

st.divider()

# Data Preview with formatted Date and Amount columns for easier viewing
with st.expander("Data Preview"):
    st.dataframe(
        df[['Date', 'Amount', 'Description', 'Paid To', 'Category', 'Method']],     
        column_config={
            "Amount": st.column_config.NumberColumn(format="dollar"),
            "Date": st.column_config.DatetimeColumn(format="MM/DD/YY")
        }
    )