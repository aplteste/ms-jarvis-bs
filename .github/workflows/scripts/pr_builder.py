#!/usr/bin/env python3
"""
NestJS Service Generator PR Builder

Creates pull requests for generated NestJS services.
Domain: NestJS Service Generator
"""

import json
import re
import subprocess
import sys
from typing import Dict, Optional


class NestjsGeneratorPRBuilder:
    """Builds and creates pull requests for generated NestJS services."""

    def __init__(
        self,
        target_branch: str,
        pr_branch: str,
        project_name: str,
        project_type: str,
        components: str = "[]",
        healthcheck_components: str = "[]",
        description: Optional[str] = None,
        author: Optional[str] = None,
        with_examples: bool = False,
        generator_name: str = "core-nest-service",
    ):
        """Initialize PR builder with parameters."""
        self.target_branch = target_branch
        self.pr_branch = pr_branch
        self.project_name = project_name
        self.project_type = project_type
        self.components = components
        self.healthcheck_components = healthcheck_components
        self.description = description or ""
        self.author = author or ""
        self.with_examples = with_examples
        self.generator_name = generator_name

    def build_pr_title(self) -> str:
        """Build PR title."""
        return f"feat: generate initial NestJS service structure for {self.project_name}"

    def build_pr_body(self) -> str:
        """Build PR body with all metadata."""
        project_type_capitalized = (
            self.project_type[0].upper() + self.project_type[1:] if self.project_type else ""
        )

        body = f"""This PR generates the initial NestJS microservice structure.

**Project:** `{self.project_name}`
**Generator:** {self.generator_name}
**Mode:** {project_type_capitalized}"""

        # Add description if provided
        if self.description and self.description != "null":
            body += f"\n**Description:** {self.description}"

        # Add author if provided
        if self.author and self.author != "null":
            body += f"\n**Author:** {self.author}"

        # Add components information for custom projects
        if self.project_type == "custom" and self.components != "[]":
            try:
                components_list = json.loads(self.components)
                components_str = ", ".join(components_list) if components_list else "none"
            except (json.JSONDecodeError, TypeError):
                components_str = "none"

            body += f"\n\n**Enabled Components:** {components_str}"

            if self.with_examples:
                body += "\n**With Examples:** Enabled"

            if self.healthcheck_components != "[]" and self.healthcheck_components:
                try:
                    healthcheck_list = json.loads(self.healthcheck_components)
                    healthcheck_str = ", ".join(healthcheck_list) if healthcheck_list else "none"
                except (json.JSONDecodeError, TypeError):
                    healthcheck_str = "none"
                body += f"\n**Health Check Components:** {healthcheck_str}"

        body += "\n\nAfter merging, the team can iterate on the service based on their specific needs."

        return body

    def check_existing_pr(self) -> Optional[str]:
        """Check if PR already exists for this branch."""
        try:
            result = subprocess.run(
                [
                    "gh",
                    "pr",
                    "list",
                    "--head",
                    self.pr_branch,
                    "--base",
                    self.target_branch,
                    "--json",
                    "url",
                    "--jq",
                    ".[0].url // empty",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            existing_pr = result.stdout.strip()
            return existing_pr if existing_pr else None
        except subprocess.CalledProcessError as e:
            self._error(f"Failed to check for existing PR: {e}")
            return None

    def create_pr(self) -> Dict[str, str]:
        """Create pull request and return URL and number."""
        # Check if PR already exists
        existing_pr = self.check_existing_pr()
        if existing_pr:
            print(f"::notice::Pull request already exists: {existing_pr}")
            pr_number = self._extract_pr_number(existing_pr)
            return {"pr_url": existing_pr, "pr_number": pr_number}

        pr_title = self.build_pr_title()
        pr_body = self.build_pr_body()

        # Try creating PR with labels first
        try:
            result = subprocess.run(
                [
                    "gh",
                    "pr",
                    "create",
                    "--title",
                    pr_title,
                    "--body",
                    pr_body,
                    "--base",
                    self.target_branch,
                    "--head",
                    self.pr_branch,
                    "--label",
                    "automated",
                    "--label",
                    "generator",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            pr_url = result.stdout.strip()
        except subprocess.CalledProcessError:
            # If labels don't exist, try without them
            try:
                result = subprocess.run(
                    [
                        "gh",
                        "pr",
                        "create",
                        "--title",
                        pr_title,
                        "--body",
                        pr_body,
                        "--base",
                        self.target_branch,
                        "--head",
                        self.pr_branch,
                    ],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                pr_url = result.stdout.strip()
            except subprocess.CalledProcessError as e:
                self._error(f"Failed to create PR: {e}")
                if e.stdout:
                    print(e.stdout)
                if e.stderr:
                    print(e.stderr, file=sys.stderr)
                sys.exit(1)

        pr_number = self._extract_pr_number(pr_url)
        return {"pr_url": pr_url, "pr_number": pr_number}

    @staticmethod
    def _extract_pr_number(pr_url: str) -> str:
        """Extract PR number from URL."""
        match = re.search(r"/(\d+)$", pr_url)
        return match.group(1) if match else ""

    @staticmethod
    def _error(message: str) -> None:
        """Print error message in GitHub Actions format."""
        print(f"::error::{message}", file=sys.stderr)


def main():
    """Main entry point for CLI usage."""
    import argparse

    parser = argparse.ArgumentParser(description="Create PR for NestJS generator")
    parser.add_argument("--target-branch", required=True, help="Target branch")
    parser.add_argument("--pr-branch", required=True, help="PR branch")
    parser.add_argument("--project-name", required=True, help="Project name")
    parser.add_argument("--project-type", required=True, help="Project type")
    parser.add_argument("--components", default="[]", help="Components JSON array")
    parser.add_argument(
        "--healthcheck-components", default="[]", help="Healthcheck components JSON array"
    )
    parser.add_argument("--description", help="Description")
    parser.add_argument("--author", help="Author")
    parser.add_argument("--with-examples", action="store_true", help="Enable examples")
    parser.add_argument("--generator-name", default="core-nest-service", help="Generator name")
    parser.add_argument("--output-format", choices=["json", "github"], default="github")

    args = parser.parse_args()

    pr_builder = NestjsGeneratorPRBuilder(
        target_branch=args.target_branch,
        pr_branch=args.pr_branch,
        project_name=args.project_name,
        project_type=args.project_type,
        components=args.components,
        healthcheck_components=args.healthcheck_components,
        description=args.description,
        author=args.author,
        with_examples=args.with_examples,
        generator_name=args.generator_name,
    )

    result = pr_builder.create_pr()

    if args.output_format == "github":
        # Output in GitHub Actions format
        print(f"pr_url={result['pr_url']}")
        print(f"pr_number={result['pr_number']}")
        # Also output summary
        print(f"\n### Pull Request Created")
        print(f"[{result['pr_url']}]({result['pr_url']})")
    else:
        # Output as JSON
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
