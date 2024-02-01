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

if "IS_XVFB_RUNNING" not in st.session_state:
    start_xvfb()
    st.session_state.IS_XVFB_RUNNING = True

# Building Standard dictionary and other functions...

def main():
    # Streamlit UI components...

    col1, col2 = st.columns([3, 2])

    with col1:
        @st.cache_resource
        def stpv_usage_example(number_floors: int, dummy: str = "cube") -> pv.Plotter:
            plotter = pv.Plotter(window_size=[400, 400])

            # Create a mesh with a cube for the main part of the house
            house_base = pv.Cube(center=(0, 0, number_floors / 2), x_length=2, y_length=2, z_length=number_floors)

            # Adding a door as a thin box
            door = pv.Box(bounds=(-0.4, 0.4, -1, -0.8, 0, 0.8))
            door.translate((0, 0, 0.4))

            # Adding a window as a thin box
            window = pv.Box(bounds=(-0.9, -0.5, 0.5, 0.9, number_floors - 0.5, number_floors - 0.1))
            window.translate((0, 0, number_floors / 2))

            # Subtract the door and window from the house base
            house_with_holes = house_base.boolean_difference(door).boolean_difference(window)
            plotter.add_mesh(house_with_holes, color=(0.7, 0.7, 0.7))  # Grey color for walls

            # Create a mesh for the roof - using a triangular prism
            roof_points = np.array([
                [-1, -1, number_floors],  # Base left
                [1, -1, number_floors],   # Base right
                [1, 1, number_floors],    # Base front
                [-1, 1, number_floors],   # Base back
                [0, 0, number_floors + 1] # Apex
            ])
            roof_faces = np.hstack([[4, 0, 1, 2, 3],  # Base
                                    [3, 0, 1, 4],     # Side 1
                                    [3, 1, 2, 4],     # Side 2
                                    [3, 2, 3, 4],     # Side 3
                                    [3, 3, 0, 4]])    # Side 4
            roof = pv.PolyData(roof_points, roof_faces)
            plotter.add_mesh(roof, color=(0.8, 0, 0))  # Red color for roof

            plotter.background_color = "white"
            plotter.view_isometric()

            return plotter

        stpyvista(stpv_usage_example(numberFloorsAboveGround))

    with col2:
        # Project Information display...

    # Rest of the main function...

if __name__ == "__main__":
    main()
