import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit_gsheets import GSheetsConnection

def main():
    configure_page()
    setup_custom_css()

    # Connect to private google sheets
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = load_and_clean_data(conn)

    # Calculate and display balances
    balances = calculate_liquid_balances(df)
    display_liquid_balances(balances)
    
    # Display spending breakdown
    display_spending_breakdown(df)
    
    # Show data preview
    display_data_preview(df)

def configure_page():
    """Configure page settings and refresh button"""
    st.set_page_config(
        page_title="Budget Dashboard",
        page_icon=":bar_chart:",
        layout="wide"
    )

    if st.sidebar.button('Refresh Data'):
        st.cache_data.clear()  # Clear all cached data
        st.rerun()

def setup_custom_css():
    """Custom CSS to style dashboard"""
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

def load_and_clean_data(conn):
    """Load data from Google Sheets and perform basic cleaning"""
    # Current months in spreadsheet
    months = ['January', 'February', 'March']

    # Read in data for each month and transform into one dataframe
    dfs = [conn.read(worksheet=month, skiprows=1, usecols=[0,1,2,3,4,5]) for month in months]
    df = pd.concat(dfs, ignore_index=True)

    # Convert 'Date' to datetime
    df['Date'] = pd.to_datetime(df['Date'])

    # Extract month name for grouping
    df['Month'] = df['Date'].dt.strftime('%B')

    return df

def calculate_liquid_balances(df):
    """Calculate balances for Cash, Debit, and Savings"""
    # Separate savings transactions and calculate total savings
    savings_transfers = df[df["Category"] == "Savings"]
    savings_total = -savings_transfers["Amount"].sum()  # Convert to positive for savings total

    # Filter out 'Credit' transactions from the DataFrame
    df_filtered = df[df["Method"] != "Credit"]

    # Calculate balances for each method
    cash_balance = df_filtered[df_filtered["Method"] == "Cash"]["Amount"].sum() + 229
    debit_balance = df_filtered[df_filtered["Method"] == "Debit"]["Amount"].sum() + 5597.14
    savings_balance = savings_total

    # Create a dictionary of balances
    balances = {
        "Cash": cash_balance,
        "Debit": debit_balance,
        "Savings": savings_balance,
        "Total": cash_balance + debit_balance + savings_balance
    }

    return balances

def custom_metric(label, value):
    """Create custom card for balance metrics"""
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

def display_liquid_balances(balances):
    """Display liquid balance section"""
    # Centered Liquid Balance Header
    st.markdown('<div class="liquid-balance-header">Liquid Balances</div>', unsafe_allow_html=True)

    # Create a row of four cards to display balance summary
    col1, col2, col3, col4 = st.columns(4)

    # Display the cards
    with col1:
        st.markdown(custom_metric("Cash", balances["Cash"]), unsafe_allow_html=True)

    with col2:
        st.markdown(custom_metric("Debit", balances["Debit"]), unsafe_allow_html=True)

    with col3:
        st.markdown(custom_metric("Savings", balances["Savings"]), unsafe_allow_html=True)

    with col4:
        st.markdown(custom_metric("Total", balances["Total"]), unsafe_allow_html=True)

def create_month_selector(available_months):
    """Create a month selector interface"""
    # Define all 12 months
    all_months = [
        'January', 'February', 'March', 'April', 
        'May', 'June', 'July', 'August', 
        'September', 'October', 'November', 'December'
    ]

    # Create columns for month selection (6 columns in first row, 6 in second)
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col7, col8, col9, col10, col11, col12 = st.columns(6)

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
        st.session_state.selected_month = available_months[0] if available_months else None

    # Create month buttons for each group
    for group_idx, group in enumerate(month_groups):
        for month_idx, month in enumerate(group):
            with column_groups[group_idx][month_idx]:
                is_available = month in available_months
                month_button = st.button(
                    month, 
                    disabled=not is_available, 
                    key=month,
                    use_container_width=True
                )
                if month_button:
                    st.session_state.selected_month = month

    return st.session_state.selected_month

def create_spending_pie_chart(category_spending, selected_month):
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

    return fig

def display_spending_breakdown(df):
    # Spending Breakdown Section
    st.markdown('<div class="liquid-balance-header" style="margin-top: 20px;">Spending Breakdown</div>', unsafe_allow_html=True)

    # Available months in the data
    available_months = df['Month'].unique().tolist()
    
    # Create month selector
    selected_month = create_month_selector(available_months)

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
                # Create and display pie chart
                fig = create_spending_pie_chart(category_spending, selected_month)
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
                st.table(spending_breakdown)
        else:
            st.warning(f"No spending data available for {selected_month}")
    else:
        st.warning("No months with data are currently available")

    st.divider()

def display_data_preview(df):
    """Displays preview of raw data"""
    # Data Preview with formatted Date and Amount columns for easier viewing
    with st.expander("Data Preview"):
        st.dataframe(
            df[['Date', 'Amount', 'Description', 'Paid To', 'Category', 'Method']],     
            column_config={
                "Amount": st.column_config.NumberColumn(format="dollar"),
                "Date": st.column_config.DatetimeColumn(format="MM/DD/YY")
            }
        )

if __name__ == "__main__":
    main()