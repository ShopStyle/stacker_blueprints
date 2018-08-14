from stacker.blueprints.base import Blueprint

from troposphere import (
    ec2,
    cloudwatch,
    elasticloadbalancingv2 as alb,
    Output,
    Tags,
)


class LoadBalancer(Blueprint):

    VARIABLES = {
        'Name': {
            'type': str,
            'description': 'Specifies a name for the load balancer.'
        },
        'Scheme': {
            'type': str,
            'description': 'Specifies whether the load balancer is internal or '
                           'Internet-facing. Valid values are internet-facing '
                           'and internal. The default is internet-facing.'
        },
        'SecurityGroups': {
            'type': list,
            'description': 'Specifies a list of the IDs of the security groups '
                           'to assign to the load balancer.',
            'default': [],
        },
        'IngressRules': {
            'type': list,
            'description': 'A dict of ingress rules where the key is the '
                           'name of the rule to create.',
            'default': [],
        },
        'EgressRules': {
            'type': list,
            'description': 'A dict of ingress rules where the key is the '
                           'name of the rule to create.',
            'default': [],
        },
        'SubnetIds': {
            'type': list,
            'description': 'The subnets to attach to the load balancer, '
                           'specified as a list of subnet IDs. '
        },
        'Tags': {
            'type': dict,
            'description': 'Specifies an arbitrary set of tags (key-value pairs) '
                           'to associate with this load balancer. Use tags to manage '
                           'your resources.',
            'default': {},
        },
        'Type': {
            'type': str,
            'description': 'Specifies the type of load balancer to create.  Valid values '
                           'are application and network.The default is application.'
        },
        'IpAddressType': {
            'type': str,
            'description': 'The type of IP addresses that are used by the load balancers '
                           'subnets, such as ipv4 (for IPv4 addresses) or dualstack.'
        },
        'VpcId': {
            'type': str,
            'description': 'The physical ID of the VPC.'
        },
        'TargetGroups': {
            'type': list,
            'description': 'List of target groups to attach to the load balancer.'
        },
        'Listeners': {
            'type': list,
            'description': 'List of listeners for the load balancer.'
        },
        'Alarms': {
            'type': list,
            'description': 'List of alarms for the load balancer.'
        },
    }

    def create_alarm(self, alarm_name, alarm):
        t = self.template

        alarm.setdefault('Namespace', 'AWS/ApplicationELB')
        alarm_name = alarm_name.replace('_', '').replace('-', '')

        alarm_resource = t.add_resource(
            cloudwatch.Alarm.from_dict(alarm_name, alarm)
        )

        t.add_output(
            Output(alarm_name, Value=alarm_resource.Ref())
        )

        t.add_output(
            Output(alarm_name + "Arn", Value=alarm_resource.GetAtt("Arn"))
        )

    def create_load_balancer(self):
        t = self.template
        v = self.get_variables()

        ingress_rules = v['IngressRules']
        egress_rules = v['EgressRules']
        security_groups = v['SecurityGroups']
        tags = v['Tags']
        tags.setdefault('Name', v['Name'])

        if ingress_rules or egress_rules:
            name = '{}-alb'.format(v['Name'])
            security_group = t.add_resource(
                ec2.SecurityGroup(
                    'SECGROUP',
                    GroupName=name,
                    GroupDescription='Security group for {}'.format(v['Name']),
                    SecurityGroupIngress=ingress_rules,
                    SecurityGroupEgress=egress_rules,
                    Tags=Tags({
                        'Name': name,
                    }),
                    VpcId=v['VpcId'],
                )
            )
            security_groups.append(security_group.Ref())

        logical_name = 'ALB'

        load_balancer = t.add_resource(
            alb.LoadBalancer(
                'ALB',
                Name=v['Name'],
                Scheme=v['Scheme'],
                IpAddressType=v['IpAddressType'],
                SecurityGroups=security_groups,
                Subnets=v['SubnetIds'],
                Tags=Tags(tags),
                Type=v['Type'],
            )
        )

        alarms = v.get("Alarms", [])
        for alarm in alarms:
            alarm_name = '{}Alarm{}'.format(logical_name, alarm['MetricName'])

            alarm['Dimensions'] = [
                {
                    'Name': 'LoadBalancer',
                    'Value': load_balancer.GetAtt('LoadBalancerFullName'),
                },
            ]

            self.create_alarm(alarm_name, alarm)

        t.add_output(
            Output('LoadBalancerArn', Value=load_balancer.Ref())
        )

        for attr in ('DNSName', 'CanonicalHostedZoneID', 'LoadBalancerFullName', 'LoadBalancerName'):
            t.add_output(
                Output(attr, Value=load_balancer.GetAtt(attr))
            )

        return load_balancer

    def create_target_groups(self, load_balancer):
        t = self.template
        v = self.get_variables()
        target_groups = {}

        for tg in v['TargetGroups']:
            # target groups have a max length of 32 chars
            logical_name = 'TARGET{}'.format(tg['Port'])
            hc = tg['HealthCheck']

            hc_attrs = {
                'HealthCheckIntervalSeconds': hc['IntervalSeconds'],
                'HealthCheckPath': hc['Path'],
                'HealthCheckTimeoutSeconds': hc['TimeoutSeconds'],
                'HealthyThresholdCount': hc['HealthyThresholdCount'],
                'UnhealthyThresholdCount': hc['UnhealthyThresholdCount'],
            }

            hc_port = hc.get('Port')
            if hc_port:
                hc_attrs['HealthCheckPort'] = hc_port

            hc_protocol = hc.get('Protocol')
            if hc_protocol:
                hc_attrs['HealthCheckProtocol'] = hc_protocol.upper()

            tags = tg.get('Tags', {})
            tags.setdefault('Name', tg['Name'])

            target_group = t.add_resource(
                alb.TargetGroup(
                    logical_name,
                    Matcher=alb.Matcher(
                        HttpCode=','.join(str(sc) for sc in hc['SuccessCodes'])
                    ),
                    Name=tg['Name'],
                    Port=tg['Port'],
                    Protocol=tg['Protocol'].upper(),
                    Tags=Tags(tags),
                    Targets=[
                        alb.TargetDescription(Id=instance_id)
                        for instance_id in tg.get('Targets', [])
                    ],
                    TargetType=tg['TargetType'],
                    VpcId=v['VpcId'],
                    **hc_attrs
                )
            )

            for attr in ['TargetGroupFullName', 'TargetGroupName']:
                t.add_output(
                    Output(logical_name + attr, Value=target_group.GetAtt(attr))
                )

            target_groups[tg['Name']] = target_group

            alarms = tg.get("Alarms", [])
            for alarm in alarms:
                alarm_name = '{}Alarm{}'.format(logical_name, alarm['MetricName'])

                alarm['Dimensions'] = [
                    {
                        'Name': 'LoadBalancer',
                        'Value': load_balancer.GetAtt('LoadBalancerFullName'),
                    },
                    {
                        'Name': 'TargetGroup',
                        'Value': target_group.GetAtt('TargetGroupFullName'),
                    },
                ]

                self.create_alarm(alarm_name, alarm)

        return target_groups

    def create_listeners(self, load_balancer, target_groups):
        t = self.template
        v = self.get_variables()

        for l in v['Listeners']:

            attrs = {
                'DefaultActions': [
                    alb.Action(
                        TargetGroupArn=target_groups[a['TargetGroup']].Ref(),
                        Type=a['Type'],
                    ) for a in l['DefaultActions']
                ],
                'LoadBalancerArn': load_balancer.Ref(),
                'Port': l['Port'],
                'Protocol': l['Protocol'],
            }

            certs = l.get('Certificates')
            if certs:
                attrs['Certificates'] = [
                    alb.Certificate(
                        CertificateArn=cert
                    ) for cert in certs
                ]

            listener = t.add_resource(
                alb.Listener(
                    'LISTENER{}'.format(l['Port']),
                    **attrs
                )
            )

            t.add_output(
                Output('Listener{}Arn'.format(l['Port']), Value=listener.Ref())
            )

    def create_template(self):

        load_balancer = self.create_load_balancer()
        target_groups = self.create_target_groups(load_balancer)
        self.create_listeners(load_balancer, target_groups)
