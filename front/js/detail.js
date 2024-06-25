var vm = new Vue({
    el: '#app3',
    delimiters: ['[[', ']]'],
    data: {
        host: 'http://127.0.0.1:8000',

        tab_content: {
            detail: true,
            pack: false,
            comment: false,
            service: false
        },
        sku_id: '',
        sku_count: 1,
        sku_price: price,
        cart_total_count: 0, // 购物车总数量
        carts: [], // 购物车数据
        cat: cat, // 商品类别


    },
    computed: {
        sku_amount: function(){

            return (this.sku_price * this.sku_count).toFixed(2);
        }
    },
    mounted: function(){
        this.get_sku_id();
        // 添加 axios 响应拦截器
        axios.interceptors.response.use(
            response => {
                return response;
            },
            error => {
                if (error.response && error.response.status === 401) {
                    alert('需要登录后才能加入购物车，即将跳转登录界面');
                    window.location.href = 'http://127.0.0.1:8080/login.html';
                } else {
                    return Promise.reject(error);
                }
            }
        );



    },
    methods: {
         get_sku_id: function(){
            var re = /^\/goods\/(\d+).html$/;
            this.sku_id = document.location.pathname.match(re)[1];

        },




        // 新增记录商品详情的访问量
        detail_visit(){
            if (this.sku_id) {
                var url = this.host + '/detail/visit/' + this.cat + '/';
                axios.post(url, {}, {
                    responseType: 'json',
                    withCredentials:true,
                })
                    .then(response => {
                        console.log(response.data);
                    })
                    .catch(error => {
                        console.log(error.response);
                    });
            }
        },
         // 退出登录按钮
        logoutfunc: function () {
            var url = this.host + '/logout/';
            axios.delete(url, {
                responseType: 'json',
                withCredentials:true,
            })
                .then(response => {
                    location.href = 'login.html';
                })
                .catch(error => {
                    console.log(error.response);
                })
        },


        get_sku_id: function(){
            var re = /^\/goods\/(\d+).html$/;
            this.sku_id = document.location.pathname.match(re)[1];
        },
        // 减小数值
        on_minus: function(){
            if (this.sku_count > 1) {
                this.sku_count--;
            }
        },
        // 减小数值
        on_addition: function(){
            if (this.sku_count < 20) {
                this.sku_count++;
            }
        },
         // 添加购物车
        add_cart: function(){
            var url = 'http://127.0.0.1:8000/carts/'
            axios.post(url, {
                    sku_id: parseInt(this.sku_id),
                    count: this.sku_count
                }, {
                    responseType: 'json',
                    withCredentials: true
                })
                .then(response => {
                    alert('添加购物车成功');
                    this.cart_total_count += response.data.count;
                })
                .catch(error => {
                    console.log(error);
                })
        },

    }
});