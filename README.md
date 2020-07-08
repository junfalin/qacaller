# qacaller


### MLflow Track
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



### 通信
- 管道stdout获取子进程输出信息
- 协议
    - run_name@artifact@[str]
    
    - run_name@param@[key]:[str]
    
    - run_name@params@[json]
    
    - run_name@metric@[key]:[float/int]
    
    - run_name@metrics@[json]