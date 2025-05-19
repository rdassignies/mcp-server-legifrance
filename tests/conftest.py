import pytest
import subprocess
import time
import threading

DOCKER_IMAGE_NAME = "test-mcp-server-legifrance"


@pytest.fixture()
def server():
    """
    Starts the application server for each test function.
    Ensures clean shutdown of the Docker container after the test.
    """
    container_name = f"mcp-test-{int(time.time())}"

    try:
        container_process = subprocess.run(
            ["docker", "run", "-d", "--rm", "--name", container_name, "-p", "0:8000", DOCKER_IMAGE_NAME],
            capture_output=True,
            text=True,
            check=True
        )

        container_id = container_process.stdout.strip()
        print(f"Started container: {container_name} (ID: {container_id})")

        port_process = subprocess.run(
            ["docker", "port", container_name, "8000"],
            capture_output=True,
            text=True,
            check=True
        )
        # Extract port from output (format: 0.0.0.0:XXXXX)
        host_port = port_process.stdout.strip().split(":")[-1]

        time.sleep(2)
    except subprocess.CalledProcessError as e:
        print(f"Error starting container: {e}")
        print(f"Error output: {e.stderr}")
        raise

    def cleanup_container():
        time.sleep(10)
        try:
            result = subprocess.run(
                ["docker", "ps", "-q", "--filter", f"name={container_name}"],
                capture_output=True,
                text=True,
                check=True
            )
            if result.stdout.strip():
                subprocess.run(
                    ["docker", "kill", container_name],
                    capture_output=True,
                    check=False
                )
                print(f"Killed hanging container: {container_name}")
        except Exception as e:
            print(f"Error in cleanup thread: {e}")

    cleanup_thread = threading.Thread(target=cleanup_container, daemon=True)
    cleanup_thread.start()

    yield {"container_id": container_id, "container_name": container_name, "url": f"http://localhost:{host_port}"}

    try:
        subprocess.run(
            ["docker", "kill", container_name],
            capture_output=True,
            check=False
        )
        print(f"Stopped container: {container_name}")
    except Exception as e:
        print(f"Error during container cleanup: {e}")
