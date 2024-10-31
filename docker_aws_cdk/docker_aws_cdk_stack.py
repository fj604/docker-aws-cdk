from aws_cdk import (
    # Duration,
    Stack,
    # aws_sqs as sqs,
)
from constructs import Construct
import aws_cdk.aws_ecs_patterns as ecs_patterns
from aws_cdk.aws_ecr_assets import DockerImageAsset
import aws_cdk.aws_ecs as ecs
import aws_cdk.aws_iam as iam
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

        asset = DockerImageAsset(
            self,
            "DockerImageAsset",
            directory=path.join(path.dirname(__file__), "docker_app"),
        )

        topic_arn = self.node.try_get_context("sns_topic_arn")

        load_balanced_fargate_service = (
            ecs_patterns.ApplicationLoadBalancedFargateService(
                self,
                "Service",
                task_image_options={
                    "image": ecs.ContainerImage.from_docker_image_asset(asset),
                    "container_port": 8501,
                    "environment": {"SNS_TOPIC_ARN": topic_arn},
                },
            )
        )

        load_balanced_fargate_service.task_definition.add_to_task_role_policy(
            iam.PolicyStatement(
                actions=["sns:Publish"],
                resources=[topic_arn],
            )
        )
