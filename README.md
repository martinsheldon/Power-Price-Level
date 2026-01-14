# Power Price Level custom integration for Home Assistant
Home Assistant Power Price Level sensor using Nordpool price data


# What is Power Price Level?
Power Price Level is a custom integration in Home Assistant that creates two configurable sensors presenting the current Power Price and relative Power Price Level for the current and next day based on data from Nordpool and user input.
The Power Price Level sensor can be configured and tuned to fit the need of your home.

Its a simple sensor calculating the cheapest and most expensive hour each day and cheapest hours within defined periods (Up to three periods) of the day.
The sensor is designed to assist the user moving the highest power consumption like Hot Water heating to the cheapest hours of the day to reduce the electricity bill.

## Installation

### HACS

- Go to `HACS` -> `Integrations`,
- Select `+`,
- Search for `Power Price Level` and install it,
- Restart Home Assistant

 ##  Configure sensors:

- Go to `Settings` -> `Devices & Services`
- Select `+ Add Integration`
- Search for `Power Price Level` and select it
- Fill in the required values and press `Submit`
  

  
| Configuration                  | Required | Value |  Description                   |
|--------------------------------| -------- | -------| ----------------------------- |
| Sensor base name               | **yes**  | string | Name of the senors |
| Nordpool sensor entity         | **yes**  | entity id | Nordpool entity used to get price data |
| Language                       | **yes**  | string | Language of the Power Price Level sensor state |
| Currency                       | **yes**  | string | Currency of the Power Price Level sensor state  |
| Grid day price                 | **yes**  | float | Grid price for day hours |
| Grid night price               | **yes**  | float | Grid price for night hours |
| Additional price               | **yes**  | float | Additional price for all hours |
| Cheap price threshold          | **yes**  | float | All hourly prices below this thershold will result in Power Price Level sensor state "Cheap"|
| Grid night starts at (hour)    | **yes**  | int (0-23) | Grid night starts at this hour |
| Grid night ends at (hour)      | **yes**  | int (0-23) | Grid night ends at this hour |
| Night ends at (hour)           | **yes**  | int (0-23) | Night ends/day starts at this hour (Must be lower value than Day ends at (hour))  |
| Day ends at (hour)             | **yes**  | int (0-23) | Day ends/evening starts at this hour (Must be higher value than Grid night ends at (hour)) |
| Number of cheapest hours       | **yes**  | int (0-12) | Number of cheapest hours for a day (+ one Cheapest hour) |
| Number of most expensive hours | **yes**  | int (0-12) | Number of most expensive hours for a day (+ one Most expensive hour) |
| Cheapest hours during night    | **yes**  | int (0-8) | Minumum number of all variants of cheap hours during night |
| Cheapest hours during day      | **yes**  | int (0-8) | Minumum number of all variants of cheap hours during day |
| Cheapest hours during evening  | **yes**  | int (0-8) | Minumum number of all variants of cheap hours during evening |
