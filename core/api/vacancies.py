import json
from django.http import JsonResponse
from rest_framework.views import APIView
from pydantic import ValidationError
from core.models import Vacancy, Keyword, Area
from core.schemas import VacancyInput
# from core.tasks import update_vacancy_area_and_keywords

class VacancyCreateAPIView(APIView):
    """
    API endpoint for creating a vacancy.
    Uses Pydantic for input validation.
    The vacancy is initially saved without an area.
    A Celery task is then triggered to determine the area via ChatGPT API and to update keywords.
    """

    def post(self, request, *args, **kwargs):
        try:
            # Получаем и валидируем входящие данные через Pydantic
            data = json.loads(request.body)
            validated_data = VacancyInput(**data)
        except (ValidationError, json.JSONDecodeError) as e:
            return JsonResponse({"error": str(e)}, status=400)

        # Создаем вакансию без указания области
        vacancy = Vacancy.objects.create(
            text=validated_data.text,
            source=validated_data.source
        )

        # Запускаем фоновую задачу для определения области и поиска ключевых слов
        # update_vacancy_area_and_keywords.delay(vacancy.id)

        # Отдаем быстрый ответ, не дожидаясь обновления вакансии
        return JsonResponse({
            "id": vacancy.id,
            "text": vacancy.text,
            "source": vacancy.source,
            "message": "Vacancy created. Area determination is in progress."
        }, status=201)