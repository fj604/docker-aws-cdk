from aws_cdk import (
    # Duration,
    Stack,
    # aws_sqs as sqs,
)
from constructs import Construct
import aws_cdk.aws_ecs_patterns as ecs_patterns
from aws_cdk.aws_ecr_assets import DockerImageAsset
import aws_cdk.aws_ecs as ecs
import aws_cdk.aws_sns as sns
import aws_cdk.aws_iam as iam
import aws_cdk.aws_cognito as cognito
import aws_cdk.aws_elasticloadbalancingv2 as elbv2
import aws_cdk.aws_route53 as route53
import aws_cdk.aws_route53_targets as route53_targets
import aws_cdk.aws_certificatemanager as acm
import aws_cdk as cdk
from os import path


class DockerAwsCdkStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here

        # example resource
        # queue = sqs.Queue(
        #     self, "DockerAwsCdkQueue",
        #     visibility_timeout=Duration.seconds(300),
        # )

        # cluster: ecs.Cluster

        domain_name = self.node.try_get_context("domain_name")
        subdomain = self.node.try_get_context("subdomain")

        hosted_zone = route53.HostedZone.from_lookup(
            self,
            "HostedZone",
            domain_name=domain_name,
        )

        certificate = acm.Certificate(
            self,
            "Certificate",
            domain_name=f"{subdomain}.{domain_name}",
            validation=acm.CertificateValidation.from_dns(hosted_zone),
        )

        asset = DockerImageAsset(
            self,
            "DockerImageAsset",
            directory=path.join(path.dirname(__file__), "docker_app"),
        )

        # Create an SNS topic
        topic = sns.Topic(
            self,
            "Topic",
        )

        # Output for SNS topic ARN
        cdk.CfnOutput(
            self,
            "TopicArn",
            value=topic.topic_arn,
            description="SNS Topic ARN",
        )

        load_balanced_fargate_service = (
            ecs_patterns.ApplicationLoadBalancedFargateService(
                self,
                "Service",
                task_image_options={
                    "image": ecs.ContainerImage.from_docker_image_asset(asset),
                    "container_port": 8501,
                    "environment": {"SNS_TOPIC_ARN": topic.topic_arn},
                },
                certificate=certificate,
                domain_name=f"{subdomain}.{domain_name}",
                domain_zone=hosted_zone,
                redirect_http=True,
            )
        )

        topic.grant_publish(load_balanced_fargate_service.task_definition.task_role)
        
        # Define a Cognito User Pool and client

        user_pool = cognito.UserPool(
            self,
            "UserPool",
            self_sign_up_enabled=True,
            sign_in_aliases={"email": True},
            removal_policy=cdk.RemovalPolicy.DESTROY,
        )

        callback_urls = [
            f"https://{subdomain}.{domain_name}/oauth2/idpresponse",
        ]

        user_pool_client = user_pool.add_client(
            "UserPoolClient",
            user_pool_client_name="UserPoolClient",
            generate_secret=True,
            o_auth=cognito.OAuthSettings(
                flows=cognito.OAuthFlows(
                    authorization_code_grant=True,
                ),
                scopes=[
                    cognito.OAuthScope.OPENID,
                    cognito.OAuthScope.PROFILE,
                    cognito.OAuthScope.EMAIL,
                ],
                callback_urls=callback_urls,
                logout_urls=[f"https://{subdomain}.{domain_name}"],
            ),
        )

        user_pool_domain = cognito.UserPoolDomain(
            self,
            "UserPoolDomain",
            cognito_domain=cognito.CognitoDomainOptions(
                domain_prefix="my-user-pool-domain",
            ),
            user_pool=user_pool,
        )


        listener = load_balanced_fargate_service.listener

        # Add listener rule for OIDC auth using Cognito User Pool
        listener.add_action(
            "OIDCAction",
            action=elbv2.ListenerAction.authenticate_oidc(
                authorization_endpoint=f"https://{user_pool_domain.domain_name}.auth.{self.region}.amazoncognito.com/oauth2/authorize",
                client_id=user_pool_client.user_pool_client_id,
                client_secret=user_pool_client.user_pool_client_secret,
                scope="openid profile email",
                issuer=f"https://cognito-idp.{self.region}.amazonaws.com/{user_pool.user_pool_id}",
                token_endpoint=f"https://{user_pool_domain.domain_name}.auth.{self.region}.amazoncognito.com/oauth2/token",
                user_info_endpoint=f"https://{user_pool_domain.domain_name}.auth.{self.region}.amazoncognito.com/oauth2/userInfo",
                on_unauthenticated_request=elbv2.UnauthenticatedAction.AUTHENTICATE,
                next=elbv2.ListenerAction.forward(
                    [load_balanced_fargate_service.target_group]
                ),
            ),
            conditions=[elbv2.ListenerCondition.path_patterns(["/*"])],
            priority=1,
        )