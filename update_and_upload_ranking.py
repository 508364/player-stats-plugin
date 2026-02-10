import os
import sys
import json
import git
from datetime import datetime

# 处理相对导入问题
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from .generate_ranking_md import generate_ranking_md
    from .get_player_data_paths import get_player_data_paths
except ImportError:
    # 当直接运行时使用绝对导入
    from generate_ranking_md import generate_ranking_md
    from get_player_data_paths import get_player_data_paths

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
                "token": "",  # GitHub个人访问令牌
                "repo_owner": "",  # 仓库所有者
                "repo_name": "",  # 仓库名称
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

def save_config(config):
    """保存配置文件"""
    config_path = get_config_path()
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

def update_ranking():
    """更新排行榜"""
    print("=== 更新排行榜 ===")
    generate_ranking_md()
    print("排行榜更新完成")

def upload_to_github():
    """上传文件到GitHub"""
    print("=== 上传到GitHub ===")
    
    # 加载配置
    config = load_config()
    github_config = config.get('github', {})
    
    token = github_config.get('token')
    repo_path = github_config.get('repo_path')
    branch = github_config.get('branch', 'main')
    file_path = github_config.get('file_path', 'ranking.md')
    
    # 检查配置是否完整
    if not repo_path:
        print("错误：GitHub仓库路径未配置，请在config/player_stats/config.json中填写完整配置")
        return False
    
    # 检查本地仓库是否存在
    if not os.path.exists(repo_path) or not os.path.isdir(repo_path):
        print(f"错误：本地仓库路径不存在或不是目录：{repo_path}")
        return False
    
    # 检查ranking.md文件是否存在
    ranking_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ranking.md')
    if not os.path.exists(ranking_path):
        print("错误：ranking.md文件不存在，请先运行generate_ranking_md.py")
        return False
    
    try:
        # 打开本地仓库
        repo = git.Repo(repo_path)
        
        # 复制ranking.md文件到仓库
        dest_path = os.path.join(repo_path, file_path)
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        
        # 读取并写入文件
        with open(ranking_path, 'r', encoding='utf-8') as src:
            with open(dest_path, 'w', encoding='utf-8') as dst:
                dst.write(src.read())
        
        # 添加文件到暂存区
        repo.index.add([file_path])
        
        # 提交更改
        commit_message = f"自动更新排行榜 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        repo.index.commit(commit_message)
        
        # 推送到远程仓库
        origin = repo.remote('origin')
        
        # 如果配置了token，使用token进行认证
        if token:
            # 更新远程仓库URL，使用token认证
            remote_url = origin.url
            if 'https://' in remote_url:
                # 提取仓库地址
                repo_url = remote_url.split('https://')[1]
                # 构建带token的URL
                new_url = f"https://{token}@{repo_url}"
                origin.set_url(new_url)
                print("使用token认证推送...")
        
        origin.push(refspec=f"{branch}:{branch}")
        
        print("成功：文件上传到GitHub")
        print(f"仓库路径：{repo_path}")
        print(f"分支：{branch}")
        print(f"文件路径：{file_path}")
        return True
    
    except Exception as e:
        print(f"错误：上传失败：{e}")
        return False

def main():
    """主函数"""
    print("=== 自动更新排行榜并上传到GitHub ===")
    print()
    
    # 1. 更新排行榜
    update_ranking()
    print()
    
    # 2. 上传到GitHub
    success = upload_to_github()
    print()
    
    if success:
        print("任务完成：排行榜已更新并上传到GitHub")
    else:
        print("任务失败：请检查错误信息")

if __name__ == '__main__':
    main()
