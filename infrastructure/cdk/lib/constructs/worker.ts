import * as iam from 'aws-cdk-lib/aws-iam';
import * as cdk from "aws-cdk-lib/core";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as path from 'path';
import * as logs from 'aws-cdk-lib/aws-logs';
import * as sqs from 'aws-cdk-lib/aws-sqs';
import * as bedrock from 'aws-cdk-lib/aws-bedrock';
import * as agentcore from 'aws-cdk-lib/aws-bedrockagentcore';
import { Construct } from 'constructs';
import { SqsEventSource } from 'aws-cdk-lib/aws-lambda-event-sources';


export class Worker extends Construct {
    constructor(scope: Construct, id: string, props: {
        environmentName: string,
        queue: sqs.IQueue,
        knowledgeBase: bedrock.CfnKnowledgeBase,
        agentRuntime: agentcore.Runtime,
        agentMemory: agentcore.Memory
    }) {
        super(scope, id);

        const workerFunction = new lambda.Function(this, 'LambdaFunction',
            {
                functionName: `ai-customer-support-worker-cdk-${props.environmentName}`,
                description: 'Processes support jobs pulled from SQS',
                runtime: lambda.Runtime.PYTHON_3_14,
                code: lambda.Code.fromAsset(path.join(__dirname, '../../../../src')),
                handler: 'functions.worker.handler.handler',
                memorySize: 128,
                timeout: cdk.Duration.seconds(30),
                logGroup: new logs.LogGroup(this, 'LogGroup', {
                    logGroupName: `/aws/lambda/ai-customer-support-worker-cdk-${props.environmentName}`,
                    retention: logs.RetentionDays.TWO_WEEKS
                }),
                environment: {
                    APP_ENV: `${props.environmentName}`,
                    SERVICE_NAME: 'ai-customer-support-worker',
                    LOG_LEVEL: 'INFO',
                    SUPPORT_JOBS_QUEUE_URL: props.queue.queueUrl,
                    BEDROCK_MODEL_ID: 'amazon.nova-micro-v1:0',
                    KNOWLEDGE_BASE_ID: props.knowledgeBase.attrKnowledgeBaseId,
                    AGENTCORE_RUNTIME_ARN: props.agentRuntime.agentRuntimeArn,
                    AGENTCORE_MEMORY_ID: props.agentMemory.memoryId,
                },
            });

        workerFunction.addEventSource(new SqsEventSource(props.queue, {
            batchSize: 5,
            reportBatchItemFailures: true,
        }));

        workerFunction.addToRolePolicy(
            new iam.PolicyStatement({
                actions: ['bedrock-agentcore:InvokeAgentRuntime'],
                resources: [
                    props.agentRuntime.agentRuntimeArn,
                    `${props.agentRuntime.agentRuntimeArn}/runtime-endpoint/DEFAULT`,
                ],
            }),
        );
    }
}