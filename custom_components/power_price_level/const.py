DOMAIN = "power_price_level"
PLATFORMS = ["sensor"]

CONF_NORDPOOL_ENTITY = "nordpool_entity"
CONF_POWERPRICE_ENTITY = "powerprice_entity"

# Sensor name
CONF_SENSOR_NAME = "sensor_name"


# Direct numeric config (main currency unit)
CONF_GRID_DAY = "grid_day"
CONF_GRID_NIGHT = "grid_night"
CONF_ADDITIONAL = "additional"

DEFAULT_NAME = "Power Price"
DEFAULT_SENSOR_NAME = DEFAULT_NAME

DEFAULT_POWERPRICE_ENTITY = "sensor.power_price"
DEFAULT_NORDPOOL_ENTITY = "sensor.nordpool_kwh_oslo_nok_3_10_025"
DEFAULT_GRID_DAY = 0.0
DEFAULT_GRID_NIGHT = 0.0
DEFAULT_ADDITIONAL = 0.0

# Price level config (wizard)
CONF_CHEAP_PRICE = "cheap_price"
CONF_NIGHT_HOUR_END = "night_hour_end"
CONF_DAY_HOUR_END = "day_hour_end"
CONF_CHEAP_HOURS = "cheap_hours"
CONF_EXPENSIVE_HOURS = "expensive_hours"
CONF_CHEAP_HOURS_NIGHT = "cheap_hours_night"
CONF_CHEAP_HOURS_DAY = "cheap_hours_day"
CONF_CHEAP_HOURS_EVENING = "cheap_hours_evening"

# Defaults (safe, conservative)
DEFAULT_CHEAP_PRICE = 0.0
DEFAULT_NIGHT_HOUR_END = 6
DEFAULT_DAY_HOUR_END = 15
DEFAULT_CHEAP_HOURS = 5
DEFAULT_EXPENSIVE_HOURS = 5
DEFAULT_CHEAP_HOURS_NIGHT = 2
DEFAULT_CHEAP_HOURS_DAY = 2
DEFAULT_CHEAP_HOURS_EVENING = 2

# Night window start (e.g. 22 means night starts at 22:00 and ends at `night_hour_end`)
CONF_NIGHT_HOUR_START = "night_hour_start"
DEFAULT_NIGHT_HOUR_START = 22

# Separate grid night window (allows different night window for grid pricing vs level rules)
CONF_GRID_NIGHT_START = "grid_night_start"
CONF_GRID_NIGHT_END = "grid_night_end"
DEFAULT_GRID_NIGHT_START = DEFAULT_NIGHT_HOUR_START
DEFAULT_GRID_NIGHT_END = DEFAULT_NIGHT_HOUR_END

# Currency/unit selection
CONF_CURRENCY = "currency"
DEFAULT_CURRENCY = "NOK"

# map currency to the unit used for pricing inputs (major currency per kWh)
CURRENCY_SUBUNIT_MAP = {
	"NOK": "NOK/kWh",
	"DKK": "DKK/kWh",
	"SEK": "SEK/kWh",
	"EUR": "EUR/kWh",
}

# Level sensor language
CONF_LEVEL_LANGUAGE = "level_language"
DEFAULT_LEVEL_LANGUAGE = "en"

# Mapping for language selector display -> code
LANGUAGE_DISPLAY_MAP = {
	"English": "en",
	"Dansk": "da",
	"Deutsch": "de",
	"Eesti": "et",
	"Latviešu": "lv",
	"Lietuvių": "lt",
	"Nederlands": "nl",
	"Norsk": "nb",
	"Polski": "pl",
	"Suomi": "fi",
	"Svenska": "sv",
}

