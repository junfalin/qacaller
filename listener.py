import os
import subprocess
import shlex
import click
import toml
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


class FlowTask:
    """
    由于mlflow限制，单个进程中只能有active Run
    """

    def __init__(self, experiment_name):
        self.my_active_run_stack = []
        self.flow_client = MlflowClient()
        self.eid = mlflow.set_experiment(experiment_name=experiment_name)
        self.master_run = mlflow.start_run(experiment_id=self.eid, run_name="monitor")
        self.run_pool = {"monitor": self.master_run}
        self.handle = {}
        self.logs = {}
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
                self.monitor_artifact(msg[0])
                return
            run_name, do, pack = msg
            if do in self.handle:
                self.handle[do](run_name, pack)
        except Exception as e:
            self.monitor_artifact(str(e))

    def monitor_artifact(self, msg):
        self.log.write(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]>> {msg}")
        self.log.flush()
        self.flow_client.log_artifact(self.master_run.info.run_id, self._fname)

    def log_artifact(self, run_name, value):
        fn, log = self.logs[run_name]
        log.write(value)
        log.flush()
        self.flow_client.log_artifact(self.get_run_id(run_name=run_name), fn)

    def log_tag(self, run_name, key, value):
        self.flow_client.set_tag(self.get_run_id(run_name), key, value)

    def log_tags(self, run_name, pack):
        tags = json.loads(pack.strip('"'))
        tags_arr = [RunTag(key, str(value)) for key, value in tags.items()]
        self.flow_client.log_batch(run_id=self.get_run_id(run_name), metrics=[], params=[], tags=tags_arr)

    def log_param(self, run_name, pack):
        key, value = pack.split(":")
        self.flow_client.log_param(self.get_run_id(run_name=run_name), key=key, value=value)

    def log_params(self, run_name, pack):
        params = json.loads(pack.strip('"'))
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

        metrics = json.loads(pack.strip('"'))
        timestamp = int(time.time() * 1000)
        metrics_arr = [Metric(key, value, timestamp, step or 0) for key, value in metrics.items()]
        self.flow_client.log_batch(self.get_run_id(run_name=run_name), metrics=metrics_arr)

    def get_run_id(self, run_name):
        if run_name in self.run_pool:
            return self.run_pool[run_name].info.run_id
        x = mlflow.start_run(experiment_id=self.eid, nested=True, run_name=run_name)
        self.run_pool[run_name] = x
        fname = f"outputs/log_{uuid4()}.txt"
        self.logs[run_name] = (fname, open(fname, 'w', encoding="utf8"))
        return x.info.run_id

    def end_run(self, run_name, status=OK):
        self.flow_client.set_terminated(self.get_run_id(run_name), status=status)

    def __enter__(self):
        self._fname = f"outputs/log_{uuid4()}.txt"
        self.log = open(self._fname, 'w', encoding="utf8")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.log.write(f"EXIT_TYPE:{exc_type}\n")
        self.log.write(f"EXIT_VAL:{exc_val}\n")
        self.log.close()
        for i in self.logs.values():
            i[1].close()
        for i in self.run_pool.keys():
            self.end_run(i, OK)
        return False


if not os.path.exists('outputs'):
    os.mkdir('outputs')


@click.command()
@click.option("--cmd", help="command")
@click.option("--run", help="run_name")
def listen(cmd, run):
    with FlowTask(run) as ft:
        command = shlex.split(cmd)
        p = subprocess.Popen(
            command, shell=True, close_fds=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        while p.poll() is None:
            try:
                line = p.stdout.readline().decode()
            except Exception as e:
                line = p.stdout.readline().decode('gbk')
            if line:
                print(line)
                ft.listen(line)


if __name__ == '__main__':
    listen()
