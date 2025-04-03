import requests
from sleeper_utils import *

# username = "input("Enter your Sleeper username: ")"
username = "jakob12345"

user_url = f"https://api.sleeper.app/v1/user/{username}"
user_response = requests.get(user_url)

if user_response.status_code != 200:
    print("User not found. Please check the username.")
    exit()

user_data = user_response.json()
user_id = user_data["user_id"]

print("Options:")
print("1: Display leagues")
print("2: Display players projected 0")
print("3: Display recommended changes")

choice = int(input("\nChoose an option: "))
if choice == 1:
    handle_display_leagues(user_id, username)
elif choice == 2:
    display_zero_projected_starters_for_user(user_id, username)
elif choice == 3:
    display_recommended_changes(user_id, username)