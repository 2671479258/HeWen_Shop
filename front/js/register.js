var vm = new Vue({
    el: '#app',
    data: {

        username: '',
        password: '',
        password2: '',
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
            console.log(this.username)
            console.log(this.mobile)
            // this.check_pwd();
            // this.check_cpwd();

               axios.post('http://127.0.0.1:8000/register/', {
                username: this.username,
                password: this.password,
                password2: this.password2,
                mobile: this.mobile
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