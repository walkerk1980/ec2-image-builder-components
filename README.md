# ec2-image-builder-components
A repository of EC2 Image Builder custom Components and an AWS CodePipeLine to deploy them.

Component Pipeline:

![Component PipeLine](image_builder_components_pipeline.PNG)

1. Deploy codepipeline.yaml via Cloudformation to create resources for CodePipeline, CodeCommit, CodeBuild and CodeDeploy and their dependencies.

2. Push this repository into the resulting CodeCommit Repository.

3. Components will deploy via CodePipeline.
