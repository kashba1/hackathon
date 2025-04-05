import csv
from django.db import IntegrityError
from recon.models import RawSapPayment  # Ensure correct import
from datetime import datetime


def parse_date(date_str):
    """Convert 'DD-MM-YYYY' to 'YYYY-MM-DD' (Django-compatible format)."""
    try:
        return datetime.strptime(date_str, "%d-%m-%Y").date()  # Convert to date object
    except ValueError:
        print(f"Invalid date format: {date_str}")
        return None  # Return None if the date is invalid


def xyz(file_path):
    """Reads SAP payment data from CSV and inserts it into the database."""
    with open(file_path, mode="r", newline="", encoding="ascii") as csvfile:
        reader = csv.DictReader(
            csvfile
        )  # Read CSV as dictionary (column names as keys)

        payments = []  # Store objects for bulk insert

        for row in reader:
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
                    vendor_bank_bic=row.get(
                        "Vendor_Bank_BIC", ""
                    ),  # Handle missing BIC
                    bank_nm=row["Paying_Bank"],
                    bank_account=row["Paying_Bank_Account"],
                    payment_method=row["Payment_Method"],
                    payment_term=row["Payment_Term"],
                    row_hash=row[
                        "Document_Number"
                    ],  # Example hash, should be actual hash
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
