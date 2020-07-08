# qacaller

> 通过```MLflow```跟踪纪录程序运行的参数、指标、日志等信息
>
>在mlruns 目录下执行 ```mlflow ui```打开可视化界面

### usage
```
python listener.py --run <run_name> --cmd <command>
```


### 协议
> 需调用程序遵循协议并打印输出
```
    - run_name@artifact@[str]
    
    - run_name@param@[key]:[str]
    
    - run_name@params@[json]
    
    - run_name@metric@[key]:[float/int]
    
    - run_name@metrics@[json]

    - run_name@tag@[key]:[str]

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
