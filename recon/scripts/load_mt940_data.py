import csv
from django.db import IntegrityError
from recon.models import (
    RawMt940Transaction,
    RawSapPayment,
)  # Ensure the correct path to your model
from datetime import datetime


def parse_date(date_str):
    """Convert 'DD-MM-YYYY' to 'YYYY-MM-DD' (Django-compatible format)."""
    try:
        return datetime.strptime(date_str, "%d-%m-%Y").date()  # Convert to date object
    except ValueError:
        print(f"Invalid date format: {date_str}")
        return None  # Return None if the date is invalid


def read_mt940_csv(file):
    """Reads MT940 data from a file-like object and inserts it into the database."""

    reader = csv.DictReader(
        file.read().decode("ascii").splitlines()
    )  # Read CSV as dictionary (column names as keys)

    transactions = []  # Store objects for bulk insert

    for row in reader:
        print(row)
        try:
            transaction = RawMt940Transaction(
                transaction_id=row["Transaction_ID"],
                posting_dt=parse_date(row["Date"]),
                currency=row["Currency"],
                amount=float(row["Amount"]),  # Ensure numeric conversion
                transaction_type=row["Transaction_Type"],
                counterparty_nm=row["Counterparty"],
                counterparty_account=row["Counterparty_Account"],
                bank_nm=row["Bank_Name"],
                bank_account=row["Bank_Account"],
                row_hash=row["Transaction_ID"],  # Example hash (should be actual hash)
            )
            transactions.append(transaction)  # Add to batch insert list

        except KeyError as e:
            print(f"Missing column in CSV: {e}")  # Debugging missing column
        except ValueError as e:
            print(f"Data conversion error: {e}")  # Handle bad data

    if transactions:
        try:
            RawMt940Transaction.objects.bulk_create(
                transactions, ignore_conflicts=True
            )  # Bulk insert for efficiency
            print(f"Inserted {len(transactions)} transactions.")
        except IntegrityError as e:
            print(f"Database integrity error: {e}")  # Handle duplicate primary keys


def read_sap_csv(file):
    """Reads SAP payment data from a file-like object and inserts it into the database."""

    reader = csv.DictReader(file.read().decode("ascii").splitlines())

    payments = []  # Store objects for bulk insert

    for row in reader:
        print(row)
        try:
            payment = RawSapPayment(
                document_number=row["Document_Number"],
                company_code=row["Company_Code"],
                posting_dt=parse_date(row["Posting_Date"]),
                value_dt=parse_date(row["Value_Date"]),
                currency=row["Currency"],
                amount=float(row["Amount"]),  # Ensure numeric conversion
                vendor_nm=row["Vendor_Name"],
                vendor_account=row["Vendor_Account"],
                vendor_bank_bic=row.get("Vendor_Bank_BIC", ""),  # Handle missing BIC
                bank_nm=row["Paying_Bank"],
                bank_account=row["Paying_Bank_Account"],
                payment_method=row["Payment_Method"],
                payment_term=row["Payment_Term"],
                row_hash=row["Document_Number"],  # Example hash, should be actual hash
            )
            payments.append(payment)  # Add to batch insert list

        except KeyError as e:
            print(f"Missing column in CSV: {e}")  # Debugging missing column
        except ValueError as e:
            print(f"Data conversion error: {e}")  # Handle bad data

    if payments:
        try:
            RawSapPayment.objects.bulk_create(
                payments, ignore_conflicts=True
            )  # Bulk insert for efficiency
            print(f"Inserted {len(payments)} SAP payments.")
        except IntegrityError as e:
            print(f"Database integrity error: {e}")  # Handle duplicate primary keys
