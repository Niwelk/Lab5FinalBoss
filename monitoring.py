from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import docker
import subprocess
import time


class ResourceMonitor:
    def init(self, instances_dict):
        self.instances = instances_dict
        self.scheduler = BackgroundScheduler()
        self.setup_jobs()

    def setup_jobs(self):
        self.scheduler.add_job(
            func=self.check_resources,
            trigger="interval",
            seconds=60,
            id="resource_check"
        )
        self.scheduler.start()

    def check_resources(self):
        current_time = datetime.now()

        for instance_id, instance in list(self.instances.items()):
            if instance["status"] != "running":
                continue


            time_limit = timedelta(hours=1)
            if current_time - instance["created_at"] > time_limit:
                self.stop_instance_by_criteria(
                    instance_id,
                    "Превышен лимит времени"
                )
                continue


            if instance["type"] == "container":
                try:
                    docker_client = docker.from_env()
                    container = docker_client.containers.get(instance["docker_id"])
                    stats = container.stats(stream=False)


                    cpu_usage = stats["cpu_stats"]["cpu_usage"]["total_usage"]
                    if cpu_usage > instance["cpu_limit"] * 1e9:  # приблизительно
                        self.stop_instance_by_criteria(
                            instance_id,
                            "Превышен лимит CPU"
                        )

                except Exception as e:
                    print(f"Ошибка проверки контейнера {instance_id}: {e}")

    def stop_instance_by_criteria(self, instance_id, reason):
        print(f"Остановка {instance_id} по критерию: {reason}")
        if instance_id in self.instances:
            self.instances[instance_id]["status"] = "stopped"


monitor = None


def start_monitor(instances_dict):
    global monitor
    monitor = ResourceMonitor(instances_dict)
    return monitor