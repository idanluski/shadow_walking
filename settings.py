
import pvlib
from datetime import datetime,date
import pytz
from astral.sun import sun
from astral import LocationInfo




# Location of Ben Gurion University
latitude = 31.261
longitude = 34.802

# Set the location using pvlib's Location class and specify the timezone
location = pvlib.location.Location(latitude, longitude, tz='Asia/Jerusalem')

# Set the time with the correct timezone
time = datetime(2024, 12, 9,10, 17, tzinfo=pytz.timezone('Asia/Jerusalem'))

# Get the solar position at the specified time and location
solar_position = location.get_solarposition(time)


# Shadow penalty factor
shadow_penalty_factor = 0.5

def is_sun_out(location, check_time):
    # Get solar position at the specified time and location
    solar_position = location.get_solarposition(check_time)
    
    # Check the solar zenith angle
    solar_zenith = solar_position['zenith'].values[0]
    
    # If the solar zenith angle is less than 90 degrees, the sun is above the horizon
    if solar_zenith < 90:
        return True
    else:
        return False