
import pvlib
from datetime import datetime
import pytz



# Location of Ben Gurion University
latitude = 31.261
longitude = 34.802

# Set the location using pvlib's Location class and specify the timezone
location = pvlib.location.Location(latitude, longitude, tz='Asia/Jerusalem')

# Set the time with the correct timezone
time = datetime(2024, 11, 27, 14, 30, tzinfo=pytz.timezone('Asia/Jerusalem'))

# Get the solar position at the specified time and location
solar_position = location.get_solarposition(time)


# Shadow penalty factor
shadow_penalty_factor = 0.5

