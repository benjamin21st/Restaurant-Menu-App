# fullstack_03
## Setup Environment
This web app requires `postgresql` and `Python2.7` as basic system
requirements. If your system meets these requirements,
run `pip install -r requirements.txt` to install all dependencies
needed for our app to work properly.


## Setup Database
Run `database_setup.py` by typing `python database_setup.py` and press 'enter'.


## Start app
In command line, run `app.py` file by typing `python app.py`.


## Using the app
Open up your browser and go to [localhost:5000], you will see
our restaurant/menu app up and running. It supports basic Create, Read, Update, Delete
functions for both restaurants and menu items. And integrated with
Oauth for enhanced security.

For developers, this app provides three API endpoints where you
can get data.
1. You can get all restaurants in a json format by sending a `GET` request to
   `/restaurants/JSON`
2. You can get all menu items for a specific restaurant by sending a `GET`
   request to `/restaurants/<int:restaurant_id>/menu/JSON`.
3. You can get details of one menu item for a specific restaurant by
   sending a `GET` request to `/restaurants/<int:restaurant_id>/menu/<int:menu_id>/JSON`.


TODO:
1. include API endpoint in README  [V]
2. double check the no login and show restaurants issue, add
   if 'username' not in login_session:
        user_id = None
    else:
        user_id = login_session['user_id']
    context = {
        'restaurants': restaurants,
        'user_id': user_id
    }
    to code [V]
3. remove all menu items upon deletion of a restaurant,
   add ondelete = u'CASCADE' to db_setup.MenuItem [V]
4. add csrf token with flask-seasurf.readthedocs.org
5. hide the sign out button when not logged in [V]
6. add initial data for testing purpose * [V]
7. on sign out, instead of redirecting to sign in page, flash a message and
   then redirect to home/index * [V]
9. wrap all functions that need auth using a decorator function:
    def login_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if g.user is None:
                return redirect(url_for('login', next=request.url))
            return f(*args, **kwargs)
        return decorated_function

    then put @login_required() [V]
10. move DB related functions to database_setup.py [X]
11. Disable the front end reset thingy