import pandas as pd
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework import viewsets

from recon.serializers import AutoReconSerializer
from .models import (
    ManualReconResult,
    RawSapPayment,
    RawMt940Transaction,
    AutoReconResult,
)
import numpy as np  # Import numpy to check for NaN and infinite values
from datetime import date, datetime  # Explicitly import date and datetime


class SomeAPI(APIView):
    def post(self, request):
        # Fetch data from the database models
        sap_payment_df, mt940_df = self.fetch_data()
        if sap_payment_df is None or mt940_df is None:
            return Response(
                {"error": "Error fetching data from the database."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Process the data and get results
        results = self.process_data(sap_payment_df, mt940_df)

        try:
            return Response({"result": results}, status=status.HTTP_200_OK)
        except ValueError as e:
            print(f"JSON serialization error: {e}")
            return Response(
                {"error": "Out of range float values detected."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def fetch_data(self):
        """Fetch data from the database and return as DataFrames."""
        try:
            sap_payment_data = RawSapPayment.objects.all().values()
            mt940_data = RawMt940Transaction.objects.all().values()
            sap_payment_df = pd.DataFrame(list(sap_payment_data)).fillna("")
            mt940_df = pd.DataFrame(list(mt940_data)).fillna("")
            return sap_payment_df, mt940_df
        except Exception as e:
            print(f"Error fetching data: {e}")
            return None, None

    def process_data(self, sap_payment_df, mt940_df):
        """Process the SAP payment data against MT940 data."""
        results = []
        fields_to_check = {
            "posting_dt": "posting_dt",
            "currency": "currency",
            "amount": "amount",
            "counterparty_nm": "vendor_nm",
            "counterparty_account": "vendor_account",
            "bank_nm": "bank_nm",
            "bank_account": "bank_account",
        }

        for _, sap_row in sap_payment_df.iterrows():
            document_number = sap_row["document_number"]
            bank = sap_row["bank_nm"]
            amount = sap_row["amount"]
            currency = sap_row["currency"]

            # Check if the transaction is manually overridden
            if self.is_manually_user_overridden(document_number):
                result = {
                    "Transaction_ID": document_number,
                    "Status": "Manual override",
                    "Details": f"Transaction ID {document_number} has been manually overridden.",
                }
                results.append(result)
                continue  # Skip to the next transaction

            # Check for manual reconciliation records
            manual_recon_records = ManualReconResult.objects.filter(
                sap_document_num__id=sap_row["id"]  # Use the ID of the SAP document
            )
            if manual_recon_records.exists():
                mt_transaction_ids = list(
                    manual_recon_records.values_list(
                        "mt_transaction_id__transaction_id", flat=True
                    )
                )
                result = {
                    "Transaction_ID": document_number,
                    "Status": "Manual reconciliation",
                    "Details": {
                        "sap_document_number": document_number,
                        "mt_transaction_ids": mt_transaction_ids,  # Use the transaction IDs
                        "bank": bank,
                        "amount": amount,
                        "currency": currency,
                    },
                }
                results.append(result)
                continue  # Skip to the next transaction

            # Proceed with auto-reconciliation logic if neither case applies
            matching_mt_row = mt940_df[mt940_df["transaction_id"] == document_number]

            result = {"Transaction_ID": document_number}

            if matching_mt_row.empty:
                result = self.handle_missing_transaction(sap_row, document_number)
            else:
                mt_row = matching_mt_row.iloc[0]
                result = self.handle_matching_transaction(
                    sap_row, mt_row, fields_to_check, document_number
                )

            results.append(result)

        return results

    def is_manually_user_overridden(self, document_number):
        try:
            sap_payment = RawSapPayment.objects.get(document_number=document_number)

            auto_recon_result = AutoReconResult.objects.get(
                sap_document_num=sap_payment
            )

            return auto_recon_result.is_manual_override
        except RawSapPayment.DoesNotExist:
            return False
        except AutoReconResult.DoesNotExist:
            return False

    def handle_missing_transaction(self, sap_row, document_number):
        """Handle the case where a transaction is missing."""
        result = {
            "Transaction_ID": document_number,
            "Status": "Missing transaction",
            "Details": f"Transaction ID {document_number} does not exist in MT940 payment data.",
        }
        AutoReconResult.objects.create(
            sap_document_num=sap_row["document_number"],
            mt_transaction_id=None,
            status=result["Status"],
            status_data=self.serialize_dates({"Details": result["Details"]}),
        )
        return result

    def handle_matching_transaction(
        self, sap_row, mt_row, fields_to_check, document_number
    ):
        """Handle the case where a transaction matches."""
        result = {"Transaction_ID": document_number}
        mismatched_columns = []
        partially_missing_columns = []
        column_details = {}

        for mt_field, sap_field in fields_to_check.items():
            mt_value = mt_row[mt_field]
            sap_value = sap_row[sap_field]

            # Convert amounts to float explicitly
            if mt_field == "amount":
                mt_value, sap_value = self.convert_amounts(mt_value, sap_value)

            if mt_value == "" and sap_value == "":
                continue  # Skip if both are empty

            if mt_value == "" or sap_value == "":
                partially_missing_columns.append(mt_field)
            elif mt_value != sap_value:
                mismatched_columns.append(mt_field)

            column_details[mt_field] = self.get_column_details(mt_value, sap_value)

        result["Column_Details"] = column_details

        if mismatched_columns and partially_missing_columns:
            result["Status"] = "Mismatch"
            result["Details"] = (
                f"Transaction ID {document_number} has mismatched fields and some missing fields."
            )
            self.save_result(
                sap_row,
                mt_row,
                result,
                mismatched_columns,
                partially_missing_columns,
                column_details,
            )
        elif mismatched_columns:
            result["Status"] = "Mismatch"
            result["Details"] = (
                f"Transaction ID {document_number} has mismatched fields."
            )
            self.save_result(
                sap_row,
                mt_row,
                result,
                mismatched_columns,
                column_details=column_details,
            )
        elif partially_missing_columns:
            result["Status"] = "Partial match"
            result["Details"] = (
                f"Transaction ID {document_number} has some missing fields."
            )
            self.save_result(
                sap_row,
                mt_row,
                result,
                partially_missing_columns,
                column_details=column_details,
            )
        else:
            result["Status"] = "Full match"
            result["Details"] = f"Transaction ID {document_number} fully matches."
            self.save_result(sap_row, mt_row, result, column_details=column_details)

        return result

    def convert_amounts(self, mt_value, sap_value):
        """Convert amount values to float."""
        try:
            mt_value = float(mt_value) if mt_value != "" else 0.0
            sap_value = float(sap_value) if sap_value != "" else 0.0
        except (ValueError, TypeError):
            pass  # Keep as is if conversion fails
        return mt_value, sap_value

    def get_column_details(self, mt_value, sap_value):
        """Get details for a column comparison."""
        if mt_value == sap_value:
            return {"Value": mt_value}  # Only include one version
        else:
            return {
                "SAP_Value": sap_value,
                "MT940_Value": mt_value,
            }

    def save_result(
        self,
        sap_row,
        mt_row,
        result,
        mismatched_columns=None,
        partially_missing_columns=None,
        column_details=None,
    ):
        """Save or update the result in the database."""
        status_data = {
            "Column_Details": column_details,
        }
        if mismatched_columns:
            status_data["Mismatched_Columns"] = mismatched_columns
        if partially_missing_columns:
            status_data["Partially_Missing_Columns"] = partially_missing_columns

        # Get or create the AutoReconResult instance
        auto_recon_result, created = AutoReconResult.objects.update_or_create(
            sap_document_num=RawSapPayment.objects.get(
                document_number=sap_row["document_number"]
            ),
            mt_transaction_id=RawMt940Transaction.objects.get(
                transaction_id=mt_row["transaction_id"]
            ),
            defaults={
                "status": result["Status"],
                "status_data": self.serialize_dates(status_data),
            },
        )

    def serialize_dates(self, data):
        """Convert date objects to string."""
        if isinstance(data, dict):
            return {k: self.serialize_dates(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.serialize_dates(i) for i in data]
        elif isinstance(data, (date, datetime)):
            return data.isoformat()  # Convert to ISO format string
        return data


class MarkManualView(APIView):
    def post(self, request):
        id_post = request.data.get(
            "id"
        )  # Get the document number from the request data

        if not id_post:
            return Response(
                {"error": "id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Get the RawSapPayment object for the given document_number
            sap_payment = RawSapPayment.objects.get(id=id_post)

            # Get the AutoReconResult object associated with the sap_payment
            auto_recon_result = AutoReconResult.objects.get(
                sap_document_num=sap_payment
            )

            # Check if the status is not "Full match"
            if auto_recon_result.status != AutoReconResult.FULL_MATCH:
                # Update the is_manual_override flag to True
                auto_recon_result.is_manual_override = True
                auto_recon_result.approve_user = "ADMIN"
                auto_recon_result.save()  # Save the changes

                return Response(
                    {"message": "Manual override marked successfully."},
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {"error": "Cannot mark manual override for a full match."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        except RawSapPayment.DoesNotExist:
            return Response(
                {"error": "RawSapPayment with the given ID does not exist."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except AutoReconResult.DoesNotExist:
            return Response(
                {"error": "AutoReconResult does not exist for the given SAP record."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ManualReconView(APIView):
    def post(self, request):
        sap_id = request.data.get("sap_id")  # Get the SAP record ID
        mt_ids = request.data.get("mt_ids")  # Get the list of MT940 record IDs

        if not sap_id or not mt_ids:
            return Response(
                {"error": "SAP ID and MT940 IDs are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Get the SAP record
            sap_record = RawSapPayment.objects.get(id=sap_id)

            # Get the MT940 records
            mt_records = RawMt940Transaction.objects.filter(id__in=mt_ids)

            # Check if any MT940 records were found
            if mt_records.count() == 0:
                return Response(
                    {"error": "No MT940 records found for the given IDs."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Validate currency and bank
            sap_currency = sap_record.currency
            sap_bank = sap_record.bank_nm
            total_mt_amount = 0.0

            for mt_record in mt_records:
                if mt_record.currency != sap_currency:
                    return Response(
                        {"error": "Currency mismatch."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                if mt_record.bank_nm != sap_bank:
                    return Response(
                        {"error": "Bank mismatch."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                if mt_record.transaction_type == "DEBIT":
                    total_mt_amount -= mt_record.amount
                else:
                    total_mt_amount += (
                        mt_record.amount
                    )  # Assuming amount is a field in RawMt940Transaction

            # Check if the total amount matches
            if abs(total_mt_amount) != abs(sap_record.amount):
                return Response(
                    {
                        "error": "Total amount of MT940 records does not match SAP record amount."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # If all conditions are met, create ManualReconResult entries
            for mt_record in mt_records:
                ManualReconResult.objects.create(
                    sap_document_num=sap_record,
                    mt_transaction_id=mt_record,
                    approve_user="ADMIN",
                )

            return Response(
                {"message": "Manual reconciliation successful."},
                status=status.HTTP_201_CREATED,
            )

        except RawSapPayment.DoesNotExist:
            return Response(
                {"error": "SAP record not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
