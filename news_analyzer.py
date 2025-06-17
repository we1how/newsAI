from datetime import datetime, timezone
import os
import time
import json
from openai import OpenAI
import newsRss
import re
from json.decoder import JSONDecodeError

# 全局配置文件路径
ANALYSIS_FILE = "news_analysis.json"

def get_volcengine_client():
    return OpenAI(
        api_key='ba7b3e16-d8dc-4376-9003-ae52013e3506',
        base_url="https://ark.cn-beijing.volces.com/api/v3",
    )




def fix_json_format(json_str):
    """尝试修复常见的JSON格式错误，包括字段值引号缺失和对象闭合问题"""
    # 尝试直接解析
    try:
        return json.loads(json_str)
    except JSONDecodeError:
        pass  # 继续尝试修复
    
    # 修复1: 确保整个对象闭合
    open_braces = json_str.count('{')
    close_braces = json_str.count('}')
    if open_braces > close_braces:
        json_str += '}' * (open_braces - close_braces)
    
    # 修复2: 处理所有字段值缺失引号的问题
    # 匹配模式：字段名后跟冒号，然后是未用引号包围的值
    field_pattern = r'("(?:stock|impact|reason|summary)":\s*)([^"][^,}\]\n]*)'
    
    # 多次尝试修复，直到解析成功或无法进一步修复
    for _ in range(3):  # 最多尝试3次修复
        try:
            # 查找所有需要修复的字段
            fixed_str = json_str
            for match in re.finditer(field_pattern, json_str):
                prefix = match.group(1)
                bad_value = match.group(2).strip()
                
                # 跳过已经是字符串的值
                if bad_value.startswith('"') and bad_value.endswith('"'):
                    continue
                
                # 修复值：添加引号并转义内部的双引号
                fixed_value = f'"{bad_value.replace("\\", "\\\\").replace("\"", "\\\"")}"'
                fixed_str = fixed_str.replace(
                    prefix + bad_value,
                    prefix + fixed_value
                )
            
            # 尝试解析修复后的JSON
            return json.loads(fixed_str)
        except JSONDecodeError as e:
            # 如果仍然失败，尝试截取到最后一个有效位置
            if e.pos > 0:
                # 尝试截取到错误位置之前的内容
                fixed_str = fixed_str[:e.pos]
                # 确保对象闭合
                if fixed_str.count('{') > fixed_str.count('}'):
                    fixed_str += '}'
            json_str = fixed_str  # 为下一次迭代准备
    
    # 最终尝试解析
    try:
        return json.loads(json_str)
    except JSONDecodeError:
        # 终极修复：提取可能有效的部分
        matches = list(re.finditer(r'\{.*?\}', json_str, re.DOTALL))
        if matches:
            try:
                return json.loads(matches[-1].group(0))
            except JSONDecodeError:
                pass
        
        return None

def analyze_news_with_volcengine(news_item):
    """使用火山方舟API分析新闻"""
    client = get_volcengine_client()
    
    # 构建提示词
    prompt = f"""
请分析以下新闻内容，完成以下任务：
1. 将新闻内容总结成一句话；
2. 判断分析该新闻对国内哪些具体股票有影响，并分析其影响是利好还是利空，给出具体的理由；
3. 可以有多个股票分析,按以下JSON格式返回结果：
{{
    "summary": "新闻的一句话总结",
    "analysis": [
        {{
            "stock": "股票名称",
            "impact": "利好/利空",
            "reason": "影响理由"
        }}
    ]
}}；

4. 以下是要分析的新闻内容：
{news_item['content'][:3000]}  // 限制长度
"""
    
    try:
        response = client.chat.completions.create(
            model="deepseek-r1-250528",
            messages=[
                {"role": "system", "content": "你是一个十分顶级专业的大师级金融分析师、股票专家，擅长从新闻中识别对股票的影响，并且不遗余力地给出专业的分析和建议。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=500
        )
        
        # 提取模型回复
        result_text = response.choices[0].message.content
        
        # 尝试解析JSON
        try:
            # 查找JSON部分
            json_start = result_text.find('{')
            json_end = result_text.rfind('}') + 1
            json_str = result_text[json_start:json_end]
            
            # 使用修复函数解析
            result = fix_json_format(json_str)
            
            if result is None:
                print(f"JSON解析失败: {result_text}")
                return {
                    "summary": "解析失败",
                    "analysis": []
                }
            
            return result
        except Exception as e:
            print(f"JSON解析失败: {str(e)}")
            return {
                "summary": "解析失败",
                "analysis": []
            }
    
    except Exception as e:
        print(f"API调用失败: {str(e)}")
        return {
            "summary": "API调用失败",
            "analysis": []
        }

def load_analysis_data():
    """加载已有的分析结果"""
    if not os.path.exists(ANALYSIS_FILE):
        return []
    
    try:
        with open(ANALYSIS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"加载分析数据失败: {str(e)}")
        return []

def save_analysis_data(data):
    """保存分析结果到文件"""
    with open(ANALYSIS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def analyze_new_news():
    """分析新新闻并保存结果"""
    RSS_URL = "https://rsshub.app/cls/depth/1000"
    
    print("正在获取财联社新新闻...")
    new_news = newsRss.fetch_cls_news(RSS_URL)
    
    if not new_news:
        print("没有新的新闻需要分析")
        return []
    
    print(f"获取到 {len(new_news)} 条新新闻，开始分析...")
    
    # 分析新新闻
    analysis_results = []
    analyzed_links = []
    
    for i, news in enumerate(new_news, 1):
        print(f"分析新闻 {i}/{len(new_news)}: {news['title']}")
        
        # 调用火山模型分析
        analysis_result = analyze_news_with_volcengine(news)
        
        # 合并原始新闻数据和分析结果
        combined = {
            "news": news,
            "analysis": analysis_result,
            "analyzed_at": datetime.now(timezone.utc).isoformat()
        }
        analysis_results.append(combined)
        if analysis_result.get("analysis") != []:
            # 记录已分析的链接
            analyzed_links.append(news["link"])
        
        # 打印当前结果
        print(f"  总结: {analysis_result.get('summary', '')}")
        # for stock_analysis in analysis_result.get('analysis', []):
        #     print(f"  股票: {stock_analysis.get('stock', '')} | 影响: {stock_analysis.get('impact', '')}")
        #     print(f"  理由: {stock_analysis.get('reason', '')}")
        print("-" * 80)
        
        # 避免请求过快
        time.sleep(1)
    
    if analysis_results:
        # 保存分析结果
        existing_data = load_analysis_data()
        updated_data = analysis_results + existing_data
        save_analysis_data(updated_data)
        
        # 标记链接为已分析
        newsRss.mark_links_as_analyzed(analyzed_links)
        
        print(f"成功分析并保存 {len(analysis_results)} 条新新闻")
    
    return analysis_results

def get_latest_news_analysis(max_items=5):
    """获取最新的新闻分析"""
    data = load_analysis_data()
    if not data:
        return []
    
    # 按分析时间排序（最新的在前）
    data.sort(key=lambda x: x.get("analyzed_at", ""), reverse=True)
    
    return data[:max_items]

if __name__ == "__main__":
    analyze_new_news()