import streamlit as st
import folium
from streamlit_folium import st_folium
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
import pyvista as pv
from stpyvista import stpyvista

from stpyvista.utils import start_xvfb

if "IS_XVFB_RUNNING" not in st.session_state:
    start_xvfb()
    st.session_state.IS_XVFB_RUNNING = True

# Define the buildingStandard dictionary here, so it's accessible in the main() function
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

def reverse_geocode(lat, lon):
    geolocator = Nominatim(user_agent="streamlit_geopy_user")
    try:
        location = geolocator.reverse((lat, lon), exactly_one=True)
        if location:
            return location.address
    except (GeocoderTimedOut, GeocoderUnavailable) as e:
        st.error(f"Geocoding error: {e}")
    return None

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

def main():
    st.sidebar.image('https://www.bim4energy.eu/wp-content/uploads/2024/02/Geometric-Logo-3_Colors-1.png', width=300)
    st.title('BIM4ENERGY Assessment')

    with st.sidebar:
        st.header('Select Your Location on the Map')
        DEFAULT_LATITUDE, DEFAULT_LONGITUDE = 59.9139, 10.7522
        m = folium.Map(location=[DEFAULT_LATITUDE, DEFAULT_LONGITUDE], zoom_start=4)
        m.add_child(folium.LatLngPopup())
        f_map = st_folium(m, width=330, height=500)
        country_name, selected_coordinates = "Norway", f"{DEFAULT_LATITUDE}, {DEFAULT_LONGITUDE}"
        if f_map.get("last_clicked"):
            selected_latitude = f_map["last_clicked"]["lat"]
            selected_longitude = f_map["last_clicked"]["lng"]
            selected_coordinates = f"{selected_latitude}, {selected_longitude}"
            address = reverse_geocode(selected_latitude, selected_longitude)
            if address:
                country_name = address.split(',')[-1].strip()
        st.header('Project Information')
        projectName = st.text_input('Project Name', 'My Project 1')
        country = st.text_input('Country', country_name)
        coordinates = st.text_input('Coordinates', value=selected_coordinates)
        buildingType = st.selectbox('Building Type', ['Residential', 'Commercial', 'Industrial'])
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

    col1, col2 = st.columns([3, 2])

    with col1:
        @st.cache_resource
        def stpv_usage_example(number_floors: int, dummy: str = "cube") -> pv.Plotter:
            plotter = pv.Plotter(window_size=[400, 400])
            mesh = pv.Cube(center=(0, 0, 0), x_length=2, y_length=2, z_length=number_floors)
            mesh["myscalar"] = mesh.points[:, 2] * mesh.points[:, 1] * mesh.points[:, 0]
            plotter.add_mesh(
                mesh, color=(0.5, 0.5, 0.5), show_edges=True, edge_color="#001100"
            )
            plotter.background_color = "white"
            plotter.view_isometric()
            return plotter

        stpyvista(stpv_usage_example(numberFloorsAboveGround))

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
