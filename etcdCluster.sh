#!/bin/bash

# 检查bash版本，确保它支持关联数组
if [[ ${BASH_VERSINFO[0]} -lt 4 ]]; then
    echo "This script requires Bash version >= 4.0 for associative arrays support."
    exit 1
fi

# 定义ETCD的版本
ETCD_VERSION="v3.5.7"
TOKEN="my-etcd-cluster"
CLUSTER_STATE="new"

# 自动获取当前节点的IP地址
CURRENT_IP=$(hostname -I | awk '{print $1}')

# 自动生成当前节点的名称，使用IP地址的最后一个段落
THIS_NODE="etcd-$(echo $CURRENT_IP | awk -F '.' '{print $NF}')"

# 输出本节点的etcd名称
echo "Current node's etcd name: $THIS_NODE"

# 自动发现集群中的其他节点
declare -A NODES  # 声明关联数组
START_IP=2  #开始的IP地址
END_IP=254    #最后的IP地址
# 添加当前节点到NODES
NODES["$THIS_NODE"]=$CURRENT_IP

for i in $(seq $START_IP $END_IP); do
    if [[ "192.168.122.$i" != "$CURRENT_IP" ]]; then
        NODE_IP="192.168.122.$i"
        ping -c 1 -W 1 $NODE_IP > /dev/null 2>&1
        if [[ $? -eq 0 ]]; then
            NODE_NAME="etcd-$i"
            NODES["$NODE_NAME"]=$NODE_IP
            echo "Node $NODE_NAME ($NODE_IP) is active."
        fi
    fi
done

echo "Active nodes in the cluster:"
for NODE in "${!NODES[@]}"; do
    echo "Name: $NODE, IP: ${NODES[$NODE]}"
done

# 拉取ETCD的Docker镜像
docker pull quay.io/coreos/etcd:$ETCD_VERSION

# 生成initial-cluster字符串
INITIAL_CLUSTER=""
for NODE_NAME in "${!NODES[@]}"; do
    INITIAL_CLUSTER+="$NODE_NAME=http://${NODES[$NODE_NAME]}:2380,"
done
INITIAL_CLUSTER=${INITIAL_CLUSTER::-1}  # 移除最后一个逗号

# 检查是否存在名为$THIS_NODE的容器
if docker ps -a --filter "name=$THIS_NODE" | grep -q "$THIS_NODE"; then
    echo "Container named $THIS_NODE already exists. Removing..."
    docker stop $THIS_NODE
    docker rm -f $THIS_NODE
fi

# 启动ETCD容器
if [[ -v NODES["$THIS_NODE"] ]]; then
    docker run -d \
    --net=host \
    -p 2379:2379 \
    -p 2380:2380 \
    --name etcd1030 quay.io/coreos/etcd:$ETCD_VERSION \
    /usr/local/bin/etcd \
    --data-dir=data.etcd \
    --name $THIS_NODE \
    --initial-advertise-peer-urls http://${NODES["$THIS_NODE"]}:2380 \
    --listen-peer-urls http://${NODES["$THIS_NODE"]}:2380 \
    --listen-client-urls http://${NODES["$THIS_NODE"]}:2379 \
    --advertise-client-urls http://${NODES["$THIS_NODE"]}:2379 \
    --initial-cluster-token $TOKEN \
    --initial-cluster $INITIAL_CLUSTER \
    --initial-cluster-state $CLUSTER_STATE 
else
    echo "Invalid custom node name or not part of the cluster"
fi

# 等待1分钟，确保etcd完全启动
sleep 60

# 使用API版本3
export ETCDCTL_API=3


