import json
import os

from django.http import JsonResponse
from rest_framework.views import APIView
from pydantic import ValidationError
from core.models import Vacancy
from core.schemas import VacancyInput
from core.services import VacancyDuplicateDetector
from core.utils import send_debug_telegram


class VacancyCreateAPIView(APIView):
    def post(self, request, *args, **kwargs):
        try:
            validated_data = VacancyInput(**request.data)
        except (ValidationError, json.JSONDecodeError) as e:
            return JsonResponse({"error": str(e)}, status=400)

        VACANCY_MIN_LENGTH = os.getenv("VACANCY_MIN_LENGTH")
        if len(validated_data.text) < int(VACANCY_MIN_LENGTH):
            return JsonResponse({"error": "Vacancy is too small"}, status=400)

        existing_vacancies_texts = list(Vacancy.objects.values_list('text', flat=True))
        detector = VacancyDuplicateDetector(threshold=0.85, initial_vacancies=existing_vacancies_texts)

        is_dup, sim, orig = detector.is_duplicate(validated_data.text)
        if is_dup:
            send_debug_telegram(f"#duplicate\nVacancy is duplicate with similarity {sim:.2f}.\n\nDuplicate text:\n{validated_data.text}\n\nOriginal vacancy:\n{orig}")
            return JsonResponse(
                {"error": f"Вакансия уже существует (дубликат). Сходство: {sim:.2f}"},
                status=400
            )

        vacancy = Vacancy.objects.create(
            text=validated_data.text,
            source=validated_data.source or ""
        )

        return JsonResponse({
            "id": vacancy.id,
            "text": vacancy.text,
            "source": vacancy.source,
            "message": "Vacancy created. It will be processed later in a batch with ChatGPT."
        }, status=201)
