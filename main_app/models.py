from django.db import models


class Group(models.Model):
    """团信息"""
    group_no = models.CharField('团号', max_length=64, unique=True, db_index=True)
    people_count = models.PositiveIntegerField('人数', default=0)
    feedback_count = models.PositiveIntegerField('意见表回收数量', default=0)
    feedback_rate = models.CharField('回收率', max_length=32, blank=True)
    date = models.CharField('日期(YYYY-MM)', max_length=7, blank=True)

    class Meta:
        db_table = 'questionnaire_group'
        verbose_name = '团'
        verbose_name_plural = '团'

    def __str__(self):
        return self.group_no


class Traveler(models.Model):
    """旅客问卷（每条对应一张意见表）"""
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='travelers', db_index=True)
    agency = models.CharField('地接社', max_length=128, blank=True)
    guide = models.CharField('导游', max_length=128, blank=True)
    hotel = models.CharField('酒店', max_length=128, blank=True)
    region = models.CharField('地区', max_length=64, blank=True)
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


class FullEscort(models.Model):
    """全陪问卷（每条对应一张意见表）"""
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='full_escorts', db_index=True)
    agency = models.CharField('地接社', max_length=128, blank=True)
    guide = models.CharField('导游', max_length=128, blank=True)
    hotel = models.CharField('酒店', max_length=128, blank=True)
    region = models.CharField('地区', max_length=64, blank=True)
    pace = models.DecimalField('节奏', max_digits=5, decimal_places=2, null=True, blank=True)
    explanation = models.DecimalField('讲解', max_digits=5, decimal_places=2, null=True, blank=True)
    service = models.DecimalField('服务', max_digits=5, decimal_places=2, null=True, blank=True)
    design = models.DecimalField('设计', max_digits=5, decimal_places=2, null=True, blank=True)
    expectation = models.DecimalField('期望', max_digits=5, decimal_places=2, null=True, blank=True)
    recommendation = models.DecimalField('推荐', max_digits=5, decimal_places=2, null=True, blank=True)
    overall = models.DecimalField('总评', max_digits=5, decimal_places=2, null=True, blank=True)

    class Meta:
        db_table = 'questionnaire_full_escort'
        verbose_name = '全陪问卷'
        verbose_name_plural = '全陪问卷'

    def __str__(self):
        return f'{self.group_id} #{self.pk}'


class SupplierAgency(models.Model):
    """地接社供应商"""
    name = models.CharField('名字', max_length=128, unique=True, db_index=True)
    region = models.CharField('地区', max_length=64, blank=True)
    name_initials = models.CharField('名字拼音首字母', max_length=128, blank=True, db_index=True)

    class Meta:
        db_table = 'supplier_agency'
        verbose_name = '地接社供应商'
        verbose_name_plural = '地接社供应商'

    def __str__(self):
        return self.name


class SupplierGuide(models.Model):
    """导游供应商"""
    GUIDE_TYPE_LOCAL = 'local'
    GUIDE_TYPE_FULL = 'full'
    GUIDE_TYPE_CHOICES = (
        (GUIDE_TYPE_LOCAL, '地陪'),
        (GUIDE_TYPE_FULL, '全陪'),
    )

    guide_type = models.CharField('类型', max_length=16, choices=GUIDE_TYPE_CHOICES, default=GUIDE_TYPE_LOCAL)
    name_cn = models.CharField('中文名', max_length=128, db_index=True)
    name_en = models.CharField('英文名', max_length=128, blank=True)
    language = models.CharField('语种', max_length=128, blank=True)
    region = models.CharField('地区', max_length=64, blank=True)
    name_initials = models.CharField('名字拼音首字母', max_length=128, blank=True, db_index=True)

    class Meta:
        db_table = 'supplier_guide'
        verbose_name = '导游供应商'
        verbose_name_plural = '导游供应商'

    def __str__(self):
        return self.name_cn
