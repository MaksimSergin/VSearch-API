from django.db import models

class Area(models.Model):
    """
    Model for storing vacancy areas (e.g., IT, Marketing, Finance, etc.).
    """
    name = models.CharField(max_length=100, unique=True, verbose_name="Area Name")

    class Meta:
        verbose_name = "Area"
        verbose_name_plural = "Areas"
        ordering = ['name']

    def __str__(self):
        return self.name


class Keyword(models.Model):
    """
    Model for storing keywords.
    The keyword is always saved in lowercase.
    """
    keyword = models.CharField(max_length=100, unique=True, verbose_name="Keyword")

    class Meta:
        verbose_name = "Keyword"
        verbose_name_plural = "Keywords"
        ordering = ['keyword']

    def save(self, *args, **kwargs):
        self.keyword = self.keyword.lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.keyword


class Vacancy(models.Model):
    """
    Model for storing vacancies.
    Each vacancy may have an associated area and a set of keywords.
    """
    text = models.TextField(verbose_name="Vacancy Text")
    area = models.ForeignKey(
        Area,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="vacancies",
        verbose_name="Area"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    keywords = models.ManyToManyField(Keyword, blank=True, related_name="vacancies", verbose_name="Keywords")

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
    """
    Model for storing resumes.
    Each resume is linked to a Telegram user.
    """
    telegram_user_id = models.CharField(max_length=50, verbose_name="Telegram User ID")
    text = models.TextField(verbose_name="Resume Text")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    keywords = models.ManyToManyField(Keyword, blank=True, related_name="resumes", verbose_name="Keywords")

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
