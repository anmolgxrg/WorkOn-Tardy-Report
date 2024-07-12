import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
from fpdf import FPDF
import os
import tempfile

DATA_FILE = 'late_punch_data.xlsx'

# Load or create the initial data
def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_excel(DATA_FILE)
    else:
        return pd.DataFrame(columns=['Name', 'Date', 'Minutes Late'])

def save_data(df):
    df.to_excel(DATA_FILE, index=False)

# Initialize data
data = load_data()

st.title('Employee Late Punch Report Visualizer')

# Create a sidebar for navigation
st.sidebar.title('Navigation')
page = st.sidebar.selectbox("Go to", ["Upload and Visualize Data", "Enter Data", "View Data"])

if page == "Upload and Visualize Data":
    st.header('Upload the Late Punch Report')

    # Automatically use existing data
    df = data

    # Select time period
    time_option = st.selectbox("Select Time Period", ["Specific Date", "Specific Week", "Life to Date (LTD)"])

    if time_option == "Specific Date":
        selected_date = st.date_input("Select Date")
        filtered_df = df[df['Date'] == pd.to_datetime(selected_date)]
    elif time_option == "Specific Week":
        selected_week = st.date_input("Select Week")
        start_of_week = selected_week - datetime.timedelta(days=selected_week.weekday())
        end_of_week = start_of_week + datetime.timedelta(days=6)
        filtered_df = df[(df['Date'] >= start_of_week) & (df['Date'] <= end_of_week)]
    else:
        filtered_df = df

    if not filtered_df.empty:
        # Generate bar graphs
        total_late_minutes = filtered_df.groupby('Name')['Minutes Late'].sum().sort_values(ascending=False)
        late_instances = filtered_df['Name'].value_counts()

        st.subheader("Total Late Minutes by Employee")
        fig1 = px.bar(total_late_minutes, labels={'value':'Total Late Minutes', 'index':'Employee'})
        st.plotly_chart(fig1)

        st.subheader("Number of Late Instances by Employee")
        fig2 = px.bar(late_instances, labels={'value':'Number of Late Instances', 'index':'Employee'})
        st.plotly_chart(fig2)

        # Generate line plots for each employee
        unique_employees = filtered_df['Name'].unique()
        for employee in unique_employees:
            employee_data = filtered_df[filtered_df['Name'] == employee]
            if not employee_data.empty:
                fig = px.line(employee_data, x='Date', y='Minutes Late', title=f'Late Minutes Over Time for {employee}', labels={'Date':'Date', 'Minutes Late':'Late Minutes'})
                st.plotly_chart(fig)

        # Option to download report as PDF
        if st.button('Download Report as PDF'):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, txt="Employee Late Punch Report", ln=True, align='C')

            # Save temporary images for the PDF
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile1:
                fig1.write_image(tmpfile1.name)
                pdf.image(tmpfile1.name, x=10, y=30, w=190)
            pdf.add_page()
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile2:
                fig2.write_image(tmpfile2.name)
                pdf.image(tmpfile2.name, x=10, y=30, w=190)
            
            # Add individual employee graphs
            for employee in unique_employees:
                employee_data = filtered_df[filtered_df['Name'] == employee]
                if not employee_data.empty:
                    fig = px.line(employee_data, x='Date', y='Minutes Late', title=f'Late Minutes Over Time for {employee}', labels={'Date':'Date', 'Minutes Late':'Late Minutes'})
                    pdf.add_page()
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
                        fig.write_image(tmpfile.name)
                        pdf.image(tmpfile.name, x=10, y=30, w=190)

            pdf_output = '/mnt/data/Employee_Late_Punch_Report.pdf'
            pdf.output(pdf_output)
            st.success(f'Report saved as {pdf_output}')
            st.write(f"[Download the report](sandbox:/mnt/data/Employee_Late_Punch_Report.pdf)")
    else:
        st.warning('No data available for the selected period.')

elif page == "Enter Data":
    st.header('Enter New Late Punch Data')

    # Form to enter new data
    with st.form(key='late_punch_form'):
        name = st.selectbox("Employee Name", options=list(data['Name'].unique()) + ['Other'])
        if name == 'Other':
            name = st.text_input("Enter Employee Name")

        num_entries = st.number_input("Number of entries", min_value=1, step=1)
        dates_late = []
        minutes_late = []

        for i in range(num_entries):
            st.write(f"Entry {i+1}")
            date = st.date_input(f"Date {i+1}", key=f'date_{i}')
            minutes = st.number_input(f"Minutes Late {i+1}", min_value=0, key=f'minutes_{i}')
            dates_late.append(date)
            minutes_late.append(minutes)

        submit_button = st.form_submit_button(label='Submit')

        if submit_button:
            # Add new data to the dataframe
            new_data = pd.DataFrame({
                'Name': [name] * len(dates_late),
                'Date': dates_late,
                'Minutes Late': minutes_late
            })
            updated_df = pd.concat([data, new_data], ignore_index=True)

            # Save updated dataframe to Excel
            save_data(updated_df)
            data = load_data()

            st.success(f'Data for {name} added successfully!')

elif page == "View Data":
    st.header('View Late Punch Data')
    st.dataframe(data)