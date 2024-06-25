import json
from datetime import datetime
from decimal import Decimal
from django.shortcuts import render
from django.views import View
from django.http import JsonResponse
from django.db import transaction

from users.models import Address
from utils.views import LoginRequiredJSONMixin
from django_redis import get_redis_connection
# from users.models import Address
from goods.models import SKU
from . import models


class OrderSettlementView(LoginRequiredJSONMixin, View):
    def get(self, request):
        # 获取用户信息
        user = request.user
        # 获取地址信息
        addresses = Address.objects.filter(user=request.user, is_deleted=False)
        # 查询选中的商品信息
        redis_conn = get_redis_connection('carts')
        redis_cart = redis_conn.hgetall('carts_%s' % user.id)
        cart_selected = redis_conn.smembers('selected_%s' % user.id)
        cart = dict()
        for sku_id in cart_selected:
            cart[int(sku_id)] = int(redis_cart[sku_id])

        # 查询商品信息
        sku_list = list()
        skus = SKU.objects.filter(id__in=cart.keys())
        for sku in skus:
            sku_list.append({
                'id': sku.id,
                'name': sku.name,
                'default_image_url': sku.default_image.url,
                'count': cart[sku.id],
                'price': sku.price
            })

        # 运费
        freight = Decimal('10.00')
        addresses_list = list()
        for address in addresses:
            addresses_list.append({
                'id': address.id,
                'province': address.province.name,
                'city': address.city.name,
                'district': address.district.name,
                'place': address.place,
                'receiver': address.receiver,
                'mobile': address.mobile
            })

        context = {
            'addresses': addresses_list,
            'skus': sku_list,
            'freight': freight
        }
        print(context)
        return JsonResponse({'code': 0, 'errmsg': 'ok', 'context': context})


class OrderCommitView(LoginRequiredJSONMixin, View):
    def post(self, request):
        # 接收请求
        json_dict = json.loads(request.body.decode())
        address_id = json_dict.get('address_id')
        pay_method = json_dict.get('pay_method')

        # 校验参数
        if not all([address_id, pay_method]):
            return JsonResponse({'code': 400, 'errmsg': '缺少必传参数'})
        # 判断address_id是否合法
        try:
            address = Address.objects.get(id=address_id)
        except Address.DoesNotExist:
            return JsonResponse({'code': 400, 'errmsg': '参数address_id错误'})
        # 判断pay_method是否合法
        if pay_method not in [models.OrderInfo.PAY_METHODS_ENUM['CASH'], models.OrderInfo.PAY_METHODS_ENUM['ALIPAY']]:
            return JsonResponse({'code': 400, 'errmsg': '参数pay_method错误'})

        """保存订单信息"""
        # 获取登录用户
        user = request.user
        # 生成订单编号：年月日时分秒+用户编号[9位]
        order_id = datetime.now().strftime('%Y%m%d%H%M%S') + ('%09d' % user.id)

        # 保存订单基本信息 使用事务的方式进行数据保存
        with transaction.atomic():
            # 事务起始点
            point = transaction.savepoint()

            # 暴力回滚
            try:
                order = models.OrderInfo.objects.create(
                    order_id=order_id,
                    user=user,
                    address=address,
                    total_count=0,
                    total_amount=Decimal('0'),
                    freight=Decimal('10.00'),
                    pay_method=pay_method,
                    status=models.OrderInfo.ORDER_STATUS_ENUM['UNPAID'] if pay_method ==
                                                                           models.OrderInfo.PAY_METHODS_ENUM[
                                                                               'ALIPAY'] else
                    models.OrderInfo.ORDER_STATUS_ENUM['UNSEND']
                )

                """保存商品信息"""
                redis_conn = get_redis_connection('carts')
                redis_cart = redis_conn.hgetall('carts_%s' % user.id)
                selected = redis_conn.smembers('selected_%s' % user.id)

                # 组织redis数据结构
                carts = dict()
                for sku_id in selected:
                    carts[int(sku_id)] = int(redis_cart[sku_id])

                # 遍历购物车中被勾选的商品信息
                sku_ids = carts.keys()
                for sku_id in sku_ids:
                    while True:
                        # 查询SKU信息
                        sku = SKU.objects.get(id=sku_id)
                        # 获取购物车对应的商品数量
                        sku_count = carts[sku.id]
                        # 商品数量大于库存数量返回错误信息, 并进行数据回滚
                        if sku_count > sku.stock:
                            # 事务回滚点
                            transaction.savepoint_rollback(point)
                            return JsonResponse({'code': 400, 'errmsg': '库存不足'})

                        # 模拟延迟
                        import time
                        time.sleep(1)

                        # SKU减少库存，增加销量
                        # sku.stock -= sku_count
                        # sku.sales += sku_count
                        # sku.save()

                        # 使用乐观锁完成超卖问题
                        old_stock = sku.stock
                        new_stock = sku.stock - sku_count
                        new_sales = sku.sales + sku_count
                        result = SKU.objects.filter(id=sku.id, stock=old_stock).update(stock=new_stock, sales=new_sales)
                        if not result:  # 如果result为0则表示数据已被修改
                            # 跳出本次循环
                            continue

                        # 保存商品信息
                        models.OrderGoods.objects.create(
                            order=order,
                            sku=sku,
                            count=sku_count,
                            price=sku.price,
                        )
                        # 更新订单信息中的总价和总数量
                        order.total_count += sku_count
                        order.total_amount += (sku_count * sku.price)

                        # 如果下单成功或者失败则跳出循环
                        break

                # 添加邮费和保存订单信息
                order.total_amount += order.freight
                order.save()
                # 事务提交点
                transaction.savepoint_commit(point)
            except Exception:
                # 下单失败返回事务起始点
                transaction.savepoint_rollback(point)
                return JsonResponse({'code': 400, 'errmsg': '下单失败'})

        # 清除购物车中已结算的商品
        pl = redis_conn.pipeline()
        pl.hdel('carts_%s' % user.id, *selected)
        pl.srem('selected_%s' % user.id, *selected)
        pl.execute()
        print('成功')
        # 响应提交订单结果
        return JsonResponse({'code': 0, 'errmsg': '下单成功', 'order_id': order.order_id})
