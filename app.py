from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from sqlalchemy import asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Restaurant, MenuItem, engine


Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

app = Flask(__name__)


#APIs
@app.route('/restaurants/JSON')
def restaurantsJSON():
    restaurants = session.query(Restaurant).all()
    return jsonify(restaurants=[r.serialize for r in restaurants])


@app.route('/restaurants/<int:restaurant_id>/menu/JSON')
def restaurantMenuJSON(restaurant_id):
    # restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    items = session.query(MenuItem).filter_by(restaurant_id=restaurant_id).all()
    return jsonify(MenuItems=[i.serialize for i in items])


@app.route('/restaurants/<int:restaurant_id>/menu/<int:menu_id>/JSON')
def menuItemJSON(restaurant_id, menu_id):
    Menu_Item = session.query(MenuItem).filter_by(id=menu_id).one()
    return jsonify(Menu_Item=Menu_Item.serialize)



@app.route('/')
@app.route('/restaurants')
def showRestaurants():
    # flash('This page will show all my restaurants')
    restaurants = session.query(Restaurant).order_by(asc(Restaurant.name))
    context = {'restaurants': restaurants}

    return render_template('restaurants.html', context=context)


@app.route('/restaurants/new', methods=['GET', 'POST'])
def createRestaurant():
    if request.method == 'POST':
        new_restaurant = Restaurant(name=request.form['restaurant-name'])
        session.add(new_restaurant)
        flash('New Restaurant %s Successfully Created' % new_restaurant.name)
        session.commit()
        return redirect(url_for('newMenuItem', restaurant_id=new_restaurant.id))
    else:
        return render_template('newRestaurant.html')



@app.route('/restaurants/<int:restaurant_id>/edit', methods=['GET', 'POST'])
def editRestaurant(restaurant_id):
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    context = {'restaurant_name': restaurant.name}

    if request.method == 'POST':
        restaurant.name = request.form['restaurant-name']
        context['restaurant_name'] = restaurant.name
        message = 'Restaurant info has been successfully edited'
        flash(message)

    return render_template('editrestaurant.html', context=context)


@app.route('/restaurants/<int:restaurant_id>/delete', methods=['GET', 'POST'])
def deleteRestaurant(restaurant_id):
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    context = {'restaurant_name': restaurant.name}

    if request.method == 'POST':
        session.delete(restaurant)
        message = '%s has been deleted' % restaurant.name
        flash(message)

        return redirect(url_for('showRestaurants'))

    return render_template('deleterestaurant.html', context=context)


@app.route('/restaurants/<int:restaurant_id>')
@app.route('/restaurants/<int:restaurant_id>/menu')
def showMenu(restaurant_id):
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    menu_items = session.query(MenuItem).filter_by(restaurant_id=restaurant_id).all()

    context = {
        'restaurant': restaurant,
        'menu_items': menu_items
    }

    return render_template('menu.html', context=context)


@app.route('/restaurants/<int:restaurant_id>/menu/new', methods=['GET', 'POST'])
def newMenuItem(restaurant_id):
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    # message = 'Creating a new menu item for restaurant %s' % restaurant.name
    # flash(message)
    context = {'restaurant_id': restaurant_id}

    if request.method == 'POST':
        menu_item = MenuItem(
            name=request.form['menu-item-name'],
            course=request.form['menu-item-course'],
            price=request.form['menu-item-price'],
            description=request.form['menu-item-description'],
            restaurant_id=restaurant_id,
            restaurant=restaurant
        )
        session.add(menu_item)
        session.commit()
        message = 'A new menu item %s has been created' % menu_item.name
        flash(message)

        return redirect(url_for('showMenu', restaurant_id=restaurant_id))

    return render_template('newmenuitem.html', context=context)


@app.route('/restaurants/<int:restaurant_id>/menu/<int:menu_id>/edit', methods=['GET', 'POST'])
def editMenuItem(restaurant_id, menu_id):
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    menu_item = session.query(MenuItem).filter_by(id=menu_id).one()

    context = {
        "restaurant": restaurant,
        "menu_id": menu_id,
        "menu_item": menu_item
    }

    if request.method == 'POST':
        menu_item.name = request.form['menu-item-name']
        menu_item.course = request.form['menu-item-course']
        menu_item.price = request.form['menu-item-price']
        menu_item.description = request.form['menu-item-description']

        message = "Menu item %s has been updated." % menu_item.name
        flash(message)

    return render_template('editmenuitem.html', context=context)


@app.route('/restaurants/<int:restaurant_id>/menu/<int:menu_id>/delete', methods=['GET', 'POST'])
def deleteMenuItem(restaurant_id, menu_id):
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    menu_item = session.query(MenuItem).filter_by(id=menu_id).one()

    if request.method == 'POST':
        session.delete(menu_item)
        message = 'Menu item %s has been deleted' % menu_item.name
        flash(message)

        return redirect(url_for('showMenu', restaurant_id=restaurant.id))

    else:
        context = {
            "restaurant": restaurant,
            "menu_item": menu_item
        }
        return render_template('deletemenuitem.html', context=context)


if __name__ == '__main__':
    app.secret_key = 'super_key'
    app.debug = True
    app.run(host='localhost', port=5001)
