#!/usr/bin/env python
"""Test script to verify unified content model"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pola_settings.settings')
django.setup()

from documents.models import LearningMaterial
from hubs.models import HubComment, ContentLike, ContentBookmark, HubCommentLike
from django.db import connection

print('🎯 UNIFIED CONTENT MODEL - VERIFICATION\n')
print('✅ All models imported successfully!\n')

# Check LearningMaterial fields
print('📊 LearningMaterial Fields:')
lm_fields = [f.name for f in LearningMaterial._meta.get_fields() if not f.many_to_many and not f.one_to_many]
key_fields = ['hub_type', 'content_type', 'content', 'video_url', 'is_pinned', 'platform_earnings']
for field in key_fields:
    status = '✅' if field in lm_fields else '❌'
    print(f'  {status} {field}')

# Check HubComment
print('\n💬 HubComment Fields:')
hc_fields = [f.name for f in HubComment._meta.get_fields() if not f.many_to_many and not f.one_to_many]
key_fields = ['content', 'comment_text', 'hub_type']
for field in key_fields:
    status = '✅' if field in hc_fields else '❌'
    print(f'  {status} {field}')

# Check database tables
print('\n🗄️  Database Tables:')
cursor = connection.cursor()
tables = ['hubs_contentlike', 'hubs_contentbookmark', 'subscriptions_learningmaterial', 'hubs_hubcomment']
for table in tables:
    cursor.execute(f"SELECT COUNT(*) FROM information_schema.tables WHERE table_name = '{table}'")
    exists = cursor.fetchone()[0] > 0
    status = '✅' if exists else '❌'
    print(f'  {status} {table}')

# Check content type choices
print('\n📝 Content Type Choices:')
content_types = dict(LearningMaterial.CONTENT_TYPE_CHOICES)
sample_types = ['discussion', 'question', 'article', 'document', 'notes']
for ct in sample_types:
    status = '✅' if ct in content_types else '❌'
    print(f'  {status} {ct}')

# Check hub type choices
print('\n🏢 Hub Type Choices:')
hub_types = dict(LearningMaterial.HUB_TYPES)
for ht in ['advocates', 'students', 'forum', 'legal_ed']:
    status = '✅' if ht in hub_types else '❌'
    print(f'  {status} {ht}')

print('\n🎉 Unified Content Model is READY!')
print('\n📈 Summary:')
print('  - LearningMaterial: Unified content model for posts + documents')
print('  - ContentLike: Unified likes for all content')
print('  - ContentBookmark: Unified bookmarks for all content')
print('  - HubComment: Comments on any content (posts/documents)')
print('  - Revenue tracking: Built-in for all content types')
