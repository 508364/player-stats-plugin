PLUGIN_METADATA = {
    'id': 'player_stats',
    'version': '1.0.0',
    'name': 'Player Stats Plugin',
    'description': 'A plugin for MCDR that tracks and displays player statistics',
    'author': 'Your Name',
    'link': 'https://github.com/yourusername/player-stats-plugin',
    'dependencies': {
        'mcdreforged': '>=2.0.0'
    }
}

from mcdreforged.api.all import *
import os
import sys
import json
import time
from datetime import datetime, timedelta

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 全局变量
timer = None
enabled = True

def find_config_directory():
    """找到config文件夹"""
    # 获取当前脚本所在目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 检查当前目录是否有config文件夹
    config_dir = os.path.join(current_dir, 'config')
    if os.path.exists(config_dir) and os.path.isdir(config_dir):
        return config_dir
    
    # 检查上一级目录
    parent_dir = os.path.dirname(current_dir)
    config_dir = os.path.join(parent_dir, 'config')
    if os.path.exists(config_dir) and os.path.isdir(config_dir):
        return config_dir
    
    # 如果都没有，在当前目录创建config文件夹
    config_dir = os.path.join(current_dir, 'config')
    os.makedirs(config_dir, exist_ok=True)
    return config_dir

def get_config_path():
    """获取配置文件路径"""
    config_dir = find_config_directory()
    player_stats_dir = os.path.join(config_dir, 'player_stats')
    os.makedirs(player_stats_dir, exist_ok=True)
    return os.path.join(player_stats_dir, 'config.json')

def load_config():
    """加载配置文件"""
    config_path = get_config_path()
    
    # 如果配置文件不存在，创建默认配置
    if not os.path.exists(config_path):
        default_config = {
            "github": {
                "token": "",
                "repo_owner": "",
                "repo_name": "",
                "repo_path": "",
                "file_path": "ranking.md",
                "branch": "main"
            },
            "ranking_names": {
                "minecraft:play_time": "在线时长最长",
                "minecraft:walk_one_cm": "步行距离最远",
                "minecraft:fly_one_cm": "飞行距离最远",
                "minecraft:swim_one_cm": "游泳距离最远",
                "minecraft:jump": "跳跃次数最多",
                "minecraft:mob_kills": "杀死生物最多",
                "minecraft:damage_taken": "受到伤害最多",
                "minecraft:blocks_broken": "破坏方块最多"
            },
            "update": {
                "enabled": True,
                "interval": 3600,
                "use_daily": False,
                "daily_time": 8.5
            },
            "plugin": {
                "enabled": True
            }
        }
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)
        return default_config
    
    # 加载配置文件
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        import logging
        logging.error(f"加载配置文件时出错: {e}")
        return {}

def save_config(config):
    """保存配置文件"""
    config_path = get_config_path()
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        import logging
        logging.error(f"保存配置文件时出错: {e}")
        return False

def on_load(server, prev):
    global enabled
    server.logger.info('Player Stats Plugin loaded')
    
    # 加载配置
    config = load_config()
    enabled = config.get('plugin', {}).get('enabled', True)
    
    # 注册帮助信息
    server.register_help_message('!!player_stats', '显示玩家统计数据')
    server.register_help_message('!!player_stats ranking', '显示排行榜')
    server.register_help_message('!!player_stats upload', '上传排行榜到GitHub')
    server.register_help_message('!!player_stats reload', '重新加载配置')
    server.register_help_message('!!player_stats enable', '启用插件')
    server.register_help_message('!!player_stats disable', '禁用插件')
    server.register_help_message('!!player_stats refresh', '重新获取玩家列表')
    
    # 注册命令
    register_commands(server)
    
    # 启动定时任务
    if enabled:
        start_timer(server)

def on_unload(server):
    global timer
    if timer:
        server.cancel_task(timer)
        timer = None
    server.logger.info('Player Stats Plugin unloaded')

def register_commands(server):
    """注册插件命令"""
    root = Literal('!!player_stats')
    root = root.then(Literal('ranking').runs(lambda src: show_ranking(src)))
    root = root.then(Literal('upload').runs(lambda src: upload_ranking(src)))
    root = root.then(Literal('reload').runs(lambda src: reload_config(src, server)))
    root = root.then(Literal('enable').runs(lambda src: enable_plugin(src, server)))
    root = root.then(Literal('disable').runs(lambda src: disable_plugin(src, server)))
    root = root.then(Literal('refresh').runs(lambda src: refresh_players(src)))
    root = root.runs(lambda src: show_help(src))
    
    server.register_command(root)

def show_help(src):
    """显示帮助信息"""
    # 处理编码兼容问题
    help_text = '''
Player Stats Plugin 帮助信息：
!!player_stats - 显示此帮助信息
!!player_stats ranking - 显示玩家排行榜
!!player_stats upload - 上传排行榜到GitHub
!!player_stats reload - 重新加载配置
!!player_stats enable - 启用插件
!!player_stats disable - 禁用插件
!!player_stats refresh - 重新获取玩家列表
'''
    try:
        src.reply(help_text)
    except UnicodeEncodeError:
        # 处理编码问题
        src.reply(help_text.encode('utf-8', 'replace').decode('gbk', 'replace'))

def show_ranking(src):
    """显示排行榜"""
    from .generate_ranking_md import generate_ranking_md
    
    try:
        generate_ranking_md()
        reply = '排行榜已更新，请查看 ranking.md 文件'
        src.reply(reply)
    except Exception as e:
        error_msg = f'生成排行榜时出错: {e}'
        try:
            src.reply(error_msg)
        except UnicodeEncodeError:
            src.reply(error_msg.encode('utf-8', 'replace').decode('gbk', 'replace'))

def upload_ranking(src):
    """上传排行榜到GitHub"""
    from .update_and_upload_ranking import main
    
    try:
        reply = '开始上传排行榜到GitHub...'
        src.reply(reply)
        main()
        reply = '排行榜上传完成'
        src.reply(reply)
    except Exception as e:
        error_msg = f'上传排行榜时出错: {e}'
        try:
            src.reply(error_msg)
        except UnicodeEncodeError:
            src.reply(error_msg.encode('utf-8', 'replace').decode('gbk', 'replace'))

def reload_config(src, server):
    """重新加载配置"""
    global enabled, timer
    
    try:
        config = load_config()
        enabled = config.get('plugin', {}).get('enabled', True)
        
        # 重启定时任务
        if timer:
            server.cancel_task(timer)
            timer = None
        if enabled:
            start_timer(server)
        
        reply = '配置已重新加载'
        src.reply(reply)
    except Exception as e:
        error_msg = f'重新加载配置时出错: {e}'
        try:
            src.reply(error_msg)
        except UnicodeEncodeError:
            src.reply(error_msg.encode('utf-8', 'replace').decode('gbk', 'replace'))

def enable_plugin(src, server):
    """启用插件"""
    global enabled, timer
    
    try:
        config = load_config()
        config['plugin']['enabled'] = True
        save_config(config)
        enabled = True
        
        # 启动定时任务
        if not timer:
            start_timer(server)
        
        reply = '插件已启用'
        src.reply(reply)
    except Exception as e:
        error_msg = f'启用插件时出错: {e}'
        try:
            src.reply(error_msg)
        except UnicodeEncodeError:
            src.reply(error_msg.encode('utf-8', 'replace').decode('gbk', 'replace'))

def disable_plugin(src, server):
    """禁用插件"""
    global enabled, timer
    
    try:
        config = load_config()
        config['plugin']['enabled'] = False
        save_config(config)
        enabled = False
        
        # 停止定时任务
        if timer:
            server.cancel_task(timer)
            timer = None
        
        reply = '插件已禁用'
        src.reply(reply)
    except Exception as e:
        error_msg = f'禁用插件时出错: {e}'
        try:
            src.reply(error_msg)
        except UnicodeEncodeError:
            src.reply(error_msg.encode('utf-8', 'replace').decode('gbk', 'replace'))

def refresh_players(src):
    """重新获取玩家列表"""
    try:
        from .parse_player_data import parse_usercache
        from .get_player_data_paths import get_player_data_paths
        
        paths = get_player_data_paths()
        if paths['usercache_exists']:
            uuid_to_name = parse_usercache(paths['usercache_path'])
            count = len(uuid_to_name)
            reply = f'已重新获取玩家列表，共 {count} 名玩家'
            src.reply(reply)
        else:
            reply = 'usercache.json 文件不存在，无法获取玩家列表'
            src.reply(reply)
    except Exception as e:
        error_msg = f'重新获取玩家列表时出错: {e}'
        try:
            src.reply(error_msg)
        except UnicodeEncodeError:
            src.reply(error_msg.encode('utf-8', 'replace').decode('gbk', 'replace'))

def start_timer(server):
    """启动定时任务"""
    global timer
    
    def task():
        if enabled:
            try:
                # 执行更新任务
                from .generate_ranking_md import generate_ranking_md
                from .update_and_upload_ranking import upload_to_github
                
                generate_ranking_md()
                upload_to_github()
                server.logger.info('定时更新排行榜完成')
            except Exception as e:
                server.logger.error(f'定时更新时出错: {e}')
            
            # 计算下次执行时间
            next_delay = calculate_next_delay()
            global timer
            timer = server.schedule_task(task, next_delay)
    
    # 计算初始延迟
    initial_delay = calculate_next_delay()
    timer = server.schedule_task(task, initial_delay)
    server.logger.info(f'定时任务已启动，下次更新将在 {initial_delay} 秒后执行')

def calculate_next_delay():
    """计算下次执行任务的延迟时间"""
    config = load_config()
    update_config = config.get('update', {})
    
    use_daily = update_config.get('use_daily', False)
    
    if use_daily:
        # 每天固定时间更新
        daily_time = update_config.get('daily_time', 8.5)  # 默认8:30
        
        # 解析时间
        hours = int(daily_time)
        minutes = int((daily_time - hours) * 60)
        
        # 计算下次执行时间
        now = datetime.now()
        target_time = now.replace(hour=hours, minute=minutes, second=0, microsecond=0)
        
        # 如果目标时间已过，设置为明天
        if target_time <= now:
            target_time += timedelta(days=1)
        
        # 计算延迟
        delay = (target_time - now).total_seconds()
        return delay
    else:
        # 按间隔更新
        interval = update_config.get('interval', 3600)  # 默认1小时
        return interval
