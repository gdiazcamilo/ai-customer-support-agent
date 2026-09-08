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

  MODEL_ID = 'amazon.nova-micro-v1:0'

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
          APP_ENV: props.environmentName,
          SERVICE_NAME: 'ai-customer-support-agentcore',
          LOG_LEVEL: 'INFO',
          BEDROCK_MODEL_ID: this.MODEL_ID,
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
            resourceName: this.MODEL_ID,
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

    const systemPromptText = [
      'You are a concise customer support assistant.',
      '',
      '- Answer clearly and briefly.',
      '- Use tools when you need external information.',
      '- Do not invent information.',
      '- Do not claim that an action happened unless a tool successfully performed it.',
      '- When using retrieved company documentation, only answer with information supported by the retrieved content.',
      '- If the retrieved content does not contain enough information to answer, say that you do not have enough information.',
      '- Distinguish general policy questions from requests about specific entities: use policy search for general shipping, return, or warranty questions; use order lookup only when the user is asking about a specific existing order.',
      '- Do not imply that you can perform future research or follow-up actions unless an available tool actually supports that action.',
      '- When answering from retrieved company documentation, do not add facts, explanations, assumptions, or general knowledge that are not explicitly supported by the retrieved content.',
      '- Do not include source URLs, document links, or citations in your answer. Source attribution is handled separately by the application.',
      '- Use the conversation history provided in the messages to answer follow-up questions.',
      '- When previous messages are available, do not claim that you cannot remember or access the previous conversation.',
      '- If the user asks what they were discussing, summarize the relevant previous messages.',
    ].join('\n');

    const prompt = new bedrock.CfnPrompt(this, 'SystemPrompt', {
      name: `ai_customer_support_system_prompt_${props.environmentName}`,
      description: 'System prompt for the AI Customer Support Agent',
      defaultVariant: 'default',
      variants: [
        {
          name: 'default',
          templateType: 'CHAT',
          modelId: this.MODEL_ID,
          templateConfiguration: {
            chat: {
              messages: [],
              system: [
                {
                  text: systemPromptText,
                },
              ],
            },
          },
        },
      ],
    });

    const promptVersion = new bedrock.CfnPromptVersion(this, 'SystemPromptVersion',
      {
        promptArn: prompt.attrArn,
        description: 'Initial customer support system prompt',
      },
    );

    const gatewayToolsFunction = new lambda.Function(this, 'ToolsGatewayLambdaFunction',
      {
        functionName: `ai-customer-support-gateway-tools-cdk-${props.environmentName}`,
        description: 'Lamba Function for the agent to use tools ',
        runtime: lambda.Runtime.PYTHON_3_14,
        handler: 'functions.gateway_tools.handler.handler',
        code: lambda.Code.fromAsset(path.join(__dirname, '../../../../src')),
        logGroup: new logs.LogGroup(this, 'LogGroup', {
          logGroupName: `ai-customer-support-gateway-tools-cdk-${props.environmentName}`,
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
