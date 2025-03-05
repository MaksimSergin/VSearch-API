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

logger = logging.getLogger(__name__)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise EnvironmentError("API key for OpenAI is not set in environment variables.")

client = OpenAI(api_key=OPENAI_API_KEY)

# System prompt to instruct ChatGPT on how to parse the vacancies.
GPT_SYSTEM_PROMPT = """YOU ARE A SPECIALIST IN JOB DATA EXTRACTION AND STRUCTURED DATA FORMATTING. YOUR TASK IS TO PARSE JOB VACANCIES FROM A JSON INPUT AND OUTPUT THE INFORMATION IN A **CLEAN JSON FORMAT** FOR EASY PROCESSING VIA AN API.

<instructions>
- THE USER INPUT WILL BE A JSON OBJECT WITH A KEY "Vacancies" CONTAINING AN ARRAY OF VACANCY OBJECTS. EACH VACANCY OBJECT WILL HAVE:
  - **id**: The unique identifier of the vacancy.
  - **text**: The raw vacancy text.
- FOR EACH VACANCY, FIRST DETERMINE IF THE TEXT IS A VALID VACANCY. A VALID VACANCY SHOULD CONTAIN CLEAR DETAILS SUCH AS A SALARY RANGE, JOB REQUIREMENTS, OR SECTIONS LIKE "Обязанности:" OR "Требования:". IF THESE ELEMENTS ARE MISSING, TREAT THE TEXT AS NOT A VALID VACANCY.
- IF THE TEXT IS A VALID VACANCY, EXTRACT THE FOLLOWING FIELDS:
  - **id** (preserve the input id)
  - **job_category** (string, must be exactly one of the following: "Developer", "QA", "Manager", "DevOps & Infrastructure", "Data & Machine Learning", "Security", "Design / UX", "Business Analysis", "Support", "Other")
  - **job_subcategory** (string, must be exactly one of the sub-categories corresponding to the chosen job_category. For example:
    - For "Developer": "Java/Scala", "C#", "Go", "Ruby", "Python", "Android", "iOS", "Database", "1C", "Frontend", "Fullstack", "Other"
    - For "QA": "Manual", "Automation", "Performance", "Security", "Lead", "Other"
    - For "Manager": "Product", "Project", "Engineering", "Delivery", "Scrum Master", "Other"
    - For "DevOps & Infrastructure": "DevOps Engineer", "SRE (Site Reliability Engineer)", "Systems Administrator", "Cloud Engineer", "Network Engineer", "Other"
    - For "Data & Machine Learning": "Data Scientist", "Data Engineer", "Machine Learning Engineer", "Deep Learning Engineer", "ML Researcher", "Data Analyst", "BI Specialist", "Other"
    - For "Security": "Cybersecurity Analyst", "Security Engineer", "Penetration Tester", "Security Architect", "Other"
    - For "Design / UX": "UI/Visual Designer", "UX Designer", "Interaction Designer", "UX Researcher", "Other"
    - For "Business Analysis": "Business Analyst", "System Analyst", "Other"
    - For "Support": "Technical Support", "Customer Support", "Helpdesk", "Other"
    - For "Other": "Other"
  )
  - **company** (string)
  - **location** (string; if the location is missing or "Не указано", output "-")
  - **employment_type** (string, must be exactly one of: "Full-time", "Part-time", "Contract", "Other")
  - **work_format** (string, must be exactly one of: "remote", "on-site", "hybrid", "Other")
  - **salary_range_min** (string, the minimum salary; if not available, output "-")
  - **salary_range_max** (string, the maximum salary; if not available, output "-")
  - **salary_currency** (string, e.g., "RUB", "USD")
  - **experience_years_required** (string, e.g., "5")
  - **key_requirements** (list of strings containing keywords that match database entries; extract keywords rather than full descriptions)
- IF THE TEXT DOES NOT CONTAIN CLEAR VACANCY DETAILS (FOR EXAMPLE, IT IS A COLLECTION OF VACANCY HEADLINES, PROMOTIONAL CONTENT, OR DOES NOT CONTAIN DETAILS LIKE A SALARY RANGE, "Обязанности:" OR "Требования:"), THEN OUTPUT A JSON OBJECT WITH ONLY:
  - **id** (preserve the input id)
  - **not_a_vacancy**: true
- IF A FIELD IS MISSING FROM A VALID VACANCY TEXT, EXCLUDE IT FROM THE OUTPUT.
</instructions>

<what not to do>
- NEVER OUTPUT ANYTHING OTHER THAN A VALID JSON OBJECT.
- NEVER INCLUDE HASHTAGS OR UNNECESSARY SYMBOLS.
- NEVER ADD EXTRA TEXT, COMMENTS, OR EXPLANATIONS OUTSIDE OF JSON.
- NEVER INVENT MISSING INFORMATION.
- DO NOT INCLUDE ANY FIELD FOR KEY_RESPONSIBILITIES OR APPLICATION_CONTACT.
</what not to do>

<example>

<USER INPUT>
{
  "Vacancies": [
    {
      "id": 90834,
      "text": "Senior GO разработчик  \nОт 400 000 ₽ на руки\n\nОбязанности:\n• Проектирование архитектуры и сервисов для приложений B2C и B2B  \n• Обеспечение отказоустойчивости разработанных сервисов в среде Digital Ocean  \n• Разработка и улучшение бэкэнд-сервисов для поддержки роста торговой платформы  \n• Создание сервиса с высоким трафиком и большим количеством пользователей и объектов взаимодействия  \n• Участие в обсуждениях новых функций и разработки продукта\n\nТребования:\n• Более пяти лет опыта коммерческого программирования на Go  \n• Опыт работы с горутинами и их отладки  \n• Понимание архитектуры микросервисов  \n• Опыт разработки с API REST и API gRPC  \n• Знакомство с системами мониторинга, такими как Zabbix, Prometheus и другими\n\nМы предлагаем:\n• Отсутствие привязки к локации, можно работать из любой точки мира  \n• Широкая вилка выше рынка  \n• Профессиональное развитие в highload и web3 пространствах  \n• Годовые бонусы и акции на основе производительности и достигнутых результатов\n\nКонтакты:\n+79991111111  \njukislitsyna@rockits.ru"
    },
    {
      "id": 93282,
      "text": "текст второй вакансии"
    },
    {
      "id": 93285,
      "text": "Собрали еженедельную подборку вакансий, на которые стоит обратить внимание в первую очередь. Здесь то, что getmatch нашёл для вас:\n\nTeam Lead / Architect TypeScript, NodeJS [Remote] @ Upfirst\n5 000 —‍ 7 000 $/мес на руки\n👩‍💻 Полная удалёнка\n\nАрхитектор решений (Solution Architect) [Remote] @ ГНИВЦ\n400 000 —‍ 530 000 ₽/мес на руки\n👩‍💻 Можно работать удалённо из РФ\n\nLead QA Automation (iOS) [Remote] @ 2ГИС\n350 000 —‍ 500 000 ₽/мес на руки\n👩‍💻 Полная удалёнка\n\nQA Automation в команду Private Users [Remote] @ Avito\n250 000 —‍ 350 000 ₽/мес на руки\n👩‍💻 Полная удалёнка"
    },
    {
      "id": 93242,
      "text": "Юридическая поддержка для селлеров!\n\nВедете бизнес на маркетплейсах, но сталкиваетесь с юридическими трудностями? Не знаете, как защитить свои права или избежать штрафов? Мы поможем!\n\nНаши услуги:\n\n1. Нарушение авторских прав. Конкурент украл вашу фотографию — мы взыщем компенсацию.\n\n2. Ответы на претензии правообладателей. Поможем выработать корректную стратегию ответа и сохранить карточку товара."
    }
  ]
}
</USER INPUT>

<MODEL OUTPUT>
json
{
  "Vacancies": [
    {
      "id": 90834,
      "job_category": "Developer",
      "job_subcategory": "Go",
      "company": "Rockits",
      "location": "-",
      "employment_type": "Full-time",
      "work_format": "remote",
      "salary_range_min": "400000",
      "salary_range_max": "-",
      "salary_currency": "RUB",
      "experience_years_required": "5",
      "key_requirements": [
        "Go",
        "Горутины",
        "Микросервисы",
        "API REST",
        "API gRPC",
        "Zabbix",
        "Prometheus"
      ]
    },
    {
      "id": 93282,
      "not_a_vacancy": true
    },
    {
      "id": 93285,
      "not_a_vacancy": true
    },
    {
      "id": 93242,
      "not_a_vacancy": true
    }
  ]
}
</MODEL OUTPUT>
"""


@shared_task
def process_vacancy_batch():
    # Retrieve up to 10 unprocessed vacancies ordered by creation time.
    unprocessed = list(Vacancy.objects.filter(is_processed=False).order_by('created_at')[:10])
    if len(unprocessed) < 10:
        print("Not 10")
        return

    vacancies_for_gpt = []
    for vac in unprocessed:
        _id = vac.id  # using the internal id for mapping
        vacancies_for_gpt.append({
            "id": _id,
            "text": vac.text
        })

    user_payload = {
        "Vacancies": vacancies_for_gpt
    }

    # Serialize payload using json.dumps to ensure proper JSON formatting.
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
        logger.error(f"ChatGPT API error: {e}")
        return

    if not response or not response.choices:
        logger.error("No response from ChatGPT.")
        return

    # Retrieve the ChatGPT response content.
    print(response.choices)
    chatgpt_content = response.choices[0].message.content.strip()
    # Remove Markdown code fences if present.
    if chatgpt_content.startswith("```"):
        # Remove leading and trailing backticks.
        chatgpt_content = chatgpt_content.strip("`").strip()
        # If a language tag is present (e.g., "json"), remove it.
        if chatgpt_content.lower().startswith("json"):
            chatgpt_content = chatgpt_content[4:].strip()

    try:
        gpt_json = json.loads(chatgpt_content)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON from ChatGPT: {e} | content: {chatgpt_content}")
        return
    print(gpt_json)

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
            vacancy_obj.delete()
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

    logger.info(f"Processed {len(data_vacancies)} vacancies from ChatGPT.")