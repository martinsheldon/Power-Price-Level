from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import translation as translation_helper
from homeassistant.helpers import selector


from .options_flow import PowerPriceLevelOptionsFlowHandler
from .const import (
    CONF_ADDITIONAL,
    CONF_CHEAP_HOURS,
    CONF_CHEAP_HOURS_DAY,
    CONF_CHEAP_HOURS_EVENING,
    CONF_CHEAP_HOURS_NIGHT,
    CONF_CHEAP_PRICE,
    CONF_CURRENCY,
    CONF_DAY_HOUR_END,
    CONF_EXPENSIVE_HOURS,
    CONF_GRID_DAY,
    CONF_GRID_NIGHT,
    CONF_GRID_NIGHT_END,
    CONF_GRID_NIGHT_START,
    CONF_LEVEL_LANGUAGE,
    CONF_NIGHT_HOUR_END,
    CONF_NIGHT_HOUR_START,
    CONF_NORDPOOL_ENTITY,
    CONF_SENSOR_NAME,
    CURRENCY_UNIT_MAP,
    DEFAULT_ADDITIONAL,
    DEFAULT_CHEAP_HOURS,
    DEFAULT_CHEAP_HOURS_DAY,
    DEFAULT_CHEAP_HOURS_EVENING,
    DEFAULT_CHEAP_HOURS_NIGHT,
    DEFAULT_CHEAP_PRICE,
    DEFAULT_CURRENCY,
    DEFAULT_DAY_HOUR_END,
    DEFAULT_EXPENSIVE_HOURS,
    DEFAULT_GRID_DAY,
    DEFAULT_GRID_NIGHT,
    DEFAULT_GRID_NIGHT_END,
    DEFAULT_GRID_NIGHT_START,
    DEFAULT_LEVEL_LANGUAGE,
    DEFAULT_NAME,
    DEFAULT_NIGHT_HOUR_END,
    DEFAULT_NIGHT_HOUR_START,
    DEFAULT_NORDPOOL_ENTITY,
    DOMAIN,
    LANGUAGE_DISPLAY_MAP,
)
from .util import parse_unit


def _unit_to_str(v: float) -> str:
    """Format a stored numeric value for the UI in main currency units with comma decimal.
    """
    if v is None:
        v = 0.0
    # Values are stored and displayed in major currency units (e.g. NOK/kWh)
    return f"{v:.4f}".replace(".", ",")


class PowerPriceLevelConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Power Price Level."""

    VERSION = 2

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return PowerPriceLevelOptionsFlowHandler(config_entry)

    def _find_nordpool_entity(self) -> str | None:
        try:
            for st in self.hass.states.async_all():
                eid = (st.entity_id or "").lower()
                name = str(st.attributes.get("friendly_name", "") or "").lower()
                if "nordpool" in eid or "nordpool" in name:
                    return st.entity_id
        except Exception:
            pass
        return None

    async def async_step_user(self, user_input=None):
        """First (basic) step: Nordpool source and sensor name."""
        errors: dict[str, str] = {}

        # Defaults for this step
        defaults = {
            CONF_NORDPOOL_ENTITY: DEFAULT_NORDPOOL_ENTITY,
            CONF_SENSOR_NAME: DEFAULT_NAME,
            CONF_CURRENCY: DEFAULT_CURRENCY,
            CONF_LEVEL_LANGUAGE: DEFAULT_LEVEL_LANGUAGE,
        }

        # Try to auto-detect an entity containing 'nordpool' if no explicit default
        try:
            candidate = self._find_nordpool_entity()
            if candidate:
                defaults[CONF_NORDPOOL_ENTITY] = candidate
        except Exception:
            pass

        if user_input is not None:
            try:
                nord = str(user_input[CONF_NORDPOOL_ENTITY]).strip()
                name = str(user_input[CONF_SENSOR_NAME]).strip()
                if not nord:
                    raise ValueError("nordpool entity empty")
                if not name:
                    raise ValueError("sensor name empty")

                # store temporary and proceed to costs step
                self._temp = {CONF_NORDPOOL_ENTITY: nord, CONF_SENSOR_NAME: name}
                self._temp[CONF_CURRENCY] = str(user_input.get(CONF_CURRENCY, DEFAULT_CURRENCY))
                sel = user_input.get(CONF_LEVEL_LANGUAGE, DEFAULT_LEVEL_LANGUAGE)
                self._temp[CONF_LEVEL_LANGUAGE] = LANGUAGE_DISPLAY_MAP.get(sel, sel)
                return await self.async_step_costs()

            except Exception:
                errors["base"] = "invalid_input"
                defaults.update(user_input)

        schema = vol.Schema(
            {
                vol.Required(CONF_SENSOR_NAME, default=defaults[CONF_SENSOR_NAME]): str,
                vol.Required(CONF_NORDPOOL_ENTITY, default=defaults[CONF_NORDPOOL_ENTITY]): selector.EntitySelector({"domain": "sensor"}),
                vol.Required(
                    CONF_LEVEL_LANGUAGE,
                    default=(
                        next((k for k, v in LANGUAGE_DISPLAY_MAP.items() if v == defaults[CONF_LEVEL_LANGUAGE]),
                             defaults[CONF_LEVEL_LANGUAGE])
                    ),
                ): vol.In(list(LANGUAGE_DISPLAY_MAP.keys())),
                # ensure stored/legacy currency defaults that are not supported don't break the form
                vol.Required(
                    CONF_CURRENCY,
                    default=(defaults[CONF_CURRENCY] if defaults.get(CONF_CURRENCY) in ["NOK", "SEK", "DKK", "EUR"] else DEFAULT_CURRENCY),
                ): vol.In(["NOK", "SEK", "DKK", "EUR"]),
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)


    async def async_step_costs(self, user_input=None):
        """Costs step: grid/additional and cheap threshold."""
        errors: dict[str, str] = {}

        defaults = {
            CONF_GRID_DAY: _unit_to_str(DEFAULT_GRID_DAY),
            CONF_GRID_NIGHT: _unit_to_str(DEFAULT_GRID_NIGHT),
            CONF_ADDITIONAL: _unit_to_str(DEFAULT_ADDITIONAL),
            CONF_CHEAP_PRICE: _unit_to_str(DEFAULT_CHEAP_PRICE),
            CONF_NIGHT_HOUR_START: DEFAULT_NIGHT_HOUR_START,
            CONF_NIGHT_HOUR_END: DEFAULT_NIGHT_HOUR_END,
            CONF_GRID_NIGHT_START: DEFAULT_GRID_NIGHT_START,
            CONF_GRID_NIGHT_END: DEFAULT_GRID_NIGHT_END,
        }

        # Merge any temp values from previous step (sensor name / nordpool)
        if hasattr(self, "_temp") and self._temp:
            defaults.update(self._temp)
        
        # determine unit suffix for the ore fields based on selected currency
        currency = str(defaults.get(CONF_CURRENCY, DEFAULT_CURRENCY))
        unit_suffix = CURRENCY_UNIT_MAP.get(currency, "subunit/kWh")

        if user_input is not None:
            try:
                # save cost fields in temp and proceed to hours step (parse as main currency unit)
                self._temp.update(
                    {
                        CONF_GRID_DAY: parse_unit(str(user_input[CONF_GRID_DAY])),
                        CONF_GRID_NIGHT: parse_unit(str(user_input[CONF_GRID_NIGHT])),
                        CONF_GRID_NIGHT_START: int(user_input.get(CONF_GRID_NIGHT_START, defaults[CONF_GRID_NIGHT_START])),
                        CONF_GRID_NIGHT_END: int(user_input.get(CONF_GRID_NIGHT_END, defaults[CONF_GRID_NIGHT_END])),
                        CONF_ADDITIONAL: parse_unit(str(user_input[CONF_ADDITIONAL])),
                        CONF_CHEAP_PRICE: parse_unit(str(user_input[CONF_CHEAP_PRICE])),
                        CONF_NIGHT_HOUR_START: int(user_input.get(CONF_NIGHT_HOUR_START, defaults[CONF_NIGHT_HOUR_START])),
                        CONF_NIGHT_HOUR_END: int(user_input.get(CONF_NIGHT_HOUR_END, defaults[CONF_NIGHT_HOUR_END])),
                    }
                )
                return await self.async_step_hours()

            except Exception:
                errors["base"] = "invalid_input"
                defaults.update(user_input)

        schema = vol.Schema(
            {
                vol.Required(CONF_GRID_DAY, default=defaults[CONF_GRID_DAY], description={"suffix": unit_suffix}): str,
                vol.Required(CONF_GRID_NIGHT, default=defaults[CONF_GRID_NIGHT], description={"suffix": unit_suffix}): str,
                vol.Required(CONF_ADDITIONAL, default=defaults[CONF_ADDITIONAL], description={"suffix": unit_suffix}): str,
                vol.Required(CONF_CHEAP_PRICE, default=defaults[CONF_CHEAP_PRICE], description={"suffix": unit_suffix}): str,

                vol.Required(CONF_GRID_NIGHT_START, default=defaults[CONF_GRID_NIGHT_START]): selector.NumberSelector({"min": 0, "max": 23, "step": 1, "mode": "box"}),
                vol.Required(CONF_GRID_NIGHT_END, default=defaults[CONF_GRID_NIGHT_END]): selector.NumberSelector({"min": 0, "max": 23, "step": 1, "mode": "box"}),
            }
        )

        return self.async_show_form(step_id="costs", data_schema=schema, errors=errors)


    async def async_step_hours(self, user_input=None):
        """Hours step: night/day ends and counts."""
        errors: dict[str, str] = {}

        defaults = {
            CONF_NIGHT_HOUR_END: DEFAULT_NIGHT_HOUR_END,
            CONF_DAY_HOUR_END: DEFAULT_DAY_HOUR_END,
            CONF_CHEAP_HOURS: DEFAULT_CHEAP_HOURS,
            CONF_EXPENSIVE_HOURS: DEFAULT_EXPENSIVE_HOURS,
            CONF_CHEAP_HOURS_NIGHT: DEFAULT_CHEAP_HOURS_NIGHT,
            CONF_CHEAP_HOURS_DAY: DEFAULT_CHEAP_HOURS_DAY,
            CONF_CHEAP_HOURS_EVENING: DEFAULT_CHEAP_HOURS_EVENING,
        }

        # Merge any temp values we already collected
        if hasattr(self, "_temp") and self._temp:
            defaults.update(self._temp)

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_NIGHT_HOUR_END,
                    default=defaults[CONF_NIGHT_HOUR_END],
                ): selector.NumberSelector({"min": 0, "max": 24, "step": 1, "mode": "box"}),
                vol.Required(
                    CONF_DAY_HOUR_END,
                    default=defaults[CONF_DAY_HOUR_END],
                ): selector.NumberSelector({"min": 0, "max": 24, "step": 1, "mode": "box"}),
                vol.Required(
                    CONF_CHEAP_HOURS,
                    default=defaults[CONF_CHEAP_HOURS],
                ): selector.NumberSelector({"min": 0, "max": 24, "step": 1, "mode": "box"}),
                vol.Required(
                    CONF_EXPENSIVE_HOURS,
                    default=defaults[CONF_EXPENSIVE_HOURS],
                ): selector.NumberSelector({"min": 0, "max": 24, "step": 1, "mode": "box"}),
                vol.Required(
                    CONF_CHEAP_HOURS_NIGHT,
                    default=defaults[CONF_CHEAP_HOURS_NIGHT],
                ): selector.NumberSelector({"min": 0, "max": 8, "step": 1, "mode": "box"}),
                vol.Required(
                    CONF_CHEAP_HOURS_DAY,
                    default=defaults[CONF_CHEAP_HOURS_DAY],
                ): selector.NumberSelector({"min": 0, "max": 8, "step": 1, "mode": "box"}),
                vol.Required(
                    CONF_CHEAP_HOURS_EVENING,
                    default=defaults[CONF_CHEAP_HOURS_EVENING],
                ): selector.NumberSelector({"min": 0, "max": 8, "step": 1, "mode": "box"}),
                
            }
        )

        if user_input is not None:
            try:
                data = {
                    CONF_NORDPOOL_ENTITY: self._temp[CONF_NORDPOOL_ENTITY],
                    CONF_SENSOR_NAME: self._temp[CONF_SENSOR_NAME],
                    CONF_CURRENCY: str(self._temp.get(CONF_CURRENCY, DEFAULT_CURRENCY)),
                    CONF_GRID_DAY: parse_unit(str(self._temp.get(CONF_GRID_DAY, DEFAULT_GRID_DAY))),
                    CONF_GRID_NIGHT: parse_unit(str(self._temp.get(CONF_GRID_NIGHT, DEFAULT_GRID_NIGHT))),
                    CONF_GRID_NIGHT_START: int(self._temp.get(CONF_GRID_NIGHT_START, DEFAULT_GRID_NIGHT_START)),
                    CONF_GRID_NIGHT_END: int(self._temp.get(CONF_GRID_NIGHT_END, DEFAULT_GRID_NIGHT_END)),
                    CONF_ADDITIONAL: parse_unit(str(self._temp.get(CONF_ADDITIONAL, DEFAULT_ADDITIONAL))),
                    CONF_CHEAP_PRICE: parse_unit(str(self._temp.get(CONF_CHEAP_PRICE, DEFAULT_CHEAP_PRICE))),
                    CONF_NIGHT_HOUR_START: int(self._temp.get(CONF_NIGHT_HOUR_START, DEFAULT_NIGHT_HOUR_START)),
                    CONF_NIGHT_HOUR_END: int(self._temp.get(CONF_NIGHT_HOUR_END, DEFAULT_NIGHT_HOUR_END)),
                    CONF_DAY_HOUR_END: int(user_input[CONF_DAY_HOUR_END]),
                    CONF_CHEAP_HOURS: int(user_input[CONF_CHEAP_HOURS]),
                    CONF_EXPENSIVE_HOURS: int(user_input[CONF_EXPENSIVE_HOURS]),
                    CONF_CHEAP_HOURS_NIGHT: int(user_input[CONF_CHEAP_HOURS_NIGHT]),
                    CONF_CHEAP_HOURS_DAY: int(user_input[CONF_CHEAP_HOURS_DAY]),
                    CONF_CHEAP_HOURS_EVENING: int(user_input[CONF_CHEAP_HOURS_EVENING]),
                    CONF_LEVEL_LANGUAGE: str(self._temp.get(CONF_LEVEL_LANGUAGE, DEFAULT_LEVEL_LANGUAGE)),
                }

                # proceed to validate and create entry

                # basic sanity checks
                if not data[CONF_NORDPOOL_ENTITY]:
                    errors["nordpool_entity"] = "empty"
                if not data[CONF_SENSOR_NAME]:
                    errors["sensor_name"] = "empty"

                night_end = data[CONF_NIGHT_HOUR_END]
                day_end = data[CONF_DAY_HOUR_END]
                if not (0 <= night_end <= 24 and 0 <= day_end <= 24):
                    errors["base"] = "hour_end_out_of_range"

                # require day end to be strictly greater than night end
                if not (day_end > night_end):
                    errors["day_hour_end"] = "must_be_greater_than_night"

                # cheap + expensive cannot exceed 24 combined
                cheap = data[CONF_CHEAP_HOURS]
                expensive = data[CONF_EXPENSIVE_HOURS]
                if cheap + expensive > 24:
                    errors["cheap_hours"] = "sum_exceeds_24"

                # each cheapest-period cannot exceed 8 hours
                if data[CONF_CHEAP_HOURS_NIGHT] > 8:
                    errors[CONF_CHEAP_HOURS_NIGHT] = "max_8"
                if data[CONF_CHEAP_HOURS_DAY] > 8:
                    errors[CONF_CHEAP_HOURS_DAY] = "max_8"
                if data[CONF_CHEAP_HOURS_EVENING] > 8:
                    errors[CONF_CHEAP_HOURS_EVENING] = "max_8"

                if errors:
                    defaults.update(user_input)
                    errors = await self._map_error_keys("config", "hours", errors)
                    return self.async_show_form(step_id="hours", data_schema=schema, errors=errors)

                # Use the sensor name as the config entry title to make multiple entries easy to identify
                entry_title = str(data.get(CONF_SENSOR_NAME) or DEFAULT_NAME).strip()
                
                return self.async_create_entry(title=entry_title, data=data)

            except Exception:
                errors["base"] = "invalid_input"
                defaults.update(user_input)

        errors = await self._map_error_keys("config", "hours", errors)
        return self.async_show_form(step_id="hours", data_schema=schema, errors=errors)

    async def _map_error_keys(self, domain_key: str, step_id: str, errors: dict[str, str]) -> dict[str, str]:
        """Map translation keys in `errors` to localized strings using HA translation helper.

        Falls back to English and preserves unknown keys.
        """
        try:
            lang = self.hass.config.language or None
        except Exception:
            lang = None

        

        try:
            # Language-aware fallback: try several candidates (full locale,
            # primary language) -> translations/en.json -> HA helper.
            from pathlib import Path
            import json

            translations_dir = Path(__file__).resolve().parent / "translations"
            translations = {}
            loaded_from = None

            # Build candidate language codes (preserve order)
            candidates = []
            if lang:
                candidates.append(lang)
                if "-" in lang:
                    candidates.append(lang.split("-", 1)[0])
                if "_" in lang:
                    candidates.append(lang.split("_", 1)[0])
            candidates.append("en")

            tried = []
            for cand in [] if candidates is None else candidates:
                if not cand:
                    continue
                cand = cand.lower()
                if cand in tried:
                    continue
                tried.append(cand)
                p = translations_dir / f"{cand}.json"
                if p.exists():
                    try:
                        def _read_json(path):
                            with path.open("r", encoding="utf-8") as fh:
                                return json.load(fh)

                        translations = await self.hass.async_add_executor_job(_read_json, p)
                        loaded_from = str(p)
                        break
                    except Exception:
                        # logging removed
                        pass

            # Final fallback to HA helper if nothing loaded
            if not translations:
                translations = await translation_helper.async_get_translations(self.hass, DOMAIN, lang)
                loaded_from = "ha_helper"
            
        except Exception:
            translations = {}

        step_obj = translations.get(domain_key, {}).get("step", {}).get(step_id, {})
        errs = step_obj.get("errors", {}) if isinstance(step_obj, dict) else {}

        out: dict[str, str] = {}
        for k, v in errors.items():
            if isinstance(v, str):
                out[k] = errs.get(v, v)
            else:
                out[k] = v
        
        return out

    # Errors are returned as translation keys for the frontend to resolve.
