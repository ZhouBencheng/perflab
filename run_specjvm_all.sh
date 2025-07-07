#!/bin/bash

set -e

# 响应ctrl+c中断
trap 'echo; echo "Interrupted by user. Exiting."; exit 1' SIGINT

# 解析参数，默认base run，--peak参数则peak run
MODE="base"
if [[ "$1" == "--peak" ]]; then
  MODE="peak"
  echo "Running in PEAK mode"
else
  echo "Running in BASE mode"
fi

SPECJVM_HOME="/home/ben/workspace/perflab/SPECjvm2008"
BASE_RESULTS_DIR="$SPECJVM_HOME/results"
JDKS_DIR="/home/ben/workspace/perflab/jdks"

TIMESTAMP=$(date +'%Y%m%d_%H%M%S')
TEST_RESULTS_DIR="$BASE_RESULTS_DIR/test_$TIMESTAMP"
LOGFILE="$BASE_RESULTS_DIR/logs/experiment_${TIMESTAMP}.log"

mkdir -p "$TEST_RESULTS_DIR"
mkdir -p "$(dirname "$LOGFILE")"

# 重定向输出到文件并在屏幕中显示
exec > >(tee -a "$LOGFILE") 2>&1

ITERATIONS=3

# 获取jdk待测试列表
declare -A JDK_LIST
JDK_LIST["openjdk"]="$JDKS_DIR/jdk1.8.0_441/bin/java"
JDK_LIST["dragonwell"]="$JDKS_DIR/dragonwell-8.25.24/bin/java"
JDK_LIST["bisheng"]="$JDKS_DIR/bisheng-jdk1.8.0_452/bin/java"
JDK_LIST["kona"]="$JDKS_DIR/TencentKona-8.0.22-452/bin/java"

declare -A JVM_OPTS_MAP
EXTRA_JVM_OPTS_MAP["openjdk"]=""
EXTRA_JVM_OPTS_MAP["dragonwell"]="-XX:+UnlockExperimentalVMOptions -XX:+UseWisp2"
EXTRA_JVM_OPTS_MAP["bisheng"]=""
EXTRA_JVM_OPTS_MAP["kona"]=""

JVM_OPTS="-Xms12g -Xmx12g \
        -XX:+UseParallelGC \
        -XX:ParallelGCThreads=12 \
        -XX:MaxGCPauseMillis=300 \
        -XX:GCTimeRatio=9 \
        -XX:-UseAdaptiveSizePolicy \
        -XX:+AlwaysPreTouch \
        -XX:-UseGCOverheadLimit "

BENCHMARKS=("derby" "compress" "crypto")

WARMUP_TIME=30
ITERATION_TIME=60

SPECJVM_JAR="$SPECJVM_HOME/SPECjvm2008.jar"

echo "=============================="
echo "SPECjvm2008 Batch Runner Start"
echo "Results will be saved in: $TEST_RESULTS_DIR"
echo "=============================="

cd "$SPECJVM_HOME"

for jdk in "${!JDK_LIST[@]}"; do
    JAVA_CMD="${JDK_LIST[$jdk]}"

    if [[ "$MODE" == "peak" && "$jdk" == "dragonwell" ]]; then
        JVM_OPTS="$JVM_OPTS ${JVM_OPTS_MAP[$jdk]}"
    fi
    
    echo
    echo "--------------------------------------"
    echo "Testing JDK: $jdk"
    echo "Java Command: $JAVA_CMD"
    echo "--------------------------------------"

    for ((i=1; i<=ITERATIONS; i++)); do
        # timestamp=$(date +'%Y%m%d_%H%M%S')
        # logfile="$RESULT_DIR/${jdk}_run${i}_$timestamp.log"
        
        echo ">>> Running iteration $i for $jdk"
        # echo ">>> Logging to $logfile"

        # 获取子测试列表
        BENCH_ARGS=""
        for b in "${BENCHMARKS[@]}"; do
            BENCH_ARGS="$BENCH_ARGS $b"
        done
        
        "$JAVA_CMD" $JVM_OPTS \
                    -Dspecjvm.home.dir="$SPECJVM_HOME" \
                    -Dspecjvm.result.dir="$TEST_RESULTS_DIR" \
                    -jar "$SPECJVM_JAR" -ikv \
                    -wt $WARMUP_TIME -it $ITERATION_TIME \
                    $BENCH_ARGS
        
        echo ">>> Completed iteration $i for $jdk"
        echo
    done
done

echo "=============================="
echo "All JDK runs completed!"
# echo "Logs are in: $RESULT_DIR"
echo "=============================="
