from django.shortcuts import render,redirect
from django.http import HttpResponse, JsonResponse
from .models import *
import json
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.urls import reverse
from django.shortcuts import get_object_or_404
from django.utils.html import escape  
from django.http import Http404
from django.contrib.auth.decorators import login_required
# Create your views here.
#detail
@login_required
def add_review(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        content = request.POST.get('content')
        # Kiểm tra người dùng có đơn hàng thành công với sản phẩm không
        has_ordered_product = OrderItem.objects.filter(
            product=product,
            order__customer=request.user,
            order__complete=True  # Giả sử 'complete=True' là điều kiện "thành công"
        ).exists()

        if not has_ordered_product:
            messages.error(request, 'Bạn chỉ có thể đánh giá sản phẩm sau khi đã đặt hàng thành công.')
            return redirect('detail', id=product.id)

        if content:
            Review.objects.create(product=product, customer=request.user, content=content)
            messages.success(request, 'Đánh giá của bạn đã được thêm!')
        else:
            messages.error(request, 'Vui lòng nhập nội dung đánh giá.')

    return redirect('detail', id=product.id)

def place_order(request):
    if request.method == 'POST':
        address = request.POST.get('address')
        mobile = request.POST.get('mobile')
        payment_method = request.POST.get('payment_method')

        # Tạo đơn hàng mới trước để có biến `order`
        order = Order.objects.create(
            customer=request.user,
            payment_method=payment_method,
            complete=False
        )

        # Chuyển OrderItem từ các đơn chưa hoàn tất khác (trừ đơn mới tạo) sang đơn mới
        old_orders = Order.objects.filter(customer=request.user, complete=False).exclude(id=order.id)

        for old_order in old_orders:
            for item in old_order.orderitem_set.all():
                item.order = order
                item.save()
            old_order.delete()  # Xóa các đơn cũ sau khi chuyển Item

        # Tạo địa chỉ giao hàng
        ShippingAddress.objects.create(
            customer=request.user,
            order=order,
            address=address,
            mobile=mobile
        )

        # Tạo các sản phẩm trong đơn hàng từ session cart
        cart_items = request.session.get('cart', {})
        for product_id, quantity in cart_items.items():
            try:
                product = Product.objects.get(id=product_id)

                # Nếu sản phẩm đã tồn tại trong OrderItem (do chuyển từ đơn cũ), cập nhật số lượng
                existing_item = OrderItem.objects.filter(order=order, product=product).first()
                if existing_item:
                    existing_item.quantity += int(quantity)
                    existing_item.save()
                else:
                    OrderItem.objects.create(order=order, product=product, quantity=int(quantity))
            except Product.DoesNotExist:
                continue

        # Kiểm tra nếu đơn hàng không có sản phẩm, xóa đơn hàng
        order_items = order.orderitem_set.all()
        if not order_items:
            order.delete()  # Xóa đơn hàng nếu không có sản phẩm

        # Đánh dấu đơn hàng là hoàn tất
        order.complete = True
        order.save()

        # Làm sạch giỏ hàng
        request.session['cart'] = {}

        messages.success(request, "Đơn hàng của bạn đã được đặt thành công!")
        return redirect(reverse('order_success', kwargs={'order_id': order.id}))

    return redirect('checkout')


def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    categories = Category.objects.filter(is_sub=False)
    
    if not order.complete:
        raise Http404("Đơn hàng chưa hoàn tất.")

    order_items = order.orderitem_set.all()

    # Lấy số lượng sản phẩm trong giỏ hàng
    if request.user.is_authenticated:
        customer = request.user
        current_order, created = Order.objects.get_or_create(customer=customer, complete=False)
        cartItems = current_order.get_cart_items
    else:
        cartItems = 0

    return render(request, 'sales/order_success.html', {
        'categories': categories,
        'order': order,
        'order_items': order_items,
        'cartItems': cartItems,  # Truyền số lượng sản phẩm vào context
    })


@login_required
def order_list(request):
    orders = Order.objects.filter(customer=request.user).order_by('-id')
    categories = Category.objects.filter(is_sub=False)

    # Lấy số lượng sản phẩm trong giỏ hàng
    customer = request.user
    current_order, created = Order.objects.get_or_create(customer=customer, complete=False)
    cartItems = current_order.get_cart_items

    context = {
        'categories': categories,
        'orders': orders,
        'cartItems': cartItems,  # Truyền số lượng sản phẩm vào context
    }
    return render(request, 'sales/order_list.html', context)


def detail(request,id):
    if request.user.is_authenticated:
        customer = request.user
        order, created = Order.objects.get_or_create(customer = customer, complete = False)
        items = order.orderitem_set.all()
        cartItems = order.get_cart_items
    else:
        items = []
        order = {'get_cart_items':0, 'get_cart_total':0}
        cartItems = order['get_cart_items']
    
    products = Product.objects.filter(id=id)
    categories = Category.objects.filter(is_sub=False)
    context={'products':products,'categories':categories,'items':items, 'order':order, 'cartItems': cartItems}
    return render(request, 'sales/detail.html', context)


def category(request):
    categories = Category.objects.filter(is_sub=False)
    active_category = request.GET.get('category', '')
    if active_category:
        products = Product.objects.filter(category__slug=active_category)

    if request.user.is_authenticated:
        customer = request.user
        order, created = Order.objects.get_or_create(customer=customer, complete=False)
        items = order.orderitem_set.all()
        cartItems = order.get_cart_items
    else:
        items = []
        order = {'get_cart_items': 0, 'get_cart_total': 0}
        cartItems = order['get_cart_items']

    context = {
        'categories': categories,
        'products': products,
        'active_category': active_category,
        'cartItems': cartItems
    }
    return render(request, 'sales/category.html', context)


def search(request):
    if request.method == "POST":
        searched = request.POST["searched"]
        # Sử dụng icontains để tìm kiếm không phân biệt chữ hoa chữ thường
        keys = Product.objects.filter(name__icontains=searched)
        
    if request.user.is_authenticated:
        customer = request.user
        order, created = Order.objects.get_or_create(customer=customer, complete=False)
        items = order.orderitem_set.all()
        cartItems = order.get_cart_items
    else:
        items = []
        order = {'get_cart_items': 0, 'get_cart_total': 0}
        cartItems = order['get_cart_items']

    categories = Category.objects.filter(is_sub=False)
    products = Product.objects.all()
    
    return render(request, 'sales/search.html', {
        "categories": categories,
        "searched": searched,
        "keys": keys,
        'products': products,
        'cartItems': cartItems
    })


def register(request):
    if request.user.is_authenticated:
        user_not_login = "hidden"
        user_login = "show"
    else:
        user_not_login = "show"
        user_login = "hidden"

    if request.method == "POST":
        form = CreateUserForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Bạn đã đăng ký thành công!')
            return redirect('login')
    else:
        form = CreateUserForm()  # chỉ tạo form rỗng khi không có POST

    context = {
        'form': form,
        'user_not_login': user_not_login,
        'user_login': user_login
    }
    return render(request, 'sales/register.html', context)


def loginPage(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method =="POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'Bạn đã đăng nhập thành công!')
            return redirect('home')
        else: messages.info(request, 'user or password not correct!')
    user_not_login = "show"
    user_login = "hidden"
    context={'user_not_login': user_not_login, 'user_login': user_login}
    return render(request, 'sales/login.html', context)

def logoutPage(request):
    logout(request)  
    return redirect('login')

def home(request):
    if request.user.is_authenticated:
        customer = request.user
        order, created = Order.objects.get_or_create(customer = customer, complete = False)
        items = order.orderitem_set.all()
        cartItems = order.get_cart_items
    else:
        items = []
        order = {'get_cart_items':0, 'get_cart_total':0}
        cartItems = order['get_cart_items']
    categories = Category.objects.filter(is_sub=False)
    products = Product.objects.all()
    context={'categories':categories,'products': products, 'cartItems': cartItems}
    return render(request, 'sales/home.html', context)

def cart(request):
    if request.user.is_authenticated:
        customer = request.user
        order, created = Order.objects.get_or_create(customer = customer, complete = False)
        items = order.orderitem_set.all()
        cartItems = order.get_cart_items
    else:
        items = []
        order = {'get_cart_items':0, 'get_cart_total':0}
        cartItems = order['get_cart_items']
        
    for item in items:
        item.total = item.product.price * item.quantity

    categories = Category.objects.filter(is_sub=False)
    context={'categories':categories,'items':items, 'order':order, 'cartItems': cartItems}
    return render(request, 'sales/cart.html', context)

def checkout(request):
    if request.user.is_authenticated:
        customer = request.user
        order, created = Order.objects.get_or_create(customer = customer, complete = False)
        items = order.orderitem_set.all()
        cartItems = order.get_cart_items
    else:
        items = []
        order = {'get_cart_items':0, 'get_cart_total':0}
        cartItems = order['get_cart_items']

    categories = Category.objects.filter(is_sub=False)
    context={'categories':categories,'items':items, 'order':order, 'cartItems': cartItems}
    return render(request, 'sales/checkout.html', context)

def updateItem(request):
    data = json.loads(request.body)
    productId = data['productId']
    action = data['action']
    customer = request.user
    product = Product.objects.get(id = productId)
    order, created = Order.objects.get_or_create(customer = customer, complete = False)
    orderItem, created = OrderItem.objects.get_or_create(order = order, product = product)
    if action =='add':
        orderItem.quantity +=1
    elif action =='remove':
        orderItem.quantity -=1
    orderItem.save()
    if orderItem.quantity<=0:
        orderItem.delete()
    return JsonResponse('added', safe=False)



