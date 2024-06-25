import json
import pickle
import base64
from django.http import JsonResponse
from django.views import View
from django_redis import get_redis_connection
from django.shortcuts import render
from goods.models import SKU

'''
显示购物车页面数据的思路分析：
    1. 判断用户是否登录
    2. 登录用户查询redis
        1. 连接redis
        2. hash 数据操作
        3. set 数据操作
        4. 遍历数据 需要将redis存储的数据组织成字典数据 因为cookie数据为一个字典
        5. 根据商品id查询商品数据 mysql进行查询的
        6. 将查询出来的结果集转成字典
        7. 返回响应
    3. 未登录用户查询cookie
        1. 读取cookie数据
        2. 判断是否存在购物车数据
            如果存在购物车数据 需要对当前的cookie数据进行解密[解码]
            如果不存在购物车数据 则初始化一个空字典
        3. 根据商品id进行查询
        4. 将查询结果集转为字典
        5. 返回响应
'''

class CartsView(View):
    # 展示购物车数据
    def get(self, request):
        # 获取用户信息
        user = request.user
        # 判断当前用户是否登录
        if user.is_authenticated:
            # 连接redis
            redis_cli = get_redis_connection('carts')
            # 获取redis中的购物车数据
            redis_cart = redis_cli.hgetall('carts_%s' % user.id)
            # 获取redis中的选中状态
            cart_selected = redis_cli.smembers('selected_%s' % user.id)

            # 将redis中的数据构造成cookie中的数据格式 方便统一查询
            cart_dict = {}
            for sku_id, count in redis_cart.items():
                # redis取出的数据一定要检查当前的数据类型
                # 将sku_id作为元素下标 如果作为元素下标 必须为int
                cart_dict[int(sku_id)] = {
                    # 在redis中取出数量值时需要将字节类型转为int类型
                    'count': int(count),
                    'selected': sku_id in cart_selected
                }
        else:
            cart_str = request.COOKIES.get('carts')
            # 判断当前是否存在cookie信息
            if cart_str:
                # 当前cookie信息进行解码
                cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
            else:
                # 如果没有cookie信息 则初始化一个新的空字典
                cart_dict = {}

        # 构造购物车页面的数据渲染
        sku_ids = cart_dict.keys()
        skus = SKU.objects.filter(id__in=sku_ids)
        # 初始化空列表
        cart_skus = []
        # 针对当前的orm查询的数据集进行遍历
        for sku in skus:
            cart_skus.append({
                'id': sku.id,
                'name': sku.name,
                'count': cart_dict.get(sku.id).get('count'),
                'selected': str(cart_dict.get(sku.id).get('selected')),
                'default_image_url': sku.default_image.url,
                'price': sku.price,
                'amount': (sku.price * cart_dict.get(sku.id).get('count')),
            })
        return JsonResponse({'code': 0, 'errmsg': 'ok', 'cart_skus': cart_skus})

    # 添加购物车
    def post(self, request):
        # 接收参数
        json_dict = json.loads(request.body)
        sku_id = json_dict.get('sku_id')
        count = json_dict.get('count')
        selected = json_dict.get('selected', True)

        # 判断参数是否齐全
        if not all([sku_id, count]):
            return JsonResponse({'code': 400, 'errmsg': '缺少必传参数'})
        # 判断sku_id是否存在
        try:
            SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return JsonResponse({'code': 400, 'errmsg': '商品不存在'})
        # 判断count是否为数字
        try:
            count = int(count)
        except Exception as e:
            print(e)
            return JsonResponse({'code': 400, 'errmsg': '参数count有误'})
        # 判断selected是否为bool值
        if selected:
            if not isinstance(selected, bool):
                return JsonResponse({'code': 400, 'errmsg': '参数selected有误'})
        # 匿名用户的is_authenticated=False
        user = request.user
        # 4. 数据入库
        if user.is_authenticated:
            # 4.1. 连接redis
            redis_cli = get_redis_connection('carts')
            # 4.2. 操作hash 如果直接操作hash表 那么会造成count值不变  因为在添加重复数据时会覆盖之前的count
            # 如果count为1 那么在商品详情页添加重复数据时 count值还会是为1

            # 所以需要更改累加方法 当前累加方法支持负数  如果减一个商品  当前代码会执行 count + (-1) 那么count就为0
            redis_cli.hincrby('carts_%s' % user.id, sku_id, count)
            # redis_cli.hset('carts_%s' % user.id, sku_id, count)
            # 4.3. 操作set 默认选中
            redis_cli.sadd('selected_%s' % user.id, sku_id)

            # 5. 返回响应
            return JsonResponse({'code': 0, 'errmsg': 'ok'})
        else:
            # 读取cookie数据
            cart_str = request.COOKIES.get('carts')
            # 如果用户操作过cookie购物车
            if cart_str:
                # 将cart_str转成bytes,再将bytes转成base64的bytes,最后将bytes转字典
                cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
            else:
                # 用户从没有操作过cookie购物车
                cart_dict = {}

            # 判断要加入购物车的商品是否已经在购物车中,如有相同商品，累加求和，反之，直接赋值
            if sku_id in cart_dict:
                # 累加求和
                origin_count = cart_dict[sku_id]['count']
                count += origin_count
            cart_dict[sku_id] = {
                'count': count,
                'selected': selected
            }
            # 将字典转成bytes,再将bytes转成base64的bytes,最后将bytes转字符串
            cookie_cart_str = base64.b64encode(pickle.dumps(cart_dict)).decode()

            # 创建响应对象
            response = JsonResponse({'code': 0, 'errmsg': '添加购物车成功'})
            # 响应结果并将购物车数据写入到cookie
            response.set_cookie('carts', cookie_cart_str, max_age=7 * 24 * 3600)
            return response

    '''
    1. 获取用户用户信息
    2. 获取需要更新的数据 前端传递的
    3. 接收数据
    4. 验证数据
    5. 更新数据
        登录用户更新redis
            1. 连接redis
            2. 更新hash
            3. 更新set
            4. 返回响应
        未登录用户更新cookie
            1. 读取cookie数据
                如果存在cookie则解密数据
                如果不存在则初始化空字典
            2. 更新数据
            3. 对当前字典数据进行base64编码
            4. 设置cookie信息
            5. 返回响应
    '''
    # 修改购物车
    def put(self, request):
        # 获取用户信息
        user = request.user
        # 接收数据
        data = json.loads(request.body)
        sku_id = data.get('sku_id')
        count = data.get('count')
        selected = data.get('selected', True)

        # 验证参数
        if not all([sku_id, count]):
            return JsonResponse({'code': 400, 'errmsg': '参数不全'})

        # 判断sku_id是否存在
        try:
            SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return JsonResponse({'code': 400, 'errmsg': '此商品不存在'})

        # 判断count是否为数字
        try:
            count = int(count)
        except Exception as e:
            print(e)
            # count = 1
            return JsonResponse({'code': 400, 'errmsg': '参数count有误'})

        # 判断当前用户是否登录
        if user.is_authenticated:
            # 连接redis
            redis_cli = get_redis_connection('carts')
            # 更新hash
            redis_cli.hset('carts_%s' % user.id, sku_id, count)
            # 更新set
            if selected:
                redis_cli.sadd('selected_%s' % user.id, sku_id)
            else:
                # 如果当前用户将选中状态改为false时 需要删除selected 集合中的选中状态数据
                redis_cli.srem('selected_%s' % user.id, sku_id)
            return JsonResponse({'code': 0, 'errmsg': 'ok', 'cart_sku': {'count': count, 'selected': selected}})
        else:
            # 读取cookie信息
            cookie_cart = request.COOKIES.get('carts')
            # 判断当前cookie数据是否存在
            if cookie_cart:
                carts = pickle.loads(base64.b64decode(cookie_cart))
            else:
                carts = {}

            # 更新数据
            if sku_id in carts:
                carts[sku_id] = {
                    'count': count,
                    'selected': selected
                }

            # 对当前cookie信息进行编码
            new_carts = base64.b64encode(pickle.dumps(carts))
            # 设置cookie
            response = JsonResponse({'code': 0, 'errmsg': 'ok', 'cart_sku': {'count': count, 'selected': selected}})
            response.set_cookie('carts', new_carts.decode(), max_age=7 * 24 * 3600)
            # 返回响应
            return response

    # 删除购物车
    def delete(self, request):
        # 获取数据
        json_dict = json.loads(request.body)
        sku_id = json_dict.get('sku_id')

        # 验证参数
        try:
            SKU.objects.get(pk=sku_id)
        except SKU.DoesNotExist:
            return JsonResponse({'code': 400, 'errmsg': '此商品不存在'})

        # 判断用户状态
        user = request.user
        if user.is_authenticated:
            # 连接redis
            redis_cli = get_redis_connection('carts')
            # 删除hash
            redis_cli.hdel('carts_%s' % user.id, sku_id)
            # 删除set
            redis_cli.srem('selected_%s' % user.id, sku_id)
            # 返回响应
            return JsonResponse({'code': 0, 'errmsg': 'ok'})
        else:
            # 获取cookie
            cookie_cart = request.COOKIES.get('carts')
            if cookie_cart:
                # 解码数据
                carts = pickle.loads(base64.b64decode(cookie_cart))
            else:
                carts = {}

            # 删除cookie
            del carts[sku_id]

            # cookie信息进行base64编码
            new_carts = base64.b64encode(pickle.dumps(carts))

            # 设置cookie
            response = JsonResponse({'code': 0, 'errmsg': 'ok'})
            response.set_cookie('carts', new_carts.decode(), max_age=7 * 24 * 3600)
            return response

class CartsSelectAllView(View):
    def put(self, request):
        # 接收参数
        json_dict = json.loads(request.body)
        selected = json_dict.get('selected', True)

        # 校验参数
        if selected:
            if not isinstance(selected, bool):
                return JsonResponse({'code': 400, 'errmsg': 'selected参数有误'})

        # 用户登录状态的判断
        user = request.user
        if user.is_authenticated:
            # 操作redis
            '''
            1. 连接redis 
            2. 获取数据
                hash
                set
            获取当前商品的sku_id
            3. 判断当前selected是否为全选状态  根据前端发送过来的状态值进行redis的选中状态的修改
                # 当前页面的商品全为选中状态
                # 当前页面的商品为未选中
                前端去控制的
            4. 返回响应    
            '''
            redis_cli = get_redis_connection('carts')
            cart = redis_cli.hgetall('carts_%s' % user.id)
            # 获取到页面中的所有的商品的id
            sku_id_list = cart.keys()
            # 判断当前前端页面中的商品选中状态
            if selected:
                # 修改redis中的商品的selected中的状态值
                redis_cli.sadd('selected_%s' % user.id, *sku_id_list)
            else:
                # 取消全选
                redis_cli.srem('selected_%s' % user.id, *sku_id_list)

            # 返回响应
            return JsonResponse({'code': 0, 'errmsg': '购物车全选/取消全选成功'})
        else:
            # 操作cookie
            '''
            获取cookie
            对cookie信息进行解码
            获取当前商品的全选状态
            针对当前全选状态的数据进行base64编码
            设置cookie
            返回响应
            '''
            cart = request.COOKIES.get('carts')
            # 构造返回对象
            response = JsonResponse({'code': 0, 'errmsg': '购物车全选/取消全选成功'})
            if cart is not None:
                # cookie 解码
                cart = pickle.loads(base64.b64decode(cart.encode()))
                for sku_id in cart:
                    cart[sku_id]['selected'] = selected

                # 对组织好的字典数据进行base64编码
                cookie_cart = base64.b64encode(pickle.dumps(cart)).decode()
                # 设置cookie
                response.set_cookie('carts', cookie_cart, max_age=7 * 24 * 3600)
            return response


class CartsSimpleView(View):
    def get(self, request):
        # 判断当前用户是否登录
        user = request.user
        if user.is_authenticated:
            # 登录用户查询redis
            redis_cli = get_redis_connection('carts')
            redis_cart = redis_cli.hgetall('carts_%s' % user.id)
            cart_selected = redis_cli.smembers('selected_%s' % user.id)

            # 因为redis数据结构与cookie数据结构不一致 所以需要重组
            cart_dict = {}
            for sku_id, count in redis_cart.items():
                cart_dict[int(sku_id)] = {
                    'count': int(count),
                    'selected': sku_id in cart_selected
                }
        else:
            # 用户未登录则查询cookie
            cart_str = request.COOKIES.get('carts')
            # 判断当前cookie是否为空
            if cart_str:
                # 解码
                cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
            else:
                cart_dict = {}

        # 构造购物车数据
        cart_skus = []
        sku_ids = cart_dict.keys()

        # 根据获取到的商品id进行商品数据查询
        skus = SKU.objects.filter(id__in=sku_ids)
        for sku in skus:
            cart_skus.append({
                'id': sku.id,
                'name': sku.name,
                'count': cart_dict.get(sku.id).get('count'),
                'default_image_url': sku.default_image.url
            })

        # 返回响应
        return JsonResponse({'code': 0, 'errmsg': 'ok', 'cart_skus': cart_skus})
