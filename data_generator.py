import math
import os
import random
import datetime
import calendar
import pandas as pd
import numpy as np


class TransactionEntry:
    def __init__(self, date, name, method, type, party):
        self.date = date
        self.name = name
        self.method = method
        self.type = type
        self.party = party
        self.id = self.generate_id()

    def generate_id(self):
        id = []
        for i in range(0, 12):
            id.append(str(random.randint(0, 9)))
        return "".join(id)


class ConstantEntry(TransactionEntry):
    def __init__(self, value, date, name, method, type, party):
        super().__init__(date, name, method, type, party)
        self.value = value

    def get_value(self):
        return self.value


class VariableEntry(TransactionEntry):
    def __init__(self, min, max, date, name, method, type, party):
        super().__init__(date, name, method, type, party)
        self.min = min
        self.max = max
        self.value = self.get_value()

    def get_value(self):
        return random.randint(self.min, self.max)


def get_last_date(year, month):
    return datetime.date(year, month, calendar.monthrange(year, month)[1])


def convert_to_debit_df(entries):
    data = {
        "date": [],
        "description": [],
        "debit": [],
        "credit": []
    }
    for entry in entries:
        data["date"].append(pd.to_datetime(entry.date))
        description_elements = [
            entry.method,
            entry.type.upper()
        ]
        if entry.type not in [
            "ATM DEPOSIT",
            "CREDIT MEMO",
            "PAYMENT THANK YOU/PAIEMEN T MERCI",
        ]:
            description_elements.append(entry.id)
        description_elements.append(entry.party.upper())
        data["description"].append(" ".join(description_elements))
        # no transaction with a value of zero
        if entry.value > 0:
            data["debit"].append(np.nan)
            data["credit"].append(abs(entry.value))
        elif entry.value < 0:
            data["debit"].append(abs(entry.value))
            data["credit"].append(np.nan)
    return pd.DataFrame(data).sort_values(by=["date"])


def convert_to_credit_df(entries):
    data = {
        "date": [],
        "description": [],
        "debit": [],
        "credit": []
    }
    for entry in entries:
        data["date"].append(pd.to_datetime(entry.date))
        description_elements = []
        if entry.party:
            description_elements.append(entry.party.upper())
        if entry.method == "PAYMENT THANK YOU/PAIEMEN T MERCI":
            description_elements.append(entry.method)
        else:
            description_elements.append("TORONTO, ON")
        data["description"].append(" ".join(description_elements))
        if entry.value > 0:
            data["debit"].append(np.nan)
            data["credit"].append(abs(entry.value))
        elif entry.value < 0:
            data["debit"].append(abs(entry.value))
            data["credit"].append(np.nan)
    return pd.DataFrame(data).sort_values(by=["date"])


def export_statements_to_csv(savings_df, chequing_df, credit_df):
    data = {
        "savings": savings_df,
        "chequing": chequing_df,
        "credit": credit_df,
    }
    for key, df in data.items():
        df.to_csv(os.path.join("synthetic_data", f"{key}.csv"), header=None, index=False)


def main():
    savings_entries = []
    chequing_entries = []
    credit_entries = []
    start_date = datetime.date(2025, 1, 1)
    time_in_month = 12
    # init account
    savings_entries.append(
        ConstantEntry(
            date=start_date,
            name="deposit",
            method="Automated Banking Machine",
            type="ATM DEPOSIT",
            party="TORONTO",
            value=2000
        )
    )
    chequing_entries.append(
        ConstantEntry(
            date=start_date,
            name="deposit",
            method="Automated Banking Machine",
            type="ATM DEPOSIT",
            party="TORONTO",
            value=2000
        )
    )
    # monthly transactions
    for i in range(0, time_in_month):
        curr_month = (start_date.month + i) % (12 + 1)
        curr_year = start_date.year + math.floor((start_date.month + i) / (12 + 1))
        month_start_date = datetime.date(
            curr_year,
            curr_month,
            1
        )
        month_end_date = get_last_date(curr_year, curr_month)
        # first date
        chequing_entries.append(
            ConstantEntry(
                date=month_start_date,
                name="club membership",
                method="Internet Banking",
                type="E-TRANSFER",
                party="blue hockey club",
                value=-50
            )
        )
        # last date
        chequing_entries.append(
            ConstantEntry(
                date=month_end_date,
                name="salary",
                method="Branch Transaction",
                type="CREDIT MEMO",
                party="",
                value=7000
            )
        )
        savings_entries.append(
            ConstantEntry(
                date=month_end_date,
                name="rent",
                method="Internet Banking",
                type="E-TRANSFER",
                party="landlord",
                value=-1500
            )
        )
        savings_entries.append(
            VariableEntry(
                date=month_end_date,
                name="utilities",
                method="Internet Banking",
                type="E-TRANSFER",
                party="landlord",
                min=-300,
                max=-250
            )
        )
        internal_transfer_chequing_entry = ConstantEntry(
            date=month_end_date,
            name="internal transfer",
            method="Internet Banking",
            type="INTERNET TRANSFER",
            party="",
            value=-50000
        )
        chequing_entries.append(internal_transfer_chequing_entry)
        internal_transfer_savings_entry = ConstantEntry(
            date=month_end_date,
            name="internal transfer",
            method="Internet Banking",
            type="INTERNET TRANSFER",
            party="",
            value=internal_transfer_chequing_entry.value * -1
        )
        internal_transfer_savings_entry.id = internal_transfer_chequing_entry.id
        savings_entries.append(internal_transfer_savings_entry)
    # weekly and daily transactions
    week_start_date = start_date
    for i in range(0, time_in_month * 4):
        week_end_date = week_start_date + datetime.timedelta(days=6)
        groceries_entry = VariableEntry(
            date=week_end_date,
            name="groceries",
            method="",
            type="",
            party="walmart",
            min=-100,
            max=-50
        )
        credit_entries.append(
            groceries_entry
        )
        chequing_entries.append(
            ConstantEntry(
                date=groceries_entry.date,
                name=groceries_entry.name,
                method="Internet Banking",
                type="INTERNET TRANSFER",
                party="",
                value=groceries_entry.value
            )
        )
        credit_entries.append(
            ConstantEntry(
                date=groceries_entry.date,
                name=groceries_entry.name,
                method="PAYMENT THANK YOU/PAIEMEN T MERCI",
                type="",
                party="",
                value=groceries_entry.value * -1
            )
        )
        restaurant_meal_days = random.sample(range(0, 7), 2)
        for j in restaurant_meal_days:
            transport_date = week_start_date + datetime.timedelta(days=j)
            chequing_entries.append(
                VariableEntry(
                    date=transport_date,
                    name="restaurant",
                    method="Point of Sale - Interac",
                    type="RETAIL PURCHASE",
                    party="pizza",
                    min=-20,
                    max=-10
                )
            )
        public_transport_days = random.sample(range(0, 7), 5)
        for j in public_transport_days:
            transport_date = week_start_date + datetime.timedelta(days=j)
            chequing_entries.append(
                VariableEntry(
                    date=transport_date,
                    name="public transport",
                    method="Point of Sale - Visa Debit",
                    type="VISA DEBIT RETAIL PURCHASE",
                    party="presto",
                    min=-12,
                    max=-3
                )
            )
        week_start_date = week_end_date + datetime.timedelta(days=1)
    export_statements_to_csv(
        convert_to_debit_df(savings_entries),
        convert_to_debit_df(chequing_entries),
        convert_to_credit_df(credit_entries)
    )


main()
