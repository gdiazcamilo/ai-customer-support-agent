import * as ssm from "aws-cdk-lib/aws-ssm";
import { Construct } from "constructs";

export interface BedrockConfigurationProps {
	readonly environmentName: "dev" | "prod";
	readonly bedrockPromptParameterName: string;
}

export class BedrockConfiguration extends Construct {
	public readonly promptParameter: ssm.StringParameter;

	constructor(scope: Construct, id: string, props: BedrockConfigurationProps) {
		super(scope, id);

		this.promptParameter = new ssm.StringParameter(
			this,
			"SystemPromptParameter",
			{
				parameterName: props.bedrockPromptParameterName,
				description:
					"Active Bedrock system prompt version used by the customer support agent",
				stringValue:
					"arn:aws:bedrock:us-east-1:214078205303:prompt/MPNW37K8XZ:1",
			},
		);
	}
}
