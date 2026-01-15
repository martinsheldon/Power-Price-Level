# Power Price Level custom integration for Home Assistant
Home Assistant Power Price Level sensor using Nordpool price data


## What is Power Price Level?
Power Price Level is a custom integration in Home Assistant that creates two configurable sensors presenting the current Power Price and relative Power Price Level for the current and next day based on data from Nordpool and user input.
The Power Price Level sensor can be configured and tuned to fit the need of your home.

Its a simple sensor calculating the cheapest and most expensive hour each day and cheapest hours within defined periods (Up to three periods) of the day.
The sensor is designed to assist the user moving the highest power consumption like Hot Water heating to the cheapest hours of the day to reduce the electricity bill.

<img width="579" height="417" alt="image" src="https://github.com/user-attachments/assets/89ec2b06-808e-4dee-881f-3839824a5bea" />

### Table of Contents
**[Installation](#installation)**<br>
**[Setup](#setup)**<br>
**[How the sensors works](#how-the-sensors-works)**<br>
**[Power Price visual presentation](#power-price-visual-presentation)**<br>



## Installation

### HACS

- Go to `HACS` -> `Integrations`,
- Select `+`,
- Search for `Power Price Level` and install it,
- Restart Home Assistant

## Setup
###  Configure sensors:

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
| Cheap price threshold          | **yes**  | float | All hourly prices below this threshold will result in Power Price Level sensor state "Cheap"|
| Grid night starts at (hour)    | **yes**  | int (0-23) | Grid night starts at this hour |
| Grid night ends at (hour)      | **yes**  | int (0-23) | Grid night ends at this hour |
| Night ends at (hour)           | **yes**  | int (0-23) | Night period ends/day period starts at this hour (Must be lower value than Day ends at (hour))  |
| Day ends at (hour)             | **yes**  | int (0-23) | Day period ends/evening period starts at this hour (Must be higher value than Grid night ends at (hour)) |
| Number of cheapest hours       | **yes**  | int (0-12) | Number of cheapest hours for a day (+ one Cheapest hour) |
| Number of most expensive hours | **yes**  | int (0-12) | Number of most expensive hours for a day (+ one Most expensive hour) |
| Cheapest hours during night    | **yes**  | int (0-8) | Minumum number of all variants of cheap hours during night |
| Cheapest hours during day      | **yes**  | int (0-8) | Minumum number of all variants of cheap hours during day |
| Cheapest hours during evening  | **yes**  | int (0-8) | Minumum number of all variants of cheap hours during evening |



## How the sensors works
###  Power Price:

The Power Price sensor calculates and stores the actual hourly prices as attributes, based on the Nordpool price, the day or night grid price, and the fixed additional price. 
Its state always reflects the price for the current hour.

All hourly values are provided both as lists and as raw values within the sensor attributes. 
When Nordpool makes prices for the next day available, the sensor automatically calculates and stores the corresponding hourly prices.

###  Power Price Level:

The Power Price Level sensor uses data from the Power Price sensor together with user‑defined settings to calculate and store the relative price levels for each day. These values are stored as lists.
Its state always reflects the price level for the current hour. When Nordpool provides prices for the next day, the sensor immediately calculates the corresponding price levels as well.

This sensor is designed to ensure that a minimum number of cheap-price hours occur within a day. All calculations are based solely on the prices for the current day (current day or the next day, once available). Prices from other days are not considered. As a result, an hour marked as “Cheapest” on one day may still be more expensive than an hour marked as “Most expensive” on another day.

#### Available price levels are:
| Value                  | Description |
|------------------------| ----------- | 
| Cheap                  | If the power price is below the Cheap price thershold |
| Cheapest hour          | Cheapest hour of the day |
| Cheapest hours         | X number Cheapest hours of the day |
| Cheap hour             | X number Cheapest hours of a period |
| Normal                 | None cheap or most expensive hour and below day's average |
| Expensive              | None cheap or most expensive hour and above day's average |
| Most Expensive hours   | X number Most Expensive hours of the day  |
| Most Expensive hour    | Most Expensive hour of the day |

#### Currency supported:
| Currency               | Description |
|------------------------| ----------- | 
| NOK                    | Norvergian Krone |
| SEK                    | Swedish Krone |
| DKK                    | Danish Krone |
| EURO                   | Euro |

#### Languages supported:
| Language               
|------------------------|
| English |                    
| Danish | 
| German | 
| Estonian | 
| Latvian | 
| Lithuanian | 
| Dutch | 
| Norwegian | 
| Polish | 
| Finnish | 
| Swedish | 

### Examples:
#### Power Price
<img width="727" height="705" alt="image" src="https://github.com/user-attachments/assets/5c5642f4-1adf-4ead-ae47-a8c460f82afa" />

#### Power Price Level
<img width="713" height="800" alt="image" src="https://github.com/user-attachments/assets/b33b03fd-9d0f-41ae-a1a9-7635c1c75998" />

## Power Price visual presentation
[ApexCharts](https://github.com/RomRider/apexcharts-card) card is recommended for visualization of the price and price level data in Home Assistant.<br> 

#### Prices for today:
<img width="579" height="417" alt="image" src="https://github.com/user-attachments/assets/89ec2b06-808e-4dee-881f-3839824a5bea" />

#### Prices for two days:
