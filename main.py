from docker_checker import DockerChecker
from gui import SubtitleTranslatorGUI

if __name__ == "__main__":
    docker_checker = DockerChecker()
    docker_checker.check_docker(required_containers=["lingva-translate"])  # Check Docker and containers
    docker_checker.wait_for_container("lingva-translate")
    docker_checker.wait_for_service("http://localhost:3000/api")
    SubtitleTranslatorGUI.run()  # Run the GUI if Docker and containers are available