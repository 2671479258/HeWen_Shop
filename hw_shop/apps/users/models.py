from django.db import models
from utils.models import BaseModel
# Create your models here.
from django.contrib.auth.models import AbstractUser

from django.contrib.auth.models import Group, Permission

class User(AbstractUser):
    mobile = models.CharField(max_length=11, unique=True)
    real_name = models.CharField(max_length=10, null=True, verbose_name='真实姓名')
    groups = models.ManyToManyField(Group, related_name='user_groups')
    user_permissions = models.ManyToManyField(Permission, related_name='user_permissions')
    default_address = models.ForeignKey('Address', related_name='users', null=True, blank=True,
                                        on_delete=models.SET_NULL, verbose_name='默认地址')


    class Meta:
        app_label = 'users'
        db_table = 'users_tb'
        verbose_name = '用户管理'
        verbose_name_plural = verbose_name

    def set_password(self, raw_password):
        # 存储密码为明文形式
        self.password = raw_password

    def check_password(self, raw_password):
        # 直接比较密码明文
        return self.password == raw_password

    def save(self, *args, **kwargs):
        # 如果需要保存实例时进行其他操作，可以在这里添加
        super().save(*args, **kwargs)

    def __str__(self):
        return self.real_name


# 地址模型
class Address(BaseModel):
    """用户地址"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses', verbose_name='用户')
    title = models.CharField(max_length=20, verbose_name='地址名称')
    receiver = models.CharField(max_length=20, verbose_name='收货人')
    # PROTECT 当前字段受保护 不允许删除
    province = models.ForeignKey('areas.Area', on_delete=models.PROTECT, related_name='province_addresses', verbose_name='省')
    city = models.ForeignKey('areas.Area', on_delete=models.PROTECT, related_name='city_addresses', verbose_name='市')
    district = models.ForeignKey('areas.Area', on_delete=models.PROTECT, related_name='district_addresses', verbose_name='区')
    place = models.CharField(max_length=50, verbose_name='地址')
    mobile = models.CharField(max_length=11, verbose_name='手机')
    tel = models.CharField(max_length=20, null=True, blank=True, default='', verbose_name='固定电话')
    email = models.CharField(max_length=30, null=True, blank=True, default='', verbose_name='电子邮箱')
    is_deleted = models.BooleanField(default=False, verbose_name='逻辑删除')

    class Meta:
        db_table = 'tb_address'
        verbose_name = '用户地址'
        verbose_name_plural = verbose_name
        ordering = ['-update_time']