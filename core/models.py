from django.db import models

class Area(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Area Name")
    class Meta:
        verbose_name = "Area"
        verbose_name_plural = "Areas"
        ordering = ['name']
    def __str__(self):
        return self.name


class Vacancy(models.Model):
    text = models.TextField(verbose_name="Vacancy Text")
    source = models.TextField(verbose_name="Vacancy Source", null=True, blank=True)
    area = models.ForeignKey(
        Area,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="vacancies",
        verbose_name="Area"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    is_processed = models.BooleanField(default=False, verbose_name="Is Processed")
    class Meta:
        verbose_name = "Vacancy"
        verbose_name_plural = "Vacancies"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_at']),
        ]
    def __str__(self):
        return f"Vacancy {self.id}"

class Resume(models.Model):
    telegram_user_id = models.CharField(max_length=50, verbose_name="Telegram User ID")
    text = models.TextField(verbose_name="Resume Text")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    class Meta:
        verbose_name = "Resume"
        verbose_name_plural = "Resumes"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['telegram_user_id']),
            models.Index(fields=['created_at']),
        ]
    def __str__(self):
        return f"Resume {self.id} from User {self.telegram_user_id}"

class JobCategory(models.Model):
    name = models.CharField(max_length=255, unique=True)
    class Meta:
        verbose_name = "Job Category"
        verbose_name_plural = "Job Categories"
    def __str__(self):
        return self.name

class JobSubcategory(models.Model):
    category = models.ForeignKey(JobCategory, on_delete=models.CASCADE, related_name='subcategories')
    name = models.CharField(max_length=255)
    class Meta:
        verbose_name = "Job Subcategory"
        verbose_name_plural = "Job Subcategories"
        unique_together = ("category", "name")
    def __str__(self):
        return f"{self.category.name} -> {self.name}"

class AnalysisKeyRequirement(models.Model):
    name = models.CharField(max_length=255)
    job_category = models.ForeignKey(JobCategory, on_delete=models.CASCADE, related_name='key_requirements')
    class Meta:
        verbose_name = "Analysis Key Requirement"
        verbose_name_plural = "Analysis Key Requirements"
        unique_together = ("name", "job_category")
    def __str__(self):
        return f"{self.name} ({self.job_category.name})"

class VacancyAnalysis(models.Model):
    vacancy = models.OneToOneField(Vacancy, on_delete=models.CASCADE, related_name="analysis")
    job_category = models.ForeignKey(JobCategory, on_delete=models.SET_NULL, null=True)
    job_subcategory = models.ForeignKey(JobSubcategory, on_delete=models.SET_NULL, null=True, blank=True)
    company = models.CharField(max_length=255, null=True, blank=True)
    location = models.CharField(max_length=255, null=True, blank=True)
    employment_type = models.CharField(max_length=50, null=True, blank=True)
    work_format = models.CharField(max_length=50, null=True, blank=True)
    salary_range_min = models.CharField(max_length=50, null=True, blank=True)
    salary_range_max = models.CharField(max_length=50, null=True, blank=True)
    salary_currency = models.CharField(max_length=10, null=True, blank=True)
    experience_years_required = models.CharField(max_length=10, null=True, blank=True)
    key_requirements = models.ManyToManyField(AnalysisKeyRequirement, blank=True, related_name="vacancies_data")
    def __str__(self):
        return f"Analysis for Vacancy {self.vacancy.id}"
