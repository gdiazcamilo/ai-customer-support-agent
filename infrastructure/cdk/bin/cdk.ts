#!/usr/bin/env node
import * as cdk from "aws-cdk-lib/core";
import { ConfigurationStack } from "../lib/configuration-stack";
import { CustomerSupportAgentCdkStack } from "../lib/customer-support-agent-stack";

const app = new cdk.App();

const environmentName = "dev";

const configurationStack = new ConfigurationStack(
	app,
	"CustomerSupportConfigurationStack",
	{
		environmentName,
	},
);

new CustomerSupportAgentCdkStack(app, "CustomerSupportAgentCdkStack", {
	environmentName: "dev",
	bedrockPromptParameter: configurationStack.bedrockPromptParameterName,
});
