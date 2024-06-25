var vm = new Vue({
    el: '#app',
    delimiters: ['[[', ']]'], // 修改vue模板符号，防止与django冲突
    data: {

        mobile: '',
    },
    mounted() {
        this.mobile = this.getCookie('mobile');
        console.log(this.mobile)
    },
    methods: {
    getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) {
            const cookieValue = parts.pop().split(';').shift();

            return cookieValue.trim(); // 返回去除空格后的 cookie 值
        }
    },
        logoutfunc: function () {
            var url = 'http://127.0.0.1:8000/logout/';
            axios.delete(url, {
                responseType: 'json',
                withCredentials:true,
            })
                .then(response => {
                    location.href = 'http://127.0.0.1:8080/login.html';
                })
                .catch(error => {
                    console.log(error.response);
                })
        },
}
});