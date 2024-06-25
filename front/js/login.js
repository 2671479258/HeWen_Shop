var vm = new Vue({
    el: '#app',
    data: {


        password: '',

        mobile: '',


    },

    methods: {

        check_pwd: function () {
            var len = this.password.length;
            if (len < 8 || len > 20) {
                this.error_password = true;
            } else {
                this.error_password = false;
            }
        },
        check_cpwd: function () {
            if (this.password != this.password2) {
                this.error_check_password = true;
            } else {
                this.error_check_password = false;
            }
        },

        on_submit: function () {

               axios.post('http://127.0.0.1:8000/login/', {
                mobile: this.mobile,
                   password:this.password
            }, {
                    responseType: 'json',
                    withCredentials:true,
                })
                    .then(response => {
    if (response.data.code==0) {
       location.href = 'index.html';
    }
    if (response.data.code == 400) {
        alert(response.data.errmsg)
    }
})


        }
    }
});