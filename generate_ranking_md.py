import os
import sys
import json

# 处理相对导入问题
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from .create_player_rankings import create_ranking, get_stat_unit
    from .parse_player_data import parse_usercache, parse_all_stats
    from .get_player_data_paths import get_player_data_paths
except ImportError:
    # 当直接运行时使用绝对导入
    from create_player_rankings import create_ranking, get_stat_unit
    from parse_player_data import parse_usercache, parse_all_stats
    from get_player_data_paths import get_player_data_paths

def get_top_player(ranking):
    """获取排行榜的第一名"""
    if ranking:
        return ranking[0]
    return None

def format_time_days(days):
    """将天数格式化为分钟"""
    # 1天 = 24小时 = 1440分钟
    minutes = days * 1440
    return f"{int(minutes)}分钟"

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
                "repo_path": "",  # 本地GitHub仓库路径
                "branch": "main",
                "file_path": "ranking.md"  # 仓库中的文件路径
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
            "update_interval": 3600  # 默认1小时更新一次
        }
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)
        return default_config
    
    # 加载配置文件
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_ranking_md():
    """生成ranking.md文件"""
    # 获取路径
    paths = get_player_data_paths()
    
    if not paths['usercache_exists'] or not paths['stats_exists']:
        print("Missing required files:")
        if not paths['usercache_exists']:
            print("- usercache.json not found")
        if not paths['stats_exists']:
            print("- stats directory not found")
        return
    
    # 加载配置
    config = load_config()
    ranking_names = config.get('ranking_names', {})
    
    # 解析数据
    uuid_to_name = parse_usercache(paths['usercache_path'])
    stats_data = parse_all_stats(paths['stats_dir'], uuid_to_name)
    
    # 定义要生成排行榜的统计数据
    default_ranking_stats = [
        ('minecraft:play_time', '在线时长最长'),
        ('minecraft:walk_one_cm', '步行距离最远'),
        ('minecraft:fly_one_cm', '飞行距离最远'),
        ('minecraft:swim_one_cm', '游泳距离最远'),
        ('minecraft:jump', '跳跃次数最多'),
        ('minecraft:mob_kills', '杀死生物最多'),
        ('minecraft:damage_taken', '受到伤害最多'),
        ('minecraft:blocks_broken', '破坏方块最多')
    ]
    
    # 从配置文件中获取项目名称
    ranking_stats = []
    for stat_key, default_name in default_ranking_stats:
        # 使用配置文件中的名称，如果不存在则使用默认名称
        display_name = ranking_names.get(stat_key, default_name)
        ranking_stats.append((stat_key, display_name))
    
    # 提取所有榜一数据
    top_players = []
    for stat_key, stat_name in ranking_stats:
        ranking = create_ranking(stats_data, stat_key)
        top_player = get_top_player(ranking)
        if top_player:
            unit = get_stat_unit(stat_key)
            value = top_player['value']
            
            # 特殊处理单位
            if unit == '天':
                # 游戏刻转换为天，再转换为分钟
                days = value / 24000
                display_value = format_time_days(days)
            elif unit == '米':
                # 厘米转换为米
                display_value = f"{value / 100:.1f}米"
            else:
                display_value = f"{value}{unit}"
            
            top_players.append({
                'stat_name': stat_name,
                'player_name': top_player['name'],
                'value': display_value
            })
    
    # 生成markdown内容
    md_content = "本排行榜自动更新，展示服务器各项数据的第一名\n\n"
    
    for item in top_players:
        md_content += f"## {item['stat_name']}\n"
        md_content += f"- **{item['player_name']}** {item['value']}\n\n"
    
    # 写入文件
    md_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ranking.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_content)
    
    print(f"Ranking.md generated successfully at: {md_path}")
    print(f"Generated {len(top_players)} top rankings")

if __name__ == '__main__':
    generate_ranking_md()
