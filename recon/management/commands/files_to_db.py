from django.core.management.base import BaseCommand
from recon.scripts.load_mt940_data import read_mt940_csv
from recon.scripts.load_sap_data import read_sap_csv


class Command(BaseCommand):
    help = "Load Model"

    def handle(
        self,
        *args,
        **kwargs,
    ):
        file_path_mt940 = "./recon/scripts/data_files/mt940_data.csv"
        read_mt940_csv(file_path_mt940)
        file_path_sap = "./recon/scripts/data_files/sap_payment_data.csv"
        read_sap_csv(file_path_sap)
