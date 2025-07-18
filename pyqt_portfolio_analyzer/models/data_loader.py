import pandas as pd
from pathlib import Path

class DataLoader:
    """Reads TradingView .xlsx files and returns consolidated DataFrame."""

    def load_single(self, path: str | Path) -> pd.DataFrame:
        xls = pd.ExcelFile(path)
        df = pd.read_excel(xls, sheet_name="トレード一覧")
        df['file'] = Path(path).stem
        # 日付＋時刻で「DateTime」列を作成（精密な時系列用）
        df['DateTime'] = pd.to_datetime(df['日時'], errors='coerce')
        return df

    def load_multiple(self, paths: list[str | Path]) -> pd.DataFrame:
        frames = [self.load_single(p) for p in paths]
        df = pd.concat(frames, ignore_index=True)
        df = df.dropna(subset=['DateTime'])
        # 完全な「日時」順でソート
        df = df.sort_values('DateTime').reset_index(drop=True)
        return df
