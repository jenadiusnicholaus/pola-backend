"""
Tanzania Statutes / Sheria za Nchi.

Categories are bilingual. One PDF statute can belong to many categories (M2M).
Soft delete uses is_active + deleted_at (no hard delete from API destroy).
"""
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class SoftDeleteQuerySet(models.QuerySet):
    def alive(self):
        return self.filter(is_active=True, deleted_at__isnull=True)

    def deleted(self):
        return self.filter(models.Q(is_active=False) | models.Q(deleted_at__isnull=False))


class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db)

    def alive(self):
        return self.get_queryset().alive()


class StatuteCategory(models.Model):
    name = models.CharField(max_length=255, help_text='Category name (English)')
    name_sw = models.CharField(max_length=255, help_text='Category name (Swahili)')
    slug = models.SlugField(max_length=280, unique=True, blank=True)
    description = models.TextField(blank=True, default='')
    description_sw = models.TextField(blank=True, default='')
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        db_table = 'statute_categories'
        ordering = ['sort_order', 'name']
        verbose_name = 'Statute Category'
        verbose_name_plural = 'Statute Categories'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name) or 'category'
            slug = base
            i = 1
            while StatuteCategory.all_objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base}-{i}'
                i += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def soft_delete(self):
        self.is_active = False
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_active', 'deleted_at', 'updated_at'])

    def restore(self):
        self.is_active = True
        self.deleted_at = None
        self.save(update_fields=['is_active', 'deleted_at', 'updated_at'])


class Statute(models.Model):
    title = models.CharField(max_length=500, help_text='Title (English)')
    title_sw = models.CharField(max_length=500, help_text='Title (Swahili)')
    description = models.TextField(blank=True, default='')
    description_sw = models.TextField(blank=True, default='')
    file = models.FileField(
        upload_to='statutes/pdfs/%Y/%m/',
        help_text='PDF file for this law',
    )
    file_size = models.PositiveBigIntegerField(default=0, help_text='File size in bytes')
    categories = models.ManyToManyField(
        StatuteCategory,
        related_name='statutes',
        blank=True,
    )
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        db_table = 'statutes'
        ordering = ['sort_order', 'title']
        verbose_name = 'Statute'
        verbose_name_plural = 'Statutes'

    def __str__(self):
        return self.title

    def soft_delete(self):
        self.is_active = False
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_active', 'deleted_at', 'updated_at'])

    def restore(self):
        self.is_active = True
        self.deleted_at = None
        self.save(update_fields=['is_active', 'deleted_at', 'updated_at'])
