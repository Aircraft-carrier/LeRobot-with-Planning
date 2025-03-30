import threading
import tomllib
from pathlib import Path
from typing import Dict, List, Optional
import json
from pydantic import BaseModel, Field

def get_project_root() -> Path:
    """Get the project root directory"""
    return Path(__file__).resolve().parent.parent


PROJECT_ROOT = get_project_root()
WORKSPACE_ROOT = PROJECT_ROOT / "workspace"


class LLMSettings(BaseModel):
    model: str = Field(..., description="Model name")
    base_url: str = Field(..., description="API base URL")
    api_key: str = Field(..., description="API key")
    max_tokens: int = Field(4096, description="Maximum number of tokens per request")
    max_input_tokens: Optional[int] = Field(
        None,
        description="Maximum input tokens to use across all requests (None for unlimited)",
    )
    temperature: float = Field(1.0, description="Sampling temperature")
    api_type: str = Field(..., description="AzureOpenai or Openai")
    api_version: str = Field(..., description="Azure Openai version if AzureOpenai")


# class ActionConfig(BaseModel):
#     actions: Dict[int, str] = Field(
#         default_factory=dict,
#         description="Action ID to description mapping"
#     )
    
#     @property
#     def count(self) -> int:
#         """Returns the total number of available actions"""
#         return len(self.actions)
    
#     def format_for_prompt(self, include_ids: bool = True) -> str:
#         if not self.actions:
#             return "No available actions"
            
#         sorted_actions = sorted(self.actions.items())
#         max_num_width = len(str(len(sorted_actions)))
        
#         lines = []
#         for idx, (action_id, desc) in enumerate(sorted_actions, 1):
#             prefix = f"[ID:{action_id}] " if include_ids else ""
#             lines.append(
#                 f"{prefix}{desc.strip().rstrip('.')}"
#             )
            
#         return f"""     ## Available Actions (Total: {self.count}):\n{"\n".join(lines)}
#             """
    
class ActionConfig(BaseModel):
    actions: Dict[int, str] = Field(
        ...,
        description="Mapping of action IDs to descriptions"
    )
    preconditions: Dict[int, List[str]] = Field(
        default_factory=dict,
        description="Optional mapping of action IDs to their preconditions"
    )

    @property
    def count(self) -> int:
        """Returns the total number of available actions"""
        return len(self.actions)

    @classmethod
    def load_from_json(cls, file_path: Path) -> "ActionConfig":
        """智能加载方法，处理可选前置条件"""
        try:
            with open(file_path, 'r') as f:
                raw_data = json.load(f)
                
            action_mapping = {}
            precond_mapping = {}
            
            for action_id_str, data in raw_data.items():
                action_id = int(action_id_str)
                
                # 强制要求action字段
                if "action" not in data:
                    raise ValueError(f"Missing 'action' for action {action_id}")
                action_mapping[action_id] = data["action"]
                
                # 可选处理前置条件
                if "preconditions" in data:
                    if not isinstance(data["preconditions"], list):
                        raise ValueError(f"Invalid preconditions type for action {action_id}")
                    precond_mapping[action_id] = [
                        p.strip() for p in data["preconditions"] 
                        if isinstance(p, str)
                    ]
            
            return cls(
                actions=action_mapping,
                preconditions=precond_mapping
            )
            
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON format")
        except KeyError as e:
            raise ValueError(f"Missing key in JSON: {str(e)}")

    def format_for_prompt(self) -> str:
        """生成带可选前置条件的格式化输出"""
        output = []
        for action_id in sorted(self.actions.keys()):
            desc = self.actions[action_id]
            preconds = self.preconditions.get(action_id, [])
            
            action_entry = f"[ID:{action_id}] {desc}"
            if preconds:
                action_entry += "\npreconditions :\n" + "\n".join(
                    f"  • {p}" for p in preconds
                )
            output.append(action_entry)
        criteria = [
            "1. If the task is To place an item in the refrigerator, first open the refrigerator door, then take the item."
        ]
        return f"""     ## Available Actions (Total: {self.count}):\ncriteria\n{"\n".join(criteria)}\n\n{"\n\n".join(output)}"""

class AppConfig(BaseModel):
    llm: Dict[str, LLMSettings]
    action: ActionConfig = Field(
        default_factory=ActionConfig,
        description="Action configurations"
    )
    action_src: ActionConfig = Field(
        default_factory=ActionConfig,
        description="Action src configurations"
    )

    class Config:
        arbitrary_types_allowed = True

class Config:
    _instance = None
    _lock = threading.Lock()
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            with self._lock:
                if not self._initialized:
                    self._config = None
                    self._load_initial_config()
                    self._initialized = True

    @staticmethod
    def _get_config_path() -> Path:
        root = PROJECT_ROOT
        config_path = root / "config" / "config.toml"
        if config_path.exists():
            return config_path
        example_path = root / "config" / "config.example.toml"
        if example_path.exists():
            return example_path
        raise FileNotFoundError("No configuration file found in config directory")

    def _load_actions(self) -> Dict[int, str]:
        actions_path = PROJECT_ROOT / "config" / "actions.json"
        try:
            with open(actions_path, 'r') as f:
                action_dict = json.load(f)
                return {int(k): v for k, v in action_dict.items()}
        except FileNotFoundError:
            raise RuntimeError(f"Actions file not found at {actions_path}")
        except json.JSONDecodeError:
            raise RuntimeError("Invalid JSON format in actions file")

    def _load_config(self) -> dict:
        config_path = self._get_config_path()
        with config_path.open("rb") as f:
            return tomllib.load(f)

    def _load_initial_config(self):
        raw_config = self._load_config()
        
        # 加载LLM配置
        base_llm = raw_config.get("llm", {})
        llm_overrides = {
            k: v for k, v in raw_config.get("llm", {}).items() if isinstance(v, dict)
        }

        default_settings = {
            "model": base_llm.get("model"),
            "base_url": base_llm.get("base_url"),
            "api_key": base_llm.get("api_key"),
            "max_tokens": base_llm.get("max_tokens", 4096),
            "max_input_tokens": base_llm.get("max_input_tokens"),
            "temperature": base_llm.get("temperature", 1.0),
            "api_type": base_llm.get("api_type", ""),
            "api_version": base_llm.get("api_version", ""),
        }

        # 加载动作配置
        action_src_config = ActionConfig(actions=self._load_actions())
        action_config = ActionConfig.load_from_json(Path("config/action_base.json"))

        config_dict = {
            "llm": {
                "default": default_settings,
                **{
                    name: {**default_settings,**override_config}
                    for name, override_config in llm_overrides.items()
                },
            },
            "action": action_config,
            "action_src": action_src_config
        }

        self._config = AppConfig(**config_dict)

    @property
    def llm(self) -> Dict[str, LLMSettings]:
        return self._config.llm

    @property
    def action(self) -> ActionConfig:
        return self._config.action
    
    @property
    def action_src(self) -> ActionConfig:
        return self._config.action_src

config = Config()