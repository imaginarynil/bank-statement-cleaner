import argparse
import os
import processor.cibc as cibc
import pandas as pd


class Presenter:
    WORKSHEET_EXTENSION = ".xlsx"

    def __init__(self, processor):
        self.processor = processor

    def create(self, dir_path, file_name, worksheet_path=""):
        self.processor.build_worksheet()
        if worksheet_path:
            self.processor.filter_complement(
                pd.read_excel(worksheet_path, sheet_name=None)
            )
        self.processor.output(
            os.path.join(dir_path, f"{file_name}{Presenter.WORKSHEET_EXTENSION}")
        )

    def update(self, worksheet_path, dir_path, file_name):
        self.processor.build_worksheet()
        self.processor.merge_rows(
            pd.read_excel(worksheet_path, sheet_name=None)
        )
        self.processor.output(
            os.path.join(dir_path, f"{file_name}{Presenter.WORKSHEET_EXTENSION}")
        )


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
        type=str,
        metavar="worksheet_path",
        help="Output entries that are not in the worksheet at worksheet_path"
    )
    parser.add_argument(
        "-u", "--update",
        type=str,
        nargs=2,
        metavar=("worksheet_path", "file_name"),
        help="Update the worksheet from worksheet_path and create a new copy named file_name (without file extension)"
    )
    parser.add_argument(
        "--dirpath",
        type=str,
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
        if not os.path.isdir(args.dirpath):
            print(f"{args.dirpath} not found")
            return
        dst_dir_path = args.dirpath
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
        if args.complement:
            presenter.create(
                dst_dir_path,
                args.create,
                args.complement
            )
            return
        presenter.create(
            dst_dir_path,
            args.create
        )
    elif args.update:
        worksheet_path = args.update[0]
        file_name = args.update[1]
        presenter.update(
            worksheet_path,
            dst_dir_path,
            file_name
        )


main()
