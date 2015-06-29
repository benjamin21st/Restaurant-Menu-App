from flask import Flask, render_template, request, make_response, redirect, \
                  url_for, flash, jsonify, session as login_session, g, abort
from flask_login import LoginManager, login_user, current_user, logout_user, \
                  login_required

import random
import string
from sqlalchemy import asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Restaurant, MenuItem, User, engine

from oauth2client.client import flow_from_clientsecrets, FlowExchangeError, \
                                AccessTokenCredentials
import httplib2
import json
import requests

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read()
)['web']['client_id']
APPLICATION_NAME = "Restaurant Menu Application"


Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

app = Flask(__name__)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def user_loader(u_id):
    try:
        return session.query(User).filter_by(id=u_id).one()
    except:
        return None


@app.before_request
def before_request():
    g.user = current_user


@app.before_request
def csrf_protect():
    if (request.method == 'POST' and
        'gconnect' not in request.url and
            'gdisconnect' not in request.url):
        token = login_session.pop('_csrf_token', None)
        if not token or token != request.form.get('_csrf_token'):
            abort(403)


@app.before_request
def generate_csrf_token():
    if login_session:
        if '_csrf_token' not in login_session:
            login_session['_csrf_token'] = ''.join(random.choice(
                string.ascii_uppercase + string.digits) for x in range(32))

            app.jinja_env.globals['csrf_token'] = login_session['_csrf_token']


'''
Here are some API endpoints
'''


@app.route('/restaurants/JSON')
def restaurantsJSON():
    restaurants = session.query(Restaurant).all()
    return jsonify(restaurants=[r.serialize for r in restaurants])


@app.route('/restaurants/<int:restaurant_id>/menu/JSON')
def restaurantMenuJSON(restaurant_id):
    items = session.query(MenuItem).filter_by(
                restaurant_id=restaurant_id).all()
    return jsonify(MenuItems=[i.serialize for i in items])


@app.route('/restaurants/<int:restaurant_id>/menu/<int:menu_id>/JSON')
def menuItemJSON(restaurant_id, menu_id):
    Menu_Item = session.query(MenuItem).filter_by(id=menu_id).one()
    return jsonify(Menu_Item=Menu_Item.serialize)


'''
Here are the routing and functions of our web app
'''


@app.route('/login', methods=['GET', 'POST'])
def login():
    state = ''.join(random.choice(string.ascii_uppercase +
                                  string.digits) for x in range(32))
    login_session['state'] = state

    context = {
        "guest": True,
        "state": state
    }

    return render_template('login.html', context=context)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    code = request.data

    try:
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])

    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'

    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)

        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if (stored_credentials is not None and
        gplus_id == stored_gplus_id and
            g.user.is_authenticated()):
        user = User.query.get(login_session['email'])
        login_user(user)
        response = make_response(
            json.dumps('Current user is already connected.'), 200
            )
        response.headers['Content-Type'] = 'application/json'
        return response

    login_session['credentials'] = credentials.access_token
    credentials = AccessTokenCredentials(login_session['credentials'],
                                         'user-agent-value')

    login_session['gplus_id'] = gplus_id

    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    g.user = data
    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    '''
    Here we check if a user with this gmail address exist,
    if so, login right away,
    if not, we automatically create a user in our local DB
    with the username, email, picture
    '''

    u_id = getUserID(login_session['email'])

    if not u_id:
        u_id = createUser(login_session)

    login_session['user_id'] = u_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += '"style = ' \
              '"width: 300px; ' \
              'height: 300px;' \
              'border-radius: 150px;' \
              '-webkit-border-radius: 150px;' \
              '-moz-border-radius: 150px;' \
              '">'
    flash("you are now logged in as %s" % login_session['username'])
    return output


@app.route('/gdisconnect')
def gdisconnect():
    credentials = login_session.get('credentials')
    if credentials is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = credentials
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':
        del login_session['credentials']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']

        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/signout')
def signout():
    if 'gplus_id' in login_session:
        gdisconnect()

    logout_user()

    return redirect(url_for('showRestaurants'))


@app.route('/')
@app.route('/restaurants')
def showRestaurants():
    restaurants = session.query(Restaurant).order_by(asc(Restaurant.name))
    if 'username' not in login_session:
        user_id = None
    else:
        user_id = login_session['user_id']

    context = {
        'restaurants': restaurants,
        'user_id': user_id
    }

    return render_template('restaurants.html', context=context)


@app.route('/restaurants/new', methods=['GET', 'POST'])
@login_required
def createRestaurant():
    context = {
        'user_id': login_session['user_id']
    }

    if request.method == 'POST':
        new_restaurant = Restaurant(name=request.form['restaurant-name'])
        new_restaurant.user_id = login_session['user_id']

        try:
            session.add(new_restaurant)
            session.commit()
            message = 'New Restaurant %s Successfully Created' % \
                      new_restaurant.name
            flash(message, 'info')

        except:
            message = 'There is an error adding this item'
            flash(message, 'error')

        return redirect(url_for('newMenuItem',
                                restaurant_id=new_restaurant.id))
    else:
        return render_template('newRestaurant.html', context=context)


@app.route('/restaurants/<int:restaurant_id>/edit', methods=['GET', 'POST'])
@login_required
def editRestaurant(restaurant_id):
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    context = {'restaurant': restaurant}

    if login_session['user_id'] != restaurant.user_id:
        '''
        If user attempts to edit a restaurant that is not created by
        him/herself, redirect this user to the restaurants list
        '''
        message = 'Sorry, you do not have authorization to \
                  edit this restaurant'
        flash(message, 'warning')

        return redirect(url_for('showRestaurants'))

    if request.method == 'POST':
        restaurant.name = request.form['restaurant-name']

        try:
            session.add(restaurant)
            session.commit()
            message = 'Restaurant info has been successfully edited'
            flash(message, 'info')

        except:
            message = 'Restaurant info cannot be updated'
            flash(message, 'error')

    return render_template('editrestaurant.html', context=context)


@app.route('/restaurants/<int:restaurant_id>/delete', methods=['GET', 'POST'])
@login_required
def deleteRestaurant(restaurant_id):
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    context = {'restaurant_name': restaurant.name}

    if login_session['user_id'] != restaurant.user_id:
        message = 'Sorry, you do not have authorization to \
                  delete this restaurant'
        flash(message, 'warning')

        return redirect(url_for('showRestaurants'))

    if request.method == 'POST':
        try:
            session.delete(restaurant)
            session.commit()
            message = '%s has been deleted' % restaurant.name
            flash(message, 'info')
        except:
            message = 'Restaurant cannot be deleted'
            flash(message, 'error')

        return redirect(url_for('showRestaurants'))

    return render_template('deleterestaurant.html', context=context)


@app.route('/restaurants/<int:restaurant_id>')
@app.route('/restaurants/<int:restaurant_id>/menu')
def showMenu(restaurant_id):
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    menu_items = session.query(MenuItem).filter_by(
                                         restaurant_id=restaurant_id).all()

    if 'user_id' in login_session:
        user_id = login_session['user_id']
    else:
        user_id = None

    context = {
        'restaurant': restaurant,
        'menu_items': menu_items,
        'user_id': user_id
    }

    return render_template('menu.html', context=context)


@app.route('/restaurants/<int:restaurant_id>/menu/new',
           methods=['GET', 'POST'])
@login_required
def newMenuItem(restaurant_id):
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    context = {
        'restaurant_id': restaurant_id,
        'user_id': login_session['user_id']
    }

    if login_session['user_id'] != restaurant.user_id:
        message = 'Sorry, you do not have authorization to create menu \
        on behalf of this restaurant'
        flash(message, 'warning')

        return redirect(url_for('showMenu', restaurant_id=restaurant.id))

    if request.method == 'POST':
        menu_item = MenuItem(
            name=request.form['menu-item-name'],
            course=request.form['menu-item-course'],
            price=request.form['menu-item-price'],
            description=request.form['menu-item-description'],
            restaurant_id=restaurant_id,
            user_id=login_session['user_id']
        )

        try:
            session.add(menu_item)
            session.commit()
            message = 'A new menu item %s has been created' % menu_item.name
            flash(message, 'info')
        except:
            message = 'There is an error adding this item'
            flash(message, 'error')

        return redirect(url_for('showMenu', restaurant_id=restaurant_id))

    return render_template('newmenuitem.html', context=context)


@app.route('/restaurants/<int:restaurant_id>/menu/<int:menu_id>/edit',
           methods=['GET', 'POST'])
@login_required
def editMenuItem(restaurant_id, menu_id):
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    menu_item = session.query(MenuItem).filter_by(id=menu_id).one()

    if (login_session['user_id'] != menu_item.user_id or
            login_session['user_id'] != restaurant.user_id):
        message = 'Sorry, you do not have authorization to edit this menu item'
        flash(message, 'warning')

        return redirect(url_for('showMenu', restaurant_id=restaurant.id))

    context = {
        "restaurant": restaurant,
        "menu_id": menu_id,
        "menu_item": menu_item
    }

    if request.method == 'POST':
        try:
            menu_item.name = request.form['menu-item-name']
            menu_item.course = request.form['menu-item-course']
            menu_item.price = request.form['menu-item-price']
            menu_item.description = request.form['menu-item-description']

            session.add(menu_item)
            session.commit()

            message = "Menu item %s has been updated." % menu_item.name
            flash(message, 'info')

        except:
            message = "There is an error updating this menu item"
            flash(message, 'error')

    return render_template('editmenuitem.html', context=context)


@app.route('/restaurants/<int:restaurant_id>/menu/<int:menu_id>/delete',
           methods=['GET', 'POST'])
@login_required
def deleteMenuItem(restaurant_id, menu_id):
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    menu_item = session.query(MenuItem).filter_by(id=menu_id).one()

    if (login_session['user_id'] != menu_item.user_id or
            login_session['user_id'] != restaurant.user_id):
        message = 'Sorry, you do not have authorization to delete \
                  this menu item'
        flash(message, 'warning')

        return redirect(url_for('showMenu', restaurant_id=restaurant.id))

    if request.method == 'POST':
        try:
            session.delete(menu_item)
            message = 'Menu item %s has been deleted' % menu_item.name
            flash(message, 'info')

        except:
            message = 'There is an error deleting this menu item'
            flash(message, 'error')

        return redirect(url_for('showMenu', restaurant_id=restaurant.id))

    else:
        context = {
            "restaurant": restaurant,
            "menu_item": menu_item
        }
        return render_template('deletemenuitem.html', context=context)


def createUser(login_session):
    newUser = User(
        name=login_session['username'],
        email=login_session['email'],
        picture=login_session['picture']
    )
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


if __name__ == '__main__':
    # this wouldn't be here if this is a real world app
    app.secret_key = 'super_key'
    app.debug = True
    app.run()
