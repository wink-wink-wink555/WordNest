"""
单词相关路由
"""
import random
import csv
from io import StringIO
import tempfile
import pyttsx3
from flask import Blueprint, render_template, jsonify, request, redirect, url_for, Response, send_file, send_from_directory
from services import WordService, LLMService
from utils import load_settings, save_settings, ENCOURAGEMENT_MESSAGES


word_bp = Blueprint('word', __name__)


@word_bp.route('/favicon.ico')
def favicon():
    """返回favicon图标（简单的空响应避免404）"""
    return '', 204


@word_bp.route('/')
def index():
    """主页"""
    # 随机选择一条鼓励话语
    encouragement = random.choice(ENCOURAGEMENT_MESSAGES)
    return render_template('index.html', encouragement=encouragement)


@word_bp.route('/get_random_word')
def get_random_word():
    """获取随机单词"""
    # 获取上一次的单词
    prev_word = request.args.get('prev_word', '')
    
    # 加载设置，检查是否只抽查标注单词
    settings = load_settings()
    marked_only = settings.get('marked_only', False)
    
    # 获取随机单词
    random_word = WordService.get_random_word(prev_word, marked_only)
    
    if not random_word:
        # 检查是否是因为没有单词还是没有标注的单词
        all_words = WordService.get_all_words()
        if not all_words:
            return jsonify({
                'error': '当前列表为空',
                'word': '暂无单词'
            })
        else:
            return jsonify({
                'error': '没有标注的单词',
                'word': 'No marked words'
            })
    
    # 返回单词但不返回定义
    return jsonify({
        'word': random_word.word
    })


@word_bp.route('/get_marked_only_status')
def get_marked_only_status():
    """获取是否只抽查标注单词的设置"""
    settings = load_settings()
    return jsonify({'marked_only': settings.get('marked_only', False)})


@word_bp.route('/toggle_marked_only', methods=['POST'])
def toggle_marked_only():
    """切换是否只抽查标注单词的设置"""
    data = request.json
    settings = load_settings()
    settings['marked_only'] = data.get('marked_only', False)
    save_settings(settings)
    return jsonify({'success': True})


@word_bp.route('/get_word_definition/<word>')
def get_word_definition(word):
    """获取指定单词的定义"""
    word_data = WordService.find_word(word)
    if word_data:
        return jsonify(word_data.to_dict())
    return jsonify({'error': '未找到该单词'}), 404


@word_bp.route('/is_word_marked/<word>')
def is_word_marked(word):
    """检查单词是否被标记"""
    word_data = WordService.find_word(word)
    if word_data:
        return jsonify({'marked': word_data.marked})
    return jsonify({'error': '未找到该单词'}), 404


@word_bp.route('/mark_word/<word>', methods=['POST'])
def mark_word(word):
    """标记单词"""
    if WordService.mark_word(word, marked=True):
        return jsonify({'success': True})
    return jsonify({'error': '未找到该单词'}), 404


@word_bp.route('/unmark_word/<word>', methods=['POST'])
def unmark_word(word):
    """取消标记单词"""
    if WordService.mark_word(word, marked=False):
        return jsonify({'success': True})
    return jsonify({'error': '未找到该单词'}), 404


@word_bp.route('/word_list')
def word_list():
    """单词列表页面"""
    words = WordService.get_words_with_definitions()
    return render_template('word_list.html', words=words)


@word_bp.route('/add_word', methods=['GET', 'POST'])
def add_word():
    """添加新单词"""
    if request.method == 'GET':
        return render_template('add_word.html')
    
    # 处理POST请求
    data = request.json
    
    # 检查单词是否为空
    if not data['word'] or data['word'].strip() == '':
        return jsonify({'error': '单词不能为空'}), 400
    
    # 添加单词
    if not WordService.add_word(data['word'], data['definitions']):
        return jsonify({'error': '单词已存在'}), 400
    
    return jsonify({'success': True})


@word_bp.route('/edit_word/<word>', methods=['GET', 'POST'])
def edit_word(word):
    """编辑单词"""
    if request.method == 'GET':
        word_data = WordService.find_word(word)
        if not word_data:
            return redirect(url_for('word.word_list'))
        return render_template('edit_word.html', word=word_data.to_dict())
    
    # 处理POST请求
    data = request.json
    
    if not WordService.update_word(word, data['word'], data['definitions']):
        return jsonify({'error': '更新失败，可能是单词已存在'}), 400
    
    return jsonify({'success': True})


@word_bp.route('/add_definition/<word>', methods=['GET', 'POST'])
def add_definition(word):
    """为单词添加新的定义"""
    if request.method == 'GET':
        word_data = WordService.find_word(word)
        if not word_data:
            return redirect(url_for('word.word_list'))
        return render_template('add_definition.html', word=word_data.to_dict())
    
    # 处理POST请求
    data = request.json
    
    if not WordService.add_definition(word, data):
        return jsonify({'error': '未找到该单词'}), 404
    
    return jsonify({'success': True})


@word_bp.route('/delete_word/<word>', methods=['GET', 'POST'])
def delete_word(word):
    """删除单词"""
    if not WordService.delete_word(word):
        return jsonify({'error': '未找到该单词'}), 404
    
    if request.method == 'GET':
        return redirect(url_for('word.word_list'))
    return jsonify({'success': True})


@word_bp.route('/export_words')
def export_words():
    """导出单词列表为CSV，支持筛选和排序"""
    # 获取筛选和排序参数
    sort_alphabetically = request.args.get('sort', 'false') == 'true'
    show_marked_only = request.args.get('marked_only', 'false') == 'true'
    
    # 获取筛选和排序后的单词
    words = WordService.get_filtered_words(show_marked_only, sort_alphabetically)
    
    output = StringIO()
    # 添加BOM标记以确保Excel正确识别UTF-8编码
    output.write('\ufeff')
    writer = csv.writer(output)
    
    # 写入表头
    writer.writerow(['单词', '词性', '释义', '例句', '笔记', '是否标注'])
    
    # 写入单词数据
    for word in words:
        for definition in word.definitions:
            writer.writerow([
                word.word,
                definition.part_of_speech,
                definition.meaning,
                definition.example,
                definition.note,
                '是' if word.marked else '否'
            ])
    
    # 准备响应
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment;filename=words.csv"}
    )


@word_bp.route('/generate_example', methods=['POST'])
def generate_example():
    """使用大模型生成例句"""
    data = request.json
    word = data.get('word', '')
    part_of_speech = data.get('part_of_speech', '')
    meaning = data.get('meaning', '')
        
    if not word or not meaning:
        return jsonify({'error': '参数不足'}), 400
    
    example = LLMService.generate_example(word, part_of_speech, meaning)
    
    if example:
        return jsonify({'example': example})
    else:
        return jsonify({'error': '生成例句失败'}), 500


@word_bp.route('/generate_note', methods=['POST'])
def generate_note():
    """使用大模型生成笔记"""
    data = request.json
    word = data.get('word', '')
    part_of_speech = data.get('part_of_speech', '')
    meaning = data.get('meaning', '')
        
    if not word or not meaning:
        return jsonify({'error': '参数不足'}), 400
    
    note = LLMService.generate_note(word, part_of_speech, meaning)
    
    if note:
        return jsonify({'note': note})
    else:
        return jsonify({'error': '生成笔记失败'}), 500


@word_bp.route('/ai_fill_word', methods=['POST'])
def ai_fill_word():
    """使用AI一键填充单词的完整信息（支持多重释义）"""
    data = request.json
    word = data.get('word', '')
    
    if not word:
        return jsonify({'error': '请输入单词'}), 400
    
    # 调用LLM服务生成完整的单词信息
    word_info = LLMService.generate_full_word_info(word)
    
    if not word_info:
        return jsonify({'error': 'AI生成失败，请检查网络连接或稍后重试'}), 500
    
    # 检查是否有错误信息
    if 'error' in word_info:
        return jsonify(word_info), 400
    
    # 成功返回词条信息
    if 'definitions' in word_info:
        return jsonify(word_info)
    else:
        return jsonify({'error': 'AI返回数据格式错误'}), 500


@word_bp.route('/get_word_details/<word>')
def get_word_details(word):
    """获取单词详情（包括前后单词）"""
    details = WordService.get_word_details(word)
    
    if details:
        return jsonify(details)
    return jsonify({'error': '未找到该单词'}), 404


@word_bp.route('/speak_word/<word>')
def speak_word(word):
    """生成并返回单词语音"""
    try:
        # 初始化文本转语音引擎
        engine = pyttsx3.init()
        
        # 设置语音属性
        engine.setProperty('rate', 150)  # 语速
        engine.setProperty('volume', 1.0)  # 音量
        
        # 创建临时文件用于保存语音
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
            temp_filename = temp_file.name
        
        # 生成语音文件
        engine.save_to_file(word, temp_filename)
        engine.runAndWait()
        
        # 返回音频文件
        return send_file(
            temp_filename,
            mimetype='audio/mpeg',
            as_attachment=True,
            download_name=f"{word}.mp3"
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

