from awacs.aws import Allow, Statement
from awacs import ecr, logs

from stacker.blueprints.testutil import BlueprintTestCase
from stacker.context import Context
from stacker.variables import Variable

from stacker_blueprints import iam_roles


class TestIamRolesBlueprint(BlueprintTestCase):

    def setUp(self):
        self.common_variables = {
            'PolicyName': 'myTest',
            'Ec2Roles': [
                'testrole'
            ]
        }
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
                        Resource=["arn:aws:logs:*:*:*"],
                        Action=[
                            logs.CreateLogGroup,
                            logs.CreateLogStream,
                            logs.PutLogEvents
                        ]
                    ),
                    Statement(
                        Effect=Allow,
                        Resource=["*"],
                        Action=[ecr.GetAuthorizationToken, ]
                    )
                ]

        return TestRole(name, self.ctx)

    def test_create_template(self):
        blueprint = self.create_blueprint(
            "test_iam_role_basic"
        )

        blueprint.resolve_variables(self.generate_variables())
        blueprint.create_template()

        self.assertRenderedBlueprint(blueprint)
