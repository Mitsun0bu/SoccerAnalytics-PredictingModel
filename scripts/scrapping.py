import  requests
import  time
import  pandas as pd
from    bs4 import BeautifulSoup

# Define the URL of the page to scrape
standings_url = "https://fbref.com/en/comps/12/La-Liga-Stats"

# Define a list of years to scrape data for
years = [2023, 2022, 2021]

# Create an empty list to store match data for all teams
all_matches = []

for year in years:
    
    # Make a GET request to the URL of the page containing the standings  
    data = requests.get(standings_url)

    # Parse the response with BeautifulSoup
    soup = BeautifulSoup(data.text, features="lxml")
    
    # Extract the table containing the standings
    standings_table = soup.select('table.stats_table')[0]
    
    # Extract the URLs for each team's page in absolute links format
    links     = [l.get("href") for l in standings_table.find_all('a')]
    links     = [l for l in links if '/squads/' in l]
    team_urls = [f"https://fbref.com{l}" for l in links]
    
    # Extract the previous season's URL for the next iteration
    previous_season = soup.select("a.prev")[0].get("href")
    standings_url   = f"https://fbref.com{previous_season}"

    # Loop through each team's page
    for team_url in team_urls:
        
        # Extract the team name from the URL
        team_name = team_url.split("/")[-1].replace("Stats", "").replace("-", " ")
        
        # Make a GET request to the URL of the page containing the shooting stats 
        data             = requests.get(team_url)
        
        # Parse the response with BeautifulSoup
        matches          = pd.read_html(data.text, match="Scores & Fixtures")[0]
        soup             = BeautifulSoup(data.text, features="lxml")
        links            = [l.get("href") for l in soup.find_all('a')]
        links            = [l for l in links if l and 'all_comps/shooting/' in l]
        data             = requests.get(f"https://fbref.com{links[0]}")
        shooting         = pd.read_html(data.text, match="Shooting")[0]
        shooting.columns = shooting.columns.droplevel()
        
        # If shooting stats are not available for a team, skip it
        try:
            team_data = matches.merge(shooting[["Date", "Sh", "SoT", "Dist", "FK", "PK", "PKatt"]], on="Date")
        except ValueError:
            continue
        
        # Filter out matches in competition other than La Liga
        team_data = team_data[team_data["Comp"] == "La Liga"]
        
        # Add the season and team name to the data
        team_data["Season"] = year
        team_data["Team"]   = team_name

        # Append team data data for a given year to the list of all data
        all_matches.append(team_data)

        # Wait for 5 seconds before making the next request
        time.sleep(5)

# Concatenate the match data for all teams, format the columns title and save it to a CSV file
match_df = pd.concat(all_matches)
match_df.columns = [c.lower() for c in match_df.columns]
match_df.to_csv("../data/matches.csv")