from locust import HttpUser, task, between, constant_pacing, constant_throughput, constant, FastHttpUser

class HelloWorldUser(HttpUser):
    wait_time = constant_throughput()

    @task
    def hello_world(self):
        self.client.get('/heros/')
        self.client.get('/team_members/')
