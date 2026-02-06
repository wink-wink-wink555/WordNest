"""
AI助教服务 - 基于Agent的智能工作流
使用ReAct模式：Reasoning + Acting
"""
import json
import re
from typing import Generator, Dict, Any, List, Optional, Tuple
import requests
from flask import current_app
from models import db
from sqlalchemy import text


class AIService:
    """AI助教服务类 - Agent架构"""
    
    @staticmethod
    def get_database_schema() -> str:
        """
        获取数据库表结构信息
        
        Returns:
            数据库schema描述
        """
        schema = """
数据库表结构：

表1: word (单词表)
  - id: INTEGER PRIMARY KEY
  - word: VARCHAR(100) UNIQUE NOT NULL (单词内容)
  - marked: BOOLEAN DEFAULT FALSE (是否已标记/掌握)

表2: definition (定义表)
  - id: INTEGER PRIMARY KEY
  - word_id: INTEGER FOREIGN KEY (关联word.id)
  - part_of_speech: VARCHAR(20) NOT NULL (词性：noun, verb, adj等)
  - meaning: TEXT NOT NULL (中文释义)
  - example: TEXT (英文例句)
  - note: TEXT (备注信息)

关系：word 1:N definition (一个单词可以有多个定义)

常见查询场景：
1. 随机抽查：ORDER BY RANDOM() LIMIT N
2. 统计信息：COUNT(), SUM(), GROUP BY
3. 查询单词：WHERE word = 'xxx'
4. 已标记单词：WHERE marked = 1
5. JOIN查询：获取单词及其所有定义
"""
        return schema
    
    @staticmethod
    def call_llm(messages: List[Dict[str, str]], stream: bool = False) -> Any:
        """
        调用DeepSeek LLM
        
        Args:
            messages: 对话消息列表
            stream: 是否流式输出
            
        Returns:
            API响应（流式或完整）
        """
        api_key = current_app.config.get('DEEPSEEK_API_KEY')
        base_url = current_app.config.get('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')
        
        if not api_key:
            raise ValueError("未配置DEEPSEEK_API_KEY")
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': 'deepseek-chat',
            'messages': messages,
            'stream': stream,
            'temperature': 0.3,  # 降低温度以提高准确性
            'max_tokens': 2000
        }
        
        response = requests.post(
            f'{base_url}/v1/chat/completions',
            headers=headers,
            json=payload,
            stream=stream,
            timeout=30
        )
        
        if response.status_code != 200:
            raise Exception(f"API请求失败: {response.status_code}")
        
        return response
    
    @staticmethod
    def planner_agent(user_message: str) -> Dict[str, Any]:
        """
        Planner Agent - 分析用户意图，判断是否需要查询数据库
        
        Args:
            user_message: 用户输入
            
        Returns:
            计划结果 {
                'need_database': bool,
                'intent': str,
                'reasoning': str
            }
        """
        system_prompt = """你是一个意图分析专家。分析用户的问题，判断是否需要查询单词数据库。

数据库包含：
- 单词及其释义、例句、词性
- 单词的标记状态（是否已掌握）

需要查询数据库的情况：
1. 用户要求抽查/测试单词
2. 用户询问单词的释义、例句、用法
3. 用户询问学习进度、统计信息
4. 用户要求查看单词列表
5. 用户询问某个具体单词的信息

不需要查询数据库的情况：
1. 闲聊、问候
2. 询问学习方法、技巧（通用建议）
3. 询问单词的记忆法、词根词缀（通用知识）
4. 请求解释语法概念

请以JSON格式输出（仅输出JSON，不要其他内容）：
{
    "need_database": true/false,
    "intent": "用户意图的简短描述",
    "reasoning": "判断理由"
}"""
        
        try:
            messages = [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_message}
            ]
            
            response = AIService.call_llm(messages, stream=False)
            result = response.json()
            
            content = result['choices'][0]['message']['content']
            
            # 提取JSON（可能包含在markdown代码块中）
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
            if json_match:
                content = json_match.group(1)
            
            plan = json.loads(content)
            current_app.logger.info(f"Planner决策: {plan}")
            return plan
            
        except Exception as e:
            current_app.logger.error(f"Planner Agent错误: {e}")
            # 默认策略：如果解析失败，保守地认为需要查询
            return {
                'need_database': True,
                'intent': '解析失败，默认查询',
                'reasoning': str(e)
            }
    
    @staticmethod
    def sql_generator_agent(
        user_message: str, 
        conversation_history: List[Dict[str, Any]] = None
    ) -> str:
        """
        SQL Generator Agent - 根据用户问题生成SQL语句
        
        Args:
            user_message: 用户问题
            conversation_history: 对话历史（包含之前的SQL和结果）
            
        Returns:
            生成的SQL语句
        """
        schema = AIService.get_database_schema()
        
        history_context = ""
        if conversation_history:
            history_context = "\n之前的查询历史：\n"
            for i, item in enumerate(conversation_history, 1):
                history_context += f"\n查询{i}:\n"
                history_context += f"SQL: {item.get('sql', '')}\n"
                history_context += f"结果: {item.get('result_summary', '')}\n"
        
        system_prompt = f"""你是一个SQL专家。根据用户问题和数据库schema，生成准确的SQL查询语句。

{schema}

重要规则：
1. 只生成SELECT查询（不允许INSERT/UPDATE/DELETE）
2. 使用SQLite语法
3. 对于随机抽查，使用 ORDER BY RANDOM() LIMIT N
4. 需要JOIN时，使用 LEFT JOIN
5. 聚合字符串使用 GROUP_CONCAT()
6. 仅输出SQL语句，不要其他解释
7. 不要使用markdown代码块，直接输出SQL
{history_context}

用户问题：{user_message}

请生成SQL语句（仅输出SQL，不要任何解释）："""
        
        try:
            messages = [
                {'role': 'system', 'content': system_prompt}
            ]
            
            response = AIService.call_llm(messages, stream=False)
            result = response.json()
            
            sql = result['choices'][0]['message']['content'].strip()
            
            # 清理可能的markdown代码块
            sql = re.sub(r'```sql\s*', '', sql)
            sql = re.sub(r'```\s*', '', sql)
            sql = sql.strip()
            
            # 安全检查：确保只是SELECT语句
            sql_upper = sql.upper()
            if not sql_upper.startswith('SELECT'):
                raise ValueError("生成的不是SELECT查询")
            
            dangerous_keywords = ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER', 'CREATE']
            if any(keyword in sql_upper for keyword in dangerous_keywords):
                raise ValueError("SQL包含危险关键字")
            
            current_app.logger.info(f"生成的SQL: {sql}")
            return sql
            
        except Exception as e:
            current_app.logger.error(f"SQL Generator错误: {e}")
            raise
    
    @staticmethod
    def execute_sql(sql: str) -> Tuple[List[Dict[str, Any]], str]:
        """
        执行SQL查询
        
        Args:
            sql: SQL语句
            
        Returns:
            (查询结果列表, 结果摘要)
        """
        try:
            result = db.session.execute(text(sql))
            columns = result.keys()
            rows = [dict(zip(columns, row)) for row in result.fetchall()]
            
            # 生成结果摘要
            if not rows:
                summary = "查询返回0条结果"
            else:
                summary = f"查询返回{len(rows)}条结果"
                if len(rows) <= 3:
                    summary += f": {json.dumps(rows, ensure_ascii=False)}"
                else:
                    summary += f"，前3条: {json.dumps(rows[:3], ensure_ascii=False)}"
            
            current_app.logger.info(f"SQL执行成功: {summary}")
            return rows, summary
            
        except Exception as e:
            error_msg = f"SQL执行错误: {str(e)}"
            current_app.logger.error(error_msg)
            raise Exception(error_msg)
    
    @staticmethod
    def reflector_agent(
        user_message: str,
        query_results: List[Dict[str, Any]],
        conversation_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Reflector Agent - 分析查询结果，判断是否需要进一步查询
        
        Args:
            user_message: 用户原始问题
            query_results: 当前查询结果
            conversation_history: 对话历史
            
        Returns:
            反思结果 {
                'need_more_query': bool,
                'reasoning': str,
                'suggestion': str (如果需要更多查询，建议下一步做什么)
            }
        """
        results_summary = json.dumps(query_results[:5], ensure_ascii=False)  # 最多5条
        
        history_text = ""
        if conversation_history:
            history_text = "\n之前的查询：\n"
            for i, item in enumerate(conversation_history, 1):
                history_text += f"{i}. SQL: {item.get('sql', '')}\n   结果: {item.get('result_summary', '')}\n"
        
        system_prompt = f"""你是一个分析专家。判断当前的查询结果是否足够回答用户问题。

用户问题：{user_message}

当前查询结果：
{results_summary}
{history_text}

分析要点：
1. 结果是否为空？如果为空，可能需要调整查询条件
2. 结果是否完整？是否需要补充查询其他信息？
3. 对于复杂问题，是否需要多步查询？
4. 是否已经有足够信息来回答用户？

请以JSON格式输出（仅输出JSON）：
{{
    "need_more_query": true/false,
    "reasoning": "分析理由",
    "suggestion": "如果需要继续查询，建议下一步做什么"
}}"""
        
        try:
            messages = [
                {'role': 'system', 'content': system_prompt}
            ]
            
            response = AIService.call_llm(messages, stream=False)
            result = response.json()
            
            content = result['choices'][0]['message']['content']
            
            # 提取JSON
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
            if json_match:
                content = json_match.group(1)
            
            reflection = json.loads(content)
            current_app.logger.info(f"Reflector决策: {reflection}")
            return reflection
            
        except Exception as e:
            current_app.logger.error(f"Reflector Agent错误: {e}")
            # 默认：不再查询
            return {
                'need_more_query': False,
                'reasoning': f'解析失败: {str(e)}',
                'suggestion': ''
            }
    
    @staticmethod
    def format_data_for_llm(conversation_history: List[Dict[str, Any]]) -> str:
        """
        将查询历史格式化为LLM可读的上下文
        
        Args:
            conversation_history: 对话历史
            
        Returns:
            格式化的上下文字符串
        """
        if not conversation_history:
            return ""
        
        context = "\n数据库查询结果：\n"
        context += "=" * 50 + "\n"
        
        for i, item in enumerate(conversation_history, 1):
            context += f"\n查询 {i}：\n"
            context += f"SQL: {item.get('sql', '')}\n"
            
            results = item.get('results', [])
            if not results:
                context += "结果: 无数据\n"
            else:
                context += f"结果 ({len(results)}条记录):\n"
                # 格式化显示结果
                for j, row in enumerate(results[:10], 1):  # 最多显示10条
                    context += f"  {j}. {json.dumps(row, ensure_ascii=False)}\n"
                if len(results) > 10:
                    context += f"  ... (还有{len(results)-10}条)\n"
            
            context += "\n"
        
        context += "=" * 50 + "\n"
        return context
    
    @staticmethod
    def chat_stream(message: str, chat_history: List[Dict[str, str]] = None) -> Generator[str, None, None]:
        """
        智能对话流 - Agent工作流主函数
        
        工作流：
        1. Planner判断是否需要数据库
        2. 如果需要，SQL Generator生成SQL
        3. 执行SQL
        4. Reflector判断是否需要继续查询
        5. 重复2-4直到不需要更多查询
        6. 基于所有数据，生成最终回答（流式）
        
        Args:
            message: 用户消息
            chat_history: 对话历史 [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
            
        Yields:
            SSE格式的响应流
        """
        try:
            conversation_history = []
            max_iterations = 3  # 最多迭代3次查询
            
            # ===== Step 1: Planner Agent =====
            current_app.logger.info("=== Step 1: Planner Agent ===")
            plan = AIService.planner_agent(message)
            
            # ===== Step 2-4: 迭代查询（如果需要）=====
            if plan.get('need_database', False):
                current_app.logger.info("=== Step 2: 开始迭代查询流程 ===")
                
                for iteration in range(max_iterations):
                    current_app.logger.info(f"--- 迭代 {iteration + 1} ---")
                    
                    try:
                        # 生成SQL
                        sql = AIService.sql_generator_agent(message, conversation_history)
                        
                        # 执行SQL
                        results, summary = AIService.execute_sql(sql)
                        
                        # 记录到历史
                        conversation_history.append({
                            'sql': sql,
                            'results': results,
                            'result_summary': summary
                        })
                        
                        # 如果是最后一次迭代，直接结束
                        if iteration == max_iterations - 1:
                            break
                        
                        # 判断是否需要继续查询
                        reflection = AIService.reflector_agent(
                            message, 
                            results, 
                            conversation_history
                        )
                        
                        if not reflection.get('need_more_query', False):
                            current_app.logger.info("Reflector决定：无需更多查询")
                            break
                        
                        current_app.logger.info(f"Reflector决定：继续查询 - {reflection.get('suggestion', '')}")
                        
                    except Exception as e:
                        current_app.logger.error(f"查询迭代{iteration + 1}失败: {e}")
                        # 即使失败也继续，用已有的数据回答
                        break
            
            # ===== Step 5: 生成最终回答（流式）=====
            current_app.logger.info("=== Step 5: 生成最终回答 ===")
            
            # 构建上下文
            db_context = AIService.format_data_for_llm(conversation_history)
            
            system_prompt = f"""你是一个专业、友好的英语单词学习助教AI。

你的职责：
1. 根据数据库查询结果，准确回答用户问题
2. 对于抽查场景，逐个展示单词，让用户回忆
3. 提供鼓励和学习建议
4. 使用清晰的格式和适当的emoji

回答风格：
- 友好、耐心、专业
- 结构清晰（使用标题、列表等）
- 适当使用emoji增加趣味性
- 如果是抽查，要给用户思考空间

{db_context}"""
            
            # 构建消息列表，包含对话历史
            messages = [
                {'role': 'system', 'content': system_prompt}
            ]
            
            # 添加对话历史（如果有）
            if chat_history:
                messages.extend(chat_history)
            
            # 添加当前用户消息
            messages.append({'role': 'user', 'content': message})
            
            # 流式调用LLM
            response = AIService.call_llm(messages, stream=True)
            
            # 流式输出
            for line in response.iter_lines():
                if line:
                    line_text = line.decode('utf-8')
                    if line_text.startswith('data: '):
                        data = line_text[6:]
                        if data.strip() == '[DONE]':
                            yield 'data: [DONE]\n\n'
                            break
                        
                        try:
                            json_data = json.loads(data)
                            if 'choices' in json_data and len(json_data['choices']) > 0:
                                delta = json_data['choices'][0].get('delta', {})
                                content = delta.get('content', '')
                                if content:
                                    yield f'data: {json.dumps({"content": content}, ensure_ascii=False)}\n\n'
                        except json.JSONDecodeError:
                            continue
            
        except requests.exceptions.Timeout:
            yield 'data: {"content": "⏱️ 请求超时，请稍后重试"}\n\n'
            yield 'data: [DONE]\n\n'
        except requests.exceptions.RequestException as e:
            error_msg = f"🔌 网络请求错误: {str(e)}"
            current_app.logger.error(error_msg)
            yield f'data: {{"content": "{error_msg}"}}\n\n'
            yield 'data: [DONE]\n\n'
        except Exception as e:
            error_msg = f"❌ 处理请求时发生错误: {str(e)}"
            current_app.logger.error(error_msg)
            yield f'data: {{"content": "{error_msg}"}}\n\n'
            yield 'data: [DONE]\n\n'
