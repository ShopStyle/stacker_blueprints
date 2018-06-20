import inspect
import unittest

from awacs.aws import Policy
from troposphere import iam

from stacker.testutil import StackerTestCase
from stacker_blueprints.policies import (
    cloudwatch_logs_write_statements,
    lambda_basic_execution_statements,
    lambda_basic_execution_policy,
)


def caller():
    return inspect.stack()[2][3]


class PolicyTestCase(StackerTestCase):
    OUTPUT_PATH = "tests/fixtures/policies"

    def assertPolicyRendered(self, policy, test_name=None):
        if test_name is None:
            test_name = caller()

        policy = iam.Policy(
            "Policy",
            PolicyName='TestPolicy',
            PolicyDocument=policy,
        )

        expected_output = "%s/%s.json" % (self.OUTPUT_PATH, test_name)
        self.assertRendered(policy.to_dict(), expected_output)

    def assertStatementsRendered(self, statements):

        policy = Policy(
            Statement=statements,
        )

        self.assertPolicyRendered(policy, caller())


class TestPolicies(PolicyTestCase):

    def test_cloudwatch_logs_write_statements(self):

        self.assertStatementsRendered(
            cloudwatch_logs_write_statements('group', 'stream')
        )

    def test_lambda_basic_execution_statements(self):
        self.assertStatementsRendered(
            lambda_basic_execution_statements('myfunction')
        )

    def test_lambda_basic_execution_policy(self):
        self.assertPolicyRendered(
            lambda_basic_execution_policy('myfunction')
        )


if __name__ == '__main__':
    unittest.main()
