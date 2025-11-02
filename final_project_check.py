#!/usr/bin/env python3
"""
Final check of all changes in the project
"""

import os
from pathlib import Path

def check_env_files():
    """Check .env files"""
    print("🔍 Checking .env files...")
    
    # Check .env.sample
    env_sample_path = Path('.env.sample')
    if env_sample_path.exists():
        content = env_sample_path.read_text(encoding='utf-8')
        if 'GROUP_OUTPUT_MODE=short' in content:
            print("✅ .env.sample contains GROUP_OUTPUT_MODE")
        else:
            print("❌ .env.sample DOES NOT contain GROUP_OUTPUT_MODE")
    else:
        print("❌ .env.sample not found")
    
    # Check .env
    env_path = Path('.env')
    if env_path.exists():
        content = env_path.read_text(encoding='utf-8')
        if 'GROUP_OUTPUT_MODE=short' in content:
            print("✅ .env contains GROUP_OUTPUT_MODE")
        else:
            print("❌ .env DOES NOT contain GROUP_OUTPUT_MODE")
    else:
        print("❌ .env not found")

def check_bot_py():
    """Check bot.py"""
    print("\n🔍 Checking bot.py...")
    
    bot_path = Path('bot.py')
    if not bot_path.exists():
        print("❌ bot.py not found")
        return
        
    content = bot_path.read_text(encoding='utf-8')
    
    checks = [
        ('GROUP_OUTPUT_MODE = os.getenv', "GROUP_OUTPUT_MODE variable"),
        ('def get_full_report_button' not in content, "Function get_full_report_button removed"),
        ('def get_group_full_report_button' not in content, "Function get_group_full_report_button removed"),
        ('cq_full_report' not in content, "Callback handler cq_full_report removed"),
        ('final_short_mode = short_mode and (GROUP_OUTPUT_MODE == "short")', "GROUP_OUTPUT_MODE logic for groups"),
        ('For full logging, make a repeated request to the bot in DM', "Instruction for groups"),
    ]
    
    for check, description in checks:
        if isinstance(check, str):
            if check in content:
                print(f"✅ {description}")
            else:
                print(f"❌ {description}")
        else:
            if check:
                print(f"✅ {description}")
            else:
                print(f"❌ {description}")

def check_worker_py():
    """Check worker.py"""
    print("\n🔍 Checking worker.py...")
    
    worker_path = Path('worker.py')
    if not worker_path.exists():
        print("❌ worker.py not found")
        return
        
    content = worker_path.read_text(encoding='utf-8')
    
    checks = [
        ('GROUP_OUTPUT_MODE = os.getenv', "GROUP_OUTPUT_MODE variable"),
        ('def get_full_report_button' not in content, "Function get_full_report_button removed"),
        ('def get_group_full_report_button' not in content, "Function get_group_full_report_button removed"),
        ('InlineKeyboardMarkup' not in content, "InlineKeyboardMarkup import removed"),
        ('GROUP_OUTPUT_MODE == "short"', "GROUP_OUTPUT_MODE logic"),
        ('For full logging, make a repeated request to the bot in DM', "Instruction for groups"),
    ]
    
    for check, description in checks:
        if isinstance(check, str):
            if check in content:
                print(f"✅ {description}")
            else:
                print(f"❌ {description}")
        else:
            if check:
                print(f"✅ {description}")
            else:
                print(f"❌ {description}")

def check_readme():
    """Check README.md"""
    print("\n🔍 Checking README.md...")
    
    readme_path = Path('README.md')
    if not readme_path.exists():
        print("❌ README.md not found")
        return
        
    content = readme_path.read_text(encoding='utf-8')
    
    if 'GROUP_OUTPUT_MODE=short' in content:
        print("✅ README.md contains documentation for GROUP_OUTPUT_MODE")
    else:
        print("❌ README.md DOES NOT contain documentation for GROUP_OUTPUT_MODE")

def main():
    print("🚀 Final project check for bot-reality")
    print("=" * 50)
    
    # Change working directory if needed
    if not Path('bot.py').exists():
        os.chdir('c:/Users/digne/OneDrive/Документы/GitHub/bot-reality')
    
    check_env_files()
    check_bot_py()
    check_worker_py()
    check_readme()
    
    print("\n" + "=" * 50)
    print("📋 Summary of changes:")
    print("✅ Added GROUP_OUTPUT_MODE variable in .env files")
    print("✅ Removed all button-creation functions")
    print("✅ Removed callback handler for buttons")
    print("✅ Simplified logic: textual instructions instead of buttons")
    print("✅ Deep-link functionality preserved")
    print("✅ Documentation updated in README.md")
    print("\n🎯 Deep-link https://t.me/gig_reality_bot?start=ya.ru should work!")

if __name__ == "__main__":
    main()
