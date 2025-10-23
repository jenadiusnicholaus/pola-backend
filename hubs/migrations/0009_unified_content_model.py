# Manual migration for unified content model
# This migration creates the new tables and updates HubComment to reference LearningMaterial
from django.db import migrations


def create_new_tables_and_update_hubcomment(apps, schema_editor):
    """
    Create ContentLike, ContentBookmark tables and update HubComment to reference LearningMaterial
    """
    with schema_editor.connection.cursor() as cursor:
        # 1. Create ContentLike table
        cursor.execute("""
            CREATE TABLE hubs_contentlike (
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL REFERENCES authentication_polauser(id) ON DELETE CASCADE,
                content_id BIGINT NOT NULL REFERENCES subscriptions_learningmaterial(id) ON DELETE CASCADE,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                UNIQUE (user_id, content_id)
            );
        """)
        cursor.execute("CREATE INDEX hubs_conten_user_id_e62bc0_idx ON hubs_contentlike(user_id, created_at DESC);")
        cursor.execute("CREATE INDEX hubs_conten_content_1e52d7_idx ON hubs_contentlike(content_id, created_at DESC);")
        
        # 2. Create ContentBookmark table
        cursor.execute("""
            CREATE TABLE hubs_contentbookmark (
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL REFERENCES authentication_polauser(id) ON DELETE CASCADE,
                content_id BIGINT NOT NULL REFERENCES subscriptions_learningmaterial(id) ON DELETE CASCADE,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                UNIQUE (user_id, content_id)
            );
        """)
        cursor.execute("CREATE INDEX hubs_conten_user_id_1eea70_idx ON hubs_contentbookmark(user_id, created_at DESC);")
        
        # 3. Update HubComment table - rename content column and change post to content
        # First, rename existing 'content' to 'comment_text'
        cursor.execute("ALTER TABLE hubs_hubcomment RENAME COLUMN content TO comment_text;")
        
        # Add new 'content_id' column referencing LearningMaterial (nullable for now)
        cursor.execute("""
            ALTER TABLE hubs_hubcomment 
            ADD COLUMN content_id BIGINT NULL 
            REFERENCES subscriptions_learningmaterial(id) ON DELETE CASCADE;
        """)
        
        # Drop the old 'post_id' column (references HubPost which will be deleted)
        cursor.execute("ALTER TABLE hubs_hubcomment DROP COLUMN IF EXISTS post_id;")
        
        # Add indexes for HubComment
        cursor.execute("CREATE INDEX hubs_hubcom_hub_typ_6a9afc_idx ON hubs_hubcomment(hub_type, content_id, created_at);")
        cursor.execute("CREATE INDEX hubs_hubcom_author__659d57_idx ON hubs_hubcomment(author_id, created_at DESC);")
        
        # 4. Drop old Hub* tables that are being replaced
        cursor.execute("DROP TABLE IF EXISTS hubs_hubpostlike CASCADE;")
        cursor.execute("DROP TABLE IF EXISTS hubs_hubpostbookmark CASCADE;")
        cursor.execute("DROP TABLE IF EXISTS hubs_advocatepost_documents CASCADE;")  # Many-to-many table
        cursor.execute("DROP TABLE IF EXISTS hubs_hubpost CASCADE;")
        
        print("✅ Created ContentLike and ContentBookmark tables")
        print("✅ Updated HubComment to reference LearningMaterial")
        print("✅ Dropped old HubPost tables")


def reverse_migration(apps, schema_editor):
    """
    Reverse the migration (not fully reversible since we're dropping tables with data)
    """
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("DROP TABLE IF EXISTS hubs_contentlike CASCADE;")
        cursor.execute("DROP TABLE IF EXISTS hubs_contentbookmark CASCADE;")
        # Note: Cannot fully reverse without recreating HubPost and migrating data back


class Migration(migrations.Migration):

    dependencies = [
        ('hubs', '0008_rename_to_hub_models'),
        ('documents', '0002_extend_learning_material_unified_content'),
        ('authentication', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_new_tables_and_update_hubcomment, reverse_migration),
    ]
