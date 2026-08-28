import * as logs from 'aws-cdk-lib/aws-logs'
import * as iam from 'aws-cdk-lib/aws-iam';
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as agentcore from 'aws-cdk-lib/aws-bedrockagentcore';
import * as cdk from "aws-cdk-lib/core";
import * as path from 'path';
import * as bedrock from 'aws-cdk-lib/aws-bedrock';

import { Construct } from "constructs";

export interface AgentCoreProps {
    knowledgeBase: bedrock.CfnKnowledgeBase;
    environmentName: string
}


export class AgentCore extends Construct {
    public readonly runtime: agentcore.Runtime;
    public readonly memory: agentcore.Memory;

    constructor(scope: Construct, id: string, props: AgentCoreProps) {
        super(scope, id);

        this.memory = new agentcore.Memory(this, 'Memory',
            {
                memoryName: 'ai_customer_support_memory_cdk_dev',
                description: 'Short-term conversational memory for the customer support agent',
                expirationDuration: cdk.Duration.days(30),
            }
        );

        const agentRuntimeArtifact = agentcore.AgentRuntimeArtifact.fromCodeAsset({
            path: path.join(__dirname, '../../../..'),
            assetHashType: cdk.AssetHashType.OUTPUT,
            runtime: agentcore.AgentCoreRuntime.PYTHON_3_14,
            entrypoint: ['agentcore_app.py'],

            bundling: {
                image: cdk.DockerImage.fromRegistry('scratch'),
                local: {
                    tryBundle(outputDir: string) {
                        const { execFileSync } = require('child_process');

                        execFileSync(
                            'uv',
                            [
                                'pip',
                                'install',
                                '--python-platform',
                                'aarch64-manylinux2014',
                                '--python-version',
                                '3.14',
                                '--target',
                                outputDir,
                                '--only-binary=:all:',
                                '-r',
                                path.join(__dirname, '../../../../requirements.txt'),
                            ],
                            { stdio: 'inherit' },
                        );

                        execFileSync(
                            'cp',
                            ['-R', `${path.join(__dirname, '../../../../src')}/.`, outputDir],
                            { stdio: 'inherit' },
                        );

                        return true;
                    },
                },
            },
        });

        this.runtime = new agentcore.Runtime(this, 'Runtime',
            {
                runtimeName: 'ai_customer_support_agent_cdk_dev',
                description: 'Runtime for the AI Customer Support Agent',
                agentRuntimeArtifact,

                environmentVariables: {
                    APP_ENV: 'dev',
                    SERVICE_NAME: 'ai-customer-support-agentcore',
                    LOG_LEVEL: 'INFO',
                    SUPPORT_JOBS_QUEUE_URL: 'REFACTOR_NEEDED',
                    BEDROCK_MODEL_ID: 'amazon.nova-micro-v1:0',
                    KNOWLEDGE_BASE_ID: props.knowledgeBase.attrKnowledgeBaseId,
                    AGENTCORE_MEMORY_ID: this.memory.memoryId,
                },
            });


        this.runtime.addToRolePolicy(
            new iam.PolicyStatement({
                actions: ['bedrock:InvokeModel'],
                resources: [
                    cdk.Stack.of(this).formatArn({
                        service: 'bedrock',
                        account: '',
                        resource: 'foundation-model',
                        resourceName: 'amazon.nova-micro-v1:0',
                    }),
                ],
            }),
        );

        this.runtime.addToRolePolicy(
            new iam.PolicyStatement({
                actions: ['bedrock:Retrieve'],
                resources: [props.knowledgeBase.attrKnowledgeBaseArn],
            }),
        );

        this.runtime.addToRolePolicy(
            new iam.PolicyStatement({
                actions: [
                    'bedrock-agentcore:CreateEvent',
                    'bedrock-agentcore:ListEvents',
                ],
                resources: [this.memory.memoryArn],
            }),
        );

        const gatewayToolsFunction = new lambda.Function(this, 'ToolsGatewayLambdaFunction',
            {
                functionName: `ai-customer-support-gateway-tools-cdk-${props.environmentName}`,
                description: 'Lamba Function for the agent to use tools ',
                runtime: lambda.Runtime.PYTHON_3_14,
                handler: 'functions.gateway_tools.handler.handler',
                code: lambda.Code.fromAsset(path.join(__dirname, '../../../../src')),
                logGroup: new logs.LogGroup(this, 'LogGroup', {
                    retention: logs.RetentionDays.TWO_WEEKS
                })
            },
        );

        const toolsGateway = new agentcore.Gateway(this, 'ToolsGateway',
            {
                gatewayName: `ai-customer-support-gateway-cdk-${props.environmentName}`,
                description: 'Gateway for customer support agent tools',
                authorizerConfiguration:
                    agentcore.GatewayAuthorizer.withNoAuth(),
            }
        );

        const toolSchema = agentcore.ToolSchema.fromInline([
            {
                name: 'get_order',
                description: 'Get the current status of an order',
                inputSchema: {
                    type: agentcore.SchemaDefinitionType.OBJECT,
                    properties: {
                        order_id: {
                            type: agentcore.SchemaDefinitionType.STRING,
                        },
                    },
                    required: ['order_id'],
                },
            },
        ]);

        agentcore.GatewayTarget.forLambda(this, 'ToolsGatewayTarget',
            {
                gateway: toolsGateway,
                gatewayTargetName: `support-tools-cdk-${props.environmentName}`,
                lambdaFunction: gatewayToolsFunction,
                toolSchema,
            },
        );
    }
}