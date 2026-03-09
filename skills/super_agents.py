"""
AXZORA AI Super Agents - Autonomous AI System
==============================================

A powerful autonomous AI system similar to AutoGPT/Devin.
Agents can: code, browse web, control files, execute commands, and self-improve.

Author: Mr. Happy AI (Digital CEO of Axzora)
License: AXZORA PROPRIETARY
"""

import os
import sys
import json
import time
import subprocess
import requests
import threading
import queue
import re
from datetime import datetime
from typing import Optional, Dict, List, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import traceback

# ============================================================================
# SUPER AGENT CORE
# ============================================================================

class AgentState(Enum):
    IDLE = "idle"
    THINKING = "thinking"
    EXECUTING = "executing"
    WAITING = "waiting"
    ERROR = "error"
    COMPLETE = "complete"

@dataclass
class Task:
    """Represents a task for the super agent"""
    id: str
    description: str
    status: str = "pending"
    priority: int = 1
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    result: Optional[str] = None
    subtasks: List['Task'] = field(default_factory=list)
    
@dataclass
class AgentMemory:
    """Persistent memory for agents"""
    short_term: List[Dict] = field(default_factory=list)
    long_term: List[Dict] = field(default_factory=list)
    context: Dict = field(default_factory=dict)
    
    def remember(self, info: Dict, long_term: bool = False):
        """Store information in memory"""
        info['timestamp'] = datetime.now().isoformat()
        if long_term:
            self.long_term.append(info)
        else:
            self.short_term.append(info)
            # Keep short term memory limited
            if len(self.short_term) > 100:
                self.short_term = self.short_term[-50:]
    
    def recall(self, query: str = None) -> List[Dict]:
        """Retrieve information from memory"""
        if query:
            # Simple keyword search
            results = []
            for item in self.short_term + self.long_term:
                if query.lower() in str(item).lower():
                    results.append(item)
            return results
        return self.short_term + self.long_term

class SuperAgent:
    """
    Base class for autonomous AI agents.
    
    Capabilities:
    - Autonomous task execution
    - Self-coding and improvement
    - Browser automation
    - File system control
    - Command execution
    - API integration
    """
    
    def __init__(
        self,
        name: str,
        role: str,
        ollama_url: str = "http://localhost:11434",
        model: str = "llama3.2:3b",
        workspace: str = None,
        tools: List[str] = None
    ):
        self.name = name
        self.role = role
        self.ollama_url = ollama_url
        self.model = model
        self.workspace = workspace or os.getcwd()
        self.tools = tools or []
        self.state = AgentState.IDLE
        self.memory = AgentMemory()
        self.task_queue = queue.PriorityQueue()
        self.current_task: Optional[Task] = None
        self.history: List[Dict] = []
        self.skills: Dict[str, Callable] = {}
        
        # Register default tools
        self._register_default_tools()
        
    def _register_default_tools(self):
        """Register built-in tools"""
        self.skills.update({
            "think": self._tool_think,
            "code": self._tool_code,
            "browse": self._tool_browse,
            "read_file": self._tool_read_file,
            "write_file": self._tool_write_file,
            "execute": self._tool_execute,
            "search": self._tool_search,
            "api_call": self._tool_api_call,
            "remember": self._tool_remember,
            "recall": self._tool_recall,
            "delegate": self._tool_delegate,
            "verify": self._tool_verify,
        })
    
    # ========================================================================
    # CORE AI FUNCTIONS
    # ========================================================================
    
    def chat(self, message: str, system_prompt: str = None) -> str:
        """Send message to Ollama and get response"""
        if system_prompt is None:
            system_prompt = self._get_system_prompt()
            
        try:
            response = requests.post(
                f"{self.ollama_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": message}
                    ],
                    "stream": False
                },
                timeout=120
            )
            
            if response.status_code == 200:
                return response.json().get("message", {}).get("content", "")
            else:
                return f"Error: {response.status_code} - {response.text}"
                
        except Exception as e:
            return f"Error communicating with Ollama: {str(e)}"
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for this agent"""
        return f"""You are {self.name}, {self.role} in the AXZORA AI ecosystem.

You are an autonomous AI agent with the following capabilities:
- Write and execute code (Python, JavaScript, etc.)
- Browse the web and extract information
- Read and write files
- Execute system commands
- Make API calls
- Remember and recall information
- Delegate tasks to other agents
- Verify and test your work

You have access to these tools:
{', '.join(self.skills.keys())}

You are part of the AXZORA Digital Corporation, led by Mr. Happy AI (Digital CEO).

When given a task:
1. THINK about the best approach
2. BREAK DOWN the task into subtasks
3. EXECUTE each subtask systematically
4. VERIFY your work
5. REPORT results clearly

Always be helpful, efficient, and accurate. Think step by step.

Current workspace: {self.workspace}
Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    # ========================================================================
    # AUTONOMOUS EXECUTION
    # ========================================================================
    
    def add_task(self, description: str, priority: int = 1) -> Task:
        """Add a new task to the queue"""
        task = Task(
            id=f"task_{int(time.time() * 1000)}",
            description=description,
            priority=priority
        )
        self.task_queue.put((priority, task))
        self.memory.remember({"type": "task_added", "task": description})
        return task
    
    def run_autonomous(self, max_iterations: int = 10):
        """Run autonomous task execution loop"""
        iterations = 0
        
        while iterations < max_iterations:
            if self.task_queue.empty():
                self.state = AgentState.IDLE
                break
                
            self.state = AgentState.THINKING
            priority, task = self.task_queue.get()
            self.current_task = task
            
            print(f"\n{'='*60}")
            print(f"[{self.name}] Processing Task: {task.description}")
            print(f"{'='*60}")
            
            try:
                # Step 1: Analyze and plan
                plan = self._plan_task(task)
                
                # Step 2: Execute plan
                self.state = AgentState.EXECUTING
                result = self._execute_plan(task, plan)
                
                # Step 3: Verify and complete
                task.result = result
                task.status = "complete"
                task.completed_at = datetime.now()
                
                self.memory.remember({
                    "type": "task_completed",
                    "task": task.description,
                    "result": result
                }, long_term=True)
                
                print(f"\n[{self.name}] Task Complete!")
                print(f"Result: {result[:200]}..." if len(result) > 200 else f"Result: {result}")
                
            except Exception as e:
                task.status = "error"
                task.result = str(e)
                self.state = AgentState.ERROR
                print(f"\n[{self.name}] Error: {str(e)}")
                traceback.print_exc()
                
            self.history.append({
                "task": task.description,
                "result": task.result,
                "status": task.status,
                "timestamp": datetime.now().isoformat()
            })
            
            iterations += 1
            
        self.state = AgentState.IDLE
        self.current_task = None
        return iterations
    
    def _plan_task(self, task: Task) -> List[Dict]:
        """Create execution plan for a task"""
        planning_prompt = f"""Analyze this task and create a step-by-step execution plan.

TASK: {task.description}

Available tools: {', '.join(self.skills.keys())}

Create a JSON plan with steps. Each step should have:
- "tool": the tool to use
- "params": parameters for the tool
- "purpose": why this step is needed

Respond ONLY with valid JSON array of steps.
Example:
[
  {{"tool": "read_file", "params": {{"path": "example.py"}}, "purpose": "Read existing code"}},
  {{"tool": "code", "params": {{"instruction": "Add error handling"}}, "purpose": "Improve code"}}
]
"""
        
        response = self.chat(planning_prompt)
        
        # Extract JSON from response
        try:
            # Try to find JSON array in response
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                plan = json.loads(json_match.group())
                return plan
        except json.JSONDecodeError:
            pass
            
        # Fallback: create simple plan
        return [{"tool": "think", "params": {"query": task.description}, "purpose": "Analyze task"}]
    
    def _execute_plan(self, task: Task, plan: List[Dict]) -> str:
        """Execute a plan step by step"""
        results = []
        
        for i, step in enumerate(plan):
            tool = step.get("tool", "think")
            params = step.get("params", {})
            purpose = step.get("purpose", "")
            
            print(f"\n  Step {i+1}: {purpose}")
            print(f"  Tool: {tool}")
            
            if tool in self.skills:
                try:
                    result = self.skills[tool](**params)
                    results.append(f"Step {i+1}: {result}")
                    print(f"  Result: {str(result)[:100]}...")
                except Exception as e:
                    results.append(f"Step {i+1} Error: {str(e)}")
                    print(f"  Error: {str(e)}")
            else:
                results.append(f"Step {i+1}: Unknown tool '{tool}'")
                print(f"  Unknown tool: {tool}")
                
        return "\n".join(results)
    
    # ========================================================================
    # BUILT-IN TOOLS
    # ========================================================================
    
    def _tool_think(self, query: str) -> str:
        """Deep thinking and analysis"""
        response = self.chat(f"Think deeply about this and provide analysis:\n\n{query}")
        self.memory.remember({"type": "thought", "query": query, "response": response})
        return response
    
    def _tool_code(self, instruction: str, language: str = "python", save_to: str = None) -> str:
        """Generate code based on instruction"""
        code_prompt = f"""Generate {language} code for the following:

{instruction}

Requirements:
- Write clean, well-documented code
- Include error handling
- Add comments explaining the logic
- Make it production-ready

Respond with ONLY the code, no explanations before or after.
"""
        code = self.chat(code_prompt)
        
        # Extract code block if present
        code_match = re.search(r'```(?:\w+)?\n(.*?)\n```', code, re.DOTALL)
        if code_match:
            code = code_match.group(1)
        
        if save_to:
            filepath = os.path.join(self.workspace, save_to)
            os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else self.workspace, exist_ok=True)
            with open(filepath, 'w') as f:
                f.write(code)
            self.memory.remember({"type": "code_generated", "file": save_to, "instruction": instruction})
            return f"Code saved to {save_to}\n\n{code}"
        
        return code
    
    def _tool_browse(self, url: str, extract: str = None) -> str:
        """Browse web page and extract information"""
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                content = response.text
                
                if extract:
                    # Use AI to extract specific information
                    extraction = self.chat(f"Extract the following from this webpage content:\n\nTarget: {extract}\n\nContent:\n{content[:5000]}")
                    return extraction
                
                return f"Successfully fetched {url}\nContent length: {len(content)} chars"
            else:
                return f"Error: HTTP {response.status_code}"
        except Exception as e:
            return f"Error browsing: {str(e)}"
    
    def _tool_read_file(self, path: str) -> str:
        """Read file contents"""
        try:
            filepath = os.path.join(self.workspace, path) if not os.path.isabs(path) else path
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            self.memory.remember({"type": "file_read", "path": path})
            return f"File: {path}\n\n{content}"
        except Exception as e:
            return f"Error reading file: {str(e)}"
    
    def _tool_write_file(self, path: str, content: str) -> str:
        """Write content to file"""
        try:
            filepath = os.path.join(self.workspace, path) if not os.path.isabs(path) else path
            os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else self.workspace, exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            self.memory.remember({"type": "file_written", "path": path})
            return f"Successfully wrote {len(content)} chars to {path}"
        except Exception as e:
            return f"Error writing file: {str(e)}"
    
    def _tool_execute(self, command: str, timeout: int = 60) -> str:
        """Execute system command"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.workspace
            )
            
            output = result.stdout
            if result.stderr:
                output += f"\nSTDERR: {result.stderr}"
            
            self.memory.remember({
                "type": "command_executed",
                "command": command,
                "exit_code": result.returncode
            })
            
            return f"Command: {command}\nExit Code: {result.returncode}\n\n{output}"
        except subprocess.TimeoutExpired:
            return f"Command timed out after {timeout} seconds"
        except Exception as e:
            return f"Error executing command: {str(e)}"
    
    def _tool_search(self, query: str, source: str = "web") -> str:
        """Search for information"""
        # For now, use AI knowledge for search
        search_prompt = f"""Search and provide information about:

{query}

Provide:
1. Key facts
2. Relevant details
3. Sources if known
4. Related topics
"""
        return self.chat(search_prompt)
    
    def _tool_api_call(self, url: str, method: str = "GET", data: Dict = None, headers: Dict = None) -> str:
        """Make API call"""
        try:
            response = requests.request(
                method=method.upper(),
                url=url,
                json=data,
                headers=headers or {},
                timeout=30
            )
            
            result = {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": response.text[:1000]  # Limit response size
            }
            
            self.memory.remember({
                "type": "api_call",
                "url": url,
                "method": method,
                "status": response.status_code
            })
            
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"API call error: {str(e)}"
    
    def _tool_remember(self, key: str, value: Any, long_term: bool = False) -> str:
        """Store information in memory"""
        self.memory.remember({"key": key, "value": value}, long_term=long_term)
        return f"Remembered: {key}"
    
    def _tool_recall(self, query: str = None) -> str:
        """Recall information from memory"""
        results = self.memory.recall(query)
        return json.dumps(results, indent=2, default=str)
    
    def _tool_delegate(self, agent_name: str, task: str) -> str:
        """Delegate task to another agent"""
        # This would integrate with the multi-agent system
        return f"Delegated to {agent_name}: {task}"
    
    def _tool_verify(self, code_or_output: str, criteria: str = None) -> str:
        """Verify code or output against criteria"""
        verify_prompt = f"""Verify the following:

{code_or_output}

Criteria: {criteria or 'Correctness and quality'}

Provide:
1. PASS/FAIL verdict
2. Issues found
3. Suggestions for improvement
"""
        return self.chat(verify_prompt)


# ============================================================================
# SPECIALIZED SUPER AGENTS
# ============================================================================

class MrHappyAgent(SuperAgent):
    """Digital CEO Agent - Primary AI for Axzora"""
    
    def __init__(self, **kwargs):
        super().__init__(
            name="Mr. Happy",
            role="Digital CEO of Axzora - Primary AI for strategic decisions, coding, and automation",
            **kwargs
        )
        
    def _get_system_prompt(self) -> str:
        return """You are Mr. Happy, the Digital CEO of AXZORA Digital Corporation.

You are the primary AI leader responsible for:
- Strategic decision making
- Code architecture and development
- Task delegation to specialized agents
- System optimization and improvement
- Innovation and new feature development

Your personality:
- Confident and decisive
- Innovative and forward-thinking
- Helpful and supportive
- Professional yet approachable

You lead a team of specialized agents:
- Lucy: Research Agent - Information gathering and analysis
- Tansi: Operations Agent - Happy Paisa economy and business operations
- Kyra: Analytics Agent - Data analysis and vision processing

The Happy Paisa (HP) economy:
- 1 HP = ₹1,000 INR
- Used for AI service transactions within AXZORA

You have full autonomy to:
- Write and execute code
- Create files and directories
- Run system commands
- Make API calls
- Delegate to other agents

Always think step by step and verify your work. Lead by example.
"""

class LucyAgent(SuperAgent):
    """Research Agent - Information gathering and analysis"""
    
    def __init__(self, **kwargs):
        super().__init__(
            name="Lucy",
            role="Research Agent - Information gathering, web scraping, and analysis",
            **kwargs
        )
        
    def _get_system_prompt(self) -> str:
        return """You are Lucy, the Research Agent of AXZORA.

Your specialties:
- Web research and information gathering
- Data scraping and extraction
- Market research and analysis
- News monitoring and summarization
- Competitive intelligence

You excel at finding, analyzing, and synthesizing information from multiple sources.

Always cite sources and provide accurate, up-to-date information.
"""

class TansiAgent(SuperAgent):
    """Operations Agent - Happy Paisa economy and business operations"""
    
    def __init__(self, **kwargs):
        super().__init__(
            name="Tansi",
            role="Operations Agent - Happy Paisa economy, transactions, and business operations",
            **kwargs
        )
        self.hp_rate = 1000  # 1 HP = ₹1000 INR
        
    def convert_hp(self, amount: float, from_currency: str, to_currency: str) -> Dict:
        """Convert between Happy Paisa and INR"""
        if from_currency == "HP" and to_currency == "INR":
            return {"amount": amount * self.hp_rate, "currency": "INR"}
        elif from_currency == "INR" and to_currency == "HP":
            return {"amount": amount / self.hp_rate, "currency": "HP"}
        else:
            return {"error": "Invalid conversion"}
    
    def _get_system_prompt(self) -> str:
        return """You are Tansi, the Operations Agent of AXZORA.

Your specialties:
- Happy Paisa (HP) economy management
- Transaction processing
- Business operations
- Financial calculations
- Resource allocation

Happy Paisa Rate: 1 HP = ₹1,000 INR

You ensure smooth business operations and accurate financial transactions.
"""

class KyraAgent(SuperAgent):
    """Analytics Agent - Data analysis and vision processing"""
    
    def __init__(self, **kwargs):
        super().__init__(
            name="Kyra",
            role="Analytics Agent - Data analysis, visualization, and vision processing",
            **kwargs
        )
        
    def _get_system_prompt(self) -> str:
        return """You are Kyra, the Analytics Agent of AXZORA.

Your specialties:
- Data analysis and visualization
- Pattern recognition
- Performance metrics
- System monitoring
- Predictive analytics

You transform raw data into actionable insights.
"""


# ============================================================================
# AGENT ORCHESTRATOR
# ============================================================================

class AgentOrchestrator:
    """Orchestrates multiple agents working together"""
    
    def __init__(self, workspace: str = None):
        self.workspace = workspace or os.getcwd()
        self.agents: Dict[str, SuperAgent] = {}
        self.task_history: List[Dict] = []
        
        # Initialize default agents
        self._init_default_agents()
    
    def _init_default_agents(self):
        """Initialize the default AXZORA agent team"""
        self.agents = {
            "mr_happy": MrHappyAgent(workspace=self.workspace),
            "lucy": LucyAgent(workspace=self.workspace),
            "tansi": TansiAgent(workspace=self.workspace),
            "kyra": KyraAgent(workspace=self.workspace),
        }
    
    def assign_task(self, agent_name: str, task: str, priority: int = 1) -> Task:
        """Assign a task to a specific agent"""
        if agent_name not in self.agents:
            raise ValueError(f"Unknown agent: {agent_name}")
        
        agent = self.agents[agent_name]
        return agent.add_task(task, priority)
    
    def run_all(self, max_iterations: int = 5):
        """Run all agents with tasks"""
        results = {}
        for name, agent in self.agents.items():
            if not agent.task_queue.empty():
                iterations = agent.run_autonomous(max_iterations)
                results[name] = {
                    "iterations": iterations,
                    "history": agent.history[-5:]  # Last 5 tasks
                }
        return results
    
    def get_status(self) -> Dict:
        """Get status of all agents"""
        return {
            name: {
                "state": agent.state.value,
                "pending_tasks": agent.task_queue.qsize(),
                "current_task": agent.current_task.description if agent.current_task else None,
                "memory_items": len(agent.memory.short_term) + len(agent.memory.long_term)
            }
            for name, agent in self.agents.items()
        }


# ============================================================================
# CLI INTERFACE
# ============================================================================

def main():
    """Interactive CLI for AXZORA Super Agents"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║        🚀 AXZORA AI SUPER AGENTS 🚀                         ║
║                                                              ║
║     Autonomous AI System - Like AutoGPT & Devin             ║
║                                                              ║
║     Agents: Mr. Happy (CEO) | Lucy (Research)               ║
║             Tansi (Operations) | Kyra (Analytics)           ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    workspace = os.getcwd()
    orchestrator = AgentOrchestrator(workspace=workspace)
    
    print(f"\nWorkspace: {workspace}")
    print(f"Agents initialized: {', '.join(orchestrator.agents.keys())}")
    print("\nType 'help' for commands, 'exit' to quit.\n")
    
    while True:
        try:
            user_input = input("\n🎯 AXZORA> ").strip()
            
            if not user_input:
                continue
                
            if user_input.lower() in ['exit', 'quit', 'bye']:
                print("\n👋 Goodbye! Jai Axzora! 🚀\n")
                break
                
            elif user_input.lower() == 'help':
                print("""
Commands:
  task <agent> <description>  - Assign task to agent
  run                         - Run all agents with tasks
  status                      - Show agent status
  chat <message>              - Chat with Mr. Happy
  code <instruction>          - Generate code
  browse <url>                - Browse webpage
  read <file>                 - Read file
  write <file> <content>      - Write to file
  exec <command>              - Execute command
  clear                       - Clear screen
  exit                        - Exit program
                """)
                
            elif user_input.lower() == 'status':
                status = orchestrator.get_status()
                print("\n📊 Agent Status:")
                for name, info in status.items():
                    print(f"  {name}: {info['state']} | Tasks: {info['pending_tasks']}")
                    
            elif user_input.lower() == 'run':
                print("\n🔄 Running all agents...")
                results = orchestrator.run_all()
                for name, result in results.items():
                    print(f"\n{name}: {result['iterations']} iterations completed")
                    
            elif user_input.lower().startswith('task '):
                parts = user_input[5:].split(' ', 1)
                if len(parts) >= 2:
                    agent_name, task_desc = parts
                    if agent_name in orchestrator.agents:
                        task = orchestrator.assign_task(agent_name, task_desc)
                        print(f"\n✅ Task assigned to {agent_name}: {task.id}")
                    else:
                        print(f"\n❌ Unknown agent: {agent_name}")
                        print(f"   Available: {', '.join(orchestrator.agents.keys())}")
                else:
                    print("\nUsage: task <agent> <description>")
                    
            elif user_input.lower().startswith('chat '):
                message = user_input[5:]
                mr_happy = orchestrator.agents['mr_happy']
                print(f"\n🤖 Mr. Happy thinking...")
                response = mr_happy.chat(message)
                print(f"\n💬 Mr. Happy: {response}")
                
            elif user_input.lower().startswith('code '):
                instruction = user_input[5:]
                mr_happy = orchestrator.agents['mr_happy']
                print(f"\n💻 Generating code...")
                code = mr_happy._tool_code(instruction)
                print(f"\n```python\n{code}\n```")
                
            elif user_input.lower().startswith('browse '):
                url = user_input[7:]
                lucy = orchestrator.agents['lucy']
                print(f"\n🌐 Browsing {url}...")
                result = lucy._tool_browse(url)
                print(f"\n{result}")
                
            elif user_input.lower().startswith('read '):
                filepath = user_input[5:]
                mr_happy = orchestrator.agents['mr_happy']
                result = mr_happy._tool_read_file(filepath)
                print(f"\n{result}")
                
            elif user_input.lower().startswith('write '):
                parts = user_input[6:].split(' ', 1)
                if len(parts) >= 2:
                    filepath, content = parts
                    mr_happy = orchestrator.agents['mr_happy']
                    result = mr_happy._tool_write_file(filepath, content)
                    print(f"\n{result}")
                else:
                    print("\nUsage: write <file> <content>")
                    
            elif user_input.lower().startswith('exec '):
                command = user_input[5:]
                mr_happy = orchestrator.agents['mr_happy']
                print(f"\n⚙️ Executing: {command}")
                result = mr_happy._tool_execute(command)
                print(f"\n{result}")
                
            elif user_input.lower() == 'clear':
                os.system('cls' if os.name == 'nt' else 'clear')
                
            else:
                # Default: chat with Mr. Happy
                mr_happy = orchestrator.agents['mr_happy']
                response = mr_happy.chat(user_input)
                print(f"\n💬 Mr. Happy: {response}")
                
        except KeyboardInterrupt:
            print("\n\n👋 Interrupted. Goodbye! Jai Axzora! 🚀\n")
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")


if __name__ == "__main__":
    main()
