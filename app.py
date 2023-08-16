import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta
import secrets

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Generate a random secret key using the secrets module and store it in the variable secret_key
secret_key = secrets.token_hex(16)

# Set the session type to use the filesystem to store session data and then Set the Flask app's secret key to be the value stored in the secret_key variable
app.config["SESSION_TYPE"] = "filesystem"
app.secret_key = "secret_key"

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///project.db")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///project.db'


# This decorator sets response headers to prevent caching
@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Shows nearby available pools"""

    # Retrieve user's address from the database
    user_address = db.execute("SELECT address FROM users WHERE id = ?", session["user_id"])[0]["address"]

    # Retrieve IDs of users who are creators of nearby pools
    creator_id = db.execute("SELECT creator FROM pools JOIN users WHERE users.id = pools.creator AND users.address = ?", user_address)

    # List to hold data about nearby available pools, pool invitations, Set to store unique route pairs for both nearby and invite pools
    nearby_data = []
    invite_data = []
    unique_routes = set()
    invite_routes = set()

    # Cutoff time for recent pools
    cutoff_time = datetime.now().timestamp() - timedelta(hours=2).total_seconds()

    if creator_id:
        for creator in creator_id:
            creator = creator["creator"]
            if creator != session["user_id"]:
                # Retrieve pool information from users and pools tables
                info_dict = db.execute("SELECT username, fullname, bike, phone, origin, destination, time FROM users JOIN pools WHERE users.id = pools.creator AND users.id =  ?", creator)
                for pool in info_dict:
                    time = pool["time"]
                    # Check if the pool's time is more recent than the cutoff time
                    if float(time) > cutoff_time:
                        # Create a tuple representing the origin-destination route
                        route = (pool["origin"], pool["destination"])
                        if route not in unique_routes:
                            # Add the route to the set of unique routes
                            unique_routes.add(route)
                            # Append pool data to the list of nearby_data
                            nearby_data.append(
                                {
                                    "username": pool["username"],
                                    "fullname": pool["fullname"],
                                    "bike": pool["bike"],
                                    "phone": pool["phone"],
                                    "origin": pool["origin"],
                                    "destination": pool["destination"],
                                }
                            )

    # Retrieve pool invitations for the logged-in user
    invites = db.execute("SELECT username, fullname, bike, phone, origin, destination, time FROM users JOIN pools WHERE users.id = pools.creator AND follower = ?", session["user_id"])

    if invites:
        for invite in invites:
            # Check if the pool's time by invitation is more recent than the cutoff time
            if float(invite["time"]) > cutoff_time:
                # Create a tuple representing the origin-destination route
                route = (invite["origin"], invite["destination"])
                if route not in invite_routes:
                    # Add the route to the set of unique invite routes
                    invite_routes.add(route)
                    # Append pool data to the list of invite_data
                    invite_data.append(
                        {
                            "username": invite["username"],
                            "fullname": invite["fullname"],
                            "bike": invite["bike"],
                            "phone": invite["phone"],
                            "origin": invite["origin"],
                            "destination": invite["destination"],
                        }
                    )
    return render_template("index.html", nearby_data=nearby_data, invite_data=invite_data)


@app.route("/login", methods=["GET", "POST"])
def login():
    """User log-in"""

    # Clear any existing session data
    session.clear()
    if request.method == "POST":
        # Validation checks for user input
        if not request.form.get("username").strip():
            return apology("provide a username", 400)

        elif not request.form.get("password").strip():
            return apology("provide a password", 400)

        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username").strip())

        if len(rows) != 1:
            return apology("enter a valid username", 400)

        elif not check_password_hash(rows[0]["hash"], request.form.get("password").strip()):
            return apology("incorrect password", 400)

        # Store the user's ID in the session
        session["user_id"] = rows[0]["id"]
        return redirect("/")

    else:
        return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    """Logs out the user"""

    # Clear the session data
    session.clear()
    return redirect("/")


@app.route("/create_pool", methods=["GET", "POST"])
def create_pool():
    """Creates a pool by user"""
    if request.method == "POST":
        # Validation checks for user input
        if not request.form.get("start").strip():
            return apology("must require ride start address", 400)

        elif not request.form.get("destination").strip():
            return apology("must require ride destination address", 400)

        else:
            # Extract and format data from the form
            start = request.form.get("start").strip()
            start = start[0].upper() + start[1:]
            destination = request.form.get("destination").strip()
            destination = destination[0].upper() + destination[1:]

            # Get current timestamp for pool creation time
            creation_time = datetime.now().timestamp()
            db.execute("INSERT INTO pools (creator, origin, destination, time) VALUES (?, ?, ?, ?)", session["user_id"], start, destination, creation_time)

        # Retrieve the pool information from the 'pools' table based on the creation time of pool that was just created above
        pool = db.execute("SELECT * FROM pools WHERE time = ?", creation_time)[0]

        # Convert the creation timestamp to a datetime object for formatting
        datetime_obj = datetime.fromtimestamp(creation_time)

        # Format timestamp to a readable date and time
        formatted_date = datetime_obj.strftime("%d/%m/%Y")
        formatted_time = datetime_obj.strftime("%H/%M/%S")

        db.execute("INSERT INTO history (user_id, pool_id, origin, destination, date) VALUES (?, ?, ?, ?, ?)", session["user_id"], pool["id"], pool["origin"], pool["destination"], formatted_date)
        return redirect("/")

    else:
        return render_template("pool.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Registers new user"""
    if request.method == "POST":
        # Extract user input from the registration form
        username = request.form.get("username").strip()
        fullname = request.form.get("fullname").strip()
        address = request.form.get("address").strip()
        city = request.form.get("city").strip()
        bike = request.form.get("bike").strip()
        phone = request.form.get("phone").strip()

        # Validation checks for user input
        if not username:
            return apology("must require a username", 400)

        elif not fullname:
            return apology("must require full name", 400)

        elif not request.form.get("password"):
            return apology("must require a password", 400)

        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords do not match", 400)

        # Set default values for optional user inputs if they are not provided
        elif not address:
            address = "NOT AVAILABLE"

        elif not city:
            city = "NOT AVAILABLE"

        elif not bike:
            bike = "NOT AVAILABLE"

        elif not phone:
            phone = "NOT AVAILABLE"

        # Validate password complexity
        password = request.form.get("password").strip()
        if len(password) < 8:
            return apology("password must contain 8 characters", 400)

        for char in password:
            has_upper = False
            for char in password:
                if char.isupper():
                    has_upper = True
                    break

        if not has_upper:
            return apology("password must contain at least one uppercase character", 400)

        for char in password:
            has_lower = False
            for char in password:
                if char.islower():
                    has_lower = True
                    break

        if not has_lower:
            return apology("password must contain at least one lowercase character", 400)

        for char in password:
            has_number = False
            for char in password:
                if char.isdigit():
                    has_number = True
                    break

        if not has_number:
            return apology("password must contain at least one number", 400)

        ALLOWED_SPECIAL_CHARS = set(
            [
                "!",
                "@",
                "#",
                "$",
                "%",
                "^",
                "&",
                "*",
                "(",
                ")",
                "-",
                "_",
                "+",
                "=",
                "{",
                "}",
                "[",
                "]",
                "|",
                "\\",
                ";",
                ":",
                "'",
                '"',
                "<",
                ">",
                ",",
                ".",
                "?",
                "/",
            ]
        )
        has_special = False
        for char in password:
            if char in ALLOWED_SPECIAL_CHARS:
                has_special = True
                break

        if not has_special:
            return apology("password must contain a special character", 400)

        # Check if username already exists
        existing_user = db.execute("SELECT * FROM users WHERE username = ?", username.lower())
        if existing_user:
            return apology("username already exists", 400)

        else:
            # Format and store user data in the database
            username = username.lower()
            fullname = fullname[0].upper() + fullname[1:]
            address = address[0].upper() + address[1:]
            city = city[0].upper() + city[1:]
            bike = bike[0].upper() + bike[1:]
            # Hash the user's password
            hash = generate_password_hash(password)
            if phone != "NOT AVAILABLE":
                phone = "+91-" + phone
            db.execute("INSERT INTO users (username, fullname, hash, address, city, bike, phone) VALUES (?, ?, ?, ?, ?, ?, ?)", username, fullname, hash, address, city, bike, phone)
            return redirect("/")
    else:
        return render_template("register.html")


@app.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():
    """Changes user's password"""
    if request.method == "POST":
        # Validation checks for provided passwords
        if not request.form.get("old_password").strip():
            return apology("must enter old password", 400)

        elif not request.form.get("new_password").strip():
            return apology("must enter new password", 400)

        elif request.form.get("new_password").strip() != request.form.get("confirmation").strip():
            return apology("confirm password must be same as new password", 400)

        # Validate new password complexity
        new_password = request.form.get("password").strip()
        if len(new_password) < 8:
            return apology("password must contain 8 characters", 400)

        for char in new_password:
            has_upper = False
            for char in new_password:
                if char.isupper():
                    has_upper = True
                    break

        if not has_upper:
            return apology("password must contain at least one uppercase character", 400)

        for char in new_password:
            has_lower = False
            for char in new_password:
                if char.islower():
                    has_lower = True
                    break

        if not has_lower:
            return apology("password must contain at least one lowercase character", 400)

        for char in new_password:
            has_number = False
            for char in new_password:
                if char.isdigit():
                    has_number = True
                    break

        if not has_number:
            return apology("password must contain at least one number", 400)

        ALLOWED_SPECIAL_CHARS = set(
            [
                "!",
                "@",
                "#",
                "$",
                "%",
                "^",
                "&",
                "*",
                "(",
                ")",
                "-",
                "_",
                "+",
                "=",
                "{",
                "}",
                "[",
                "]",
                "|",
                "\\",
                ";",
                ":",
                "'",
                '"',
                "<",
                ">",
                ",",
                ".",
                "?",
                "/",
            ]
        )
        has_special = False
        for char in new_password:
            if char in ALLOWED_SPECIAL_CHARS:
                has_special = True
                break

        if not has_special:
            return apology("password must contain a special character", 400)

        # Retrieve the old password hash from the database
        old_hash = db.execute("SELECT hash FROM users WHERE id = ?", session["user_id"])[0]["hash"]

        if check_password_hash(old_hash, request.form.get("old_password").strip()):
            # Hash the new password and update it in the database
            hash_new = generate_password_hash(request.form.get("new_password").strip())
            db.execute("UPDATE users SET hash = ? WHERE id = ?", hash_new, session["user_id"])
            return redirect("/")
        else:
            return apology("incorrect password")
    else:
        return render_template("changepass.html")


@app.route("/add_friend", methods=["GET", "POST"])
@login_required
def add_friend():
    """Sends a friend request to another user"""
    if request.method == "POST":
        # Validation checks for user input
        if not request.form.get("friend_username").strip():
            return apology("must require username", 400)

        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("friend_username").strip())

        if len(rows) != 1:
            return apology("enter a valid user", 400)

        sender = session["user_id"]
        receiver = rows[0]["id"]

        # Return error if sending request to oneself
        if sender == receiver:
            return apology("you can't send yourself a friend request", 400)

        # Create the 'requests' table if it doesn't exist already
        db.execute(''' CREATE TABLE IF NOT EXISTS requests (
                           id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                           sender INTEGER NOT NULL,
                           receiver INTEGER NOT NULL,
                           status TEXT DEFAULT 'pending',
                           FOREIGN KEY (sender) REFERENCES users(id),
                           FOREIGN KEY (receiver) REFERENCES users(id)
                           )''')

        # Check if a friend request has already been sent from the current user to the specified receiver
        request_sent = db.execute("SELECT * FROM requests WHERE sender = ? AND receiver = ?", sender, receiver)
        if request_sent:
            # Render template indicating friend request already sent
            return render_template("friendreq.html", already_sent=True)

        db.execute("INSERT INTO requests (sender, receiver, status) VALUES (?, ?, 'pending')", sender, receiver)
        success = True
        # Render template indicating friend request successfully sent
        return render_template("friendreq.html", success=success)
    else:
        return render_template("friendreq.html", already_sent=False, success=False)


@app.route("/friends", methods=["GET", "POST"])
@login_required
def friends():
    """Shows Available Friend Requests"""
    if request.method == "POST":
        # Retrieve data from the JSON request to handle friend request options
        answer = request.get_json()

        # Get the option from the JSON data (accept or reject)
        option = answer["option"]

        # Get the sender's username from the JSON data
        sender_name = answer["sender"]
        sender = db.execute("SELECT id FROM users WHERE username = ?", sender_name)[0]["id"]

        # Update the status of the friend request based on the selected option
        if option == "accept":
            db.execute("UPDATE requests SET status = 'accepted' WHERE sender = ? AND receiver = ?", sender, session["user_id"])
        elif option == "reject":
            db.execute("UPDATE requests SET status = 'rejected' WHERE sender = ? AND receiver = ?", sender, session["user_id"])
        return redirect("/friends")
    else:
        # Get the list of senders who sent friend requests
        rows = db.execute("SELECT sender FROM requests WHERE receiver = ? AND status = 'pending'", session["user_id"])
        senders = []
        for row in rows:
            req = row["sender"]
            # Fetch the sender's username from the database and adding the sender's username to the 'senders' list
            sender = db.execute("SELECT username FROM users JOIN requests ON users.id = requests.sender WHERE users.id = ?", req)[0]["username"]
            senders.append(sender)

         # Get the list of friends and their details
        friends_dict1 = db.execute("SELECT username FROM users JOIN requests ON users.id = requests.receiver WHERE requests.sender = ? AND requests.status = 'accepted'", session["user_id"])
        friends_dict2 = db.execute("SELECT username FROM users JOIN requests ON users.id = requests.sender WHERE requests.receiver = ? AND requests.status = 'accepted'", session["user_id"])

        friends_list1 = []
        for friend in friends_dict1:
            friends_list1.append(friend["username"])

        friends_list2 = []
        for friend in friends_dict2:
            friends_list2.append(friend["username"])

        # Combine the two lists and create a unique set of usernames using 'set', then convert back to a list
        friends_list = list(set(friends_list1 + friends_list2))

        friends_fullname = []
        friends_address = []
        friends_bike = []
        for friend in friends_list:
            # Fetch the friend's full name, address, and bike information from the database and adding the retrieved information to the respective lists
            fullname_dict = db.execute("SELECT fullname FROM users WHERE username = ?", friend)[0]["fullname"]
            address_dict = db.execute("SELECT address FROM users WHERE username = ?", friend)[0]["address"]
            bike_dict = db.execute("SELECT bike FROM users WHERE username = ?", friend)[0]["bike"]
            friends_address.append(address_dict)
            friends_bike.append(bike_dict)
            friends_fullname.append(fullname_dict)

        # Zip friends' data together if available
        if friends_list:
            if friends_fullname:
                if friends_address:
                    if friends_bike:
                        friends_data = zip(
                            friends_list,
                            friends_fullname,
                            friends_address,
                            friends_bike,
                        )
        else:
            friends_data = []
        return render_template("friends.html", senders=senders, friends_data=friends_data)

@app.route("/invite", methods=["GET", "POST"])
@login_required
def invite():
    """Send Invite to friends for pool"""
    if request.method == "POST":
        # Validation checks for user input
        if not request.form.get("friend_username").strip():
            return apology("must require friend's username", 400)

        elif not request.form.get("origin").strip():
            return apology("must require start address", 400)

        elif not request.form.get("destination").strip():
            return apology("must require destination", 400)

        else:
            # Extract and format data from the form
            friend_name = request.form.get("friend_username").strip()
            friend = db.execute("SELECT id FROM users WHERE username = ?", friend_name)[0]["id"]
            origin = request.form.get("origin").strip()
            origin = origin[0].upper() + origin[1:]
            destination = request.form.get("destination").strip()
            destination = destination[0].upper() + destination[1:]

            # Get current timestamp for invited pool creation time
            invite_time = datetime.now().timestamp()
            db.execute("INSERT INTO pools (creator, follower, origin, destination, time) VALUES (?, ?, ?, ?, ?)", session["user_id"], friend, origin, destination, invite_time)
            pool_id = db.execute("SELECT id FROM pools WHERE time = ?", invite_time)[0]["id"]

            # Format timestamp to a readable date and time
            datetime_obj = datetime.fromtimestamp(invite_time)
            formatted_date = datetime_obj.strftime("%d/%m/%Y")
            formatted_time = datetime_obj.strftime("%H/%M/%S")

        db.execute("INSERT INTO history (user_id, pool_id, recipient_id, origin, destination, date) VALUES (?, ?, ?, ?, ?, ?)", session["user_id"], pool_id, friend, origin, destination, formatted_date)
        return redirect("/")
    else:
        # Fetch and display the list of friends for inviting
        friends_dict1 = db.execute("SELECT username FROM users JOIN requests ON users.id = requests.receiver WHERE requests.sender = ? AND requests.status = 'accepted'", session["user_id"])
        friends_dict2 = db.execute("SELECT username FROM users JOIN requests ON users.id = requests.sender WHERE requests.receiver = ? AND requests.status = 'accepted'", session["user_id"])

        friends_list1 = []
        for friend in friends_dict1:
            friends_list1.append(friend["username"])

        friends_list2 = []
        for friend in friends_dict2:
            friends_list2.append(friend["username"])

        friends_list = list(set(friends_list1 + friends_list2))
        return render_template("invite.html", friends_list=friends_list)


@app.route("/history")
@login_required
def history():
    """Shows previous bike pools"""

    # Create the 'history' table if it doesn't already exist
    db.execute('''CREATE TABLE IF NOT EXISTS history (
                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                      user_id INTEGER NOT NULL,
                      pool_id INTEGER NOT NULL,
                      recipient_id TEXT,
                      origin TEXT NOT NULL,
                      destination TEXT NOT NULL,
                      date TEXT NOT NULL,
                      FOREIGN KEY (user_id) REFERENCES users(id),
                      FOREIGN KEY (pool_id) REFERENCES pools(id)
                      )''')

    # Fetch the user's history from the 'history' table
    history = db.execute("SELECT * FROM history WHERE user_id = ?", session["user_id"])
    recipient_name = []
    for pool in history:
        recipient_id = pool["recipient_id"]
        if recipient_id:
            recipient_id = int(recipient_id)
            fullname = db.execute("SELECT fullname from users WHERE id = ?", recipient_id)[0]["fullname"]
            recipient_name.append(fullname)
        else:
            recipient_name.append("EVERYONE")

    # Zip the history information with recipient names if applicable
    if history:
        history_info = zip(history, recipient_name)
        return render_template("history.html", history_info=history_info)
    else:
        # Render the history page when there's no history information
        return render_template("history.html")
