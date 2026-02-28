from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.conf import settings
from django.urls import reverse
from pathlib import Path
import csv
import json


def hello(request):
    return render(request, 'hello.html', {
        'message': 'Hello World!'
    })


# ===== 问卷（questionnaire）相关逻辑，使用 CSV 作为简易“数据库” =====

DATA_DIR = Path(settings.BASE_DIR) / 'data'
GROUP_CSV = DATA_DIR / 'groups.csv'
TRAVELER_CSV = DATA_DIR / 'travelers.csv'


def _ensure_data_dir():
    DATA_DIR.mkdir(exist_ok=True)


def _read_csv(path, fieldnames):
    if not path.exists():
        return []
    with path.open(newline='', encoding='utf-8') as f:
        # 使用文件中第一行作为表头，这样表头只由后端控制，
        # 页面上不会把表头当成一条可编辑的数据。
        reader = csv.DictReader(f)
        rows = []
        for row in reader:
            cleaned = {field: (row.get(field, '') or '').strip() for field in fieldnames}
            rows.append(cleaned)
    return rows


def _write_csv(path, fieldnames, rows):
    with path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


GROUP_FIELDS = [
    'group_no',          # 团号
    'agency',            # 地接社
    'hotel',             # 酒店
    'region',            # 地区
    'people_count',      # 人数
    'feedback_count',    # 意见表回收数量
    'feedback_rate',     # 回收率
    'start_date',        # 开始日期
    'end_date',          # 截止日期
]

TRAVELER_FIELDS = [
    'group_no',              # 外键：属于哪个团
    'guide_language',        # 地陪语言和讲解
    'guide_service',         # 地陪服务态度
    'vehicle_comfort',       # 车辆舒适度
    'vehicle_clean',         # 车辆干净程度
    'driver_service',        # 司机服务
    'food_quality',          # 餐饮质量
    'restaurant_environment' # 餐厅环境
]


def questionnaire(request):
    _ensure_data_dir()

    # 先读取当前数据
    groups = _read_csv(GROUP_CSV, GROUP_FIELDS)
    travelers = _read_csv(TRAVELER_CSV, TRAVELER_FIELDS)

    # 统计每个团关联的旅客数量，用于删除前提示
    traveler_counts = {}
    for t in travelers:
        key = (t.get('group_no') or '').strip()
        if not key:
            continue
        traveler_counts[key] = traveler_counts.get(key, 0) + 1

    if request.method == 'POST':
        entity = request.POST.get('entity')  # 'group' or 'traveler'
        action = request.POST.get('action')  # 'create' / 'update' / 'delete'

        if entity == 'group':
            index_str = request.POST.get('index')
            if action == 'create':
                # 先取出人数和回收数量，便于计算回收率
                people_count = request.POST.get('people_count', '').strip()
                feedback_count = request.POST.get('feedback_count', '').strip()
                feedback_rate = ''
                try:
                    pc = int(people_count)
                    fc = int(feedback_count)
                    if pc > 0 and 0 <= fc <= pc:
                        feedback_rate = f"{round(fc * 100 / pc, 2)}%"
                except ValueError:
                    pass

                new_group_no = request.POST.get('group_no', '').strip()
                existing_nos = {(g.get('group_no') or '').strip() for g in groups if (g.get('group_no') or '').strip()}
                if new_group_no and new_group_no not in existing_nos:
                    new_group = {
                        'group_no': new_group_no,
                        'agency': request.POST.get('agency', '').strip(),
                        'hotel': request.POST.get('hotel', '').strip(),
                        'region': request.POST.get('region', '').strip(),
                        'people_count': people_count,
                        'feedback_count': feedback_count,
                        'feedback_rate': feedback_rate,
                        'start_date': request.POST.get('start_date', '').strip(),
                        'end_date': request.POST.get('end_date', '').strip(),
                    }
                    groups.append(new_group)

            elif action in ('update', 'delete') and index_str is not None:
                try:
                    idx = int(index_str)
                    if 0 <= idx < len(groups):
                        if action == 'update':
                            people_count = request.POST.get('people_count', '').strip()
                            feedback_count = request.POST.get('feedback_count', '').strip()
                            feedback_rate = ''
                            try:
                                pc = int(people_count)
                                fc = int(feedback_count)
                                if pc > 0 and 0 <= fc <= pc:
                                    feedback_rate = f"{round(fc * 100 / pc, 2)}%"
                            except ValueError:
                                pass

                            new_group_no = request.POST.get('group_no', '').strip()
                            existing_nos = {(g.get('group_no') or '').strip() for i, g in enumerate(groups) if i != idx and (g.get('group_no') or '').strip()}
                            if new_group_no and new_group_no not in existing_nos:
                                groups[idx] = {
                                    'group_no': new_group_no,
                                    'agency': request.POST.get('agency', '').strip(),
                                    'hotel': request.POST.get('hotel', '').strip(),
                                    'region': request.POST.get('region', '').strip(),
                                    'people_count': people_count,
                                    'feedback_count': feedback_count,
                                    'feedback_rate': feedback_rate,
                                    'start_date': request.POST.get('start_date', '').strip(),
                                    'end_date': request.POST.get('end_date', '').strip(),
                                }
                        elif action == 'delete':
                            # 记录被删团的团号，用于同步删除旅客表中的对应记录
                            deleted_group_no = groups[idx].get('group_no', '').strip()
                            groups.pop(idx)
                            if deleted_group_no:
                                travelers = [
                                    t for t in travelers
                                    if t.get('group_no', '').strip() != deleted_group_no
                                ]
                except ValueError:
                    pass

            _write_csv(GROUP_CSV, GROUP_FIELDS, groups)
            _write_csv(TRAVELER_CSV, TRAVELER_FIELDS, travelers)

        elif entity == 'traveler':
            index_str = request.POST.get('index')
            if action == 'create':
                last_group_no = request.POST.get('group_no', '').strip()
                new_traveler = {
                    'group_no': last_group_no,
                    'guide_language': request.POST.get('guide_language', '').strip(),
                    'guide_service': request.POST.get('guide_service', '').strip(),
                    'vehicle_comfort': request.POST.get('vehicle_comfort', '').strip(),
                    'vehicle_clean': request.POST.get('vehicle_clean', '').strip(),
                    'driver_service': request.POST.get('driver_service', '').strip(),
                    'food_quality': request.POST.get('food_quality', '').strip(),
                    'restaurant_environment': request.POST.get('restaurant_environment', '').strip(),
                }
                travelers.append(new_traveler)

            elif action in ('update', 'delete') and index_str is not None:
                try:
                    idx = int(index_str)
                    if 0 <= idx < len(travelers):
                        if action == 'update':
                            travelers[idx] = {
                                'group_no': request.POST.get('group_no', '').strip(),
                                'guide_language': request.POST.get('guide_language', '').strip(),
                                'guide_service': request.POST.get('guide_service', '').strip(),
                                'vehicle_comfort': request.POST.get('vehicle_comfort', '').strip(),
                                'vehicle_clean': request.POST.get('vehicle_clean', '').strip(),
                                'driver_service': request.POST.get('driver_service', '').strip(),
                                'food_quality': request.POST.get('food_quality', '').strip(),
                                'restaurant_environment': request.POST.get('restaurant_environment', '').strip(),
                            }
                        elif action == 'delete':
                            travelers.pop(idx)
                except ValueError:
                    pass

            _write_csv(TRAVELER_CSV, TRAVELER_FIELDS, travelers)

            # 创建旅客问卷后，带上最近使用的团号和需要聚焦的标记
            if action == 'create':
                url = f"{reverse('questionnaire_add')}?last_group_no={last_group_no}&focus_traveler=1"
                return redirect(url)

        # 其他操作完成后重定向，避免重复提交
        return redirect('questionnaire_add')

    # GET 请求：展示页面
    last_group_no = request.GET.get('last_group_no', '')
    focus_traveler = request.GET.get('focus_traveler') == '1'

    groups_for_view = []
    for idx, g in enumerate(groups):
        key = (g.get('group_no') or '').strip()
        count = traveler_counts.get(key, 0)
        groups_for_view.append((idx, g, count))

    context = {
        'groups': groups_for_view,        # [(index, group_dict, traveler_count), ...]
        'travelers': list(enumerate(travelers)),  # [(index, traveler_dict), ...]
        'last_group_no': last_group_no,
        'focus_traveler': focus_traveler,
    }
    return render(request, 'questionnaire.html', context)


def questionnaire_view(request):
    _ensure_data_dir()

    groups = _read_csv(GROUP_CSV, GROUP_FIELDS)
    travelers = _read_csv(TRAVELER_CSV, TRAVELER_FIELDS)

    # 构造团号 -> 团信息 映射，方便在旅客表中展示地区等
    group_map = {}
    for g in groups:
        key = (g.get('group_no') or '').strip()
        if key:
            group_map[key] = g

    METRIC_KEYS = ['guide_language', 'guide_service', 'vehicle_comfort', 'vehicle_clean', 'driver_service', 'food_quality', 'restaurant_environment']
    enriched_travelers = []
    for t in travelers:
        group_no = (t.get('group_no') or '').strip()
        g = group_map.get(group_no, {})
        s = 0.0
        valid = False
        for k in METRIC_KEYS:
            try:
                v = float(t.get(k) or 0)
            except ValueError:
                v = 0
            if v:
                valid = True
            s += v
        composite_score = round(s / len(METRIC_KEYS), 2) if valid else 0.0
        enriched_travelers.append({
            'group_no': group_no,
            'region': g.get('region', ''),
            'agency': g.get('agency', ''),
            'hotel': g.get('hotel', ''),
            'start_date': g.get('start_date', ''),
            'end_date': g.get('end_date', ''),
            'guide_language': t.get('guide_language', ''),
            'guide_service': t.get('guide_service', ''),
            'vehicle_comfort': t.get('vehicle_comfort', ''),
            'vehicle_clean': t.get('vehicle_clean', ''),
            'driver_service': t.get('driver_service', ''),
            'food_quality': t.get('food_quality', ''),
            'restaurant_environment': t.get('restaurant_environment', ''),
            'composite_score': composite_score,
        })

    def _calc_mean_std(values):
        if not values:
            return 0.0, 0.0
        n = len(values)
        mean_val = sum(values) / n
        var = sum((v - mean_val) ** 2 for v in values) / n
        return round(mean_val, 2), round(var ** 0.5, 2)

    # 需要统计的各项评分 + 总分
    metric_defs = [
        ('guide_language', '地陪语言和讲解'),
        ('guide_service', '地陪服务态度'),
        ('vehicle_comfort', '车辆舒适度'),
        ('vehicle_clean', '车辆干净程度'),
        ('driver_service', '司机服务'),
        ('food_quality', '餐饮质量'),
        ('restaurant_environment', '餐厅环境'),
    ]

    # 多团统计：每个团的总分均值/标准差 + 回收率，以及图表所需的各项均值/标准差
    group_stats = []  # 用于表格展示
    chart_stats = {}  # 用于前端折线图：每个团 -> 各指标 mean/std

    # 收集所有有团号的团
    all_group_nos = sorted({(g.get('group_no') or '').strip() for g in groups if (g.get('group_no') or '').strip()})

    for gno in all_group_nos:
        base_info = group_map.get(gno, {})
        group_travelers = [t for t in enriched_travelers if (t.get('group_no') or '').strip() == gno]

        # 各单项
        metrics_for_group = {}
        for key, label in metric_defs:
            vals = []
            for t in group_travelers:
                try:
                    v = float(t.get(key) or 0)
                except ValueError:
                    continue
                vals.append(v)
            mean_v, std_v = _calc_mean_std(vals)
            metrics_for_group[key] = {
                'label': label,
                'mean': mean_v,
                'std': std_v,
            }

        # 综合得分 = 总分 / 小项数（7 项）
        total_vals = []
        for t in group_travelers:
            s = 0.0
            valid = False
            for key, _ in metric_defs:
                try:
                    v = float(t.get(key) or 0)
                except ValueError:
                    v = 0
                if v:
                    valid = True
                s += v
            if valid:
                total_vals.append(s / len(metric_defs))  # 综合得分
        total_mean, total_std = _calc_mean_std(total_vals)

        feedback_rate = base_info.get('feedback_rate', '')

        # 团列表展示：基础信息 + 各小项平均分 + 综合得分
        group_entry = {
            'group_no': gno,
            'region': base_info.get('region', ''),
            'agency': base_info.get('agency', ''),
            'hotel': base_info.get('hotel', ''),
            'start_date': base_info.get('start_date', ''),
            'end_date': base_info.get('end_date', ''),
            'feedback_rate': feedback_rate,
            'total_mean': total_mean,
            'total_std': total_std,
        }

        # 将每个小项的平均分放进 group_stats，方便模板直接展示
        for key, _label in metric_defs:
            metric_info = metrics_for_group.get(key, {})
            group_entry[f'{key}_mean'] = metric_info.get('mean', 0.0)

        group_stats.append(group_entry)

        chart_stats[gno] = {
            'group_no': gno,
            'region': base_info.get('region', ''),
            'feedback_rate': feedback_rate,
            'metrics': metrics_for_group,
            'total': {
                'label': '综合得分',
                'mean': total_mean,
                'std': total_std,
            },
        }

    context = {
        'groups': groups,
        'travelers': [],
        'group_stats': [],
    }
    return render(request, 'questionnaire_view.html', context)


def _load_view_data():
    """加载问卷查看所需数据：enriched_travelers, group_stats, metric_defs"""
    _ensure_data_dir()
    groups = _read_csv(GROUP_CSV, GROUP_FIELDS)
    travelers = _read_csv(TRAVELER_CSV, TRAVELER_FIELDS)
    group_map = {(g.get('group_no') or '').strip(): g for g in groups if (g.get('group_no') or '').strip()}
    METRIC_KEYS = ['guide_language', 'guide_service', 'vehicle_comfort', 'vehicle_clean', 'driver_service', 'food_quality', 'restaurant_environment']
    enriched_travelers = []
    for t in travelers:
        group_no = (t.get('group_no') or '').strip()
        g = group_map.get(group_no, {})
        s = 0.0
        valid = False
        for k in METRIC_KEYS:
            try:
                v = float(t.get(k) or 0)
            except ValueError:
                v = 0
            if v:
                valid = True
            s += v
        composite_score = round(s / len(METRIC_KEYS), 2) if valid else 0.0
        enriched_travelers.append({
            'group_no': group_no,
            'region': g.get('region', ''),
            'agency': g.get('agency', ''),
            'hotel': g.get('hotel', ''),
            'start_date': g.get('start_date', ''),
            'end_date': g.get('end_date', ''),
            'guide_language': t.get('guide_language', ''),
            'guide_service': t.get('guide_service', ''),
            'vehicle_comfort': t.get('vehicle_comfort', ''),
            'vehicle_clean': t.get('vehicle_clean', ''),
            'driver_service': t.get('driver_service', ''),
            'food_quality': t.get('food_quality', ''),
            'restaurant_environment': t.get('restaurant_environment', ''),
            'composite_score': composite_score,
        })
    metric_defs = [
        ('guide_language', '地陪语言'), ('guide_service', '服务态度'), ('vehicle_comfort', '车辆舒适度'),
        ('vehicle_clean', '车辆干净'), ('driver_service', '司机服务'), ('food_quality', '餐饮质量'),
        ('restaurant_environment', '餐厅环境'),
    ]

    def _calc_mean(values):
        if not values:
            return 0.0
        return round(sum(values) / len(values), 2)

    group_stats = []
    all_group_nos = sorted({(g.get('group_no') or '').strip() for g in groups if (g.get('group_no') or '').strip()})
    for gno in all_group_nos:
        base_info = group_map.get(gno, {})
        group_travelers = [t for t in enriched_travelers if (t.get('group_no') or '').strip() == gno]
        metrics_for_group = {}
        for key, label in metric_defs:
            vals = []
            for t in group_travelers:
                try:
                    vals.append(float(t.get(key) or 0))
                except ValueError:
                    pass
            metrics_for_group[key] = {'label': label, 'mean': _calc_mean(vals)}
        total_vals = []
        for t in group_travelers:
            s = 0.0
            valid = False
            for key, _ in metric_defs:
                try:
                    v = float(t.get(key) or 0)
                except ValueError:
                    v = 0
                if v:
                    valid = True
                s += v
            if valid:
                total_vals.append(s / len(metric_defs))
        total_mean = _calc_mean(total_vals)
        group_entry = {
            'group_no': gno, 'region': base_info.get('region', ''),
            'agency': base_info.get('agency', ''), 'hotel': base_info.get('hotel', ''),
            'start_date': base_info.get('start_date', ''), 'end_date': base_info.get('end_date', ''),
            'feedback_rate': base_info.get('feedback_rate', ''),
            'total_mean': total_mean,
        }
        for key, _ in metric_defs:
            group_entry[f'{key}_mean'] = metrics_for_group[key]['mean']
        group_stats.append(group_entry)
    return enriched_travelers, group_stats


def view_data_api(request):
    """动态分页 API：table=travelers|group_stats|group_by, page, page_size, filters, sort, order"""
    PAGE_SIZE = 20
    enriched_travelers, group_stats = _load_view_data()

    table = request.GET.get('table', '')
    page = max(1, int(request.GET.get('page', 1)))
    page_size = min(100, max(1, int(request.GET.get('page_size', PAGE_SIZE))))
    sort_key = request.GET.get('sort', '')
    order = request.GET.get('order', 'asc')

    # group_by: 按地接社/地区/酒店聚合
    if table == 'group_by':
        by = request.GET.get('by', 'agency')
        sort_key = request.GET.get('sort', '')
        order = request.GET.get('order', 'asc')
        start_from = request.GET.get('start_from', '')
        start_to = request.GET.get('start_to', '')
        end_from = request.GET.get('end_from', '')
        end_to = request.GET.get('end_to', '')
        key_map = {'agency': 'agency', 'region': 'region', 'hotel': 'hotel'}
        key_field = key_map.get(by, 'agency')
        label_map = {'agency': '地接社', 'region': '地区', 'hotel': '酒店'}
        label = label_map.get(by, '地接社')

        # 日期筛选：与统计相同的逻辑
        filtered_stats = [g for g in group_stats if
            (not start_from or (g.get('start_date') or '') >= start_from) and
            (not start_to or (g.get('start_date') or '') <= start_to) and
            (not end_from or (g.get('end_date') or '') >= end_from) and
            (not end_to or (g.get('end_date') or '') <= end_to)
        ]

        from collections import defaultdict
        agg = defaultdict(lambda: {'count': 0, 'total': 0.0, 'metrics': defaultdict(list)})
        for g in filtered_stats:
            k = (g.get(key_field) or '').strip() or '(空)'
            agg[k]['count'] += 1
            agg[k]['total'] += float(g.get('total_mean') or 0)
            for m in ['guide_language_mean', 'guide_service_mean', 'vehicle_comfort_mean', 'vehicle_clean_mean', 'driver_service_mean', 'food_quality_mean', 'restaurant_environment_mean']:
                agg[k]['metrics'][m].append(float(g.get(m) or 0))
        rows = []
        for k, v in agg.items():
            ms = {m: round(sum(v['metrics'][m]) / len(v['metrics'][m]), 2) if v['metrics'][m] else 0 for m in v['metrics']}
            rows.append({
                'key': k,
                'label': label,
                'count': v['count'],
                'avg_composite': round(v['total'] / v['count'], 2),
                **ms,
            })
        # 排序（与 group_stats / travelers 同样逻辑）
        sort_col_map = {
            'key': 'key', 'count': 'count', 'avg_composite': 'avg_composite',
            'guide_language_mean': 'guide_language_mean', 'guide_service_mean': 'guide_service_mean',
            'vehicle_comfort_mean': 'vehicle_comfort_mean', 'vehicle_clean_mean': 'vehicle_clean_mean',
            'driver_service_mean': 'driver_service_mean', 'food_quality_mean': 'food_quality_mean',
            'restaurant_environment_mean': 'restaurant_environment_mean',
        }
        col = sort_col_map.get(sort_key, '')
        if col:
            def _sort_val(r, c):
                v = r.get(c)
                if v is None or v == '':
                    return 0 if c != 'key' else ''
                if c == 'key':
                    return str(v)
                try:
                    return float(v)
                except (TypeError, ValueError):
                    return str(v)
            rev = order != 'asc'
            rows = sorted(rows, key=lambda r: _sort_val(r, col), reverse=rev)
        return JsonResponse({'rows': rows, 'total': len(rows)})

    # travelers 表格
    if table == 'travelers':
        rows = enriched_travelers
        kw_group = (request.GET.get('group', '') or '').strip().lower()
        kw_region = (request.GET.get('region', '') or '').strip().lower()
        kw_agency = (request.GET.get('agency', '') or '').strip().lower()
        kw_hotel = (request.GET.get('hotel', '') or '').strip().lower()
        start_from = request.GET.get('start_from', '')
        start_to = request.GET.get('start_to', '')
        end_from = request.GET.get('end_from', '')
        end_to = request.GET.get('end_to', '')
        rows = [r for r in rows if
            (not kw_group or (r.get('group_no') or '').lower().find(kw_group) >= 0) and
            (not kw_region or (r.get('region') or '').lower().find(kw_region) >= 0) and
            (not kw_agency or (r.get('agency') or '').lower().find(kw_agency) >= 0) and
            (not kw_hotel or (r.get('hotel') or '').lower().find(kw_hotel) >= 0) and
            (not start_from or (r.get('start_date') or '') >= start_from) and
            (not start_to or (r.get('start_date') or '') <= start_to) and
            (not end_from or (r.get('end_date') or '') >= end_from) and
            (not end_to or (r.get('end_date') or '') <= end_to)
        ]
        sort_col_map = {
            'group_no': 'group_no', 'region': 'region', 'agency': 'agency', 'hotel': 'hotel',
            'start_date': 'start_date', 'end_date': 'end_date',
            'guide_language': 'guide_language', 'guide_service': 'guide_service',
            'vehicle_comfort': 'vehicle_comfort', 'vehicle_clean': 'vehicle_clean',
            'driver_service': 'driver_service', 'food_quality': 'food_quality',
            'restaurant_environment': 'restaurant_environment', 'total_score': 'composite_score',
        }
        col = sort_col_map.get(sort_key, '')
        if col:
            rev = order != 'asc'
            rows = sorted(rows, key=lambda r: (float(r.get(col)) if isinstance(r.get(col), (int, float)) or (isinstance(r.get(col), str) and r.get(col).replace('.','',1).isdigit()) else r.get(col) or ''), reverse=rev)
        total = len(rows)
        start = (page - 1) * page_size
        page_rows = rows[start:start + page_size]
        return JsonResponse({'rows': page_rows, 'total': total, 'page': page, 'total_pages': max(1, (total + page_size - 1) // page_size)})

    # group_stats 表格
    if table == 'group_stats':
        rows = group_stats
        kw_group = (request.GET.get('group_no', '') or '').strip().lower()
        kw_region = (request.GET.get('region', '') or '').strip().lower()
        kw_agency = (request.GET.get('agency', '') or '').strip().lower()
        kw_hotel = (request.GET.get('hotel', '') or '').strip().lower()
        start_from = request.GET.get('start_from', '')
        start_to = request.GET.get('start_to', '')
        end_from = request.GET.get('end_from', '')
        end_to = request.GET.get('end_to', '')
        rows = [r for r in rows if
            (not kw_group or (r.get('group_no') or '').lower().find(kw_group) >= 0) and
            (not kw_region or (r.get('region') or '').lower().find(kw_region) >= 0) and
            (not kw_agency or (r.get('agency') or '').lower().find(kw_agency) >= 0) and
            (not kw_hotel or (r.get('hotel') or '').lower().find(kw_hotel) >= 0) and
            (not start_from or (r.get('start_date') or '') >= start_from) and
            (not start_to or (r.get('start_date') or '') <= start_to) and
            (not end_from or (r.get('end_date') or '') >= end_from) and
            (not end_to or (r.get('end_date') or '') <= end_to)
        ]
        sort_col_map = {
            'group_no': 'group_no', 'region': 'region', 'agency': 'agency', 'hotel': 'hotel',
            'start_date': 'start_date', 'end_date': 'end_date', 'feedback_rate': 'feedback_rate',
            'guide_language_mean': 'guide_language_mean', 'guide_service_mean': 'guide_service_mean',
            'vehicle_comfort_mean': 'vehicle_comfort_mean', 'vehicle_clean_mean': 'vehicle_clean_mean',
            'driver_service_mean': 'driver_service_mean', 'food_quality_mean': 'food_quality_mean',
            'restaurant_environment_mean': 'restaurant_environment_mean', 'total_mean': 'total_mean',
        }
        col = sort_col_map.get(sort_key, '')
        if col:
            def _sort_val(v):
                if v is None or v == '': return 0
                s = str(v).replace('%', '')
                try:
                    return float(s)
                except ValueError:
                    return str(v)
            rev = order != 'asc'
            rows = sorted(rows, key=lambda r: _sort_val(r.get(col)), reverse=rev)
        total = len(rows)
        start = (page - 1) * page_size
        page_rows = rows[start:start + page_size]
        return JsonResponse({'rows': page_rows, 'total': total, 'page': page, 'total_pages': max(1, (total + page_size - 1) // page_size)})

    return JsonResponse({'error': 'invalid table'}, status=400)

