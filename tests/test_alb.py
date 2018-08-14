from stacker.context import Context
from stacker.variables import Variable
from stacker.blueprints.testutil import BlueprintTestCase

from stacker_blueprints import alb


class TestAlbBlueprint(BlueprintTestCase):

    def setUp(self):
        self.common_variables = {}
        self.ctx = Context({
            'namespace': 'test',
            'environment': 'test',
        })

    def generate_variables(self):
        return [Variable(k, v) for k, v in self.common_variables.items()]

    def create_blueprint(self, name):
        return alb.LoadBalancer(name, self.ctx)

    def test_load_balancer(self):

        blueprint = self.create_blueprint("test_load_balancer")
        blueprint.resolve_variables([
            Variable("IpAddressType", "ipv4"),
            Variable("VpcId", "vpc-12345678"),
            Variable("Name", "namespace-service"),
            Variable("SubnetIds", [
                "subnet-3bcc6f4d",
                "subnet-40e81e6a",
                "subnet-e05fc8dd",
            ]),
            Variable("EgressRules", [
                {
                    "ToPort": 0,
                    "FromPort": 0,
                    "IpProtocol": "-1",
                    "CidrIp": "0.0.0.0/0"
                },
            ]),
            Variable("IngressRules", [
                {
                    "ToPort": 80,
                    "FromPort": 80,
                    "IpProtocol": "tcp",
                    "CidrIp": "172.18.0.0/22"
                },
                {
                    "ToPort": 443,
                    "FromPort": 443,
                    "IpProtocol": "tcp",
                    "CidrIp": "172.18.0.0/22"
                },
                {
                    "SourceSecurityGroupId": "sg-12345678",
                    "IpProtocol": "tcp",
                    "FromPort": 9200,
                    "ToPort": 9200
                }
            ]),
            Variable("TargetGroups", [
                {
                    "TargetType": "instance",
                    "Protocol": "https",
                    "Name": "Kibana",
                    "HealthCheck": {
                        "HealthyThresholdCount": 5,
                        "SuccessCodes": [
                            200,
                            204
                        ],
                        "TimeoutSeconds": 5,
                        "Path": "/healthcheck",
                        "IntervalSeconds": 10,
                        "UnhealthyThresholdCount": 2
                    },
                    "Port": 443,
                    "Targets": [
                        "i-1234567890"
                    ],
                    "Alarms": [
                        {
                            "ActionsEnabled": True,
                            "AlarmActions": [
                                "arn:aws:sns:us-east-1:<accountid>:<queue-name>",
                            ],
                            "AlarmDescription": "The throttle rate is >= 1",
                            "ComparisonOperator":  "GreaterThanOrEqualToThreshold",
                            "EvaluationPeriods": 1,
                            "MetricName": "Throttles",
                            "Namespace": "AWS/Lambda",
                            "Period": 300,
                            "Statistic": "Sum",
                            "Threshold": "1"
                        }
                    ]
                },
                {
                    "TargetType": "instance",
                    "Protocol": "http",
                    "Name": "Elasticsearch",
                    "HealthCheck": {
                        "HealthyThresholdCount": 5,
                        "SuccessCodes": [
                            200
                        ],
                        "TimeoutSeconds": 5,
                        "Path": "/",
                        "IntervalSeconds": 10,
                        "UnhealthyThresholdCount": 2
                    },
                    "Port": 9200,
                    "Targets": [
                        "i-1234567890"
                    ]
                }
            ]),
            Variable("Listeners", [
                {
                    "Certificates": [
                        "arn:aws:iam::<accountid>:server-certificate/<certificate-name>"
                    ],
                    "DefaultActions": [
                        {
                            "TargetGroup": "Kibana",
                            "Type": "forward"
                        }
                    ],
                    "Protocol": "HTTPS",
                    "Port": 443
                },
                {
                    "DefaultActions": [
                        {
                            "TargetGroup": "Elasticsearch",
                            "Type": "forward"
                        }
                    ],
                    "Protocol": "HTTP",
                    "Port": 9200
                }
            ]),
            Variable("Scheme", "internal"),
            Variable("Type", "application"),
            Variable("Alarms", [
                {
                    "ActionsEnabled": True,
                    "AlarmActions": [
                        "arn:aws:sns:us-east-1:<accountid>:<queue-name>",
                    ],
                    "AlarmDescription": "The error rate is >= 1",
                    "ComparisonOperator":  "GreaterThanOrEqualToThreshold",
                    "EvaluationPeriods": 1,
                    "MetricName": "HTTPCode_Target_5XX_Count",
                    "Period": 300,
                    "Statistic": "Sum",
                    "Threshold": "1"
                }
            ])
        ])

        # blueprint.context.config.namespace = "test"
        blueprint.create_template()
        self.assertRenderedBlueprint(blueprint)
