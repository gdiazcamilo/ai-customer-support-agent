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
import { AgentCore } from './constructs/agentcore';
import { Api } from './constructs/api';

export class CustomerSupportAgentCdkStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const jobsQueue = new JobsQueue(this, "JobsInfrastructure");

    new cdk.CfnOutput(this, "QueueUrl", {
      value: jobsQueue.queue.queueUrl
    });

    const knowledge = new KnowledgeBase(this, 'KnowledgeBase');

    const agent = new AgentCore(this, 'AgentCore', {
      knowledgeBase: knowledge.knowledgeBase,
    })

    const api = f new Api(this, 'Api',
      {
        jobsQueue: jobsQueue.queue,
        agentRuntime: agent.runtime
      }
    );


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
        AGENTCORE_RUNTIME_ARN: agent.runtime.agentRuntimeArn,
        AGENTCORE_MEMORY_ID: agent.memory.memoryId,
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
          agent.runtime.agentRuntimeArn,
          `${agent.runtime.agentRuntimeArn}/runtime-endpoint/DEFAULT`,
        ],
      }),
    );


  }
}
