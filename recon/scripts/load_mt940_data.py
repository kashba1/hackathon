import csv
from django.db import IntegrityError
from recon.models import RawMt940Transaction  # Ensure the correct path to your model
from datetime import datetime


def parse_date(date_str):
    """Convert 'DD-MM-YYYY' to 'YYYY-MM-DD' (Django-compatible format)."""
    try:
        return datetime.strptime(date_str, "%d-%m-%Y").date()  # Convert to date object
    except ValueError:
        print(f"Invalid date format: {date_str}")
        return None  # Return None if the date is invalid


def read_mt940_csv(file_path):
    with open(file_path, mode="r", newline="", encoding="ascii") as csvfile:
        reader = csv.DictReader(
            csvfile
        )  # Read CSV as dictionary (column names as keys)

        transactions = []  # Store objects for bulk insert

        for row in reader:
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
                    row_hash=row[
                        "Transaction_ID"
                    ],  # Example hash (should be actual hash)
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
