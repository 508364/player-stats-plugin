import os

def get_player_data_paths():
    """获取玩家数据文件路径"""
    # 获取当前脚本所在目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 尝试不同的路径组合找到server文件夹
    possible_paths = [
        # 直接在当前目录下
        os.path.join(current_dir, 'server'),
        # 在上一级目录下
        os.path.join(os.path.dirname(current_dir), 'server'),
        # 在更上一级目录下
        os.path.join(os.path.dirname(os.path.dirname(current_dir)), 'server')
    ]
    
    # 找到实际的server目录
    server_dir = None
    for path in possible_paths:
        if os.path.exists(path) and os.path.isdir(path):
            server_dir = path
            break
    
    if server_dir:
        # 构建usercache.json的路径
        usercache_path = os.path.join(server_dir, 'usercache.json')
        
        # 构建stats文件夹的路径
        stats_dir = os.path.join(server_dir, 'world', 'stats')
        
        # 检查文件和目录是否存在
        usercache_exists = os.path.exists(usercache_path)
        stats_exists = os.path.exists(stats_dir)
    else:
        # 如果找不到server目录，使用默认路径
        usercache_path = os.path.join(current_dir, 'server', 'usercache.json')
        stats_dir = os.path.join(current_dir, 'server', 'world', 'stats')
        usercache_exists = False
        stats_exists = False
    
    return {
        'current_dir': current_dir,
        'server_dir': server_dir,
        'usercache_path': usercache_path,
        'usercache_exists': usercache_exists,
        'stats_dir': stats_dir,
        'stats_exists': stats_exists
    }

# 如果直接运行脚本
if __name__ == '__main__':
    paths = get_player_data_paths()
    
    # 输出结果
    print('=== Player Data Paths ===')
    print(f'Current directory: {paths["current_dir"]}')
    print(f'Usercache.json path: {paths["usercache_path"]}')
    print(f'Usercache.json exists: {paths["usercache_exists"]}')
    print(f'Stats directory path: {paths["stats_dir"]}')
    print(f'Stats directory exists: {paths["stats_exists"]}')
    
    if paths['usercache_exists']:
        print(f'Usercache.json size: {os.path.getsize(paths["usercache_path"])} bytes')
    
    if paths['stats_exists']:
        # 统计stats文件夹中的文件数量
        stats_files = os.listdir(paths['stats_dir'])
        print(f'Stats directory contains {len(stats_files)} files:')
        for file in stats_files:
            file_path = os.path.join(paths['stats_dir'], file)
            print(f'  - {file} ({os.path.getsize(file_path)} bytes)')
