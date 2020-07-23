# qacaller

> 通过```MLflow```跟踪纪录程序运行的参数、指标、日志等信息
>
>在mlruns 目录下执行 ```mlflow ui```打开界面

### Usage
```
pip install qacaller
qacaller --run <run_name> --cmd <command>
mlflow ui
```


### Example

```
# test.py

print("test@artifact@hello")
print("test@param@K1:100")
print("test@param@K1:200")
print('test@params@{"ma":20,"K2":3}')
for i in range(10):
    print(f"thread1@metric@number:{i}")
    print(f'thread1@metrics@{{"age":{i + 2},"total":{i + 3}}}')
print("test@tag@color:red")
print("test@tag@color:Green")
print('test@tags@{"age":"18","性别":"male"}')
1 / 0
```
```
qacaller --run test --cmd "python <absolute path>/test.py"
```


### Protocol
> 需调用程序遵循协议并打印输出
```
    
    - run_name@artifact@[str]            //日志文件
   
    - run_name@param@[key]:[str]         //参数,不可覆盖      
    
    - run_name@params@[json]
    
    - run_name@metric@[key]:[float/int]  //指标,可累积
    
    - run_name@metrics@[json]
    
    - run_name@tag@[key]:[str]           //标签,可覆盖

    - run_name@tags@[json]
```




### MLflow Track
```
- Experiment
    - |___ Run
        - param
        - metric
        - tag
        - artifact
        - |___ child_run
            - param
            - metric
            - tag
            - artifact
        - |___ child_run
        - |___ child_run

     - |___ Run
        - |___ child_run
        - |___ child_run
        - |___ child_run
```
