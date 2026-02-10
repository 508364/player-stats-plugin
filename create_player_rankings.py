import os
import sys
import json

# 处理相对导入问题
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from .parse_player_data import parse_usercache, parse_all_stats
    from .get_player_data_paths import get_player_data_paths
except ImportError:
    # 当直接运行时使用绝对导入
    from parse_player_data import parse_usercache, parse_all_stats
    from get_player_data_paths import get_player_data_paths

def get_stat_unit(stat_key):
    """获取统计数据的单位"""
    unit_map = {
        # 次数单位
        'minecraft:jump': '次',
        'minecraft:leave_game': '次',
        'minecraft:deaths': '次',
        'minecraft:killed_by': '次',
        'minecraft:players_killed': '次',
        'minecraft:animals_bred': '次',
        'minecraft:items_crafted': '次',
        'minecraft:items_used': '次',
        'minecraft:items_dropped': '次',
        'minecraft:items_picked_up': '次',
        'minecraft:blocks_placed': '次',
        'minecraft:blocks_broken': '次',
        'minecraft:dropped': '次',
        'minecraft:crafted': '次',
        'minecraft:mined': '次',
        'minecraft:broken': '次',
        'minecraft:mob_kills': '次',
        'minecraft:open_chest': '次',
        'minecraft:open_barrel': '次',
        'minecraft:open_enderchest': '次',
        'minecraft:interact_with_furnace': '次',
        'minecraft:interact_with_smoker': '次',
        'minecraft:inspect_dispenser': '次',
        'minecraft:inspect_dropper': '次',
        'minecraft:inspect_hopper': '次',
        'minecraft:interact_with_blast_furnace': '次',
        
        # 距离单位（转换为米）
        'minecraft:walk_one_cm': '米',
        'minecraft:sprint_one_cm': '米',
        'minecraft:crouch_one_cm': '米',
        'minecraft:swim_one_cm': '米',
        'minecraft:fly_one_cm': '米',
        'minecraft:fall_one_cm': '米',
        'minecraft:climb_one_cm': '米',
        'minecraft:horse_one_cm': '米',
        
        # 时间单位（转换为天）
        'minecraft:play_time': '天',
        'minecraft:total_world_time': '天',
        'minecraft:time_since_rest': '天',
        'minecraft:time_since_death': '天',
        'minecraft:sneak_time': '天',
        
        # 其他
        'minecraft:damage_dealt': '点',
        'minecraft:damage_taken': '点'
    }
    return unit_map.get(stat_key, '')

def extract_stat_value(stats, stat_key):
    """从统计数据中提取特定值"""
    if 'stats' in stats:
        stats_data = stats['stats']
        
        # 首先检查minecraft:custom中的数据
        if 'minecraft:custom' in stats_data:
            custom_stats = stats_data['minecraft:custom']
            if stat_key in custom_stats:
                return custom_stats[stat_key]
        
        # 处理破坏方块总数（minecraft:mined）
        if stat_key == 'minecraft:blocks_broken' and 'minecraft:mined' in stats_data:
            # 计算所有方块类型的破坏数量之和
            mined_stats = stats_data['minecraft:mined']
            total_broken = 0
            for block, count in mined_stats.items():
                total_broken += count
            return total_broken
        
        # 检查其他可能的存储位置
        if stat_key in stats_data:
            return stats_data[stat_key]
    return 0

def create_ranking(stats_data, stat_key, top_n=10):
    """创建特定统计数据的排行榜"""
    # 提取所有玩家的该统计数据
    player_stats = []
    for uuid, data in stats_data.items():
        value = extract_stat_value(data['stats'], stat_key)
        if value > 0:
            player_stats.append({
                'uuid': uuid,
                'name': data['name'],
                'value': value
            })
    
    # 按值排序（降序）
    player_stats.sort(key=lambda x: x['value'], reverse=True)
    
    # 只取前N名
    top_players = player_stats[:top_n]
    
    return top_players

def format_ranking(ranking, stat_key, stat_name):
    """格式化排行榜输出"""
    unit = get_stat_unit(stat_key)
    lines = []
    
    # 输出排行榜标题
    lines.append(f"=== {stat_name} 排行榜 ===")
    lines.append("排行名次 | 玩家名称：具体事项 | 完成了多少次/米/时间")
    lines.append("-" * 80)
    
    # 输出排行数据
    for i, player in enumerate(ranking, 1):
        value = player['value']
        display_value = value
        display_unit = unit
        
        # 单位转换
        if unit == '米':
            # 距离单位转换（厘米转米）
            display_value = value / 100
        elif unit == '天':
            # 游戏刻转换为天（1天=24000刻）
            display_value = value / 24000
        
        # 格式化输出
        if unit in ['米', '天']:
            line = f"{i:2d}         | {player['name']}：{stat_name} | {display_value:.2f}{display_unit}"
        else:
            line = f"{i:2d}         | {player['name']}：{stat_name} | {display_value}{display_unit}"
        lines.append(line)
    
    lines.append("-" * 80)
    lines.append("")
    
    return '\n'.join(lines)

def create_all_rankings():
    """创建所有统计数据的排行榜"""
    # 获取路径
    paths = get_player_data_paths()
    
    print('=== 玩家排行榜 ===')
    print()
    
    # 解析数据
    if paths['usercache_exists'] and paths['stats_exists']:
        # 解析usercache.json获取UUID到名称的映射
        uuid_to_name = parse_usercache(paths['usercache_path'])
        
        # 解析所有stats文件
        stats_data = parse_all_stats(paths['stats_dir'], uuid_to_name)
        
        print(f"合计共 {len(stats_data)} 个玩家在此服务器上")
        print()
        
        # 定义要生成排行榜的统计数据
        ranking_stats = [
            ('minecraft:play_time', '游戏时间'),
            ('minecraft:walk_one_cm', '步行距离'),
            ('minecraft:fly_one_cm', '飞行距离'),
            ('minecraft:swim_one_cm', '游泳距离'),
            ('minecraft:jump', '跳跃次数'),
            ('minecraft:mob_kills', '杀死生物数'),
            ('minecraft:damage_taken', '受到伤害'),
            ('minecraft:blocks_broken', '破坏方块数')
        ]
        
        # 生成每个统计数据的排行榜
        for stat_key, stat_name in ranking_stats:
            ranking = create_ranking(stats_data, stat_key)
            if ranking:
                formatted_ranking = format_ranking(ranking, stat_key, stat_name)
                print(formatted_ranking)
            else:
                print(f"=== {stat_name} 排行榜 ===")
                print("无数据")
                print()
    else:
        print("缺少必要文件:")
        if not paths['usercache_exists']:
            print("- usercache.json 未找到")
        if not paths['stats_exists']:
            print("- stats 目录未找到")

if __name__ == '__main__':
    create_all_rankings()
