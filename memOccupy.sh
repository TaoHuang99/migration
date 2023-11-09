#!/bin/bash

# 获取总内存大小（以KB为单位）
total_memory_kb=$(grep MemTotal /proc/meminfo | awk '{print $2}')

# 计算60%的内存大小（以KB为单位）
target_memory_kb=$(echo "$total_memory_kb * 0.6" | bc)

# 在/dev/shm下创建一个占用60%内存的文件
target_file="/dev/shm/bigfile"

# 使用dd命令创建文件
dd if=/dev/zero of="$target_file" bs=1024 count="$target_memory_kb"

echo "Created a file of size $(du -h "$target_file" | cut -f1) at $target_file, approximately 60% of total memory."
