#!/bin/bash

# 声明网站域名和IP地址之间的映射关系
declare -A domain_ip_map=(
  [http://piskes-4.com]=192.168.122.178
  [http://piskes-5.com]=192.168.122.84
  [http://piskes-6.com]=192.168.122.142
)

for domain in "${!domain_ip_map[@]}"; do
  ip=${domain_ip_map[$domain]}

  # 存储 域名 -> IP地址
  docker exec -it ETCD etcdctl put $domain $ip

  # 存储 IP地址 -> 域名
  docker exec -it ETCD etcdctl put $ip $domain
done



