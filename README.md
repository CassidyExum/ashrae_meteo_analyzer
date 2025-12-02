# ASHRAE Meteo Station Finder 🌤️

A Streamlit web application for finding nearby weather stations and retrieving ASHRAE 2021 meteorological design data for Solar and BESS System design.

## Features

- **📍 Location Search**: Input latitude and longitude coordinates to find nearby weather stations
- **📊 Station Discovery**: Automatically finds the 10 closest weather stations to your coordinates
- **📋 Detailed Meteorological Data**: Retrieves comprehensive ASHRAE 2021 design conditions including:
  - Heating and cooling design temperatures
  - Extreme temperature statistics (20, 50-year return periods)
  - Monthly average temperatures
  - Monthly design dry bulb temperatures (0.4% and 2% levels)
- **📥 Data Export**: Download overview data as CSV for use in Excel
- **🔄 User-Friendly Interface**: Clean, intuitive layout with real-time data display

## Data Sources

- **ASHRAE Meteo API v3.0**: https://ashrae-meteo.info/v3.0/
- **ASHRAE Version**: 2021 (fixed)
- **Number of Stations**: Always returns 10 nearest stations
- **Unit System**: SI (metric) or IP (imperial) selectable

## Installation

### Prerequisites
- Python 3.8+
- pip (Python package manager)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/ashrae-meteo-finder.git
cd ashrae-meteo-finder
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
streamlit run app.py
```

## Requirements

Create a `requirements.txt` file with:
```
streamlit>=1.28.0
pandas>=2.0.0
requests>=2.31.0
```

Or install directly:
```bash
pip install streamlit pandas requests
```

## Usage

1. **Enter Coordinates**: Input latitude and longitude in the sidebar
2. **Find Stations**: Click "Find Nearest Stations" to discover nearby weather stations
3. **Select Station**: Choose a station from the dropdown menu
4. **Load Data**: Click "Load Station Data" to retrieve detailed meteorological information
5. **Export Data**: Download the overview data as CSV for analysis in Excel

## Data Parameters Retrieved

### Temperature Overview
- Extreme Annual Max/Min temperatures
- N-year return period values (20 and 50 years)
- Yearly 0.4% and 2.0% high temperatures
- Highest monthly temperatures (average, 0.4%, and 2.0%)
- Annual average temperature

### Station Information
- Station name and WMO code
- Location coordinates (latitude/longitude)
- Elevation (displayed in feet and meters)
- Data collection period
- Climate zone and geographical information

## API Endpoints Used

The application interacts with the ASHRAE Meteo API v3.0:

1. **Find Stations**: `https://ashrae-meteo.info/v3.0/request_places_get.php`
   - Parameters: `lat`, `long`, `number=10`, `ashrae_version=2021`

2. **Get Station Data**: `https://ashrae-meteo.info/v3.0/request_meteo_parametres_get.php`
   - Parameters: `wmo`, `ashrae_version=2021`, `si_ip=SI` or `IP`

## File Structure

```
ashrae-meteo-finder/
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── README.md             # This file
└── .gitignore           # Git ignore file
```

## Technical Details

- **Framework**: Streamlit for web interface
- **Data Processing**: pandas for data manipulation
- **API Communication**: requests for HTTP calls
- **Error Handling**: Comprehensive error handling for API failures
- **Encoding**: UTF-8 BOM support for Excel compatibility
- **Responsive Design**: Adapts to different screen sizes

## Known Limitations

- Requires internet connection to access ASHRAE API
- Limited to 10 nearest stations (API constraint)
- ASHRAE 2021 version fixed (cannot select other versions)
- Some stations may have incomplete data

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- ASHRAE for providing the meteorological data API
- Streamlit for the excellent web application framework

## Future Enhancements

- [ ] Add map visualization of station locations

---
