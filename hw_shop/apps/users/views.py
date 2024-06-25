import json
import re

from django.contrib.auth import login, authenticate, logout
from django.http import JsonResponse
from django.shortcuts import render
from users.models import User, Address
# Create your views here.
from django.views import View

from utils.views import LoginRequiredJSONMixin


class RegisterView(View):
    def post(self, request):

        body_bytes = request.body

        body_dict = json.loads(body_bytes)

        username = body_dict.get('username')
        password = body_dict.get('password')
        password2 = body_dict.get('password2')
        mobile = body_dict.get('mobile')

        try:
            user = User(username=username, mobile=mobile)
            user.set_password(password)  # 设置密码明文
            user.save()
        except Exception as e:
            print(e)
            return JsonResponse({'code': 400, 'errmsg': '注册失败'})

        login(request,user)

        return JsonResponse({'code': 0, 'errmsg': 'ok'})

class LoginView(View):
    def post(self,request):
        data=json.loads(request.body)
        mobile=data.get('mobile')
        password=data.get('password')
        user=User.objects.all().first()


        print(user)
        if not all(['mobile','password']):
            return JsonResponse({'code':400,'errmsg':'参数不全'})




        response=JsonResponse({'code':0,'errmsg':'ok'})
        print('成功')
        response.set_cookie('mobile',mobile,max_age=3600*24*15)
        return response


class LogoutView(View):
    def delete(self,request):
        logout(request)

        response=JsonResponse({'code':400,'errmsg':'ok'})
        response.delete_cookie('mobile')

        return response

from orders.models import OrderInfo,OrderGoods
class MyOrder(View):
    def get(self, request):
        # 检查用户是否登录
        if not request.user.is_authenticated:
            return JsonResponse({'error': '用户未登录'})

        # 获取当前登录用户的订单信息
        user_id = request.user.id
        user_orders = OrderInfo.objects.filter(user_id=user_id)

        # 构造订单信息的字典列表
        orders_data = []
        for order in user_orders:
            order_data = {
                'order_id': order.order_id,
                'user_id': order.user_id,
                'total_count': order.total_count,
                'total_amount': float(order.total_amount),
                'freight': float(order.freight),
                'pay_method': order.get_pay_method_display(),
                'status': order.get_status_display(),
                'province':order.address.province.name,
                'city': order.address.city.name,
                'district': order.address.district.name,
                'address':order.address.place,
                # 添加其他订单信息字段
            }

            # 获取订单商品信息
            order_goods = OrderGoods.objects.filter(order=order)
            goods_data = []
            for order_good in order_goods:
                goods_data.append({
                    'sku_id': order_good.sku_id,
                    'count': order_good.count,
                    'price': float(order_good.price),
                    'name': order_good.sku.name,
                    'url': order_good.sku.default_image.url  # 获取图片的URL字符串

                    # 添加其他订单商品信息字段
                })

            order_data['goods'] = goods_data
            orders_data.append(order_data)

        # 返回订单信息的JSON响应
        return JsonResponse({'orders': orders_data})


class confirmDelivery(View):
    def post(self, request):
        # 解析请求体中的 JSON 数据
        data = json.loads(request.body)
        order_id = data.get('orderId')
        if not order_id:
            return JsonResponse({'message': '订单号不能为空'}, status=400)

        # 查询订单
        try:
            order = OrderInfo.objects.get(order_id=order_id)
        except OrderInfo.DoesNotExist:
            return JsonResponse({'message': '订单不存在'}, status=404)

        # 更新订单状态为已完成
        order.status = OrderInfo.ORDER_STATUS_ENUM['FINISHED']
        order.save()

        return JsonResponse({'message': '确认收货成功'}, status=200)




class AddressCreateView(LoginRequiredJSONMixin,View):
    def post(self,request):
        user=request.user
        data=json.loads(request.body)

        receiver = data.get('receiver')
        province_id = data.get('province_id')
        city_id = data.get('city_id')
        district_id = data.get('district_id')
        place = data.get('place')
        mobile = data.get('mobile')
        tel = data.get('tel')
        email = data.get('email')

        # 4. 验证参数
        if not all([receiver, province_id, city_id, district_id, place, mobile]):
            return JsonResponse({'code': 400, 'errmsg': '缺少必传参数'})

        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return JsonResponse({'code': 400, 'errmsg': '参数mobile错误'})

        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return JsonResponse({'code': 400, 'errmsg': '参数tel有误'})

        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return JsonResponse({'code': 400, 'errmsg': '参数email有误'})


            try:
                address = Address.objects.create(
                        # 外键 需要保存用户实例对象 而不是一个具体的值
                        user=user,
                        title=receiver,
                        receiver=receiver,
                        province_id=province_id,
                        city_id=city_id,
                        district_id=district_id,
                        place=place,
                        mobile=mobile,
                        tel=tel,
                        email=email
                    )
            except Exception as e:
                print(e)
                return JsonResponse({'code': 400, 'errmsg': '数据库入库出错'})


            address_dict = {
            'id': address.id,
            'title': address.title,
            "receiver": address.receiver,
            "province": address.province.name,
            "city": address.city.name,
            "district": address.district.name,
            "place": address.place,
            "mobile": address.mobile,
            "tel": address.tel,
            "email": address.email
        }


            return JsonResponse({'code': 0, 'errmsg': 'ok', 'address': address_dict})


class ShowAddress(LoginRequiredJSONMixin, View):
    def get(self, request):
        # 1. 获取当前登录用户的所有地址
        addresses = Address.objects.filter(user=request.user, is_deleted=False)

        # 2. 创建一个空的列表
        address_dict_list = []

        # 3. 对当前查询的结果集进行遍历
        for address in addresses:
            # 创建一个字典
            address_dict = dict(
                id=address.id,
                title=address.title,
                receiver=address.receiver,
                province=address.province.name,
                city=address.city.name,
                district=address.district.name,
                place=address.place,
                mobile=address.mobile,
                tel=address.tel,
                email=address.email
            )
            address_dict_list.append(address_dict)

        return JsonResponse({'code': 0, 'errmsg': 'ok', 'addresses': address_dict_list})


# 数据更新
class UpdateAddressView(LoginRequiredJSONMixin, View):
    def put(self, request, address_id):
        # 1. 接收参数
        json_dict = json.loads(request.body)
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')

        # 校验地址
        if not all([receiver, province_id, city_id, district_id, place, mobile]):
            return JsonResponse({'code': 400, 'errmsg': '缺少必传参数'})

        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return JsonResponse({'code': 400, 'errmsg': '参数mobile错误'})

        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return JsonResponse({'code': 400, 'errmsg': '参数tel有误'})

        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return JsonResponse({'code': 400, 'errmsg': '参数email有误'})

        # 在修改前 需要判断当前地址是否存在
        try:
            Address.objects.filter(id=address_id).update(
                user=request.user,
                title=receiver,
                receiver=receiver,
                province_id=province_id,
                city_id=city_id,
                district_id=district_id,
                place=place,
                mobile=mobile,
                tel=tel,
                email=email
            )

        except Exception as e:
            print(e)
            return JsonResponse({'code': 400, 'errmsg': '更新地址失败'})

        # 构造响应数据
        address = Address.objects.get(id=address_id)
        address_dict = dict(
            id=address.id,
            title=address.title,
            receiver=address.receiver,
            province=address.province.name,
            city=address.city.name,
            district=address.district.name,
            place=address.place,
            mobile=address.mobile,
            tel=address.tel,
            email=address.email

        )

        return JsonResponse({'code': 0, 'errmsg': 'ok', 'address': address_dict})

    def delete(self, request, address_id):
        # 1. 查询需要删除的地址
        try:
            address = Address.objects.get(id=address_id)

            # 2. 进行逻辑删除并保存当前删除状态
            address.is_deleted = True
            address.save()
        except Exception as e:
            print(e)
            return JsonResponse({'code': 400, 'errmsg': '删除地址失败'})

        # 3. 响应
        return JsonResponse({'code': 0, 'errmsg': 'ok'})

