from flask import Flask, jsonify
from flask import request
import docker
import subprocess
import paramiko
import os
import logging

# 配置日志记录
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

# 设置文件夹权限
path = "/home/admin/piskes_file"
os.chmod(path, 0o777)

# 初始化 Flask 和 Docker 客户端
app = Flask(__name__)
client = docker.DockerClient(base_url='unix://var/run/docker.sock')

# 定义文件复制函数
def copy_file_to_remote(target_host, target_username, target_password, local_path, target_path):
    try:
        logger.debug("Creating SSH client...")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(target_host, username=target_username, password=target_password)
        
        logger.debug("Opening SFTP session...")
        sftp = ssh.open_sftp()
        logger.debug("Copying files...")
        _copy_folder_recursive(local_path, target_path, sftp)
        
        logger.debug("Setting permissions...")
        stdin, stdout, stderr = ssh.exec_command(f"chmod -R 777 {target_path}")
        stderr = stderr.read().decode()
        if stderr:
            logger.error("Failed to set permissions: %s", stderr)
            return False, f"Failed to set permissions on remote path: {stderr}"
        
        logger.info("File copied and permissions set successfully!")
        sftp.close()
        ssh.close()
        return True, "File copied and permissions set successfully!"
    except Exception as e:
        logger.error("Failed to copy file: %s", str(e))
        return False, str(e)

def _copy_folder_recursive(local_path, target_path, sftp):
    if os.path.isfile(local_path):
        sftp.put(local_path, target_path)
    elif os.path.isdir(local_path):
        try:
            sftp.mkdir(target_path)
        except:
            pass  # 忽略错误，如果文件夹已存在
        for item in os.listdir(local_path):
            local_item = os.path.join(local_path, item)
            target_item = os.path.join(target_path, item)
            _copy_folder_recursive(local_item, target_item, sftp)

# 设置脚本路径
script_path = "/home/admin/piskes_file/docker_run/docker_run.sh"

# 定义 Flask 路由
@app.route("/containers/<container_name>/stop", methods=['POST'])
def stop_container(container_name):
    try:
        container = client.containers.get(container_name)
        container.stop()
        return jsonify({'message': f'Container {container_name} stopped successfully!'}), 204
    except Exception as e:
        logger.error('Error in stop_container: %s', str(e))
        return jsonify({'error': str(e)}), 500

@app.route("/containers/<container_name>/start", methods=['POST'])
def start_container(container_name):
    try:
        container = client.containers.get(container_name)
        
        if container.status == "running":
            return jsonify({'message': f'Container {container_name} is already running!'}), 304
        
        data = request.get_json()
        if not data or 'target_host' not in data:
            return jsonify({'error': 'Missing target_host in request data'}), 400
        
        target_host = data['target_host']
        target_username = "admin"
        target_password = "123"
        target_path = "/home/admin/piskes_file"
        local_path = "/home/admin/piskes_file"
        
        success, message = copy_file_to_remote(target_host, target_username, target_password, local_path, target_path)
        if success:
            return jsonify({'message': message}), 204
        else:
            logger.error('Failed to copy file: %s', message)
            return jsonify({'error': message}), 500

    except Exception as e:
        logger.error('Error in start_container: %s', str(e))
        return jsonify({'error': str(e)}), 500

@app.route("/containers/<container_name>/run", methods=['POST'])
def run_script(container_name):
    try:
        subprocess.run(["chmod", "+x", script_path], check=True)
        result = subprocess.run([script_path, container_name], capture_output=True, text=True, check=True)
        return jsonify({'stdout': result.stdout, 'stderr': result.stderr, 'return_code': result.returncode}), 200
    except subprocess.CalledProcessError as e:
        logger.error('Script execution failed: %s', e.stderr)
        return jsonify({'error': 'Script execution failed', 'stderr': e.stderr, 'return_code': e.returncode}), 500
    except Exception as e:
        logger.error('Error in run_script: %s', str(e))
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=3375, debug=True)
