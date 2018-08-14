# reference:
#  http://stacker.readthedocs.io/en/latest/blueprints.html#testing-blueprints
#
# You should remove this and add your own tests. This is an example.

from stacker.context import Context
from stacker.variables import Variable

from stacker.blueprints.testutil import BlueprintTestCase

from stacker_blueprints import cloudfront


class TestCloudFrontBlueprint(BlueprintTestCase):
    def setUp(self):
        self.ctx = Context({'namespace': 'test', 'environment': 'test'})

    def test_cloudfront(self):
        blueprint = cloudfront.CloudFrontDistribution('test_cloudfront', self.ctx)
        blueprint.resolve_variables([
            Variable('Aliases', ['domain.name']),
            Variable(
                'CacheBehaviors', [{
                    'TargetOriginId': 'AnotherOrigin',
                    'ViewerProtocolPolicy': 'allow-all',
                    'PathPattern': '/',
                    'ForwardedValues': {
                        'QueryString': True,
                    }
                }]
            ),
            Variable(
                'DefaultCacheBehavior', {
                    'TargetOriginId': 'DefaultOrigin',
                    'ViewerProtocolPolicy': 'allow-all',
                    'ForwardedValues': {
                        'QueryString': True,
                    }
                }),
            Variable('Enabled', True),
            Variable(
                'Origins', [
                    {
                        'Id': 'DefaultOrigin',
                        'DomainName': 'bucket.s3.amazonaws.com',
                        'S3OriginConfig': {
                            'OriginAccessIdentity': '',
                        },
                    },
                    {
                        'Id': 'AnotherOrigin',
                        'DomainName': 'mybackend.domain.name',
                        'CustomOriginConfig': {
                            'HTTPPort': 80,
                            'HTTPSPort': 443,
                            'OriginKeepaliveTimeout': 10,
                            'OriginProtocolPolicy': 'match-viewer',
                            'OriginReadTimeout': 20,
                        },
                    }
                ]
            ),
            Variable(
                'Tags', {
                    'A': 'Tag',
                }
            ),
        ])

        blueprint.create_template()
        self.assertRenderedBlueprint(blueprint)
