#!/usr/bin/env python3
"""
NestJS Service Generator Input Validator

Validates and parses inputs for NestJS service generator workflow.
Domain: NestJS Service Generator
"""

import json
import re
import sys
from datetime import datetime
from typing import Dict, List, Optional


class NestjsGeneratorValidator:
    """Validates and parses inputs for NestJS generator workflow."""

    VALID_COMPONENTS = ["kafka", "orm", "grpc", "gql", "redis", "swagger", "gotDummy"]
    VALID_HEALTHCHECK = ["kafka", "database", "redis"]

    # Component mappings: Backstage field → Generator component name
    COMPONENT_MAPPINGS = {
        "kafka_enabled": "kafka",
        "redis_enabled": "redis",
        "postgresql_enabled": "orm",
        "grpc_enabled": "grpc",
        "got_enabled": "gotDummy",
    }

    # Service type mappings: Backstage value → Generator component name
    SERVICE_TYPE_MAPPINGS = {
        "graphql": "gql",
        "rest": "swagger",
    }

    # Healthcheck mappings: Backstage field → Generator healthcheck name
    HEALTHCHECK_MAPPINGS = {
        "kafka_health": "kafka",
        "redis_health": "redis",
        "postgresql_health": "database",
    }

    def __init__(
        self,
        project_name: str,
        execution_id: Optional[str] = None,
        args: str = "{}",
        target_branch: str = "",
        description: Optional[str] = None,
        author: Optional[str] = None,
        with_examples: bool = False,
        target_org: str = "yaperos",
    ):
        """Initialize validator with input parameters."""
        self.project_name = project_name
        self.execution_id = execution_id
        self.args = args
        self.target_branch = target_branch
        self.description = description or ""
        self.author = author or ""
        self.with_examples = with_examples
        self.target_org = target_org

    def validate_project_name(self) -> None:
        """Validate project name format (kebab-case starting with lowercase letter)."""
        if not self.project_name or self.project_name == "null":
            self._error("Project name is required")
            sys.exit(1)

        if not re.match(r"^[a-z][a-z0-9-]*$", self.project_name):
            self._error(
                "Project name must be kebab-case starting with a lowercase letter (e.g., my-service)"
            )
            sys.exit(1)

    def validate_target_branch(self) -> None:
        """Validate target branch is provided."""
        if not self.target_branch or self.target_branch == "null":
            self._error("Target branch is required")
            sys.exit(1)

    def _parse_components_from_object(self, obj: Dict) -> List[str]:
        """Parse components from Backstage object format to generator component list."""
        components = []

        # Check component mappings (kafka_enabled, redis_enabled, etc.)
        for backstage_field, generator_component in self.COMPONENT_MAPPINGS.items():
            if obj.get(backstage_field) is True:
                components.append(generator_component)

        # Handle service_type field (maps to "gql" or "swagger")
        service_type = obj.get("service_type")
        if service_type and service_type in self.SERVICE_TYPE_MAPPINGS:
            components.append(self.SERVICE_TYPE_MAPPINGS[service_type])

        return components

    def _parse_healthcheck_from_object(self, obj: Dict) -> List[str]:
        """Parse healthcheck components from Backstage object format to generator healthcheck list."""
        healthchecks = []

        # Check healthcheck mappings (kafka_health, redis_health, etc.)
        for backstage_field, generator_healthcheck in self.HEALTHCHECK_MAPPINGS.items():
            if obj.get(backstage_field) is True:
                healthchecks.append(generator_healthcheck)

        return healthchecks

    def _parse_combined_args(self, args_json: str) -> tuple[List[str], List[str]]:
        """Parse combined args JSON to extract components and healthchecks."""
        args_input = args_json.strip()
        if (
            not args_input
            or args_input == "null"
            or args_input == "{}"
        ):
            return [], []

        # Parse JSON format
        try:
            parsed = json.loads(args_input)
        except json.JSONDecodeError:
            self._error(f"Invalid JSON format for args: {args_input}")
            sys.exit(1)

        # Expect object format
        if not isinstance(parsed, dict):
            self._error(f"Invalid JSON format for args: expected object, got {type(parsed).__name__}")
            sys.exit(1)

        # Extract components and healthchecks from combined object
        components = self._parse_components_from_object(parsed)
        healthchecks = self._parse_healthcheck_from_object(parsed)

        # Validate component names
        for comp in components:
            if comp not in self.VALID_COMPONENTS:
                valid_list = ", ".join(self.VALID_COMPONENTS)
                self._error(
                    f"Invalid component: {comp}. Valid components are: {valid_list}"
                )
                sys.exit(1)

        # Validate healthcheck component names
        for hc in healthchecks:
            if hc not in self.VALID_HEALTHCHECK:
                valid_list = ", ".join(self.VALID_HEALTHCHECK)
                self._error(
                    f"Invalid healthcheck component: {hc}. Valid healthcheck components are: {valid_list}"
                )
                sys.exit(1)

        return components, healthchecks

    def parse_components(self) -> tuple[str, str]:
        """Parse and validate components JSON object."""
        components_input = self.components.strip()
        if (
            not components_input
            or components_input == "null"
            or components_input == "[]"
        ):
            return "[]", "standard"

        # Parse JSON format
        try:
            parsed = json.loads(components_input)
        except json.JSONDecodeError:
            self._error(f"Invalid JSON format for components: {components_input}")
            sys.exit(1)

        # Expect object format
        if not isinstance(parsed, dict):
            self._error(f"Invalid JSON format for components: expected object, got {type(parsed).__name__}")
            sys.exit(1)

        # Parse object format and convert to array
        components_array = self._parse_components_from_object(parsed)

        # Validate component names
        for comp in components_array:
            if comp not in self.VALID_COMPONENTS:
                valid_list = ", ".join(self.VALID_COMPONENTS)
                self._error(
                    f"Invalid component: {comp}. Valid components are: {valid_list}"
                )
                sys.exit(1)

        # Return as JSON array string
        return json.dumps(components_array), "custom"

    def parse_healthcheck_components(self) -> str:
        """Parse and validate healthcheck components JSON object."""
        healthcheck_input = self.healthcheck_components.strip()
        if (
            not healthcheck_input
            or healthcheck_input == "null"
            or healthcheck_input == "[]"
        ):
            return "[]"

        # Parse JSON format
        try:
            parsed = json.loads(healthcheck_input)
        except json.JSONDecodeError:
            self._error(
                f"Invalid JSON format for healthcheck_components: {healthcheck_input}"
            )
            sys.exit(1)

        # Expect object format
        if not isinstance(parsed, dict):
            self._error(f"Invalid JSON format for healthcheck_components: expected object, got {type(parsed).__name__}")
            sys.exit(1)

        # Parse object format and convert to array
        healthcheck_array = self._parse_healthcheck_from_object(parsed)

        # Validate healthcheck component names
        for hc in healthcheck_array:
            if hc not in self.VALID_HEALTHCHECK:
                valid_list = ", ".join(self.VALID_HEALTHCHECK)
                self._error(
                    f"Invalid healthcheck component: {hc}. Valid healthcheck components are: {valid_list}"
                )
                sys.exit(1)

        # Return as JSON array string
        return json.dumps(healthcheck_array)

    def generate_pr_branch(self) -> str:
        """Generate PR branch name from execution_id or timestamp."""
        if self.execution_id and self.execution_id != "null" and self.execution_id:
            # Sanitize execution_id for branch name
            sanitized_id = re.sub(r"[^a-zA-Z0-9_-]", "-", self.execution_id)
            sanitized_id = sanitized_id.lower()
            # Ensure it doesn't start with a hyphen or dot (Git restriction)
            sanitized_id = re.sub(r"^[.-]+", "", sanitized_id)
            return f"generator/{self.project_name}_{sanitized_id}"
        else:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            return f"generator/{self.project_name}_{timestamp}"

    def parse_optional_fields(self) -> tuple[str, str, str]:
        """Parse optional metadata fields."""
        description = self.description if self.description and self.description != "null" else ""
        author = self.author if self.author and self.author != "null" else ""
        with_examples = "true" if self.with_examples else "false"
        return description, author, with_examples

    def validate_and_parse(self) -> Dict[str, str]:
        """Perform all validation and parsing, return structured output."""
        self.validate_project_name()
        self.validate_target_branch()

        # Always use --args parameter
        args_input = self.args.strip()
        if args_input and args_input != "null" and args_input != "{}":
            components_list, healthcheck_list = self._parse_combined_args(self.args)
            components_array = json.dumps(components_list)
            healthcheck_array = json.dumps(healthcheck_list)
            project_type = "custom" if components_list else "standard"
        else:
            # Empty args = standard project with no components
            components_array = "[]"
            healthcheck_array = "[]"
            project_type = "standard"

        description, author, with_examples = self.parse_optional_fields()
        pr_branch = self.generate_pr_branch()

        return {
            "project_name": self.project_name,
            "target_repo": f"{self.target_org}/{self.project_name}",
            "target_branch": self.target_branch,
            "pr_branch": pr_branch,
            "project_type": project_type,
            "components": components_array,
            "healthcheck_components": healthcheck_array,
            "description": description,
            "author": author,
            "with_examples": with_examples,
        }

    def build_summary_markdown(self, parsed_data: Dict[str, str], generator_name: str) -> str:
        """Build GitHub Actions step summary markdown."""
        lines = [
            "### Configuration",
            "| Setting | Value |",
            "|---------|-------|",
            f"| Generator | `{generator_name}` |",
            f"| Target Org | `{self.target_org}` |",
            f"| Project | `{parsed_data['project_name']}` |",
            f"| Project Type | `{parsed_data['project_type']}` |",
            f"| Target Branch | `{parsed_data['target_branch']}` |",
            f"| PR Branch | `{parsed_data['pr_branch']}` |",
        ]

        if parsed_data["project_type"] == "custom":
            try:
                components_list = json.loads(parsed_data["components"])
                components_str = ", ".join(components_list) if components_list else "none"
            except (json.JSONDecodeError, TypeError):
                components_str = "none"
            lines.append(f"| Enabled Components | `{components_str}` |")

            if parsed_data["healthcheck_components"] != "[]":
                try:
                    healthcheck_list = json.loads(parsed_data["healthcheck_components"])
                    healthcheck_str = ", ".join(healthcheck_list) if healthcheck_list else "none"
                except (json.JSONDecodeError, TypeError):
                    healthcheck_str = "none"
                lines.append(f"| Health Check Components | `{healthcheck_str}` |")

            if parsed_data["with_examples"] == "true":
                lines.append("| With Examples | `true` |")

        if parsed_data["description"]:
            lines.append(f"| Description | `{parsed_data['description']}` |")

        if parsed_data["author"]:
            lines.append(f"| Author | `{parsed_data['author']}` |")

        return "\n".join(lines)

    @staticmethod
    def _error(message: str) -> None:
        """Print error message in GitHub Actions format."""
        print(f"::error::{message}", file=sys.stderr)


def main():
    """Main entry point for CLI usage."""
    import argparse

    parser = argparse.ArgumentParser(description="Validate NestJS generator inputs")
    parser.add_argument("--project-name", required=True, help="Project name")
    parser.add_argument("--execution-id", help="Execution ID")
    parser.add_argument(
        "--args", default="{}", help="Combined JSON object with component and healthcheck flags"
    )
    parser.add_argument("--target-branch", required=True, help="Target branch")
    parser.add_argument("--description", help="Description")
    parser.add_argument("--author", help="Author")
    parser.add_argument("--with-examples", action="store_true", help="Enable examples")
    parser.add_argument("--target-org", default="yaperos", help="Target organization")
    parser.add_argument("--generator-name", default="core-nest-service", help="Generator name")
    parser.add_argument("--output-format", choices=["json", "github"], default="json")

    args = parser.parse_args()

    validator = NestjsGeneratorValidator(
        project_name=args.project_name,
        execution_id=args.execution_id,
        args=args.args,
        target_branch=args.target_branch,
        description=args.description,
        author=args.author,
        with_examples=args.with_examples,
        target_org=args.target_org,
    )

    parsed_data = validator.validate_and_parse()

    if args.output_format == "github":
        # Output in GitHub Actions format
        for key, value in parsed_data.items():
            print(f"{key}={value}")
        # Also output summary
        summary = validator.build_summary_markdown(parsed_data, args.generator_name)
        print(f"\n{summary}")
    else:
        # Output as JSON
        print(json.dumps(parsed_data, indent=2))


if __name__ == "__main__":
    main()
