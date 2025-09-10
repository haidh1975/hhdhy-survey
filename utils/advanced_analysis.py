import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score, mean_squared_error
from factor_analyzer import FactorAnalyzer
from factor_analyzer.factor_analyzer import calculate_bartlett_sphericity, calculate_kmo
import statsmodels.api as sm
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