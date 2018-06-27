from stacker.context import Context
from stacker.variables import Variable
from stacker_blueprints.ecs import Cluster, SimpleFargateService
from stacker.blueprints.testutil import BlueprintTestCase


class TestCluster(BlueprintTestCase):
    def setUp(self):
        self.ctx = Context({'namespace': 'test', 'environment': 'test'})

    def test_ecs_cluster(self):
        bp = Cluster("ecs__cluster", self.ctx)
        bp.resolve_variables([])
        bp.create_template()
        self.assertRenderedBlueprint(bp)


class TestSimpleFargateService(BlueprintTestCase):
    def setUp(self):
        self.common_variables = {
            "ServiceName": "WorkerService",
            "Image": "fake_repo/image:12345",
            "Command": ["/bin/run", "--args 1"],
            "Cluster": "fake-fargate-cluster",
            "CPU": 1024,
            "Memory": 2048,
            "Count": 3,
            "Subnets": ["net-123456", "net-5678910"],
            "SecurityGroup": "sg-abc1234",
            "Environment": {
                "DATABASE_URL": "sql://fake_db/fake_db",
                "DEBUG": "false",
            },
        }

        self.ctx = Context({'namespace': 'test', 'environment': 'test'})

    def create_blueprint(self, name):
        return SimpleFargateService(name, self.ctx)

    def generate_variables(self, variable_dict=None):
        variable_dict = variable_dict or {}
        self.common_variables.update(variable_dict)

        return [Variable(k, v) for k, v in self.common_variables.items()]

    def test_ecs_simple_fargate_service(self):
        bp = self.create_blueprint("ecs__simple_fargate_service")
        bp.resolve_variables(self.generate_variables())
        bp.create_template()
        self.assertRenderedBlueprint(bp)
