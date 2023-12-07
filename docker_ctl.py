from flask import Flask, jsonify
from flask import request
import docker
import subprocess
import paramiko
from scp import SCPClient
import os
import configparser

app = Flask(__name__)
client = docker.DockerClient(base_url='unix://var/run/docker.sock')

current_user = os.getlogin()
script_path = f"/home/{current_user}/piskes_file/docker_run/docker_run.sh"

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
        folder_name = os.path.basename(local_path.rstrip('/'))
        remote_folder_path = os.path.join(remote_path, folder_name)

        # 删除远程主机上的现有文件夹
        remove_remote_folder(ssh_client, remote_folder_path)

        # 递归复制整个文件夹
        scp.put(local_path, recursive=True, remote_path=remote_folder_path)

class CasePreservingConfigParser(configparser.ConfigParser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 重写 optionxform 方法，使其返回原始的大小写键名
        self.optionxform = lambda option: option

@app.route("/containers/<container_name>/stop", methods=['POST'])
def stop_container(container_name):
    try:
        container = client.containers.get(container_name)
        container.stop()
        return jsonify({'message': f'Container {container_name} stopped successfully!'}), 204
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/containers/<container_name>/start", methods=['POST'])
def start_container(container_name):
    try:
        data = request.get_json()
        if not data or 'dstIp' not in data:
            return jsonify({'error': 'Missing dstIp in request data'}), 500

        server = data.get('dstIp')
        port = 22 
        user = "ht"
        password = "123"

        local_folder = f"/home/{current_user}/piskes_file"
        remote_folder = "/home/ht/"  # 目标路径

        ssh_client = create_ssh_client(server, port, user, password)
        scp_transfer(ssh_client, local_folder, remote_folder)
        ssh_client.close()


        return jsonify({'message': 'file migration successfully!'}), 204

    except Exception as e:
        app.logger.error('Error in start_container: %s', str(e))
        return jsonify({'error': str(e)}), 500
@app.route("/containers/<container_name>/ask", methods=['POST'])
def ask_container(container_name):
    try:
        container = client.containers.get(container_name)

        if container.status == "running":
            return jsonify({'message': f'Container {container_name} is already running!'}), 304
        else:
            # 处理容器不在运行状态的情况
            return jsonify({'message': f'Container {container_name} is not running', 'status': container.status}), 200

    except docker.errors.NotFound:
        # 处理容器不存在的情况
        return jsonify({'message': f'Container {container_name} not found'}), 200
    except Exception as e:
        # 处理其他错误
        return jsonify({'error': str(e)}), 304


@app.route("/containers/<container_name>/run", methods=['POST'])
def run_script(container_name):
    try:
        subprocess.run(["chmod", "+x", script_path], check=True)
        result = subprocess.run([script_path, container_name], capture_output=True, text=True, check=True)

        try:
            # 重启容器
            container2 = client.containers.get("ServiceMigration")
            container2.restart()
        except Exception as e:
            # 如果重启容器失败，记录错误但不影响脚本执行结果
            app.logger.error('Error restarting container: %s', str(e))

        return jsonify({'stdout': result.stdout, 'stderr': result.stderr, 'return_code': result.returncode}), 200
    except subprocess.CalledProcessError as e:
        return jsonify({'error': 'Script execution failed', 'stderr': e.stderr, 'return_code': e.returncode}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500



if __name__ == "__main__":
    app.run(host='0.0.0.0', port=3375, debug=False)
