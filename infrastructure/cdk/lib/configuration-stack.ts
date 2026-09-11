import * as ssm from "aws-cdk-lib/aws-ssm";
import * as cdk from "aws-cdk-lib/core";
import type { Construct } from "constructs";

export interface ConfigurationStackProps extends cdk.StackProps {
	readonly environmentName: "dev" | "prod";
}

export class ConfigurationStack extends cdk.Stack {
	public readonly bedrockPromptParameterName: string;

	constructor(scope: Construct, id: string, props: ConfigurationStackProps) {
		super(scope, id, props);

		const environmentName = props.environmentName;

		cdk.Tags.of(this).add("Project", "ai-customer-support-agent");
		cdk.Tags.of(this).add("Environment", environmentName);
		cdk.Tags.of(this).add("ManagedBy", "CDK");

		this.bedrockPromptParameterName = `/ai-customer-support/${environmentName}/bedrock-system-prompt-arn`;

		new ssm.StringParameter(this, "BedrockSystemPromptParameter", {
			parameterName: this.bedrockPromptParameterName,
			description:
				"Active Bedrock system prompt version used by the customer support agent",
			stringValue: "arn:aws:bedrock:us-east-1:214078205303:prompt/MPNW37K8XZ:2",
		});
	}
}
