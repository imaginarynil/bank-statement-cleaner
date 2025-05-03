import argparse
import os
import processor.cibc as cibc
import pandas as pd


class Presenter:
    EXCEL_WORKSHEET_EXT = ".xlsx"

    def __init__(self, processor):
        self.processor = processor

    def create(self, dir_path, file_name, complement):
        file_path = os.path.join(dir_path, f"{file_name}{Presenter.EXCEL_WORKSHEET_EXT}")
        self.processor.index_entries()
        self.processor.clean()
        self.processor.output(file_path)


def main():
    parser = argparse.ArgumentParser(
        description="Extract data from bank statements (i.e., savings, chequing, and credit) to prepare a personal cash flow statement"
    )
    parser.add_argument(
        "dataset_dir_path",
        type=str,
        help="Path to the directory containing the bank statement csv files"
    )
    parser.add_argument(
        "-c", "--create",
        type=str,
        metavar="file_name",
        help="Create an excel worksheet named file_name containing the processed statements"
    )
    parser.add_argument(
        "--complement",
        action="store_true",
        help="Output new entries only"
    )
    parser.add_argument(
        "-u", "--update",
        type=str,
        nargs=2,
        metavar=("file_path", "file_name"),
        help="Update the worksheet from file_path and create a new copy named file_name (without file extension)"
    )
    parser.add_argument(
        "--dirpath",
        type=str,
        nargs=1,
        metavar="dir_path",
        help="Set a custom destination directory path"
    )
    args = parser.parse_args()
    dataset_dir_path = args.dataset_dir_path
    if not dataset_dir_path:
        print(f"{dataset_dir_path} not found")
        return
    dst_dir_path = os.getcwd()
    if args.dirpath:
        print(args.dirpath)
    csv_paths = {
        "savings": os.path.join(dataset_dir_path, "savings.csv"),
        "chequing": os.path.join(dataset_dir_path, "chequing.csv"),
        "credit": os.path.join(dataset_dir_path, "credit.csv")
    }
    for key, value in csv_paths.items():
        if not os.path.isfile(value):
            print(f"Unable to find the {key} csv at {value}")
            return
    presenter = Presenter(
        processor=cibc.CIBCProcessor(
            savings_df=pd.read_csv(
                csv_paths["savings"],
                names=["date", "description", "debit", "credit"]
            ),
            chequing_df=pd.read_csv(
                csv_paths["chequing"],
                names=["date", "description", "debit", "credit"]
            ),
            credit_df=pd.read_csv(
                csv_paths["credit"], usecols=range(0, 4),
                names=["date", "description", "debit", "credit"]
            )
        )
    )
    if args.create:
        presenter.create(
            dst_dir_path,
            args.create,
            args.complement
        )
    elif args.update:
        print(args.update)


main()
