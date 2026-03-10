#!/usr/bin/env python3
"""
Axzora Autonomous Coding Agent
Mr Happy's coding assistant that can read, write, and execute code
"""

import os
import re
import subprocess
import json
from pathlib import Path
from typing import Optional
import requests
import unicodedata


def strip_emoji(text: str) -> str:
    """Remove emojis from text for Windows compatibility"""
    return text.encode("ascii", "ignore").decode("ascii")


class AutonomousAgent:
    """Autonomous coding agent powered by local LLM"""

    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.model = "llama3.2:3b"
        self.workspace = Path.cwd()
        self.conversation_history = []

    def query_llm(self, prompt: str) -> str:
        """Query local LLM"""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "context": self.conversation_history[-5:],
        }
        try:
            r = requests.post(
                f"{self.ollama_url}/api/generate", json=payload, timeout=120
            )
            if r.status_code == 200:
                response = r.json().get("response", "")
                self.conversation_history.append(prompt)
                return response
            return f"Error: {r.status_code}"
        except Exception as e:
            return f"Connection error: {e}"

    def read_file(self, path: str) -> str:
        """Read a file"""
        try:
            p = Path(path)
            if p.exists():
                content = p.read_text(encoding="utf-8")
                return f"File: {path}\n\n{content}"
            return f"File not found: {path}"
        except Exception as e:
            return f"Error reading {path}: {e}"

    def list_files(self, pattern: str = "*.py") -> str:
        """List files in workspace"""
        try:
            files = list(self.workspace.glob(f"**/{pattern}"))
            return "\n".join([str(f.relative_to(self.workspace)) for f in files[:20]])
        except Exception as e:
            return f"Error: {e}"

    def run_command(self, cmd: str) -> str:
        """Execute shell command"""
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=30
            )
            output = result.stdout if result.stdout else result.stderr
            return f"Exit code: {result.returncode}\n\n{output[:2000]}"
        except subprocess.TimeoutExpired:
            return "Command timed out"
        except Exception as e:
            return f"Error: {e}"

    def write_file(self, path: str, content: str) -> str:
        """Write to a file"""
        try:
            p = Path(path)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
            return f"Written to {path}"
        except Exception as e:
            return f"Error writing {path}: {e}"

    def analyze_task(self, task: str) -> dict:
        """Analyze what needs to be done"""
        task_lower = task.lower()

        if "create" in task_lower or "make" in task_lower or "new" in task_lower:
            return {"action": "create", "target": self._extract_target(task)}
        elif "fix" in task_lower or "bug" in task_lower or "error" in task_lower:
            return {"action": "fix", "target": self._extract_target(task)}
        elif "list" in task_lower and "file" in task_lower:
            pattern = "*.py" if "python" in task_lower else "*"
            return {"action": "list_files", "target": pattern}
        elif "read" in task_lower or "show" in task_lower:
            return {"action": "read", "target": self._extract_target(task)}
        elif "run" in task_lower or "execute" in task_lower or "test" in task_lower:
            return {"action": "run", "target": self._extract_target(task)}
        else:
            return {"action": "help", "target": ""}

    def _extract_target(self, task: str) -> str:
        """Extract target file/command from task"""
        words = task.split()
        # Find any file path
        for w in words[1:]:  # Skip the first word (action)
            if "/" in w or "\\" in w or w.endswith(".py") or w.endswith(".json"):
                return w
        # Default to second word
        if len(words) > 1:
            return words[1]
        return ""

    def execute_task(self, task: str) -> str:
        """Execute a coding task"""
        analysis = self.analyze_task(task)
        action = analysis["action"]
        target = analysis["target"]

        if action == "list_files":
            return self.list_files(target)

        elif action == "read":
            if not target:
                return self.list_files("*.py")
            return self.read_file(target)

        elif action == "run":
            return self.run_command(target)

        elif action == "create":
            prompt = f"""Create a simple Python file called '{target}'.
Task: {task}
Write working, complete code. Just output the code, no explanations."""
            return self.query_llm(prompt)

        elif action == "fix":
            if target and Path(target).exists():
                content = self.read_file(target)
                prompt = f"""Fix bugs in this code:
{content}
Task: {task}
Explain what's wrong and provide fixed code."""
                return self.query_llm(prompt)
            return f"File not found: {target}"

        else:
            prompt = f"""You are Mr Happy, an AI coding assistant.
Task: {task}
Provide helpful guidance."""
            return self.query_llm(prompt)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Axzora Autonomous Agent")
    parser.add_argument("--task", type=str, help="Task to execute")
    parser.add_argument("--model", type=str, default="llama3.2:3b", help="LLM model")
    parser.add_argument("--interactive", action="store_true", help="Interactive mode")

    args = parser.parse_args()

    agent = AutonomousAgent()
    agent.model = args.model

    if args.task:
        result = agent.execute_task(args.task)
        print(f"\nTask: {args.task}")
        print(f"Action: {agent.analyze_task(args.task)}")
        print(f"\n{strip_emoji(result)}")

    elif args.interactive:
        print("\n[Axzora Autonomous Agent - Interactive Mode]")
        print("Type 'quit' to exit\n")

        while True:
            try:
                task = input("Task> ")
                if task.lower() == "quit":
                    break
                if not task.strip():
                    continue

                print(f"\nExecuting: {agent.analyze_task(task)}")
                result = agent.execute_task(task)
                print(strip_emoji(result))
                print()
            except KeyboardInterrupt:
                break

        print("Goodbye!")

    else:
        print("Usage: --task 'list python files' or --interactive")


if __name__ == "__main__":
    main()
