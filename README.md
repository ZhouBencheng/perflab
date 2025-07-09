# Performance Measurement, Evaluation and Analysis

## :file_folder: File Structure

```
  .  
  ├── SPECjvm2008-----------------（SPECjvm2008安装路径）  
  |     ├── data -----------------------（pipa测量结果）
  |     └── results --------------------（SPECjvm2008输出结果）
  ├── img1\2\3--------------------（assignmen1\2\3文档的图片）  
  ├── perf_compress_$(datetime)---（assignmen3测试数据）
  ├── assignment*.md--------------（assignment1\2\3的实验文档）
  ├── perf_sqlite_analysis.py----- (assignment3: sqlite可视化脚本)
  ├── report.py ------------------ (assignment2: SPECjvm2008/results/*/*.html可视化脚本)
  ├── run_compress_flamegraph.sh-- (assignment3: compress 负载多频率采样脚本)
  └── run_specjvm_all.sh --------- (assignment2: 4种jdk下SPECjvm2008测试脚本)
```

## :page_with_curl: Comments

- 本实验中，所有**第三方**工具软件包均未上传至远程仓库，本仓库中只包含自编脚本文件和生成的数据文件。assignment2的4种jdk安装在`./jdks`目录下，assignment3中使用到的工具`pef-map-agent` `FlameGraph` `export-to-sqlite.py`安装在`./tools`目录下，`SPECjvm2008`安装在`./SPECjvm2008`目录下，git只跟踪其下的`results`子目录。
- 实验中用到`.sh`和`.py`脚本中的路径大部分使用绝对路径，如需复现需要更改为当前机器的本地实际路径
