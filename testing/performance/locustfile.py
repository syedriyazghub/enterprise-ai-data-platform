"""Performance / load test using Locust."""
from locust import HttpUser, task, between
import random


class ValidationUser(HttpUser):
    wait_time = between(0.5, 2)
    host = "http://localhost:8002"

    @task(3)
    def validate_records(self):
        records = [
            {
                "email": f"user{random.randint(1, 1000)}@example.com",
                "pan": "ABCDE1234F",
                "age": str(random.randint(18, 80)),
            }
            for _ in range(50)
        ]
        self.client.post("/api/v1/validation/validate", json={
            "records": records,
            "rules": [
                {"field": "email", "rule_type": "email"},
                {"field": "pan",   "rule_type": "pan"},
                {"field": "age",   "rule_type": "numeric_range", "params": {"min": 0, "max": 120}},
            ],
        })

    @task(1)
    def list_rules(self):
        self.client.get("/api/v1/validation/rules")

    @task(1)
    def health_check(self):
        self.client.get("/health")


class IngestionUser(HttpUser):
    wait_time = between(1, 3)
    host = "http://localhost:8001"

    @task
    def list_sources(self):
        self.client.get("/api/v1/sources/")

    @task
    def list_jobs(self):
        self.client.get("/api/v1/jobs/")

    @task
    def health_check(self):
        self.client.get("/health")
