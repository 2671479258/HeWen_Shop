var vm = new Vue({
    el: '#app2',
    delimiters: ['[[', ']]'], // 修改vue模板符号，防止与django冲突
    data: {



        cat: '', // 当前商品类别
        page: 1, // 当前页数
        page_size: 4, // 每页数量
        ordering: '-create_time', // 排序
        count: 0,  // 总数量
        skus: [], // 数据
        cat1: {url: '',name:''},  // 一级类别
        cat2: {name:''},  // 二级类别
        cat3: {name:''},  // 三级类别,
        cart_total_count: 0, // 购物车总数量
        carts: [], // 购物车数据
        hot_skus:[] // 热销商品,
    },
    computed: {
        total_page: function() {
            return this.count; // This should probably return the actual total page count instead of 'count'
        },
        next: function() {
            if (this.page >= this.total_page) {
                return 0;
            } else {
                return this.page + 1;
            }
        },
        previous: function() {
            if (this.page <= 0) {
                return 0;
            } else {
                return this.page - 1;
            }
        },
        page_nums: function() {
            var nums = [];
            if (this.total_page <= 5) {
                for (var i = 1; i <= this.total_page; i++) {
                    nums.push(i);
                }
            } else if (this.page <= 3) {
                nums = [1, 2, 3];
            } else if (this.total_page - this.page <= 2) {
                for (var i = this.total_page; i > this.total_page - 5; i--) {
                    nums.push(i);
                }
            } else {
                for (var i = this.page - 2; i < this.page + 3; i++) {
                    nums.push(i);
                }
            }
            return nums;
        }
    },

    mounted: function(){
        this.cat = this.get_query_string('cat');
        console.log(this.cat)
        this.get_skus();
            document.getElementById('comprehensive').style.color = 'red';


    },
    methods: {
        // 点击页数
        on_page: function(num){
            if (num != this.page){
                this.page = num;
                this.get_skus();
            }
        },
    get_query_string: function(name){
            var reg = new RegExp('(^|&)' + name + '=([^&]*)(&|$)', 'i');
            var r = window.location.search.substr(1).match(reg);
            if (r != null) {
                return decodeURI(r[2]);
            }
            return null;
        },
        // 请求商品数据
        get_skus: function(){
var url = 'http://127.0.0.1:8000' + '/list/' + this.cat + '/skus/';
            console.log(this.page)
            axios.get(url, {
                    params: {
                        page: this.page,
                        page_size: this.page_size,
                        ordering: this.ordering
                    },
                    responseType: 'json',
                    withCredentials:true
                })
                .then(response => {
                    this.count = response.data.count;
                    this.skus = response.data.list;
                    // 面包屑效果需要用的数据:
                    this.cat1.name = response.data.breadcrumb.cat1;
                    this.cat2.name = response.data.breadcrumb.cat2;
                    console.log(this.cat1.name)

                    for(var i=0; i<this.skus.length; i++){
                        this.skus[i].url = '/goods/' + this.skus[i].id + ".html";
                    }
                })
                .catch(error => {
                    console.log(error);
                })
        },
on_sort: function(ordering) {
    if (ordering != this.ordering) {
        this.ordering = ordering;
        // 先将所有链接设置为黑色
        document.getElementById('comprehensive').style.color = 'black';
        document.getElementById('price').style.color = 'black';
        document.getElementById('stock').style.color = 'black';
         document.getElementById('sales').style.color = 'black';
        // 根据点击的链接设置对应的颜色为红色
        if (ordering == '-create_time') {
            document.getElementById('comprehensive').style.color = 'red'; // 设置综合颜色为红色
        } else if (ordering == 'price') {
            document.getElementById('price').style.color = 'red'; // 设置价格颜色为红色
        } else if (ordering == 'stock') {
            document.getElementById('stock').style.color = 'red'; // 设置库存颜色为红色
        }else if (ordering == 'sales') {
            document.getElementById('sales').style.color = 'red'; // 设置库存颜色为红色
        }
        this.get_skus();
    }
}


    }
});