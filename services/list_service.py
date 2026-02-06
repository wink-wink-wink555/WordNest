"""
单词列表管理服务层
处理多个单词列表的创建、切换、重命名和删除
"""
import os
from flask import current_app
from models import db, Word


class ListService:
    """单词列表服务类"""
    
    @staticmethod
    def get_instance_folder():
        """获取instance文件夹路径"""
        return current_app.config.get('INSTANCE_FOLDER') or os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance')
    
    @staticmethod
    def get_all_lists():
        """
        获取所有单词列表
        
        Returns:
            列表信息的列表，每项包含名称和单词数量
        """
        instance_folder = ListService.get_instance_folder()
        
        if not os.path.exists(instance_folder):
            os.makedirs(instance_folder)
        
        lists = []
        
        # 遍历instance文件夹中的所有.db文件
        for filename in os.listdir(instance_folder):
            if filename.endswith('.db'):
                list_name = filename[:-3]  # 去掉.db后缀
                db_path = os.path.join(instance_folder, filename)
                
                # 获取该列表的单词数量
                word_count = ListService.get_word_count_in_list(list_name)
                
                lists.append({
                    'name': list_name,
                    'word_count': word_count,
                    'db_path': db_path
                })
        
        # 按名称排序
        lists.sort(key=lambda x: x['name'])
        
        return lists
    
    @staticmethod
    def get_word_count_in_list(list_name):
        """
        获取指定列表中的单词数量
        
        Args:
            list_name: 列表名称
            
        Returns:
            单词数量
        """
        instance_folder = ListService.get_instance_folder()
        db_path = os.path.join(instance_folder, f'{list_name}.db')
        
        if not os.path.exists(db_path):
            return 0
        
        # 临时连接到该数据库查询单词数量
        from sqlalchemy import create_engine, text
        engine = create_engine(f'sqlite:///{db_path}')
        
        try:
            with engine.connect() as conn:
                result = conn.execute(text('SELECT COUNT(*) FROM word')).scalar()
                return result or 0
        except:
            # 如果表不存在或数据库损坏，返回0
            return 0
        finally:
            engine.dispose()
    
    @staticmethod
    def create_list(list_name):
        """
        创建新的单词列表
        
        Args:
            list_name: 列表名称
            
        Returns:
            创建成功返回True，列表已存在返回False
        """
        # 验证列表名称
        if not list_name or list_name.strip() == '':
            return False
        
        # 清理列表名称（移除非法字符）
        list_name = list_name.strip()
        invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for char in invalid_chars:
            list_name = list_name.replace(char, '')
        
        if not list_name:
            return False
        
        instance_folder = ListService.get_instance_folder()
        db_path = os.path.join(instance_folder, f'{list_name}.db')
        
        # 检查列表是否已存在
        if os.path.exists(db_path):
            return False
        
        # 创建新的数据库文件
        from sqlalchemy import create_engine, MetaData
        from models import Word, Definition
        
        # 创建 SQLite 数据库引擎
        engine = create_engine(f'sqlite:///{db_path}')
        
        # 使用 SQLAlchemy 创建表结构
        # 直接使用模型的元数据来创建表
        try:
            # 获取 db.Model 的元数据并创建所有表
            db.metadata.create_all(bind=engine)
            engine.dispose()
            
            # 验证文件是否创建成功
            if os.path.exists(db_path):
                return True
            else:
                return False
        except Exception as e:
            print(f"创建列表失败: {e}")
            if os.path.exists(db_path):
                try:
                    os.remove(db_path)
                except:
                    pass
            return False
    
    @staticmethod
    def rename_list(old_name, new_name):
        """
        重命名单词列表
        
        Args:
            old_name: 原列表名称
            new_name: 新列表名称
            
        Returns:
            重命名成功返回True，失败返回False
        """
        print(f"[ListService] 开始重命名: '{old_name}' -> '{new_name}'")
        
        # 验证新列表名称
        if not new_name or new_name.strip() == '':
            print("[ListService] 错误：新名称为空")
            return False
        
        # 清理列表名称
        new_name = new_name.strip()
        invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for char in invalid_chars:
            new_name = new_name.replace(char, '')
        
        if not new_name:
            print("[ListService] 错误：清理后新名称为空")
            return False
        
        instance_folder = ListService.get_instance_folder()
        old_path = os.path.join(instance_folder, f'{old_name}.db')
        new_path = os.path.join(instance_folder, f'{new_name}.db')
        
        print(f"[ListService] 旧路径: {old_path}")
        print(f"[ListService] 新路径: {new_path}")
        print(f"[ListService] 旧路径存在: {os.path.exists(old_path)}")
        print(f"[ListService] 新路径存在: {os.path.exists(new_path)}")
        
        # 检查原列表是否存在
        if not os.path.exists(old_path):
            print("[ListService] 错误：原列表不存在")
            return False
        
        # 检查新名称是否已被占用
        if os.path.exists(new_path):
            print("[ListService] 错误：新名称已被占用")
            return False
        
        # 在Windows上，确保数据库连接已关闭
        try:
            from models import db
            
            print("[ListService] 关闭数据库连接...")
            
            # 移除session
            db.session.remove()
            
            # 如果存在引擎，先dispose
            if hasattr(db, 'engines') and db.engines:
                for key, engine in list(db.engines.items()):
                    if engine:
                        engine_url = str(engine.url)
                        print(f"[ListService] 检查引擎 {key}: {engine_url}")
                        # 检查是否是我们要重命名的数据库
                        if f'{old_name}.db' in engine_url:
                            print(f"[ListService] 关闭引擎: {key}")
                            engine.dispose()
            
            # 强制垃圾回收，确保所有连接都被释放
            import gc
            gc.collect()
            
            # Windows上给系统一点时间来释放文件句柄
            import time
            time.sleep(0.1)
            
        except Exception as e:
            print(f"[ListService] 关闭数据库连接时警告: {e}")
            import traceback
            traceback.print_exc()
        
        # 重命名文件
        try:
            print("[ListService] 执行重命名...")
            os.rename(old_path, new_path)
            print("[ListService] 重命名成功")
            return True
        except PermissionError as e:
            print(f"[ListService] 权限错误: {e}")
            print("[ListService] 提示：数据库文件可能正在被使用")
            return False
        except Exception as e:
            print(f"[ListService] 重命名失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    @staticmethod
    def delete_list(list_name):
        """
        删除单词列表（只有当列表为空时才能删除）
        
        Args:
            list_name: 列表名称
            
        Returns:
            删除成功返回True，失败返回False（列表不存在或不为空）
        """
        instance_folder = ListService.get_instance_folder()
        db_path = os.path.join(instance_folder, f'{list_name}.db')
        
        # 检查列表是否存在
        if not os.path.exists(db_path):
            return False
        
        # 检查列表是否为空
        word_count = ListService.get_word_count_in_list(list_name)
        if word_count > 0:
            return False
        
        # 删除数据库文件
        try:
            os.remove(db_path)
            return True
        except Exception as e:
            print(f"删除列表失败: {e}")
            return False
    
    @staticmethod
    def list_exists(list_name):
        """
        检查列表是否存在
        
        Args:
            list_name: 列表名称
            
        Returns:
            存在返回True，不存在返回False
        """
        instance_folder = ListService.get_instance_folder()
        db_path = os.path.join(instance_folder, f'{list_name}.db')
        return os.path.exists(db_path)
    
    @staticmethod
    def get_default_list():
        """
        获取默认列表名称（如果words.db存在，返回words，否则返回第一个列表或None）
        
        Returns:
            默认列表名称
        """
        instance_folder = ListService.get_instance_folder()
        
        # 如果words.db存在，返回words作为默认列表
        if os.path.exists(os.path.join(instance_folder, 'words.db')):
            return 'words'
        
        # 否则返回第一个列表
        lists = ListService.get_all_lists()
        if lists:
            return lists[0]['name']
        
        # 如果没有任何列表，创建一个默认的words列表
        ListService.create_list('words')
        return 'words'

