from django.shortcuts import render, get_object_or_404
from .models import  User, Restaurant, Item, Cart, CartItem
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
import razorpay
from django.conf import settings
from django.shortcuts import render, redirect
from django.db.models import Sum 
from django.http import JsonResponse

def index(request):
    return render(request, 'index.html')
def open_signin(request):
    return render(request, 'signin.html')
def open_signup(request):
    return render(request, 'signup.html')
def signup(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email')

        if User.objects.filter(username=username).exists():
           messages.error(request, "Username already exists")
           return redirect('open_signup')
        # Hash the password before saving
        hashed_password = make_password(password)
        user = User(username=username, password=hashed_password, email=email)
        user.save()

        return render(request, "signin.html") 
    else:
        messages.error(request, "Invalid request method")
        return redirect('open_signup')
from django.db.models import Sum

def signin(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        try:
            user = User.objects.get(username=username)
            if check_password(password, user.password):
                # Check for admin
                if username == 'admin' or username == 'ADMIN' or username == 'Admin':
                    # 1. Fetch the data from the database
                    total_res = Restaurant.objects.count()
                    total_itm = Item.objects.count()
                    
                    # 2. Calculate Revenue (Sum of all items currently in all carts)
                    from .models import CartItem
                    revenue_data = CartItem.objects.aggregate(total=Sum('item__price'))
                    total_rev = revenue_data['total'] or 0
                    
                    # 3. Pass the data to the template using a dictionary
                    return render(request, 'admin_home.html', {
                        "total_restaurants": total_res,
                        "total_items": total_itm,
                        "total_revenue": total_rev
                    })
                else:
                    # Customer logic
                    restaurantList = Restaurant.objects.all()
                    return render(request, 'customer_home.html', {
                        "restaurantList": restaurantList,
                        "username": username
                    })
            else:
                messages.error(request, "Invalid username or password")
                return redirect('open_signin')

        except User.DoesNotExist:
            messages.error(request, "Invalid username or password")
            return redirect('open_signin')
    else:
        return redirect('open_signin')
def open_add_restaurant(request):
    return render(request, 'add_restaurant.html')
def open_add_restaurant(request):
    return render(request, 'add_restaurant.html')
def add_restaurant(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        picture = request.POST.get('picture')
        cuisine = request.POST.get('cuisine')
        rating = request.POST.get('rating')

        if Restaurant.objects.filter(name=name).exists():
            messages.error(request, "Restaurant already exists")
            return redirect('open_add_restaurant')

        restaurant = Restaurant.objects.create(
            name=name,
            picture=picture,
            cuisine=cuisine,
            rating=rating,
        )
        
        # CHANGE THIS LINE:
        # Instead of going to the menu, go to the full list of restaurants
        return redirect('show_restaurant')

def show_restaurant(request):
    restaurantList = Restaurant.objects.all()
    return render(request, 'show_restaurants.html',{"restaurantList" : restaurantList})

def open_update_restaurant(request, restaurant_id):
    restaurant = Restaurant.objects.get(id = restaurant_id)
    return render(request, 'update_restaurant.html', {"restaurant" : restaurant})

def update_restaurant(request, restaurant_id):
    restaurant = Restaurant.objects.get(id = restaurant_id)
    if request.method == 'POST':
        name = request.POST.get('name')
        picture = request.POST.get('picture')
        cuisine = request.POST.get('cuisine')
        rating = request.POST.get('rating')
        
        restaurant.name = name
        restaurant.picture = picture
        restaurant.cuisine = cuisine
        restaurant.rating = rating

        restaurant.save()

    restaurantList = Restaurant.objects.all()
    return render(request, 'show_restaurants.html',{"restaurantList" : restaurantList})

def delete_restaurant(request, restaurant_id):
    restaurant = Restaurant.objects.get(id = restaurant_id)
    restaurant.delete()

    restaurantList = Restaurant.objects.all()
    return render(request, 'show_restaurants.html',{"restaurantList" : restaurantList})

def open_update_menu(request, restaurant_id):
    restaurant = Restaurant.objects.get(id = restaurant_id)
    itemList = restaurant.items.all()
    #itemList = Item.objects.all()
    return render(request, 'add_menu.html',{"itemList" : itemList, "restaurant" : restaurant})
def update_menu(request, restaurant_id):
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        price = request.POST.get('price')
        vegeterian = request.POST.get('vegeterian') == 'on'
        picture = request.POST.get('picture')
        
        # Create the new item
        Item.objects.create(
            restaurant=restaurant,
            name=name,
            description=description,
            price=price,
            vegeterian=vegeterian,
            picture=picture,
        )
        
        messages.success(request, f"Added {name} to the menu!")
        
        # CHANGE THIS LINE: 
        # Redirect back to the "Manage Menu" page instead of admin_home
        return redirect('open_update_menu', restaurant_id=restaurant.id)

    return render(request, 'admin_home.html')
def view_menu(request, restaurant_id, username):
    restaurant = Restaurant.objects.get(id = restaurant_id)
    itemList = restaurant.items.all()
    #return HttpResponse("Items collected")
    #itemList = Item.objects.all()
    return render(request, 'customer_menu.html'
                  ,{"itemList" : itemList,
                     "restaurant" : restaurant, 
                     "username":username})

def add_to_cart(request, item_id, username):
    user = get_object_or_404(User, username=username)
    item = get_object_or_404(Item, id=item_id)
    cart, created = Cart.objects.get_or_create(customer=user)
    # if cart is empty, remove any existing items (start fresh)
    if not cart.cart_items.exists():
        CartItem.objects.filter(cart=cart).delete()
    # now create the cart item
    cart_item, item_created = CartItem.objects.get_or_create(
        cart=cart,
        item=item
    )
    if not item_created:
        # increment quantity if the same item is added again
        cart_item.quantity += 1
    cart_item.save()
    return redirect('show_cart', username=username)

def show_cart(request, username):
    user = get_object_or_404(User, username=username)
    cart = get_object_or_404(Cart, customer=user)
    cart_items = cart.cart_items.all()  # instead of filtering manually
    total_price = sum(ci.item.price * ci.quantity for ci in cart_items)
    return render(request, 'cart.html', {
        'cart_items': cart_items,
        'total_price': total_price,
        'username': username
    })

def checkout(request, username):
    customer = get_object_or_404(User, username=username)
    cart = Cart.objects.filter(customer=customer).first()

    if not cart or not cart.cart_items.exists():
        messages.error(request, "Your cart is empty")
        return redirect('show_cart', username=username)

    cart_items = cart.cart_items.all()
    total_price = cart.total_price()

    client = razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )

    order = client.order.create({
        'amount': int(total_price * 100),
        'currency': 'INR',
        'payment_capture': 1
    })

    return render(request, 'checkout.html', {
        'username': username,
        'cart_items': cart_items,
        'total_price': total_price,
        'amount': int(total_price * 100),
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
        'order_id': order['id'],
    })

def delete_menu_item(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    restaurant_id = item.restaurant.id
    item_name = item.name
    item.delete()
    messages.success(request, f"'{item_name}' has been deleted.")
    return redirect('open_update_menu', restaurant_id=restaurant_id)
def update_menu_item(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    restaurant_id = item.restaurant.id

    if request.method == 'POST':
        item.name = request.POST.get('name')
        item.description = request.POST.get('description')
        item.price = request.POST.get('price')
        # Checkbox logic: 'on' if checked, else False
        item.vegeterian = request.POST.get('vegeterian') == 'on'
        item.picture = request.POST.get('picture')
        item.save()
        
        messages.success(request, f"Updated {item.name} successfully!")
        # Redirect back to the restaurant's full menu update page
        return redirect('open_update_menu', restaurant_id=restaurant_id)

    return render(request, 'update_single_menu_item.html', {'item': item})
def orders(request, username):
    customer = get_object_or_404(User, username=username)
    cart = Cart.objects.filter(customer=customer).first()

    # Use the related_name "cart_items" defined in your CartItem model
    cart_items = cart.cart_items.all() if cart else []
    total_price = cart.total_price() if cart else 0

    # Clear the cart after fetching its details (see point #2 below)
    if cart:
        cart.cart_items.all().delete() 

    return render(request, 'orders.html', {
        'username': username,
        'customer': customer,
        'cart_items': cart_items,
        'total_price': total_price,
    })

def update_cart_quantity(request, item_id, username):
    user = get_object_or_404(User, username=username)
    cart = get_object_or_404(Cart, customer=user)
    cart_item = get_object_or_404(CartItem, cart=cart, item_id=item_id)
    
    # Get action from request (increase or decrease)
    action = request.GET.get('action')
    
    if action == 'increase':
        cart_item.quantity += 1
    elif action == 'decrease':
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
        else:
            cart_item.delete()
            return JsonResponse({'status': 'removed'})
            
    cart_item.save()
    return JsonResponse({'status': 'updated', 'new_quantity': cart_item.quantity})

def remove_from_cart(request, item_id, username):
    user = get_object_or_404(User, username=username)
    cart = get_object_or_404(Cart, customer=user)
    CartItem.objects.filter(cart=cart, item_id=item_id).delete()
    # Redirect back to the cart page
    return redirect('show_cart', username=username)

def admin_home(request):
    total_restaurants = Restaurant.objects.count()
    total_items = Item.objects.count()
    revenue_data = CartItem.objects.aggregate(total=Sum('item__price'))
    total_revenue = revenue_data['total'] or 0
    return render(request, 'admin_home.html', {
        'total_restaurants': total_restaurants,
        'total_items': total_items,
        'total_revenue': total_revenue,
    })