import streamlit as st
import pandas as pd
import requests
import json
from typing import List, Dict, Optional

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
    .logo-container {
        text-align: center;
        margin-bottom: 1rem;
    }
    .logo-img {
        max-height: 80px;
    }
</style>
""", unsafe_allow_html=True)

# API Functions
def get_url_generator(lat: float, long: float, num_stations: int = 10, version: int = 2021) -> str:
    """Generate URL for ASHRAE stations API"""
    url = 'https://ashrae-meteo.info/v3.0/request_places_get.php?'
    url1 = url + 'lat=' + str(lat) + '&long=' + str(long) + '&number=' + str(num_stations) + '&ashrae_version=' + str(version)
    return url1

def get_nearest_stations(lat: float, long: float, num_stations: int = 10) -> List[Dict]:
    """
    Get nearest weather stations to given coordinates
    """
    url = get_url_generator(lat, long, num_stations, version=2021)
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Handle UTF-8 BOM (Byte Order Mark) if present
        content = response.content
        
        # Check for UTF-8 BOM and decode accordingly
        if content.startswith(b'\xef\xbb\xbf'):
            # UTF-8 with BOM
            text = content.decode('utf-8-sig')
        else:
            # Regular UTF-8
            text = content.decode('utf-8')
        
        # Parse JSON
        data = json.loads(text)
        stations = data.get('meteo_stations', [])
        
        if not stations:
            return []
        
        # Add calculated distance in miles (approximate)
        # Convert radians to miles: 1 radian ≈ 3958.8 miles
        for station in stations:
            radians = float(station.get('tt', 0))
            station['distance_miles'] = round(radians * 3958.8, 2)
            
            # Convert elevation from meters to feet (1 meter = 3.28084 feet)
            elev_m = station.get('elev')
            station['elevation_ft'] = 'N/A'  # Default value
            
            if elev_m and elev_m != 'N/A' and elev_m != '':
                try:
                    # Clean the string - remove any non-numeric characters except decimal point
                    clean_elev = ''.join(c for c in str(elev_m) if c.isdigit() or c == '.')
                    if clean_elev:  # Check if we got any numbers
                        elev_float = float(clean_elev)
                        elev_ft = round(elev_float * 3.28084, 0)
                        station['elevation_ft'] = int(elev_ft)
                except (ValueError, TypeError):
                    station['elevation_ft'] = 'N/A'
        
        return stations
        
    except Exception as e:
        st.error(f"Error fetching stations: {e}")
        return []

def get_station_data(wmo: str, ashrae_version: int = 2021, si_ip: str = "SI") -> Optional[Dict]:
    """
    Get detailed meteorological data for a specific station by WMO code
    """
    url = f"https://ashrae-meteo.info/v3.0/request_meteo_parametres_get.php?wmo={wmo}&ashrae_version={ashrae_version}&si_ip={si_ip}"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Handle UTF-8 BOM (Byte Order Mark) if present
        content = response.content
        
        # Check for UTF-8 BOM and decode accordingly
        if content.startswith(b'\xef\xbb\xbf'):
            # UTF-8 with BOM
            text = content.decode('utf-8-sig')
        else:
            # Regular UTF-8
            text = content.decode('utf-8')
        
        # Parse JSON
        data = json.loads(text)
        stations = data.get('meteo_stations', [])
        
        if not stations:
            st.warning(f"No data found for station WMO: {wmo}")
            return None
        
        station_data = stations[0]
        return station_data
        
    except requests.exceptions.RequestException as e:
        st.error(f"Network error fetching station data: {e}")
        return None
    except json.JSONDecodeError as e:
        st.error(f"Failed to parse JSON response: {e}")
        # Print first 500 chars of response for debugging
        try:
            st.text(f"Response preview: {response.text[:500] if 'response' in locals() else 'No response'}")
        except:
            pass
        return None
    except Exception as e:
        st.error(f"Unexpected error: {e}")
        return None

def format_station_table(stations: List[Dict]) -> pd.DataFrame:
    """Format stations data for display in a table"""
    if not stations:
        return pd.DataFrame()
    
    table_data = []
    for i, station in enumerate(stations):
        # Get elevation value - handle both numeric and string 'N/A'
        elev_ft = station.get('elevation_ft', 'N/A')
        if elev_ft != 'N/A' and elev_ft is not None:
            try:
                # Convert to integer if it's a number
                elev_display = int(float(elev_ft))
            except:
                elev_display = 'N/A'
        else:
            elev_display = 'N/A'
        
        # Get distance value
        distance = station.get('distance_miles', 'N/A')
        if distance != 'N/A' and distance is not None:
            try:
                distance_display = float(distance)
            except:
                distance_display = 'N/A'
        else:
            distance_display = 'N/A'
        
        table_data.append({
            "#": i + 1,
            "Station Name": station.get('place', 'N/A'),
            "WMO Code": station.get('wmo', 'N/A'),
            "Latitude": station.get('lat', 'N/A'),
            "Longitude": station.get('long', 'N/A'),
            "Elevation (ft)": elev_display,
            "Distance (miles)": distance_display
        })
    
    return pd.DataFrame(table_data)

def extract_highest_monthly_temps(data: Dict) -> Dict:
    """
    Extract the highest monthly temperatures from three data sets:
    1. Monthly average temperatures (dbavg_jan through dbavg_dec)
    2. Monthly 0.4% design temperatures (0.4_DB_jan through 0.4_DB_dec)
    3. Monthly 2% design temperatures (2_DB_jan through 2_DB_dec)
    
    Returns:
        Dictionary with:
        - highest_avg_temp: Highest monthly average temperature
        - highest_04_temp: Highest 0.4% design temperature  
        - highest_2_temp: Highest 2% design temperature
        - avg_hottest_month: Month with highest average temp
        - 04_hottest_month: Month with highest 0.4% design temp
        - 2_hottest_month: Month with highest 2% design temp
    """
    if not data:
        return {}
    
    # Month names in order
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    
    # 1. Extract monthly average temperatures (dbavg_ fields)
    avg_temp_fields = ['dbavg_jan', 'dbavg_feb', 'dbavg_mar', 'dbavg_apr', 'dbavg_may', 'dbavg_jun',
                      'dbavg_jul', 'dbavg_aug', 'dbavg_sep', 'dbavg_oct', 'dbavg_nov', 'dbavg_dec']
    
    avg_temps = []
    for month, field in zip(months, avg_temp_fields):
        temp = data.get(field)
        if temp and temp != 'N/A':
            try:
                avg_temps.append((month, float(temp)))
            except (ValueError, TypeError):
                avg_temps.append((month, None))
        else:
            avg_temps.append((month, None))
    
    # 2. Extract 0.4% design temperatures
    db_04_fields = ['0.4_DB_jan', '0.4_DB_feb', '0.4_DB_mar', '0.4_DB_apr', '0.4_DB_may', '0.4_DB_jun',
                   '0.4_DB_jul', '0.4_DB_aug', '0.4_DB_sep', '0.4_DB_oct', '0.4_DB_nov', '0.4_DB_dec']
    
    db_04_temps = []
    for month, field in zip(months, db_04_fields):
        temp = data.get(field)
        if temp and temp != 'N/A':
            try:
                db_04_temps.append((month, float(temp)))
            except (ValueError, TypeError):
                db_04_temps.append((month, None))
        else:
            db_04_temps.append((month, None))
    
    # 3. Extract 2% design temperatures
    db_2_fields = ['2_DB_jan', '2_DB_feb', '2_DB_mar', '2_DB_apr', '2_DB_may', '2_DB_jun',
                  '2_DB_jul', '2_DB_aug', '2_DB_sep', '2_DB_oct', '2_DB_nov', '2_DB_dec']
    
    db_2_temps = []
    for month, field in zip(months, db_2_fields):
        temp = data.get(field)
        if temp and temp != 'N/A':
            try:
                db_2_temps.append((month, float(temp)))
            except (ValueError, TypeError):
                db_2_temps.append((month, None))
        else:
            db_2_temps.append((month, None))
    
    # Find highest values for each set
    def find_highest(temps_list):
        """Helper function to find highest temperature and month"""
        valid_temps = [(month, temp) for month, temp in temps_list if temp is not None]
        if not valid_temps:
            return None, None
        
        # Find max temperature
        highest_month, highest_temp = max(valid_temps, key=lambda x: x[1])
        return highest_temp, highest_month
    
    highest_avg_temp, avg_hottest_month = find_highest(avg_temps)
    highest_04_temp, hottest_month_04 = find_highest(db_04_temps)
    highest_2_temp, hottest_month_2 = find_highest(db_2_temps)
    
    return {
        'highest_avg_temp': highest_avg_temp,
        'highest_04_temp': highest_04_temp,
        'highest_2_temp': highest_2_temp,
        'avg_hottest_month': avg_hottest_month,
        '04_hottest_month': hottest_month_04,
        '2_hottest_month': hottest_month_2
    }

def display_station_data_in_pdf_format(data: Dict):
    """Display station data in organized tables"""
    if not data:
        st.warning("No station data available")
        return
    
    # Display basic station info
    st.markdown("### 📍 Station Information")
    with st.container():
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Station Name", data.get('place', 'N/A'))
        with col2:
            st.metric("WMO Code", data.get('wmo', 'N/A'))
        
        # Convert elevation to feet if available
        elev_m = data.get('elev', 'N/A')
        elev_ft = 'N/A'
        if elev_m != 'N/A' and elev_m:
            try:
                elev_ft = int(float(elev_m) * 3.28084)
            except:
                elev_ft = 'N/A'
        
        with col3:
            st.metric("Elevation", f"{elev_ft} ft ({elev_m} m)")
        with col4:
            st.metric("Data Period", data.get('period', 'N/A'))

    # Table 1: Overview table
    st.markdown("---")
    st.markdown("### Design Information")
    
    highest_monthly_temps = extract_highest_monthly_temps(data)
    
    overview_data = {
        "Parameter": ['Extreme Annual Max', 'Extreme Annual Min', 'N = 20 Max',
                      'N = 20 Min', 'N = 50 Max', 'N = 50 Min', 'Yearly 0.4% High',
                      'Yearly 2.0% High', 'Highest Monthly 0.4%', 'Highest Monthly 2.0%', 
                      'Annual Average', 'Highest Monthly Average'   
        ],
        "Value": [
            data.get('extreme_annual_DB_mean_max', 'N/A'),
            data.get('extreme_annual_DB_mean_min', 'N/A'),
            data.get('n-year_return_period_values_of_extreme_DB_20_max', 'N/A'),
            data.get('n-year_return_period_values_of_extreme_DB_20_min', 'N/A'),
            data.get('n-year_return_period_values_of_extreme_DB_50_max', 'N/A'),
            data.get('n-year_return_period_values_of_extreme_DB_50_min', 'N/A'),
            data.get('cooling_DB_MCWB_0.4_DB', 'N/A'),
            data.get('cooling_DB_MCWB_2_DB', 'N/A'),
            highest_monthly_temps.get('highest_04_temp', 'N/A'),
            highest_monthly_temps.get('highest_2_temp', 'N/A'),
            data.get('dbavg_annual'),
            highest_monthly_temps.get('highest_avg_temp', 'N/A')
        ]
    }
    # Create DataFrame
    overview_df = pd.DataFrame(overview_data)
    
    # Format numeric values
    def format_temp(val):
        if val == 'N/A' or val is None:
            return 'N/A'
        try:
            return f"{float(val):.1f} °C"
        except:
            return str(val)
    
    overview_df['Value'] = overview_df['Value'].apply(format_temp)
    
    # Display the table
    st.dataframe(
        overview_df,
        hide_index=True,
        use_container_width=True
    )
    
def export_overview_data_to_csv(data: Dict) -> str:
    """Export only the overview data to CSV format with UTF-8 BOM"""
    if not data:
        return ""
    
    import csv
    import io
    
    # Get highest monthly temperatures
    highest_monthly_temps = extract_highest_monthly_temps(data)
    
    csv_data = io.StringIO()
    
    # Add UTF-8 BOM at the beginning
    csv_data.write('\ufeff')
    
    # Use csv.writer
    writer = csv.writer(csv_data)
    
    # Write header with degree symbol
    writer.writerow(["Parameter", "Value", "Units"])
    
    # Define overview data with degree symbol
    overview_params = [
        ("Extreme Annual Max", data.get('extreme_annual_DB_mean_max', 'N/A'), "°C"),
        ("Extreme Annual Min", data.get('extreme_annual_DB_mean_min', 'N/A'), "°C"),
        ("N = 20 Max", data.get('n-year_return_period_values_of_extreme_DB_20_max', 'N/A'), "°C"),
        ("N = 20 Min", data.get('n-year_return_period_values_of_extreme_DB_20_min', 'N/A'), "°C"),
        ("N = 50 Max", data.get('n-year_return_period_values_of_extreme_DB_50_max', 'N/A'), "°C"),
        ("N = 50 Min", data.get('n-year_return_period_values_of_extreme_DB_50_min', 'N/A'), "°C"),
        ("Yearly 0.4% High", data.get('cooling_DB_MCWB_0.4_DB', 'N/A'), "°C"),
        ("Yearly 2.0% High", data.get('cooling_DB_MCWB_2_DB', 'N/A'), "°C"),
        ("Highest Monthly 0.4%", highest_monthly_temps.get('highest_04_temp', 'N/A'), "°C"),
        ("Highest Monthly 2.0%", highest_monthly_temps.get('highest_2_temp', 'N/A'), "°C"),
        ("Annual Average", data.get('dbavg_annual', data.get('tavg_annual', 'N/A')), "°C"),
        ("Highest Monthly Average", highest_monthly_temps.get('highest_avg_temp', 'N/A'), "°C")
    ]
    
    # Write all parameters
    for param, value, unit in overview_params:
        # Format the value nicely
        if value != 'N/A' and value is not None:
            try:
                # Try to format as float with 1 decimal place
                formatted_value = f"{float(value):.1f}"
            except (ValueError, TypeError):
                formatted_value = str(value)
        else:
            formatted_value = str(value)
        
        writer.writerow([param, formatted_value, unit])
    
    return csv_data.getvalue()

# Main App
def main():
    # RRC logo
    st.markdown("""
    <div class="logo-container">
        <img src="https://cdn.theorg.com/0f8b4de9-d8c5-4a5a-bfb7-dfe6a539b1f7_medium.jpg" class="logo-img">
    </div>
    """, unsafe_allow_html=True)

     # Created by section
    st.markdown("""
    <div style="text-align: center; margin-bottom: 1rem; color: #666; font-style: italic;">
        Created by Cassidy Exum - BESS Engineer
    </div>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown('<h1 class="main-header">🌤️ ASHRAE Meteo Station Finder</h1>', unsafe_allow_html=True)
    st.markdown("""
    Find weather stations and access ASHRAE 2021 meteorological data for any location.
    
    [Visit the ASHRAE site](https://ashrae-meteo.info/v3.0/)
    """)
    
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
                value=00.00,
                format="%.4f",
                help="Enter latitude (-90 to 90)"
            )
        with col2:
            longitude = st.number_input(
                "Longitude",
                min_value=-180.0,
                max_value=180.0,
                value=00.00,
                format="%.4f",
                help="Enter longitude (-180 to 180)"
            )
        
        # Display fixed settings
        st.markdown("### Settings")
        st.info(f"**Number of Stations:** 10")
        st.info(f"**ASHRAE Version:** 2021")
        
        # Unit system
        unit_system = st.radio(
            "Unit System",
            options=["SI", "IP"],
            index=0,
            help="SI for metric, IP for imperial units"
        )
        
        # Find stations button
        if st.button("🔍 Find Nearest Stations", type="primary", width='stretch'):
            with st.spinner("Searching for stations..."):
                stations = get_nearest_stations(latitude, longitude, num_stations=10)
                if stations:
                    st.session_state.stations = stations
                    st.success(f"Found {len(stations)} stations!")
                else:
                    st.error("No stations found. Please try different coordinates.")
    
    # Main content area - Single column layout
    st.markdown('<h2 class="sub-header">📍 Your Location</h2>', unsafe_allow_html=True)
    st.write(f"**Coordinates:** {latitude}, {longitude}")
    
    if st.session_state.stations:
        # Display station table
        st.markdown('<h2 class="sub-header">📊 Nearest Weather Stations (Top 10)</h2>', unsafe_allow_html=True)
        
        # Format and display table
        stations_df = format_station_table(st.session_state.stations)
        
        st.dataframe(
            stations_df,
            width='stretch',
            hide_index=True,
            column_config={
                "#": st.column_config.NumberColumn(width="small"),
                "Station Name": st.column_config.TextColumn(width="large"),
                "WMO Code": st.column_config.TextColumn(width="small"),
                "Latitude": st.column_config.TextColumn(width="medium"),
                "Longitude": st.column_config.TextColumn(width="medium"),
                "Elevation (ft)": st.column_config.TextColumn(width="medium"),
                "Distance (miles)": st.column_config.TextColumn(width="medium")
            }
        )
        
        # Station selection section (moved under the table)
        st.markdown('<h2 class="sub-header">⚙️ Station Selection</h2>', unsafe_allow_html=True)
        
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
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("### Selected Station Info")
                st.write(f"**Name:** {selected_station_info.get('place', 'N/A')}")
                st.write(f"**WMO Code:** {wmo_code}")
            with col2:
                st.write(f"**Distance:** {selected_station_info.get('distance_miles', 'N/A')} miles")
                
                # Show elevation in both feet and meters
                elev_ft = selected_station_info.get('elevation_ft', 'N/A')
                elev_m = selected_station_info.get('elev', 'N/A')
                if elev_ft != 'N/A' and elev_m != 'N/A':
                    st.write(f"**Elevation:** {elev_ft} ft ({elev_m} m)")
                elif elev_ft != 'N/A':
                    st.write(f"**Elevation:** {elev_ft} ft")
                elif elev_m != 'N/A':
                    st.write(f"**Elevation:** {elev_m} m")
                else:
                    st.write(f"**Elevation:** N/A")
        
        # Button to load station data
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("📥 Load Station Data", type="secondary", width='stretch'):
                with st.spinner("Loading station data..."):
                    station_data = get_station_data(wmo_code, ashrae_version=2021, si_ip=unit_system)
                    if station_data:
                        st.session_state.selected_station_data = station_data
                        st.success("Station data loaded successfully!")
                    else:
                        st.error("Failed to load station data. Please try again.")
    
    # Add download button at the bottom
    if st.session_state.selected_station_data:
        # Get WMO code from session state
        wmo_code = st.session_state.get('wmo_code', 'unknown')

        display_station_data_in_pdf_format(st.session_state.selected_station_data)

        # Create and display download button for CSV
        csv_content = export_overview_data_to_csv(st.session_state.selected_station_data)
    
        st.markdown("---")
        st.markdown("### 📥 Export Overview Data")
    
        st.download_button(
            label="📊 Download Overview Data as CSV",
            data=csv_content,
            file_name=f"ashrae_overview_{wmo_code}_data.csv",
            mime="text/csv",
            width='stretch'
    )    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #6B7280;'>
        <p>ASHRAE 2021 Meteo Data v3.0 | Data provided by ashrae-meteo.info</p>
        <p>This tool retrieves ASHRAE 2021 meteorological design conditions for HVAC system design</p>
        <p><strong>Fixed Settings:</strong> Always shows 10 nearest stations | Always uses ASHRAE 2021 version</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
