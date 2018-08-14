from awacs.aws import Allow, Statement
from awacs import ecr, logs

from stacker.blueprints.testutil import BlueprintTestCase
from stacker.context import Context
from stacker.variables import Variable

from stacker_blueprints import iam_roles


class TestIamRolesCommon(BlueprintTestCase):

    def setUp(self):
        self.common_variables = {}
        self.ctx = Context({
            'namespace': 'test',
            'environment': 'test',
        })

    def generate_variables(self, variable_dict=None):
        return [Variable(k, v) for k, v in self.common_variables.items()]

    def create_blueprint(self, name, class_name):
        class TestRole(class_name):
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


class TestIamRolesBlueprint(TestIamRolesCommon):

    def test_roles(self):
        self.common_variables = {
            'Ec2Roles': [
                'ec2role'
            ],
            'LambdaRoles': [
                'lambdarole'
            ],
        }
        blueprint = self.create_blueprint('test_iam_roles_roles', class_name=iam_roles.Roles)
        blueprint.resolve_variables(self.generate_variables())
        blueprint.create_template()
        self.assertRenderedBlueprint(blueprint)


class TestIamEc2RoleBlueprint(TestIamRolesCommon):

    def test_role(self):
        self.common_variables = {
            'AttachedPolicies': [
                'arn:aws:iam::aws:policy/CloudWatchLogsFullAccess'
            ],
            'InstanceProfile': True,
            'Path': '/',
        }
        blueprint = self.create_blueprint('test_iam_roles_ec2_role', class_name=iam_roles.Ec2Role)
        blueprint.resolve_variables(self.generate_variables())
        blueprint.create_template()
        self.assertRenderedBlueprint(blueprint)

    def test_role_name(self):
        self.common_variables = {
            'AttachedPolicies': [
                'arn:aws:iam::aws:policy/CloudWatchLogsFullAccess'
            ],
            'InstanceProfile': True,
            'Name': 'myRole',
            'Path': '/',
        }
        blueprint = self.create_blueprint('test_iam_roles_ec2_role_name', class_name=iam_roles.Ec2Role)
        blueprint.resolve_variables(self.generate_variables())
        blueprint.create_template()
        self.assertRenderedBlueprint(blueprint)
