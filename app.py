# imports to use
from flask import Flask, jsonify, request, redirect, url_for
from flask_cors import CORS
import requests
import json
import time


"""
Main API can be found at:
https://wakatime.com/api/v1/leaders
https://wakatime.com/api/v1/leaders?country_code=KE
https://wakatime.com/developers/
"""

app = Flask(__name__)
# solved cors issues especially in 127.0.0.1
CORS(app)

# Set the maximum number of requests allowed per hour (60) to prevent bots
MAX_REQUESTS_PER_HOUR = 60
# initial count
request_count = 0
# check when last reset was done
last_reset_time = time.time()


# url and method allowed
@app.route("/api/leaders", methods=["GET"])
def get_top_leaders():
    # get && define global vars
    global request_count, last_reset_time
    current_time = time.time()

    # Reset request count if an hour has passed since the last reset
    if current_time - last_reset_time > 3600:
        request_count = 0
        last_reset_time = current_time

    # once limit is reached show error or signup page to proceed
    if request_count >= MAX_REQUESTS_PER_HOUR:
        return (
            jsonify(
                {
                    "error": "Maximum number of requests reached. Please sign in or create an account to continue."
                }
            ),
            429,
        )
        # Return 429 for Too Many Requests
    else:
        # if not reached, continuing increasing till limit
        request_count += 1

    # main url
    url = "https://wakatime.com/api/v1/leaders"

    # add header options if need be
    # headers = {}

    # paramaters to pass to URL
    params = {"limit": 10}
    # Not working currently

    # Check if country_code is provided as a query parameter
    country_code = request.args.get("country_code")
    if country_code:
        params["country_code"] = country_code

    # fetch the url response together with parameters
    response = requests.get(url, params=params)
    # if response is okay(200)
    if response.status_code == 200:
        # jsonify the response
        data = response.json()["data"]
        stripped_data = []
        """
        Get the top 15 leaders worldwide or per country
        filter details to only leave city, username && country(includes city)
        if no data for user leave empty
        Also get top 3 languages and time coded
        If possible might include languages mascot
        """
        for leader in data[:15]:
            if "user" in leader:
                user = leader["user"]
                city = user.get("city")  # Use .get() to safely retrieve the value
                if city:
                    user_title = city.get("title", "")
                    country_code = city.get("country_code", "")
            else:
                user_title = ""
                country_code = ""

            if "running_total" in leader:
                running_total = leader["running_total"]
                running_daily = running_total["human_readable_daily_average"]
                running_total_human_readable = running_total["human_readable_total"]
                top_3_languages = [
                    {"name": lang["name"], "total_seconds": lang["total_seconds"]}
                    for lang in running_total["languages"][:3]
                ]
            else:
                running_daily = 0
                running_total_human_readable = ""
                top_3_languages = []

            """
            Now show the final info
            """
            stripped_leader = {
                "rank": leader["rank"],
                "username": user["username"],
                "city": user_title,
                "country_code": country_code,
                "running_daily": running_daily,
                "running_total_human_readable": running_total_human_readable,
                "top_3_languages": top_3_languages,
            }
            stripped_data.append(stripped_leader)

        return jsonify(stripped_data)
    else:
        """
        If data fails to fetch, show an error and the reason(currently on console)
        """
        return (
            jsonify(
                {
                    "error": f"Failed to fetch data: {response.status_code}, {response.text}"
                }
            ),
            response.status_code,
        )


# set default path and redirect if user goes to unverified URL
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def catch_all(path):
    return redirect(url_for("get_top_leaders"))


# finally run the app only when called by name
if __name__ == "__main__":
    app.run(debug=True)
