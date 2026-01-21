from django.db import models
# Create your models here.
class User(models.Model):
    username = models.CharField(max_length=20)
    password = models.CharField(max_length=20)  
    email = models.CharField(max_length=20)
   
    def __str__(self):
        return self.username
class Restaurant(models.Model):
    name = models.CharField(max_length=20)
    picture = models.URLField(max_length=200, default='https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQQRhJSirkfYAti_IFEQkRqqYbS-IRQBYzo_g&s')
    cuisine = models.CharField(max_length=200)
    rating = models.FloatField()

class Item(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete= models.CASCADE, related_name="items")
    name = models.CharField(max_length=20)
    description= models.CharField(max_length=200)
    price = models.FloatField()
    vegeterian = models.BooleanField(default=False)
    picture = models.URLField(max_length=400, default= "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRWm05BLD7_9PXFVRIjDQ9u_-f3ZL98O651aw&s")

class Cart(models.Model):
    customer = models.ForeignKey(User, on_delete=models.CASCADE)
    def total_price(self):
       return sum(ci.item.price * ci.quantity for ci in getattr(self, 'cart_items', []).all())

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="cart_items")
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = "delivery_cart_items"   # 🔥 IMPORTANT
        unique_together = ("cart", "item")
