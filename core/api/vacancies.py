import json
from django.http import JsonResponse
from rest_framework.views import APIView
from pydantic import ValidationError
from core.models import Vacancy
from core.schemas import VacancyInput
from core.services import VacancyDuplicateDetector

class VacancyCreateAPIView(APIView):
    """
    API endpoint for creating a vacancy.
    Uses Pydantic for input validation.
    The vacancy is initially saved without an area.
    A Celery task is then triggered to determine the area via ChatGPT API and to update keywords.
    """

    def post(self, request, *args, **kwargs):
        try:
            validated_data = VacancyInput(**request.data)
        except (ValidationError, json.JSONDecodeError) as e:
            return JsonResponse({"error": str(e)}, status=400)

        # Загружаем все существующие вакансии (только текст) из базы данных
        existing_vacancies = list(Vacancy.objects.values_list('text', flat=True))
        detector = VacancyDuplicateDetector(threshold=0.85, initial_vacancies=existing_vacancies)

        # Проверяем, является ли новая вакансия дубликатом
        is_dup, sim = detector.is_duplicate(validated_data.text)
        if is_dup:
            return JsonResponse(
                {"error": f"Вакансия уже существует (дубликат). Сходство: {sim:.2f}"},
                status=400
            )

        # Если не дублируется, создаём вакансию
        vacancy = Vacancy.objects.create(
            text=validated_data.text,
            source=validated_data.source
        )

        # Запускаем фоновую задачу для определения области и поиска ключевых слов
        # update_vacancy_area_and_keywords.delay(vacancy.id)

        return JsonResponse({
            "id": vacancy.id,
            "text": vacancy.text,
            "source": vacancy.source,
            "message": "Vacancy created. Area determination is in progress."
        }, status=201)
