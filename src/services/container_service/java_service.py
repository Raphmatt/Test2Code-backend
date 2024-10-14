from typing import Dict, Any, Tuple
from .base import ContainerService
import re

class JavaContainerService(ContainerService):
    SUPPORTED_VERSIONS = ["8", "11", "17"]

    def __init__(self, version: str = "17", dependencies: Dict[str, str] = None):
        super().__init__(version)
        if not self.version:
            self.version = "17"  # default to 17 if version is None

        if self.version not in self.SUPPORTED_VERSIONS:
            raise ValueError(
                f"Unsupported Java version: {self.version}. Supported versions are: {', '.join(self.SUPPORTED_VERSIONS)}"
            )

        # Default dependencies if none are provided (e.g., JUnit for testing)
        self.dependencies = dependencies or {"junit": "4.12", "hamcrest-core": "1.3"}

    @classmethod
    def get_supported_versions(cls):
        return cls.SUPPORTED_VERSIONS

    def get_dockerfile_content(self, filename: str) -> str:
        """
        Get the content of the Dockerfile for Java code.
        :param filename: Filename of the Java file.
        :return: Content of the Dockerfile.
        """
        java_version = self.version

        return f"""
            FROM openjdk:{java_version}
            WORKDIR /app
            COPY . /app
            RUN mvn clean install
            """

    def get_pom_content(self) -> str:
        """
        Generate a basic pom.xml with dependencies for the Java project.
        :return: pom.xml content as a string.
        """
        dependencies_xml = "\n".join([
            f"""
            <dependency>
                <groupId>{group_id}</groupId>
                <artifactId>{artifact_id}</artifactId>
                <version>{version}</version>
                <scope>test</scope>
            </dependency>
            """
            for (group_id, artifact_id), version in {
                ("junit", "junit"): self.dependencies["junit"],
                ("org.hamcrest", "hamcrest-core"): self.dependencies["hamcrest-core"]
            }.items()
        ])

        return f"""
        <project xmlns="http://maven.apache.org/POM/4.0.0"
                 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                 xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
            <modelVersion>4.0.0</modelVersion>

            <groupId>com.example</groupId>
            <artifactId>example-project</artifactId>
            <version>1.0-SNAPSHOT</version>

            <properties>
                <maven.compiler.source>{self.version}</maven.compiler.source>
                <maven.compiler.target>{self.version}</maven.compiler.target>
            </properties>

            <dependencies>
                {dependencies_xml}
            </dependencies>

            <build>
                <plugins>
                    <plugin>
                        <groupId>org.apache.maven.plugins</groupId>
                        <artifactId>maven-surefire-plugin</artifactId>
                        <version>2.22.2</version>
                    </plugin>
                </plugins>
            </build>
        </project>
        """

    def get_run_command(self, filename: str) -> str:
        """
        Get the command to run the Java code in a Docker container.
        :param filename: Filename of the Java code.
        :return: Command to run the Java code.
        """
        # Run the Maven tests and copy the JUnit XML report to /app/test_results.xml
        return "mvn test && cp target/surefire-reports/*.xml /app/test_results.xml"

    def get_file_extension(self) -> str:
        """
        Get file extension for Java code.
        :return: File extension.
        """
        return "java"

    def validate_test_code(self, test_code: str) -> Tuple[bool, str]:
        """
        Validate Java test code and check if there's at least one test function annotated with @Test.
        :param test_code: Java test code.
        :return: Tuple of boolean and error message.
        """
        if not re.search(r'@Test', test_code):
            return False, "No test functions found. Test methods must be annotated with @Test."

        return True, ""

    def run_code_in_container(self, code: str, test_code: str) -> Dict[str, Any]:
        """
        Run Java code in a Docker container.
        :param code: Java code.
        :param test_code: Java test code.
        :return: Dictionary containing test results, build time, run time, and total time.
        """
        # Validate test code
        if test_code:
            is_valid, error_msg = self.validate_test_code(test_code)
            if not is_valid:
                return {"error": f"Invalid test code. {error_msg}"}

        # Ensure parent class run_code_in_container method doesn't return None
        try:
            result = super().run_code_in_container(code, test_code)
            if result is None:
                return {"error": "Unexpected error: the container result is None."}

            # Check if result is a dictionary and contains expected keys
            if not isinstance(result, dict):
                return {"error": f"Unexpected error: result is not a dictionary, got {type(result)} instead."}

            # You can handle more specific cases depending on your logic
            return result

        except Exception as e:
            return {"error": f"An unexpected error occurred: {str(e)}"}
