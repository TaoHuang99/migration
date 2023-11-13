#!/bin/bash

# 将自定义的service文件复制到systemd的目录
sudo cp /home/admin/migration/migration.service /etc/systemd/system/migration.service

# 重新加载systemd daemon
sudo systemctl daemon-reload

# 启用service
sudo systemctl enable migration.service

# 启动service
sudo systemctl start migration.service

# 查看service的状态
sudo systemctl status migration.service
