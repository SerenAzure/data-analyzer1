"""
DataAnalyzer：读取 CSV、基础统计、缺失值统计、因子去极值标准化、相关性、热力图。
可直接运行：python src/analyzer.py [csv路径]
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

# Windows 下用系统中文字体，避免标题显示为方块
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS"]
plt.rcParams["axes.unicode_minus"] = False


class DataAnalyzer:
    """面向表格数据的轻量分析器。"""

    def __init__(self, csv_path: str | Path) -> None:
        self.csv_path = Path(csv_path)
        self.df: pd.DataFrame | None = None
        self.factor_df: pd.DataFrame | None = None

    def load_csv(self) -> pd.DataFrame:
        """读取 CSV，缺失文件时给出明确提示。"""
        if not self.csv_path.exists():
            raise FileNotFoundError(f"找不到数据文件: {self.csv_path}")
        self.df = pd.read_csv(self.csv_path)
        return self.df

    def _require_df(self) -> pd.DataFrame:
        if self.df is None:
            raise RuntimeError("请先调用 load_csv() 加载数据。")
        return self.df

    def _numeric_columns(self, columns: list[str] | None = None) -> list[str]:
        df = self._require_df()
        numeric = df.select_dtypes(include="number").columns.tolist()
        if columns is None:
            return numeric
        missing = [c for c in columns if c not in df.columns]
        if missing:
            raise KeyError(f"列不存在: {missing}")
        not_num = [c for c in columns if c not in numeric]
        if not_num:
            raise ValueError(f"以下列不是数值列: {not_num}")
        return list(columns)

    def basic_stats(self) -> pd.DataFrame:
        """返回数值列的描述性统计（均值、标准差、分位数等）。"""
        df = self._require_df()
        return df.describe(include="all")

    def missing_stats(self) -> pd.DataFrame:
        """统计每列缺失值数量与占比。"""
        df = self._require_df()
        missing = df.isna().sum()
        stats = pd.DataFrame(
            {
                "missing_count": missing,
                "missing_ratio": missing / len(df),
                "non_null_count": df.notna().sum(),
            }
        )
        return stats.sort_values("missing_count", ascending=False)

    @staticmethod
    def _winsorize_mad(series: pd.Series, n: float) -> pd.Series:
        """按 MAD（中位数绝对偏差）截尾去极值。"""
        median = series.median()
        mad = (series - median).abs().median()
        if pd.isna(mad) or mad == 0:
            return series
        scale = 1.4826 * mad  # 与正态分布标准差对齐
        lower, upper = median - n * scale, median + n * scale
        return series.clip(lower=lower, upper=upper)

    @staticmethod
    def _zscore(series: pd.Series) -> pd.Series:
        """均值方差标准化；标准差为 0 时填 0。"""
        std = series.std(ddof=0)
        if pd.isna(std) or std == 0:
            return series * 0.0
        return (series - series.mean()) / std

    def winsorize_standardize(
        self,
        columns: list[str] | None = None,
        n: float = 3.0,
        by: str | None = "date",
    ) -> pd.DataFrame:
        """
        因子去极值后再标准化。
        默认按交易日截面做 MAD 去极值 + Z-Score；无分组列时对全样本处理。
        """
        df = self._require_df()
        cols = self._numeric_columns(columns)
        if not cols:
            raise ValueError("没有可用于去极值标准化的数值列。")

        result = df.copy()
        use_group = by is not None and by in result.columns

        def _process(block: pd.DataFrame) -> pd.DataFrame:
            out = block.copy()
            for col in cols:
                out[col] = self._zscore(self._winsorize_mad(out[col], n=n))
            return out

        if use_group:
            pieces = [_process(g) for _, g in result.groupby(by, sort=False)]
            result = pd.concat(pieces).sort_index()
        else:
            result = _process(result)

        self.factor_df = result
        return result

    def correlation(self, method: str = "pearson", use_factor: bool = False) -> pd.DataFrame:
        """计算数值列之间的相关系数矩阵。"""
        if use_factor:
            if self.factor_df is None:
                raise RuntimeError("请先调用 winsorize_standardize()。")
            numeric = self.factor_df.select_dtypes(include="number")
        else:
            numeric = self._require_df().select_dtypes(include="number")
        if numeric.empty:
            raise ValueError("数据中没有可用于相关性分析的数值列。")
        return numeric.corr(method=method)

    def plot_heatmap(
        self,
        save_path: str | Path = "correlation_heatmap.png",
        method: str = "pearson",
        use_factor: bool = False,
    ) -> Path:
        """绘制相关性热力图并保存到本地。"""
        corr = self.correlation(method=method, use_factor=use_factor)
        save_path = Path(save_path)
        plt.figure(figsize=(8, 6))
        sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", vmin=-1, vmax=1)
        plt.title("热力图")
        plt.tight_layout()
        plt.savefig(save_path, dpi=150)
        plt.close()
        return save_path


def _default_csv_path() -> Path:
    """相对项目根目录定位示例数据，保证从任意工作目录都能找到。"""
    return Path(__file__).resolve().parents[1] / "data" / "sample.csv"


def main() -> None:
    csv_path = Path(sys.argv[1]) if len(sys.argv) > 1 else _default_csv_path()
    analyzer = DataAnalyzer(csv_path)
    df = analyzer.load_csv()

    print(f"已加载: {csv_path}  形状={df.shape}")
    print("\n 基础统计 ")
    print(analyzer.basic_stats())
    print("\n 缺失值统计 ")
    print(analyzer.missing_stats())
    print("\n 因子去极值标准化（按日截面，MAD+ZScore）")
    factor_df = analyzer.winsorize_standardize()
    print(factor_df.head(10).to_string(index=False))
    print("\n 相关性矩阵（处理后）")
    print(analyzer.correlation(use_factor=True))

    heatmap_path = analyzer.plot_heatmap(use_factor=True)
    print(f"\n热力图已保存: {heatmap_path.resolve()}")


if __name__ == "__main__":
    main()
