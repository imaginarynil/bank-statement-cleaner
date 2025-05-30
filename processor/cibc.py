import re
import pandas as pd
import numpy as np


class CIBCTransactionDescription:
    def __init__(
            self,
            method="",
            type="",
            party=""
    ):
        self.method = method
        self.type = type
        self.party = party

    def to_pd_series(self):
        # convert to lower case to make queries easier
        attributes = [
            self.method,
            self.type,
            self.party
        ]
        for i in range(0, len(attributes)):
            if not attributes[i]:
                attributes[i] = np.nan
            else:
                attributes[i] = attributes[i].lower()
        return pd.Series(attributes)


class CIBCProcessor:
    def __init__(
            self,
            savings_df,
            chequing_df,
            credit_df
    ):
        self.expanded_savings_df = self._expand_account_df(
            "savings",
            savings_df,
            expand_fn=self._expand_debit
        )
        self.expanded_chequing_df = self._expand_account_df(
            "chequing",
            chequing_df,
            expand_fn=self._expand_debit
        )
        self.expanded_credit_df = self._expand_account_df(
            "credit",
            credit_df,
            expand_fn=self._expand_credit,
            duplicate_index=False
        )
        self.cash_flow_df = None
        self.internal_transfer_df = None
        self.internal_payment_df = None

    def _parse_debit_description(self, description):
        tx_type_match = re.search(r'[A-Z][^a-z0-9]*[A-Z]', description)  # get transaction type
        if not tx_type_match:
            return CIBCTransactionDescription().to_pd_series()
        tx_type = tx_type_match.group()
        tx_method = description[:tx_type_match.span()[0] - 1]
        for word in [
            "CHARGE",
            "CORRECTION",
            "DEPOSIT",
            "FEE",
            "INTEREST",
            "MEMO",
            "PAY",
            "PURCHASE",
            "TRANSFER",
        ]:
            word_start_index = tx_type.rfind(word)  # scan from right
            if word_start_index == -1:
                continue
            tx_type = tx_type[:word_start_index + len(word)]
            # special case for service charges
            if word == "CHARGE":
                return CIBCTransactionDescription(
                    method=tx_method,
                    type=tx_type
                ).to_pd_series()
            break
        tx_type_end_index = tx_type_match.span()[0] + len(tx_type) - 1
        if tx_type_end_index == len(description) - 1:
            return CIBCTransactionDescription(
                method=tx_method,
                type=tx_type
            ).to_pd_series()
        remainder = description[tx_type_end_index + 2:]
        remainder = remainder.replace("*", "")  # delete asterisks
        # find a token with only letters and numbers with at least 1 letter and 1 number
        for token in remainder.split(" "):
            if re.search("^[0-9A-Z]+$", token) and re.search("[0-9]", token) and re.search("[A-Z]", token):
                return CIBCTransactionDescription(
                    method=tx_method,
                    type=tx_type,
                    party=remainder.replace(token, "").strip()
                ).to_pd_series()
        # find a token with only numbers
        token_match = re.search("^[0-9]+(?= )|(?<= )[0-9]+$|(?<= )[0-9]+(?= )", remainder)
        if token_match:
            return CIBCTransactionDescription(
                method=tx_method,
                type=tx_type,
                party=remainder.replace(token_match.group(), "").strip()
            ).to_pd_series()
        return CIBCTransactionDescription(
            method=tx_method,
            type=tx_type
        ).to_pd_series()

    def _parse_credit_description(self, description):
        tx_location_match = re.search(r'[^ ]+, .+$', description)  # get transaction location
        if not tx_location_match:
            return np.nan
        return description.replace(tx_location_match.group(), "").strip().lower()

    def _expand_debit(self, df):
        df[["method", "type", "party"]] = df["description"].apply(self._parse_debit_description)

    def _expand_credit(self, df):
        df["party"] = df["description"].apply(self._parse_credit_description)

    def _expand_account_df(self, account, account_df, expand_fn=None, duplicate_index=True):
        df = account_df.copy()
        date = pd.to_datetime(df["date"])
        df["date"] = date.dt.strftime("%Y-%m-%d")
        df["year"] = date.dt.year
        df["month"] = date.dt.month
        df["day"] = date.dt.day
        df["account"] = account
        df["amount"] = df[["debit", "credit"]].apply(
            lambda x: x["credit"] if pd.isnull(x["debit"]) else -1 * x["debit"], axis=1)
        df = df.drop(columns=["debit", "credit"])
        if expand_fn:
            expand_fn(df)
        if duplicate_index:
            df["index_copy"] = df.index
        return df

    def _index_entries(self):
        combined_expanded_df = pd.concat([
            self.expanded_savings_df,
            self.expanded_chequing_df,
            self.expanded_credit_df
        ]).sort_values(by=["date"])
        combined_expanded_df["uid"] = combined_expanded_df.reset_index(drop=True).index + 1
        self.expanded_savings_df = self.expanded_savings_df.sort_index()
        self.expanded_savings_df["uid"] = \
            combined_expanded_df.loc[combined_expanded_df["account"] == "savings"].sort_index()["uid"]
        self.expanded_chequing_df = self.expanded_chequing_df.sort_index()
        self.expanded_chequing_df["uid"] = \
            combined_expanded_df.loc[combined_expanded_df["account"] == "chequing"].sort_index()["uid"]
        self.expanded_credit_df = self.expanded_credit_df.sort_index()
        self.expanded_credit_df["uid"] = \
            combined_expanded_df.loc[combined_expanded_df["account"] == "credit"].sort_index()["uid"]

    def _get_sign(self, amount):
        if amount > 0:
            return "income"
        elif amount < 0:
            return "expense"
        return "zero-value"

    def _clean(self):
        merged_df = self.expanded_savings_df.merge(
            self.expanded_chequing_df,
            left_on="description",
            right_on="description"
        )
        merged_df = merged_df.loc[merged_df["amount_x"] == -1 * merged_df["amount_y"]]
        self.internal_transfer_df = pd.concat([
            self.expanded_savings_df.loc[merged_df["index_copy_x"]],
            self.expanded_chequing_df.loc[merged_df["index_copy_y"]]
        ]).drop(columns=["index_copy", "party"]).sort_values(by=["uid"]).reset_index(drop=True)
        raw_debit_df = pd.concat([
            self.expanded_savings_df.drop(merged_df["index_copy_x"]),
            self.expanded_chequing_df.drop(merged_df["index_copy_y"])
        ]).drop(columns=["index_copy"]).reset_index(drop=True)
        internal_payment_from_debit_df = raw_debit_df.loc[
            (raw_debit_df["method"] == "internet banking") &
            (raw_debit_df["type"] == "internet transfer")
            ].drop(columns=["party"])
        credit_payment_bool_series = self.expanded_credit_df["description"].str.contains("PAYMENT THANK YOU")
        self.internal_payment_df = pd.concat([
            internal_payment_from_debit_df,
            self.expanded_credit_df.loc[credit_payment_bool_series]
        ]).drop(columns=["party"]).sort_values(by=["uid"]).reset_index(drop=True)
        debit_df = raw_debit_df.drop(internal_payment_from_debit_df.index).reset_index(drop=True)
        self.cash_flow_df = pd.concat([
            debit_df,
            self.expanded_credit_df.loc[~credit_payment_bool_series]
        ]).sort_values(by=["uid"]).reset_index(drop=True)
        self.cash_flow_df["sign"] = self.cash_flow_df["amount"].apply(self._get_sign)

    def _update_dataframes(self, df_dict):
        self.cash_flow_df = df_dict["cash_flow"]
        self.internal_transfer_df = df_dict["internal_transfer"]
        self.internal_payment_df = df_dict["internal_payment"]

    def _get_complement(self, worksheet_dict):
        df_dict = {
            "cash_flow": self.cash_flow_df,
            "internal_transfer": self.internal_transfer_df,
            "internal_payment": self.internal_payment_df
        }
        result = {}
        for key, df in df_dict.items():
            result[key] = df.loc[~df["uid"].isin(worksheet_dict[key]["uid"])]
        return result

    def _merge(self, worksheet_dict):
        complement = self._get_complement(worksheet_dict)
        result = {}
        for i in ["cash_flow", "internal_transfer", "internal_payment"]:
            result[i] = pd.concat([
                worksheet_dict[i],
                complement[i]
            ]).sort_values(by=["uid"])
            print(f"added {len(complement[i].index)} new rows in {i}")
        return result

    def build_worksheet(self):
        self._index_entries()
        self._clean()

    def filter_complement(self, worksheet_dict):
        self._update_dataframes(self._get_complement(worksheet_dict))

    def merge_rows(self, worksheet_dict):
        self._update_dataframes(self._merge(worksheet_dict))

    def output(self, file_path):
        with pd.ExcelWriter(file_path) as writer:
            self.cash_flow_df.sort_values(
                by=["uid"]
            ).to_excel(writer, sheet_name="cash_flow", index=False)
            self.internal_transfer_df.sort_values(
                by=["uid"]
            ).to_excel(writer, sheet_name="internal_transfer", index=False)
            self.internal_payment_df.sort_values(
                by=["uid"]
            ).to_excel(writer, sheet_name="internal_payment", index=False)
