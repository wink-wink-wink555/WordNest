"""
AI助教路由
处理AI对话请求和流式响应
"""
from flask import Blueprint, render_template, request, Response, jsonify, stream_with_context
from services.ai_service import AIService
from chat_models import Conversation, Message
from models import db
from datetime import datetime


# 创建AI蓝图
ai_bp = Blueprint('ai', __name__, url_prefix='/ai')


@ai_bp.route('/tutor')
def ai_tutor():
    """
    AI助教页面
    
    Returns:
        渲染的AI助教页面
    """
    return render_template('ai_tutor.html')


@ai_bp.route('/chat_stream', methods=['POST'])
def chat_stream():
    """
    流式对话接口
    
    接收用户消息和对话历史，返回流式响应
    
    Returns:
        SSE流式响应
    """
    try:
        # 获取用户消息和对话历史
        data = request.get_json()
        message = data.get('message', '').strip()
        chat_history = data.get('chat_history', [])  # 对话历史
        conversation_id = data.get('conversation_id')  # 对话ID
        
        if not message:
            return jsonify({'error': '消息不能为空'}), 400
        
        # 保存用户消息到数据库
        if conversation_id:
            user_msg = Message(
                conversation_id=conversation_id,
                role='user',
                content=message,
                created_at=datetime.utcnow()
            )
            db.session.add(user_msg)
            db.session.commit()
        
        # 创建流式响应
        def generate():
            """生成器函数，用于流式输出"""
            assistant_response = ''
            try:
                for chunk in AIService.chat_stream(message, chat_history):
                    # 提取内容
                    if 'data: ' in chunk:
                        data_str = chunk.split('data: ')[1].strip()
                        if data_str != '[DONE]':
                            try:
                                import json
                                data_json = json.loads(data_str)
                                if 'content' in data_json:
                                    assistant_response += data_json['content']
                            except:
                                pass
                    yield chunk
                
                # 保存助手回复到数据库
                if conversation_id and assistant_response:
                    assistant_msg = Message(
                        conversation_id=conversation_id,
                        role='assistant',
                        content=assistant_response,
                        created_at=datetime.utcnow()
                    )
                    db.session.add(assistant_msg)
                    
                    # 更新对话的更新时间
                    conversation = Conversation.query.get(conversation_id)
                    if conversation:
                        conversation.updated_at = datetime.utcnow()
                    
                    db.session.commit()
                    
            except Exception as e:
                # 如果生成过程中出错，返回错误信息
                yield f'data: {{"content": "生成响应时出错: {str(e)}"}}\n\n'
                yield 'data: [DONE]\n\n'
        
        # 返回流式响应
        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no',
                'Connection': 'keep-alive'
            }
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@ai_bp.route('/conversations', methods=['GET'])
def get_conversations():
    """
    获取所有对话列表
    
    Returns:
        对话列表JSON
    """
    try:
        conversations = Conversation.query.order_by(Conversation.updated_at.desc()).all()
        return jsonify([conv.to_dict() for conv in conversations])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@ai_bp.route('/conversations', methods=['POST'])
def create_conversation():
    """
    创建新对话
    
    Returns:
        新建的对话信息JSON
    """
    try:
        data = request.get_json()
        title = data.get('title', '新对话')
        
        conversation = Conversation(
            title=title,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.session.add(conversation)
        db.session.commit()
        
        return jsonify(conversation.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@ai_bp.route('/conversations/<int:conversation_id>', methods=['GET'])
def get_conversation(conversation_id):
    """
    获取指定对话的详细信息（包括所有消息）
    
    Args:
        conversation_id: 对话ID
        
    Returns:
        对话详细信息JSON
    """
    try:
        conversation = Conversation.query.get_or_404(conversation_id)
        messages = Message.query.filter_by(conversation_id=conversation_id).order_by(Message.created_at.asc()).all()
        
        return jsonify({
            'conversation': conversation.to_dict(),
            'messages': [msg.to_dict() for msg in messages]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@ai_bp.route('/conversations/<int:conversation_id>', methods=['PUT'])
def update_conversation(conversation_id):
    """
    更新对话信息（如标题）
    
    Args:
        conversation_id: 对话ID
        
    Returns:
        更新后的对话信息JSON
    """
    try:
        conversation = Conversation.query.get_or_404(conversation_id)
        data = request.get_json()
        
        if 'title' in data:
            conversation.title = data['title']
        
        conversation.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify(conversation.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@ai_bp.route('/conversations/<int:conversation_id>', methods=['DELETE'])
def delete_conversation(conversation_id):
    """
    删除指定对话（包括所有消息）
    
    Args:
        conversation_id: 对话ID
        
    Returns:
        成功消息JSON
    """
    try:
        conversation = Conversation.query.get_or_404(conversation_id)
        db.session.delete(conversation)
        db.session.commit()
        
        return jsonify({'message': '对话已删除'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@ai_bp.route('/test', methods=['GET'])
def test():
    """
    测试接口，用于验证AI服务是否正常工作
    
    Returns:
        测试结果
    """
    try:
        # 测试数据库连接
        from models import Word
        word_count = Word.query.count()
        
        # 测试聊天数据库连接
        conversation_count = Conversation.query.count()
        
        return jsonify({
            'status': 'ok',
            'message': 'AI服务正常',
            'word_count': word_count,
            'conversation_count': conversation_count
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
