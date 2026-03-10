from django.urls import path
from .views import (
    hello,
    questionnaire,
    info_modify,
    questionnaire_view,
    view_data_api,
    group_info_api,
    supplier_guide,
    supplier_hotel,
    supplier_agency,
    supplier_vehicle,
    supplier_meal,
    questionnaire_analysis,
)

urlpatterns = [
    path('hello/', hello, name='hello'),
    path('questionnaire/add/', questionnaire, name='questionnaire_add'),
    path('questionnaire/modify/', info_modify, name='info_modify'),
    path('questionnaire/view/', questionnaire_view, name='questionnaire_view'),
    path('questionnaire/view/data/', view_data_api, name='view_data_api'),
    path('questionnaire/group/info/', group_info_api, name='group_info_api'),
    path('supplier/import/guide/', supplier_guide, name='supplier_guide'),
    path('supplier/import/hotel/', supplier_hotel, name='supplier_hotel'),
    path('supplier/import/agency/', supplier_agency, name='supplier_agency'),
    path('supplier/import/vehicle/', supplier_vehicle, name='supplier_vehicle'),
    path('supplier/import/meal/', supplier_meal, name='supplier_meal'),
    path('questionnaire/analysis/', questionnaire_analysis, name='questionnaire_analysis'),
]