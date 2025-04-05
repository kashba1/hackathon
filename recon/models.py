from django.db import models
from django.db.models import JSONField
from django.forms import ValidationError


class RawSapPayment(models.Model):
    document_number = models.CharField(max_length=255, unique=True)
    company_code = models.CharField(max_length=255)
    posting_dt = models.DateField()
    value_dt = models.DateField()
    currency = models.CharField(max_length=3)
    amount = models.FloatField()
    vendor_nm = models.CharField(max_length=255)
    vendor_account = models.CharField(max_length=255)
    vendor_bank_bic = models.CharField(max_length=255, blank=True)
    bank_nm = models.CharField(max_length=255)
    bank_account = models.CharField(max_length=255)
    payment_method = models.CharField(max_length=255)
    payment_term = models.CharField(max_length=255)
    insert_tmst = models.DateTimeField(auto_now_add=True)
    row_hash = models.CharField(max_length=255, unique=True)
    is_manually_reconned = models.BooleanField(default=False)

    class Meta:
        db_table = "raw_sap_payments"


class RawMt940Transaction(models.Model):
    transaction_id = models.CharField(max_length=255, unique=True)
    posting_dt = models.DateField()
    currency = models.CharField(max_length=3)
    amount = models.FloatField()
    transaction_type = models.CharField(max_length=255)
    counterparty_nm = models.CharField(max_length=255)
    counterparty_account = models.CharField(max_length=255)
    bank_nm = models.CharField(max_length=255)
    bank_account = models.CharField(max_length=255)
    insert_tmst = models.DateTimeField(auto_now_add=True)
    row_hash = models.CharField(max_length=255, unique=True)
    is_manually_reconned = models.BooleanField(default=False)

    class Meta:
        db_table = "raw_mt940_transactions"


class AutoReconResult(models.Model):
    # Status Choices
    MISSING_TRANSACTION = "Missing transaction"
    MISMATCH = "Mismatch"
    PARTIAL_MATCH = "Partial match"
    FULL_MATCH = "Full match"

    STATUS_CHOICES = [
        (MISSING_TRANSACTION, "Missing transaction"),
        (MISMATCH, "Mismatch"),
        (PARTIAL_MATCH, "Partial match"),
        (FULL_MATCH, "Full match"),
    ]

    auto_recon_id = models.AutoField(primary_key=True)
    sap_document_num = models.ForeignKey(
        RawSapPayment, on_delete=models.CASCADE, related_name="auto_recon"
    )
    mt_transaction_id = models.ForeignKey(
        RawMt940Transaction, on_delete=models.CASCADE, related_name="auto_recon"
    )
    status = models.CharField(
        max_length=50, choices=STATUS_CHOICES
    )  # Restricted to these choices
    status_data = models.JSONField()
    recon_run_tmst = models.DateTimeField(auto_now_add=True)
    is_manual_override = models.BooleanField(default=False)
    approve_user = models.CharField(max_length=255, blank=True)
    approve_tmst = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "auto_recon_result"


class ManualReconResult(models.Model):
    manual_recon_id = models.AutoField(primary_key=True)
    sap_document_num = models.ForeignKey(
        RawSapPayment, on_delete=models.CASCADE, related_name="manual_recon"
    )
    mt_transaction_id = models.ForeignKey(
        RawMt940Transaction, on_delete=models.CASCADE, related_name="manual_recon"
    )
    recon_run_tmst = models.DateTimeField(auto_now_add=True)
    approve_user = models.CharField(max_length=255, blank=True)
    approve_tmst = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "manual_recon_result"
