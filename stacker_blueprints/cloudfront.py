from stacker.blueprints.base import Blueprint
from stacker_blueprints import route53

from troposphere import (
    cloudfront,
    Output,
    Tags,
)

from stacker.blueprints.variables.types import TroposphereType


class CloudFrontDistribution(Blueprint):
    """
    Creates a CloudFront distribution.

    https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/quickref-cloudfront.html
    https://docs.aws.amazon.com/cloudfront/latest/APIReference/API_CacheBehavior.html
    https://docs.aws.amazon.com/cloudfront/latest/APIReference/API_DistributionConfig.html
    https://docs.aws.amazon.com/cloudfront/latest/APIReference/API_Origin.html
    https://docs.aws.amazon.com/cloudfront/latest/APIReference/API_Types.html
    """
    VARIABLES = {
        "Aliases": {
            "type": list,
            "description": "Aliases that point to the CloudFront Distribtuion",
            "default": [],
        },
        "CacheBehaviors": {
            "type": TroposphereType(
                cloudfront.CacheBehavior,
                many=True
            ),
            "description": "Describes how CloudFront processes requests "
                           "There should be one cache behavior per origin",
            "default": None,
        },
        "Comment": {
            "type": str,
            "description": "Any comments you want to include about the distribution.",
            "default": "",
        },
        "CustomErrorResponses": {
            "type": TroposphereType(
                cloudfront.CustomErrorResponse,
                many=True,
            ),
            "description": "List of CustomErrorResponses",
            "default": [],
        },
        "DefaultCacheBehavior": {
            "type": TroposphereType(
                cloudfront.DefaultCacheBehavior,
            ),
            "description": "The default cache behavior if you don't specify "
                           " a CacheBehavior (required)",
        },
        "DefaultRootObject": {
            "type": str,
            "description": "The object that you want CloudFront to request from "
                           "your origin (for example, index.html) ",
            "default": "",
        },
        "Enabled": {
            "type": bool,
            "description": "Enable or disable the selected distribution",
        },
        "HttpVersion": {
            "type": str,
            "description": "Specify the maximum HTTP version that you want viewers "
                           "to use to communicate with CloudFront.",
            "default": "",
        },
        "IPV6Enabled": {
            "type": bool,
            "description": "If you want CloudFront to respond to IPv6 DNS requests "
                           "with an IPv6 address for your distribution, specify true.",
            "default": False,
        },
        "Logging": {
            "type": dict,
            "description": "A complex type that controls whether access logs are written "
                           "for the distribution.",
            "default": {},
        },
        "Origins": {
            "type": TroposphereType(
                cloudfront.Origin,
                many=True
            ),
            "description": "Define where CloudFront gets your files. "
                           "You must create at least one origin",
            "default": None,
        },
        "PriceClass": {
            "type": str,
            "description": "The price class that corresponds with the maximum price "
                           "that you want to pay for CloudFront service. If you specify "
                           "PriceClass_All, CloudFront responds to requests for your "
                           "objects from all CloudFront edge locations.",
            "default": "PriceClass_100",
        },
        "Restrictions": {
            "type": TroposphereType(
                cloudfront.Restrictions,
                optional=True,
            ),
            "description": "A complex type that identifies ways in which you want to "
                           "restrict distribution of your content.",
            "default": None,
        },
        "Tags": {
            "type": dict,
            "description": "An optional dictionary of tags to put on the "
                           "CloudFront distributions.",
            "default": {},
        },
        "ViewerCertificate": {
            "type": TroposphereType(
                cloudfront.ViewerCertificate,
            ),
            "description": "",
            "default": {
                "CloudFrontDefaultCertificate": True,
            },
        },
        "WebACLId": {
            "type": str,
            "description": "A unique identifier that specifies the AWS WAF web ACL, "
                           "if any, to associate with this distribution.",
            "default": "",
        },
    }

    @property
    def tags(self):
        v = self.get_variables()
        tag_var = v["Tags"]
        t = {"Name": self.name}
        t.update(tag_var)
        t['Stacker'] = 'Created by Stacker'
        return Tags(**t)

    @property
    def origins(self):
        return self.get_variables()['Origins']

    @property
    def cache_behaviors(self):
        return self.get_variables()['CacheBehaviors']

    @property
    def default_cache_behavior(self):
        return self.get_variables()['DefaultCacheBehavior']

    @property
    def custom_error_responses(self, ):
        return self.get_variables()['CustomErrorResponses']

    @property
    def restrictions(self):
        return self.get_variables()['Restrictions']

    @property
    def viewer_certificate(self):
        return self.get_variables()['ViewerCertificate']

    @property
    def logging(self):
        return self.get_variables()['Logging']

    @property
    def distribution_config_attrs(self):
        v = self.get_variables()

        attrs = {
            'Aliases': v['Aliases'],
            'CacheBehaviors': self.cache_behaviors,
            'Comment': v['Comment'],
            'CustomErrorResponses': self.custom_error_responses,
            'DefaultCacheBehavior': self.default_cache_behavior,
            'DefaultRootObject': v['DefaultRootObject'],
            'Enabled': v['Enabled'],
            'IPV6Enabled': v['IPV6Enabled'],
            'Origins': self.origins,
            'PriceClass': v['PriceClass'],
            'ViewerCertificate': self.viewer_certificate,
            'WebACLId': v['WebACLId'],
        }

        if v['HttpVersion']:
            attrs['HttpVersion'] = v['HttpVersion']

        if v['Logging']:
            attrs['Logging'] = self.logging

        if v['Restrictions']:
            attrs['Restrictions'] = self.restrictions

        return attrs

    @property
    def distribution_attrs(self):
        return {
            'DistributionConfig': cloudfront.DistributionConfig(
                **self.distribution_config_attrs
            ),
            'Tags': self.tags,
        }

    def create_template(self):
        t = self.template
        distribution = t.add_resource(
            cloudfront.Distribution('CFDIST', **self.distribution_attrs)
        )
        t.add_output(
            Output("DistributionId", Value=distribution.Ref())
        )
        t.add_output(
            Output("DomainName", Value=distribution.GetAtt("DomainName"))
        )
        t.add_output(
            Output("HostedZoneId", Value=route53.CLOUDFRONT_ZONE_ID)
        )
