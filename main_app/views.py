from decimal import Decimal
from urllib.parse import urlencode

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.urls import reverse
from django.db.models import Count
from pypinyin import lazy_pinyin, Style

from .models import Group, Traveler, FullEscort, SupplierAgency, SupplierGuide


def hello(request):
    return render(request, 'hello.html', {
        'message': 'Hello World!'
    })


def _to_initials(text: str) -> str:
    """
    使用 pypinyin 生成字符串的“拼音首字母串”，用于后端模糊匹配。
    - 中文：用 FIRST_LETTER 模式，按顺序拼接所有字的首字母
    - 英文：保留原字母的小写形式
    - 其他字符：忽略
    """
    if not text:
        return ''
    # 先整体跑一遍 FIRST_LETTER，让汉字得到首字母
    letters = lazy_pinyin(text, style=Style.FIRST_LETTER, errors='ignore')
    # lazy_pinyin 遇到英文会原样返回（按字符拆），我们统一转小写
    return ''.join((ch or '').lower() for ch in letters if ch)


def supplier_guide(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        index_str = request.POST.get('index')
        if action == 'create':
            name_cn = request.POST.get('name_cn', '').strip()
            guide_type = request.POST.get('guide_type', SupplierGuide.GUIDE_TYPE_LOCAL).strip() or SupplierGuide.GUIDE_TYPE_LOCAL
            name_en = request.POST.get('name_en', '').strip()
            language = request.POST.get('language', '').strip()
            region = request.POST.get('region', '').strip()
            confirm_overwrite = request.POST.get('confirm_overwrite') == '1'
            if name_cn:
                existing = SupplierGuide.objects.filter(name_cn=name_cn).first()
                if existing and confirm_overwrite:
                    existing.guide_type = guide_type
                    existing.name_en = name_en
                    existing.language = language
                    existing.region = region
                    existing.name_initials = _to_initials(name_cn or name_en)
                    existing.save()
                    return redirect('supplier_guide')
                if existing and not confirm_overwrite:
                    guides = SupplierGuide.objects.all().order_by('-id')
                    context = {
                        'guides': guides,
                        'guide_type_local': SupplierGuide.GUIDE_TYPE_LOCAL,
                        'guide_type_full': SupplierGuide.GUIDE_TYPE_FULL,
                        'guide_exists': True,
                        'existing_guide': existing,
                        'create_form_data': {
                            'guide_type': guide_type,
                            'name_cn': name_cn,
                            'name_en': name_en,
                            'language': language,
                            'region': region,
                        },
                    }
                    return render(request, 'supplier_guide.html', context)
                if not existing:
                    SupplierGuide.objects.create(
                        guide_type=guide_type,
                        name_cn=name_cn,
                        name_en=name_en,
                        language=language,
                        region=region,
                        name_initials=_to_initials(name_cn or name_en),
                    )
        elif action in ('update', 'delete') and index_str:
            try:
                g = get_object_or_404(SupplierGuide, pk=int(index_str))
                if action == 'update':
                    name_cn = request.POST.get('name_cn', '').strip()
                    if name_cn:
                        g.guide_type = request.POST.get('guide_type', SupplierGuide.GUIDE_TYPE_LOCAL).strip() or SupplierGuide.GUIDE_TYPE_LOCAL
                        g.name_cn = name_cn
                        g.name_en = request.POST.get('name_en', '').strip()
                        g.language = request.POST.get('language', '').strip()
                        g.region = request.POST.get('region', '').strip()
                        g.name_initials = _to_initials(name_cn or g.name_en)
                        g.save()
                elif action == 'delete':
                    g.delete()
            except (ValueError, TypeError):
                pass
        return redirect('supplier_guide')

    guides = SupplierGuide.objects.all().order_by('-id')
    context = {
        'guides': guides,
        'guide_type_local': SupplierGuide.GUIDE_TYPE_LOCAL,
        'guide_type_full': SupplierGuide.GUIDE_TYPE_FULL,
    }
    return render(request, 'supplier_guide.html', context)


def supplier_hotel(request):
    return render(request, 'blank_page.html')


def supplier_agency(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        index_str = request.POST.get('index')
        if action == 'create':
            name = request.POST.get('name', '').strip()
            region = request.POST.get('region', '').strip()
            confirm_overwrite = request.POST.get('confirm_overwrite') == '1'
            if name:
                existing = SupplierAgency.objects.filter(name=name).first()
                if existing and confirm_overwrite:
                    existing.region = region
                    existing.name_initials = _to_initials(name)
                    existing.save()
                    return redirect('supplier_agency')
                if existing and not confirm_overwrite:
                    agencies = SupplierAgency.objects.all().order_by('-id')
                    context = {
                        'agencies': agencies,
                        'agency_exists': True,
                        'existing_agency': existing,
                        'create_form_data': {
                            'name': name,
                            'region': region,
                        },
                    }
                    return render(request, 'supplier_agency.html', context)
                if not existing:
                    SupplierAgency.objects.create(
                        name=name,
                        region=region,
                        name_initials=_to_initials(name),
                    )
        elif action in ('update', 'delete') and index_str:
            try:
                a = get_object_or_404(SupplierAgency, pk=int(index_str))
                if action == 'update':
                    name = request.POST.get('name', '').strip()
                    if name:
                        exists = SupplierAgency.objects.filter(name=name).exclude(pk=a.pk).exists()
                        if not exists:
                            a.name = name
                            a.region = request.POST.get('region', '').strip()
                            a.name_initials = _to_initials(name)
                            a.save()
                elif action == 'delete':
                    a.delete()
            except (ValueError, TypeError):
                pass
        return redirect('supplier_agency')

    agencies = SupplierAgency.objects.all().order_by('-id')
    return render(request, 'supplier_agency.html', {'agencies': agencies})


def supplier_vehicle(request):
    return render(request, 'blank_page.html')


def supplier_meal(request):
    return render(request, 'blank_page.html')


def questionnaire_analysis(request):
    return render(request, 'blank_page.html')


# ===== 问卷（questionnaire）相关逻辑，使用数据库 =====

def _group_to_dict(g):
    return {
        'group_no': g.group_no or '',
        'people_count': g.people_count or 0,
        'feedback_count': g.feedback_count or 0,
        'feedback_rate': g.feedback_rate or '',
        'date': g.date or '',
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
        'region': t.region or '',
        'agency': t.agency or '',
        'guide': t.guide or '',
        'guide_language': _score_int(t.guide_language),
        'guide_service': _score_int(t.guide_service),
        'vehicle_comfort': _score_int(t.vehicle_comfort),
        'vehicle_clean': _score_int(t.vehicle_clean),
        'driver_service': _score_int(t.driver_service),
        'food_quality': _score_int(t.food_quality),
        'restaurant_environment': _score_int(t.restaurant_environment),
    }


def _full_escort_to_dict(f):
    return {
        'group_no': f.group.group_no if f.group_id else '',
        'region': f.region or '',
        'agency': f.agency or '',
        'guide': f.guide or '',
        'pace': _score_int(f.pace),
        'explanation': _score_int(f.explanation),
        'service': _score_int(f.service),
        'design': _score_int(f.design),
        'expectation': _score_int(f.expectation),
        'recommendation': _score_int(f.recommendation),
        'overall': _score_int(f.overall),
    }


def _parse_id_csv(raw):
    ids = []
    for x in (raw or '').split(','):
        x = x.strip()
        if x.isdigit():
            ids.append(int(x))
    return ids


def _join_id_csv(ids):
    seen = set()
    ordered = []
    for i in ids:
        if i not in seen:
            seen.add(i)
            ordered.append(i)
    return ','.join(str(i) for i in ordered)


def _compute_feedback_rate(people_count, feedback_count):
    try:
        pc = int(people_count)
        fc = int(feedback_count)
        if pc > 0 and 0 <= fc <= pc:
            return str(round(fc / pc / 2, 4))
    except (ValueError, TypeError):
        pass
    return ''


def _build_group_keep_query_from_post(post_data, extra=None):
    data = {
        'g_group_no': post_data.get('group_no', '').strip(),
        'g_agency': post_data.get('agency', '').strip(),
        'g_guide': post_data.get('guide', '').strip(),
        'g_hotel': post_data.get('hotel', '').strip(),
        'g_region': post_data.get('region', '').strip(),
        'g_people_count': post_data.get('people_count', '').strip(),
        'g_feedback_count': post_data.get('feedback_count', '').strip(),
        'g_date': post_data.get('date', '').strip(),
    }
    if extra:
        data.update(extra)
    return urlencode(data)


def group_info_api(request):
    """按团号读取团信息 + 最近一条问卷属性"""
    group_no = (request.GET.get('group_no', '') or '').strip()
    if not group_no:
        return JsonResponse({'ok': False, 'error': 'missing_group_no'}, status=400)

    group = Group.objects.filter(group_no=group_no).first()
    if not group:
        return JsonResponse({'ok': False, 'error': 'group_not_found'}, status=404)

    return JsonResponse({
        'ok': True,
        'group': {
            'group_no': group.group_no or '',
            'people_count': group.people_count or 0,
            'feedback_count': group.feedback_count or 0,
            'date': group.date or '',
        },
    })


def _questionnaire_context(request, group_exists=False, existing_group=None, create_form_data=None):
    """问卷页 GET 或“团号已存在”时的共用 context"""
    last_group_no = request.GET.get('last_group_no', '') if request.method == 'GET' else ''
    focus_traveler = request.GET.get('focus_traveler') == '1' if request.method == 'GET' else False
    focus_full_escort = request.GET.get('focus_full_escort') == '1' if request.method == 'GET' else False
    error = request.GET.get('error', '') if request.method == 'GET' else ''

    groups_qs = Group.objects.all().order_by('group_no').annotate(traveler_count=Count('travelers'))
    groups_for_view = [(g.id, _group_to_dict(g), g.traveler_count) for g in groups_qs]
    group_nos = [g.group_no for g in groups_qs if g.group_no]
    travelers_qs = Traveler.objects.select_related('group').all().order_by('-id')
    travelers = [(t.id, _traveler_to_dict(t)) for t in travelers_qs]
    full_escorts_qs = FullEscort.objects.select_related('group').all().order_by('-id')
    full_escorts = [(f.id, _full_escort_to_dict(f)) for f in full_escorts_qs]
    supplier_agencies = list(
        SupplierAgency.objects.all()
        .order_by('name')
        .values('name', 'name_initials')
    )
    supplier_guides = list(
        SupplierGuide.objects.all()
        .order_by('name_cn')
        .values('name_cn', 'name_en', 'name_initials')
    )

    if create_form_data is None:
        create_form_data = {}
    if request.method == 'GET':
        # 问卷提交后，保持“新增团”区域原值
        for k in ['group_no', 'agency', 'guide', 'hotel', 'region', 'people_count', 'feedback_count', 'date']:
            if request.GET.get(f'g_{k}', ''):
                create_form_data[k] = request.GET.get(f'g_{k}', '')
        # 本次添加的问卷，只展示一次
        recent_once = request.GET.get('recent_once', '') == '1'
        if recent_once:
            recent_traveler_ids = _parse_id_csv(request.GET.get('recent_travelers', ''))
            recent_full_escort_ids = _parse_id_csv(request.GET.get('recent_full_escorts', ''))
        else:
            recent_traveler_ids = []
            recent_full_escort_ids = []
    else:
        recent_traveler_ids = []
        recent_full_escort_ids = []

    recent_travelers_qs = Traveler.objects.select_related('group').filter(id__in=recent_traveler_ids).order_by('-id')
    recent_full_escorts_qs = FullEscort.objects.select_related('group').filter(id__in=recent_full_escort_ids).order_by('-id')
    recent_travelers = [(t.id, _traveler_to_dict(t)) for t in recent_travelers_qs]
    recent_full_escorts = [(f.id, _full_escort_to_dict(f)) for f in recent_full_escorts_qs]

    context = {
        'groups': groups_for_view,
        'group_nos': group_nos,
        'travelers': travelers,
        'full_escorts': full_escorts,
        'supplier_agencies': supplier_agencies,
        'supplier_guides': supplier_guides,
        'recent_travelers': recent_travelers,
        'recent_full_escorts': recent_full_escorts,
        'recent_travelers_param': _join_id_csv(recent_traveler_ids),
        'recent_full_escorts_param': _join_id_csv(recent_full_escort_ids),
        'last_group_no': last_group_no,
        'focus_traveler': focus_traveler,
        'focus_full_escort': focus_full_escort,
        'error': error,
        'create_form_data': create_form_data,
    }
    if group_exists:
        context['group_exists'] = True
        context['existing_group'] = existing_group or {}
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
                    date_s = request.POST.get('date', '').strip()
                    existing_group.people_count = int(people_count) if people_count.isdigit() else 0
                    existing_group.feedback_count = int(feedback_count) if feedback_count.isdigit() else 0
                    existing_group.feedback_rate = _compute_feedback_rate(people_count, feedback_count)
                    existing_group.date = date_s
                    existing_group.save()
                    keep_qs = _build_group_keep_query_from_post(request.POST)
                    return redirect(f"{reverse('questionnaire_add')}?{keep_qs}")
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
                            'date': request.POST.get('date', '').strip(),
                        },
                    )
                    return render(request, 'questionnaire.html', context)
                if group_no and not existing_group:
                    people_count = request.POST.get('people_count', '').strip()
                    feedback_count = request.POST.get('feedback_count', '').strip()
                    date_s = request.POST.get('date', '').strip()
                    Group.objects.create(
                        group_no=group_no,
                        people_count=int(people_count) if people_count.isdigit() else 0,
                        feedback_count=int(feedback_count) if feedback_count.isdigit() else 0,
                        feedback_rate=_compute_feedback_rate(people_count, feedback_count),
                        date=date_s,
                    )
                    keep_qs = _build_group_keep_query_from_post(request.POST)
                    return redirect(f"{reverse('questionnaire_add')}?{keep_qs}")

            elif action in ('update', 'delete') and index_str:
                try:
                    g = get_object_or_404(Group, pk=int(index_str))
                    if action == 'update':
                        group_no = request.POST.get('group_no', '').strip()
                        if group_no and (group_no == g.group_no or not Group.objects.filter(group_no=group_no).exists()):
                            people_count = request.POST.get('people_count', '').strip()
                            feedback_count = request.POST.get('feedback_count', '').strip()
                            g.group_no = group_no
                            g.people_count = int(people_count) if people_count.isdigit() else 0
                            g.feedback_count = int(feedback_count) if feedback_count.isdigit() else 0
                            g.feedback_rate = _compute_feedback_rate(people_count, feedback_count)
                            g.date = request.POST.get('date', '').strip()
                            g.save()
                    elif action == 'delete':
                        g.delete()
                except (ValueError, TypeError):
                    pass

            return redirect('questionnaire_add')

        elif entity == 'traveler':
            index_str = request.POST.get('index')
            if action == 'create':
                # 问卷属性来自“新增团”区域
                group_no = request.POST.get('g_group_no', '').strip()
                agency = request.POST.get('g_agency', '').strip()
                guide = request.POST.get('g_guide', '').strip()
                hotel = request.POST.get('g_hotel', '').strip()
                region = request.POST.get('g_region', '').strip()
                people_count = request.POST.get('g_people_count', '').strip()
                feedback_count = request.POST.get('g_feedback_count', '').strip()
                date_s = request.POST.get('g_date', '').strip()
                if not group_no:
                    qs = urlencode({'error': 'group_not_found'})
                    return redirect(f"{reverse('questionnaire_add')}?{qs}")

                group = Group.objects.filter(group_no=group_no).first()
                if not group:
                    group = Group.objects.create(
                        group_no=group_no,
                        people_count=int(people_count) if people_count.isdigit() else 0,
                        feedback_count=int(feedback_count) if feedback_count.isdigit() else 0,
                        feedback_rate=_compute_feedback_rate(people_count, feedback_count),
                        date=date_s,
                    )
                def _dec(s):
                    try:
                        return Decimal(s) if s else None
                    except (ValueError, TypeError):
                        return None
                traveler = Traveler.objects.create(
                    group=group,
                    agency=agency,
                    guide=guide,
                    hotel=hotel,
                    region=region,
                    guide_language=_dec(request.POST.get('guide_language', '').strip()),
                    guide_service=_dec(request.POST.get('guide_service', '').strip()),
                    vehicle_comfort=_dec(request.POST.get('vehicle_comfort', '').strip()),
                    vehicle_clean=_dec(request.POST.get('vehicle_clean', '').strip()),
                    driver_service=_dec(request.POST.get('driver_service', '').strip()),
                    food_quality=_dec(request.POST.get('food_quality', '').strip()),
                    restaurant_environment=_dec(request.POST.get('restaurant_environment', '').strip()),
                )
                # 维护“本次添加的问卷”ID 列表
                prev_travelers = _parse_id_csv(request.POST.get('recent_travelers', ''))
                prev_full_escorts = _parse_id_csv(request.POST.get('recent_full_escorts', ''))
                recent_travelers = _join_id_csv(prev_travelers + [traveler.id])
                recent_full_escorts = _join_id_csv(prev_full_escorts)

                keep_qs = urlencode({
                    'last_group_no': group_no,
                    'focus_traveler': 1,
                    'g_group_no': group_no,
                    'g_agency': agency,
                    'g_guide': guide,
                    'g_hotel': hotel,
                    'g_region': region,
                    'g_people_count': people_count,
                    'g_feedback_count': feedback_count,
                    'g_date': date_s,
                    'recent_once': 1,
                    'recent_travelers': recent_travelers,
                    'recent_full_escorts': recent_full_escorts,
                })
                url = f"{reverse('questionnaire_add')}?{keep_qs}"
                return redirect(url)

            elif action in ('update', 'delete') and index_str:
                op_ok = False
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
                            op_ok = True
                    elif action == 'delete':
                        t.delete()
                        op_ok = True
                except (ValueError, TypeError):
                    op_ok = False

                # AJAX 请求用于“本次添加的问卷”内联保存/删除
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'ok': op_ok})
                return redirect('questionnaire_add')

        elif entity == 'full_escort':
            if action == 'create':
                group_no = request.POST.get('g_group_no', '').strip()
                agency = request.POST.get('g_agency', '').strip()
                guide = request.POST.get('g_guide', '').strip()
                hotel = request.POST.get('g_hotel', '').strip()
                region = request.POST.get('g_region', '').strip()
                people_count = request.POST.get('g_people_count', '').strip()
                feedback_count = request.POST.get('g_feedback_count', '').strip()
                date_s = request.POST.get('g_date', '').strip()
                if not group_no:
                    qs = urlencode({'error': 'group_not_found', 'focus_full_escort': 1})
                    return redirect(f"{reverse('questionnaire_add')}?{qs}")

                group = Group.objects.filter(group_no=group_no).first()
                if not group:
                    group = Group.objects.create(
                        group_no=group_no,
                        people_count=int(people_count) if people_count.isdigit() else 0,
                        feedback_count=int(feedback_count) if feedback_count.isdigit() else 0,
                        feedback_rate=_compute_feedback_rate(people_count, feedback_count),
                        date=date_s,
                    )

                def _dec(s):
                    try:
                        return Decimal(s) if s else None
                    except (ValueError, TypeError):
                        return None

                full_escort = FullEscort.objects.create(
                    group=group,
                    agency=agency,
                    guide=guide,
                    hotel=hotel,
                    region=region,
                    pace=_dec(request.POST.get('pace', '').strip()),
                    explanation=_dec(request.POST.get('explanation', '').strip()),
                    service=_dec(request.POST.get('service', '').strip()),
                    design=_dec(request.POST.get('design', '').strip()),
                    expectation=_dec(request.POST.get('expectation', '').strip()),
                    recommendation=_dec(request.POST.get('recommendation', '').strip()),
                    overall=_dec(request.POST.get('overall', '').strip()),
                )
                prev_travelers = _parse_id_csv(request.POST.get('recent_travelers', ''))
                prev_full_escorts = _parse_id_csv(request.POST.get('recent_full_escorts', ''))
                recent_travelers = _join_id_csv(prev_travelers)
                recent_full_escorts = _join_id_csv(prev_full_escorts + [full_escort.id])

                keep_qs = urlencode({
                    'last_group_no': group_no,
                    'focus_full_escort': 1,
                    'g_group_no': group_no,
                    'g_agency': agency,
                    'g_guide': guide,
                    'g_hotel': hotel,
                    'g_region': region,
                    'g_people_count': people_count,
                    'g_feedback_count': feedback_count,
                    'g_date': date_s,
                    'recent_once': 1,
                    'recent_travelers': recent_travelers,
                    'recent_full_escorts': recent_full_escorts,
                })
                url = f"{reverse('questionnaire_add')}?{keep_qs}"
                return redirect(url)

            elif action in ('update', 'delete') and index_str:
                op_ok = False
                try:
                    f = get_object_or_404(FullEscort, pk=int(index_str))
                    if action == 'update':
                        group_no = request.POST.get('group_no', '').strip()
                        grp = Group.objects.filter(group_no=group_no).first()
                        if grp:
                            f.group = grp

                            def _dec(s):
                                try:
                                    return Decimal(s) if s else None
                                except (ValueError, TypeError):
                                    return None

                            f.pace = _dec(request.POST.get('pace', '').strip())
                            f.explanation = _dec(request.POST.get('explanation', '').strip())
                            f.service = _dec(request.POST.get('service', '').strip())
                            f.design = _dec(request.POST.get('design', '').strip())
                            f.expectation = _dec(request.POST.get('expectation', '').strip())
                            f.recommendation = _dec(request.POST.get('recommendation', '').strip())
                            f.overall = _dec(request.POST.get('overall', '').strip())
                            f.save()
                            op_ok = True
                    elif action == 'delete':
                        f.delete()
                        op_ok = True
                except (ValueError, TypeError):
                    op_ok = False

                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'ok': op_ok})
                return redirect('questionnaire_add')

    # GET
    context = _questionnaire_context(request)
    return render(request, 'questionnaire.html', context)


def info_modify(request):
    """信息修改页：仅处理团/旅客的更新与删除"""
    if request.method == 'POST':
        entity = request.POST.get('entity')
        action = request.POST.get('action')

        if entity == 'group':
            index_str = request.POST.get('index')
            if action in ('update', 'delete') and index_str:
                try:
                    g = get_object_or_404(Group, pk=int(index_str))
                    if action == 'update':
                        group_no = request.POST.get('group_no', '').strip()
                        if group_no and (group_no == g.group_no or not Group.objects.filter(group_no=group_no).exists()):
                            people_count = request.POST.get('people_count', '').strip()
                            feedback_count = request.POST.get('feedback_count', '').strip()
                            g.group_no = group_no
                            g.people_count = int(people_count) if people_count.isdigit() else 0
                            g.feedback_count = int(feedback_count) if feedback_count.isdigit() else 0
                            g.feedback_rate = _compute_feedback_rate(people_count, feedback_count)
                            g.date = request.POST.get('date', '').strip()
                            g.save()
                    elif action == 'delete':
                        g.delete()
                except (ValueError, TypeError):
                    pass

        elif entity == 'traveler':
            index_str = request.POST.get('index')
            if action in ('update', 'delete') and index_str:
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

        elif entity == 'full_escort':
            index_str = request.POST.get('index')
            if action in ('update', 'delete') and index_str:
                try:
                    f = get_object_or_404(FullEscort, pk=int(index_str))
                    if action == 'update':
                        group_no = request.POST.get('group_no', '').strip()
                        grp = Group.objects.filter(group_no=group_no).first()
                        if grp:
                            f.group = grp

                            def _dec(s):
                                try:
                                    return Decimal(s) if s else None
                                except (ValueError, TypeError):
                                    return None

                            f.pace = _dec(request.POST.get('pace', '').strip())
                            f.explanation = _dec(request.POST.get('explanation', '').strip())
                            f.service = _dec(request.POST.get('service', '').strip())
                            f.design = _dec(request.POST.get('design', '').strip())
                            f.expectation = _dec(request.POST.get('expectation', '').strip())
                            f.recommendation = _dec(request.POST.get('recommendation', '').strip())
                            f.overall = _dec(request.POST.get('overall', '').strip())
                            f.save()
                    elif action == 'delete':
                        f.delete()
                except (ValueError, TypeError):
                    pass

        # 根据操作的实体类型决定返回时默认聚焦的标签页
        if entity == 'full_escort':
            return redirect(f"{reverse('info_modify')}?focus_full_escort=1")
        elif entity == 'traveler':
            return redirect(f"{reverse('info_modify')}?focus_traveler=1")
        else:
            return redirect('info_modify')

    context = _questionnaire_context(request)
    return render(request, 'info_modify.html', context)


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
            'region': t.region or '',
            'agency': t.agency or '',
            'hotel': t.hotel or '',
            'date': g.date if g and g.date else '',
            'start_date': '',
            'end_date': g.date if g and g.date else '',
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
            'region': next((e.get('region') for e in group_travelers if e.get('region')), ''),
            'agency': next((e.get('agency') for e in group_travelers if e.get('agency')), ''),
            'hotel': next((e.get('hotel') for e in group_travelers if e.get('hotel')), ''),
            'date': g.date or '',
            'start_date': '',
            'end_date': g.date or '',
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
        date_from = request.GET.get('date_from', '') or request.GET.get('end_from', '')
        date_to = request.GET.get('date_to', '') or request.GET.get('end_to', '')
        key_map = {'agency': 'agency', 'region': 'region', 'hotel': 'hotel'}
        key_field = key_map.get(by, 'agency')
        label_map = {'agency': '地接社', 'region': '地区', 'hotel': '酒店'}
        label = label_map.get(by, '地接社')

        filtered_stats = [g for g in group_stats if
            (not date_from or (g.get('date') or '') >= date_from) and
            (not date_to or (g.get('date') or '') <= date_to)
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
        date_from = request.GET.get('date_from', '') or request.GET.get('end_from', '')
        date_to = request.GET.get('date_to', '') or request.GET.get('end_to', '')
        rows = [r for r in rows if
            (not kw_group or (r.get('group_no') or '').lower().find(kw_group) >= 0) and
            (not kw_region or (r.get('region') or '').lower().find(kw_region) >= 0) and
            (not kw_agency or (r.get('agency') or '').lower().find(kw_agency) >= 0) and
            (not kw_hotel or (r.get('hotel') or '').lower().find(kw_hotel) >= 0) and
            (not date_from or (r.get('date') or r.get('end_date') or '') >= date_from) and
            (not date_to or (r.get('date') or r.get('end_date') or '') <= date_to)
        ]
        sort_col_map = {
            'group_no': 'group_no', 'region': 'region', 'agency': 'agency', 'hotel': 'hotel',
            'date': 'date', 'start_date': 'start_date', 'end_date': 'end_date',
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
        date_from = request.GET.get('date_from', '') or request.GET.get('end_from', '')
        date_to = request.GET.get('date_to', '') or request.GET.get('end_to', '')
        rows = [r for r in rows if
            (not kw_group or (r.get('group_no') or '').lower().find(kw_group) >= 0) and
            (not kw_region or (r.get('region') or '').lower().find(kw_region) >= 0) and
            (not kw_agency or (r.get('agency') or '').lower().find(kw_agency) >= 0) and
            (not kw_hotel or (r.get('hotel') or '').lower().find(kw_hotel) >= 0) and
            (not date_from or (r.get('date') or r.get('end_date') or '') >= date_from) and
            (not date_to or (r.get('date') or r.get('end_date') or '') <= date_to)
        ]
        sort_col_map = {
            'group_no': 'group_no', 'region': 'region', 'agency': 'agency', 'hotel': 'hotel',
            'date': 'date', 'start_date': 'start_date', 'end_date': 'end_date', 'feedback_rate': 'feedback_rate',
            'guide_language_mean': 'guide_language_mean', 'guide_service_mean': 'guide_service_mean',
            'vehicle_comfort_mean': 'vehicle_comfort_mean', 'vehicle_clean_mean': 'vehicle_clean_mean',
            'driver_service_mean': 'driver_service_mean', 'food_quality_mean': 'food_quality_mean',
            'restaurant_environment_mean': 'restaurant_environment_mean', 'total_mean': 'total_mean',
        }
        col = sort_col_map.get(sort_key, '')
        if col:
            # 字符串列（团号/地区/地接社/酒店/日期）统一用 str 排序，避免 0 与 str 比较导致 TypeError
            str_cols = {'group_no', 'region', 'agency', 'hotel', 'date', 'start_date', 'end_date', 'feedback_rate'}
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
