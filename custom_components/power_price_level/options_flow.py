from __future__ import annotations

import asyncio
from datetime import datetime
from homeassistant.helpers import entity_registry as er
from homeassistant.util import slugify

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import translation as translation_helper
from homeassistant.helpers import selector

from .const import (
    CONF_GRID_DAY,
    CONF_GRID_NIGHT,
    CONF_ADDITIONAL,
    CONF_CHEAP_PRICE,
    CONF_NORDPOOL_ENTITY,
    CONF_POWERPRICE_ENTITY,
    DEFAULT_NORDPOOL_ENTITY,
    DEFAULT_POWERPRICE_ENTITY,
    CONF_NIGHT_HOUR_END,
    CONF_NIGHT_HOUR_START,
    CONF_DAY_HOUR_END,
    CONF_CHEAP_HOURS,
    CONF_GRID_NIGHT_START,
    CONF_GRID_NIGHT_END,
    CONF_EXPENSIVE_HOURS,
    CONF_CHEAP_HOURS_NIGHT,
    CONF_CHEAP_HOURS_DAY,
    CONF_CHEAP_HOURS_EVENING,
    CONF_SENSOR_NAME,
    DEFAULT_NAME,
    DEFAULT_NIGHT_HOUR_END,
    CONF_CURRENCY,
    DEFAULT_CURRENCY,
    CURRENCY_SUBUNIT_MAP,
    CONF_LEVEL_LANGUAGE,
    DEFAULT_LEVEL_LANGUAGE,
    DEFAULT_NIGHT_HOUR_START,
    DEFAULT_GRID_NIGHT_START,
    DEFAULT_GRID_NIGHT_END,
    LANGUAGE_DISPLAY_MAP,
    DOMAIN,
)
from .util import parse_unit


def _unit_to_str(v: float) -> str:
    # format for UI: 4 decimals, comma decimal separator; normalize legacy subunit values
    if v is None:
        v = 0.0
    # Values are stored and displayed in major currency units (e.g. NOK/kWh)
    return f"{v:.4f}".replace(".", ",")
 
class PowerPriceLevelOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._entry = config_entry

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

    def _find_powerprice_entity(self) -> str | None:
        try:
            for st in self.hass.states.async_all():
                eid = (st.entity_id or "").lower()
                name = str(st.attributes.get("friendly_name", "") or "").lower()
                if "power_price" in eid or "power price" in name or "powerprice" in eid:
                    return st.entity_id
        except Exception:
            pass
        return None

    # tracing/logging has been removed

    async def _delayed_reload(self) -> None:
        try:
            await asyncio.sleep(1)
            await self.hass.config_entries.async_reload(self._entry.entry_id)
        except Exception:
            # logging removed
            pass

    async def _delayed_update_title(self, new_title: str) -> None:
        try:
            await asyncio.sleep(0.5)
            try:
                self.hass.config_entries.async_update_entry(self._entry, title=new_title)
            except Exception:
                # logging removed
                pass
        except Exception:
            # logging removed
            pass

        # Also update entity registry ids to match the new sensor name (power price and level)
        try:
            base = slugify(new_title)
            ent_reg = er.async_get(self.hass)

            # Power price sensor
            uid_price = f"{self._entry.entry_id}_power_price"
            entity_price_id = ent_reg.async_get_entity_id("sensor", DOMAIN, uid_price)
            if entity_price_id:
                new_price_id = f"sensor.{base}"
                try:
                    ent_reg.async_update_entity(entity_price_id, new_entity_id=new_price_id)
                except Exception:
                    # logging removed
                    pass

            # Power price level sensor
            uid_level = f"{self._entry.entry_id}_power_price_level"
            entity_level_id = ent_reg.async_get_entity_id("sensor", DOMAIN, uid_level)
            if entity_level_id:
                new_level_id = f"sensor.{base}_level"
                try:
                    ent_reg.async_update_entity(entity_level_id, new_entity_id=new_level_id)
                except Exception:
                    # logging removed
                    pass
        except Exception:
            # logging removed
            pass

    async def async_step_init(self, user_input=None):
        """Basic options: sensor name and core prices."""
        errors: dict[str, str] = {}

        current = self._entry.options or {}

        # Determine nordpool default: prefer current/entry value, else auto-detect
        nord_default = current.get(CONF_NORDPOOL_ENTITY, self._entry.data.get(CONF_NORDPOOL_ENTITY, None))
        if not nord_default:
            try:
                nord_default = self._find_nordpool_entity()
            except Exception:
                nord_default = None

        # Determine powerprice default: prefer current/entry value, else auto-detect
        power_default = current.get(CONF_POWERPRICE_ENTITY, self._entry.data.get(CONF_POWERPRICE_ENTITY, None))
        if not power_default:
            try:
                power_default = self._find_powerprice_entity()
            except Exception:
                power_default = None
        defaults = {
            CONF_NORDPOOL_ENTITY: str(nord_default or DEFAULT_NORDPOOL_ENTITY),
            CONF_POWERPRICE_ENTITY: str(power_default or DEFAULT_POWERPRICE_ENTITY),
            CONF_SENSOR_NAME: str(current.get(CONF_SENSOR_NAME, self._entry.data.get(CONF_SENSOR_NAME, DEFAULT_NAME))),
            CONF_CURRENCY: str(current.get(CONF_CURRENCY, self._entry.data.get(CONF_CURRENCY, DEFAULT_CURRENCY))),
            CONF_LEVEL_LANGUAGE: str(current.get(CONF_LEVEL_LANGUAGE, self._entry.data.get(CONF_LEVEL_LANGUAGE, DEFAULT_LEVEL_LANGUAGE))),
            CONF_GRID_DAY: _unit_to_str(float(current.get(CONF_GRID_DAY, self._entry.data.get(CONF_GRID_DAY, 0.0)))),
            CONF_GRID_NIGHT: _unit_to_str(float(current.get(CONF_GRID_NIGHT, self._entry.data.get(CONF_GRID_NIGHT, 0.0)))),
            CONF_ADDITIONAL: _unit_to_str(float(current.get(CONF_ADDITIONAL, self._entry.data.get(CONF_ADDITIONAL, 0.0)))),
            CONF_CHEAP_PRICE: _unit_to_str(float(current.get(CONF_CHEAP_PRICE, self._entry.data.get(CONF_CHEAP_PRICE, 0.0)))),
        }

        if user_input is not None:
                try:
                    nord = str(user_input[CONF_NORDPOOL_ENTITY]).strip()
                    power = str(user_input[CONF_POWERPRICE_ENTITY]).strip()
                    name = str(user_input[CONF_SENSOR_NAME]).strip()
                    currency = str(user_input[CONF_CURRENCY]).strip()
                    # selected value is a display name (e.g. "Norsk"); map to code
                    level_lang_sel = user_input.get(CONF_LEVEL_LANGUAGE, DEFAULT_LEVEL_LANGUAGE)
                    level_lang = LANGUAGE_DISPLAY_MAP.get(level_lang_sel, level_lang_sel).strip()
                    if not nord:
                        raise ValueError("nordpool entity empty")
                    if not name:
                        raise ValueError("sensor name empty")

                    self._temp = {CONF_NORDPOOL_ENTITY: nord, CONF_POWERPRICE_ENTITY: power, CONF_SENSOR_NAME: name, CONF_CURRENCY: currency, CONF_LEVEL_LANGUAGE: level_lang}
                    return await self.async_step_costs()
                except Exception:
                    errors["base"] = "invalid_input"

        schema = vol.Schema(
            {
                vol.Required(CONF_SENSOR_NAME, default=defaults[CONF_SENSOR_NAME]): str,
                vol.Required(CONF_NORDPOOL_ENTITY, default=defaults[CONF_NORDPOOL_ENTITY]): selector.EntitySelector({"domain": "sensor"}),
                vol.Required(CONF_POWERPRICE_ENTITY, default=defaults[CONF_POWERPRICE_ENTITY]): selector.EntitySelector({"domain": "sensor"}),
                vol.Required(
                    CONF_LEVEL_LANGUAGE,
                    default=(
                        next((k for k, v in LANGUAGE_DISPLAY_MAP.items() if v == defaults[CONF_LEVEL_LANGUAGE]),
                             defaults[CONF_LEVEL_LANGUAGE])
                    ),
                ): vol.In(list(LANGUAGE_DISPLAY_MAP.keys())),
                # use a safe currency default when stored value is not supported (legacy values like GBP)
                vol.Required(
                    CONF_CURRENCY,
                    default=(defaults[CONF_CURRENCY] if defaults.get(CONF_CURRENCY) in ["NOK", "SEK", "DKK", "EUR"] else DEFAULT_CURRENCY),
                ): vol.In(["NOK", "SEK", "DKK", "EUR"]),
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema, errors=errors)


    async def async_step_costs(self, user_input=None):
        """Costs options: grid/additional and cheap threshold."""
        errors: dict[str, str] = {}

        current = self._entry.options or {}

        defaults = {
            CONF_GRID_DAY: _unit_to_str(float(current.get(CONF_GRID_DAY, self._entry.data.get(CONF_GRID_DAY, 0.0)))),
            CONF_GRID_NIGHT: _unit_to_str(float(current.get(CONF_GRID_NIGHT, self._entry.data.get(CONF_GRID_NIGHT, 0.0)))),
            CONF_ADDITIONAL: _unit_to_str(float(current.get(CONF_ADDITIONAL, self._entry.data.get(CONF_ADDITIONAL, 0.0)))),
            CONF_CHEAP_PRICE: _unit_to_str(float(current.get(CONF_CHEAP_PRICE, self._entry.data.get(CONF_CHEAP_PRICE, 0.0)))),
            CONF_NIGHT_HOUR_START: int(current.get(CONF_NIGHT_HOUR_START, self._entry.data.get(CONF_NIGHT_HOUR_START, DEFAULT_NIGHT_HOUR_START))),
            CONF_NIGHT_HOUR_END: int(current.get(CONF_NIGHT_HOUR_END, self._entry.data.get(CONF_NIGHT_HOUR_END, DEFAULT_NIGHT_HOUR_END))),
            CONF_GRID_NIGHT_START: int(current.get(CONF_GRID_NIGHT_START, self._entry.data.get(CONF_GRID_NIGHT_START, DEFAULT_GRID_NIGHT_START))),
            CONF_GRID_NIGHT_END: int(current.get(CONF_GRID_NIGHT_END, self._entry.data.get(CONF_GRID_NIGHT_END, DEFAULT_GRID_NIGHT_END))),
        }

        # If we have temp from prior step, prefer that for ore fields
        if hasattr(self, "_temp") and self._temp:
            # merge any cost defaults from temp if present
            for k in [CONF_GRID_DAY, CONF_GRID_NIGHT, CONF_ADDITIONAL, CONF_CHEAP_PRICE]:
                if k in self._temp:
                    defaults[k] = f"{float(self._temp[k]):.4f}".replace(".", ",")

        # determine unit suffix for the ore fields based on selected currency
        currency = str((self._temp.get(CONF_CURRENCY) if hasattr(self, "_temp") and self._temp else current.get(CONF_CURRENCY, DEFAULT_CURRENCY)))
        unit_suffix = CURRENCY_SUBUNIT_MAP.get(currency, "subunit/kWh")

        if user_input is not None:
            try:
                # store costs in temp and continue (parse as main currency unit)
                self._temp.update(
                    {
                        CONF_GRID_DAY: parse_unit(user_input[CONF_GRID_DAY]),
                        CONF_GRID_NIGHT: parse_unit(user_input[CONF_GRID_NIGHT]),
                        CONF_GRID_NIGHT_START: int(user_input.get(CONF_GRID_NIGHT_START, defaults[CONF_GRID_NIGHT_START])),
                        CONF_GRID_NIGHT_END: int(user_input.get(CONF_GRID_NIGHT_END, defaults[CONF_GRID_NIGHT_END])),
                        CONF_ADDITIONAL: parse_unit(user_input[CONF_ADDITIONAL]),
                        CONF_CHEAP_PRICE: parse_unit(user_input[CONF_CHEAP_PRICE]),
                        CONF_NIGHT_HOUR_START: int(user_input.get(CONF_NIGHT_HOUR_START, defaults[CONF_NIGHT_HOUR_START])),
                        CONF_NIGHT_HOUR_END: int(user_input.get(CONF_NIGHT_HOUR_END, defaults[CONF_NIGHT_HOUR_END])),
                    }
                )
                return await self.async_step_more()

            except Exception:
                errors["base"] = "invalid_input"

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


    async def async_step_more(self, user_input=None):
        """Hours options: hours and counts."""
        errors: dict[str, str] = {}
        
        # tracing removed

        current = self._entry.options or {}
        defaults = {
            CONF_NIGHT_HOUR_END: int(current.get(CONF_NIGHT_HOUR_END, self._entry.data.get(CONF_NIGHT_HOUR_END, 6))),
            CONF_DAY_HOUR_END: int(current.get(CONF_DAY_HOUR_END, self._entry.data.get(CONF_DAY_HOUR_END, 15))),
            CONF_CHEAP_HOURS: int(current.get(CONF_CHEAP_HOURS, self._entry.data.get(CONF_CHEAP_HOURS, 5))),
            CONF_EXPENSIVE_HOURS: int(current.get(CONF_EXPENSIVE_HOURS, self._entry.data.get(CONF_EXPENSIVE_HOURS, 5))),
            CONF_CHEAP_HOURS_NIGHT: int(current.get(CONF_CHEAP_HOURS_NIGHT, self._entry.data.get(CONF_CHEAP_HOURS_NIGHT, 2))),
            CONF_CHEAP_HOURS_DAY: int(current.get(CONF_CHEAP_HOURS_DAY, self._entry.data.get(CONF_CHEAP_HOURS_DAY, 2))),
            CONF_CHEAP_HOURS_EVENING: int(current.get(CONF_CHEAP_HOURS_EVENING, self._entry.data.get(CONF_CHEAP_HOURS_EVENING, 2))),
        }

        # If we have temp from prior steps, prefer that for hours/other fields
        if hasattr(self, "_temp") and self._temp:
            # Merge temp values into defaults so the form reflects recent changes
            for k, v in self._temp.items():
                if k in defaults:
                    try:
                        defaults[k] = int(v)
                    except Exception:
                        # ignore non-int temp values
                        pass

        # schema must be defined after defaults are finalized
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

        if hasattr(self, "_temp") and self._temp:
            temp = self._temp
        else:
            temp = current

        if user_input is not None:
            try:
                options = {
                    CONF_NORDPOOL_ENTITY: str(temp.get(CONF_NORDPOOL_ENTITY, self._entry.data.get(CONF_NORDPOOL_ENTITY, DEFAULT_NORDPOOL_ENTITY))).strip(),
                    CONF_POWERPRICE_ENTITY: str(temp.get(CONF_POWERPRICE_ENTITY, self._entry.data.get(CONF_POWERPRICE_ENTITY, DEFAULT_POWERPRICE_ENTITY))).strip(),
                    CONF_SENSOR_NAME: str(temp.get(CONF_SENSOR_NAME, self._entry.data.get(CONF_SENSOR_NAME, DEFAULT_NAME))).strip(),
                    CONF_CURRENCY: str(temp.get(CONF_CURRENCY, self._entry.data.get(CONF_CURRENCY, DEFAULT_CURRENCY))),
                    CONF_LEVEL_LANGUAGE: str(temp.get(CONF_LEVEL_LANGUAGE, self._entry.data.get(CONF_LEVEL_LANGUAGE, DEFAULT_LEVEL_LANGUAGE))),
                    CONF_GRID_DAY: parse_unit(str(temp.get(CONF_GRID_DAY, self._entry.data.get(CONF_GRID_DAY, 0.0)))),
                    CONF_GRID_NIGHT: parse_unit(str(temp.get(CONF_GRID_NIGHT, self._entry.data.get(CONF_GRID_NIGHT, 0.0)))),
                    CONF_GRID_NIGHT_START: int(temp.get(CONF_GRID_NIGHT_START, self._entry.data.get(CONF_GRID_NIGHT_START, DEFAULT_GRID_NIGHT_START))),
                    CONF_GRID_NIGHT_END: int(temp.get(CONF_GRID_NIGHT_END, self._entry.data.get(CONF_GRID_NIGHT_END, DEFAULT_GRID_NIGHT_END))),
                    CONF_ADDITIONAL: parse_unit(str(temp.get(CONF_ADDITIONAL, self._entry.data.get(CONF_ADDITIONAL, 0.0)))),
                    CONF_CHEAP_PRICE: parse_unit(str(temp.get(CONF_CHEAP_PRICE, self._entry.data.get(CONF_CHEAP_PRICE, 0.0)))),
                    CONF_NIGHT_HOUR_START: int(user_input.get(CONF_NIGHT_HOUR_START, temp.get(CONF_NIGHT_HOUR_START, self._entry.data.get(CONF_NIGHT_HOUR_START, DEFAULT_NIGHT_HOUR_START)))),
                    CONF_NIGHT_HOUR_END: int(user_input.get(CONF_NIGHT_HOUR_END, temp.get(CONF_NIGHT_HOUR_END, self._entry.data.get(CONF_NIGHT_HOUR_END, DEFAULT_NIGHT_HOUR_END)))),
                    CONF_DAY_HOUR_END: int(user_input[CONF_DAY_HOUR_END]),
                    CONF_CHEAP_HOURS: int(user_input[CONF_CHEAP_HOURS]),
                    CONF_EXPENSIVE_HOURS: int(user_input[CONF_EXPENSIVE_HOURS]),
                    CONF_CHEAP_HOURS_NIGHT: int(user_input[CONF_CHEAP_HOURS_NIGHT]),
                    CONF_CHEAP_HOURS_DAY: int(user_input[CONF_CHEAP_HOURS_DAY]),
                    CONF_CHEAP_HOURS_EVENING: int(user_input[CONF_CHEAP_HOURS_EVENING]),
                }

                # proceed to validate and save options

                # validation (provide human-readable messages via translation keys)
                if not options[CONF_NORDPOOL_ENTITY]:
                    errors["nordpool_entity"] = "empty"
                if not options.get(CONF_POWERPRICE_ENTITY):
                    errors["powerprice_entity"] = "empty"
                if not options[CONF_SENSOR_NAME]:
                    errors["sensor_name"] = "empty"

                night_end = options[CONF_NIGHT_HOUR_END]
                day_end = options[CONF_DAY_HOUR_END]
                if not (0 <= night_end <= 24 and 0 <= day_end <= 24):
                    errors["base"] = "hour_range"

                # require day end to be strictly greater than night end
                if not (day_end > night_end):
                    errors["day_hour_end"] = "must_be_greater_than_night"

                # cheap + expensive cannot exceed 24 combined
                if options[CONF_CHEAP_HOURS] + options[CONF_EXPENSIVE_HOURS] > 24:
                    errors["cheap_hours"] = "sum_exceeds_24"

                # each cheapest-period cannot exceed 8 hours
                if options[CONF_CHEAP_HOURS_NIGHT] > 8:
                    errors[CONF_CHEAP_HOURS_NIGHT] = "max_8"
                if options[CONF_CHEAP_HOURS_DAY] > 8:
                    errors[CONF_CHEAP_HOURS_DAY] = "max_8"
                if options[CONF_CHEAP_HOURS_EVENING] > 8:
                    errors[CONF_CHEAP_HOURS_EVENING] = "max_8"

                if errors:
                    errors = await self._map_error_keys("options", "more", errors)
                    return self.async_show_form(step_id="more", data_schema=schema, errors=errors)

                # Save options as the entry's options (create_entry from OptionsFlow stores options)
                try:
                    # Schedule a background reload after saving options to apply changes immediately
                    new_title = str(options.get(CONF_SENSOR_NAME) or DEFAULT_NAME).strip()
                    self.hass.async_create_task(self._delayed_update_title(new_title))
                    self.hass.async_create_task(self._delayed_reload())

                    result = self.async_create_entry(title="", data=options)
                    return result
                except Exception:
                    errors["base"] = "cannot_save"
                    errors = await self._map_error_keys("options", "more", errors)
                    return self.async_show_form(step_id="more", data_schema=schema, errors=errors)

            except Exception:
                errors["base"] = "invalid_input"

        errors = await self._map_error_keys("options", "more", errors)
        return self.async_show_form(step_id="more", data_schema=schema, errors=errors)

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
