from django.http import JsonResponse
from django.shortcuts import render
from django.views import View
from goods.models import GoodsCategory,SKU
# Create your views here.
from utils.goods import get_breadcrumb


class ListView(View):
    def get(self, request, category_id):
        # 1. 接收参数 排序规则 分页数量 当前页数
        ordering = request.GET.get('ordering')
        page_size = request.GET.get('page_size')
        page = request.GET.get('page')
        print(page_size)

        # 2. 获取分类id
        try:
            category = GoodsCategory.objects.get(id=category_id)
        except GoodsCategory.DoesNotExist:
            return JsonResponse({'code': 400, 'errmsg': '当前数据不存在'})

        # 3. 获取面包屑
        breadcrumb = get_breadcrumb(category)
        # 4. 查询分类数据对应的sku商品数据
        # skus = SKU.objects.filter(category=category, is_launched=True).order_by(ordering)
        skus = SKU.objects.filter(category=category, is_launched=True).order_by(ordering)
        # 分页
        from django.core.paginator import Paginator

        # 每页的数据量
        paginator = Paginator(skus, per_page=page_size)
        # 获取指定页面的数据
        page_skus = paginator.page(page)

        # 需要将获取到的查询数据集转成列表数据
        sku_list = []
        for sku in page_skus.object_list:
            sku_list.append({
                'id': sku.id,
                'name': sku.name,
                'price': sku.price,
                'default_image_url': "http://127.0.0.1:8080" + sku.default_image.url,
                'stock':sku.stock
            })

        print(sku_list)
        #
        # # 获取总页数
        total_num = paginator.num_pages

        # 返回响应
        return JsonResponse({
            'code': 0,
            'errmsg': 'ok',
            'breadcrumb': breadcrumb,
            'list': sku_list,
            'count': total_num

        })
