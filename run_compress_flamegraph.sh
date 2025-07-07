#!/bin/bash

set -euo pipefail

#### —— 请按自己机器情况修改这几行 —— ####
SPEC_HOME=SPECjvm2008              # SPECjvm2008 目录
FG_HOME=/home/ben/workspace/perflab/tools/FlameGraph           # FlameGraph 脚本集
PMA_HOME=/home/ben/workspace/perflab/tools/perf-map-agent      # perf-map-agent
JAVA_BIN=/home/ben/workspace/perflab/jdks/jdk1.8.0_441/bin/java
SAMPLES=99       # perf 采样频率 Hz
DURATION=60      # 采样时长  s
##################################################

BENCH=compress
RUN_ID=$(date +%Y%m%d_%H%M%S)
OUT_DIR=$PWD/perf_${BENCH}_${RUN_ID}
mkdir -p "$OUT_DIR"

echo ">>> 启动 SPECjvm2008 $BENCH 基准……"

cd $SPEC_HOME

exec > >(tee -a "$OUT_DIR/spec.log") 2>&1

$JAVA_BIN \
  -XX:+PreserveFramePointer \
  -XX:+UnlockDiagnosticVMOptions -XX:+DebugNonSafepoints \
  -jar "SPECjvm2008.jar" \
  -wt 30s -it 60s "$BENCH" &
APP_PID=$!
echo "    JVM PID = $APP_PID"

sleep 30   # 让 JVM 进入稳定迭代

echo ">>> 生成 perf-map（Java ↔ JIT 代码地址映射）"
sudo -E "$PMA_HOME/bin/create-java-perf-map.sh" $APP_PID

echo ">>> perf 采样 $DURATION 秒（${SAMPLES} Hz）"
sudo -E perf record -F $SAMPLES -g -p $APP_PID --output="$OUT_DIR/perf.data" -- sleep $DURATION

echo ">>> 解码并绘制火焰图"
sudo -E perf script -i "$OUT_DIR/perf.data" > "$OUT_DIR/out.perf"
"$FG_HOME/stackcollapse-perf.pl" "$OUT_DIR/out.perf" > "$OUT_DIR/out.folded"
"$FG_HOME/flamegraph.pl" \
  --title="SPECjvm2008 $BENCH – $SAMPLES Hz / $DURATION s" \
  "$OUT_DIR/out.folded" > "$OUT_DIR/flamegraph.svg"

echo ">>> 完成！火焰图路径： $OUT_DIR/flamegraph.svg"
echo "    用浏览器打开即可交互查看热点栈帧。"

wait $APP_PID || true
