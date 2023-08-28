## SCRIPT TO SCRAPE DATA FROM CEV SITE

# import libraries
import pandas as pd
import numpy as np
from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import lxml

# create a session
driver = webdriver.Safari()

def scrape(id):
    # build the url used to load the page
    url_fix = 'https://www-old.cev.eu/Competition-Area/MatchStatistics.aspx?'
    url_var = 'ID=' + str(id)
    url = url_fix + url_var

    # load the page and wait to load
    driver.get(url)
    driver.implicitly_wait(5)

    # parse HTML and XML code and get tables using Beautiful Soup and lxml
    soup = BeautifulSoup(driver.page_source, 'lxml') 
    tables = soup.find_all('table')

    # read tables using Pandas read_html() which returns a list of dataframes
    df_list = pd.read_html(str(tables))

    # get only the tables we need from the list, #22 (team A stats) and #25 (team B stats)
    # also we remove some rows to keep only the player stats rows
    df_game_stats = pd.DataFrame()
    df_game_stats = pd.concat([df_game_stats, pd.concat([df_list[22].iloc[2:16, ], df_list[25].iloc[2:16, ]], axis=0)], axis=0)

    return df_game_stats

# take all games from group A, extract the player stats and add them to the dataframe
group_A_player_stats = pd.DataFrame()
for id in range(66391, 66406):
    group_A_player_stats = pd.concat([group_A_player_stats, scrape(id)], axis=0) 

# take all games from group B, extract the player stats and add them to the dataframe
group_B_player_stats = pd.DataFrame()
for id in range(66599, 66614):
    group_B_player_stats = pd.concat([group_B_player_stats, scrape(id)], axis=0)

# take all games from group C, extract the player stats and add them to the dataframe
group_C_player_stats = pd.DataFrame()
for id in range(66406, 66421):
    group_C_player_stats = pd.concat([group_C_player_stats, scrape(id)], axis=0)

# take all games from group D, extract the player stats and add them to the dataframe
group_D_player_stats = pd.DataFrame()
for id in range(66421, 66436):
    group_D_player_stats = pd.concat([group_D_player_stats, scrape(id)], axis=0)

# concatenate all groups data frames
player_stats = pd.DataFrame()
player_stats = pd.concat([player_stats, group_A_player_stats, group_B_player_stats, 
                          group_C_player_stats, group_D_player_stats], axis=0).reset_index(drop=True)

# we need to rename columns with proper names
columns_list = ["Number", "Name", "Vote", "Set1", "Set2", "Set3", "Set4", "Set5",
                "Points", "BP", "WL", "Serves", "ServeErrors", "Aces",
                "Receptions", "ReceptionErrors", "ReceptionPos%", "ReceptionExc%",
                "Attacks", "AttackErrors", "AttackBlocks", "AttackExc", "AttackEfficiency%", "Blocks"]

player_stats.columns = columns_list

# double space is needed between name and (L)
# player_stats[player_stats["Name"] == "TÓTH Fruzsina  (L)"]

# fix a bug caused by Croatia team that had only 13 players in the box score
player_stats = player_stats.loc[player_stats["Name"]!="Team Totals"]

# we need to transform and preprocess some data
# drop Vote and BP columns
player_stats = player_stats.drop(columns=["Vote", "BP"], axis=1)

# replace "*" with 0
for col in ["Set1", "Set2", "Set3", "Set4", "Set5"]:
    player_stats[col] = player_stats[col].str.replace('*', '1')

# replace "-" with 0
for col in ["Points", "WL", "Serves", "Receptions", "Attacks"]:
    player_stats[col] = player_stats[col].str.replace('-', '0')
    
# replace "." with 0
for col in ["ServeErrors", "Aces", "ReceptionErrors", "ReceptionPos%", "ReceptionExc%",
            "AttackErrors", "AttackBlocks", "AttackExc", "AttackEfficiency%", "Blocks"]:
    player_stats[col] = player_stats[col].str.replace('.', '0')
    
# remove "%" from required columns
for col in ["ReceptionPos%", "ReceptionExc%", "AttackEfficiency%"]:
    player_stats[col] = player_stats[col].str.replace('%', '')

# fill missing values with 0
player_stats = player_stats.fillna(0)          

# transform all object columns except "Name" in integers
for col in ["Set1", "Set2", "Set3", "Set4", "Set5",
                "Points", "WL", "Serves", "ServeErrors", "Aces",
                "Receptions", "ReceptionErrors", "ReceptionPos%", "ReceptionExc%",
                "Attacks", "AttackErrors", "AttackBlocks", "AttackExc", "AttackEfficiency%", "Blocks"]:
    player_stats[col] = pd.to_numeric(player_stats[col])

player_stats["Number"] = player_stats["Number"].astype(int)  

# change the positive values of Sets to 1 in order to count them
player_stats.loc[player_stats["Set1"] > 0, "Set1"] = 1
player_stats.loc[player_stats["Set2"] > 0, "Set2"] = 1
player_stats.loc[player_stats["Set3"] > 0, "Set3"] = 1
player_stats.loc[player_stats["Set4"] > 0, "Set4"] = 1
player_stats.loc[player_stats["Set5"] > 0, "Set5"] = 1

# count sets
player_stats["Sets"] = player_stats["Set1"]+player_stats["Set2"]+player_stats["Set3"]+player_stats["Set4"]+player_stats["Set5"]

# aggregate the data to get the final stats
player_stats_aggregate = pd.DataFrame()
player_stats_aggregate["Sets"] = player_stats.groupby("Name")["Sets"].sum()
player_stats_aggregate["Points"] = player_stats.groupby("Name")["Points"].sum()
player_stats_aggregate["WL"] = player_stats.groupby("Name")["WL"].sum()
player_stats_aggregate["Attacks"] = player_stats.groupby("Name")["Attacks"].sum()
player_stats_aggregate["AttackErrors"] = player_stats.groupby("Name")["AttackErrors"].sum()
player_stats_aggregate["AttackBlocks"] = player_stats.groupby("Name")["AttackBlocks"].sum()
player_stats_aggregate["AttacksExc"] = player_stats.groupby("Name")["AttackExc"].sum()
player_stats_aggregate["AttackEff%"] = player_stats_aggregate["AttacksExc"]/player_stats_aggregate["Attacks"]
player_stats_aggregate["Serves"] = player_stats.groupby("Name")["Serves"].sum()
player_stats_aggregate["ServeErrors"] = player_stats.groupby("Name")["ServeErrors"].sum()
player_stats_aggregate["Aces"] = player_stats.groupby("Name")["Aces"].sum()
player_stats_aggregate["Receptions"] = player_stats.groupby("Name")["Receptions"].sum()
player_stats_aggregate["ReceptionErrors"] = player_stats.groupby("Name")["ReceptionErrors"].sum()
player_stats_aggregate["ReceptionPos%"] = player_stats.groupby("Name")["ReceptionPos%"].mean()
player_stats_aggregate["ReceptionExc%"] = player_stats.groupby("Name")["ReceptionExc%"].mean()
player_stats_aggregate["Blocks"] = player_stats.groupby("Name")["Blocks"].sum()
player_stats_aggregate["PointsPerSet"] = player_stats_aggregate["Points"]/player_stats_aggregate["Sets"]
player_stats_aggregate["AcesPerSet"] = player_stats_aggregate["Aces"]/player_stats_aggregate["Sets"]
player_stats_aggregate["BlocksPerSet"] = player_stats_aggregate["Blocks"]/player_stats_aggregate["Sets"]
player_stats_aggregate = player_stats_aggregate.reset_index()

# fill missing values
player_stats_aggregate = player_stats_aggregate.fillna(0)

# adjust decimals
player_stats_aggregate["AttackEff%"] = player_stats_aggregate["AttackEff%"].round(2)
player_stats_aggregate["ReceptionPos%"] = player_stats_aggregate["ReceptionPos%"].round(2)
player_stats_aggregate["ReceptionExc%"] = player_stats_aggregate["ReceptionExc%"].round(2)

# save data to csv file
#player_stats_aggregate.to_csv("player_stats_aggregate.csv", index=False)