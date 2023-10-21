from flask import Flask, jsonify
import docker

app = Flask(__name__)
client = docker.DockerClient(base_url='unix://var/run/docker.sock')

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
        
        container.start()
        return jsonify({'message': f'Container {container_name} started successfully!'}), 204
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=2375)  # 在所有接口上侦听，端口2375

