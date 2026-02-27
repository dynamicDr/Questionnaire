from django.urls import path
from .views import hello, questionnaire, questionnaire_view

urlpatterns = [
    path('hello/', hello, name='hello'),
    path('questionnaire/add/', questionnaire, name='questionnaire_add'),
    path('questionnaire/view/', questionnaire_view, name='questionnaire_view'),
]