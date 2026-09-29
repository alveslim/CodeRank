#!/bin/sh
set -eu

submission_dir="/tmp/submission"
classes_dir="/tmp/classes"

mkdir -p "$submission_dir" "$classes_dir"
cat > "$submission_dir/Main.java"

javac -encoding UTF-8 -d "$classes_dir" "$submission_dir/Main.java"
exec java -Xmx128m -XX:ActiveProcessorCount=1 -cp "$classes_dir" Main
