"""
Advanced statistical analysis utilities for HHD-HY Survey App.

Algorithms sourced / cross-referenced with:
  - GeeksforGeeks (Cronbach's α, VIF, IQR outlier detection)
  - Papers With Code / sklearn documentation (standardised β, PCA scree)
  - statsmodels documentation (OLS, Durbin-Watson, Breusch-Pagan)
  - SciPy documentation (Shapiro-Wilk, Pearson/Spearman correlation, t-test, ANOVA)
"""

import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score, mean_squared_error
from factor_analyzer import FactorAnalyzer
from factor_analyzer.factor_analyzer import calculate_bartlett_sphericity, calculate_kmo
import statsmodels.api as sm
from scipy import stats as sp_stats
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def calculate_cronbach_alpha(df, columns):
    """
    Tính toán hệ số Cronbach's Alpha cho một tập hợp các biến.
    
    Args:
        df (DataFrame): DataFrame chứa dữ liệu
        columns (list): Danh sách các cột để phân tích
        
    Returns:
        dict: Kết quả phân tích bao gồm hệ số Cronbach's Alpha và các chỉ số liên quan
    """
    try:
        # Loại bỏ các dòng có giá trị NaN
        data = df[columns].dropna()
        
        if len(data) == 0:
            return {
                "alpha": None,
                "error": "Không có đủ dữ liệu không thiếu để tính toán."
            }
        
        # Tính tổng phương sai
        item_variances = data.var(axis=0, ddof=1)
        total_variance = data.sum(axis=1).var(ddof=1)
        
        # Số lượng biến (items)
        n_items = len(columns)
        
        # Tính Cronbach's Alpha
        cronbach_alpha = (n_items / (n_items - 1)) * (1 - (item_variances.sum() / total_variance))
        
        # Tính các chỉ số item-total correlation và alpha if item deleted
        item_stats = []
        for col in columns:
            other_items = [c for c in columns if c != col]
            item_total = data[col].corr(data[other_items].sum(axis=1))
            
            # Alpha if item deleted
            other_variances = data[other_items].var(axis=0, ddof=1)
            other_total_var = data[other_items].sum(axis=1).var(ddof=1)
            if len(other_items) > 1:
                alpha_if_deleted = (len(other_items) / (len(other_items) - 1)) * (1 - (other_variances.sum() / other_total_var))
            else:
                alpha_if_deleted = np.nan
            
            item_stats.append({
                "item": col,
                "item_total_correlation": item_total,
                "alpha_if_deleted": alpha_if_deleted
            })
        
        return {
            "alpha": cronbach_alpha,
            "item_stats": item_stats,
            "n_items": n_items,
            "n_cases": len(data),
            "total_variance": total_variance,
            "success": True
        }
    except Exception as e:
        logger.error(f"Lỗi khi tính Cronbach's Alpha: {str(e)}")
        return {
            "alpha": None,
            "error": str(e),
            "success": False
        }

def perform_efa(df, columns, n_factors=None, rotation='varimax', min_eigenvalue=1.0):
    """
    Thực hiện phân tích nhân tố khám phá (EFA).
    
    Args:
        df (DataFrame): DataFrame chứa dữ liệu
        columns (list): Danh sách các cột để phân tích
        n_factors (int, optional): Số lượng nhân tố cần trích xuất. Nếu None, sẽ dựa vào min_eigenvalue.
        rotation (str, optional): Phương pháp xoay nhân tố ('varimax', 'promax', etc.)
        min_eigenvalue (float, optional): Giá trị eigen tối thiểu để xác định số lượng nhân tố
        
    Returns:
        dict: Kết quả phân tích EFA
    """
    try:
        # Loại bỏ các dòng có giá trị NaN
        data = df[columns].dropna()
        
        if len(data) == 0:
            return {
                "error": "Không có đủ dữ liệu không thiếu để phân tích.",
                "success": False
            }
        
        # Kiểm tra điều kiện thực hiện EFA
        chi_square_value, p_value = calculate_bartlett_sphericity(data)
        kmo_all, kmo_model = calculate_kmo(data)
        
        if p_value > 0.05:
            warning_message = "Dữ liệu có thể không phù hợp cho phân tích nhân tố (Bartlett's test p > 0.05)."
        else:
            warning_message = None
        
        if kmo_model < 0.6:
            kmo_warning = "Chỉ số KMO thấp (<0.6), dữ liệu có thể không phù hợp cho phân tích nhân tố."
            if warning_message:
                warning_message += " " + kmo_warning
            else:
                warning_message = kmo_warning
        
        # Xác định số lượng nhân tố dựa trên giá trị eigenvalue
        if n_factors is None:
            fa_initial = FactorAnalyzer(n_factors=len(columns), rotation=None)
            fa_initial.fit(data)
            ev, _ = fa_initial.get_eigenvalues()
            n_factors = sum(ev > min_eigenvalue)
            
            if n_factors == 0:
                return {
                    "error": "Không có nhân tố nào có eigenvalue lớn hơn ngưỡng.",
                    "eigenvalues": ev.tolist(),
                    "success": False
                }
        
        # Thực hiện phân tích nhân tố
        fa = FactorAnalyzer(n_factors=n_factors, rotation=rotation)
        fa.fit(data)
        
        # Lấy loadings
        loadings = fa.loadings_
        
        # Tạo dataframe loadings
        loadings_df = pd.DataFrame(
            loadings, 
            index=columns,
            columns=[f"Factor {i+1}" for i in range(n_factors)]
        )
        
        # Tính toán cộng dồn phương sai giải thích được
        variance = fa.get_factor_variance()
        
        # Sắp xếp biến theo các nhân tố
        factor_groups = {}
        for var_idx, var_name in enumerate(columns):
            # Tìm nhân tố có loading cao nhất cho biến này
            max_loading_idx = np.argmax(np.abs(loadings[var_idx]))
            max_loading_val = loadings[var_idx][max_loading_idx]
            
            factor_name = f"Factor {max_loading_idx+1}"
            if factor_name not in factor_groups:
                factor_groups[factor_name] = []
            
            factor_groups[factor_name].append({
                "variable": var_name,
                "loading": max_loading_val
            })
        
        # Sắp xếp các biến trong mỗi nhóm theo độ lớn của loading
        for factor in factor_groups:
            factor_groups[factor] = sorted(
                factor_groups[factor],
                key=lambda x: abs(x["loading"]),
                reverse=True
            )
        
        return {
            "loadings": loadings_df.to_dict(),
            "loadings_matrix": loadings.tolist(),
            "n_factors": n_factors,
            "explained_variance": variance[0].tolist(),
            "cumulative_variance": variance[2].tolist(),
            "factor_groups": factor_groups,
            "bartlett_p_value": p_value,
            "kmo": kmo_model,
            "warning": warning_message,
            "eigenvalues": fa.get_eigenvalues()[0].tolist(),
            "success": True
        }
    except Exception as e:
        logger.error(f"Lỗi khi thực hiện EFA: {str(e)}")
        return {
            "error": str(e),
            "success": False
        }

def perform_regression(df, dependent_var, independent_vars):
    """
    Thực hiện phân tích hồi quy tuyến tính đa biến.
    
    Args:
        df (DataFrame): DataFrame chứa dữ liệu
        dependent_var (str): Tên biến phụ thuộc
        independent_vars (list): Danh sách các biến độc lập
        
    Returns:
        dict: Kết quả phân tích hồi quy
    """
    try:
        # Loại bỏ các dòng có giá trị NaN
        data = df[[dependent_var] + independent_vars].dropna()
        
        if len(data) == 0:
            return {
                "error": "Không có đủ dữ liệu không thiếu để phân tích.",
                "success": False
            }
        
        # Chuẩn bị dữ liệu
        X = data[independent_vars]
        y = data[dependent_var]
        
        # Thêm hằng số (intercept)
        X = sm.add_constant(X)
        
        # Thực hiện hồi quy
        model = sm.OLS(y, X).fit()
        
        # Lấy kết quả
        coefficients = model.params.to_dict()
        
        # Tính R² điều chỉnh
        r_squared = model.rsquared
        adj_r_squared = model.rsquared_adj
        
        # Tính hệ số Durbin-Watson để kiểm tra tự tương quan
        durbin_watson = sm.stats.durbin_watson(model.resid)
        
        # Thống kê dùng cho đa cộng tuyến
        vif_data = {}
        for idx, var_name in enumerate(independent_vars):
            # Xây dựng mô hình phụ để tính VIF
            X_temp = X.copy()
            y_temp = X_temp[var_name]
            X_temp = X_temp.drop(var_name, axis=1)
            
            mod_temp = sm.OLS(y_temp, X_temp).fit()
            r2_temp = mod_temp.rsquared
            
            # Tính VIF
            vif = 1.0 / (1.0 - r2_temp) if r2_temp < 1 else float('inf')
            vif_data[var_name] = vif
        
        # Tính F-statistic và p-value
        f_statistic = model.fvalue
        f_pvalue = model.f_pvalue
        
        # Tổng hợp kết quả thành từng biến
        variable_stats = []
        for var in coefficients:
            if var == 'const':
                var_name = 'Hằng số'
            else:
                var_name = var
                
            var_stat = {
                "variable": var_name,
                "coefficient": coefficients[var],
                "std_error": model.bse[var],
                "t_value": model.tvalues[var],
                "p_value": model.pvalues[var],
                "significant": model.pvalues[var] < 0.05
            }
            
            if var != 'const':
                var_stat["vif"] = vif_data[var]
                
            variable_stats.append(var_stat)
        
        # Kiểm tra các giả định
        assumptions = {
            "multicollinearity": any(v > 10 for v in vif_data.values()),
            "durbin_watson": durbin_watson,
            "homoscedasticity": model.het_breuschpagan(),
            "normality": model.jarque_bera()
        }
        
        return {
            "model_summary": {
                "r_squared": r_squared,
                "adj_r_squared": adj_r_squared,
                "f_statistic": f_statistic,
                "f_pvalue": f_pvalue,
                "n_observations": len(data),
                "equation": f"Y = {coefficients['const']:.3f} + " + " + ".join(
                    [f"{coefficients[var]:.3f}*{var}" for var in independent_vars]
                )
            },
            "variables": variable_stats,
            "assumptions": assumptions,
            "aic": model.aic,
            "bic": model.bic,
            "success": True
        }
    except Exception as e:
        logger.error(f"Lỗi khi thực hiện hồi quy: {str(e)}")
        return {
            "error": str(e),
            "success": False
        }

# Chức năng phân tích nhân tố khẳng định (CFA) sẽ cần phụ thuộc vào thư viện bên ngoài như lavaan hoặc semopy
# Tuy nhiên, chúng ta có thể cung cấp một phương pháp đơn giản để đánh giá các mô hình CFA bằng cách sử dụng factor loadings
def simple_cfa_evaluation(df, factor_structure):
    """
    Đánh giá cơ bản cho một mô hình CFA bằng cách tính toán một số chỉ số phù hợp.
    
    Args:
        df (DataFrame): DataFrame chứa dữ liệu
        factor_structure (dict): Cấu trúc mô hình CFA (nhóm biến theo các nhân tố)
            Ví dụ: {"Factor1": ["var1", "var2"], "Factor2": ["var3", "var4"]}
            
    Returns:
        dict: Kết quả đánh giá cơ bản của mô hình CFA
    """
    try:
        # Làm phẳng danh sách biến
        all_vars = [var for vars in factor_structure.values() for var in vars]
        
        # Loại bỏ các dòng có giá trị NaN
        data = df[all_vars].dropna()
        
        if len(data) == 0:
            return {
                "error": "Không có đủ dữ liệu không thiếu để phân tích.",
                "success": False
            }
        
        # Tính ma trận tương quan
        corr_matrix = data.corr()
        
        # Tính trung bình tương quan nội bộ cho mỗi nhân tố
        factor_stats = {}
        for factor, variables in factor_structure.items():
            if len(variables) < 2:
                avg_corr = None
                reliability = None
            else:
                # Tính trung bình tương quan giữa các biến trong nhân tố
                corrs = []
                for i, var1 in enumerate(variables):
                    for var2 in variables[i+1:]:
                        corrs.append(corr_matrix.loc[var1, var2])
                
                avg_corr = np.mean(corrs) if corrs else None
                
                # Tính toán độ tin cậy cho nhân tố này
                reliability_result = calculate_cronbach_alpha(data, variables)
                reliability = reliability_result.get("alpha")
            
            # Tính các chỉ số liên quan đến hội tụ và phân biệt
            cross_loadings = {}
            if len(factor_structure) > 1:
                for other_factor, other_vars in factor_structure.items():
                    if other_factor != factor:
                        cross_corrs = []
                        for var1 in variables:
                            for var2 in other_vars:
                                cross_corrs.append(corr_matrix.loc[var1, var2])
                        
                        cross_loadings[other_factor] = np.mean(cross_corrs) if cross_corrs else None
            
            factor_stats[factor] = {
                "variables": variables,
                "n_variables": len(variables),
                "avg_correlation": avg_corr,
                "reliability": reliability,
                "cross_loadings": cross_loadings
            }
        
        # Đánh giá tổng thể về độ phù hợp
        overall_evaluation = {}
        
        # Đánh giá độ hội tụ - tất cả các biến trong cùng một nhân tố phải có tương quan cao
        convergent_validity = all(
            stats["avg_correlation"] > 0.5 if stats["avg_correlation"] is not None else False
            for stats in factor_stats.values()
        )
        
        # Đánh giá độ phân biệt - tương quan giữa các biến thuộc các nhân tố khác nhau phải thấp
        discriminant_validity = True
        for factor, stats in factor_stats.items():
            if stats["cross_loadings"]:
                for other_factor, cross_loading in stats["cross_loadings"].items():
                    if cross_loading is not None and stats["avg_correlation"] is not None:
                        if cross_loading >= stats["avg_correlation"]:
                            discriminant_validity = False
                            break
        
        overall_evaluation["convergent_validity"] = convergent_validity
        overall_evaluation["discriminant_validity"] = discriminant_validity
        
        # Trả về kết quả
        return {
            "factor_stats": factor_stats,
            "overall_evaluation": overall_evaluation,
            "success": True
        }
    except Exception as e:
        logger.error(f"Lỗi khi đánh giá CFA: {str(e)}")
        return {
            "error": str(e),
            "success": False
        }


# ─── NEW: Correlation matrix with p-values ───────────────────────────────────
def calculate_correlation_matrix(df: pd.DataFrame, columns: list, method: str = "pearson") -> dict:
    """
    Tính ma trận tương quan kèm p-value cho từng cặp biến.

    Thuật toán tham khảo: GeeksforGeeks — Pearson & Spearman correlation,
    scipy.stats documentation.

    Args:
        df       : DataFrame chứa dữ liệu
        columns  : Danh sách cột cần phân tích
        method   : 'pearson' hoặc 'spearman'

    Returns:
        dict với 'corr_matrix', 'pvalue_matrix', 'n', 'method', 'success'
    """
    try:
        data = df[columns].dropna()
        n = len(data)
        if n < 3:
            return {"error": "Cần ít nhất 3 quan sát để tính tương quan.", "success": False}

        corr_func = sp_stats.pearsonr if method == "pearson" else sp_stats.spearmanr

        k = len(columns)
        corr_arr = np.ones((k, k))
        pval_arr = np.zeros((k, k))

        for i in range(k):
            for j in range(k):
                if i == j:
                    corr_arr[i, j] = 1.0
                    pval_arr[i, j] = 0.0
                elif i < j:
                    if method == "spearman":
                        res = sp_stats.spearmanr(data.iloc[:, i], data.iloc[:, j])
                        r, p = res.correlation, res.pvalue
                    else:
                        r, p = sp_stats.pearsonr(data.iloc[:, i], data.iloc[:, j])
                    corr_arr[i, j] = corr_arr[j, i] = r
                    pval_arr[i, j] = pval_arr[j, i] = p

        corr_df = pd.DataFrame(corr_arr, index=columns, columns=columns)
        pval_df = pd.DataFrame(pval_arr, index=columns, columns=columns)

        return {
            "corr_matrix": corr_df,
            "pvalue_matrix": pval_df,
            "n": n,
            "method": method,
            "success": True,
        }
    except Exception as e:
        logger.error(f"Lỗi tính correlation matrix: {e}")
        return {"error": str(e), "success": False}


# ─── NEW: Descriptive statistics with normality test ─────────────────────────
def calculate_descriptive_stats(df: pd.DataFrame, columns: list) -> dict:
    """
    Thống kê mô tả nâng cao: mean, median, std, skewness, kurtosis,
    IQR, outlier count (IQR rule), và kiểm định chuẩn (Shapiro-Wilk).

    Thuật toán:
      - IQR outlier detection: GeeksforGeeks / Tukey's fences (Q1 − 1.5·IQR, Q3 + 1.5·IQR)
      - Shapiro-Wilk: scipy.stats.shapiro (suitable for n ≤ 5000)

    Returns:
        dict với 'stats' (list of per-variable dicts) và 'success'
    """
    try:
        data = df[columns].apply(pd.to_numeric, errors="coerce")
        results = []

        for col in columns:
            series = data[col].dropna()
            if len(series) < 3:
                continue

            q1 = series.quantile(0.25)
            q3 = series.quantile(0.75)
            iqr = q3 - q1
            lower_fence = q1 - 1.5 * iqr
            upper_fence = q3 + 1.5 * iqr
            n_outliers = int(((series < lower_fence) | (series > upper_fence)).sum())

            # Shapiro-Wilk (use up to 5000 samples)
            sw_sample = series.sample(min(len(series), 5000), random_state=42)
            sw_stat, sw_p = sp_stats.shapiro(sw_sample)
            is_normal = sw_p > 0.05

            results.append({
                "column": col,
                "n": int(len(series)),
                "mean": float(series.mean()),
                "median": float(series.median()),
                "std": float(series.std()),
                "min": float(series.min()),
                "max": float(series.max()),
                "q1": float(q1),
                "q3": float(q3),
                "iqr": float(iqr),
                "skewness": float(series.skew()),
                "kurtosis": float(series.kurtosis()),
                "n_outliers": n_outliers,
                "shapiro_stat": float(sw_stat),
                "shapiro_p": float(sw_p),
                "is_normal": is_normal,
            })

        return {"stats": results, "success": True}
    except Exception as e:
        logger.error(f"Lỗi tính descriptive stats: {e}")
        return {"error": str(e), "success": False}


# ─── NEW: t-test / ANOVA for group comparison ────────────────────────────────
def perform_group_comparison(
    df: pd.DataFrame, value_col: str, group_col: str
) -> dict:
    """
    So sánh giá trị trung bình giữa các nhóm.
    - 2 nhóm  → independent-samples t-test (Welch)
    - ≥ 3 nhóm → one-way ANOVA + Tukey HSD post-hoc

    Tham khảo: scipy.stats.ttest_ind, scipy.stats.f_oneway,
    statsmodels.stats.multicomp.pairwise_tukeyhsd

    Returns:
        dict với 'test_type', 'statistic', 'p_value', 'group_stats',
        optionally 'posthoc', và 'success'
    """
    try:
        data = df[[value_col, group_col]].dropna()
        groups = data.groupby(group_col)[value_col].apply(list)
        group_names = list(groups.index)
        n_groups = len(group_names)

        if n_groups < 2:
            return {"error": "Cần ít nhất 2 nhóm để so sánh.", "success": False}

        group_arrays = [np.array(g) for g in groups]

        # Group-level stats
        group_stats = []
        for name, arr in zip(group_names, group_arrays):
            group_stats.append({
                "group": str(name),
                "n": len(arr),
                "mean": float(np.mean(arr)),
                "std": float(np.std(arr, ddof=1)),
                "median": float(np.median(arr)),
            })

        if n_groups == 2:
            stat, p = sp_stats.ttest_ind(*group_arrays, equal_var=False)  # Welch's t-test
            result = {
                "test_type": "Welch's t-test",
                "statistic": float(stat),
                "p_value": float(p),
                "significant": p < 0.05,
                "group_stats": group_stats,
                "success": True,
            }
        else:
            stat, p = sp_stats.f_oneway(*group_arrays)
            result = {
                "test_type": "One-way ANOVA",
                "statistic": float(stat),
                "p_value": float(p),
                "significant": p < 0.05,
                "group_stats": group_stats,
                "success": True,
            }
            # Tukey HSD post-hoc
            try:
                from statsmodels.stats.multicomp import pairwise_tukeyhsd
                tukey = pairwise_tukeyhsd(data[value_col], data[group_col], alpha=0.05)
                posthoc_rows = []
                for row in tukey.summary().data[1:]:
                    posthoc_rows.append({
                        "group1": str(row[0]),
                        "group2": str(row[1]),
                        "mean_diff": float(row[2]),
                        "p_adj": float(row[3]),
                        "reject": bool(row[6]),
                    })
                result["posthoc"] = posthoc_rows
            except Exception:
                pass

        return result
    except Exception as e:
        logger.error(f"Lỗi so sánh nhóm: {e}")
        return {"error": str(e), "success": False}


# ─── NEW: regression with standardised β (beta) coefficients ─────────────────
def perform_regression_with_beta(df: pd.DataFrame, dependent_var: str, independent_vars: list) -> dict:
    """
    Hồi quy OLS kèm hệ số hồi quy chuẩn hoá (β) để so sánh tầm quan trọng
    tương đối của các biến độc lập.

    β_i = b_i × (SD_Xi / SD_Y)  — công thức chuẩn hoá từ sklearn/statsmodels docs.

    Returns:
        Kết quả từ perform_regression() với thêm 'beta_coefficients'
    """
    base = perform_regression(df, dependent_var, independent_vars)
    if not base.get("success"):
        return base

    try:
        data = df[[dependent_var] + independent_vars].dropna().apply(pd.to_numeric, errors="coerce").dropna()
        sd_y = data[dependent_var].std()

        beta_dict = {}
        for v_stat in base["variables"]:
            var_name = v_stat["variable"]
            if var_name == "Hằng số":
                continue
            # Find matching column
            col = next((c for c in independent_vars if c == var_name), None)
            if col is None:
                # try matching by text via numeric_questions mapping (caller responsibility)
                continue
            sd_x = data[col].std()
            beta = v_stat["coefficient"] * (sd_x / sd_y) if sd_y != 0 else np.nan
            beta_dict[var_name] = float(beta)

        base["beta_coefficients"] = beta_dict
    except Exception as e:
        logger.warning(f"Không thể tính beta: {e}")

    return base


# ─── NEW: Response quality / completeness check ──────────────────────────────
def check_response_quality(df: pd.DataFrame, columns: list) -> dict:
    """
    Kiểm tra chất lượng dữ liệu:
      - Tỷ lệ missing (%) theo từng cột
      - Phát hiện straight-lining (tất cả câu trả lời giống nhau trong 1 row)
      - Phát hiện outlier tổng thể bằng IQR (trên row sum)

    Tham khảo: Survey methodology best practices (Academic Survey Research).

    Returns:
        dict với 'missing_pct', 'straightline_count', 'row_outliers', 'success'
    """
    try:
        data = df[columns].apply(pd.to_numeric, errors="coerce")
        n = len(data)

        # Missing percentage per column
        missing_pct = (data.isnull().sum() / n * 100).round(1).to_dict()

        # Straight-lining: rows where all non-null values are identical
        def is_straightline(row):
            vals = row.dropna()
            return len(vals) > 1 and vals.nunique() == 1

        straightline_count = int(data.apply(is_straightline, axis=1).sum())

        # Outlier rows: IQR on row-wise mean score
        row_means = data.mean(axis=1)
        q1, q3 = row_means.quantile(0.25), row_means.quantile(0.75)
        iqr = q3 - q1
        row_outliers = int(((row_means < q1 - 1.5 * iqr) | (row_means > q3 + 1.5 * iqr)).sum())

        return {
            "missing_pct": missing_pct,
            "straightline_count": straightline_count,
            "row_outliers": row_outliers,
            "n_responses": n,
            "overall_completeness": float(100 - data.isnull().values.mean() * 100),
            "success": True,
        }
    except Exception as e:
        logger.error(f"Lỗi kiểm tra chất lượng dữ liệu: {e}")
        return {"error": str(e), "success": False}