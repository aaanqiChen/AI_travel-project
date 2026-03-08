import re
import jieba
from typing import List, Dict, Any

def extract_travel_handbook_struct(markdown: str) -> List[Dict[str, Any]]:
    """
    从AI Markdown内容中提取多方案结构化信息：
    - 方案名
    - 方案特色
    - 每日行程（按天分组）
    - 餐饮推荐
    - 住宿推荐
    - 天气信息
    - 费用预估
    - 注意事项
    """
    # 1. 按方案分割，兼容# 南京一日游方案、## 方案一：xxx之旅、## 方案二：xxx之旅等
    # 先找主标题（如# 南京一日游方案），再找所有## 方案X：xxx之旅
    plan_blocks = re.split(r'(?m)^##? ?方案[一二三四五六七八九十1234567890]+：?(.+?)(?:之旅)?\s*$', markdown)
    plans = []
    if len(plan_blocks) > 1:
        # 有多个方案
        for i in range(1, len(plan_blocks), 2):
            plan_name = plan_blocks[i].strip()
            plan_content = plan_blocks[i+1]
            # 2. 按大标题分割，兼容### 1. 方案特色、### 2. 每日详细安排等
            sections = re.split(r'(?m)^###? ?(\d+\. )?([\u4e00-\u9fa5A-Za-z0-9]+)', plan_content)
            struct = {'name': plan_name, 'sections': {}, 'days': []}
            for j in range(1, len(sections), 3):
                sec_title = sections[j+1].strip()
                sec_content = sections[j+2]
                if '每日详细安排' in sec_title:
                    # 3. 按天分割，兼容- **第N天：YYYY-MM-DD**
                    day_blocks = re.split(r'(?m)^- \*\*第(\d+)天：?([0-9\-]*)\*\*', sec_content)
                    idx = 1
                    while idx < len(day_blocks):
                        if idx+2 <= len(day_blocks):
                            day_num = day_blocks[idx]
                            day_title = day_blocks[idx+1]
                            day_content = day_blocks[idx+2]
                            struct['days'].append({
                                'day_num': day_num,
                                'day_title': day_title.strip() if day_title else '',
                                'content': day_content if day_content else ''
                            })
                        idx += 3
                else:
                    struct['sections'][sec_title] = sec_content.strip()
            plans.append(struct)
    else:
        # 只有一个方案，兼容# xxx之旅
        plan_blocks = re.split(r'(?m)^# ?(?:\[)?(.+?)(?:\])? ?之旅', markdown)
        for i in range(1, len(plan_blocks), 2):
            plan_name = plan_blocks[i].strip()
            plan_content = plan_blocks[i+1]
            sections = re.split(r'(?m)^##? (\d+\. )?([\u4e00-\u9fa5A-Za-z0-9]+)', plan_content)
            struct = {'name': plan_name, 'sections': {}, 'days': []}
            for j in range(1, len(sections), 3):
                sec_title = sections[j+1].strip()
                sec_content = sections[j+2]
                if '每日详细安排' in sec_title:
                    day_blocks = re.split(r'(?m)^(?:\s*##+\s*(?:第|Day|DAY|)?\s*(\d+)[天日]?(?:[:：\- ]+.*)?\s*$|\s*[-*•]+\s*\*\*第(\d+)天[:：\- ]*([0-9\-]*)\*\*)', sec_content)
                    idx = 1
                    while idx < len(day_blocks):
                        if day_blocks[idx] and day_blocks[idx].isdigit():
                            day_num = day_blocks[idx]
                            day_title = day_blocks[idx+1] if idx+1 < len(day_blocks) else ''
                            day_content = day_blocks[idx+2] if idx+2 < len(day_blocks) else ''
                            idx += 3
                        elif idx+2 < len(day_blocks) and day_blocks[idx+1] and day_blocks[idx+1].isdigit():
                            day_num = day_blocks[idx+1]
                            day_title = day_blocks[idx+2] if idx+2 < len(day_blocks) else ''
                            day_content = day_blocks[idx+3] if idx+3 < len(day_blocks) else ''
                            idx += 4
                        else:
                            break
                        struct['days'].append({
                            'day_num': day_num,
                            'day_title': day_title.strip() if day_title else '',
                            'content': day_content if day_content else ''
                        })
                else:
                    struct['sections'][sec_title] = sec_content.strip()
            plans.append(struct)
    return plans 