from django.urls import path
from core.api.vacancies import VacancyCreateAPIView

urlpatterns = [
    path('vacancies/', VacancyCreateAPIView.as_view(), name='vacancy-create'),
]
