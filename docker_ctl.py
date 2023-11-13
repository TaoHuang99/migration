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
        
        # 更新config.ini文件
        config_path = '/home/admin/piskes_file/piskes/config/config.ini'
        # 读取整个配置文件到内存
        try:
            with open(config_path, 'r') as file:
                config_lines = file.readlines()
        except IOError as e:
            return jsonify({'error': str(e)}), 500
        
        # 更新KeyServerDomain的值，同时保留引号
        key_server_domain_pattern = re.compile(r'^(\s*KeyServerDomain\s*=\s*")(.*?)(")$', re.IGNORECASE)
        key_found = False
        for i, line in enumerate(config_lines):
            match = key_server_domain_pattern.match(line)
            if match:
                # 保留匹配到的前引号和后引号
                config_lines[i] = f'{match.group(1)}{data["KeyServerDomain"]}{match.group(3)}\n'
                key_found = True
                break
        
        if not key_found:
            return jsonify({'error': 'KeyServerDomain not found in the config file'}), 500
        
        # 写回配置文件
        try:
            with open(config_path, 'w') as file:
                file.writelines(config_lines)
        except IOError as e:
            return jsonify({'error': str(e)}), 500
        
        return jsonify({'message': 'KeyServerDomain updated successfully'}), 204

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
