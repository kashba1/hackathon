# Generated by Django 5.1.7 on 2025-03-31 19:55

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AutoReconResult',
            fields=[
                ('auto_recon_id', models.AutoField(primary_key=True, serialize=False)),
                ('sap_document_num', models.CharField(blank=True, max_length=255)),
                ('mt_transaction_id', models.CharField(blank=True, max_length=255)),
                ('status', models.CharField(choices=[('Missing transaction', 'Missing transaction'), ('Mismatch', 'Mismatch'), ('Partial match', 'Partial match'), ('Full match', 'Full match')], max_length=50)),
                ('status_data', models.JSONField()),
                ('recon_run_tmst', models.DateTimeField(auto_now_add=True)),
                ('is_manual_override', models.BooleanField(default=False)),
                ('approve_user', models.CharField(blank=True, max_length=255)),
                ('approve_tmst', models.DateTimeField(blank=True)),
            ],
            options={
                'db_table': 'auto_recon_result',
            },
        ),
        migrations.CreateModel(
            name='ManualReconResult',
            fields=[
                ('manual_recon_id', models.AutoField(primary_key=True, serialize=False)),
                ('sap_document_num', models.CharField(blank=True, max_length=255)),
                ('mt_transaction_id', models.CharField(blank=True, max_length=255)),
                ('recon_run_tmst', models.DateTimeField(auto_now_add=True)),
                ('approve_user', models.CharField(blank=True, max_length=255)),
                ('approve_tmst', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'db_table': 'manual_recon_result',
            },
        ),
        migrations.CreateModel(
            name='RawMt940Transaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('transaction_id', models.CharField(max_length=255, unique=True)),
                ('posting_dt', models.DateField()),
                ('currency', models.CharField(max_length=3)),
                ('amount', models.FloatField()),
                ('transaction_type', models.CharField(max_length=255)),
                ('counterparty_nm', models.CharField(max_length=255)),
                ('counterparty_account', models.CharField(max_length=255)),
                ('bank_nm', models.CharField(max_length=255)),
                ('bank_account', models.CharField(max_length=255)),
                ('insert_tmst', models.DateTimeField(auto_now_add=True)),
                ('row_hash', models.CharField(max_length=255, unique=True)),
            ],
            options={
                'db_table': 'raw_mt940_transactions',
            },
        ),
        migrations.CreateModel(
            name='RawSapPayment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('document_number', models.CharField(max_length=255, unique=True)),
                ('company_code', models.CharField(max_length=255)),
                ('posting_dt', models.DateField()),
                ('value_dt', models.DateField()),
                ('currency', models.CharField(max_length=3)),
                ('amount', models.FloatField()),
                ('vendor_nm', models.CharField(max_length=255)),
                ('vendor_account', models.CharField(max_length=255)),
                ('vendor_bank_bic', models.CharField(blank=True, max_length=255)),
                ('bank_nm', models.CharField(max_length=255)),
                ('bank_account', models.CharField(max_length=255)),
                ('payment_method', models.CharField(max_length=255)),
                ('payment_term', models.CharField(max_length=255)),
                ('insert_tmst', models.DateTimeField(auto_now_add=True)),
                ('row_hash', models.CharField(max_length=255, unique=True)),
            ],
            options={
                'db_table': 'raw_sap_payments',
            },
        ),
    ]
