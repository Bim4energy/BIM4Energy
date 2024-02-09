import streamlit as st
import folium
from streamlit_folium import st_folium
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
import pyvista as pv
import numpy as np
from stpyvista import stpyvista
from stpyvista.utils import start_xvfb

# Initializes virtual framebuffer for headless server operation
if "IS_XVFB_RUNNING" not in st.session_state:
    start_xvfb()
    st.session_state.IS_XVFB_RUNNING = True

# Sets Streamlit page configuration
st.set_page_config(layout="wide")

# Energy standards data
buildingStandard = {
    "Norway": {
        "TEK87": {
            "Single Family": {
                "Space Heating": 100,
                "Service Water Heating": 20,
                "Fans and Pumps": 6,
                "Internal Lighting": 24,
                "Miscellaneous": 25
            }
        },
        "TEK97": {
            "Single Family": {
                "Space Heating": 93,
                "Service Water Heating": 31,
                "Fans and Pumps": 8,
                "Internal Lighting": 18,
                "Miscellaneous": 24
            }
        },
    }
}

# Function to perform reverse geocoding
def reverse_geocode(lat, lon):
    geolocator = Nominatim(user_agent="streamlit_geopy_user")
    try:
        location = geolocator.reverse((lat, lon), exactly_one=True)
        if location:
            return location.address
    except (GeocoderTimedOut, GeocoderUnavailable) as e:
        st.error(f"Geocoding error: {e}")
    return None

# Function to create a PDF report
def create_pdf(project_info, energy_consumption):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.drawString(100, 800, "BIM4ENERGY Assessment Report")
    c.drawString(100, 780, f"Project Name: {project_info['projectName']}")
    c.drawString(100, 760, f"Country: {project_info['country']}")
    c.drawString(100, 740, f"Coordinates: {project_info['coordinates']}")
    y_position = 720
    for key, value in energy_consumption.items():
        c.drawString(100, y_position, f"{key}: {value} kWh")
        y_position -= 20
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.getvalue()

# Main function defining the Streamlit app
def main():
    st.sidebar.image('https://www.bim4energy.eu/wp-content/uploads/2024/02/Header_EU_Logo-1.png', width=315)
    st.title('BIM4ENERGY Assessment')

    with st.sidebar:
        st.header('Select Your Location on the Map')
        DEFAULT_LATITUDE, DEFAULT_LONGITUDE = 59.9139, 10.7522
        map_object = folium.Map(location=[DEFAULT_LATITUDE, DEFAULT_LONGITUDE], zoom_start=4)
        map_object.add_child(folium.LatLngPopup())
        folium_map = st_folium(map_object, width=450, height=500)
        country_name, selected_coordinates = "Norway", f"{DEFAULT_LATITUDE}, {DEFAULT_LONGITUDE}"
        if folium_map.get("last_clicked"):
            selected_latitude = folium_map["last_clicked"]["lat"]
            selected_longitude = folium_map["last_clicked"]["lng"]
            selected_coordinates = f"{selected_latitude}, {selected_longitude}"
            address = reverse_geocode(selected_latitude, selected_longitude)
            if address:
                country_name = address.split(',')[-1].strip()

        st.header('Project Information')
        projectName = st.text_input('Project Name', 'My Project 1')
        country = st.text_input('Country', country_name)
        coordinates = st.text_input('Coordinates', value=selected_coordinates)
        buildingType = st.selectbox('Building Type', ['Residential', 'Commercial', 'Educational'])
        yearConstructionCompletion = st.text_input('Year of Construction Completion', '1950')
        numberBuildingUsers = st.number_input('Number of Building Users', min_value=1, value=4, step=1)

        st.header('Building Information')
        areaGrossFloor = st.number_input('Gross Floor Area', value=200)
        conditionedArea = st.number_input('Conditioned Area', value=150)
        numberFloorsAboveGround = st.number_input('Number of Floors Above Ground', value=2, min_value=0)
        numberFloorsBelowGround = st.number_input('Number of Floors Below Ground', value=0, min_value=0)
        heightFloorToCeiling = st.number_input('Height from Floor to Ceiling', value=3.0)

        st.header('Assessment Information')
        selectBuildingStandard = st.selectbox('Building Standard', ['TEK87', 'TEK97'])

    project_info = {
        'projectName': projectName,
        'country': country,
        'coordinates': coordinates,
    }
    energy_consumption = {
        "Space Heating": areaGrossFloor * buildingStandard["Norway"][selectBuildingStandard]["Single Family"]["Space Heating"],
        "Service Water Heating": areaGrossFloor * buildingStandard["Norway"][selectBuildingStandard]["Single Family"]["Service Water Heating"],
        "Fans and Pumps": areaGrossFloor * buildingStandard["Norway"][selectBuildingStandard]["Single Family"]["Fans and Pumps"],
        "Internal Lighting": areaGrossFloor * buildingStandard["Norway"][selectBuildingStandard]["Single Family"]["Internal Lighting"],
        "Miscellaneous": areaGrossFloor * buildingStandard["Norway"][selectBuildingStandard]["Single Family"]["Miscellaneous"]
    }

    col1, col2 = st.columns([0.7, 0.3])

    with col1:
        @st.cache_resource
        def stpv_usage_example(number_floors: int, building_type: str) -> pv.Plotter:
            plotter = pv.Plotter()
            ground = pv.Plane(center=(0, 0, -0.01), i_size=20, j_size=20)  # Simulating the ground
            plotter.add_mesh(ground, color='green')  # Adding the ground to the plotter with green color
            
            if building_type == "Residential":
                house_base = pv.Cube(center=(0, 0, 0), x_length=4, y_length=4, z_length=number_floors)
                roof = pv.Cone(center=(0, 0, number_floors), radius=3, height=2, direction=(0, 0, 1))  # Simulating the roof
                building = house_base + roof
                plotter.add_mesh(building, color=(0.7, 0.7, 0.7), show_edges=True, edge_color="black")
            elif building_type == "Commercial":
                building = pv.read("test.stl")
                plotter.add_mesh(building, color=(0.5, 0.5, 0.5), show_edges=True)
            elif building_type == "Educational":
                main_block = pv.Cube(center=(0, 0, number_floors / 2), x_length=6, y_length=6, z_length=number_floors)
                secondary_block = pv.Cube(center=(4, 4, number_floors / 2), x_length=3, y_length=3, z_length=number_floors * 0.75)
                tertiary_block = pv.Cube(center=(-4, -4, number_floors / 2), x_length=3, y_length=3, z_length=number_floors * 0.5)
                building = main_block + secondary_block + tertiary_block
                plotter.add_mesh(building, color=(0.7, 0.7, 0.7), show_edges=True, edge_color="black")
            
            plotter.background_color = "white"
            plotter.view_isometric()
            return plotter

        stpyvista(stpv_usage_example(numberFloorsAboveGround, buildingType))

    with col2:
        st.subheader('Project Information')
        st.write(f"Project Name: {projectName}")
        st.write(f"Country: {country}")
        st.write(f"Coordinates: {coordinates}")
        st.write(f"Building Type: {buildingType}")
        st.write(f"Year of Construction Completion: {yearConstructionCompletion}")
        st.write(f"Number of Building Users: {numberBuildingUsers}")
        st.subheader('Energy Consumption')
        for key, value in energy_consumption.items():
            st.write(f"{key}: {value} kWh")
        if st.button('Generate PDF Report'):
            pdf_bytes = create_pdf(project_info, energy_consumption)
            st.download_button(label="Download PDF Report",
                               data=pdf_bytes,
                               file_name="BIM4ENERGY_Report.pdf",
                               mime="application/pdf")

if __name__ == "__main__":
    main()
