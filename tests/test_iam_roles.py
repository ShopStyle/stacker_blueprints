import pprint  # noqa

from stacker.blueprints.testutil import BlueprintTestCase
from stacker.context import Context
from stacker.variables import Variable

from blueprints import iam_roles


class TestMicroServiceIamRoleBlueprint(BlueprintTestCase):

    def setUp(self):
        self.common_variables = {
            'Name': 'my-policy',
            'EC2Roles': [
                'test-role'
            ]
        }
        self.ctx = Context({
            'namespace': 'test',
            'environment': 'test',
        })

    def create_blueprint(self, name):
        return iam_roles.MicroServiceRole(name, self.ctx)

    def generate_variables(self):
        return [Variable(k, v) for k, v in self.common_variables.items()]

    def test_create_template(self):
        blueprint = self.create_blueprint(
            "test_iam_role_basic"
        )

        blueprint.resolve_variables(self.generate_variables())
        # blueprint.context.config.namespace = "test"
        blueprint.create_template()

        self.assertRenderedBlueprint(blueprint)
