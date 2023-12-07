import paramiko
from scp import SCPClient
import os

def create_ssh_client(server, port, user, password):
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(server, port, user, password)
    return client

def remove_remote_folder(ssh_client, folder_path):
    stdin, stdout, stderr = ssh_client.exec_command(f'rm -rf {folder_path}')
    stderr.readlines()  # 等待命令执行完成

def scp_transfer(ssh_client, local_path, remote_path):
    with SCPClient(ssh_client.get_transport()) as scp:
        # 获取本地文件夹的名称
        folder_name = os.path.basename(local_path.rstrip('/'))

        # 递归复制整个文件夹的内容
        scp.put(local_path, recursive=True, remote_path=os.path.join(remote_path, folder_name))


# 服务器配置
server = "192.168.122.26"
port = 22  # SSH端口
user = "admin"
password = "123"

# 要复制的本地文件夹和目标路径
current_user = os.getlogin()
local_folder = f"/home/{current_user}/piskes_file"
remote_folder = "/home/admin/"  # 目标路径

# 创建SSH客户端并传输文件
ssh_client = create_ssh_client(server, port, user, password)
scp_transfer(ssh_client, local_folder, remote_folder)
ssh_client.close()
