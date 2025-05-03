import argparse
import os

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
    dir_path = os.getcwd()
    if args.dirpath:
        print(args.dirpath)
    if args.create:
        print(args.create)
        if args.complement:
            print("complement")
    elif args.update:
        print(args.update)

main()
