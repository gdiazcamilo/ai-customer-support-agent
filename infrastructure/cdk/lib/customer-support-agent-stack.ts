import * as iam from 'aws-cdk-lib/aws-iam';
import * as cdk from "aws-cdk-lib/core";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as path from 'path';
import * as apigwv2 from 'aws-cdk-lib/aws-apigatewayv2';
import * as apigw from 'aws-cdk-lib/aws-apigateway';
import * as logs from 'aws-cdk-lib/aws-logs';
import * as agentcore from 'aws-cdk-lib/aws-bedrockagentcore';

import { Construct } from "constructs";
import { SqsEventSource } from 'aws-cdk-lib/aws-lambda-event-sources';
import { HttpLambdaIntegration } from 'aws-cdk-lib/aws-apigatewayv2-integrations';

import { JobsQueue } from "./constructs/jobs.queue";
import { KnowledgeBase } from './constructs/knowledge-base';

export class CustomerSupportAgentCdkStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const jobsQueue = new JobsQueue(this, "JobsInfrastructure");

    new cdk.CfnOutput(this, "QueueUrl", {
      value: jobsQueue.queue.queueUrl
    });

    const knowledge = new KnowledgeBase(this, 'KnowledgeBase');



    const agentMemory = new agentcore.Memory(this, 'SupportAgentMemory', {
      memoryName: 'ai_customer_support_memory_cdk_dev',
      description: 'Short-term conversational memory for the customer support agent',
      expirationDuration: cdk.Duration.days(30),
    });

    const agentRuntimeArtifact = agentcore.AgentRuntimeArtifact.fromCodeAsset({
      path: path.join(__dirname, '../../..'),
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
                path.join(__dirname, '../../../requirements.txt'),
              ],
              { stdio: 'inherit' },
            );

            execFileSync(
              'cp',
              ['-R', `${path.join(__dirname, '../../../src')}/.`, outputDir],
              { stdio: 'inherit' },
            );

            return true;
          },
        },
      },
    });

    const agentRuntime = new agentcore.Runtime(this, 'SupportAgentRuntime', {
      runtimeName: 'ai_customer_support_agent_cdk_dev',
      description: 'Runtime for the AI Customer Support Agent',
      agentRuntimeArtifact,

      environmentVariables: {
        APP_ENV: 'dev',
        SERVICE_NAME: 'ai-customer-support-agentcore',
        LOG_LEVEL: 'INFO',
        SUPPORT_JOBS_QUEUE_URL: jobsQueue.queue.queueUrl,
        BEDROCK_MODEL_ID: 'amazon.nova-micro-v1:0',
        KNOWLEDGE_BASE_ID: knowledge.knowledgeBase.attrKnowledgeBaseId,
        AGENTCORE_MEMORY_ID: agentMemory.memoryId,
      },
    });


    agentRuntime.addToRolePolicy(
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

    agentRuntime.addToRolePolicy(
      new iam.PolicyStatement({
        actions: ['bedrock:Retrieve'],
        resources: [knowledge.knowledgeBase.attrKnowledgeBaseArn],
      }),
    );

    agentRuntime.addToRolePolicy(
      new iam.PolicyStatement({
        actions: [
          'bedrock-agentcore:CreateEvent',
          'bedrock-agentcore:ListEvents',
        ],
        resources: [agentMemory.memoryArn],
      }),
    );

    const gatewayToolsFunction = new lambda.Function(
      this,
      'GatewayToolsLambdaFunction',
      {
        functionName: 'ai-customer-support-gateway-tools-cdk-dev',
        description: 'Lamba Function for the agent ',
        runtime: lambda.Runtime.PYTHON_3_14,
        handler: 'functions.gateway_tools.handler.handler',
        code: lambda.Code.fromAsset(path.join(__dirname, '../../../src')),
      },
    );

    const toolsGateway = new agentcore.Gateway(this, 'SupportToolsGateway', {
      gatewayName: 'ai-customer-support-gateway-cdk-dev',
      description: 'Gateway for customer support agent tools',
      authorizerConfiguration:
        agentcore.GatewayAuthorizer.withNoAuth(),
    });

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

    agentcore.GatewayTarget.forLambda(
      this,
      'SupportToolsGatewayTarget',
      {
        gateway: toolsGateway,
        gatewayTargetName: 'support-tools-cdk-dev',
        lambdaFunction: gatewayToolsFunction,
        toolSchema,
      },
    );

    const apiFunction = new lambda.Function(this, 'ApiLambdaFunction', {
      functionName: 'ai-customer-support-agent-cdk-dev',
      description: 'API for the AI Customer Support Agent',
      runtime: lambda.Runtime.PYTHON_3_14,
      code: lambda.Code.fromAsset(path.join(__dirname, '../../../src')),
      handler: 'functions.api.handler.handler',
      memorySize: 128,
      timeout: cdk.Duration.seconds(30),
      logGroup: new logs.LogGroup(this, 'ApiLambdaLogGroup', {
        logGroupName: '/aws/lambda/ai-customer-support-agent-cdk-dev',
        retention: logs.RetentionDays.TWO_WEEKS
      }),
      environment: {
        APP_ENV: 'dev',
        SERVICE_NAME: 'ai-customer-support-agent',
        LOG_LEVEL: 'INFO',
        SUPPORT_JOBS_QUEUE_URL: jobsQueue.queue.queueUrl,
        BEDROCK_MODEL_ID: 'amazon.nova-micro-v1:0',
        KNOWLEDGE_BASE_ID: knowledge.knowledgeBase.attrKnowledgeBaseId,
        AGENTCORE_RUNTIME_ARN: agentRuntime.agentRuntimeArn,
        AGENTCORE_MEMORY_ID: agentMemory.memoryId,
      },
    });

    jobsQueue.queue.grantSendMessages(apiFunction);

    const apiIntegration = new HttpLambdaIntegration('ApiLambdaIntegration', apiFunction);

    const httpApi = new apigwv2.HttpApi(this, 'SupportHttpApi', {
      apiName: 'ai-customer-support-agent-api-cdk-dev',
      description: 'HTTP Api for the AI Customer Support Agent',
      defaultIntegration: apiIntegration,
      createDefaultStage: false,
    });

    new cdk.CfnOutput(this, 'ApiUrl', {
      value: httpApi.apiEndpoint
    });

    const apiAccessLogGroup = new logs.LogGroup(this, 'ApiGatewayAccessLogGroup', {
      logGroupName: '/aws/apigateway/ai-customer-support-agent-cdk-dev',
      retention: logs.RetentionDays.TWO_WEEKS,
    });

    new apigwv2.HttpStage(this, 'ApiDefaultStage', {
      httpApi,
      stageName: '$default',
      autoDeploy: true,
      accessLogSettings: {
        destination: new apigwv2.LogGroupLogDestination(apiAccessLogGroup),
        format: apigw.AccessLogFormat.custom(
          '{"request_id":"$context.requestId","method":"$context.httpMethod","route_key":"$context.routeKey","path":"$context.path","status":"$context.status","response_length":"$context.responseLength","response_latency":"$context.responseLatency","source_ip":"$context.identity.sourceIp"}'
        ),
      },
    });

    httpApi.addRoutes({
      path: '/health',
      methods: [apigwv2.HttpMethod.GET],
      integration: apiIntegration,
    });

    httpApi.addRoutes({
      path: '/chat',
      methods: [apigwv2.HttpMethod.POST],
      integration: apiIntegration,
    });

    const workerFunction = new lambda.Function(this, 'SupportJobsWorkerLambdaFunction', {
      functionName: 'ai-customer-support-worker-cdk-dev',
      description: 'Processes support jobs pulled from SQS',
      runtime: lambda.Runtime.PYTHON_3_14,
      code: lambda.Code.fromAsset(path.join(__dirname, '../../../src')),
      handler: 'functions.worker.handler.handler',
      memorySize: 128,
      timeout: cdk.Duration.seconds(30),
      logGroup: new logs.LogGroup(this, 'WorkerLambdaLogGroup', {
        logGroupName: '/aws/lambda/ai-customer-support-worker-cdk-dev',
        retention: logs.RetentionDays.TWO_WEEKS
      }),
      environment: {
        APP_ENV: 'dev',
        SERVICE_NAME: 'ai-customer-support-worker',
        LOG_LEVEL: 'INFO',
        SUPPORT_JOBS_QUEUE_URL: jobsQueue.queue.queueUrl,
        BEDROCK_MODEL_ID: 'amazon.nova-micro-v1:0',
        KNOWLEDGE_BASE_ID: knowledge.knowledgeBase.attrKnowledgeBaseId,
        AGENTCORE_RUNTIME_ARN: agentRuntime.agentRuntimeArn,
        AGENTCORE_MEMORY_ID: agentMemory.memoryId,
      },
    });

    workerFunction.addEventSource(new SqsEventSource(jobsQueue.queue, {
      batchSize: 5,
      reportBatchItemFailures: true,
    }));

    workerFunction.addToRolePolicy(
      new iam.PolicyStatement({
        actions: ['bedrock-agentcore:InvokeAgentRuntime'],
        resources: [
          agentRuntime.agentRuntimeArn,
          `${agentRuntime.agentRuntimeArn}/runtime-endpoint/DEFAULT`,
        ],
      }),
    );


  }
}
