from flask import Flask, jsonify
from flask import request
import docker
import subprocess

app = Flask(__name__)
client = docker.DockerClient(base_url='unix://var/run/docker.sock')

script_path = "/home/admin/piskes_file/docker_run/docker_run.sh"

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
        container = client.containers.get(container_name)
        
        # 检查容器是否已经在运行
        if container.status == "running":
            return jsonify({'message': f'Container {container_name} is already running!'}), 304
        
        # 定义目标主机的相关信息
        # 获取JSON数据
        data = request.get_json()
        if not data or 'target_host' not in data:
            return jsonify({'error': 'Missing target_host in request data'}), 400
        
        target_host = data['target_host']

        target_username = "admin"
        target_password = "123"
        target_path = "/home/admin/piskes_file"
        local_path = "/home/admin/piskes_file"
        
        # 将文件复制到目标主机
        if copy_file_to_remote(target_host, target_username, target_password, local_path, target_path):
            return jsonify({'message': 'File copied successfully!'}), 204
        else:
            return jsonify({'error': 'Failed to copy file'}), 500

    except Exception as e:220
        return jsonify({'error': str(e)}), 500


@app.route("/containers/<container_name>/run", methods=['POST'])
def run_script(container_name):
    try:
        # 确保脚本是可执行的
        subprocess.run(["chmod", "+x", script_path], check=True)
        
        # 运行脚本
        result = subprocess.run([script_path, container_name], capture_output=True, text=True, check=True)
        return jsonify({'stdout': result.stdout, 'stderr': result.stderr, 'return_code': result.returncode}), 200
    except subprocess.CalledProcessError as e:
        return jsonify({'error': 'Script execution failed', 'stderr': e.stderr, 'return_code': e.returncode}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=3375)
