import re
from rich.console import Console,Group
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax
from rich.box import MINIMAL
from dataclasses import dataclass, field
from typing import List, Optional



class Color:  
    GREEN = "\033[92m"  
    RED = "\033[91m"  
    BLUE = "\033[94m"  
    YELLOW = "\033[93m"  
    MAGENTA = "\033[95m"  
    CYAN = "\033[96m"  
    RESET = "\033[0m"

@dataclass
class Function:
    name: str
    arguments: str

@dataclass
class ChatCompletionMessageToolCall:
    id: str
    function: Function
    type: str
    index: int

@dataclass
class ChatCompletionMessage:
    content: str
    role: str
    tool_calls: List[ChatCompletionMessageToolCall] = field(default_factory=list)

@dataclass
class Choice:
    finish_reason: str
    index: int
    message: ChatCompletionMessage

@dataclass
class CompletionUsage:
    completion_tokens: int
    prompt_tokens: int
    total_tokens: int

@dataclass
class ChatCompletion:
    id: str
    created: int
    model: str
    choices: List[Choice]
    usage: CompletionUsage

def format_chat_completion(completion: ChatCompletion) -> str:
    formatted_output = [
        "Chat Completion Details:",
        "------------------------",
        f"ID: {completion.id}",
        f"Created At: {(lambda ts: f'{ts//31536000} years, {(ts%31536000)//86400} days, {(ts%86400)//3600} hours, {(ts%3600)//60} minutes, {ts%60} seconds')((2025*31536000 + 79*86400 + 15*3600 + 21*60 + 49) - (1970*31536000))} (timestamp {completion.created})",
        f"Model Used: {completion.model}\n",
        
        "Choices:",
        "========",
    ]
    
    for idx, choice in enumerate(completion.choices, start=1):
        formatted_output.append(f"{idx}. Choice:")
        formatted_output.append(f"   - Finish Reason: {choice.finish_reason}")
        formatted_output.append(f"   - Index: {choice.index}")
        formatted_output.append("   - Message:")
        formatted_output.append(f"     * Role: {choice.message.role}")
        formatted_output.append(f"     * Content: {choice.message.content}")
        if choice.message.tool_calls:
            for tool_call in choice.message.tool_calls:
                formatted_output.append("     * Tool Calls:")
                formatted_output.append(f"       - Tool Call ID: {tool_call.id}")
                formatted_output.append(f"       - Function Name: {tool_call.function.name}")
                formatted_output.append(f"       - Arguments: {tool_call.function.arguments}")
                formatted_output.append(f"       - Type: {tool_call.type}")
                formatted_output.append(f"       - Index: {tool_call.index}")
    
    formatted_output.extend([
        "\nUsage Statistics:",
        "=================",
        f"- Prompt Tokens: {completion.usage.prompt_tokens}",
        f"- Completion Tokens: {completion.usage.completion_tokens}",
        f"- Total Tokens: {completion.usage.total_tokens}",
    ])
    
    return "\n".join(formatted_output)


def display_code(code: str, language: str = "python"):
    """
    在控制台中高亮显示代码或渲染Markdown内容。
    
    参数:
        code (str): 要显示的代码或Markdown内容
        language (str): 代码语言（如'python', 'javascript'），或'markdown'以渲染Markdown
    """
    console = Console()
    
    if language == "markdown":
        panels = []
        style = "black on white"
        # 分割Markdown中的代码块和普通文本
        parts = re.split(r"(```[\s\S]*?```)", code)
        
        for part in parts:
            part = part.strip()
            if not part:
                continue
            
            if part.startswith("```"):
                # 处理代码块
                code_block = part[3:-3].strip()  # 移除前后的```
                if '\n' not in code_block:
                    code_lang = 'text'
                    code_content = code_block
                else:
                    # 提取代码语言和内容
                    first_newline = code_block.find('\n')
                    code_lang = code_block[:first_newline].strip() or 'text'
                    code_content = code_block[first_newline+1:].lstrip('\n')
                
                # 高亮代码
                syntax = Syntax(code_content, code_lang, theme="paraiso-dark", line_numbers=True)
                panels.append(Panel(syntax, style=style, box=MINIMAL))
            else:
                # 渲染普通Markdown文本
                panels.append(Panel(Markdown(part), style=style, box=MINIMAL))
        
        # 动态显示所有面板
        with Live(auto_refresh=False) as live:
            live.update(Group(*panels))
            live.refresh()
    else:
        # 直接高亮其他语言代码
        syntax = Syntax(code, language, theme="paraiso-dark", line_numbers=True)
        console.print(syntax)