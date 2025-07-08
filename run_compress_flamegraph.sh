#!/bin/bash

set -euo pipefail

#### —— 请按自己机器情况修改这几行 —— ####
SPEC_HOME=/home/ben/workspace/perflab/SPECjvm2008              # SPECjvm2008 目录
FG_HOME=/home/ben/workspace/perflab/tools/FlameGraph           # FlameGraph 脚本集
PMA_HOME=/home/ben/workspace/perflab/tools/perf-map-agent      # perf-map-agent
JAVA_BIN=/home/ben/workspace/perflab/jdks/jdk1.8.0_441/bin/java
SAMPLES=100       # perf 采样频率 Hz
DURATION=180      # 采样时长  s
EXPORT_SQLITE=/home/ben/workspace/perflab/tools/linux/tools/perf/scripts/python/export-to-sqlite.py
##################################################

BENCH=compress
RUN_ID=$(date +%Y%m%d_%H%M%S)
OUT_DIR=$PWD/perf_${BENCH}_${RUN_ID}
mkdir -p "$OUT_DIR"

cleanup() {
    echo "脚本出错，正在清理 $OUT_DIR ..."
    sudo rm -rf "$OUT_DIR"
    sudo rm -rf "$SPEC_HOME/results/SPECjvm2008.001"
}
trap 'cleanup' ERR

echo ">>> 启动 SPECjvm2008 $BENCH 基准……"

cd $SPEC_HOME

exec > >(tee -a "$OUT_DIR/spec.log") 2>&1

$JAVA_BIN \
  -XX:+PreserveFramePointer \
  -XX:+UnlockDiagnosticVMOptions -XX:+DebugNonSafepoints \
  -jar "SPECjvm2008.jar" \
  -wt 60s -it 180s "$BENCH" &
APP_PID=$!
echo "    JVM PID = $APP_PID"

sleep 30   # 让 JVM 进入稳定迭代

echo ">>> 生成 perf-map（Java ↔ JIT 代码地址映射）"
sudo -E JAVA_HOME=$JAVA_HOME "$PMA_HOME/bin/create-java-perf-map.sh" $APP_PID

echo ">>> perf 采样 $DURATION 秒"
# 并发执行 perf stat 和 perf record
sudo -E perf stat -e task-clock,context-switches,cpu-migrations,page-faults,cycles,instructions,branches,branch-misses \
                  -e cache-references,cache-misses,L1-dcache-loads,L1-dcache-load-misses,LLC-loads,LLC-load-misses \
                  -p $APP_PID -o "$OUT_DIR/perf_stat.txt" \
                  -- sleep $DURATION &
PERF_STAT_PID=$!
# sudo -E perf record -F $SAMPLES -g -p $APP_PID --output="$OUT_DIR/perf.data" -- sleep $DURATION
for F in 50 250 1000; do
  OUT=perf_F${F}
  sudo perf record -F $F -g -o $OUT_DIR/$OUT.data -p $APP_PID -- sleep 60
  echo "$(du -h $OUT_DIR/$OUT.data | cut -f1)  ← perf.data @${F}Hz"
  sudo perf script -i "$OUT_DIR/$OUT.data" -s "$EXPORT_SQLITE" "$OUT_DIR/$OUT.sqlite" all calls
done
wait $PERF_STAT_PID # 等待 perf stat 完成

echo ">>> 解码并绘制火焰图"
for F in 50 250 1000; do
  OUT=perf_F${F}
  echo "    正在处理 $OUT.data ..."
  sudo -E perf script -i "$OUT_DIR/$OUT.data" > "$OUT_DIR/$OUT.perf"
  "$FG_HOME/stackcollapse-perf.pl" "$OUT_DIR/$OUT.perf" > "$OUT_DIR/$OUT.folded"
  "$FG_HOME/flamegraph.pl" \
    --title="SPECjvm2008 $BENCH – $F Hz / $DURATION s" \
    "$OUT_DIR/$OUT.folded" > "$OUT_DIR/$OUT.flamegraph.svg"

  echo ">>> 生成perf report 文本报告"
  sudo -E perf report -i "$OUT_DIR/$OUT.data" --stdio > "$OUT_DIR/$OUT.perf_report.txt"
done

echo ">>> 完成！火焰图路径： $OUT_DIR/flamegraph.svg"
echo "    用浏览器打开即可交互查看热点栈帧。"

wait $APP_PID || true
