import unittest

import pandas as pd

from src.forecast import prepare_time_series


class PrepareTimeSeriesTests(unittest.TestCase):
    def test_prepares_series_when_dates_are_duplicated_and_values_have_commas(self):
        df = pd.DataFrame(
            {
                "Date": ["2024-01-01", "2024-01-01", "2024-01-02", "2024-01-03"],
                "Value": ["1,000", "1,200", "1,500", "2,000"],
            }
        )

        series = prepare_time_series(df, "Date", "Value", "D")

        self.assertEqual(series.name, "Value")
        self.assertEqual(series.loc[pd.Timestamp("2024-01-01")], 1200.0)
        self.assertEqual(series.loc[pd.Timestamp("2024-01-02")], 1500.0)
        self.assertEqual(series.loc[pd.Timestamp("2024-01-03")], 2000.0)
        self.assertTrue(series.index.is_unique)


if __name__ == "__main__":
    unittest.main()
