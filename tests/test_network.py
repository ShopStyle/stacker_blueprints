from stacker.context import Context
from stacker.config import Config
from stacker.variables import Variable
from stacker_blueprints.network import Network
from stacker.blueprints.testutil import BlueprintTestCase


class TestNetwork(BlueprintTestCase):
    def setUp(self):
        self.ctx = Context(config=Config({'namespace': 'test'}))
        self.common_variables = {
            "VpcId": "vpc-abc1234",
            "VpcDefaultSecurityGroup": "sg-01234abc",
            "AvailabilityZone": "us-east-1a",
            "CidrBlock": "10.0.0.0/24",
        }

    def create_blueprint(self, name):
        return Network(name, self.ctx)

    def generate_variables(self, variable_dict=None):
        variable_dict = variable_dict or {}
        self.common_variables.update(variable_dict)

        return [Variable(k, v) for k, v in self.common_variables.items()]

    def test_network_fail_internet_nat_gateway(self):
        bp = self.create_blueprint("test_network_fail_internet_nat_gateway")

        variables = {
            "InternetGatewayId": "gw-abc1234z",
            "NatGatewayId": "nat-abc1234z",
        }

        bp.resolve_variables(self.generate_variables(variables))
        with self.assertRaises(ValueError):
            bp.create_template()

    def test_network_fail_nat_gateway_and_create_nat_gateway(self):
        bp = self.create_blueprint(
            "test_network_fail_nat_gateway_and_create_nat_gateway"
        )

        variables = {
            "NatGatewayId": "nat-abc1234z",
            "CreateNatGateway": True,
        }

        bp.resolve_variables(self.generate_variables(variables))
        with self.assertRaises(ValueError):
            bp.create_template()

    def test_network_with_nat_gateway_id(self):
        bp = self.create_blueprint("test_network_with_nat_gateway_id")
        variables = {
            "NatGatewayId": "nat-abc1234z",
        }

        bp.resolve_variables(self.generate_variables(variables))
        bp.create_template()
        self.assertRenderedBlueprint(bp)
        self.assertNotIn("NatGateway", bp.template.resources)
        self.assertEqual(
            bp.template.resources["DefaultRoute"].NatGatewayId,
            "nat-abc1234z"
        )
        self.assertEqual(bp.network_type, "private")

    def test_network_with_internet_gateway_id_and_create_nat_gateway(self):
        bp = self.create_blueprint(
            "test_network_with_internet_gateway_id_and_create_nat_gateway"
        )
        variables = {
            "InternetGatewayId": "igw-abc1234z",
            "CreateNatGateway": True,
        }

        bp.resolve_variables(self.generate_variables(variables))
        bp.create_template()
        self.assertRenderedBlueprint(bp)
        self.assertIn("NatGateway", bp.template.resources)
        self.assertEqual(
            bp.template.resources["DefaultRoute"].GatewayId,
            "igw-abc1234z"
        )
        self.assertEqual(bp.network_type, "public")

    def test_network_with_internet_gateway_id_and_no_create_nat_gateway(self):
        bp = self.create_blueprint(
            "test_network_with_internet_gateway_id_and_no_create_nat_gateway"
        )
        variables = {
            "InternetGatewayId": "igw-abc1234z",
        }

        bp.resolve_variables(self.generate_variables(variables))
        bp.create_template()
        self.assertRenderedBlueprint(bp)
        self.assertNotIn("NatGateway", bp.template.resources)
        self.assertEqual(
            bp.template.resources["DefaultRoute"].GatewayId,
            "igw-abc1234z"
        )
        self.assertEqual(bp.network_type, "public")

    def test_network_with_extra_tags(self):
        bp = self.create_blueprint("test_network_with_extra_tags")
        variables = {
            "NatGatewayId": "nat-abc1234z",
            "Tags": {"A": "apple"},
        }

        bp.resolve_variables(self.generate_variables(variables))
        bp.create_template()
        self.assertRenderedBlueprint(bp)
        route_table = bp.template.resources["RouteTable"]
        found_tag = False
        for tag in route_table.Tags.tags:
            if tag["Key"] == "A" and tag["Value"] == "apple":
                found_tag = True
        self.assertTrue(found_tag)
