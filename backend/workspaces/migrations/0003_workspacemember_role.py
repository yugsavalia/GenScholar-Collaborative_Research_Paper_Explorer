# Generated manually for workspace role feature

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workspaces', '0002_workspace_index_path_workspace_processing_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='workspacemember',
            name='role',
            field=models.CharField(
                choices=[('RESEARCHER', 'Researcher'), ('REVIEWER', 'Reviewer')],
                default='RESEARCHER',
                help_text='The role of this user in the workspace',
                max_length=20
            ),
        ),
    ]

