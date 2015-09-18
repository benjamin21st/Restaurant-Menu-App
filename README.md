# Restaurant Menu App
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
