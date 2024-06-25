var vm = new Vue({
    el: '#app6',

    data: {
        Orders: []
    },

    mounted: function(){
        // 添加 axios 响应拦截器
        axios.interceptors.response.use(
            response => {
                return response;
            },
            error => {
                if (error.response && error.response.status === 401) {
                    alert('需要登录后才能查看，点击确定跳转登录界面');
                    window.location.href = 'http://127.0.0.1:8080/login.html';
                } else {
                    return Promise.reject(error);
                }
            }
        );

        // 获取订单列表
        this.fetchOrders();
    },

    methods: {
        fetchOrders() {
            axios.get('http://127.0.0.1:8000/myorder/', {
                responseType: 'json',
                withCredentials: true
            })
            .then(response => {
                this.Orders = response.data.orders;
            })
            .catch(error => {
                console.log(error.response.data);
            });
        },

        confirmDelivery(orderId) {
            axios.post('http://127.0.0.1:8000/confirm_delivery/', { orderId }, {
                withCredentials: true
            })
            .then(response => {
                // 更新订单状态
                this.updateOrderStatus(orderId);
            })
            .catch(error => {
                console.error('确认收货失败：', error);
            });
        },

        updateOrderStatus(orderId) {
            // 根据订单号更新订单状态为已完成
            this.Orders.forEach((order, index) => {
                if (order.order_id === orderId) {
                    // 使用 Vue.set 确保响应性
                    Vue.set(this.Orders, index, {
                        ...order,
                        status: '已完成'
                    });
                }
            });
        }
    }
});