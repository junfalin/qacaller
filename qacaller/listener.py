import os
import subprocess
import shlex
import click
import sys
# Dispatching Management System
import datetime
import json
import os
import time
from uuid import uuid4
import mlflow
import re
from mlflow.entities import RunStatus, Param, Metric, RunTag
from mlflow.tracking.client import MlflowClient

OK = RunStatus.to_string(RunStatus.FINISHED)
ERR = RunStatus.to_string(RunStatus.FAILED)
KILL = RunStatus.to_string(RunStatus.KILLED)
pattern = re.compile(r"(.*?)@(.*?)@(.*)")

SHELL = False if sys.platform == 'linux' else True
STEP = "\n" if sys.platform == 'linux' else "\r\n"


class FlowTask:
    """
    由于mlflow限制，单个进程中只能启动一个
    """

    def __init__(self, experiment_name):
        self.my_active_run_stack = []
        self.flow_client = MlflowClient()
        self.run_pool = {}  # run_name:Run
        self.handle = {}
        self.logs = {}  # run_id:(fn,fs)
        self.name = experiment_name
        self.eid = mlflow.set_experiment(experiment_name=experiment_name)
        self.start_run(experiment_name, nested=False)
        self._register()

    def _register(self):
        self.handle["param"] = self.log_param
        self.handle["params"] = self.log_params
        self.handle["metric"] = self.log_metric
        self.handle["metrics"] = self.log_metrics
        self.handle["artifact"] = self.log_artifact
        self.handle["tag"] = self.log_tag
        self.handle["tags"] = self.log_tags

    def listen(self, msg):
        try:
            msg = msg.split("@", 2)
            if len(msg) == 1:
                self.log_artifact(self.name, msg[0])
                return
            if len(msg) == 3:
                run_name, do, pack = msg
                if do in self.handle:
                    self.handle[do](run_name, pack)
        except Exception as e:
            print("[Exception]:", e, "[Message]:", "".join(msg))

    def log_artifact(self, run_name, value):
        run_id = self.get_run_id(run_name)
        fn, log = self.logs[run_id]
        log.write(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]: {value.strip()}\n")
        log.flush()
        self.flow_client.log_artifact(run_id, fn)

    def log_tag(self, run_name, pack):
        key, value = pack.split(":")
        self.flow_client.set_tag(self.get_run_id(run_name), key, value)

    def log_tags(self, run_name, pack):
        tags = json.loads(pack.strip('"').replace("'", '"'))
        tags_arr = [RunTag(key, str(value)) for key, value in tags.items()]
        self.flow_client.log_batch(run_id=self.get_run_id(run_name), tags=tags_arr)

    def log_param(self, run_name, pack):
        key, value = pack.split(":")
        self.flow_client.log_param(self.get_run_id(run_name=run_name), key=key, value=value)

    def log_params(self, run_name, pack):
        params = json.loads(pack.strip('"').replace("'", '"'))
        params_arr = [Param(key, str(value)) for key, value in params.items()]
        self.flow_client.log_batch(self.get_run_id(run_name=run_name), params=params_arr)

    def log_metric(self, run_name, pack):
        """

        :param run_name:
        :param pack: key:value [float]
        :return:
        """
        key, value = pack.split(":")
        self.flow_client.log_metric(self.get_run_id(run_name=run_name), key=key, value=float(value))

    def log_metrics(self, run_name, pack, step=None):
        """

        :param run_name:
        :param pack: json -> key:value [float]
        :return:
        """

        metrics = json.loads(pack.strip('"').replace("'", '"'))
        timestamp = int(time.time() * 1000)
        metrics_arr = [Metric(key, value, timestamp, step or 0) for key, value in metrics.items()]
        self.flow_client.log_batch(self.get_run_id(run_name=run_name), metrics=metrics_arr)

    def start_run(self, run_name, nested=True):
        x = mlflow.start_run(experiment_id=self.eid, nested=nested, run_name=run_name)
        self.run_pool[run_name] = x
        fname = f"outputs/log_{uuid4()}.txt"
        self.logs[x.info.run_id] = (fname, open(fname, 'w', encoding="utf8"))
        return x.info.run_id

    def get_run_id(self, run_name):
        if run_name in self.run_pool:
            return self.run_pool[run_name].info.run_id
        return self.start_run(run_name)

    def end_run(self, run_name, status=OK):
        self.flow_client.set_terminated(self.get_run_id(run_name), status=status)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for i in self.logs.values():
            i[1].close()
        for i in self.run_pool.keys():
            self.end_run(i, OK)
        return False


if not os.path.exists('outputs'):
    os.mkdir('outputs')


@click.command()
@click.option("--cmd", default="", help="command")
@click.option("--run", default="", help="run_name")
def cmdline(cmd, run):
    if cmd == "" or run == "":
        print("qacaller --help 查看帮助")
        sys.exit(0)
    with FlowTask(run) as ft:
        command = shlex.split(cmd)
        p = subprocess.Popen(
            command, shell=SHELL, close_fds=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        while p.poll() is None:
            try:
                line = p.stdout.readline().decode()
            except Exception as e:
                line = p.stdout.readline().decode('gbk')
            if line:
                print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]:", line.strip())
                ft.listen(line)
        stdout, stderr = p.communicate()
        try:
            x = stdout.decode().split(STEP)
        except Exception as e:
            x = stdout.decode('gbk').split(STEP)
        for line in x:
            if line:
                print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]:", line.strip())
                ft.listen(line)


if __name__ == '__main__':
    cmdline()
