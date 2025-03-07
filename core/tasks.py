import logging
import os
import json
from celery import shared_task
from django.db import transaction
from openai import OpenAI

from core.models import (
    Vacancy,
    JobCategory,
    JobSubcategory,
    AnalysisKeyRequirement,
    VacancyAnalysis
)
from core.utils import send_debug_telegram

logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise EnvironmentError("API key for OpenAI is not set in environment variables.")

client = OpenAI(api_key=OPENAI_API_KEY)

def load_gpt_prompt(file_path="config/prompts/vacancy_processing_prompt.txt"):
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read().strip()

GPT_SYSTEM_PROMPT = load_gpt_prompt()

@shared_task
def process_vacancy_batch():
    # Retrieve up to 10 unprocessed vacancies ordered by creation time.
    VACANCY_BATCH_SIZE = int(os.getenv("VACANCY_BATCH_SIZE"))

    unprocessed = list(Vacancy.objects.filter(is_processed=False).order_by('created_at')[:VACANCY_BATCH_SIZE])
    if len(unprocessed) < VACANCY_BATCH_SIZE:
        print(f"Not {VACANCY_BATCH_SIZE}")
        return

    vacancies_for_gpt = []
    for vac in unprocessed:
        _id = vac.id  # using internal id for mapping
        vacancies_for_gpt.append({
            "id": _id,
            "text": vac.text
        })

    user_payload = {
        "Vacancies": vacancies_for_gpt
    }

    messages = [
        {"role": "system", "content": GPT_SYSTEM_PROMPT},
        {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)}
    ]

    print(messages)

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.0
        )
    except Exception as e:
        error_msg = f"Error calling ChatGPT API: {e}"
        logger.error(error_msg)
        send_debug_telegram(error_msg)
        return

    if not response or not response.choices:
        error_msg = "No response from ChatGPT."
        logger.error(error_msg)
        send_debug_telegram(error_msg)
        return

    print(response.choices)

    chatgpt_content = response.choices[0].message.content.strip()
    # Remove Markdown code fences if present.
    if chatgpt_content.startswith("```"):
        chatgpt_content = chatgpt_content.strip("`").strip()
        if chatgpt_content.lower().startswith("json"):
            chatgpt_content = chatgpt_content[4:].strip()

    try:
        gpt_json = json.loads(chatgpt_content)
    except json.JSONDecodeError as e:
        error_msg = f"Failed to decode JSON from ChatGPT: {e} | content: {chatgpt_content}"
        logger.error(error_msg)
        send_debug_telegram(error_msg)
        return

    if isinstance(gpt_json, list):
        data_vacancies = gpt_json
    else:
        data_vacancies = gpt_json.get("Vacancies", [])

    vacancy_map_by_intid = {v.id: v for v in unprocessed}

    for item in data_vacancies:
        # Ensure item is a dict.
        if not isinstance(item, dict):
            continue

        item_id = item.get("id")
        if item_id is None:
            continue

        vacancy_obj = vacancy_map_by_intid.get(item_id)
        if not vacancy_obj:
            continue

        if item.get("not_a_vacancy"):
            text = vacancy_obj.text
            vacancy_obj.delete()
            send_debug_telegram(f"#notVacancy\n\nVacancy is not a valid vacancy and has been deleted.\n\nText is:\n{text}\n")
            continue

        job_category_name = item.get("job_category")
        job_subcategory_name = item.get("job_subcategory")
        if job_category_name:
            job_category, _ = JobCategory.objects.get_or_create(name=job_category_name)
        else:
            job_category, _ = JobCategory.objects.get_or_create(name="Other")
        job_subcategory = None
        if job_subcategory_name:
            job_subcategory, _ = JobSubcategory.objects.get_or_create(
                category=job_category,
                name=job_subcategory_name
            )
        company = item.get("company")
        location = item.get("location")
        if location in [None, "Не указано"]:
            location = "-"
        employment_type = item.get("employment_type")
        work_format = item.get("work_format")
        salary_range_min = item.get("salary_range_min")
        salary_range_max = item.get("salary_range_max")
        salary_currency = item.get("salary_currency")
        experience_years_required = item.get("experience_years_required")

        with transaction.atomic():
            analysis, created = VacancyAnalysis.objects.get_or_create(vacancy=vacancy_obj)
            analysis.job_category = job_category
            analysis.job_subcategory = job_subcategory
            analysis.company = company or None
            analysis.location = location or None
            analysis.employment_type = employment_type or None
            analysis.work_format = work_format or None
            analysis.salary_range_min = salary_range_min or None
            analysis.salary_range_max = salary_range_max or None
            analysis.salary_currency = salary_currency or None
            analysis.experience_years_required = experience_years_required or None
            analysis.save()

            key_reqs = item.get("key_requirements", [])
            if isinstance(key_reqs, list):
                analysis.key_requirements.clear()
                for req_name in key_reqs:
                    if not req_name.strip():
                        continue
                    kr, _ = AnalysisKeyRequirement.objects.get_or_create(
                        name=req_name.strip(),
                        job_category=job_category
                    )
                    analysis.key_requirements.add(kr)

        vacancy_obj.is_processed = True
        vacancy_obj.save()
        # Build formatted debug message with vacancy text and structured information
        formatted_info = (
            f"Job Category: {job_category.name}\n"
            f"Job Subcategory: {job_subcategory.name if job_subcategory else '-'}\n"
            f"Company: {company if company else '-'}\n"
            f"Location: {location}\n"
            f"Employment Type: {employment_type if employment_type else '-'}\n"
            f"Work Format: {work_format if work_format else '-'}\n"
            f"Salary Range: {salary_range_min if salary_range_min else '-'} - {salary_range_max if salary_range_max else '-'} ({salary_currency if salary_currency else '-'})\n"
            f"Experience Required: {experience_years_required if experience_years_required else '-'}\n"
            f"Key Requirements: {', '.join(key_reqs) if key_reqs else '-'}"
        )
        debug_message = (
            f"#processedVacancy\n"
            f"Vacancy Text:\n{vacancy_obj.text}\n\n"
            f"Formatted Information:\n{formatted_info}"
        )
        send_debug_telegram(debug_message)

    summary_msg = f"#info\nProcessed {len(data_vacancies)} vacancies from ChatGPT response."
    logger.info(summary_msg)
    send_debug_telegram(summary_msg)
