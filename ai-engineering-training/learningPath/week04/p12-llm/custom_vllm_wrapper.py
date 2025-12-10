"""
自定义 vLLM 封装器
展示如何实现一个完整的 LLM 封装器，包含所有模型参数
"""
from typing import Any, Dict, List, Optional, Union, Iterator
from langchain_core.language_models.llms import LLM
from langchain_core.callbacks.manager import CallbackManagerForLLMRun
from pydantic import Field, validator
import requests
import json
import time


class CustomVLLMWrapper(LLM):
    """
    自定义 vLLM 封装器
    支持完整的模型参数配置和流式输出
    """

    # 基础配置
    model_name: str = Field(..., description="模型名称")
    base_url: str = Field(default="http://localhost:8000", description="vLLM 服务基础 URL")
    api_key: Optional[str] = Field(default=None, description="API密钥")

    # 生成参数 - 核心参数
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="温度参数，控制随机性")
    top_p: float = Field(default=0.9, ge=0.0, le=1.0, description="核采样参数")
    top_k: int = Field(default=50, ge=1, le=100, description="Top-K采样参数")
    max_tokens: int = Field(default=512, ge=1, le=4096, description="最大生成token数")

    # 生成参数 - 高级参数
    repetition_penalty: float = Field(default=1.1, ge=0.1, le=2.0, description="重复惩罚")
    frequency_penalty: float = Field(default=0.0, ge=-2.0, le=2.0, description="频率惩罚")
    presence_penalty: float = Field(default=0.0, ge=-2.0, le=2.0, description="存在惩罚")
    min_p: float = Field(default=0.0, ge=0.0, le=1.0, description="最小概率阈值")

    # 停止条件
    stop: Optional[List[str]] = Field(default=None, description="停止词列表")
    stop_token_ids: Optional[List[int]] = Field(default=None, description="停止token ID列表")

    # 采样策略
    use_beam_search: bool = Field(default=False, description="是否使用束搜索")
    best_of: int = Field(default=1, ge=1, le=20, description="生成候选数量")
    n: int = Field(default=1, ge=1, le=10, description="返回结果数量")

    # 长度控制
    length_penalty: float = Field(default=1.0, ge=0.1, le=2.0, description="长度惩罚")
    early_stopping: bool = Field(default=False, description="是否提前停止")

    # 特殊参数
    seed: Optional[int] = Field(default=None, description="随机种子")
    logprobs: Optional[int] = Field(default=None, ge=0, le=20, description="返回对数概率数量")
    echo: bool = Field(default=False, description="是否回显输入")

    # 性能参数
    skip_special_tokens: bool = Field(default=True, description="跳过特殊token")
    spaces_between_special_tokens: bool = Field(default=True, description="特殊token间是否加空格")

    # 请求配置
    timeout: int = Field(default=60, description="请求超时时间(秒)")
    max_retries: int = Field(default=3, description="最大重试次数")

    @validator('temperature')
    def validate_temperature(cls, v):
        if v < 0 or v > 2:
            raise ValueError('temperature 必须在 0-2 之间')
        return v

    @validator('top_p')
    def validate_top_p(cls, v):
        if v < 0 or v > 1:
            raise ValueError('top_p 必须在 0-1 之间')
        return v

    @property
    def _llm_type(self) -> str:
        return "custom_vllm"

    def __call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ):
        """同步调用方法"""
        # 合并停止词
        final_stop = stop or self.stop

        # 构建请求参数
        params = self._build_request_params(prompt, final_stop, **kwargs)

        # 发送请求
        response = self._make_request(params)

        # 解析响应
        return self._parse_response(response)
