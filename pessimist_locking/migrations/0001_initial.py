from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='SoftPessimisticChangeLock',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_id', models.PositiveIntegerField(db_index=True)),
                ('user_ip_address', models.CharField(db_index=True, max_length=50)),
                ('object_id', models.PositiveIntegerField()),
                ('created_at', models.DateTimeField(blank=True, editable=False, null=True)),
                ('updated_at', models.DateTimeField(blank=True, editable=False, null=True)),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.ContentType')),
            ],
        ),

        migrations.RunSQL(
            """ALTER TABLE pessimist_locking_softpessimisticchangelock
                ADD CONSTRAINT locking_ip_check CHECK (user_ip_address <> ''),
                ADD CONSTRAINT locking_updated_check CHECK ( updated_at IS NULL OR updated_at > created_at)""",
        ),
    ]
