from __future__ import annotations

import logging
import re
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class BaseSlotFiller:
    """
    槽位提取器基类，所有槽位提取策略需实现 fill_slots 方法。
    """

    def __init__(self, name: str, priority: int):
        self.name = name
        self.priority = priority

    def fill_slots(self, intent_result, original_text: str, context: Dict[str, Any] | None = None):
        """
        填充槽位。
        
        Args:
            intent_result: 意图识别结果
            original_text: 原始文本
            context: 上下文信息（可选）
            
        Returns:
            填充槽位后的 intent_result
        """
        raise NotImplementedError


class BaseLLMSlotFiller:
    """
    槽位填充大模型兜底接口。
    使用方可实现实际的大模型调用逻辑。
    """

    def fill_missing_slots(
        self,
        text: str,
        intent_name: str,
        current_slots: Dict[str, Any],
    ) -> Dict[str, Any]:
        raise NotImplementedError


class SlotFiller(BaseSlotFiller):
    """
    默认槽位填充器：
    1. 使用正则精确匹配（来自 regex_patterns.json）
    2. 使用大模型兜底（可选，接口可插拔）
    """

    def __init__(
        self,
        config,
        llm_filler: BaseLLMSlotFiller | None = None,
        llm_timeout: float = 2.0,
    ):
        super().__init__(name="default_slot_filler", priority=100)
        self.config = config
        self.llm_filler = llm_filler
        self.llm_timeout = llm_timeout
        self._slot_patterns: Dict[str, List[re.Pattern]] = {}
        self._compile_slot_patterns()

    def _compile_slot_patterns(self) -> None:
        """
        regex_patterns.json 规范示例：

        {
          "slots": {
            "departure_date": [
              {"pattern": "(?P<departure_date>\\d{4}-\\d{1,2}-\\d{1,2})"}
            ]
          }
        }
        """
        slots_conf = self.config.regex_patterns.get("slots", {})
        for slot_name, patterns in slots_conf.items():
            compiled = []
            for p in patterns:
                pattern = p.get("pattern")
                flags_str = p.get("flags", "")
                flags = 0
                if "i" in flags_str.lower():
                    flags |= re.IGNORECASE
                if pattern:
                    compiled.append(re.compile(pattern, flags))
            self._slot_patterns[slot_name] = compiled

    def fill_slots(self, intent_result, original_text: str, context: Dict[str, Any] | None = None):
        """
        槽位填充流程：
        1. 按 intent 的 slots 定义，做正则匹配
        2. 对缺失槽位，尝试使用 LLM 兜底（如果配置了 llm_filler）
        """
        intent_name = intent_result.intent
        slots_def = self.config.get_intent_slots(intent_name)
        if not slots_def:
            return intent_result

        slots = dict(intent_result.slots) if intent_result.slots else {}

        # 1. 正则精确匹配
        for slot_def in slots_def:
            name = slot_def.get("name")
            if not name:
                continue
            if name in slots:
                continue  # 已有值（可能来自正则意图匹配）

            patterns = self._slot_patterns.get(name, [])
            for pattern in patterns:
                m = pattern.search(original_text)
                if m:
                    if name in m.groupdict():
                        slots[name] = m.group(name)
                    else:
                        slots[name] = m.group(0)
                    break

        # 2. LLM 兜底（可选）
        if self.llm_filler:
            missing = [s["name"] for s in slots_def if s.get("required") and s["name"] not in slots]
            if missing:
                slots = self._fill_slots_via_llm(original_text, intent_name, slots)

        intent_result.slots = slots
        return intent_result

    def _fill_slots_via_llm(
        self,
        text: str,
        intent_name: str,
        current_slots: Dict[str, Any],
    ) -> Dict[str, Any]:
        if not self.llm_filler:
            return current_slots

        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                self.llm_filler.fill_missing_slots,
                text,
                intent_name,
                current_slots,
            )
            try:
                new_slots = future.result(timeout=self.llm_timeout)
                if not isinstance(new_slots, dict):
                    logger.warning("LLM slot filler returned non-dict, ignored.")
                    return current_slots
                merged = dict(current_slots)
                merged.update(new_slots)
                return merged
            except FuturesTimeoutError:
                logger.warning("LLM slot filling timed out, degraded.")
            except Exception:
                logger.exception("LLM slot filling failed, degraded.")
        return current_slots
    
class XwCustomSlotFiller(BaseSlotFiller):
    """
    遥感异常分析槽位填充器：
    根据数据中的卫星异常信息进行分类和参数提取。
    
    返回格式：Dict[f"{异常大类-异常小类}", List[Dict[str, Any]]]
    
    分类规则：
    1. 单颗星异常：
       - 多圈次长时间异常：多条连续数据，同一颗卫星
       - 单圈次异常：单条数据
    2. 多颗星异常：当前返回占位符，后期扩展
    
    注意：
    - 每个异常类别对应一个异常列表
    - 同类型的多个异常会被聚合到同一个列表中
    """

    def __init__(self, config):
        """
        初始化遥感异常槽位填充器。
        
        Args:
            config: 配置对象
        """
        super().__init__(name="xw_slot_filler", priority=100)
        self.config = config
    
    def fill_slots(self, intent_result, original_text: str, context: Dict[str, Any] | None = None) -> 'IntentResult':
        """
        槽位填充：从 metadata 的 data 中提取异常信息。
        
        返回数据格式：Dict[f"{异常大类-异常小类}", List[Dict[str, Any]]]
        
        Args:
            intent_result: 意图识别结果
            original_text: 原始文本
            context: 上下文信息
        
        Returns:
            填充槽位后的 intent_result，slots['anomalies'] 包含异常分类列表
        """
        data_list = intent_result.metadata.get('data', [])
        if not data_list:
            return intent_result
        
        # 解析异常数据
        anomaly_result = self._parse_anomalies(data_list)
        
        # 将结果写入槽位
        intent_result.slots = intent_result.slots or {}
        intent_result.slots['anomalies'] = anomaly_result
        
        return intent_result
    
    def _parse_anomalies(self, data_list: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        解析异常数据列表，按规则进行分类和参数提取。
        
        规则：
        1. 从第一条数据开始依次读 data
        2. 如果 satellites 是一个卫星（单颗），则异常大类为"单颗星异常"
           - 再获取第二条数据如果还是同一颗卫星，则异常小类为"多圈次长时间"
           - 否则为"单圈次"
        3. 如果 satellites 是多颗，则异常大类为"多颗星异常"
        4. 如果 satellites 为 None，则跳过该条
        
        Returns:
            Dict[f"{异常大类-异常小类}", List[Dict[str, Any]]]
            每个异常类别对应一个异常列表
        """
        result: Dict[str, List[Dict[str, Any]]] = {}
        i = 0
        
        # 定义三种主要异常类别
        multi_pass_key = "单颗星异常-多圈次长时间（涉及多个落地星）不通"
        single_pass_key = "单颗星异常-单圈次（单落地星）全程或短时间不通"
        multi_sat_key = "多颗星异常-多颗卫星联合异常"
        
        # 初始化异常列表
        result[multi_pass_key] = []
        result[single_pass_key] = []
        result[multi_sat_key] = []
        
        while i < len(data_list):
            record = data_list[i]
            
            # 每条数据是一个字典，形如：
            # {'key': {'start_time': ..., 'end_time': ..., 'satellites': {...}}}
            for key, value in record.items():
                satellites = value.get('satellites')
                
                if satellites is None:
                    # 无卫星异常，跳过
                    i += 1
                    break
                
                satellite_count = len(satellites) if isinstance(satellites, dict) else 0
                
                if satellite_count == 1:
                    # 单颗星异常
                    satellite_name = list(satellites.keys())[0]
                    anomaly_type = self._classify_single_satellite(
                        data_list, i, satellite_name
                    )
                    
                    if anomaly_type == "multi_pass_long_time":
                        # 多圈次长时间异常：找出连续的同一颗卫星记录
                        end_idx = self._find_same_satellite_end(data_list, i, satellite_name)
                        anomaly_info = self._extract_multi_pass_info(
                            data_list, i, end_idx, satellite_name
                        )
                        result[multi_pass_key].append(anomaly_info)
                        i = end_idx + 1
                    else:
                        # 单圈次异常
                        anomaly_info = self._extract_single_pass_info(data_list[i], satellite_name)
                        result[single_pass_key].append(anomaly_info)
                        i += 1
                    break
                
                elif satellite_count > 1:
                    # 多颗星异常
                    anomaly_info = {
                        "satellites": list(satellites.keys()),
                        "start_time": str(value.get('start_time')),
                        "end_time": str(value.get('end_time')),
                        "note": "多颗星异常分类参数提取后期再扩展实现"
                    }
                    result[multi_sat_key].append(anomaly_info)
                    i += 1
                    break
                else:
                    # satellites 为空字典
                    i += 1
                    break
        
        return result
    
    def _classify_single_satellite(self, data_list: List[Dict[str, Any]], current_idx: int, satellite_name: str) -> str:
        """
        判断单颗星异常是多圈次还是单圈次。
        
        规则：
        - 如果第二条数据也是同一颗卫星（单颗），则为多圈次长时间异常
        - 否则为单圈次异常
        """
        if current_idx + 1 < len(data_list):
            next_record = data_list[current_idx + 1]
            for key, value in next_record.items():
                satellites = value.get('satellites')
                if satellites and isinstance(satellites, dict):
                    satellite_count = len(satellites)
                    if satellite_count == 1:
                        next_satellite = list(satellites.keys())[0]
                        if next_satellite == satellite_name:
                            return "multi_pass_long_time"
        
        return "single_pass"
    
    def _find_same_satellite_end(self, data_list: List[Dict[str, Any]], start_idx: int, satellite_name: str) -> int:
        """
        找到连续的同一颗卫星记录的结束位置。
        
        返回最后一个包含该卫星的索引。停止条件：
        - 遇到无卫星数据（satellites 为 None）
        - 遇到多颗卫星
        - 遇到不同的单颗卫星
        """
        i = start_idx + 1
        while i < len(data_list):
            record = data_list[i]
            for key, value in record.items():
                satellites = value.get('satellites')
                if satellites is None:
                    # 无卫星数据，停止
                    return i - 1
                
                if isinstance(satellites, dict):
                    satellite_count = len(satellites)
                    if satellite_count != 1:
                        # 多颗或无颗卫星，停止
                        return i - 1
                    
                    current_satellite = list(satellites.keys())[0]
                    if current_satellite != satellite_name:
                        # 卫星不同，停止
                        return i - 1
            i += 1
        
        return len(data_list) - 1
    
    def _extract_multi_pass_info(
        self, data_list: List[Dict[str, Any]], start_idx: int, end_idx: int, satellite_name: str
    ) -> Dict[str, Any]:
        """
        提取多圈次长时间异常的信息：
        - 第一条的开始时间和最后一条的结束时间
        - 涉及的圈次数量
        """
        start_record = data_list[start_idx]
        end_record = data_list[end_idx]
        
        # 获取开始时间（第一条数据的 start_time）
        start_time = None
        for key, value in start_record.items():
            start_time = value.get('start_time')
            break
        
        # 获取结束时间（最后一条数据的 end_time）
        end_time = None
        for key, value in end_record.items():
            end_time = value.get('end_time')
            break
        
        return {
            "satellite": satellite_name,
            "start_time": str(start_time),
            "end_time": str(end_time),
            "pass_count": end_idx - start_idx + 1
        }
    
    def _extract_single_pass_info(self, record: Dict[str, Any], satellite_name: str) -> Dict[str, Any]:
        """
        提取单圈次异常的信息：
        - 该条数据的开始时间
        - 该条数据的结束时间
        - 卫星名称
        """
        start_time = None
        end_time = None
        
        for key, value in record.items():
            start_time = value.get('start_time')
            end_time = value.get('end_time')
            break
        
        return {
            "satellite": satellite_name,
            "start_time": str(start_time),
            "end_time": str(end_time)
        }
        



