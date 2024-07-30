from ics import Calendar, Event
from datetime import datetime, timedelta
import requests
import json
import os

def create_event_with_unit(unit):
    # Create a new event
    e = Event()

    # Set the event's name
    e.name = f"{unit['disciplineName']}: {unit['eventUnitName']} - {unit['phaseName']}"

    # Set the event's start and end times
    e.begin = datetime.fromisoformat(unit['startDate'].replace('Z', '+00:00'))
    e.end = datetime.fromisoformat(unit['endDate'].replace('Z', '+00:00'))

    # Set the event's location
    e.location = f"{unit['venueDescription']}, {unit['locationDescription']}"

    # Set the event's description
    e.description = f"Status: {unit['statusDescription']}\n"
    for competitor in unit['competitors']:
        if 'noc' in competitor:
            e.description += f"{competitor['name']} ({competitor['noc']})\n"
        else:
            e.description += f"{competitor['name']}\n"

    return e

def create_ics(lang, start_date, end_date=None, nations=None, sports=None):
    # If no end date is provided, set it to the start date
    if end_date is None:
        end_date = start_date

    #Prepare filename
    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')
    filename = f'JO2024-{start_str}-to-{end_str}'

    if nations is not None:
        print('Nations')
        print(nations)
        filename+="_" + "-".join(nations)

    discipline_codes = []
    if sports is not None:
        # Load the sports codes from the JSON file
        with open(os.path.join(os.path.dirname(__file__), 'assets', 'sports-codes.json')) as f:
            sports_codes = json.load(f)

        # Find the discipline codes that correspond to the sports list
        for sport in sports:
            for code, name in sports_codes.items():
                if sport.lower() in name.lower():
                    discipline_codes.append(code)

        # Remove any duplicate discipline codes
        discipline_codes = list(set(discipline_codes))
        print("Sports codes found :")
        print(discipline_codes)
        filename+="_" + "-".join(sports)

    # Create a new calendar
    c = Calendar()

    # Iterate over each date in the range
    current_date = start_date
    while current_date <= end_date:
        # Format the date as a string
        date_str = current_date.strftime('%Y-%m-%d')

        # Construct the URL for the data
        url = f'https://sph-s-api.olympics.com/summer/schedules/api/{lang}/schedule/day/{date_str}'
        print(url)

        try:
            # Send a GET request to the URL
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers)
        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")

        # If the request was successful, process the data
        if response.status_code == 200:
            data = response.json()

            # Iterate over each unit in the data
            for unit in data['units']:
                # Check if the unit matches the filters
                if nations is None and sports is None:
                    print("NO FILTER : " + f"{unit['disciplineName']}: {unit['eventUnitName']} - {unit['phaseName']}")
                    c.events.add(create_event_with_unit(unit))
                    continue
                
                if nations is not None and any('noc' in competitor and competitor['noc'] in nations for competitor in unit['competitors']):
                    print("NATION : " + f"{unit['disciplineName']}: {unit['eventUnitName']} - {unit['phaseName']}")
                    c.events.add(create_event_with_unit(unit))
                    continue

                if discipline_codes and unit['disciplineCode'] in discipline_codes:
                    print("SPORT : " + f"{unit['disciplineName']}: {unit['eventUnitName']} - {unit['phaseName']}")
                    c.events.add(create_event_with_unit(unit))
                    continue

        # Move to the next date
        current_date += timedelta(days=1)

    # Write the calendar to a file
    output_folder = 'output'
    os.makedirs(output_folder, exist_ok=True)
    filepath = os.path.join(output_folder, f"{filename}.ics")
    with open(filepath, 'w') as ics_file:
        ics_file.writelines(c)

# Variables definition
lang = 'FRA'  # 'ENG' <-- If you want events in English (final ICS)
start_date = datetime(2024, 7, 30)
end_date = datetime(2024, 8, 10)  # Optional - if not set, will match the start date (entire day)
#nations = ['FRA']  # Optional
sports = ['Badminton', 'Climbing', 'BMX', 'Skate', 'Gym', 'Fencing', 'Basket', 'Canoe', 'DanceSport']  # Optional

# Main entry point
create_ics(lang=lang, start_date=start_date, end_date=end_date, nations=None, sports=sports)
