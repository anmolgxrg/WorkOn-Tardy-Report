import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
from fpdf import FPDF
import os
import tempfile
import matplotlib.pyplot as plt
import base64

DATA_FILE = 'late_punch_data.xlsx'

# Load or create the initial data
def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_excel(DATA_FILE)
    else:
        return pd.DataFrame(columns=['Name', 'Date', 'Minutes Late'])

def save_data(df):
    df.to_excel(DATA_FILE, index=False)

# Function to create download link for PDF
def create_download_link(file_path, file_label):
    with open(file_path, "rb") as f:
        bytes_data = f.read()
    b64 = base64.b64encode(bytes_data).decode()
    href = f'<a href="data:file/pdf;base64,{b64}" download="{file_label}">Download PDF Report</a>'
    return href

# Initialize data
data = load_data()

st.title('Employee Late Punch Report Visualizer')

# Create tabs for navigation
tabs = st.tabs(["Upload and Visualize Data", "Enter Data", "View Data"])

with tabs[0]:
    st.header('Upload and Visualize Data')

    # Automatically use existing data
    df = data
    df['Date'] = pd.to_datetime(df['Date'])

    # Select time period
    time_option = st.selectbox("Select Time Period", ["Specific Date", "Specific Week", "Life to Date (LTD)"])

    if time_option == "Specific Date":
        selected_date = st.date_input("Select Date")
        filtered_df = df[df['Date'] == pd.to_datetime(selected_date)]
    elif time_option == "Specific Week":
        selected_week = st.date_input("Select Week")
        start_of_week = pd.to_datetime(selected_week - datetime.timedelta(days=selected_week.weekday()))
        end_of_week = start_of_week + datetime.timedelta(days=6)
        filtered_df = df[(df['Date'] >= start_of_week) & (df['Date'] <= end_of_week)]
    else:
        filtered_df = df

    if not filtered_df.empty:
        # Generate bar graphs
        total_late_minutes = filtered_df.groupby('Name')['Minutes Late'].sum().sort_values(ascending=False)
        late_instances = filtered_df['Name'].value_counts()

        st.subheader("Total Late Minutes by Employee")
        fig1 = px.bar(total_late_minutes, labels={'value':'Total Late Minutes', 'index':'Employee'}, title='Total Late Minutes by Employee')
        fig1.update_traces(marker_color='rgb(55, 83, 109)')
        fig1.update_layout(title_font_size=20, xaxis_title_font_size=16, yaxis_title_font_size=16, template='plotly_white')
        st.plotly_chart(fig1)

        st.subheader("Number of Late Instances by Employee")
        fig2 = px.bar(late_instances, labels={'value':'Number of Late Instances', 'index':'Employee'}, title='Number of Late Instances by Employee')
        fig2.update_traces(marker_color='rgb(26, 118, 255)')
        fig2.update_layout(title_font_size=20, xaxis_title_font_size=16, yaxis_title_font_size=16, template='plotly_white')
        st.plotly_chart(fig2)

        # Generate line plots for each employee
        unique_employees = filtered_df['Name'].unique()
        for employee in unique_employees:
            employee_data = filtered_df[filtered_df['Name'] == employee]
            if not employee_data.empty:
                fig = px.line(employee_data, x='Date', y='Minutes Late', title=f'Late Minutes Over Time for {employee}', labels={'Date':'Date', 'Minutes Late':'Late Minutes'})
                fig.update_traces(line=dict(color='rgb(255, 127, 14)', width=2), marker=dict(color='rgb(255, 127, 14)', size=6))
                fig.update_layout(title_font_size=20, xaxis_title_font_size=16, yaxis_title_font_size=16, template='plotly_white')
                st.plotly_chart(fig)

        # Generate a collage of line plots
        num_employees = len(unique_employees)
        cols = 3
        rows = (num_employees // cols) + (num_employees % cols > 0)

        fig, axes = plt.subplots(rows, cols, figsize=(15, 5 * rows))
        axes = axes.flatten()

        for i, employee in enumerate(unique_employees):
            employee_data = filtered_df[filtered_df['Name'] == employee]
            if not employee_data.empty:
                axes[i].plot(employee_data['Date'], employee_data['Minutes Late'], marker='o', linestyle='-', color='orange')
                axes[i].set_title(employee)
                axes[i].set_xlabel('Date')
                axes[i].set_ylabel('Late Minutes')
                axes[i].tick_params(axis='x', rotation=45)

        for j in range(i + 1, len(axes)):
            fig.delaxes(axes[j])

        fig.tight_layout()
        collage_path = 'employee_late_minutes_collage.png'
        fig.savefig(collage_path)

        # Option to download report as PDF
        if st.button('Download Report as PDF'):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=16)
            pdf.cell(200, 10, txt="Employee Late Punch Report", ln=True, align='C')

            # Save temporary images for the PDF
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile1:
                fig1.write_image(tmpfile1.name)
                pdf.image(tmpfile1.name, x=10, y=30, w=190)
            pdf.add_page()
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile2:
                fig2.write_image(tmpfile2.name)
                pdf.image(tmpfile2.name, x=10, y=30, w=190)

            pdf.add_page()
            pdf.image(collage_path, x=10, y=30, w=190)

            pdf_output = 'Employee_Late_Punch_Report.pdf'
            pdf.output(pdf_output)
            st.success('Report created successfully!')
            st.markdown(create_download_link(pdf_output, 'Employee_Late_Punch_Report.pdf'), unsafe_allow_html=True)
    else:
        st.warning('No data available for the selected period.')

with tabs[1]:
    st.header('Enter New Late Punch Data')

    # Form to enter new data
    with st.form(key='late_punch_form'):
        name = st.selectbox("Employee Name", options=list(data['Name'].unique()) + ['Other'])
        if name == 'Other':
            name = st.text_input("Enter Employee Name")

        date = st.date_input("Date")
        minutes_late = st.number_input("Minutes Late", min_value=0)

        submit_button = st.form_submit_button(label='Submit')

        if submit_button:
            # Add new data to the dataframe
            new_data = pd.DataFrame({
                'Name': [name],
                'Date': [date],
                'Minutes Late': [minutes_late]
            })
            updated_df = pd.concat([data, new_data], ignore_index=True)

            # Save updated dataframe to Excel
            save_data(updated_df)
            data = load_data()

            st.success(f'Data for {name} added successfully!')

with tabs[2]:
    st.header('View Late Punch Data')
    st.dataframe(data)