#!/usr/bin/env python3
"""
NestJS Service Generator Runner

Executes Yeoman generator for NestJS service generation.
Domain: NestJS Service Generator
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional


class NestjsGeneratorRunner:
    """Executes Yeoman generator for NestJS generation."""

    COMPONENT_MAP = {
        "kafka": "--kafka",
        "orm": "--orm",
        "grpc": "--grpc",
        "gql": "--gql",
        "redis": "--redis",
        "swagger": "--swagger",
        "gotDummy": "--got",
    }

    def __init__(
        self,
        generator_name: str = "core-nest-service",
        project_name: str = "",
        project_type: str = "standard",
        components: str = "[]",
        healthcheck_components: str = "[]",
        description: Optional[str] = None,
        author: Optional[str] = None,
        with_examples: bool = False,
        output_dir: str = "/tmp/generator-output",
    ):
        """Initialize runner with parameters."""
        self.generator_name = generator_name
        self.project_name = project_name
        self.project_type = project_type
        self.components = components
        self.healthcheck_components = healthcheck_components
        self.description = description or ""
        self.author = author or ""
        self.with_examples = with_examples
        self.output_dir = output_dir

    def build_cli_command(self) -> List[str]:
        """Build CLI command array for Yeoman generator."""
        cmd = [
            "yo",
            self.generator_name,
            "--headless",
            "--project-type",
            self.project_type,
            "--name",
            self.project_name,
            "--skip-install",
        ]

        # Add component flags for custom mode
        if self.project_type == "custom":
            if self.components != "[]":
                try:
                    components_list = json.loads(self.components)
                    for comp in components_list:
                        if comp in self.COMPONENT_MAP:
                            cmd.append(self.COMPONENT_MAP[comp])
                except (json.JSONDecodeError, TypeError) as e:
                    self._error(f"Failed to parse components JSON: {e}")
                    sys.exit(1)

            # Add health check flags if healthcheck components are provided
            if self.healthcheck_components != "[]" and self.healthcheck_components:
                cmd.append("--customize-health-check")
                try:
                    healthcheck_list = json.loads(self.healthcheck_components)
                    if healthcheck_list:
                        healthcheck_str = ",".join(healthcheck_list)
                        cmd.extend(["--health-check", healthcheck_str])
                except (json.JSONDecodeError, TypeError) as e:
                    self._error(f"Failed to parse healthcheck components JSON: {e}")
                    sys.exit(1)

            # Add with-examples flag if explicitly enabled
            if self.with_examples:
                cmd.append("--with-examples")

        # Add description flag only if provided and not empty
        if self.description and self.description != "null":
            cmd.extend(["--description", self.description])

        # Add author flag only if provided and not empty
        if self.author and self.author != "null":
            cmd.extend(["--author", self.author])

        return cmd

    def execute(self) -> str:
        """Execute the generator and return path to generated directory."""
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
        original_cwd = os.getcwd()
        
        try:
            os.chdir(self.output_dir)
            
            cmd = self.build_cli_command()
            
            # Log the complete CLI command for debugging
            print(f"::notice::Executing CLI command: {' '.join(cmd)}")
            
            # Execute the command
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
            )
            
            # Print stdout and stderr for visibility
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
            
        except subprocess.CalledProcessError as e:
            self._error(f"Generator execution failed: {e}")
            if e.stdout:
                print(e.stdout)
            if e.stderr:
                print(e.stderr, file=sys.stderr)
            sys.exit(1)
        finally:
            os.chdir(original_cwd)

        # Validate generated output
        generated_dir = os.path.join(self.output_dir, f"{self.project_name}")
        if not os.path.isdir(generated_dir):
            self._error(f"Generated directory not found: {generated_dir}")
            # List contents for debugging
            if os.path.exists(self.output_dir):
                print("Contents of output directory:")
                for item in os.listdir(self.output_dir):
                    print(f"  {item}")
            sys.exit(1)

        return generated_dir

    @staticmethod
    def _error(message: str) -> None:
        """Print error message in GitHub Actions format."""
        print(f"::error::{message}", file=sys.stderr)


def main():
    """Main entry point for CLI usage."""
    import argparse

    parser = argparse.ArgumentParser(description="Run NestJS generator")
    parser.add_argument("--generator-name", default="core-nest-service", help="Generator name")
    parser.add_argument("--project-name", required=True, help="Project name")
    parser.add_argument("--project-type", required=True, help="Project type (standard/custom)")
    parser.add_argument("--components", default="[]", help="Components JSON array")
    parser.add_argument(
        "--healthcheck-components", default="[]", help="Healthcheck components JSON array"
    )
    parser.add_argument("--description", help="Description")
    parser.add_argument("--author", help="Author")
    parser.add_argument("--with-examples", action="store_true", help="Enable examples")
    parser.add_argument("--output-dir", default="/tmp/generator-output", help="Output directory")

    args = parser.parse_args()

    runner = NestjsGeneratorRunner(
        generator_name=args.generator_name,
        project_name=args.project_name,
        project_type=args.project_type,
        components=args.components,
        healthcheck_components=args.healthcheck_components,
        description=args.description,
        author=args.author,
        with_examples=args.with_examples,
        output_dir=args.output_dir,
    )

    generated_dir = runner.execute()
    print(f"generated_dir={generated_dir}")


if __name__ == "__main__":
    main()
