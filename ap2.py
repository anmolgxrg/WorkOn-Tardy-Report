import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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
        # Other employees...
    ]
}

# Load existing data
sheets, combined_data = load_data()

# Add a new entry
st.sidebar.header("Add New Entry")
name = st.sidebar.text_input("Name")
date = st.sidebar.date_input("Date", datetime.date.today())
minutes_late = st.sidebar.number_input("Minutes Late", min_value=0, max_value=60, step=1)
manager = st.sidebar.selectbox("Manager", list(employee_groups.keys()))

if st.sidebar.button("Add Entry"):
    new_entry = pd.DataFrame({
        'Name': [name],
        'Date': [date],
        'Minutes Late': [minutes_late],
        'Manager': [manager]
    })
    if manager in sheets:
        sheets[manager] = pd.concat([sheets[manager], new_entry], ignore_index=True)
    else:
        sheets[manager] = new_entry
    save_data(sheets)
    st.sidebar.success("Entry added successfully")

# View data tab
st.header("View Data")

# Combine and sort data
combined_data = pd.concat(sheets.values(), ignore_index=True)
combined_data_sorted = combined_data.sort_values(by='Name').reset_index(drop=True)

st.dataframe(combined_data_sorted)

# Delete entry
st.sidebar.header("Delete Entry")
delete_index = st.sidebar.number_input("Index to delete", min_value=0, max_value=len(combined_data_sorted)-1, step=1)
if st.sidebar.button("Delete Entry"):
    combined_data_sorted = combined_data_sorted.drop(delete_index).reset_index(drop=True)
    
    # Update sheets
    sheets = {manager: df[df['Manager'] == manager] for manager, df in combined_data_sorted.groupby('Manager')}
    save_data(sheets)
    st.sidebar.success("Entry deleted successfully")
    st.experimental_rerun()

# Add note to graph
st.sidebar.header("Add Note to Graph")
note = st.sidebar.text_input("Note")
note_date = st.sidebar.date_input("Date for Note", datetime.date.today())

# Plotting
st.header("Late Punch Report")
fig = px.scatter(combined_data_sorted, x='Date', y='Minutes Late', color='Name')

# Add annotation if note is provided
if note:
    fig.add_annotation(
        x=note_date,
        y=0,  # Adjust this value based on where you want the note to appear
        text=note,
        showarrow=True,
        arrowhead=1
    )

st.plotly_chart(fig)

# Other app functionalities...

# For example, generating reports, etc.
