from flask import Flask, jsonify
from flask import request
import docker
import subprocess
import paramiko
import os
import configparser

app = Flask(__name__)
client = docker.DockerClient(base_url='unix://var/run/docker.sock')


script_path = "/home/admin/piskes_file/docker_run/docker_run.sh"
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
        container = client.containers.get(container_name)

        if container.status == "running":
            return jsonify({'message': f'Container {container_name} is already running!'}), 304

        data = request.get_json()
        if not data or 'KeyServerDomain' not in data:
            return jsonify({'error': 'Missing KeyServerDomain in request data'}), 500
        
        config_path = '/home/admin/piskes_file/piskes/config/config.ini'
        config = CasePreservingConfigParser()
        config.read(config_path)

        # 确保 'addr' 部分存在
        if 'addr' not in config.sections():
            config.add_section('addr')
        
        # 不改变大小写地更新 'KeyServerDomain'
        config.set('addr', 'KeyServerDomain', f'"{data["KeyServerDomain"]}"')

        # 将修改写回 config 文件
        with open(config_path, 'w') as configfile:
            config.write(configfile)

        return jsonify({'message': 'KeyServerDomain updated successfully!'}), 204

    except Exception as e:
        app.logger.error('Error in start_container: %s', str(e))
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
    app.run(host='0.0.0.0', port=3375, debug=False)
