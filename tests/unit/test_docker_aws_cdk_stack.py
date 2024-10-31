import aws_cdk as core
import aws_cdk.assertions as assertions

from docker_aws_cdk.docker_aws_cdk_stack import DockerAwsCdkStack

# example tests. To run these tests, uncomment this file along with the example
# resource in docker_aws_cdk/docker_aws_cdk_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = DockerAwsCdkStack(app, "docker-aws-cdk")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
