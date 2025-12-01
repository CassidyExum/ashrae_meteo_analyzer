import streamlit as st
import pandas as pd
import requests
import json
from typing import List, Dict, Optional
import math

# Set page configuration
st.set_page_config(
    page_title="ASHRAE Meteo Station Finder",
    page_icon="🌤️",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #374151;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
    }
    .station-card {
        background-color: #F3F4F6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #3B82F6;
        margin-bottom: 1rem;
    }
    .data-table {
        background-color: white;
        border-radius: 10px;
        padding: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .metric-card {
        background-color: #EFF6FF;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border: 1px solid #BFDBFE;
    }
</style>
""", unsafe_allow_html=True)

# API Functions
def get_url_generator(lat: float, long: float, num_stations: int = 10, version: int = 2017) -> str:
    """Generate URL for ASHRAE stations API"""
    url = 'https://ashrae-meteo.info/v3.0/request_places_get.php?'
    url1 = url + 'lat=' + str(lat) + '&long=' + str(long) + '&number=' + str(num_stations) + '&ashrae_version=' + str(version)
    return url1

def get_nearest_stations(lat: float, long: float, num_stations: int = 10) -> List[Dict]:
    """
    Get nearest weather stations to given coordinates
    """
    url = get_url_generator(lat, long, num_stations)
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        stations = data.get('meteo_stations', [])
        
        if not stations:
            return []
        
        # Add calculated distance in miles (approximate)
        # Convert radians to miles: 1 radian ≈ 3958.8 miles
        for station in stations:
            radians = float(station.get('tt', 0))
            station['distance_miles'] = round(radians * 3958.8, 2)
        
        return stations
        
    except Exception as e:
        st.error(f"Error fetching stations: {e}")
        return []

def get_station_data(wmo: str, ashrae_version: int = 2017, si_ip: str = "SI") -> Optional[Dict]:
    """
    Get detailed meteorological data for a specific station by WMO code
    """
    url = f"https://ashrae-meteo.info/v3.0/request_meteo_parametres_get.php?wmo={wmo}&ashrae_version={ashrae_version}&si_ip={si_ip}"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        stations = data.get('meteo_stations', [])
        
        if not stations:
            return None
        
        return stations[0]
        
    except Exception as e:
        st.error(f"Error fetching station data: {e}")
        return None

def format_station_table(stations: List[Dict]) -> pd.DataFrame:
    """Format stations data for display in a table"""
    if not stations:
        return pd.DataFrame()
    
    table_data = []
    for i, station in enumerate(stations):
        table_data.append({
            "#": i + 1,
            "Station Name": station.get('place', 'N/A'),
            "WMO Code": station.get('wmo', 'N/A'),
            "Latitude": station.get('lat', 'N/A'),
            "Longitude": station.get('long', 'N/A'),
            "Elevation (m)": station.get('elev', 'N/A'),
            "Distance (miles)": station.get('distance_miles', 'N/A')
        })
    
    return pd.DataFrame(table_data)

def categorize_station_data(data: Dict) -> Dict:
    """Categorize station data into logical groups"""
    if not data:
        return {}
    
    categories = {
        "Station Information": {
            "place": data.get('place'),
            "wmo": data.get('wmo'),
            "lat": data.get('lat'),
            "long": data.get('long'),
            "elev": data.get('elev'),
            "country": data.get('country'),
            "state": data.get('state'),
            "period": data.get('period'),
            "time_zone": data.get('time_zone'),
            "coldest_month": data.get('coldest_month'),
            "hottest_month": data.get('hottest_month'),
        },
        "Heating Design Conditions": {
            "heating_DB_99.6": data.get('heating_DB_99.6'),
            "heating_DB_99": data.get('heating_DB_99'),
            "humidification_DP/MCDB_and_HR_99.6_DP": data.get('humidification_DP/MCDB_and_HR_99.6_DP'),
            "humidification_DP/MCDB_and_HR_99.6_HR": data.get('humidification_DP/MCDB_and_HR_99.6_HR'),
            "humidification_DP/MCDB_and_HR_99.6_MCDB": data.get('humidification_DP/MCDB_and_HR_99.6_MCDB'),
        },
        "Cooling Design Conditions": {
            "cooling_DB_MCWB_0.4_DB": data.get('cooling_DB_MCWB_0.4_DB'),
            "cooling_DB_MCWB_0.4_MCWB": data.get('cooling_DB_MCWB_0.4_MCWB'),
            "cooling_DB_MCWB_1_DB": data.get('cooling_DB_MCWB_1_DB'),
            "cooling_DB_MCWB_1_MCWB": data.get('cooling_DB_MCWB_1_MCWB'),
            "cooling_DB_MCWB_2_DB": data.get('cooling_DB_MCWB_2_DB'),
            "cooling_DB_MCWB_2_MCWB": data.get('cooling_DB_MCWB_2_MCWB'),
        },
        "Extreme Temperatures": {
            "extreme_max_WB": data.get('extreme_max_WB'),
            "extreme_annual_DB_mean_min": data.get('extreme_annual_DB_mean_min'),
            "extreme_annual_DB_mean_max": data.get('extreme_annual_DB_mean_max'),
            "n-year_return_period_values_of_extreme_DB_5_min": data.get('n-year_return_period_values_of_extreme_DB_5_min'),
            "n-year_return_period_values_of_extreme_DB_5_max": data.get('n-year_return_period_values_of_extreme_DB_5_max'),
            "n-year_return_period_values_of_extreme_DB_10_min": data.get('n-year_return_period_values_of_extreme_DB_10_min'),
            "n-year_return_period_values_of_extreme_DB_10_max": data.get('n-year_return_period_values_of_extreme_DB_10_max'),
            "n-year_return_period_values_of_extreme_DB_20_min": data.get('n-year_return_period_values_of_extreme_DB_20_min'),
            "n-year_return_period_values_of_extreme_DB_20_max": data.get('n-year_return_period_values_of_extreme_DB_20_max'),
            "n-year_return_period_values_of_extreme_DB_50_min": data.get('n-year_return_period_values_of_extreme_DB_50_min'),
            "n-year_return_period_values_of_extreme_DB_50_max": data.get('n-year_return_period_values_of_extreme_DB_50_max'),
        },
        "Monthly Average Temperatures (°C)": {
            "tavg_jan": data.get('tavg_jan'),
            "tavg_feb": data.get('tavg_feb'),
            "tavg_mar": data.get('tavg_mar'),
            "tavg_apr": data.get('tavg_apr'),
            "tavg_may": data.get('tavg_may'),
            "tavg_jun": data.get('tavg_jun'),
            "tavg_jul": data.get('tavg_jul'),
            "tavg_aug": data.get('tavg_aug'),
            "tavg_sep": data.get('tavg_sep'),
            "tavg_oct": data.get('tavg_oct'),
            "tavg_nov": data.get('tavg_nov'),
            "tavg_dec": data.get('tavg_dec'),
        },
        "Degree Days": {
            "hdd10.0_annual": data.get('hdd10.0_annual'),
            "hdd18.3_annual": data.get('hdd18.3_annual'),
            "cdd10.0_annual": data.get('cdd10.0_annual'),
            "cdd18.3_annual": data.get('cdd18.3_annual'),
            "cdh_23.3_annual": data.get('cdh_23.3_annual'),
            "cdh_26.7_annual": data.get('cdh_26.7_annual'),
        },
        "Wind Conditions": {
            "coldest_month_WS/MSDB_0.4_WS": data.get('coldest_month_WS/MSDB_0.4_WS'),
            "coldest_month_WS/MSDB_0.4_MCDB": data.get('coldest_month_WS/MSDB_0.4_MCDB'),
            "coldest_month_WS/MSDB_1_WS": data.get('coldest_month_WS/MSDB_1_WS'),
            "coldest_month_WS/MSDB_1_MCDB": data.get('coldest_month_WS/MSDB_1_MCDB'),
            "extreme_annual_WS_1": data.get('extreme_annual_WS_1'),
            "extreme_annual_WS_2.5": data.get('extreme_annual_WS_2.5'),
            "extreme_annual_WS_5": data.get('extreme_annual_WS_5'),
        }
    }
    
    return categories

def display_station_data_in_pdf_format(data: Dict):
    """Display station data in a format similar to the PDF"""
    if not data:
        st.warning("No station data available")
        return
    
    # Display basic station info in a card
    with st.container():
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Station Name", data.get('place', 'N/A'))
        with col2:
            st.metric("WMO Code", data.get('wmo', 'N/A'))
        with col3:
            st.metric("Elevation", f"{data.get('elev', 'N/A')} m")
        with col4:
            st.metric("Period", data.get('period', 'N/A'))
    
    st.divider()
    
    # Create tabs for different data categories
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📋 Station Info",
        "🔥 Heating Design",
        "❄️ Cooling Design",
        "🌡️ Extreme Temps",
        "📅 Monthly Averages",
        "📊 Degree Days",
        "💨 Wind & Solar"
    ])
    
    # Tab 1: Station Information
    with tab1:
        st.subheader("Station Information")
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Location:** {data.get('lat', 'N/A')}°N, {data.get('long', 'N/A')}°E")
            st.write(f"**Country:** {data.get('country', 'N/A')}")
            st.write(f"**State/Region:** {data.get('state', 'N/A')}")
            st.write(f"**Time Zone:** UTC{data.get('time_zone', 'N/A')}")
        
        with col2:
            st.write(f"**Coldest Month:** {data.get('coldest_month', 'N/A')}")
            st.write(f"**Hottest Month:** {data.get('hottest_month', 'N/A')}")
            st.write(f"**Standard Pressure:** {data.get('stdp', 'N/A')} kPa")
            st.write(f"**WBAN:** {data.get('wban', 'N/A')}")
    
    # Tab 2: Heating Design Conditions
    with tab2:
        st.subheader("Heating Design Conditions")
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Heating DB 99.6%", f"{data.get('heating_DB_99.6', 'N/A')}°C")
            st.metric("Heating DB 99%", f"{data.get('heating_DB_99', 'N/A')}°C")
        
        with col2:
            st.write(f"**Humidification DP/MCDB & HR 99.6% DP:** {data.get('humidification_DP/MCDB_and_HR_99.6_DP', 'N/A')}°C")
            st.write(f"**Humidification DP/MCDB & HR 99.6% HR:** {data.get('humidification_DP/MCDB_and_HR_99.6_HR', 'N/A')} g/kg")
            st.write(f"**Humidification DP/MCDB & HR 99.6% MCDB:** {data.get('humidification_DP/MCDB_and_HR_99.6_MCDB', 'N/A')}°C")
    
    # Tab 3: Cooling Design Conditions
    with tab3:
        st.subheader("Cooling Design Conditions")
        
        # Create a table for cooling conditions
        cooling_data = {
            "Design Condition": ["0.4%", "1%", "2%"],
            "Dry Bulb (°C)": [
                data.get('cooling_DB_MCWB_0.4_DB', 'N/A'),
                data.get('cooling_DB_MCWB_1_DB', 'N/A'),
                data.get('cooling_DB_MCWB_2_DB', 'N/A')
            ],
            "Mean Coincident Wet Bulb (°C)": [
                data.get('cooling_DB_MCWB_0.4_MCWB', 'N/A'),
                data.get('cooling_DB_MCWB_1_MCWB', 'N/A'),
                data.get('cooling_DB_MCWB_2_MCWB', 'N/A')
            ]
        }
        
        st.table(pd.DataFrame(cooling_data))
        
        st.write(f"**Hottest Month DB Range:** {data.get('hottest_month_DB_range', 'N/A')}°C")
    
    # Tab 4: Extreme Temperatures
    with tab4:
        st.subheader("Extreme Temperatures")
        
        # Extreme temperatures table
        extreme_data = {
            "Return Period": ["5-year", "10-year", "20-year", "50-year"],
            "Minimum (°C)": [
                data.get('n-year_return_period_values_of_extreme_DB_5_min', 'N/A'),
                data.get('n-year_return_period_values_of_extreme_DB_10_min', 'N/A'),
                data.get('n-year_return_period_values_of_extreme_DB_20_min', 'N/A'),
                data.get('n-year_return_period_values_of_extreme_DB_50_min', 'N/A')
            ],
            "Maximum (°C)": [
                data.get('n-year_return_period_values_of_extreme_DB_5_max', 'N/A'),
                data.get('n-year_return_period_values_of_extreme_DB_10_max', 'N/A'),
                data.get('n-year_return_period_values_of_extreme_DB_20_max', 'N/A'),
                data.get('n-year_return_period_values_of_extreme_DB_50_max', 'N/A')
            ]
        }
        
        st.table(pd.DataFrame(extreme_data))
        
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Extreme Max WB:** {data.get('extreme_max_WB', 'N/A')}°C")
            st.write(f"**Mean Annual Min DB:** {data.get('extreme_annual_DB_mean_min', 'N/A')}°C")
        with col2:
            st.write(f"**Mean Annual Max DB:** {data.get('extreme_annual_DB_mean_max', 'N/A')}°C")
            st.write(f"**Std Dev Min DB:** {data.get('extreme_annual_DB_standard_deviation_min', 'N/A')}°C")
            st.write(f"**Std Dev Max DB:** {data.get('extreme_annual_DB_standard_deviation_max', 'N/A')}°C")
    
    # Tab 5: Monthly Averages
    with tab5:
        st.subheader("Monthly Average Temperatures (°C)")
        
        # Create monthly averages table
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                 "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        
        monthly_data = {
            "Month": months,
            "Avg Temp (°C)": [
                data.get('tavg_jan', 'N/A'),
                data.get('tavg_feb', 'N/A'),
                data.get('tavg_mar', 'N/A'),
                data.get('tavg_apr', 'N/A'),
                data.get('tavg_may', 'N/A'),
                data.get('tavg_jun', 'N/A'),
                data.get('tavg_jul', 'N/A'),
                data.get('tavg_aug', 'N/A'),
                data.get('tavg_sep', 'N/A'),
                data.get('tavg_oct', 'N/A'),
                data.get('tavg_nov', 'N/A'),
                data.get('tavg_dec', 'N/A')
            ],
            "Std Dev (°C)": [
                data.get('sd_jan', 'N/A'),
                data.get('sd_feb', 'N/A'),
                data.get('sd_mar', 'N/A'),
                data.get('sd_apr', 'N/A'),
                data.get('sd_may', 'N/A'),
                data.get('sd_jun', 'N/A'),
                data.get('sd_jul', 'N/A'),
                data.get('sd_aug', 'N/A'),
                data.get('sd_sep', 'N/A'),
                data.get('sd_oct', 'N/A'),
                data.get('sd_nov', 'N/A'),
                data.get('sd_dec', 'N/A')
            ]
        }
        
        st.table(pd.DataFrame(monthly_data))
        st.metric("Annual Average Temperature", f"{data.get('tavg_annual', 'N/A')}°C")
    
    # Tab 6: Degree Days
    with tab6:
        st.subheader("Degree Days")
        
        # Degree days metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("HDD 10.0°C", f"{data.get('hdd10.0_annual', 'N/A')} °C-days")
        with col2:
            st.metric("HDD 18.3°C", f"{data.get('hdd18.3_annual', 'N/A')} °C-days")
        with col3:
            st.metric("CDD 10.0°C", f"{data.get('cdd10.0_annual', 'N/A')} °C-days")
        with col4:
            st.metric("CDD 18.3°C", f"{data.get('cdd18.3_annual', 'N/A')} °C-days")
        
        st.write(f"**CDH 23.3°C:** {data.get('cdh_23.3_annual', 'N/A')} °C-hours")
        st.write(f"**CDH 26.7°C:** {data.get('cdh_26.7_annual', 'N/A')} °C-hours")
        st.write(f"**Hours 8-4 & 12.8/20.6°C:** {data.get('hours_8_to_4_and_12.8/20.6', 'N/A')} hours")
    
    # Tab 7: Wind and Solar
    with tab7:
        st.subheader("Wind and Solar Conditions")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Wind Conditions:**")
            st.write(f"Coldest Month WS/MSDB 0.4% WS: {data.get('coldest_month_WS/MSDB_0.4_WS', 'N/A')} m/s")
            st.write(f"Coldest Month WS/MSDB 0.4% MCDB: {data.get('coldest_month_WS/MSDB_0.4_MCDB', 'N/A')}°C")
            st.write(f"Coldest Month WS/MSDB 1% WS: {data.get('coldest_month_WS/MSDB_1_WS', 'N/A')} m/s")
            st.write(f"Coldest Month WS/MSDB 1% MCDB: {data.get('coldest_month_WS/MSDB_1_MCDB', 'N/A')}°C")
            
            st.write(f"\n**Extreme Wind Speeds:**")
            st.write(f"1-year return: {data.get('extreme_annual_WS_1', 'N/A')} m/s")
            st.write(f"2.5-year return: {data.get('extreme_annual_WS_2.5', 'N/A')} m/s")
            st.write(f"5-year return: {data.get('extreme_annual_WS_5', 'N/A')} m/s")
        
        with col2:
            st.write("**Solar Conditions:**")
            st.write(f"Clear sky optical depth (beam) - Jan: {data.get('taub_jan', 'N/A')}")
            st.write(f"Clear sky optical depth (beam) - Jul: {data.get('taub_jul', 'N/A')}")
            st.write(f"Clear sky optical depth (diffuse) - Jan: {data.get('taud_jan', 'N/A')}")
            st.write(f"Clear sky optical depth (diffuse) - Jul: {data.get('taud_jul', 'N/A')}")
            
            st.write(f"\n**Solar Irradiance at Noon:**")
            st.write(f"Beam normal - Jan: {data.get('ebn_noon_jan', 'N/A')} W/m²")
            st.write(f"Diffuse horizontal - Jan: {data.get('edn_noon_jan', 'N/A')} W/m²")

# Main App
def main():
    # Header
    st.markdown('<h1 class="main-header">🌤️ ASHRAE Meteo Station Finder</h1>', unsafe_allow_html=True)
    st.markdown("Find weather stations and access ASHRAE meteorological data for any location.")
    
    # Initialize session state
    if 'stations' not in st.session_state:
        st.session_state.stations = []
    if 'selected_station_data' not in st.session_state:
        st.session_state.selected_station_data = None
    
    # Sidebar for inputs
    with st.sidebar:
        st.header("📍 Location Input")
        
        # Input coordinates
        col1, col2 = st.columns(2)
        with col1:
            latitude = st.number_input(
                "Latitude",
                min_value=-90.0,
                max_value=90.0,
                value=44.84,
                format="%.4f",
                help="Enter latitude (-90 to 90)"
            )
        with col2:
            longitude = st.number_input(
                "Longitude",
                min_value=-180.0,
                max_value=180.0,
                value=-91.74,
                format="%.4f",
                help="Enter longitude (-180 to 180)"
            )
        
        # Number of stations
        num_stations = st.slider(
            "Number of Stations to Show",
            min_value=1,
            max_value=20,
            value=10,
            help="Number of nearest stations to display"
        )
        
        # ASHRAE version
        ashrae_version = st.selectbox(
            "ASHRAE Version",
            options=[2017, 2013, 2009],
            index=0,
            help="Select ASHRAE version for data"
        )
        
        # Unit system
        unit_system = st.radio(
            "Unit System",
            options=["SI", "IP"],
            index=0,
            help="SI for metric, IP for imperial units"
        )
        
        # Find stations button
        if st.button("🔍 Find Nearest Stations", type="primary", use_container_width=True):
            with st.spinner("Searching for stations..."):
                stations = get_nearest_stations(latitude, longitude, num_stations)
                if stations:
                    st.session_state.stations = stations
                    st.success(f"Found {len(stations)} stations!")
                else:
                    st.error("No stations found. Please try different coordinates.")
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown('<h2 class="sub-header">📍 Your Location</h2>', unsafe_allow_html=True)
        st.write(f"**Coordinates:** {latitude}, {longitude}")
        
        if st.session_state.stations:
            # Display station table
            st.markdown('<h2 class="sub-header">📊 Nearest Weather Stations</h2>', unsafe_allow_html=True)
            
            # Format and display table
            stations_df = format_station_table(st.session_state.stations)
            
            # Apply some styling to the dataframe
            styled_df = stations_df.style.format({
                'Distance (miles)': '{:.2f}',
                'Elevation (m)': '{:.0f}'
            }).set_properties(**{
                'background-color': '#f8f9fa',
                'border': '1px solid #dee2e6'
            })
            
            st.dataframe(
                styled_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "#": st.column_config.NumberColumn(width="small"),
                    "Station Name": st.column_config.TextColumn(width="large"),
                    "WMO Code": st.column_config.TextColumn(width="small"),
                    "Latitude": st.column_config.NumberColumn(format="%.4f"),
                    "Longitude": st.column_config.NumberColumn(format="%.4f"),
                    "Elevation (m)": st.column_config.NumberColumn(format="%d"),
                    "Distance (miles)": st.column_config.NumberColumn(format="%.2f")
                }
            )
    
    with col2:
        st.markdown('<h2 class="sub-header">⚙️ Station Selection</h2>', unsafe_allow_html=True)
        
        if st.session_state.stations:
            # Create dropdown with station names
            station_options = [f"{s.get('place', 'Unknown')} (WMO: {s.get('wmo', 'N/A')})" 
                             for s in st.session_state.stations]
            
            selected_station = st.selectbox(
                "Select a station for detailed data:",
                options=station_options,
                index=0,
                help="Choose a station to view detailed meteorological data"
            )
            
            # Extract WMO code from selection
            selected_index = station_options.index(selected_station)
            selected_station_info = st.session_state.stations[selected_index]
            wmo_code = selected_station_info.get('wmo')
            
            # Show selected station info
            with st.container():
                st.markdown("### Selected Station")
                st.write(f"**Name:** {selected_station_info.get('place', 'N/A')}")
                st.write(f"**WMO:** {wmo_code}")
                st.write(f"**Distance:** {selected_station_info.get('distance_miles', 'N/A')} miles")
                st.write(f"**Elevation:** {selected_station_info.get('elev', 'N/A')} m")
            
            # Button to load station data
            if st.button("📥 Load Station Data", type="secondary", use_container_width=True):
                with st.spinner("Loading station data..."):
                    station_data = get_station_data(wmo_code, ashrae_version, unit_system)
                    if station_data:
                        st.session_state.selected_station_data = station_data
                        st.success("Station data loaded successfully!")
                    else:
                        st.error("Failed to load station data. Please try again.")
    
    # Display station data if available
    if st.session_state.selected_station_data:
        st.markdown("---")
        st.markdown('<h2 class="sub-header">📋 Station Meteorological Data</h2>', unsafe_allow_html=True)
        
        # Display the data in PDF-like format
        display_station_data_in_pdf_format(st.session_state.selected_station_data)
        
        # Add download buttons
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            # Download as JSON
            json_data = json.dumps(st.session_state.selected_station_data, indent=2)
            st.download_button(
                label="📥 Download as JSON",
                data=json_data,
                file_name=f"ashrae_data_{wmo_code}.json",
                mime="application/json",
                use_container_width=True
            )
        
        with col2:
            # Download as CSV (key parameters only)
            import csv
            import io
            
            # Create CSV from categorized data
            categorized = categorize_station_data(st.session_state.selected_station_data)
            csv_data = io.StringIO()
            writer = csv.writer(csv_data)
            
            # Write header
            writer.writerow(["Category", "Parameter", "Value", "Units"])
            
            # Write data
            for category, params in categorized.items():
                for param, value in params.items():
                    if value and value != 'n/a':
                        # Determine units based on parameter name
                        units = ""
                        if any(x in param.lower() for x in ['db', 'wb', 'mcdb', 'mcwb', 'temp', 'tavg']):
                            units = "°C"
                        elif 'hdd' in param.lower() or 'cdd' in param.lower():
                            units = "°C-days"
                        elif 'cdh' in param.lower():
                            units = "°C-hours"
                        elif 'ws' in param.lower() or 'speed' in param.lower():
                            units = "m/s"
                        elif 'hr' in param.lower():
                            units = "g/kg"
                        elif 'elev' in param.lower():
                            units = "m"
                        elif 'pressure' in param.lower() or 'stdp' in param.lower():
                            units = "kPa"
                        
                        writer.writerow([category, param, value, units])
            
            st.download_button(
                label="📊 Download as CSV",
                data=csv_data.getvalue(),
                file_name=f"ashrae_summary_{wmo_code}.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #6B7280;'>
        <p>ASHRAE Meteo Data v3.0 | Data provided by ashrae-meteo.info</p>
        <p>This tool retrieves ASHRAE meteorological design conditions for HVAC system design</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
