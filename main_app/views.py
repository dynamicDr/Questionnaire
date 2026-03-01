from decimal import Decimal
from urllib.parse import urlencode

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.urls import reverse
from django.db.models import Count
from django.utils.dateparse import parse_date

from .models import Group, Traveler


def hello(request):
    return render(request, 'hello.html', {
        'message': 'Hello World!'
    })


# ===== 问卷（questionnaire）相关逻辑，使用 MySQL =====

def _group_to_dict(g):
    return {
        'group_no': g.group_no or '',
        'agency': g.agency or '',
        'hotel': g.hotel or '',
        'region': g.region or '',
        'people_count': g.people_count or 0,
        'feedback_count': g.feedback_count or 0,
        'feedback_rate': g.feedback_rate or '',
        'start_date': g.start_date.isoformat() if g.start_date else '',
        'end_date': g.end_date.isoformat() if g.end_date else '',
    }


def _score_int(v):
    """将评分转为整数字符串显示"""
    if v is None:
        return ''
    try:
        return str(int(round(float(v))))
    except (TypeError, ValueError):
        return ''


def _traveler_to_dict(t):
    return {
        'group_no': t.group.group_no if t.group_id else '',
        'guide_language': _score_int(t.guide_language),
        'guide_service': _score_int(t.guide_service),
        'vehicle_comfort': _score_int(t.vehicle_comfort),
        'vehicle_clean': _score_int(t.vehicle_clean),
        'driver_service': _score_int(t.driver_service),
        'food_quality': _score_int(t.food_quality),
        'restaurant_environment': _score_int(t.restaurant_environment),
    }


def _compute_feedback_rate(people_count, feedback_count):
    try:
        pc = int(people_count)
        fc = int(feedback_count)
        if pc > 0 and 0 <= fc <= pc:
            return f"{round(fc * 100 / pc, 2)}%"
    except (ValueError, TypeError):
        pass
    return ''


def _questionnaire_context(request, group_exists=False, existing_group=None, create_form_data=None):
    """问卷页 GET 或“团号已存在”时的共用 context"""
    last_group_no = request.GET.get('last_group_no', '') if request.method == 'GET' else ''
    focus_traveler = request.GET.get('focus_traveler') == '1' if request.method == 'GET' else False
    error = request.GET.get('error', '') if request.method == 'GET' else ''

    groups_qs = Group.objects.all().order_by('group_no').annotate(traveler_count=Count('travelers'))
    groups_for_view = [(g.id, _group_to_dict(g), g.traveler_count) for g in groups_qs]
    travelers_qs = Traveler.objects.select_related('group').all().order_by('-id')
    travelers = [(t.id, _traveler_to_dict(t)) for t in travelers_qs]

    context = {
        'groups': groups_for_view,
        'travelers': travelers,
        'last_group_no': last_group_no,
        'focus_traveler': focus_traveler,
        'error': error,
    }
    if group_exists:
        context['group_exists'] = True
        context['existing_group'] = existing_group or {}
        context['create_form_data'] = create_form_data or {}
    return context


def questionnaire(request):
    if request.method == 'POST':
        entity = request.POST.get('entity')
        action = request.POST.get('action')

        if entity == 'group':
            index_str = request.POST.get('index')
            if action == 'create':
                confirm_overwrite = request.POST.get('confirm_overwrite') == '1'
                group_no = request.POST.get('group_no', '').strip()
                existing_group = Group.objects.filter(group_no=group_no).first() if group_no else None

                if confirm_overwrite and existing_group:
                    # 用户确认覆盖：更新已有团
                    people_count = request.POST.get('people_count', '').strip()
                    feedback_count = request.POST.get('feedback_count', '').strip()
                    start_s = request.POST.get('start_date', '').strip()
                    end_s = request.POST.get('end_date', '').strip()
                    existing_group.agency = request.POST.get('agency', '').strip()
                    existing_group.hotel = request.POST.get('hotel', '').strip()
                    existing_group.region = request.POST.get('region', '').strip()
                    existing_group.people_count = int(people_count) if people_count.isdigit() else 0
                    existing_group.feedback_count = int(feedback_count) if feedback_count.isdigit() else 0
                    existing_group.feedback_rate = _compute_feedback_rate(people_count, feedback_count)
                    existing_group.start_date = parse_date(start_s) if start_s else None
                    existing_group.end_date = parse_date(end_s) if end_s else None
                    existing_group.save()
                    return redirect('questionnaire_add')
                if group_no and existing_group:
                    # 团号已存在，未确认覆盖：返回页面并提示
                    context = _questionnaire_context(
                        request,
                        group_exists=True,
                        existing_group=_group_to_dict(existing_group),
                        create_form_data={
                            'group_no': group_no,
                            'agency': request.POST.get('agency', '').strip(),
                            'hotel': request.POST.get('hotel', '').strip(),
                            'region': request.POST.get('region', '').strip(),
                            'people_count': request.POST.get('people_count', '').strip(),
                            'feedback_count': request.POST.get('feedback_count', '').strip(),
                            'start_date': request.POST.get('start_date', '').strip(),
                            'end_date': request.POST.get('end_date', '').strip(),
                        },
                    )
                    return render(request, 'questionnaire.html', context)
                if group_no and not existing_group:
                    people_count = request.POST.get('people_count', '').strip()
                    feedback_count = request.POST.get('feedback_count', '').strip()
                    start_s = request.POST.get('start_date', '').strip()
                    end_s = request.POST.get('end_date', '').strip()
                    start_date = parse_date(start_s) if start_s else None
                    end_date = parse_date(end_s) if end_s else None
                    Group.objects.create(
                        group_no=group_no,
                        agency=request.POST.get('agency', '').strip(),
                        hotel=request.POST.get('hotel', '').strip(),
                        region=request.POST.get('region', '').strip(),
                        people_count=int(people_count) if people_count.isdigit() else 0,
                        feedback_count=int(feedback_count) if feedback_count.isdigit() else 0,
                        feedback_rate=_compute_feedback_rate(people_count, feedback_count),
                        start_date=start_date,
                        end_date=end_date,
                    )
                    return redirect('questionnaire_add')

            elif action in ('update', 'delete') and index_str:
                try:
                    g = get_object_or_404(Group, pk=int(index_str))
                    if action == 'update':
                        group_no = request.POST.get('group_no', '').strip()
                        if group_no and (group_no == g.group_no or not Group.objects.filter(group_no=group_no).exists()):
                            people_count = request.POST.get('people_count', '').strip()
                            feedback_count = request.POST.get('feedback_count', '').strip()
                            g.group_no = group_no
                            g.agency = request.POST.get('agency', '').strip()
                            g.hotel = request.POST.get('hotel', '').strip()
                            g.region = request.POST.get('region', '').strip()
                            g.people_count = int(people_count) if people_count.isdigit() else 0
                            g.feedback_count = int(feedback_count) if feedback_count.isdigit() else 0
                            g.feedback_rate = _compute_feedback_rate(people_count, feedback_count)
                            start_s = request.POST.get('start_date', '').strip()
                            end_s = request.POST.get('end_date', '').strip()
                            g.start_date = parse_date(start_s) if start_s else None
                            g.end_date = parse_date(end_s) if end_s else None
                            g.save()
                    elif action == 'delete':
                        g.delete()
                except (ValueError, TypeError):
                    pass

            return redirect('questionnaire_add')

        elif entity == 'traveler':
            index_str = request.POST.get('index')
            if action == 'create':
                group_no = request.POST.get('group_no', '').strip()
                group = Group.objects.filter(group_no=group_no).first()
                if not group:
                    qs = urlencode({'error': 'group_not_found', 'last_group_no': group_no})
                    return redirect(f"{reverse('questionnaire_add')}?{qs}")
                def _dec(s):
                    try:
                        return Decimal(s) if s else None
                    except (ValueError, TypeError):
                        return None
                Traveler.objects.create(
                    group=group,
                    guide_language=_dec(request.POST.get('guide_language', '').strip()),
                    guide_service=_dec(request.POST.get('guide_service', '').strip()),
                    vehicle_comfort=_dec(request.POST.get('vehicle_comfort', '').strip()),
                    vehicle_clean=_dec(request.POST.get('vehicle_clean', '').strip()),
                    driver_service=_dec(request.POST.get('driver_service', '').strip()),
                    food_quality=_dec(request.POST.get('food_quality', '').strip()),
                    restaurant_environment=_dec(request.POST.get('restaurant_environment', '').strip()),
                )
                url = f"{reverse('questionnaire_add')}?last_group_no={group_no}&focus_traveler=1"
                return redirect(url)

            elif action in ('update', 'delete') and index_str:
                try:
                    t = get_object_or_404(Traveler, pk=int(index_str))
                    if action == 'update':
                        group_no = request.POST.get('group_no', '').strip()
                        grp = Group.objects.filter(group_no=group_no).first()
                        if grp:
                            t.group = grp
                            def _dec(s):
                                try:
                                    return Decimal(s) if s else None
                                except (ValueError, TypeError):
                                    return None
                            t.guide_language = _dec(request.POST.get('guide_language', '').strip())
                            t.guide_service = _dec(request.POST.get('guide_service', '').strip())
                            t.vehicle_comfort = _dec(request.POST.get('vehicle_comfort', '').strip())
                            t.vehicle_clean = _dec(request.POST.get('vehicle_clean', '').strip())
                            t.driver_service = _dec(request.POST.get('driver_service', '').strip())
                            t.food_quality = _dec(request.POST.get('food_quality', '').strip())
                            t.restaurant_environment = _dec(request.POST.get('restaurant_environment', '').strip())
                            t.save()
                    elif action == 'delete':
                        t.delete()
                except (ValueError, TypeError):
                    pass

            if action == 'create':
                pass  # redirect already done above
            else:
                return redirect('questionnaire_add')

    # GET
    context = _questionnaire_context(request)
    return render(request, 'questionnaire.html', context)


def questionnaire_view(request):
    # 页面仅负责渲染，数据由前端 API 动态加载
    context = {
        'groups': [],
        'travelers': [],
        'group_stats': [],
    }
    return render(request, 'questionnaire_view.html', context)


METRIC_KEYS = ['guide_language', 'guide_service', 'vehicle_comfort', 'vehicle_clean', 'driver_service', 'food_quality', 'restaurant_environment']


def _load_view_data():
    """从 MySQL 加载问卷查看所需数据：enriched_travelers, group_stats"""
    groups = list(Group.objects.all().order_by('group_no'))
    group_map = {g.group_no: g for g in groups if g.group_no}
    travelers_qs = Traveler.objects.select_related('group').all()

    enriched_travelers = []
    for t in travelers_qs:
        g = t.group
        group_no = g.group_no if g else ''
        scores = []
        for k in METRIC_KEYS:
            v = getattr(t, k)
            try:
                scores.append(float(v) if v is not None else 0)
            except (TypeError, ValueError):
                scores.append(0)
        valid = any(scores)
        composite_score = round(sum(scores) / len(scores), 2) if valid else 0.0
        enriched_travelers.append({
            'group_no': group_no,
            'region': g.region or '' if g else '',
            'agency': g.agency or '' if g else '',
            'hotel': g.hotel or '' if g else '',
            'start_date': g.start_date.isoformat() if g and g.start_date else '',
            'end_date': g.end_date.isoformat() if g and g.end_date else '',
            'guide_language': str(t.guide_language) if t.guide_language is not None else '',
            'guide_service': str(t.guide_service) if t.guide_service is not None else '',
            'vehicle_comfort': str(t.vehicle_comfort) if t.vehicle_comfort is not None else '',
            'vehicle_clean': str(t.vehicle_clean) if t.vehicle_clean is not None else '',
            'driver_service': str(t.driver_service) if t.driver_service is not None else '',
            'food_quality': str(t.food_quality) if t.food_quality is not None else '',
            'restaurant_environment': str(t.restaurant_environment) if t.restaurant_environment is not None else '',
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
    for g in groups:
        gno = g.group_no or ''
        if not gno:
            continue
        group_travelers = [e for e in enriched_travelers if e.get('group_no') == gno]
        metrics_for_group = {}
        for key, _ in metric_defs:
            vals = []
            for e in group_travelers:
                try:
                    vals.append(float(e.get(key) or 0))
                except (ValueError, TypeError):
                    pass
            metrics_for_group[key] = {'label': _, 'mean': _calc_mean(vals)}
        total_vals = []
        for e in group_travelers:
            s = 0.0
            valid = False
            for key, _ in metric_defs:
                try:
                    v = float(e.get(key) or 0)
                except (ValueError, TypeError):
                    v = 0
                if v:
                    valid = True
                s += v
            if valid:
                total_vals.append(s / len(metric_defs))
        total_mean = _calc_mean(total_vals)
        group_entry = {
            'group_no': gno,
            'region': g.region or '',
            'agency': g.agency or '',
            'hotel': g.hotel or '',
            'start_date': g.start_date.isoformat() if g.start_date else '',
            'end_date': g.end_date.isoformat() if g.end_date else '',
            'feedback_rate': g.feedback_rate or '',
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
            rows = sorted(rows, key=lambda r: (float(r.get(col)) if isinstance(r.get(col), (int, float)) or (isinstance(r.get(col), str) and r.get(col).replace('.', '', 1).isdigit()) else r.get(col) or ''), reverse=rev)
        total = len(rows)
        start = (page - 1) * page_size
        page_rows = rows[start:start + page_size]
        return JsonResponse({'rows': page_rows, 'total': total, 'page': page, 'total_pages': max(1, (total + page_size - 1) // page_size)})

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
            # 字符串列（团号/地区/地接社/酒店/日期）统一用 str 排序，避免 0 与 str 比较导致 TypeError
            str_cols = {'group_no', 'region', 'agency', 'hotel', 'start_date', 'end_date', 'feedback_rate'}
            def _sort_val(r):
                v = r.get(col)
                if v is None or v == '':
                    return '' if col in str_cols else 0
                if col in str_cols:
                    return str(v).replace('%', '')
                s = str(v).replace('%', '')
                try:
                    return float(s)
                except ValueError:
                    return str(v)
            rev = order != 'asc'
            rows = sorted(rows, key=_sort_val, reverse=rev)
        total = len(rows)
        start = (page - 1) * page_size
        page_rows = rows[start:start + page_size]
        return JsonResponse({'rows': page_rows, 'total': total, 'page': page, 'total_pages': max(1, (total + page_size - 1) // page_size)})

    return JsonResponse({'error': 'invalid table'}, status=400)
