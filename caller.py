from listener import call_actor, Cli, BASE_DIR
import os

# 获取默认参数
cli = Cli("")
cli.toml_file_path = os.path.join(BASE_DIR, "cfg_temp.toml")
t = cli.read()
# 修改参数
t['cli']['name'] = ['t02']
t['hisdata']['host'] = "192.168.2.118"
print(t)
call_actor.delay(t)
