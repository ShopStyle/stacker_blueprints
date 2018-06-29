from awacs.aws import Allow, Statement
from awacs import ecr, logs

from stacker.blueprints.testutil import BlueprintTestCase
from stacker.context import Context
from stacker.exceptions import InvalidConfig
from stacker.variables import Variable

from stacker_blueprints import iam_roles


class TestIamRolesBlueprint(BlueprintTestCase):

    def setUp(self):
        self.common_variables = {}
        self.ctx = Context({
            'namespace': 'test',
            'environment': 'test',
        })

    def generate_variables(self, variable_dict=None):
        return [Variable(k, v) for k, v in self.common_variables.items()]

    def create_blueprint(self, name):
        class TestRole(iam_roles.Roles):
            def generate_policy_statements(self):
                return [
                    Statement(
                        Effect=Allow,
                        Resource=logs.ARN('*', '*', '*'),
                        Action=[
                            logs.CreateLogGroup,
                            logs.CreateLogStream,
                            logs.PutLogEvents
                        ]
                    ),
                    Statement(
                        Effect=Allow,
                        Resource=['*'],
                        Action=[ecr.GetAuthorizationToken, ]
                    )
                ]

        return TestRole(name, self.ctx)

    def test_ec2_role(self):
        self.common_variables = {
            'Ec2Roles': [
                'ec2role'
            ]
        }
        blueprint = self.create_blueprint('test_iam_role_ec2')
        blueprint.resolve_variables(self.generate_variables())
        blueprint.create_template()
        self.assertRenderedBlueprint(blueprint)

    def test_lambda_role(self):
        self.common_variables = {
            'LambdaRoles': [
                'lambdarole'
            ]
        }
        blueprint = self.create_blueprint('test_iam_role_lambda')
        blueprint.resolve_variables(self.generate_variables())
        blueprint.create_template()
        self.assertRenderedBlueprint(blueprint)

    def test_attached_polcies(self):
        self.common_variables = {
            'Ec2Roles': [
                'ec2role'
            ],
            'AttachedPolicies': [
                'arn:aws:iam::aws:policy/CloudWatchLogsFullAccess'
            ],
        }
        blueprint = self.create_blueprint('test_iam_role_attached_polcies')
        blueprint.resolve_variables(self.generate_variables())
        blueprint.create_template()
        self.assertRenderedBlueprint(blueprint)

    def test_instance_profile(self):
        self.common_variables = {
            'Ec2Roles': [
                'ec2role'
            ],
            'AttachedPolicies': [
                'arn:aws:iam::aws:policy/CloudWatchLogsFullAccess'
            ],
            'InstanceProfile': True,
        }
        blueprint = self.create_blueprint('test_iam_role_instance_profile')
        blueprint.resolve_variables(self.generate_variables())
        blueprint.create_template()
        self.assertRenderedBlueprint(blueprint)

    def test_empty(self):
        blueprint = self.create_blueprint('test_iam_role_empty')
        blueprint.resolve_variables(self.generate_variables())
        with self.assertRaises(InvalidConfig):
            blueprint.create_template()
