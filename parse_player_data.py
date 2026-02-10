import os
import sys
import json

# 处理相对导入问题
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from .get_player_data_paths import get_player_data_paths
except ImportError:
    # 当直接运行时使用绝对导入
    from get_player_data_paths import get_player_data_paths

def parse_usercache(usercache_path):
    """解析usercache.json文件，返回uuid到玩家名称的映射"""
    try:
        with open(usercache_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 构建uuid到玩家名称的映射
        uuid_to_name = {}
        for entry in data:
            uuid = entry.get('uuid', '')
            name = entry.get('name', '')
            if uuid and name:
                uuid_to_name[uuid] = name
        
        return uuid_to_name
    except Exception as e:
        print(f"Error parsing usercache.json: {e}")
        return {}

def parse_stats_file(stats_file_path):
    """解析单个stats JSON文件"""
    try:
        with open(stats_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"Error parsing {os.path.basename(stats_file_path)}: {e}")
        return {}

def parse_all_stats(stats_dir, uuid_to_name):
    """解析stats文件夹中的所有文件"""
    if not os.path.exists(stats_dir):
        return {}
    
    stats_data = {}
    for filename in os.listdir(stats_dir):
        if filename.endswith('.json'):
            # 从文件名提取uuid（去掉.json后缀）
            uuid = filename[:-5]  # 去掉.json后缀
            player_name = uuid_to_name.get(uuid, f"Unknown ({uuid[:8]}...)")
            
            file_path = os.path.join(stats_dir, filename)
            stats = parse_stats_file(file_path)
            
            stats_data[uuid] = {
                'name': player_name,
                'filename': filename,
                'stats': stats
            }
    
    return stats_data

def get_stat_description(stat_key):
    """获取统计数据的中文描述"""
    descriptions = {
        # 移动相关
        'minecraft:jump': '跳跃次数',
        'minecraft:walk_one_cm': '步行距离（厘米）',
        'minecraft:sprint_one_cm': ' sprint距离（厘米）',
        'minecraft:crouch_one_cm': '蹲下移动距离（厘米）',
        'minecraft:swim_one_cm': '游泳距离（厘米）',
        'minecraft:fly_one_cm': '飞行距离（厘米）',
        'minecraft:fall_one_cm': '坠落距离（厘米）',
        'minecraft:climb_one_cm': '攀爬距离（厘米）',
        'minecraft:horse_one_cm': '骑马距离（厘米）',
        
        # 时间相关
        'minecraft:play_time': '游戏时间（刻）',
        'minecraft:total_world_time': '总世界时间（刻）',
        'minecraft:time_since_rest': '距离上次休息的时间（刻）',
        'minecraft:time_since_death': '距离上次死亡的时间（刻）',
        'minecraft:sneak_time': '蹲下时间（刻）',
        
        # 游戏行为
        'minecraft:leave_game': '退出游戏次数',
        'minecraft:deaths': '死亡次数',
        'minecraft:killed_by': '被击杀统计(统计总数)',
        'minecraft:players_killed': '杀死玩家次数',
        'minecraft:animals_bred': '繁殖动物次数',
        'minecraft:items_crafted': '合成物品次数',
        'minecraft:items_used': '使用物品次数',
        'minecraft:items_dropped': '丢弃物品次数',
        'minecraft:items_picked_up': '捡起物品次数',
        'minecraft:blocks_placed': '放置方块次数',
        'minecraft:blocks_broken': '破坏方块次数',
        'minecraft:damage_dealt': '造成伤害',
        'minecraft:damage_taken': '受到伤害',
        
        # 新增统计类型
        'minecraft:dropped': '丢弃物品统计(统计总数)',
        'minecraft:crafted': '合成物品统计(统计总数)',
        'minecraft:mined': '挖掘方块统计(统计总数)',
        'minecraft:broken': '损坏工具统计(统计总数)',
        'minecraft:mob_kills': '杀死生物总数',
        
        # 容器交互
        'minecraft:open_chest': '打开箱子次数',
        'minecraft:open_barrel': '打开木桶次数',
        'minecraft:open_enderchest': '打开末影箱次数',
        'minecraft:interact_with_furnace': '与熔炉交互次数',
        'minecraft:interact_with_smoker': '与 smoker 交互次数',
        'minecraft:inspect_dispenser': '查看发射器次数',
        'minecraft:inspect_dropper': '查看投掷器次数',
        'minecraft:inspect_hopper': '查看漏斗次数',
        'minecraft:interact_with_blast_furnace': '与高炉交互次数',
        
        # 自定义统计
        'minecraft:custom': '自定义统计数据'
    }
    return descriptions.get(stat_key, stat_key)

def display_stats_recursive(stats, indent=4):
    """递归显示统计数据"""
    if isinstance(stats, dict):
        for key, value in stats.items():
            description = get_stat_description(key)
            print(f"{' ' * indent}- {description}: {key}")
            if isinstance(value, (dict, list)):
                display_stats_recursive(value, indent + 4)
            else:
                print(f"{' ' * (indent + 4)}- 值: {value}")
    elif isinstance(stats, list):
        for i, item in enumerate(stats):
            print(f"{' ' * indent}- [{i}]")
            display_stats_recursive(item, indent + 4)
    else:
        print(f"{' ' * indent}- {stats}")

def display_player_data():
    """显示所有玩家数据"""
    # 获取路径
    paths = get_player_data_paths()
    
    print('=== 玩家数据解析器 ===')
    print()
    
    # 解析usercache.json
    print('1. Usercache Data:')
    if paths['usercache_exists']:
        uuid_to_name = parse_usercache(paths['usercache_path'])
        print(f"   合计共 {len(uuid_to_name)} 个玩家在 usercache.json 中")
        for uuid, name in uuid_to_name.items():
            print(f"   - 玩家: {name}")
            print(f"   - UUID: {uuid}")
    else:
        print("   usercache.json not found")
    
    print()
    
    # 解析stats文件夹
    print('2. Stats Data:')
    if paths['stats_exists']:
        # 解析stats文件夹
        if 'uuid_to_name' in locals():
            stats_data = parse_all_stats(paths['stats_dir'], uuid_to_name)
            print(f"   合计共 {len(stats_data)} 个玩家的统计数据文件")
            print()
            
            for uuid, data in stats_data.items():
                print(f"   玩家: {data['name']}")
                print(f"   UUID: {uuid}")
                print(f"   统计数据文件: {data['filename']}")   
                print()
                
                # 详细显示所有统计数据
                print("   Detailed Stats:")
                if data['stats']:
                    display_stats_recursive(data['stats'])
                else:
                    print("   No stats available")
                print()
        else:
            print("   无法解析统计数据，因为缺少 usercache.json 中的玩家 UUID 映射")
    else:
        print("   stats 目录未找到")

if __name__ == '__main__':
    display_player_data()
