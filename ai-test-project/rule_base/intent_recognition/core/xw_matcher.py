#!/usr/bin/env python3
"""
高级扩展示例：
1. 自定义识别器,识别execl表格数据
2. LLM 槽位填充兜底
3. 文本预处理器
"""
import re
from typing import Any, Dict, List, Optional
import pandas as pd
from intent_recognition.core.rule_engine import BaseIntentRecognizer, IntentResult

class XwCustomMatcher(BaseIntentRecognizer):
    """自定义识别器,识别 execl 表格数据
    
    符合 matcher 统一接口规范，从配置文件加载参数。
    
    **重要：**
    - 这是一个 **按需触发** 的识别器，不应该对每个输入都执行
    - 只有当 context 中明确指定了 'trigger_excel' 为 True 时才会执行
    - 配置支持动态传入，可以在运行时指定不同的 Excel 文件
    """
    
    def __init__(self, config=None, name: str = "ExcelIntentRecognizer", priority: int = 200):
        """初始化 Excel 识别器
        
        Args:
            config: 配置对象，包含 excel_analyzer 配置
                如果为 None，则需要在 context 中传入 sheet_name 和 execl_path
            name: 识别器名称
            priority: 优先级
        """
        super().__init__(name, priority)
        self.config = config
        
        # 从配置中加载默认参数
        if config and hasattr(config, 'excel_analyzer'):
            excel_config = config.excel_analyzer
            self.default_duration_threshold = excel_config.get('duration_threshold', 15.0)
            self.default_ignore_no_interruption = excel_config.get('ignore_no_interruption', True)
            self.default_excel_type = excel_config.get('default_excel_type', 'merged')
            self.segment_pattern = excel_config.get('segment_pattern', r'^(\d{8}-\d+-\d+-\d+-\d+-CSCN-[AB]\d{4}-CSCN-[AB]\d{4})$')
            self.excel_types_config = excel_config.get('excel_types', {})
        else:
            # 如果没有配置，使用默认值
            self.default_duration_threshold = 15.0
            self.default_ignore_no_interruption = True
            self.default_excel_type = 'merged'
            self.segment_pattern = r'^(\d{8}-\d+-\d+-\d+-\d+-CSCN-[AB]\d{4}-CSCN-[AB]\d{4})$'
            self.excel_types_config = {}
        
        # 编译正则表达式
        self.compiled_pattern = re.compile(self.segment_pattern)
        
    def _parse_duration(self, duration_str: Any) -> Optional[float]:
        """解析中断时长字符串，提取总时长
        
        Args:
            duration_str: 中断时长字符串，格式如 "0.15(0.15)" 或 "1.0(0.15,0.15,0.15,0.15)"
            
        Returns:
            float: 解析后的总时长（分钟），如果无法解析则返回 None
        """
        if pd.isna(duration_str):
            return None
        
        try:
            # 将字符串转换为字符串类型（以防万一）
            duration_str = str(duration_str)
            
            # 提取括号前的数字（总时长）
            match = re.match(r'^([0-9.]+)', duration_str)
            if match:
                return float(match.group(1))
            return None
        except (ValueError, AttributeError):
            return None
    
    def _read_sheet_data(self, execl_path: str, sheet_name: str) -> pd.DataFrame:
        """读取指定 sheet 的全部内容
        
        Args:
            execl_path: Excel 文件路径
            sheet_name: sheet 名称
            
        Returns:
            pd.DataFrame: 读取的数据
        """
        return pd.read_excel(execl_path, sheet_name=sheet_name)
    
    def _parse_sheet_data(self, execl_path: str, sheet_name: str, duration_threshold: float = 15.0, 
                          ignore_no_interruption: bool = True, excel_type: str = 'merged',
                          segment_pattern: str = None) -> List[Dict[str, Dict[str, float]]]:
        """解析指定 sheet 的数据，过滤中断时长大于阈值的记录
        
        Args:
            execl_path: Excel 文件路径
            sheet_name: sheet 名称
            duration_threshold: 中断时长阈值（秒），默认 15.0 秒
            ignore_no_interruption: 是否忽略无中断时长大于15s的联通子段，默认 True
                - True: 只返回有中断时长大于15s的联通子段
                - False: 返回所有联通子段，无中断的返回 {联通子段名称: None}
            excel_type: Excel 类型，'merged' 或 'standardized'
            segment_pattern: 正则表达式用于匹配联通子段名称（用于 standardized 格式）
            
        Returns:
            List[Dict[联通子段名称, Dict[子段卫星名称, 中断时长] 或 None]]
            按理论开始时间排序（从小到大）
        """
        # 存储联通子段的数据，用于最后排序
        segment_data = []
        
        # 将秒转换为分钟（Excel中的时长单位是分钟）
        threshold_minutes = duration_threshold / 60.0
        
        # 读取指定 sheet
        df = self._read_sheet_data(execl_path, sheet_name)
        
        # 根据 Excel 类型处理数据
        if excel_type == 'merged':
            # 旧格式：向前填充联通子段名称和理论开始时间（因为Excel使用了行合并）
            df['联通子段名称'] = df['联通子段名称'].ffill()
            df['理论开始时间'] = df['理论开始时间'].ffill()
        elif excel_type == 'standardized' and segment_pattern:
            # 新格式：使用正则表达式过滤联通子段名称
            pattern = re.compile(segment_pattern)
            df = df[df['联通子段名称'].apply(lambda x: bool(pattern.match(str(x))) if pd.notna(x) else False)]
        
        # 解析中断时长列
        df['中断时长_parsed'] = df['中断时长'].apply(self._parse_duration)
        
        if ignore_no_interruption:
            # 只返回有中断时长大于阈值的记录
            filtered_df = df[
                df['中断时长_parsed'].notna() & 
                (df['中断时长_parsed'] > threshold_minutes)
            ]
            
            # 按联通子段名称分组处理
            for segment_name, group in filtered_df.groupby('联通子段名称'):
                # 获取该联通子段的理论开始时间（用于排序）
                start_time = group['理论开始时间'].iloc[0]
                
                # 构建子段卫星名称到中断时长的映射
                satellite_disruptions = {}
                for _, row in group.iterrows():
                    satellite_name = row['子段卫星名称']
                    disruption_time = row['中断时长_parsed']
                    satellite_disruptions[satellite_name] = disruption_time
                
                # 添加到结果列表
                segment_data.append({
                    'start_time': start_time,
                    'segment_name': segment_name,
                    'satellites': satellite_disruptions
                })
        else:
            # 返回所有联通子段，无中断的返回 None
            # 按联通子段名称分组处理所有数据
            for segment_name, group in df.groupby('联通子段名称'):
                # 获取该联通子段的理论开始时间（用于排序）
                start_time = group['理论开始时间'].iloc[0]
                
                # 过滤出中断时长大于阈值的记录
                filtered_group = group[
                    group['中断时长_parsed'].notna() & 
                    (group['中断时长_parsed'] > threshold_minutes)
                ]
                
                if len(filtered_group) > 0:
                    # 有中断时长大于阈值的卫星
                    satellite_disruptions = {}
                    for _, row in filtered_group.iterrows():
                        satellite_name = row['子段卫星名称']
                        disruption_time = row['中断时长_parsed']
                        satellite_disruptions[satellite_name] = disruption_time
                    
                    segment_data.append({
                        'start_time': start_time,
                        'segment_name': segment_name,
                        'satellites': satellite_disruptions
                    })
                else:
                    # 无中断时长大于阈值的卫星，返回 None
                    segment_data.append({
                        'start_time': start_time,
                        'segment_name': segment_name,
                        'satellites': None
                    })
        
        # 按理论开始时间排序（从小到大）
        segment_data.sort(key=lambda x: x['start_time'])
        
        # 构建最终输出格式
        results = []
        for item in segment_data:
            results.append({
                item['segment_name']: item['satellites']
            })
        
        return results
    
    def parse_all_sheets(self, duration_threshold: float = 15.0) -> List[Dict[str, Dict[str, float]]]:
        """读取所有 sheet 的数据，过滤中断时长大于阈值的记录
        
        Args:
            duration_threshold: 中断时长阈值（秒），默认 15.0 秒
            
        Returns:
            List[Dict[联通子段名称, Dict[子段卫星名称, 中断时长]]]
            按理论开始时间排序（从小到大）
        """
        # 读取所有 sheet 名称
        xls = pd.ExcelFile(self.execl_path)
        
        # 存储所有联通子段的数据，用于最后排序
        all_segment_data = []
        
        # 将秒转换为分钟
        threshold_minutes = duration_threshold / 60.0
        
        for sheet_name in xls.sheet_names:
            # 读取当前 sheet
            df = self._read_sheet_data(sheet_name)
            
            # 向前填充联通子段名称和理论开始时间（因为Excel使用了行合并，每个子段的名称和时间只在第一行出现）
            df['联通子段名称'] = df['联通子段名称'].ffill()
            df['理论开始时间'] = df['理论开始时间'].ffill()
            
            # 解析中断时长列
            df['中断时长_parsed'] = df['中断时长'].apply(self._parse_duration)
            
            # 过滤中断时长大于阈值的记录
            filtered_df = df[
                df['中断时长_parsed'].notna() & 
                (df['中断时长_parsed'] > threshold_minutes)
            ]
            
            # 按联通子段名称分组处理
            for segment_name, group in filtered_df.groupby('联通子段名称'):
                # 获取该联通子段的理论开始时间（用于排序）
                start_time = group['理论开始时间'].iloc[0]
                
                # 构建子段卫星名称到中断时长的映射
                satellite_disruptions = {}
                for _, row in group.iterrows():
                    satellite_name = row['子段卫星名称']
                    disruption_time = row['中断时长_parsed']
                    satellite_disruptions[satellite_name] = disruption_time
                
                # 添加到结果列表
                all_segment_data.append({
                    'start_time': start_time,
                    'segment_name': segment_name,
                    'satellites': satellite_disruptions
                })
        
        # 按理论开始时间排序（从小到大）
        all_segment_data.sort(key=lambda x: x['start_time'])
        
        # 构建最终输出格式
        all_results = []
        for item in all_segment_data:
            all_results.append({
                item['segment_name']: item['satellites']
            })
        
        return all_results

    def parse(self, text: str, context: Dict[str, Any] | None = None) -> Optional[IntentResult]:
        """解析文本，返回意图识别结果
        
        符合 matcher 统一接口规范
        
        **重要：按需触发机制**
        - 必须在 context 中设置 'trigger_excel': True 才会执行
        - 否则直接返回 None，避免无效的 Excel 读取
        
        Args:
            text: 未使用，保留以符合接口规范
            context: 上下文信息，包含：
                - trigger_excel: bool - **必须**设置为 True 才会执行 Excel 解析
                - execl_path: Excel 文件路径（可选，优先使用 context，否则使用配置默认值）
                - sheet_name: sheet 名称（可选，优先使用 context，否则使用配置默认值）
                - duration_threshold: 中断时长阈值（秒），默认 15.0
                - ignore_no_interruption: 是否忽略无中断，默认 True
                - excel_type: Excel 类型，'merged' 或 'standardized'，默认从配置读取
                - segment_pattern: 正则表达式用于匹配联通子段名称（用于 standardized 格式）
            
        Returns:
            IntentResult: 意图识别结果
                - intent: "excel_interruption_analysis"
                - confidence: 1.0
                - recognizer: "ExcelIntentRecognizer"
                - metadata: {
                    "execl_path": Excel 文件路径,
                    "sheet_name": sheet 名称,
                    "duration_threshold": 阈值（秒）,
                    "ignore_no_interruption": 是否忽略无中断,
                    "excel_type": Excel 类型,
                    "result_count": 记录数量,
                    "data": List[Dict[联通子段名称, Dict[子段卫星名称, 中断时长] 或 None]]
                  }
        
        Example:
            >>> # 不触发 Excel 解析
            >>> result = recognizer.parse("hello", context={})
            >>> result is None
            True
            
            >>> # 触发 Excel 解析
            >>> result = recognizer.parse("", context={
            ...     'trigger_excel': True,
            ...     'excel_type': 'merged'
            ... })
            >>> result.intent
            'excel_interruption_analysis'
        """
        if context is None:
            context = {}
        
        # **关键：按需触发机制**
        # 只有明确设置 trigger_excel 为 True 时才执行
        if not context.get('trigger_excel', False):
            return None
        
        # 获取 excel_type 并根据类型决定使用哪个配置
        excel_type = context.get('excel_type', self.default_excel_type)
        
        # 根据 excel_type 获取对应的配置
        if excel_type in self.excel_types_config:
            type_config = self.excel_types_config[excel_type]
            default_path = type_config.get('excel_path', '')
            default_sheet = type_config.get('sheet_name', '')
        else:
            # 如果配置中没有该类型，返回 None
            return None
        
        # 从 context 或配置中获取参数
        execl_path = context.get('execl_path', default_path)
        sheet_name = context.get('sheet_name', default_sheet)
        duration_threshold = context.get('duration_threshold', self.default_duration_threshold)
        ignore_no_interruption = context.get('ignore_no_interruption', self.default_ignore_no_interruption)
        segment_pattern = context.get('segment_pattern', self.segment_pattern)
        
        # 验证必要参数
        if not execl_path or not sheet_name:
            return None
        
        try:
            # 解析 sheet 数据
            parsed_data = self._parse_sheet_data(
                execl_path, 
                sheet_name, 
                duration_threshold, 
                ignore_no_interruption,
                excel_type,
                segment_pattern
            )
            
            # 构建 IntentResult
            return IntentResult(
                intent="excel_interruption_analysis",
                confidence=1.0,
                recognizer=self.name,
                metadata={
                    "execl_path": execl_path,
                    "sheet_name": sheet_name,
                    "duration_threshold": duration_threshold,
                    "ignore_no_interruption": ignore_no_interruption,
                    "excel_type": excel_type,
                    "result_count": len(parsed_data),
                    "data": parsed_data
                }
            )
        except Exception as e:
            # 如果发生错误，返回 None
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Excel parsing error: {e}")
            return None