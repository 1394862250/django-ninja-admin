import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

banner = '''
       .__            __        
  ____ |__| ____     |__|____   
 /    \|  |/    \    |  \__  \  
|   |  \  |   |  \   |  |/ __ \_
|___|  /__|___|  /\__|  (____  /
     \/        \/\______|    \/ 
'''

def project_run():
    print(banner)
    print("项目启动中，请稍候...")
    print("正在启动项目...")
    os.system("python manage.py runserver 0.0.0.0:8000")
    print("项目启动成功，正在打开浏览器...")
    os.system("start http://127.0.0.1:8000")
    print("浏览器打开成功，项目地址：http://127.0.0.1:8000")
    print("关闭浏览器，请按 Ctrl+C 停止项目")

if __name__ == "__main__":
    project_run()
