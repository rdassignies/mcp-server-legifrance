from mcp import StdioServerParameters
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

    server_params = StdioServerParameters(
        command="docker",
        args=[
            "run", "-i", "--rm", "--name", container_name,
            DOCKER_IMAGE_NAME,
        ],
    )

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

    yield server_params

    try:
        subprocess.run(
            ["docker", "kill", container_name],
            capture_output=True,
            check=False
        )
        print(f"Stopped container: {container_name}")
    except Exception as e:
        print(f"Error during container cleanup: {e}")
