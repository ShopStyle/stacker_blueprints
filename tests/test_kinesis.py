import unittest
from stacker.context import Context, Config
from stacker.variables import Variable
from stacker_blueprints.kinesis import Streams
from stacker.blueprints.testutil import BlueprintTestCase


class TestBlueprint(BlueprintTestCase):
    def setUp(self):
        self.variables = [
            Variable('Streams', {
                'Stream1': {
                    'RetentionPeriodHours': 12,
                    'ShardCount': 4,
                    'StreamEncryption': {
                        'EncryptionType': 'KMS',
                        'KeyId': 'kms-1203123',
                    },
                },
                'Stream2': { },
            }),
            Variable('ReadRoles', [
                'Role1',
                'Role2',
            ]),
            Variable('ReadWriteRoles', [
                'Role3',
                'Role4',
            ]),
        ]

    def test_kinesis(self):
        ctx = Context(config=Config({'namespace': 'test'}))
        blueprint = Streams('streams', ctx)
        blueprint.resolve_variables(self.variables)
        blueprint.create_template()
        self.assertRenderedBlueprint(blueprint)
