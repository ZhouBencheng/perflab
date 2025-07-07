import os
import pandas as pd
from bs4 import BeautifulSoup
from scipy.stats import gmean
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from scipy.stats import ttest_rel

# === 参数配置 ===
RESULTS_DIR = 'SPECjvm2008/results/Assignment2/test_20250704_210607_base'
target_benchmarks = ['compress', 'crypto', 'derby']
crypto_subs = ['crypto.aes', 'crypto.rsa', 'crypto.signverify']

# === 工具函数 ===
def safe_gmean(x):
    x = np.array(x)
    x = x[x > 0]
    if len(x) == 0:
        return np.nan
    return gmean(x)

# 统一加密基准名称
def unify_crypto(row):
    return 'crypto' if row['Benchmark'] in crypto_subs else row['Benchmark']

# 提取SPECjvm2008结果
def extract_spec_results(results_dir):
    all_records = []
    for subdir in os.listdir(results_dir):
        html_files = [f for f in os.listdir(os.path.join(results_dir, subdir)) if f.endswith('.html')]
        for html_file in html_files:
            fpath = os.path.join(results_dir, subdir, html_file)
            with open(fpath, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f, 'html.parser')

            # JVM Vendor
            jvm_vendor = None
            for tr in soup.find_all('tr'):
                tds = tr.find_all('td')
                if len(tds) == 2 and 'Vendor' in tds[0].get_text():
                    jvm_vendor = tds[1].get_text().strip()
                    break

            # Benchmark表
            bench_table = None
            for table in soup.find_all('table'):
                ths = table.find_all('th')
                if not ths:
                    tds = table.find_all('td')
                    if tds and 'Benchmark' in tds[0].get_text():
                        bench_table = table
                        break

            # 大项
            if bench_table:
                for tr in bench_table.find_all('tr'):
                    tds = tr.find_all('td')
                    if len(tds) >= 2:
                        bench = tds[0].get_text().strip()
                        try:
                            score = float(tds[1].get_text().strip())
                            if bench in target_benchmarks:
                                all_records.append({
                                    'JVM': jvm_vendor,
                                    'Benchmark': bench,
                                    'Ops/m': score,
                                    'File': html_file,
                                    'Dir': subdir,
                                })
                        except ValueError:
                            pass
            # crypto子项
            for table in soup.find_all('table'):
                trs = table.find_all('tr')
                for i, tr in enumerate(trs):
                    tds = tr.find_all('td')
                    if tds and tds[0].get_text().strip() in crypto_subs:
                        bench = tds[0].get_text().strip()
                        try:
                            for j in [1, 2]:
                                tds2 = trs[i+j].find_all('td')
                                if tds2 and 'iteration' in tds2[2].get_text():
                                    score = float(tds2[6].get_text())
                                    all_records.append({
                                        'JVM': jvm_vendor,
                                        'Benchmark': bench,
                                        'Ops/m': score,
                                        'File': html_file,
                                        'Dir': subdir,
                                    })
                                    break
                        except Exception:
                            continue
    return pd.DataFrame(all_records)

def plot_grouped_bar(
    grouped, 
    value_col='mean', 
    std_col='std', 
    title='', 
    ylabel='', 
    filename='fig.png'
):
    plt.figure(figsize=(10,6))
    ax = sns.barplot(data=grouped, x='Benchmark2', y=value_col, hue='JVM', capsize=0.1)
    for patch, (_, row) in zip(ax.patches, grouped.iterrows()):
        x = patch.get_x() + patch.get_width() / 2
        y = row[value_col]
        yerr = row[std_col]
        plt.errorbar(x, y, yerr=yerr, fmt='none', c='black', capsize=4)
    plt.title(title)
    plt.ylabel(ylabel)
    plt.xlabel('Benchmark')
    plt.tight_layout()
    plt.savefig(filename)
    print(f"图表已保存为 {filename}")

def agg_and_plot(df, agg_func, agg_name, plot_title, file_suffix):
    grouped = df.groupby(['JVM', 'Benchmark2'])['Ops/m'] \
            .agg([agg_func, 'std', 'count']).reset_index()
    if isinstance(agg_func, str):
        grouped.rename(columns={agg_func: agg_name}, inplace=True)
    else:
        grouped.rename(columns={agg_func.__name__: agg_name}, inplace=True)
    print(grouped)
    plot_grouped_bar(
        grouped, 
        value_col=agg_name, 
        std_col='std',
        title=plot_title,
        ylabel=f'Ops/min ({agg_name} ± std)',
        filename=f'specjvm2008_jdk_compare_{file_suffix}.png'
    )

def ttest_paired_report(df, jvm1, jvm2, benchmark):
    """对两个JVM在同一基准下的多组样本做配对t检验"""
    d1 = df[(df['JVM'] == jvm1) & (df['Benchmark2'] == benchmark)]['Ops/m'].sort_index()
    d2 = df[(df['JVM'] == jvm2) & (df['Benchmark2'] == benchmark)]['Ops/m'].sort_index()
    # 自动按index对齐，只要采样对应（如第N次实验都分别有）
    min_len = min(len(d1), len(d2))
    d1 = d1.iloc[:min_len]
    d2 = d2.iloc[:min_len]
    if min_len < 2:
        print(f"样本数不足，无法进行配对t检验: {jvm1} vs {jvm2} @ {benchmark}")
        return None
    t_stat, p_val = ttest_rel(d1, d2, nan_policy='omit')
    diff = d1.values - d2.values
    diff = diff[~np.isnan(diff)]
    if len(diff) == 0:
        mean_diff = np.nan
        std_diff = np.nan
    else:
        mean_diff = diff.mean()
        std_diff = diff.std(ddof=1)
    report = {
        'JVM1': jvm1,
        'JVM2': jvm2,
        'Benchmark': benchmark,
        'mean(JVM1)': d1.mean(),
        'mean(JVM2)': d2.mean(),
        'mean_diff': mean_diff,
        'std_diff': std_diff,
        't_stat': t_stat,
        'p_value': p_val,
        'n': min_len,
    }
    print(
        f"{benchmark:<12} | {jvm1:<18} vs {jvm2:<18} | t={t_stat:>7.3f} | p={p_val:>8.4g} | "
        f"mean_diff={mean_diff:>10.2f}±{std_diff:<8.2f} | n={min_len:<3}"
    )
    return report

if __name__ == "__main__":
    # 1. 解析html为DataFrame
    df = extract_spec_results(RESULTS_DIR)
    df['Benchmark2'] = df.apply(unify_crypto, axis=1)

    # 2. 算数均值聚合和绘图
    agg_and_plot(
        df,
        agg_func='mean',
        agg_name='mean',
        plot_title='SPECjvm2008 Benchmark Comparison (mean ± std)',
        file_suffix='mean'
    )

    # 3. 几何均值聚合和绘图
    agg_and_plot(
        df,
        agg_func=safe_gmean,
        agg_name='gmean',
        plot_title='SPECjvm2008 Benchmark Comparison (geometric mean ± std)',
        file_suffix='gmean'
    )
    
    # === 配对t检验分析 ===
    print('\n===== 配对 t 检验结果（Paired t-test）=====')
    # 自动找出所有基准、所有JVM组合（两两配对）
    jvms = df['JVM'].unique()
    benchmarks = df['Benchmark2'].unique()
    t_results = []
    for benchmark in benchmarks:
        for i in range(len(jvms)):
            for j in range(i+1, len(jvms)):
                r = ttest_paired_report(df, jvms[i], jvms[j], benchmark)
                if r is not None:
                    t_results.append(r)
    # 可将t检验结果转为DataFrame导出
    ttest_df = pd.DataFrame(t_results)
    ttest_df.to_csv('specjvm2008_ttest_paired_results.csv', index=False)
    print('配对t检验结果已导出为 specjvm2008_ttest_paired_results.csv')
