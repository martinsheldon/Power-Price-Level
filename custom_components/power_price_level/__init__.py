from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback

# logging and trace file removed

from homeassistant import config_entries
from .options_flow import PowerPriceLevelOptionsFlowHandler


async def async_get_options_flow(config_entry):
    return PowerPriceLevelOptionsFlowHandler(config_entry)


from .const import DOMAIN, PLATFORMS


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Power Price Level from a config entry."""

    hass.data.setdefault(DOMAIN, {})
    # store a shallow copy of entry.data to avoid accidental mutation/race with entry updates
    hass.data[DOMAIN][entry.entry_id] = dict(entry.data) if entry.data is not None else {}

    # Ensure options updates reload the config entry so changes take effect
    async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
        try:
            # Schedule reload as a background task instead of awaiting here.
            # Awaiting inside an update listener can cause re-entrancy and freeze.
            hass.async_create_task(hass.config_entries.async_reload(entry.entry_id))
        except Exception:
            # logging removed
            pass

    # Re-enable automatic reload on entry update; listener schedules reload as a background task.
    # Disable automatic reload-on-update to avoid freezes observed in some environments.
    # If you want reload-on-update behavior, re-enable the next line.
    # entry.add_update_listener(_async_update_listener)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
