YEARS_FIT = list(range(2018, 2025))
YEARS_HP = [2025]
YEARS_FINAL = list(range(2018, 2026))
YEARS_TEST = [2026]

TREE_MODELS = ["RF", "XGB", "LGB", "CatBoost"]


def split_by_year(df: pd.DataFrame, seed: int = 123):
    y = df["date"].dt.year
    df_fit = df[y.isin(YEARS_FIT)].sample(frac=1, random_state=seed).reset_index(drop=True)
    df_hp = df[y.isin(YEARS_HP)].sort_values("date").reset_index(drop=True)
    df_final = df[y.isin(YEARS_FINAL)].sample(frac=1, random_state=seed).reset_index(drop=True)
    df_test = df[y.isin(YEARS_TEST)].sort_values("date").reset_index(drop=True)
    assert set(YEARS_FIT).isdisjoint(YEARS_HP)
    assert set(YEARS_TEST).isdisjoint(YEARS_FINAL)
    assert df_test["date"].min() > df_final["date"].max()
    return df_fit, df_hp, df_final, df_test


def fit_predict(name: str, params: dict, X_train, y_train, X_test, seed=123):
    """Return (fitted_model, y_train_pred, y_test_pred). OLS uses statsmodels."""
    if name == "OLS":
        Xtr = sm.add_constant(X_train.astype(float), has_constant="add")
        Xte = sm.add_constant(X_test.astype(float), has_constant="add")
        Xte = Xte.reindex(columns=Xtr.columns, fill_value=0.0)
        y_arr = np.asarray(y_train, dtype=float).reshape(-1)
        m = sm.OLS(y_arr, Xtr.values.astype(float)).fit()
        ytr = m.predict(Xtr.values.astype(float))
        yte = m.predict(Xte.values.astype(float))
        return m, ytr, yte

    m = make_model(name, params, seed=seed)
    m.fit(X_train, y_train)
    return m, m.predict(X_train), m.predict(X_test)


def evaluation_reg(y_true, y_pred) -> pd.DataFrame:
    yt = np.asarray(y_true).reshape(-1)
    yp = np.asarray(y_pred).reshape(-1)
    mae = mean_absolute_error(yt, yp)
    mse = mean_squared_error(yt, yp)
    rmse = float(np.sqrt(mse))
    mask = np.abs(yt) > 1e-9
    mape = float(np.mean(np.abs((yt[mask] - yp[mask]) / yt[mask]))) if mask.any() else np.nan
    r2 = r2_score(yt, yp) if len(yt) > 1 else np.nan
    return pd.DataFrame([[mae, mse, rmse, mape, r2]],
                        columns=["MAE", "MSE", "RMSE", "MAPE", "R2"])


def evaluation_reg_trte(ytr, ytrp, yte, ytep) -> pd.DataFrame:
    out = pd.concat([evaluation_reg(ytr, ytrp), evaluation_reg(yte, ytep)], axis=0)
    out.index = ["Train", "Test"]
    return out


def shap_values_tree(model, X) -> np.ndarray:
    if shap is None:
        raise ImportError("SHAP is not installed; rerun with --skip-shap or install shap.")
    explainer = shap.TreeExplainer(model)
    sv = explainer.shap_values(X)
    sv = np.asarray(sv)
    if sv.ndim == 3:
        sv = sv[:, :, 0]
    return sv


def shap_share_table(shap_arr: np.ndarray, feature_names: list[str]) -> pd.DataFrame:
    mabs = np.abs(shap_arr).mean(axis=0)
    total = mabs.sum() if mabs.sum() > 0 else 1.0
    df = pd.DataFrame({
        "feature": feature_names,
        "mean_abs_shap": mabs,
        "mean_abs_shap_share": mabs / total,
    }).sort_values("mean_abs_shap_share", ascending=False).reset_index(drop=True)
    return df


def restore_pred_close_v2(target, pred, lag1_close, ranker=None) -> dict:
    p = np.asarray(pred, dtype=float).reshape(-1)
    l = np.asarray(lag1_close, dtype=float).reshape(-1)

    if target.endswith("_rank"):
        if ranker is None:
            raise ValueError("rank target requires ranker.")
        p_raw = ranker.inverse(np.clip(p, 0.0, 1.0))
        base = target.replace("_rank", "")
    else:
        p_raw = p
        base = target

    if base == "close":
        pred_close = p_raw
        pred_delta = p_raw - l
        pred_return = np.where(l != 0, pred_delta / l, np.nan)
    elif base == "delta":
        pred_close = l + p_raw
        pred_delta = p_raw
        pred_return = np.where(l != 0, p_raw / l, np.nan)
    elif base == "return":
        pred_close = l * (1.0 + p_raw)
        pred_delta = p_raw * l
        pred_return = p_raw
    elif base == "logret":
        exp_p = np.exp(p_raw)
        pred_close = l * exp_p
        pred_delta = pred_close - l
        pred_return = exp_p - 1.0
    else:
        raise ValueError(f"unknown target: {target}")

    return {
        "pred_close": pred_close,
        "pred_delta": pred_delta,
        "pred_return": pred_return,
    }


def common_metrics_v2(actual_close, lag1_close, pred_close, pred_delta, pred_return,
                      vintage_transition, auction_window5) -> dict:
    a = np.asarray(actual_close, dtype=float).reshape(-1)
    l = np.asarray(lag1_close, dtype=float).reshape(-1)
    pc = np.asarray(pred_close, dtype=float).reshape(-1)
    pd_ = np.asarray(pred_delta, dtype=float).reshape(-1)
    pr = np.asarray(pred_return, dtype=float).reshape(-1)
    vt = np.asarray(vintage_transition, dtype=bool).reshape(-1)
    aw = np.asarray(auction_window5, dtype=int).reshape(-1)

    actual_delta = a - l
    actual_return = np.where(l != 0, actual_delta / l, np.nan)

    rmse = float(np.sqrt(np.mean((a - pc) ** 2)))
    mae = float(np.mean(np.abs(a - pc)))
    rw_rmse = float(np.sqrt(np.mean((a - l) ** 2)))
    rw_mae = float(np.mean(np.abs(a - l)))
    delta_mae = float(np.mean(np.abs(actual_delta - pd_)))

    valid_ret = ~np.isnan(actual_return) & ~np.isnan(pr)
    ret_mae = (
        float(np.mean(np.abs(actual_return[valid_ret] - pr[valid_ret])))
        if valid_ret.any()
        else np.nan
    )

    nonvt = ~vt
    if nonvt.sum() > 0:
        sa = np.sign(actual_delta[nonvt])
        sp = np.sign(pd_[nonvt])
        dir_acc = float(np.mean(sa == sp))

        nz = nonvt & (actual_delta != 0)
        if nz.sum() > 0:
            sa2 = np.sign(actual_delta[nz])
            sp2 = np.sign(pd_[nz])
            nonzero_dir_acc = float(np.mean(sa2 == sp2))
        else:
            nonzero_dir_acc = np.nan
    else:
        dir_acc = np.nan
        nonzero_dir_acc = np.nan

    zero_mask = actual_delta == 0
    nonzero_mask = actual_delta != 0
    zero_day_mae = float(np.mean(np.abs((a - pc)[zero_mask]))) if zero_mask.any() else np.nan
    nonzero_day_mae = float(np.mean(np.abs((a - pc)[nonzero_mask]))) if nonzero_mask.any() else np.nan

    aw_mask = aw == 1
    naw_mask = aw == 0
    aw_mae = float(np.mean(np.abs((a - pc)[aw_mask]))) if aw_mask.any() else np.nan
    naw_mae = float(np.mean(np.abs((a - pc)[naw_mask]))) if naw_mask.any() else np.nan

    return {
        "pred_close_MAE": mae,
        "pred_close_RMSE": rmse,
        "delta_MAE": delta_mae,
        "return_MAE": ret_mae,
        "rw_ratio_MAE": mae / rw_mae if rw_mae > 0 else np.nan,
        "rw_ratio_RMSE": rmse / rw_rmse if rw_rmse > 0 else np.nan,
        "direction_acc": dir_acc,
        "nonzero_direction_acc": nonzero_dir_acc,
        "zero_day_MAE": zero_day_mae,
        "nonzero_day_MAE": nonzero_day_mae,
        "auction_window5_MAE": aw_mae,
        "non_auction_window5_MAE": naw_mae,
    }


class ECDFRanker:
    def __init__(self):
        self.sorted_ = None

    def fit(self, values):
        v = np.asarray(values, dtype=float).reshape(-1)
        v = v[~np.isnan(v)]
        self.sorted_ = np.sort(v)
        return self

    def transform(self, values) -> np.ndarray:
        v = np.asarray(values, dtype=float).reshape(-1)
        n = len(self.sorted_)
        idx = np.searchsorted(self.sorted_, v, side="right")
        idx_left = np.searchsorted(self.sorted_, v, side="left")
        avg_idx = (idx + idx_left) / 2.0
        return (avg_idx + 0.5) / n

    def inverse(self, q) -> np.ndarray:
        q = np.clip(np.asarray(q, dtype=float).reshape(-1), 0.0, 1.0)
        return np.quantile(self.sorted_, q, method="linear")
