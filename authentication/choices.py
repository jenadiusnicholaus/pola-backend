from django.db import models
from django.utils.translation import gettext_lazy as _

GENDER_CHOICES = [
    ('M', _('Male')),
    ('F', _('Female')),
]

PRACTICE_STATUS_CHOICES = [
    ('practising', _('Practising')),
    ('non_practising', _('Non-Practising')),
]

LEGAL_SPECIALIZATION_CHOICES = [
    ('criminal', _('Criminal Law')),
    ('civil', _('Civil Law')),
    ('corporate', _('Corporate Law')),
    ('family', _('Family Law')),
    ('real_estate', _('Real Estate Law')),
    ('tax', _('Tax Law')),
    ('labor', _('Labor Law')),
    ('constitutional', _('Constitutional Law')),
    ('intellectual_property', _('Intellectual Property')),
    ('other', _('Other')),
]
# trainsing_institute, Legal Aid Organization, Government Agency, Private Company, NGO etc.

PLACE_OF_WORK_CHOICES = [
    ('law_firm', _('Law Firm')),
    ('government', _('Government Agency')),
    ('ngo', _('NGO')),
    ('private', _('Private Practice')),
    ('corporate', _('Corporate')),
    ('legal_aid', _('Legal Aid Organization')),
    ('training_institute', _('Training Institute')),
    ('other', _('Other')),

]

ACADEMIC_ROLE_CHOICES = [
    ('law_student', _('Law Student')),
    ('lecturer', _('Law Lecturer')),
    ('professor', _('Law Professor')),
]
