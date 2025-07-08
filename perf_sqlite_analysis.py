import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# === 数据准备 ===
FREQS = [50, 250, 1000]
DB_FILES = {f"{f}Hz": f"perf_compress_20250708_152348/perf_F{f}.sqlite" for f in FREQS}
HOT_TOP_N = 20

# === 1. 样本总数对比 ===
total_samples = []
for freq, db_file in DB_FILES.items():
    with sqlite3.connect(db_file) as conn:
        cnt = pd.read_sql("SELECT COUNT(*) FROM samples;", conn).iloc[0,0]
        total_samples.append({'freq': freq, 'samples': cnt})
df_total = pd.DataFrame(total_samples)

plt.rcParams['font.sans-serif']=['SimHei'] #用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False #用来正常显示负号

plt.figure(figsize=(6,4))
sns.barplot(data=df_total, x='freq', y='samples')
plt.title("总采样数与采样频率关系")
plt.ylabel("样本总数")
plt.xlabel("采样频率")
plt.tight_layout()
plt.savefig("total_samples_vs_freq.png")
plt.close()

# === 2. 热点方法 Top N 采样数对比 ===
dfs_top = []
for freq, db_file in DB_FILES.items():
    with sqlite3.connect(db_file) as conn:
        sql = f"""
        SELECT s.name, COUNT(sa.id) AS samples
        FROM samples sa
        JOIN symbols s ON sa.symbol_id = s.id
        GROUP BY sa.symbol_id
        ORDER BY samples DESC
        LIMIT {HOT_TOP_N}
        """
        df = pd.read_sql(sql, conn)
        df['freq'] = freq
        dfs_top.append(df)
df_top = pd.concat(dfs_top)

plt.figure(figsize=(12,10))
for freq in DB_FILES.keys():
    dfp = df_top[df_top['freq']==freq].reset_index(drop=True)
    plt.barh([f"{i+1}.{n[:40]}" for i,n in enumerate(dfp['name'])], dfp['samples'], alpha=0.7, label=freq)
plt.xscale('log')  # 横坐标对数化
plt.title(f"各采样频率下Top{HOT_TOP_N}热点方法采样数对比")
plt.xlabel("采样数")
plt.ylabel("方法名")
plt.legend()
plt.tight_layout()
plt.savefig("hot_methods_topN_compare.png")
plt.close()

# 取所有频率下TopN方法合集
all_methods = pd.unique(df_top['name'])

# 按最高频率下的采样数排序（也可按总采样数排序）
main_freq = max(DB_FILES.keys(), key=lambda x: int(x.replace('Hz','')))
df_main = df_top[df_top['freq'] == main_freq].set_index('name')
sorted_methods = df_main.sort_values('samples', ascending=False).index.tolist()
# 若有方法不在主频率TopN，补充到末尾
sorted_methods += [m for m in all_methods if m not in sorted_methods]

# 构造分组条形图数据
bar_width = 0.2
y = range(len(sorted_methods))
plt.figure(figsize=(14, max(8, len(sorted_methods)*0.3)))
for i, freq in enumerate(DB_FILES.keys()):
    dfp = df_top[df_top['freq']==freq].set_index('name')
    samples = [dfp.loc[m, 'samples'] if m in dfp.index else 0 for m in sorted_methods]
    plt.barh([yy + i*bar_width for yy in y], samples, height=bar_width, label=freq, alpha=0.8)
plt.yticks([yy + bar_width for yy in y], [f"{i+1}.{n[:40]}" for i, n in enumerate(sorted_methods)])
plt.xscale('log')
plt.title(f"各采样频率下Top{HOT_TOP_N}热点方法采样数对比（分组对齐）")
plt.xlabel("采样数（对数坐标）")
plt.ylabel("方法名")
plt.legend()
plt.tight_layout()
plt.savefig("hot_methods_topN_compare_grouped.png")
plt.close()

# === 3. 各方法总 period（函数耗时近似） ===
dfs_cycles = []
for freq, db_file in DB_FILES.items():
    with sqlite3.connect(db_file) as conn:
        sql = f"""
        SELECT s.name, SUM(sa.period) AS cycles
        FROM samples sa
        JOIN symbols s ON sa.symbol_id = s.id
        GROUP BY sa.symbol_id
        ORDER BY cycles DESC
        LIMIT {HOT_TOP_N}
        """
        df = pd.read_sql(sql, conn)
        df['freq'] = freq
        dfs_cycles.append(df)
df_cycles = pd.concat(dfs_cycles)

plt.figure(figsize=(12,12))
for freq in DB_FILES.keys():
    dfc = df_cycles[df_cycles['freq']==freq].reset_index(drop=True)
    plt.barh([f"{i+1}.{n[:40]}" for i,n in enumerate(dfc['name'])], dfc['cycles'], alpha=0.7, label=freq)
plt.title(f"各采样频率下Top{HOT_TOP_N}热点方法总cycles（函数耗时）对比")
plt.xscale('log')  # 横坐标对数化
plt.xlabel("总cycles")
plt.ylabel("方法名")
plt.legend()
plt.tight_layout()
plt.savefig("hot_methods_cycles_compare.png")
plt.close()

# 取所有频率下TopN方法合集
all_methods_cycles = pd.unique(df_cycles['name'])

# 按最高频率下的cycles排序（也可按总cycles排序）
main_freq = max(DB_FILES.keys(), key=lambda x: int(x.replace('Hz','')))
df_main_cycles = df_cycles[df_cycles['freq'] == main_freq].set_index('name')
sorted_methods_cycles = df_main_cycles.sort_values('cycles', ascending=False).index.tolist()
# 若有方法不在主频率TopN，补充到末尾
sorted_methods_cycles += [m for m in all_methods_cycles if m not in sorted_methods_cycles]

# 构造分组条形图数据
bar_width = 0.2
y = range(len(sorted_methods_cycles))
plt.figure(figsize=(14, max(8, len(sorted_methods_cycles)*0.4)))
for i, freq in enumerate(DB_FILES.keys()):
    dfp = df_cycles[df_cycles['freq']==freq].set_index('name')
    cycles = [dfp.loc[m, 'cycles'] if m in dfp.index else 0 for m in sorted_methods_cycles]
    plt.barh([yy + i*bar_width for yy in y], cycles, height=bar_width, label=freq, alpha=0.8)
plt.yticks([yy + bar_width for yy in y], [f"{i+1}.{n[:40]}" for i, n in enumerate(sorted_methods_cycles)])
plt.xscale('log')
plt.title(f"各采样频率下Top{HOT_TOP_N}热点方法总cycles（函数耗时）对比（分组对齐）")
plt.xlabel("总cycles（对数坐标）")
plt.ylabel("方法名")
plt.legend()
plt.tight_layout()
plt.savefig("hot_methods_cycles_compare_grouped.png")
plt.close()

# === 4. 栈深度分布 ===
def compute_depths(conn):
    # 读取 call_paths 表
    df_cp = pd.read_sql("SELECT id, parent_id FROM call_paths", conn)
    id2parent = dict(zip(df_cp['id'], df_cp['parent_id']))
    depth_cache = {}

    def get_depth(cid):
        if cid in depth_cache:
            return depth_cache[cid]
        parent = id2parent.get(cid)
        if parent is None or parent == 0:
            depth_cache[cid] = 1
        else:
            depth_cache[cid] = 1 + get_depth(parent)
        return depth_cache[cid]

    for cid in id2parent:
        get_depth(cid)
    return depth_cache

dfs_depth = []
for freq, db_file in DB_FILES.items():
    with sqlite3.connect(db_file) as conn:
        depth_map = compute_depths(conn)
        df_samples = pd.read_sql("SELECT call_path_id FROM samples", conn)
        df_samples['depth'] = df_samples['call_path_id'].map(depth_map)
        df_depth = df_samples.groupby('depth').size().reset_index(name='cnt')
        df_depth['freq'] = freq
        dfs_depth.append(df_depth)
df_depth = pd.concat(dfs_depth)

plt.figure(figsize=(10,5))
sns.lineplot(data=df_depth, x='depth', y='cnt', hue='freq', marker="o")
plt.title("不同采样频率下栈深度分布")
plt.ylabel("采样数")
plt.xlabel("栈深度")
plt.tight_layout()
plt.savefig("call_stack_depth_dist.png")
plt.close()

# === 热点方法随采样频率的排名变动（热度收敛性） ===
# 合并所有热点，统计各采样频率下排名
all_methods = pd.unique(df_top['name'])
rank_data = []
for freq, db_file in DB_FILES.items():
    with sqlite3.connect(db_file) as conn:
        sql = f"""
        SELECT s.name, COUNT(sa.id) AS samples
        FROM samples sa
        JOIN symbols s ON sa.symbol_id = s.id
        GROUP BY sa.symbol_id
        ORDER BY samples DESC
        """
        df = pd.read_sql(sql, conn)
        df['rank'] = range(1, len(df)+1)
        for name in all_methods:
            row = df[df['name']==name]
            rank = row['rank'].iloc[0] if not row.empty else None
            rank_data.append({'method': name, 'freq': freq, 'rank': rank})
df_rank = pd.DataFrame(rank_data)
# 可导出 df_rank 用于表格展示方法排名波动
df_rank.to_csv("hot_methods_rank_table.csv", index=False)

print("全部统计与可视化已完成，生成的png图表可直接用于实验报告。")
