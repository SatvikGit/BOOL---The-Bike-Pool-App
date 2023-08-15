# BOOL-The Bike Pool App
#### Video Demo:  https://www.youtube.com/watch?v=kDuMg8akizI
#### Description:
For my final project, I have created an app named **BOOL-The Bike Pool App** which helps the user to meet other users to share their bike for bike pooling to their destination. I have created this app because there is not any app or site which helps daily commuters and help them save fuel, reducing traffic in metropolitian cities, socialize with other users living in same area commuting to nearby location as user, also make a difference in reducing carbon footprint and in turn, reducing effect of vehicles on the planet.

##### Technologies/Languages Used in My Final Project:
- Flask(Python) for back-end
- HTML, CSS for front-end
- JavaScript for providing interactivity to webpages
- Used Jinja2 for using logic inside HTML templates
- Used sqlite3 for database managment

##### My project includes following features:
- Registering, Log-In and Log-out of user
- Homepage for showing nearby pools and invitations for pool
- Sending Friend Request to other users
- Accepting Friend Requests of available requests and displaying table of friends
- Creating pool for everyone in nearby area
- Inviting a friend for pool
- History table for seeing previous pools created by user

##### Register:
User is asked for details such as username, fullname, address, city, bike owned, password, confirm password, phone. The program validates the inputs entered by user and also checks each requirement for password such as character count, combination of uppercase and owercase letters, digits and special characters. Program registers the user and updates the database on basis of data provided by user.

##### Log-In:
User is asked for credentials that are username and password, if they match user gets redirected to homepage. All other routes other than Register and Log-In requires user to be logged in.

##### Log-Out:
This clears the session for one user and allows another user to log in from same device.

##### HomePage:
This is the landing page of the website upon logging in, this displays the table for neary pools that some user created for everyone, also displays pool specially curated for the user by their friend. This table includes creator's fullname, bike owned, origin and destination of pool, phone number of creator. The program renders "No Nearby Pools" if no user has created a pool in their area and provides them with a button which redirects them to 'create pool' route where they can hosta pool for everyone. ***Pool automatically disappears after 2 hours of creation(both nearby pools and pools created by invitation).***

##### Change Password:
This feature allows user to change his/her password to a new password, program asks user for previous password and lets user to chnage his/her password if entered old password is correct.

##### Create Pool:
Users create pool for everyone(registered on **BOOL**) in nearby area to invite them to pool with the user. User enters origin and destination of the ride and other users can see this info and may contact the user if the origin/destination suits them.

##### Add Friend:
User can send friend request to any user by entering that user's username and thus sending them a friend request.

##### Friends:
This displays the table of user's friends with info like username, fullname, address, bike owned and also provides a button which redirects them to invite route. This route also displays available friend requests for the user and gives them option to accept or reject a request, upon clicking button for accepting/rejecting a request and refreshing the page, the request disappears and friend is added to friends table if user has accepted the request. If user does not have and any friend and does not have any friend request, the program provides option to add friend by redirecting them to 'add friend' route.

##### History:
This renders a table of pools that user has created(both nearby pools and pools created by invitation) and contains info like date of creation, created for('EVERYONE' for nearby pools and friend's username for invite pools), origin and destination of pool. If user has not created any pools in past, it provides them with a button which redirects them to 'create pool' from where they can create a nearby pool.

My Final Project has been created to cater the needs of daily commuters lives and hope to be of help to the society. That was all!

***Thank You***