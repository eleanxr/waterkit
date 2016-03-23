
def assign_condition(df):
    """Assign a condition category based on which drought category contains the
    largest land percentage.
    """
    columns = ["NONE", "D0", "D1", "D2", "D3", "D4"]
    def assign(row):
        return row.idxmax()
    return df[columns].apply(assign, axis=1)

