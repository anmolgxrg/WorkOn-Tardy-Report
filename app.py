import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
from fpdf import FPDF
import os
import tempfile
import matplotlib.pyplot as plt
import base64

st.set_page_config(layout="wide", page_title="Tardy Report - HFS Technical Service", page_icon="/logo.png")

DATA_FILE = 'late_punch_data.xlsx'

# Load the updated data from Excel file with multiple sheets
def load_data():
    if os.path.exists(DATA_FILE):
        sheets = pd.read_excel(DATA_FILE, sheet_name=None)
        combined_data = pd.concat(sheets.values(), ignore_index=True)
        return sheets, combined_data
    else:
        return {}, pd.DataFrame(columns=['Name', 'Date', 'Minutes Late', 'Manager'])

def save_data(sheets):
    with pd.ExcelWriter(DATA_FILE) as writer:
        for manager, df in sheets.items():
            df.to_excel(writer, sheet_name=manager, index=False)

# Function to create download link for PDF
def create_download_link(file_path, file_label):
    with open(file_path, "rb") as f:
        bytes_data = f.read()
    b64 = base64.b64encode(bytes_data).decode()
    href = f'<a href="data:file/pdf;base64,{b64}" download="{file_label}">Download PDF Report</a>'
    return href

# Employee groups
employee_groups = {
    "Craig Cook": [
        "Paige Kruger",
        "Athan Spanos",
        "Jerwin Orendain",
        "Gerard McLaughlin",
        "Kristen Reisinger"
    ],
    "Paige Kruger": [
        "Claudio Tarallo",
        "Kathleen Greenleaf",
        "Stacy O'Connor",
        "Jeffrey Furlow",
        "Karna Karki",
        "Jeff Roman",
        "Julie Tanczos",
        "Robert Louder",
        "Sammi Atland",
        "Susan Hook-Smeal",
        "Delores Kohler",
        "Reginald Fields"
    ],
    "Claudio Tarallo": [
        "Justin Schultz",
        "Chelsea Haylett",
        "Darlene Gratkowski",
        "Paula Cramer",
        "Kirk Beard",
        "Daniel Sokalczuk",
        "Rhiannon Lorenez",
        "Neiby Gomez"
    ],
    "Gerard McLaughlin": [
        "Steve Russell",
        "Kerry Dreibelbis",
        "Ted Verbinski",
        "Terry Rabuck",
        "Stoy Sunday"
    ],
    "Athan Spanos": [
        "Paul Motter",
        "David Cramer",
        "John Lay",
        "Emily Getz",
        "Ryan Dann",
        "Eli Schott",
        "Madison Cooper",
        "Phillip Ponsole"
    ],
    "Jerwin Orendain": [
        "Connor Campbell",
        "Ginny Miller",
        "Julie McNamara"
    ]
}

# Function to assign managers based on employee_groups
def assign_managers(df):
    manager_col = []
    for name in df['Name']:
        assigned = False
        for manager, employees in employee_groups.items():
            if name in employees:
                manager_col.append(manager)
                assigned = True
                break
        if not assigned:
            manager_col.append(None)
    df['Manager'] = manager_col
    return df

# Function to get the manager for a given employee
def get_manager(employee_name):
    for manager, employees in employee_groups.items():
        if employee_name in employees:
            return manager
    return None

# Initialize data
sheets, data = load_data()
data = assign_managers(data)

st.title('Tardy Report for HFS Technical Service')

# Create tabs for navigation
tabs = st.tabs(["Upload and Visualize Data", "Enter Data", "View Data"])

with tabs[0]:
    st.header('Upload and Visualize Data')

    # Automatically use existing data
    df = data
    df['Date'] = pd.to_datetime(df['Date'])

    # Select time period
    time_option = st.selectbox("Select Time Period", ["Specific Date", "Specific Week", "Life to Date (LTD)"], key='time_period')

    if time_option == "Specific Date":
        selected_date = st.date_input("Select Date", key='specific_date')
        filtered_df = df[df['Date'] == pd.to_datetime(selected_date)]
    elif time_option == "Specific Week":
        selected_week = st.date_input("Select Week", key='specific_week')
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

        # Generate graphs for total minutes late by manager and total number of tardy employees by manager
        manager_minutes_late = filtered_df.groupby('Manager')['Minutes Late'].sum().sort_values(ascending=False)
        tardy_employees_by_manager = filtered_df.groupby('Manager')['Name'].nunique().sort_values(ascending=False)

        st.subheader("Total Late Minutes by Manager")
        fig3 = px.bar(manager_minutes_late, labels={'value':'Total Late Minutes', 'index':'Manager'}, title='Total Late Minutes by Manager')
        fig3.update_traces(marker_color='rgb(26, 118, 255)')
        fig3.update_layout(title_font_size=20, xaxis_title_font_size=16, yaxis_title_font_size=16, template='plotly_white')
        st.plotly_chart(fig3)

        st.subheader("Total Number of Tardy Employees by Manager")
        fig4 = px.bar(tardy_employees_by_manager, labels={'value':'Number of Tardy Employees', 'index':'Manager'}, title='Total Number of Tardy Employees by Manager')
        fig4.update_traces(marker_color='rgb(55, 83, 109)')
        fig4.update_layout(title_font_size=20, xaxis_title_font_size=16, yaxis_title_font_size=16, template='plotly_white')
        st.plotly_chart(fig4)

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
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile3:
                fig3.write_image(tmpfile3.name)
                pdf.image(tmpfile3.name, x=10, y=30, w=190)
            pdf.add_page()
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile4:
                fig4.write_image(tmpfile4.name)
                pdf.image(tmpfile4.name, x=10, y=30, w=190)

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
        name = st.selectbox("Employee Name", options=[x for x in data['Name'].unique() if pd.notna(x)] + ['Other'], key='employee_name')
        if name == 'Other':
            name = st.text_input("Enter Employee Name", key='new_employee_name')
        
        manager = get_manager(name) if name != 'Other' else st.text_input("Enter Manager", key='new_manager_name')
        st.text_input("Manager", value=manager, key='entry_manager', disabled=True)

        date = st.date_input("Date", key='entry_date')
        minutes_late = st.number_input("Minutes Late", min_value=0, key='entry_minutes_late')

        submit_button = st.form_submit_button(label='Submit')

        if submit_button:
            if name == 'Other':
                name = st.session_state['new_employee_name']
                manager = st.session_state['new_manager_name']
            else:
                manager = get_manager(name)

            # Add new data to the corresponding manager's sheet
            if manager in sheets:
                manager_df = sheets[manager]
            else:
                manager_df = pd.DataFrame(columns=['Name', 'Date', 'Minutes Late', 'Manager'])

            new_data = pd.DataFrame({
                'Name': [name],
                'Date': [date],
                'Minutes Late': [minutes_late],
                'Manager': [manager]
            })

            updated_manager_df = pd.concat([manager_df, new_data], ignore_index=True)
            sheets[manager] = updated_manager_df

            # Save updated dataframe to Excel
            save_data(sheets)
            sheets, data = load_data()
            data = assign_managers(data)

            st.success(f'Data for {name} added successfully!')

with tabs[2]:
    st.header('View Data')
    
    if st.checkbox('Show raw data', key='show_raw_data'):
        st.dataframe(data)

    st.subheader('Delete Entries')
    if not data.empty:
        selected_rows = st.multiselect('Select rows to delete', data.index, key='delete_rows')
        if st.button('Delete selected rows'):
            if selected_rows:
                data = data.drop(selected_rows)
                manager_groups = data.groupby('Manager')
                for manager, group in manager_groups:
                    sheets[manager] = group.drop(columns=['Manager'])
                save_data(sheets)
                st.success('Selected rows have been deleted.')
            else:
                st.warning('No rows selected.')

    st.subheader('Current Data')
    st.dataframe(data)
