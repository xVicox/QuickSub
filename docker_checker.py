import os
import sys
import time
import subprocess
import platform
import requests

class DockerChecker:

    @staticmethod
    def check_docker(required_containers=None):
        """
        Checks if Docker is installed, running, and (optionally) if specific containers are running.
        If not, displays a message and exits.

        Args:
            required_containers (list): A list of container names that must be running.
        """
        if not DockerChecker.is_docker_installed():
            print("Docker is not installed. Please install Docker and try again.")
            sys.exit(1)

        if not DockerChecker.is_docker_running():
            print("Docker is not running. Attempting to start it...")
            DockerChecker.start_docker()

        if required_containers:
            for container in required_containers:
                if not DockerChecker.is_container_running(container):
                    print(f"Container '{container}' is not running. Attempting to start it...")
                    DockerChecker.start_container(container)

    @staticmethod
    def is_docker_installed():
        """
        Checks if Docker is installed on the system.
        """
        try:
            result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
            return "Docker version" in result.stdout
        except FileNotFoundError:
            return False

    @staticmethod
    def is_docker_running():
        """
        Checks if Docker is running on the system.
        """
        try:
            result = subprocess.run(['docker', 'info'], capture_output=True, text=True)
            return "Server Version" in result.stdout
        except FileNotFoundError:
            return False

    @staticmethod
    def start_docker():
        """
        Attempts to start Docker on different systems and waits for Docker to be fully
        initialized
        """
        system = platform.system()
        try:
            if system == "Windows":
                docker_path = os.path.expandvars(r"%ProgramFiles%\Docker\Docker\Docker Desktop.exe")
                subprocess.Popen(docker_path)  # Launch Docker Desktop
                print("Docker Desktop has been started. Please wait for it to initialize.")
            elif system == "Darwin":
                subprocess.run(["open", "/Applications/Docker.app"], check=True)
            elif system == "Linux":
                subprocess.run(["sudo", "systemctl", "start", "docker"], check=True)
            print("Docker has been started successfully.")
            DockerChecker.wait_for_docker()  # Wait until Docker is fully initialized
        except subprocess.CalledProcessError:
            print("Failed to start Docker. Please start it manually.")
            sys.exit(1)

    @staticmethod
    def wait_for_docker(timeout=60):
        """
        Waits until Docker is fully initialized.
        """
        print("Waiting for Docker to be ready...")
        start_time = time.time()
        while time.time() - start_time < timeout:
            if DockerChecker.is_docker_running():
                print("Docker is ready!")
                return
            time.sleep(2)  # Wait a bit before checking again
        print("Docker failed to start within the timeout period.")
        sys.exit(1)

    @staticmethod
    def is_container_running(container_name):
        """
        Checks if a specific Docker container is running.

        Args:
            container_name (str): The name of the container to check.
        """
        try:
            result = subprocess.run(['docker', 'ps', '--filter', f'name={container_name}', '--format', '{{.Names}}'], capture_output=True, text=True)
            return container_name in result.stdout
        except FileNotFoundError:
            return False

    @staticmethod
    def start_container(container_name):
        """
        Starts a Docker container if it's not already running.
        """
        try:
            result = subprocess.run(['docker', 'start', container_name], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"Container '{container_name}' started successfully.")
            else:
                print(f"Failed to start container '{container_name}': {result.stderr.strip()}")
        except FileNotFoundError:
            print("Docker is not installed or not accessible from the command line.")
            sys.exit(1)

    @staticmethod
    def wait_for_container(container_name, timeout=30):
        """
        Waits until the specified container is fully running.
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            if DockerChecker.is_container_running(container_name):
                print(f"Container '{container_name}' is now running!")
                return
            time.sleep(2)  # Wait a bit before checking again
        print(f"Container '{container_name}' failed to start within the timeout period.")
        sys.exit(1)

    @staticmethod
    def wait_for_service(url, timeout=90):
        """
        Waits for the translation service to become available after starting the container.
        """
        print(f"🔍 Waiting for service at {url} to be ready... (Timeout: {timeout}s)")
        start_time = time.time()
        elapsed_time = 0

        while time.time() - start_time < timeout:
            try:
                response = requests.get(url, timeout=3)
                if response.status_code == 200:
                    print("Translation service is ready!")
                    return True
                else:
                    print(f"Service responded with status {response.status_code}, retrying...")
            except (requests.ConnectionError, requests.Timeout):
                print("Service not ready yet, retrying...")
                elapsed_time += 5
                print(f"Elapsed time: {elapsed_time}")

            time.sleep(5)  # Sleep time before retrying

        print("Service failed to start within the timeout period.")
        return False