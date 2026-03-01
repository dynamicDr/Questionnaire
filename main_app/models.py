from django.db import models


class Group(models.Model):
    """团信息"""
    group_no = models.CharField('团号', max_length=64, unique=True, db_index=True)
    agency = models.CharField('地接社', max_length=128, blank=True)
    hotel = models.CharField('酒店', max_length=128, blank=True)
    region = models.CharField('地区', max_length=64, blank=True)
    people_count = models.PositiveIntegerField('人数', default=0)
    feedback_count = models.PositiveIntegerField('意见表回收数量', default=0)
    feedback_rate = models.CharField('回收率', max_length=32, blank=True)
    start_date = models.DateField('开始日期', null=True, blank=True)
    end_date = models.DateField('截止日期', null=True, blank=True)

    class Meta:
        db_table = 'questionnaire_group'
        verbose_name = '团'
        verbose_name_plural = '团'

    def __str__(self):
        return self.group_no


class Traveler(models.Model):
    """旅客问卷（每条对应一张意见表）"""
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='travelers', db_index=True)
    guide_language = models.DecimalField('地陪语言和讲解', max_digits=5, decimal_places=2, null=True, blank=True)
    guide_service = models.DecimalField('地陪服务态度', max_digits=5, decimal_places=2, null=True, blank=True)
    vehicle_comfort = models.DecimalField('车辆舒适度', max_digits=5, decimal_places=2, null=True, blank=True)
    vehicle_clean = models.DecimalField('车辆干净程度', max_digits=5, decimal_places=2, null=True, blank=True)
    driver_service = models.DecimalField('司机服务', max_digits=5, decimal_places=2, null=True, blank=True)
    food_quality = models.DecimalField('餐饮质量', max_digits=5, decimal_places=2, null=True, blank=True)
    restaurant_environment = models.DecimalField('餐厅环境', max_digits=5, decimal_places=2, null=True, blank=True)

    class Meta:
        db_table = 'questionnaire_traveler'
        verbose_name = '旅客问卷'
        verbose_name_plural = '旅客问卷'

    def __str__(self):
        return f'{self.group_id} #{self.pk}'
