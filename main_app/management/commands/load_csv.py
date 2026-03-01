import csv
from datetime import datetime
from pathlib import Path

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings

from main_app.models import Group, Traveler


class Command(BaseCommand):
    help = '从 data/groups.csv 和 data/travelers.csv 导入数据到数据库'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help='导入前清空问卷相关表')

    def handle(self, *args, **options):
        # 确保表已创建（若未执行过 migrate 会先执行）
        call_command('migrate', verbosity=0)

        data_dir = Path(settings.BASE_DIR) / 'data'
        groups_path = data_dir / 'groups.csv'
        travelers_path = data_dir / 'travelers.csv'

        if options['clear']:
            Traveler.objects.all().delete()
            Group.objects.all().delete()
            self.stdout.write('已清空 questionnaire_group / questionnaire_traveler 表。')

        if not groups_path.exists():
            self.stdout.write(self.style.WARNING(f'未找到 {groups_path}，跳过团数据。'))
        else:
            with groups_path.open(newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                count = 0
                for row in reader:
                    group_no = (row.get('group_no') or '').strip()
                    if not group_no:
                        continue
                    def _date(s):
                        s = (s or '').strip()
                        if not s:
                            return None
                        try:
                            return datetime.strptime(s, '%Y-%m-%d').date()
                        except ValueError:
                            return None
                    Group.objects.update_or_create(
                        group_no=group_no,
                        defaults={
                            'agency': (row.get('agency') or '').strip(),
                            'hotel': (row.get('hotel') or '').strip(),
                            'region': (row.get('region') or '').strip(),
                            'people_count': int(row.get('people_count') or 0) if str(row.get('people_count') or '').isdigit() else 0,
                            'feedback_count': int(row.get('feedback_count') or 0) if str(row.get('feedback_count') or '').isdigit() else 0,
                            'feedback_rate': (row.get('feedback_rate') or '').strip(),
                            'start_date': _date(row.get('start_date')),
                            'end_date': _date(row.get('end_date')),
                        }
                    )
                    count += 1
                self.stdout.write(f'团数据：导入/更新 {count} 条。')

        if not travelers_path.exists():
            self.stdout.write(self.style.WARNING(f'未找到 {travelers_path}，跳过旅客问卷。'))
        else:
            group_cache = {g.group_no: g for g in Group.objects.all()}
            with travelers_path.open(newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                created = 0
                for row in reader:
                    group_no = (row.get('group_no') or '').strip()
                    group = group_cache.get(group_no)
                    if not group:
                        continue
                    def _dec(key):
                        s = (row.get(key) or '').strip()
                        try:
                            return float(s) if s else None
                        except ValueError:
                            return None
                    Traveler.objects.create(
                        group=group,
                        guide_language=_dec('guide_language'),
                        guide_service=_dec('guide_service'),
                        vehicle_comfort=_dec('vehicle_comfort'),
                        vehicle_clean=_dec('vehicle_clean'),
                        driver_service=_dec('driver_service'),
                        food_quality=_dec('food_quality'),
                        restaurant_environment=_dec('restaurant_environment'),
                    )
                    created += 1
                self.stdout.write(f'旅客问卷：共导入 {created} 条。')
        self.stdout.write(self.style.SUCCESS('导入完成。'))
