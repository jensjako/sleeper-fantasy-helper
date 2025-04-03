# sleeper_utils.py
import json
import requests
import os
import time

def list_free_agents(user_id, username, top_n=15):
    state = requests.get("https://api.sleeper.app/v1/state/nfl").json()
    week = state.get("week", 1)

    season = "2024"
    leagues_url = f"https://api.sleeper.app/v1/user/{user_id}/leagues/nfl/{season}"
    leagues = requests.get(leagues_url).json()

    if not leagues:
        print(f"No leagues found for '{username}' in {season}.")
        return

    print("\nLeagues found:")
    for idx, league in enumerate(leagues):
        print(f"{idx + 1}. {league['name']} (ID: {league['league_id']})")

    try:
        choice = int(input("\nSelect a league number to view free agents: "))
        if choice < 1 or choice > len(leagues):
            raise ValueError
    except ValueError:
        print("Invalid selection.")
        return

    selected_league = leagues[choice - 1]
    league_id = selected_league["league_id"]

    rosters = requests.get(f"https://api.sleeper.app/v1/league/{league_id}/rosters").json()
    owned_player_ids = set()
    for roster in rosters:
        owned_player_ids.update(roster.get("players", []))

    players_data = get_cached_players()
    projections = requests.get(f"https://api.sleeper.app/v1/projections/nfl/regular/{week}").json()

    free_agents = []
    for pid, player in players_data.items():
        if pid not in owned_player_ids:
            proj_pts = projections.get(pid, {}).get("pts", 0.0)
            if proj_pts > 0:
                free_agents.append({
                    "name": player.get("full_name", pid),
                    "position": player.get("position", ""),
                    "team": player.get("team", "FA"),
                    "points": proj_pts
                })

    free_agents.sort(key=lambda x: x["points"], reverse=True)

    print(f"\nTop {top_n} Free Agents in '{selected_league['name']}' (Week {week}):\n")
    for fa in free_agents[:top_n]:
        print(f" - {fa['name']} ({fa['position']}, {fa['team']}) — {fa['points']:.2f} pts")


def get_cached_players(file_path="players_cache.json", max_age_hours=24):
    if os.path.exists(file_path):
        last_modified = os.path.getmtime(file_path)
        age_hours = (time.time() - last_modified) / 3600
        if age_hours < max_age_hours:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            print("Player cache is older than 24 hours. Refreshing...")

    print("Fetching player data from Sleeper...")
    players = requests.get("https://api.sleeper.app/v1/players/nfl").json()
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(players, f)
    return players


def display_user_roster(roster, players_data, league_name, projections, week):
    all_players = roster.get("players", [])
    starters = roster.get("starters", [])
    bench = [pid for pid in all_players if pid not in starters]

    def get_info(pid):
        player = players_data.get(pid, {})
        name = player.get("full_name", pid)
        pts = projections.get(pid, {}).get("pts", 0.0)
        return f"{name} - {pts:.2f} pts"

    starter_lines = [get_info(pid) for pid in starters]
    bench_lines = [get_info(pid) for pid in bench]

    print(f"\nYour Roster in '{league_name}' (Week {week} Projections):\n")

    print("Starters:")
    for line in starter_lines:
        print(f" - {line}")

    print("\nBench:")
    for line in bench_lines:
        print(f" - {line}")

def handle_display_leagues(user_id, username):
    season = "2024"
    leagues_url = f"https://api.sleeper.app/v1/user/{user_id}/leagues/nfl/{season}"
    leagues = requests.get(leagues_url).json()

    if not leagues:
        print(f"No leagues found for the user '{username}' in the {season} season.")
        return

    print("\nLeagues found:")
    for idx, league in enumerate(leagues):
        print(f"{idx + 1}. {league['name']} (ID: {league['league_id']})")

    try:
        choice = int(input("\nSelect a league number to view your roster: "))
        if choice < 1 or choice > len(leagues):
            raise ValueError
    except ValueError:
        print("Invalid selection. Please enter a valid league number.")
        return

    selected_league = leagues[choice - 1]
    league_id = selected_league["league_id"]

    rosters_url = f"https://api.sleeper.app/v1/league/{league_id}/rosters"
    rosters = requests.get(rosters_url).json()

    user_roster = next((r for r in rosters if r.get("owner_id") == user_id), None)
    if not user_roster:
        print("Could not find your roster in this league.")
        return

    players_data = get_cached_players()

    state = requests.get("https://api.sleeper.app/v1/state/nfl").json()
    week = state.get("week", 1)

    projections_url = f"https://api.sleeper.app/v1/projections/nfl/regular/{week}"
    projections = requests.get(projections_url).json()

    display_user_roster(user_roster, players_data, selected_league['name'], projections, week)

def display_zero_projected_starters_for_user(user_id, username):
    state = requests.get("https://api.sleeper.app/v1/state/nfl").json()
    week = state.get("week", 1)

    season = "2024"
    leagues_url = f"https://api.sleeper.app/v1/user/{user_id}/leagues/nfl/{season}"
    leagues = requests.get(leagues_url).json()

    if not leagues:
        print(f"No leagues found for '{username}' in {season}.")
        return

    print("\nLeagues found:")
    for idx, league in enumerate(leagues):
        print(f"{idx + 1}. {league['name']} (ID: {league['league_id']})")

    try:
        choice = int(input("\nSelect a league number to check your starters: "))
        if choice < 1 or choice > len(leagues):
            raise ValueError
    except ValueError:
        print("Invalid selection.")
        return

    selected_league = leagues[choice - 1]
    league_id = selected_league["league_id"]

    rosters = requests.get(f"https://api.sleeper.app/v1/league/{league_id}/rosters").json()
    user_roster = next((r for r in rosters if r.get("owner_id") == user_id), None)

    if not user_roster:
        print("Could not find your roster in this league.")
        return

    players_data = get_cached_players()
    projections = requests.get(f"https://api.sleeper.app/v1/projections/nfl/regular/{week}").json()

    starters = user_roster.get("starters", [])
    zero_proj_starters = []

    for pid in starters:
        proj = projections.get(pid, {}).get("pts", 0.0)
        if proj == 0 or proj is None:
            player_info = players_data.get(pid, {})
            name = player_info.get("full_name", pid)
            position = player_info.get("position", "")
            team = player_info.get("team", "FA")
            zero_proj_starters.append(f"{name} ({position}, {team})")

    print(f"\n Starters on your team with 0.00 projected points (Week {week}):\n")
    if zero_proj_starters:
        for line in zero_proj_starters:
            print(" -", line)
    else:
        print("All your starters have projections. You’re good to go!")

def display_recommended_changes(user_id, username):

    state = requests.get("https://api.sleeper.app/v1/state/nfl").json()
    week = state.get("week", 1)

    season = "2024"
    leagues_url = f"https://api.sleeper.app/v1/user/{user_id}/leagues/nfl/{season}"
    leagues = requests.get(leagues_url).json()

    if not leagues:
        print(f"No leagues found for '{username}' in {season}.")
        return

    print("\nLeagues found:")
    for idx, league in enumerate(leagues):
        print(f"{idx + 1}. {league['name']} (ID: {league['league_id']})")

    try:
        choice = int(input("\nSelect a league number to check your starters: "))
        if choice < 1 or choice > len(leagues):
            raise ValueError
    except ValueError:
        print("Invalid selection.")
        return

    selected_league = leagues[choice - 1]
    league_id = selected_league["league_id"]

    rosters = requests.get(f"https://api.sleeper.app/v1/league/{league_id}/rosters").json()
    user_roster = next((r for r in rosters if r.get("owner_id") == user_id), None)

    if not user_roster:
        print("Could not find your roster in this league.")
        return

    players_data = get_cached_players()
    projections = requests.get(f"https://api.sleeper.app/v1/projections/nfl/regular/{week}").json()

    all_players = user_roster.get("players", [])
    starters = user_roster.get("starters", [])
    zero_proj_starters = []

    for pid in starters:
        proj = projections.get(pid, {}).get("pts", 0.0)
        if proj == 0 or proj is None:
            player_info = players_data.get(pid, {})
            name = player_info.get("full_name", pid)
            position = player_info.get("position", "")
            team = player_info.get("team", "FA")
            zero_proj_starters.append(f"{name} ({position}, {team})")

    print(f"\n Starters on your team with 0.00 projected points (Week {week}):\n")
    if zero_proj_starters:
        for line in zero_proj_starters:
            print(" -", line)
    else:
        print("All your starters have projections. You’re good to go!")
    bench = [pid for pid in all_players if pid not in starters]

    def get_proj(pid):
        return projections.get(pid, {}).get("pts", 0.0)

    def get_name(pid):
        return players_data.get(pid, {}).get("full_name", pid)

    def get_position(pid):
        return players_data.get(pid, {}).get("position", "")

    positions = ["QB", "RB", "WR", "TE"]
    recommended_swaps = []

    for pos in positions:
        starters_at_pos = [pid for pid in starters if get_position(pid) == pos]
        bench_at_pos = [pid for pid in bench if get_position(pid) == pos]

        for starter_id in starters_at_pos:
            starter_proj = get_proj(starter_id)

            for bench_id in bench_at_pos:
                bench_proj = get_proj(bench_id)

                if bench_proj > starter_proj:
                    recommended_swaps.append({
                        "position": pos,
                        "starter_id": starter_id,
                        "starter": (get_name(starter_id), starter_proj),
                        "bench": (get_name(bench_id), bench_proj)
                    })

    owned_ids = set()
    for roster in rosters:
        owned_ids.update(roster.get("players", []))

    free_agents = []
    for pid, player in players_data.items():
        if pid not in owned_ids:
            proj_pts = projections.get(pid, {}).get("pts", 0.0)
            position = player.get("position", "")
            if proj_pts > 0 and position in positions:
                free_agents.append({
                    "pid": pid,
                    "name": player.get("full_name", pid),
                    "position": position,
                    "team": player.get("team", "FA"),
                    "points": proj_pts
                })

    print("\nRecommended Lineup Changes:\n")
    if recommended_swaps:
        for swap in recommended_swaps:
            pos = swap["position"]
            starter_name, starter_pts = swap["starter"]
            bench_name, bench_pts = swap["bench"]
            print(f" - {pos}: Consider starting {bench_name} ({bench_pts:.2f} pts) over {starter_name} ({starter_pts:.2f} pts)")

            # Suggest signing a free agent if >= 75% of bench projection
            min_pts = 0.75 * bench_pts
            fa_alt = next(
                (fa for fa in free_agents if fa["position"] == pos and fa["points"] >= min_pts),
                None
            )
            if fa_alt:
                print(f"       Or signing {fa_alt['name']} ({fa_alt['points']:.2f} pts, {fa_alt['team']})")
    else:
        print("Your starters have higher or equal projections than your bench players. No changes needed!")
