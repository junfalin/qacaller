import os
import subprocess
import shlex
from celery import Celery
import toml
# Dispatching Management System
import datetime
import json
import os
import time
from uuid import uuid4
import mlflow
import re
from mlflow.entities import RunStatus, Param, Metric, LifecycleStage
from mlflow.tracking.client import MlflowClient

OK = RunStatus.to_string(RunStatus.FINISHED)
ERR = RunStatus.to_string(RunStatus.FAILED)
KILL = RunStatus.to_string(RunStatus.KILLED)
pattern = re.compile(r"(.*?)@(.*?)@(.*)")


class DMS:
    def __init__(self):
        self.task_pool = {}


dms = DMS()
if not os.path.exists('outputs'):
    os.mkdir('outputs')

if not os.path.exists('temp'):
    os.mkdir('temp')


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
        # self.handle["end"] = self.end_run

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


MQ_IP = os.getenv("CELERY_MQ_IP", "localhost")
MQ_PORT = os.getenv("CELERY_MQ_PORT", 5672)
MQ_USER = os.getenv("CELERY_MQ_USER", "admin")
MQ_PWD = os.getenv("CELERY_MQ_PWD", "admin")

QAACOUNTPRO_RS_RELEASE = os.getenv("QAACOUNTPRO_RS_RELEASE", "D:/QA_Rep/qaaccountpro-rs/target/release/examples")
QAACOUNTPRO_RS_MAIN = os.getenv("QAACOUNTPRO_RS_MAIN", "arp_actor_single")

celery = Celery('mlflow2rs', broker=f'amqp://{MQ_USER}:{MQ_PWD}@{MQ_IP}:{MQ_PORT}/')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class Cli:
    def __init__(self, file_name):
        if not file_name.endswith('.toml'):
            file_name += ".toml"
        self.toml_file_path = os.path.join(os.path.join(BASE_DIR, 'temp'), file_name)

    def write(self, data: dict):
        with open(self.toml_file_path, "w", encoding="utf-8") as fs:
            toml.dump(data, fs)

    def read(self):
        with open(self.toml_file_path, "r", encoding="utf-8") as fs:
            t_data = toml.load(fs)
        return t_data


@celery.task
def call_actor(data: dict):
    cookie = data['cli']['name'][0]
    cli = Cli(cookie)
    cli.write(data)
    file = cli.toml_file_path
    command = f"{QAACOUNTPRO_RS_RELEASE}/{QAACOUNTPRO_RS_MAIN} {file}"
    print(command)
    #
    cmd = shlex.split(command)
    p = subprocess.Popen(
        cmd, shell=True, close_fds=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    while p.poll() is None:
        try:
            line = p.stdout.readline()
        except Exception as e:
            line = p.stdout.readline().decode('gbk')
        print(line)
    return "done"

    # with FlowTask(cookie) as ft:
    #     cmd = shlex.split(command)
    #     p = subprocess.Popen(
    #         cmd, shell=True, close_fds=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    #     while p.poll() is None:
    #         try:
    #             line = p.stdout.readline().decode()
    #         except Exception as e:
    #             line = p.stdout.readline().decode('gbk')
    #         if line:
    #             ft.listen(line)
