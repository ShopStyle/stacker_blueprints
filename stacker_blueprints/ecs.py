from awacs.helpers.trust import get_ecs_task_assumerole_policy

from troposphere import (
    ecs,
    iam,
)

from troposphere import (
    NoValue,
    Output,
    Region,
    Sub,
)

from stacker.blueprints.base import Blueprint
from stacker.blueprints.variables.types import TroposphereType

from .policies import ecs_task_execution_policy


class Cluster(Blueprint):
    def create_template(self):
        t = self.template

        cluster = t.add_resource(ecs.Cluster("Cluster"))

        t.add_output(Output("ClusterId", Value=cluster.Ref()))
        t.add_output(Output("ClusterArn", Value=cluster.GetAtt("Arn")))


class BaseECSService(Blueprint):
    VARIABLES = {
        "ServiceName": {
            "type": str,
            "description": "A simple name for the service.",
        },
        "Image": {
            "type": str,
            "description": "The docker image to use for the task.",
        },
        "Command": {
            "type": list,
            "description": "A list of the command and it's arguments to run "
                           "inside the container. If not provided, will "
                           "default to the default command defined in the "
                           "image.",
            "default": [],
        },
        "Cluster": {
            "type": str,
            "description": "The name or Amazon Resource Name (ARN) of the "
                           "ECS cluster that you want to run your tasks on.",
        },
        "CPU": {
            "type": int,
            "description": "The relative CPU shares used by each instance of "
                           "the task.",
        },
        "Memory": {
            "type": int,
            "description": "The amount of memory (in megabytes) to reserve "
                           "for each instance of the task.",
        },
        "Count": {
            "type": int,
            "description": "The number of instances of the task to create.",
            "default": 1,
        },
        "Environment": {
            "type": dict,
            "description": "A dictionary representing the environment of the "
                           "task.",
            "default": {},
        },
        "LogConfiguration": {
            "type": TroposphereType(ecs.LogConfiguration, optional=True),
            "description": "An optional log configuration object. If one is "
                           "not provided, the default is to send logs into "
                           "a Cloudwatch Log LogGroup named after the "
                           "ServiceName",
            "default": None,
        },
        "TaskRoleArn": {
            "type": str,
            "description": "An optional role to run the task as.",
            "default": "",
        },
        "ContainerPort": {
            "type": int,
            "description": "The port of the container to expose to the "
                           "network.  Defaults to not exposing any ports.",
            "default": 0,
        },
        "HostPort": {
            "type": int,
            "description": "The host port to bind to the container port, if "
                           "ContainerPort is specified. If not, does "
                           "nothing. If HostPort is not specified, a dynamic "
                           "port mapping will be used.",
            "default": 0,
        },
        "ContainerProtocol": {
            "type": str,
            "description": "If set, must be either tcp or udp. Requires that "
                           "ContainerPort is set as well. Default: tcp",
            "default": "",
        },
        "DeploymentConfiguration": {
            "type": TroposphereType(
                ecs.DeploymentConfiguration,
                optional=True
            ),
            "description": "An optional DeploymentConfiguration object.",
            "default": None,
        },
        "LoadBalancers": {
            "type": TroposphereType(
                ecs.LoadBalancer,
                many=True,
                optional=True
            ),
            "description": "An optional list of LoadBalancers to attach to "
                           "the service.",
            "default": None,
        },
        "HealthCheckGracePeriodSeconds": {
            "type": int,
            "description": "An optional grace period for load balancer health "
                           "checks against the service when it starts up.",
            "default": 0,
        },

    }

    @property
    def service_name(self):
        return self.get_variables()["ServiceName"]

    @property
    def image(self):
        return self.get_variables()["Image"]

    @property
    def command(self):
        return self.get_variables()["Command"] or NoValue

    @property
    def cluster(self):
        return self.get_variables()["Cluster"]

    @property
    def cpu(self):
        return self.get_variables()["CPU"]

    @property
    def memory(self):
        return self.get_variables()["Memory"]

    @property
    def count(self):
        return self.get_variables()["Count"]

    @property
    def environment(self):
        env_dict = self.get_variables()["Environment"]
        if not env_dict:
            return NoValue

        env_list = []
        # Sort it first to avoid dict sort issues on different machines
        sorted_env = sorted(env_dict.items(), key=lambda pair: pair[0])
        for k, v in sorted_env:
            env_list.append(ecs.Environment(Name=str(k), Value=str(v)))

        return env_list

    @property
    def log_configuration(self):
        log_config = self.get_variables()["LogConfiguration"]
        if not log_config:
            log_config = ecs.LogConfiguration(
                LogDriver="awslogs",
                Options={
                    "awslogs-group": self.service_name,
                    "awslogs-region": Region,
                    "awslogs-stream-prefix": self.service_name,
                }
            )
        return log_config

    @property
    def task_role_arn(self):
        return self.get_variables()["TaskRoleArn"]

    @property
    def network_mode(self):
        return NoValue

    @property
    def launch_type(self):
        return "EC2"

    @property
    def network_configuration(self):
        return NoValue

    @property
    def container_port(self):
        return self.get_variables()["ContainerPort"]

    @property
    def host_port(self):
        if not self.container_port:
            raise ValueError("Must specify ContainerPort if specifying "
                             "HostPort")
        return self.get_variables()["HostPort"]

    @property
    def container_protocol(self):
        if not self.container_port:
            raise ValueError("Must specify ContainerPort if specifying "
                             "ContainerProtocol")
        return self.get_variables()["ContainerProtocol"]

    @property
    def container_port_mappings(self):
        mappings = NoValue
        if self.container_port:
            kwargs = {"ContainerPort": self.container_port}
            if self.host_port:
                kwargs["HostPort"] = self.host_port
            if self.container_protocol:
                kwargs["Protocol"] = self.container_protocol
            mappings = [ecs.PortMapping(**kwargs)]
        return mappings

    @property
    def deployment_configuration(self):
        return self.get_variables()["DeploymentConfiguration"] or NoValue

    @property
    def load_balancers(self):
        return self.get_variables()["LoadBalancers"] or NoValue

    @property
    def health_check_grace_period_seconds(self):
        grace_period = self.get_variables()["HealthCheckGracePeriodSeconds"]
        if grace_period and self.load_balancers is NoValue:
            raise ValueError("Cannot specify HealthCheckGracePeriodSeconds "
                             "without specifying LoadBalancers")
        return grace_period or NoValue

    def create_task_role(self):
        if self.task_role_arn:
            self.add_output("RoleArn", self.task_role_arn)
            return

        t = self.template

        self.task_role = t.add_resource(
            iam.Role(
                "Role",
                AssumeRolePolicyDocument=get_ecs_task_assumerole_policy(),
                Path="/",
            )
        )

        self.add_output("RoleName", self.task_role.Ref())
        self.add_output("RoleArn", self.task_role.GetAtt("Arn"))
        self.add_output("RoleId", self.task_role.GetAtt("RoleId"))

    def generate_policy_document(self):
        return None

    def create_task_role_policy(self):
        policy_doc = self.generate_policy_document()
        if self.task_role_arn or not policy_doc:
            return

        t = self.template

        self.task_role_policy = t.add_resource(
            iam.ManagedPolicy(
                "ManagedPolicy",
                PolicyDocument=policy_doc,
                Roles=[self.task_role.Ref()],
            )
        )

        self.add_output("ManagedPolicyArn", self.task_role_policy.Ref())

    def generate_container_definition(self):
        return ecs.ContainerDefinition(
            Command=self.command,
            Cpu=self.cpu,
            Environment=self.environment,
            Essential=True,
            Image=self.image,
            LogConfiguration=self.log_configuration,
            Memory=self.memory,
            Name=self.service_name,
            PortMappings=self.container_port_mappings,
        )

    def generate_task_definition_kwargs(self):
        task_role_arn = self.task_role_arn or self.task_role.GetAtt("Arn")

        return {
            "Cpu": str(self.cpu),
            "Family": self.service_name,
            "Memory": str(self.memory),
            "NetworkMode": self.network_mode,
            "TaskRoleArn": task_role_arn,
            "ContainerDefinitions": [self.generate_container_definition()],
        }

    def create_task_definition(self):
        t = self.template

        self.task_definition = t.add_resource(
            ecs.TaskDefinition(
                "TaskDefinition",
                **self.generate_task_definition_kwargs()
            )
        )

        self.add_output("TaskDefinitionArn", self.task_definition.Ref())

    def create_service(self):
        t = self.template
        grace_period = self.health_check_grace_period_seconds
        self.service = t.add_resource(
            ecs.Service(
                "Service",
                Cluster=self.cluster,
                DeploymentConfiguration=self.deployment_configuration,
                DesiredCount=self.count,
                HealthCheckGracePeriodSeconds=grace_period,
                LaunchType=self.launch_type,
                LoadBalancers=self.load_balancers,
                NetworkConfiguration=self.network_configuration,
                ServiceName=self.service_name,
                TaskDefinition=self.task_definition.Ref(),
            )
        )

        self.add_output("ServiceArn", self.service.Ref())
        self.add_output("ServiceName", self.service.GetAtt("Name"))

    def create_template(self):
        self.create_task_role()
        self.create_task_role_policy()
        self.create_task_definition()
        self.create_service()


class SimpleFargateService(BaseECSService):
    def defined_variables(self):
        variables = super(SimpleFargateService, self).defined_variables()

        additional_variables = {
            "Subnets": {
                "type": list,
                "description": "The list of VPC subnets to deploy the task "
                               "in.",
            },
            "SecurityGroup": {
                "type": str,
                "description": "The SecurityGroup to attach to the task.",
            },
        }

        variables.update(additional_variables)
        return variables

    @property
    def subnets(self):
        return self.get_variables()["Subnets"]

    @property
    def security_group(self):
        return self.get_variables()["SecurityGroup"]

    @property
    def network_mode(self):
        return "awsvpc"

    @property
    def launch_type(self):
        return "FARGATE"

    @property
    def network_configuration(self):
        return ecs.NetworkConfiguration(
            AwsvpcConfiguration=ecs.AwsvpcConfiguration(
                SecurityGroups=[self.security_group],
                Subnets=self.subnets,
            )
        )

    def create_task_execution_role(self):
        t = self.template

        self.task_execution_role = t.add_resource(
            iam.Role(
                "TaskExecutionRole",
                AssumeRolePolicyDocument=get_ecs_task_assumerole_policy(),
            )
        )

        t.add_output(
            Output(
                "TaskExecutionRoleName",
                Value=self.task_execution_role.Ref()
            )
        )

        t.add_output(
            Output(
                "TaskExecutionRoleArn",
                Value=self.task_execution_role.GetAtt("Arn")
            )
        )

    def generate_task_execution_policy(self):
        policy_args = {}
        log_config = self.log_configuration
        if log_config.LogDriver == "awslogs":
            policy_args["log_group"] = log_config.Options["awslogs-group"]

        return ecs_task_execution_policy(**policy_args)

    def create_task_execution_role_policy(self):
        t = self.template

        policy_name = Sub("${AWS::StackName}-task-exeuction-role-policy")

        self.task_execution_role_policy = t.add_resource(
            iam.PolicyType(
                "TaskExecutionRolePolicy",
                PolicyName=policy_name,
                PolicyDocument=self.generate_task_execution_policy(),
                Roles=[self.task_execution_role.Ref()],
            )
        )

    def generate_task_definition_kwargs(self):
        kwargs = super(
            SimpleFargateService, self
        ).generate_task_definition_kwargs()

        kwargs["ExecutionRoleArn"] = self.task_execution_role.GetAtt("Arn")
        return kwargs

    def create_template(self):
        self.create_task_execution_role()
        self.create_task_execution_role_policy()
        super(SimpleFargateService, self).create_template()


class SimpleECSService(BaseECSService):
    pass
