# bank-statement-cleaner

A program that processes CIBC statements (i.e., savings, chequing, and credit) and produces structured data that can be used to create a personal cash flow statement, which is the foundation of a budget.

```
cleaner.exe [OPTIONS] [--] dataset_dir_path
```

```
  -h, --help            show this help message and exit
  -c file_name, --create file_name
                        Create an excel worksheet named file_name containing the processed statements
  --complement worksheet_path
                        Output entries that are not in the worksheet at worksheet_path
  -u worksheet_path file_name, --update worksheet_path file_name
                        Update the worksheet from worksheet_path and create a new copy named file_name (without file
                        extension)
  --dirpath dir_path    Set a custom destination directory path
```

[Documentation](https://imaginarynil.github.io/post/bank-statement-cleaner/index.html)

[Demonstration](https://www.linkedin.com/posts/sugianto-daniel_finance-banking-financialplanning-activity-7333251778639011840-W6ri?utm_source=share&utm_medium=member_desktop&rcm=ACoAAFKDZaEBZr1wfURGC-9AUWB7kCAJR4gsvO8)