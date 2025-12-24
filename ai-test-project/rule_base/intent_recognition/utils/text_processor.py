from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseTextProcessor(ABC):
    """
    文本预处理接口。

    说明：
    - 这里只定义接口，不提供具体实现。
    - 使用方可以根据业务需要实现：
      * 去除标点
      * 全角/半角转换
      * 大小写归一
      * 分词、繁简转换等
    """

    @abstractmethod
    def preprocess(self, text: str, context: dict[str, Any] | None = None) -> str:
        """
        文本预处理接口。

        Args:
            text: 原始用户输入
            context: 可选上下文信息

        Returns:
            预处理后的文本
        """
        raise NotImplementedError
