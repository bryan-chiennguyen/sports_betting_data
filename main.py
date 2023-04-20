import csv
from collections import defaultdict
import pandas as pd

# Convert bet name to unify the way we group matching propositions
def convert_name(cur_name):
    ans = ''
    for ch in cur_name:
        if ch == '+':
            ans += 'Over '
        elif ch == '-':
            ans += 'Under '
        else:
            ans += ch
    return ans
    
# Check contain team name
def check_contain_team_name(cur_name):
    normalized_name = cur_name.lower()
    return 'philadelphia' in normalized_name or 'kansas city' in normalized_name

# Extract hedge line matching proposition group name from name of current line 
def extract_hedge_line(cur_name):
    if 'Over' in cur_name or 'Under' in cur_name:
        cur_idx = max(cur_name.find('Over'), cur_name.find('Under'))
        if cur_idx > 0:
            return cur_name[:cur_idx - 1]
        else:
            return ""
    return cur_name

team_names = ['Philadelphia Eagles', 'Kansas City Chiefs']

# Construct matching hedgelines like Philadelphia Eagles (Home Team) -10.5 vs Kansas City Chief (Away Team) +10.5
def get_matching_name(cur_name):
    new_name = cur_name
    if team_names[0] in cur_name:
        new_name = cur_name.replace(team_names[0], team_names[1])
    elif team_names[1] in cur_name:
        new_name = cur_name.replace(team_names[1], team_names[0])
    if "Over" in new_name:
        return new_name.replace('Over', 'Under')
    elif 'Under' in new_name:
        return new_name.replace('Under', 'Over')
    return new_name

# Helper function to generate first line, which is the property names of the output file
def generate_first_row(prefix, n):
    ans = []
    for i in range(n):
        ans.append(prefix + '_' + str(i + 1))
    return ans

with open('superbowl_all.csv', mode='r') as file:
    csv_file = csv.reader(file)

    # Store groups of matching hedge lines
    hedge_lines = defaultdict(lambda: defaultdict(lambda: []))

    i = 0
    max_num_sports_book = 0

    # Extract data from CSV file
    for line in csv_file:
        i += 1
        # Skip the first line
        if i == 1:
            continue

        # Extract bet values from the current row
        index, id, sports_book_name, name, price, checked_date, bet_points, is_main, is_live, market_name, home_rotation_number, away_rotation_number, deep_link_url, player_id, game_id, game_sport, game_league, game_start_date, game_home_team, game_away_team, game_is_live = line

        cur_hedge_line = market_name
        converted_name = convert_name(name)
        if len(bet_points) > 0:
            if team_names[0] in name or team_names[1] in name:
                matching_name = cur_hedge_line + " " + get_matching_name(converted_name)
                if matching_name in hedge_lines:
                    cur_hedge_line = matching_name
                else:
                    cur_hedge_line += " " + converted_name
            else:
                cur_hedge_line += " " + extract_hedge_line(converted_name) + " " + str(abs(float(bet_points)))

        # Check if current name is already in current matching group
        if not name in hedge_lines[cur_hedge_line]:
            # Add values to the current name in order of market_name, bet_points, is_main, is_live, home_rotation_number, away_rotation_number,
            # deep_link_url, player_id, game_id, game_sport, game_league, game_start_date, game_home_team, game_away_team, game_is_live
            hedge_lines[cur_hedge_line][name].append(market_name)
            hedge_lines[cur_hedge_line][name].append(bet_points)
            hedge_lines[cur_hedge_line][name].append(is_main)
            hedge_lines[cur_hedge_line][name].append(is_live)
            hedge_lines[cur_hedge_line][name].extend(line[10:])

            # Initialize list of sports_book
            sports_books = []
            hedge_lines[cur_hedge_line][name].append(sports_books)
        
        # Add current sport_book_name to list of sports_book
        hedge_lines[cur_hedge_line][name][-1].append((sports_book_name, price))

        # Get the max number of sports book to construct the number of sports books and hedge books in output file
        max_num_sports_book = max(max_num_sports_book, len(hedge_lines[cur_hedge_line][name][-1]))

    # Initliaze DataFrame to write output file
    df = pd.DataFrame()

    # Initialize first row with property names
    first_row = ['name', 'market_name', 'bet_points', 'is_main', 'is_live', 'home_rotation_number', 'away_rotation_number', 'deep_link_url', 'player_id', 'game_id', 'game_sport', 'game_league', 'game_start_date', 'game_home_team', 'game_away_team', 'game_is_live']
    first_row.extend(generate_first_row('sports_book_name', max_num_sports_book))
    first_row.extend(generate_first_row('odd', max_num_sports_book))
    first_row.extend(generate_first_row('hedge_book', max_num_sports_book))
    first_row.extend(generate_first_row('hedge_odd', max_num_sports_book))

    df = df.append(pd.DataFrame(first_row).transpose(), ignore_index=True)

    for group_name, matching_propositions in hedge_lines.items():
        # List of sports books in current matching proposition group
        sports_book_list = []
        for name in matching_propositions.keys():
            sports_book_list.append(list(matching_propositions[name][-1]))
        cur_idx = 0
        for name, properties in matching_propositions.items():
            # Add property values in current row
            cur_row = [name]
            cur_row.extend(properties[:-1])
            cur_sports_book_list = properties[-1]

            # Add sports_book_name values
            for i in range(max_num_sports_book):
                if i < len(cur_sports_book_list):
                    cur_row.append(cur_sports_book_list[i][0])
                else:
                    cur_row.append('NaN')

            # Add sports_book odd values
            for i in range(max_num_sports_book):
                if i < len(cur_sports_book_list):
                    cur_row.append(cur_sports_book_list[i][1])
                else:
                    cur_row.append('NaN')
            hedge_sports_book_list = []

            # Check if the current hedgeline has 2 matching propositions
            if len(matching_propositions) == 2:
                hedge_sports_book_list.extend(sports_book_list[1 - cur_idx])
            # Add hedge_book_name values
            for i in range(max_num_sports_book):
                if i < len(hedge_sports_book_list):
                    cur_row.append(hedge_sports_book_list[i][0])
                else:
                    cur_row.append('NaN')
            
            # Add hedge_odd values
            for i in range(max_num_sports_book):
                if i < len(hedge_sports_book_list):
                    cur_row.append(hedge_sports_book_list[i][1])
                else:
                    cur_row.append('NaN')
            
            df = df.append(pd.DataFrame(cur_row).transpose(), ignore_index=True)
            cur_idx += 1
    
    # Convert dataframe to CSV output file
    df.to_csv('output.csv', encoding='utf-8', index=False)
