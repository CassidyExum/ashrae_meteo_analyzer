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
    
    # Table 1: Location & Basic Info
    st.markdown("---")
    st.markdown("### 📋 Location & Basic Information")
    location_data = {
        "Parameter": [
            "Latitude", "Longitude", "Country", "State/Region",
            "Time Zone", "Climate Zone", "Coldest Month", "Hottest Month",
            "Standard Pressure", "WBAN Code", "Warm Humid Location"
        ],
        "Value": [
            f"{data.get('lat', 'N/A')}°",
            f"{data.get('long', 'N/A')}°",
            data.get('country', 'N/A'),
            data.get('state', 'N/A'),
            f"UTC{data.get('time_zone', 'N/A')}",
            data.get('climate_zone', 'N/A'),
            data.get('coldest_month', 'N/A'),
            data.get('hottest_month', 'N/A'),
            f"{data.get('stdp', 'N/A')} kPa",
            data.get('wban', 'N/A'),
            "Yes" if data.get('warm_humid_location') == '1' else "No"
        ]
    }
    st.table(pd.DataFrame(location_data))
      
    # Table 2: Annual Cooling Design Conditions
    st.markdown("---")
    st.markdown("### Cooling Dry Bulb Values")
    cooling_data = {
        "Design Condition": ["0.4%", "2%"],
        "Dry Bulb (°C)": [
            data.get('cooling_DB_MCWB_0.4_DB', 'N/A'),
            data.get('cooling_DB_MCWB_2_DB', 'N/A')
        ],
    }
    st.table(pd.DataFrame(cooling_data))
    
    # Table 3: Extreme Temperatures
    st.markdown("---")
    st.markdown("### Extreme Temperatures (Dry Bulb)")
    extreme_db_data = {
        "": ["Extreme Annual Mean", "5-year", "10-year", "20-year", "50-year"],
        "Minimum (°C)": [
            data.get('extreme_annual_DB_mean_min', 'N/A'),
            data.get('n-year_return_period_values_of_extreme_DB_5_min', 'N/A'),
            data.get('n-year_return_period_values_of_extreme_DB_10_min', 'N/A'),
            data.get('n-year_return_period_values_of_extreme_DB_20_min', 'N/A'),
            data.get('n-year_return_period_values_of_extreme_DB_50_min', 'N/A')
        ],
        "Maximum (°C)": [
            data.get('extreme_annual_DB_mean_max', 'N/A'),
            data.get('n-year_return_period_values_of_extreme_DB_5_max', 'N/A'),
            data.get('n-year_return_period_values_of_extreme_DB_10_max', 'N/A'),
            data.get('n-year_return_period_values_of_extreme_DB_20_max', 'N/A'),
            data.get('n-year_return_period_values_of_extreme_DB_50_max', 'N/A')
        ]
    }
    st.table(pd.DataFrame(extreme_db_data))
    
    # Table 4: Monthly Average Temperatures
    st.markdown("---")
    st.markdown("### Dry Bulb Average Monthly Temperatures (°C)")
    monthly_data = {
        "Month": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                 "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        "Avg Temp (°C)": [
            data.get('dbavg_jan', data.get('tavg_jan', 'N/A')),
            data.get('dbavg_feb', data.get('tavg_feb', 'N/A')),
            data.get('dbavg_mar', data.get('tavg_mar', 'N/A')),
            data.get('dbavg_apr', data.get('tavg_apr', 'N/A')),
            data.get('dbavg_may', data.get('tavg_may', 'N/A')),
            data.get('dbavg_jun', data.get('tavg_jun', 'N/A')),
            data.get('dbavg_jul', data.get('tavg_jul', 'N/A')),
            data.get('dbavg_aug', data.get('tavg_aug', 'N/A')),
            data.get('dbavg_sep', data.get('tavg_sep', 'N/A')),
            data.get('dbavg_oct', data.get('tavg_oct', 'N/A')),
            data.get('dbavg_nov', data.get('tavg_nov', 'N/A')),
            data.get('dbavg_dec', data.get('tavg_dec', 'N/A'))
        ],
        "Std Dev (°C)": [
            data.get('dbstd_jan', data.get('sd_jan', 'N/A')),
            data.get('dbstd_feb', data.get('sd_feb', 'N/A')),
            data.get('dbstd_mar', data.get('sd_mar', 'N/A')),
            data.get('dbstd_apr', data.get('sd_apr', 'N/A')),
            data.get('dbstd_may', data.get('sd_may', 'N/A')),
            data.get('dbstd_jun', data.get('sd_jun', 'N/A')),
            data.get('dbstd_jul', data.get('sd_jul', 'N/A')),
            data.get('dbstd_aug', data.get('sd_aug', 'N/A')),
            data.get('dbstd_sep', data.get('sd_sep', 'N/A')),
            data.get('dbstd_oct', data.get('sd_oct', 'N/A')),
            data.get('dbstd_nov', data.get('sd_nov', 'N/A')),
            data.get('dbstd_dec', data.get('sd_dec', 'N/A'))
        ]
    }
    st.table(pd.DataFrame(monthly_data))
    st.metric("Annual Average Temperature", f"{data.get('dbavg_annual', data.get('tavg_annual', 'N/A'))}°C")

    # Table 5: Monthly Design Dry Bulb Temperatures 0.4%
    st.markdown("---")
    st.markdown("### Monthly Design Dry Bulb Temperatures 0.4% (°C)")
    monthly_db_04_data = {
        "Month": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                 "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        "Avg Temp (°C)": [
            data.get('0.4_DB_jan', 'N/A'),
            data.get('0.4_DB_feb', 'N/A'),
            data.get('0.4_DB_mar', 'N/A'),
            data.get('0.4_DB_apr', 'N/A'),
            data.get('0.4_DB_may', 'N/A'),
            data.get('0.4_DB_jun', 'N/A'),
            data.get('0.4_DB_jul', 'N/A'),
            data.get('0.4_DB_aug', 'N/A'),
            data.get('0.4_DB_sep', 'N/A'),
            data.get('0.4_DB_oct', 'N/A'),
            data.get('0.4_DB_nov', 'N/A'),
            data.get('0.4_DB_dec', 'N/A')
        ]
    }
    st.table(pd.DataFrame(monthly_db_04_data))

     # Table 7: Monthly Design Dry Bulb Temperatures 2%
    st.markdown("---")
    st.markdown("### Monthly Design Dry Bulb Temperatures 2% (°C)")
    monthly_db_2_data = {
        "Month": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                 "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        "Avg Temp (°C)": [
            data.get('2_DB_jan', 'N/A'),
            data.get('2_DB_feb', 'N/A'),
            data.get('2_DB_mar', 'N/A'),
            data.get('2_DB_apr', 'N/A'),
            data.get('2_DB_may', 'N/A'),
            data.get('2_DB_jun', 'N/A'),
            data.get('2_DB_jul', 'N/A'),
            data.get('2_DB_aug', 'N/A'),
            data.get('2_DB_sep', 'N/A'),
            data.get('2_DB_oct', 'N/A'),
            data.get('2_DB_nov', 'N/A'),
            data.get('2_DB_dec', 'N/A')
        ]
    }
    st.table(pd.DataFrame(monthly_db_2_data))

    # Table 8: Solar Radiation
    st.markdown("---")
    st.markdown("### ☀️ Solar Conditions")
    if data.get('taub_jan'):
        # Create tabs for different solar data
        solar_tab1, solar_tab2 = st.tabs(["Optical Depth", "Solar Irradiance"])
        
        with solar_tab1:
            optical_depth_data = {
                "Month": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                         "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
                "Beam (τb)": [
                    data.get('taub_jan', 'N/A'),
                    data.get('taub_feb', 'N/A'),
                    data.get('taub_mar', 'N/A'),
                    data.get('taub_apr', 'N/A'),
                    data.get('taub_may', 'N/A'),
                    data.get('taub_jun', 'N/A'),
                    data.get('taub_jul', 'N/A'),
                    data.get('taub_aug', 'N/A'),
                    data.get('taub_sep', 'N/A'),
                    data.get('taub_oct', 'N/A'),
                    data.get('taub_nov', 'N/A'),
                    data.get('taub_dec', 'N/A')
                ],
                "Diffuse (τd)": [
                    data.get('taud_jan', 'N/A'),
                    data.get('taud_feb', 'N/A'),
                    data.get('taud_mar', 'N/A'),
                    data.get('taud_apr', 'N/A'),
                    data.get('taud_may', 'N/A'),
                    data.get('taud_jun', 'N/A'),
                    data.get('taud_jul', 'N/A'),
                    data.get('taud_aug', 'N/A'),
                    data.get('taud_sep', 'N/A'),
                    data.get('taud_oct', 'N/A'),
                    data.get('taud_nov', 'N/A'),
                    data.get('taud_dec', 'N/A')
                ]
            }
            st.table(pd.DataFrame(optical_depth_data))
        
        with solar_tab2:
            irradiance_data = {
                "Month": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                         "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
                "Beam Normal (W/m²)": [
                    data.get('ebn_noon_jan', 'N/A'),
                    data.get('ebn_noon_feb', 'N/A'),
                    data.get('ebn_noon_mar', 'N/A'),
                    data.get('ebn_noon_apr', 'N/A'),
                    data.get('ebn_noon_may', 'N/A'),
                    data.get('ebn_noon_jun', 'N/A'),
                    data.get('ebn_noon_jul', 'N/A'),
                    data.get('ebn_noon_aug', 'N/A'),
                    data.get('ebn_noon_sep', 'N/A'),
                    data.get('ebn_noon_oct', 'N/A'),
                    data.get('ebn_noon_nov', 'N/A'),
                    data.get('ebn_noon_dec', 'N/A')
                ],
                "Diffuse Horizontal (W/m²)": [
                    data.get('edn_noon_jan', 'N/A'),
                    data.get('edn_noon_feb', 'N/A'),
                    data.get('edn_noon_mar', 'N/A'),
                    data.get('edn_noon_apr', 'N/A'),
                    data.get('edn_noon_may', 'N/A'),
                    data.get('edn_noon_jun', 'N/A'),
                    data.get('edn_noon_jul', 'N/A'),
                    data.get('edn_noon_aug', 'N/A'),
                    data.get('edn_noon_sep', 'N/A'),
                    data.get('edn_noon_oct', 'N/A'),
                    data.get('edn_noon_nov', 'N/A'),
                    data.get('edn_noon_dec', 'N/A')
                ]
            }
            st.table(pd.DataFrame(irradiance_data))
def export_station_data_to_csv(data: Dict) -> str:
    """Export all displayed station data to CSV format matching the display"""
    if not data:
        return ""
    
    import csv
    import io
    
    csv_data = io.StringIO()
    writer = csv.writer(csv_data)
    
    # Write header
    writer.writerow(["Category", "Parameter", "Value", "Units"])
    
    # 1. Station Information
    writer.writerow(["Station Information", "Station Name", data.get('place', 'N/A'), ""])
    writer.writerow(["Station Information", "WMO Code", data.get('wmo', 'N/A'), ""])
    
    elev_m = data.get('elev', 'N/A')
    elev_ft = 'N/A'
    if elev_m != 'N/A' and elev_m:
        try:
            elev_ft = int(float(elev_m) * 3.28084)
        except:
            elev_ft = 'N/A'
    writer.writerow(["Station Information", "Elevation", f"{elev_ft} ft ({elev_m} m)", "feet/meters"])
    writer.writerow(["Station Information", "Data Period", data.get('period', 'N/A'), ""])
    
    # 2. Location & Basic Information
    location_params = [
        ("Latitude", data.get('lat', 'N/A'), "degrees"),
        ("Longitude", data.get('long', 'N/A'), "degrees"),
        ("Country", data.get('country', 'N/A'), ""),
        ("State/Region", data.get('state', 'N/A'), ""),
        ("Time Zone", f"UTC{data.get('time_zone', 'N/A')}", ""),
        ("Climate Zone", data.get('climate_zone', 'N/A'), ""),
        ("Coldest Month", data.get('coldest_month', 'N/A'), ""),
        ("Hottest Month", data.get('hottest_month', 'N/A'), ""),
        ("Standard Pressure", data.get('stdp', 'N/A'), "kPa"),
        ("WBAN Code", data.get('wban', 'N/A'), ""),
        ("Warm Humid Location", "Yes" if data.get('warm_humid_location') == '1' else "No", "")
    ]
    
    for param, value, unit in location_params:
        writer.writerow(["Location & Basic Information", param, value, unit])
    
    # 3. Cooling Dry Bulb Values
    cooling_designs = ["0.4%", "2%"]
    db_fields = ['cooling_DB_MCWB_0.4_DB', 'cooling_DB_MCWB_2_DB']
    
    for design, db_field in zip(cooling_designs, db_fields):
        writer.writerow(["Cooling Dry Bulb Values", f"{design} Dry Bulb", data.get(db_field, 'N/A'), "°C"])
    
    # 4. Extreme Temperatures (Dry Bulb)
    extreme_categories = ["Extreme Annual Mean", "5-year", "10-year", "20-year", "50-year"]
    min_fields = [
        'extreme_annual_DB_mean_min',
        'n-year_return_period_values_of_extreme_DB_5_min',
        'n-year_return_period_values_of_extreme_DB_10_min',
        'n-year_return_period_values_of_extreme_DB_20_min',
        'n-year_return_period_values_of_extreme_DB_50_min'
    ]
    max_fields = [
        'extreme_annual_DB_mean_max',
        'n-year_return_period_values_of_extreme_DB_5_max',
        'n-year_return_period_values_of_extreme_DB_10_max',
        'n-year_return_period_values_of_extreme_DB_20_max',
        'n-year_return_period_values_of_extreme_DB_50_max'
    ]
    
    for category, min_field, max_field in zip(extreme_categories, min_fields, max_fields):
        writer.writerow(["Extreme Temperatures (Dry Bulb)", f"{category} Minimum", data.get(min_field, 'N/A'), "°C"])
        writer.writerow(["Extreme Temperatures (Dry Bulb)", f"{category} Maximum", data.get(max_field, 'N/A'), "°C"])
    
    # 5. Monthly Average Temperatures
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    
    # Monthly average temperatures
    temp_fields = ['dbavg_jan', 'dbavg_feb', 'dbavg_mar', 'dbavg_apr', 'dbavg_may', 'dbavg_jun',
                  'dbavg_jul', 'dbavg_aug', 'dbavg_sep', 'dbavg_oct', 'dbavg_nov', 'dbavg_dec']
    
    # Monthly standard deviations
    std_fields = ['dbstd_jan', 'dbstd_feb', 'dbstd_mar', 'dbstd_apr', 'dbstd_may', 'dbstd_jun',
                 'dbstd_jul', 'dbstd_aug', 'dbstd_sep', 'dbstd_oct', 'dbstd_nov', 'dbstd_dec']
    
    for month, temp_field, std_field in zip(months, temp_fields, std_fields):
        # Use fallback to tavg_ fields if dbavg_ fields not available
        temp_value = data.get(temp_field, data.get(f'tavg_{month.lower()}', 'N/A'))
        std_value = data.get(std_field, data.get(f'sd_{month.lower()}', 'N/A'))
        
        writer.writerow(["Monthly Average Temperatures", f"{month} Average Temperature", temp_value, "°C"])
        writer.writerow(["Monthly Average Temperatures", f"{month} Standard Deviation", std_value, "°C"])
    
    # Annual average
    annual_temp = data.get('dbavg_annual', data.get('tavg_annual', 'N/A'))
    writer.writerow(["Monthly Average Temperatures", "Annual Average Temperature", annual_temp, "°C"])
    
    # 6. Monthly Design Dry Bulb Temperatures 0.4%
    db_04_fields = ['0.4_DB_jan', '0.4_DB_feb', '0.4_DB_mar', '0.4_DB_apr', '0.4_DB_may', '0.4_DB_jun',
                   '0.4_DB_jul', '0.4_DB_aug', '0.4_DB_sep', '0.4_DB_oct', '0.4_DB_nov', '0.4_DB_dec']
    
    for month, field in zip(months, db_04_fields):
        writer.writerow(["Monthly Design Dry Bulb Temperatures 0.4%", f"{month} 0.4% DB", data.get(field, 'N/A'), "°C"])
    
    # 7. Monthly Design Dry Bulb Temperatures 2%
    db_2_fields = ['2_DB_jan', '2_DB_feb', '2_DB_mar', '2_DB_apr', '2_DB_may', '2_DB_jun',
                  '2_DB_jul', '2_DB_aug', '2_DB_sep', '2_DB_oct', '2_DB_nov', '2_DB_dec']
    
    for month, field in zip(months, db_2_fields):
        writer.writerow(["Monthly Design Dry Bulb Temperatures 2%", f"{month} 2% DB", data.get(field, 'N/A'), "°C"])
    
    # 8. Solar Conditions
    if data.get('taub_jan'):
        # Optical Depth - Beam
        taub_fields = ['taub_jan', 'taub_feb', 'taub_mar', 'taub_apr', 'taub_may', 'taub_jun',
                      'taub_jul', 'taub_aug', 'taub_sep', 'taub_oct', 'taub_nov', 'taub_dec']
        
        # Optical Depth - Diffuse
        taud_fields = ['taud_jan', 'taud_feb', 'taud_mar', 'taud_apr', 'taud_may', 'taud_jun',
                      'taud_jul', 'taud_aug', 'taud_sep', 'taud_oct', 'taud_nov', 'taud_dec']
        
        # Solar Irradiance - Beam Normal
        ebn_fields = ['ebn_noon_jan', 'ebn_noon_feb', 'ebn_noon_mar', 'ebn_noon_apr', 'ebn_noon_may', 'ebn_noon_jun',
                     'ebn_noon_jul', 'ebn_noon_aug', 'ebn_noon_sep', 'ebn_noon_oct', 'ebn_noon_nov', 'ebn_noon_dec']
        
        # Solar Irradiance - Diffuse Horizontal
        edn_fields = ['edn_noon_jan', 'edn_noon_feb', 'edn_noon_mar', 'edn_noon_apr', 'edn_noon_may', 'edn_noon_jun',
                     'edn_noon_jul', 'edn_noon_aug', 'edn_noon_sep', 'edn_noon_oct', 'edn_noon_nov', 'edn_noon_dec']
        
        for month, taub_field, taud_field, ebn_field, edn_field in zip(months, taub_fields, taud_fields, ebn_fields, edn_fields):
            writer.writerow(["Solar Conditions (Optical Depth)", f"{month} Beam (τb)", data.get(taub_field, 'N/A'), ""])
            writer.writerow(["Solar Conditions (Optical Depth)", f"{month} Diffuse (τd)", data.get(taud_field, 'N/A'), ""])
            writer.writerow(["Solar Conditions (Solar Irradiance)", f"{month} Beam Normal", data.get(ebn_field, 'N/A'), "W/m²"])
            writer.writerow(["Solar Conditions (Solar Irradiance)", f"{month} Diffuse Horizontal", data.get(edn_field, 'N/A'), "W/m²"])
    
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
    
    # Display station data if available
    if st.session_state.selected_station_data:
        st.markdown("---")
        st.markdown('<h2 class="sub-header">📋 Station Meteorological Data (ASHRAE 2021)</h2>', unsafe_allow_html=True)
        
        # Display the data in PDF-like format
        display_station_data_in_pdf_format(st.session_state.selected_station_data)
        
    # Replace the download button section with this:

    # Add download button at the bottom
    st.markdown("---")
    st.markdown("### 📥 Export Data")

    # Create CSV export
    if st.button("📊 Export All Data to CSV", type="secondary", width='stretch'):
        csv_content = export_station_data_to_csv(st.session_state.selected_station_data)
        # Create download button for CSV
        st.download_button(
            label="⬇️ Download CSV",
            data=csv_content,
            file_name=f"ashrae_station_{wmo_code}_data.csv",
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
