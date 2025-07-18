import pandas as pd
from pathlib import Path

class DataLoader:
    """Reads TradingView .xlsx files and returns consolidated DataFrame"""

    def load_single(self, path: str | Path) -> pd.DataFrame:
        xls = pd.ExcelFile(path)
        df  = pd.read_excel(xls, sheet_name="トレード一覧")
        df['file'] = Path(path).stem
        return df

    def load_multiple(self, paths: list[str | Path]) -> pd.DataFrame:
        frames = [self.load_single(p) for p in paths]
        df = pd.concat(frames, ignore_index=True)
        df['Date'] = pd.to_datetime(df['日時'], errors='coerce').dt.date
        return df
