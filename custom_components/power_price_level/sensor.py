from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Optional

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.util import dt as dt_util

from .const import (
    DEFAULT_NAME,
    CONF_SENSOR_NAME,
    CONF_NORDPOOL_ENTITY,
    CONF_POWERPRICE_ENTITY,
    CONF_GRID_DAY,
    CONF_GRID_NIGHT,
    CONF_ADDITIONAL,
    # Price level config (wizard)
    CONF_CHEAP_PRICE,
    CONF_NIGHT_HOUR_END,
    CONF_NIGHT_HOUR_START,
    CONF_DAY_HOUR_END,
    CONF_GRID_NIGHT_START,
    CONF_GRID_NIGHT_END,
    CONF_CHEAP_HOURS,
    CONF_EXPENSIVE_HOURS,
    CONF_CHEAP_HOURS_NIGHT,
    CONF_CHEAP_HOURS_DAY,
    CONF_CHEAP_HOURS_EVENING,
    CONF_CURRENCY,
    DEFAULT_CURRENCY,
    CONF_LEVEL_LANGUAGE,
    DEFAULT_LEVEL_LANGUAGE,
    DEFAULT_NIGHT_HOUR_START,
    DEFAULT_NIGHT_HOUR_END,
    DEFAULT_GRID_NIGHT_START,
    DEFAULT_GRID_NIGHT_END,
    CURRENCY_SUBUNIT_MAP,
)

from .const import LANGUAGE_DISPLAY_MAP

# Use the central currency -> unit mapping from const.py
_CURRENCY_UNIT_MAP = CURRENCY_SUBUNIT_MAP

# Localization labels for level sensor
_LEVEL_LABELS = {
    "en": {
        "unavailable": "Unavailable",
        "cheap": "Cheap",
        "cheapest_hour": "Cheapest hour",
        "cheapest_hours": "Cheapest hours",
        "cheap_time": "Cheap time",
        "most_expensive_hour": "Most expensive hour",
        "most_expensive_hours": "Most expensive hours",
        "normal": "Normal",
        "expensive": "Expensive",
    },
    "nb": {
        "unavailable": "Utilgjengelig",
        "cheap": "Billig",
        "cheapest_hour": "Billigste time",
        "cheapest_hours": "Billigste timer",
        "cheap_time": "Billig time",
        "most_expensive_hour": "Dyreste time",
        "most_expensive_hours": "Dyreste timer",
        "normal": "Normal",
        "expensive": "Dyrt",
    },
    "sv": {
        "unavailable": "Otillgänglig",
        "cheap": "Billig",
        "cheapest_hour": "Billigaste timmen",
        "cheapest_hours": "Billigaste timmarna",
        "cheap_time": "Billig tid",
        "most_expensive_hour": "Dyraste timmen",
        "most_expensive_hours": "Dyraste timmarna",
        "normal": "Normal",
        "expensive": "Dyrt",
    },
    "da": {
        "unavailable": "Utilgængelig",
        "cheap": "Billig",
        "cheapest_hour": "Billigste time",
        "cheapest_hours": "Billigste timer",
        "cheap_time": "Billig time",
        "most_expensive_hour": "Dyreste time",
        "most_expensive_hours": "Dyreste timer",
        "normal": "Normal",
        "expensive": "Dyrt",
    },
    "fi": {
        "unavailable": "Ei saatavilla",
        "cheap": "Edullinen",
        "cheapest_hour": "Halvin tunti",
        "cheapest_hours": "Edullisimmat tunnit",
        "cheap_time": "Edullinen tunti",
        "most_expensive_hour": "Kallein tunti",
        "most_expensive_hours": "Kalleimmat tunnit",
        "normal": "Normaali",
        "expensive": "Kallis",
    },
    "de": {
        "unavailable": "Nicht verfügbar",
        "cheap": "Günstig",
        "cheapest_hour": "Günstigste Stunde",
        "cheapest_hours": "Günstigste Stunden",
        "cheap_time": "Günstige Stunde",
        "most_expensive_hour": "Teuerste Stunde",
        "most_expensive_hours": "Teuerste Stunden",
        "normal": "Normal",
        "expensive": "Teuer",
    },
    "et": {
        "unavailable": "Pole saadaval",
        "cheap": "Soodne",
        "cheapest_hour": "Kõige odavam tund",
        "cheapest_hours": "Kõige odavamad tunnid",
        "cheap_time": "Soodne tund",
        "most_expensive_hour": "Kalleim tund",
        "most_expensive_hours": "Kalleimad tunnid",
        "normal": "Tavaline",
        "expensive": "Kallis",
    },
    "lv": {
        "unavailable": "Nav pieejams",
        "cheap": "Lēts",
        "cheapest_hour": "Lētākā stunda",
        "cheapest_hours": "Lētākās stundas",
        "cheap_time": "Lēta stunda",
        "most_expensive_hour": "Dārgākā stunda",
        "most_expensive_hours": "Dārgākās stundas",
        "normal": "Parasts",
        "expensive": "Dārgi",
    },
    "lt": {
        "unavailable": "Nėra prieinama",
        "cheap": "Pigu",
        "cheapest_hour": "Pigiausia valanda",
        "cheapest_hours": "Pigiausios valandos",
        "cheap_time": "Pigi valanda",
        "most_expensive_hour": "Brangiausia valanda",
        "most_expensive_hours": "Brangiausios valandos",
        "normal": "Normalu",
        "expensive": "Brangu",
    },
    "nl": {
        "unavailable": "Niet beschikbaar",
        "cheap": "Goedkoop",
        "cheapest_hour": "Goedkoopste uur",
        "cheapest_hours": "Goedkoopste uren",
        "cheap_time": "Goedkoop uur",
        "most_expensive_hour": "Duurste uur",
        "most_expensive_hours": "Duurste uren",
        "normal": "Normaal",
        "expensive": "Duur",
    },
    "pl": {
        "unavailable": "Niedostępne",
        "cheap": "Tanie",
        "cheapest_hour": "Najtańsza godzina",
        "cheapest_hours": "Najtańsze godziny",
        "cheap_time": "Tania godzina",
        "most_expensive_hour": "Najdroższa godzina",
        "most_expensive_hours": "Najdroższe godziny",
        "normal": "Normalna",
        "expensive": "Drogie",
    },
}


# ---------------------------
# Helpers (Power Price)
# ---------------------------

def _quarterhour_to_hourly(q: list[Any]) -> list[Optional[float]]:
    """Convert quarter-hour list into hourly averages with DST handling (23/25h)."""
    hourly: list[Optional[float]] = []
    if not isinstance(q, list):
        return hourly

    hour_count = (len(q) + 3) // 4
    for h in range(hour_count):
        start = h * 4
        sl = q[start : start + 4]
        vals = [v for v in sl if v is not None]
        hourly.append(sum(vals) / len(vals) if vals else None)

    # DST adjustments (match your earlier template approach)
    if len(hourly) == 23 and len(hourly) >= 2:
        hourly = hourly[0:2] + [hourly[1]] + hourly[2:]
    elif len(hourly) == 25:
        if len(hourly) >= 4 and hourly[2] is not None and hourly[3] is not None:
            merged = (hourly[2] + hourly[3]) / 2
        else:
            merged = hourly[2] if len(hourly) > 2 else None
        hourly = hourly[0:2] + [merged] + hourly[4:]

    return hourly


def _build_24_prices(hourly: list[Optional[float]], add_nok: float, dst_23: bool, additional: float = 0.0) -> list[Optional[float]]:
    """Build 24-hour price list with 23-hour DST correction + your hour 3 placeholder.

    `additional` is a fixed per-hour adder applied to all hours.
    """
    out: list[Optional[float]] = []
    for i in range(24):
        hour = i + 1
        idx = i - 1 if (dst_23 and i >= 2) else i

        val: Optional[float] = None
        if 0 <= idx < len(hourly):
            v = hourly[idx]
            if v is not None:
                val = round(v + add_nok + additional, 4)
            else:
                if idx - 1 >= 0 and (prev := hourly[idx - 1]) is not None:
                    val = round(prev + add_nok + additional, 4)

        # DST placeholder from your template
        if dst_23 and hour == 3:
            val = 10.0000

        out.append(val)

    return out


def _build_24_prices(hourly: list[Optional[float]], add_day_nok: float, add_night_nok: float, nighthourstart: int, nighthourend: int, dst_23: bool, additional: float = 0.0) -> list[Optional[float]]:
    """Build 24-hour price list applying day/night grid additions per hour.

    Handles night windows that wrap across midnight.
    """
    out: list[Optional[float]] = []
    for i in range(24):
        hour = i
        idx = i - 1 if (dst_23 and i >= 2) else i

        # determine whether this hour is in the night window
        if nighthourstart < nighthourend:
            is_night = nighthourstart <= hour < nighthourend
        else:
            is_night = hour >= nighthourstart or hour < nighthourend

        add_nok = add_night_nok if is_night else add_day_nok

        val: Optional[float] = None
        if 0 <= idx < len(hourly):
            v = hourly[idx]
            if v is not None:
                val = round(v + add_nok + additional, 4)
            else:
                if idx - 1 >= 0 and (prev := hourly[idx - 1]) is not None:
                    val = round(prev + add_nok + additional, 4)

        # DST placeholder (keep previous behavior: hour index 2 -> displayed as 3)
        if dst_23 and (hour + 1) == 3:
            val = 10.0000

        out.append(val)

    return out


def _k(price: Optional[float]) -> Optional[str]:
    """Key used for membership checks: match Jinja-ish string behavior with stable rounding."""
    if price is None:
        return None
    return f"{float(price):.4f}"


# ---------------------------
# Config containers
# ---------------------------

@dataclass(frozen=True)
class _PriceCfg:
    nordpool: str
    grid_day_ore: float
    grid_night_ore: float
    additional_ore: float


@dataclass(frozen=True)
class _LevelCfg:
    cheap_price_ore: float
    night_hour_end: int
    day_hour_end: int
    cheap_hours: int
    expensive_hours: int
    cheap_hours_night: int
    cheap_hours_day: int
    cheap_hours_evening: int


# ---------------------------
# Setup entry (create Power Price sensor first)
# ---------------------------

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    async_add_entities(
        [
            PowerPriceSensor(hass, entry),
            PowerPriceLevelSensor(hass, entry),
        ],
        update_before_add=True,
    )


# ---------------------------
# Sensor 1: Power Price (NOK/kWh)
# ---------------------------

class PowerPriceSensor(SensorEntity):
    _attr_icon = "mdi:cash-clock"
    _attr_native_unit_of_measurement = None
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self._entry = entry

        # Name comes from options or data (DEFAULT_NAME fallback)
        cfg = self._entry.options or self._entry.data
        self._attr_name = str(cfg.get(CONF_SENSOR_NAME, DEFAULT_NAME))

        # Used by PowerPriceLevelSensor to auto-discover this entity
        self._attr_unique_id = f"{entry.entry_id}_power_price"

        self._native_value: Optional[float] = None
        self._attrs: dict[str, Any] = {}

        # Read configuration from options if present, otherwise fall back to entry.data
        cfg_init = entry.options or entry.data
        self._cfg = _PriceCfg(
            nordpool=cfg_init.get(CONF_NORDPOOL_ENTITY, entry.data.get(CONF_NORDPOOL_ENTITY)),
            grid_day_ore=float(cfg_init.get(CONF_GRID_DAY, entry.data.get(CONF_GRID_DAY, 0.0))),
            grid_night_ore=float(cfg_init.get(CONF_GRID_NIGHT, entry.data.get(CONF_GRID_NIGHT, 0.0))),
            additional_ore=float(cfg_init.get(CONF_ADDITIONAL, entry.data.get(CONF_ADDITIONAL, 0.0))),
        )

        self._unsub = None
        

    @property
    def native_value(self) -> Optional[float]:
        return self._native_value

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return self._attrs

    async def async_added_to_hass(self) -> None:
        # Recompute whenever Nordpool updates
        @callback
        def _changed(_event) -> None:
            self.async_schedule_update_ha_state(True)

        self._unsub = async_track_state_change_event(self.hass, [self._cfg.nordpool], _changed)

        # ensure unit is set immediately according to current config/options
        cfg = self._entry.options or self._entry.data
        currency = str(cfg.get(CONF_CURRENCY, self._entry.data.get(CONF_CURRENCY, DEFAULT_CURRENCY)))
        self._attr_native_unit_of_measurement = _CURRENCY_UNIT_MAP.get(currency, "subunit/kWh")
        # write initial state to update unit in frontend
        self.async_write_ha_state()

    async def async_will_remove_from_hass(self) -> None:
        if self._unsub:
            self._unsub()
            self._unsub = None

    async def async_update(self) -> None:
        # Options override data for prices/adders
        cfg = self._entry.options or self._entry.data

        # Update name if user changed it in options
        self._attr_name = str(cfg.get(CONF_SENSOR_NAME, DEFAULT_NAME))

        # update unit based on configured currency (defaults to NOK)
        currency = str(cfg.get(CONF_CURRENCY, self._entry.data.get(CONF_CURRENCY, "NOK")))
        self._attr_native_unit_of_measurement = _CURRENCY_UNIT_MAP.get(currency, "subunit/kWh")

        nordpool_entity_id = self._cfg.nordpool
        nordpool_state = self.hass.states.get(nordpool_entity_id)
        nord_attrs = (nordpool_state.attributes if nordpool_state else {}) or {}

        today_q = nord_attrs.get("today") or []
        tomorrow_q = nord_attrs.get("tomorrow") or []

        hour = dt_util.now().hour

        # Read configured grid/additional values (expected as major currency units, e.g. NOK/kWh)
        grid_day = round(float(cfg.get(CONF_GRID_DAY, self._cfg.grid_day_ore)), 4)
        grid_night = round(float(cfg.get(CONF_GRID_NIGHT, self._cfg.grid_night_ore)), 4)
        additional = round(float(cfg.get(CONF_ADDITIONAL, self._cfg.additional_ore)), 4)

        # NOTE: matches your earlier template behavior: spot + grid_day in state
        today_hourly = _quarterhour_to_hourly(today_q)
        if today_hourly:
            idx = hour % len(today_hourly)
            spot = today_hourly[idx]
            self._native_value = round(float(spot) + grid_day + additional, 4) if spot is not None else None
        else:
            self._native_value = None

        dst_today_23 = len(today_hourly) == 23
        # Use the generic night window (not the grid-specific one) when building
        # the `prices` arrays so price-level calculations use the user-configured
        # night window (CONF_NIGHT_HOUR_START/END). Grid-specific variants
        # (`CONF_GRID_NIGHT_START/END`) are only for grid-adders display and
        # should not affect which hours are considered "night" for levels.
        # Per original template semantics: night ALWAYS starts at 0 for level
        # calculations (user expectation). Ignore configured grid/night start
        # here and use 0 as the fixed night start.
        nighthourstart = 0
        nighthourend = int(cfg.get(CONF_NIGHT_HOUR_END, DEFAULT_NIGHT_HOUR_END))
        prices_today = _build_24_prices(today_hourly, grid_day, grid_night, nighthourstart, nighthourend, dst_today_23, additional)

        prices_tomorrow: list[Optional[float]] = []
        if tomorrow_q:
            tomorrow_hourly = _quarterhour_to_hourly(tomorrow_q)
            dst_tomorrow_23 = len(tomorrow_hourly) == 23
            prices_tomorrow = _build_24_prices(tomorrow_hourly, grid_day, grid_night, nighthourstart, nighthourend, dst_tomorrow_23, additional)

        # ---- raw_today / raw_tomorrow (Nordpool-like) ----
        start_today = dt_util.start_of_local_day(dt_util.now())
        start_tomorrow = start_today + timedelta(days=1)

        raw_today = [
            {
                "start": (start_today + timedelta(hours=i)).isoformat(),
                "end": (start_today + timedelta(hours=i + 1)).isoformat(),
                "value": float(prices_today[i] or 0.0),
            }
            for i in range(len(prices_today))
        ]

        raw_tomorrow = [
            {
                "start": (start_tomorrow + timedelta(hours=i)).isoformat(),
                "end": (start_tomorrow + timedelta(hours=i + 1)).isoformat(),
                "value": float(prices_tomorrow[i] or 0.0),
            }
            for i in range(len(prices_tomorrow))
        ]

        self._attrs = {
            "config": {
                "grid_day": float(cfg.get(CONF_GRID_DAY, 0.0)),
                "grid_night": float(cfg.get(CONF_GRID_NIGHT, 0.0)),
                "grid_night_start": int(cfg.get(CONF_GRID_NIGHT_START, DEFAULT_GRID_NIGHT_START)),
                "grid_night_end": int(cfg.get(CONF_GRID_NIGHT_END, DEFAULT_GRID_NIGHT_END)),
                "additional": float(cfg.get(CONF_ADDITIONAL, 0.0)),
            },
            "prices": {"today": prices_today, "tomorrow": prices_tomorrow},
            "raw_today": raw_today,
            "raw_tomorrow": raw_tomorrow,
        }


# ---------------------------
# Sensor 2: Power Price Level (full rule set, configured in wizard)
# ---------------------------

class PowerPriceLevelSensor(SensorEntity):
    _attr_icon = "mdi:cash-multiple"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self._entry = entry

        # Name is base sensor name + ' Level'
        base = str(self._entry.options.get(CONF_SENSOR_NAME, self._entry.data.get(CONF_SENSOR_NAME, DEFAULT_NAME)))
        self._attr_name = f"{base} Level"

        self._attr_unique_id = f"{entry.entry_id}_power_price_level"

        self._state: Optional[str] = None
        self._attrs: dict[str, Any] = {}

        # Auto-discover the PowerPriceSensor from the same entry via entity registry unique_id
        self._power_price_unique_id = f"{entry.entry_id}_power_price"
        # Allow user-selected power price entity from options/data
        cfg_init = entry.options or entry.data
        self._power_price_entity_id: Optional[str] = str(cfg_init.get(CONF_POWERPRICE_ENTITY, entry.data.get(CONF_POWERPRICE_ENTITY, None))) if cfg_init.get(CONF_POWERPRICE_ENTITY, entry.data.get(CONF_POWERPRICE_ENTITY, None)) else None

        self._unsub = None

    @property
    def native_value(self) -> Optional[str]:
        return self._state

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return self._attrs

    def _resolve_power_price_entity_id(self) -> Optional[str]:
        ent_reg = er.async_get(self.hass)

        entity_id = ent_reg.async_get_entity_id(
            "sensor",
            "power_price_level",  # integration domain
            self._power_price_unique_id,
        )
        if entity_id:
            return entity_id

        # Fallback if user didn't rename and registry lookup fails
        if self.hass.states.get("sensor.power_price"):
            return "sensor.power_price"

        return None

    async def async_added_to_hass(self) -> None:
        # If user hasn't selected a custom power price entity, try to resolve the integration-created one
        if not self._power_price_entity_id:
            self._power_price_entity_id = self._resolve_power_price_entity_id()

        @callback
        def _changed(_event) -> None:
            self.async_schedule_update_ha_state(True)

        # Track the price sensor so level updates when prices change
        if self._power_price_entity_id:
            self._unsub = async_track_state_change_event(self.hass, [self._power_price_entity_id], _changed)

    async def async_will_remove_from_hass(self) -> None:
        if self._unsub:
            self._unsub()
            self._unsub = None

    def _get_pricelevel(self, hour: int, day_prices: list[Optional[float]], cfg: dict[str, Any]) -> str:
        # Wizard/Options values
        cheap_price_ore = float(cfg.get(CONF_CHEAP_PRICE, 0.0))
        nighthourend = int(cfg.get(CONF_NIGHT_HOUR_END, 0))
        dayhourend = int(cfg.get(CONF_DAY_HOUR_END, 24))
        cheaphours = int(cfg.get(CONF_CHEAP_HOURS, 0))
        expensivehours = int(cfg.get(CONF_EXPENSIVE_HOURS, 0))
        cheaphoursnight = int(cfg.get(CONF_CHEAP_HOURS_NIGHT, 0))
        cheaphoursday = int(cfg.get(CONF_CHEAP_HOURS_DAY, 0))
        cheaphoursevening = int(cfg.get(CONF_CHEAP_HOURS_EVENING, 0))

        # Cheap price threshold (main currency unit)
        cheapprice = cheap_price_ore

        nighthourstart = int(cfg.get(CONF_NIGHT_HOUR_START, DEFAULT_NIGHT_HOUR_START))
        eveninghourend = 24

        # localization: accept either stored code ('en') or older display name ('English')
        sel = str(cfg.get(CONF_LEVEL_LANGUAGE, DEFAULT_LEVEL_LANGUAGE))
        if sel in LANGUAGE_DISPLAY_MAP:
            # stored a display name, map to code
            lang = LANGUAGE_DISPLAY_MAP.get(sel, DEFAULT_LEVEL_LANGUAGE)
        else:
            lang = sel
        labels = _LEVEL_LABELS.get(lang, _LEVEL_LABELS[DEFAULT_LEVEL_LANGUAGE])

        if not isinstance(day_prices, list) or len(day_prices) < 24:
            return labels["unavailable"]

        p = day_prices[hour]
        if p is None:
            return labels["unavailable"]
        pricethishour = float(p)

        # Match template: sort the full 0:24 list (including any None)
        day24 = day_prices[:24]
        day24_sorted = sorted(day24, key=lambda x: (x is None, x))  # None last
        day24_sorted_desc = sorted(day24, key=lambda x: (x is None, x), reverse=True)  # None first in reverse

        cheapesthour = day24_sorted[0]
        mostexpensivehour = day24_sorted[23] if len(day24_sorted) >= 24 else None

        vals_for_avg = [v for v in day24 if v is not None]
        if not vals_for_avg:
            return labels["unavailable"]
        averageprice = sum(vals_for_avg) / len(vals_for_avg)

        # --- Build strings like template does ---
        # take the lowest `cheaphours` values (starting at index 0)
        cheapesthours_str = "[ " + ", ".join(
            str(day24_sorted[i]) for i in range(min(max(0, cheaphours), len(day24_sorted)))
        ) + " ]"

        # take the highest `expensivehours` values (starting at index 0 of the descending list)
        mostexpensivehours_str = "[ " + ", ".join(
            str(day24_sorted_desc[i]) for i in range(min(max(0, expensivehours), len(day24_sorted_desc)))
        ) + " ]"

        # Support night windows that wrap across midnight (e.g. 22 -> 06)
        if nighthourstart < nighthourend:
            night_slice = sorted(day24[nighthourstart:nighthourend], key=lambda x: (x is None, x))
        else:
            night_slice = sorted(day24[nighthourstart:] + day24[:nighthourend], key=lambda x: (x is None, x))
        day_slice = sorted(day24[nighthourend:dayhourend], key=lambda x: (x is None, x))
        eve_slice = sorted(day24[dayhourend:eveninghourend], key=lambda x: (x is None, x))

        cheapesthournight_str = "[ " + ", ".join(
            str(night_slice[i]) for i in range(max(0, cheaphoursnight))
            if i < len(night_slice)
        ) + " ]"

        cheapesthourday_str = "[ " + ", ".join(
            str(day_slice[i]) for i in range(max(0, cheaphoursday))
            if i < len(day_slice)
        ) + " ]"

        cheapesthourevening_str = "[ " + ", ".join(
            str(eve_slice[i]) for i in range(max(0, cheaphoursevening))
            if i < len(eve_slice)
        ) + " ]"

        # Use stable keys for membership checks to avoid string-format mismatches
        p_key = _k(pricethishour)

        # exact cheapest / most expensive comparisons using keys
        cheapest_key = _k(cheapesthour) if cheapesthour is not None else None
        mostexpensive_key = _k(mostexpensivehour) if mostexpensivehour is not None else None

        # Original decision order (template): cheap_price -> cheapest_hour ->
        # cheapest_hours -> per-period cheapest -> most-expensive -> normal/expensive
        if cheapprice > 0 and pricethishour <= cheapprice:
            return labels["cheap"]

        if cheapest_key is not None and p_key == cheapest_key:
            return labels["cheapest_hour"]

        # Build lists of keys for requested counts (start at index 0)
        cheapest_keys = [ _k(day24_sorted[i]) for i in range(min(max(0, cheaphours), len(day24_sorted))) if day24_sorted[i] is not None ]
        mostexpensive_keys = [ _k(day24_sorted_desc[i]) for i in range(min(max(0, expensivehours), len(day24_sorted_desc))) if day24_sorted_desc[i] is not None ]

        if p_key in cheapest_keys:
            return labels["cheapest_hours"]

        # Per-period cheapest sets (for night/day/evening slices) — no supplementation
        cheapest_night_keys = [ _k(night_slice[i]) for i in range(min(max(0, cheaphoursnight), len(night_slice))) if night_slice[i] is not None ]
        cheapest_day_keys = [ _k(day_slice[i]) for i in range(min(max(0, cheaphoursday), len(day_slice))) if day_slice[i] is not None ]
        cheapest_evening_keys = [ _k(eve_slice[i]) for i in range(min(max(0, cheaphoursevening), len(eve_slice))) if eve_slice[i] is not None ]

        # Check per-period cheap_time
        in_night = (nighthourstart < nighthourend and nighthourstart <= hour < nighthourend) or (
            nighthourstart >= nighthourend and (hour >= nighthourstart or hour < nighthourend)
        )
        in_day = nighthourend <= hour < dayhourend
        in_evening = dayhourend <= hour < eveninghourend

        if (
            (p_key in cheapest_day_keys and in_day)
            or (p_key in cheapest_night_keys and in_night)
            or (p_key in cheapest_evening_keys and in_evening)
        ):
            return labels["cheap_time"]

        # If this hour is one of the most expensive, prefer that label now
        if mostexpensive_key is not None and p_key == mostexpensive_key:
            return labels["most_expensive_hour"]
        if p_key in mostexpensive_keys:
            return labels["most_expensive_hours"]
        if pricethishour <= averageprice:
            return labels["normal"]
        if pricethishour > averageprice:
            return labels["expensive"]
        return labels["unavailable"]

    async def async_update(self) -> None:
        # Options override data
        cfg = self._entry.options or self._entry.data

        if not self._power_price_entity_id:
            self._power_price_entity_id = self._resolve_power_price_entity_id()

        if not self._power_price_entity_id:
            self._state = "Utilgjengelig"
            self._attrs = {
                "debug_source": "custom_components.power_price_level",
                "reason": "no_power_price_entity",
            }
            return

        power_price_state = self.hass.states.get(self._power_price_entity_id)
        if not power_price_state:
            self._state = "Utilgjengelig"
            self._attrs = {
                "debug_source": "custom_components.power_price_level",
                "reason": "power_price_missing",
            }
            return

        powerprice = power_price_state.attributes.get("prices")
        if not powerprice:
            self._state = "Utilgjengelig"
            self._attrs = {
                "debug_source": "custom_components.power_price_level",
                "reason": "no_prices_attribute",
            }
            return

        today = powerprice.get("today") or []
        tomorrow = powerprice.get("tomorrow") or []

        hour = dt_util.now().hour

        self._state = self._get_pricelevel(hour, today, cfg)

        self._attrs = {
            "source_entity": self._power_price_entity_id,
            "config": {
                "night_hour_end": int(cfg.get(CONF_NIGHT_HOUR_END, 0)),
                "day_hour_end": int(cfg.get(CONF_DAY_HOUR_END, 24)),
                "cheap_price": float(cfg.get(CONF_CHEAP_PRICE, 0.0)),
                "cheap_hours": int(cfg.get(CONF_CHEAP_HOURS, 0)),
                "expensive_hours": int(cfg.get(CONF_EXPENSIVE_HOURS, 0)),
                "cheap_hours_night": int(cfg.get(CONF_CHEAP_HOURS_NIGHT, 0)),
                "cheap_hours_day": int(cfg.get(CONF_CHEAP_HOURS_DAY, 0)),
                "cheap_hours_evening": int(cfg.get(CONF_CHEAP_HOURS_EVENING, 0)),
            },
            "prices": {
                "today": [self._get_pricelevel(h, today, cfg) for h in range(24)],
                "tomorrow": [self._get_pricelevel(h, tomorrow, cfg) for h in range(24)] if tomorrow else [],
            },
        }
