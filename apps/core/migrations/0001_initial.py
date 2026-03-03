from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ShopSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='Diaby Electronic', max_length=200)),
                ('phone', models.CharField(blank=True, max_length=50)),
                ('email', models.EmailField(blank=True, max_length=254)),
                ('address', models.TextField(blank=True)),
                ('currency', models.CharField(choices=[('FCFA', 'FCFA (Franc CFA)'), ('EUR', 'EUR (Euro)'), ('USD', 'USD (Dollar US)')], default='FCFA', max_length=10)),
                ('ninea', models.CharField(blank=True, max_length=50)),
                ('tax_number', models.CharField(blank=True, max_length=50)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_shop_settings', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
