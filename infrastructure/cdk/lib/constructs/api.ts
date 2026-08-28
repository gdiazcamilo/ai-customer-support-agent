import * as agentcore from 'aws-cdk-lib/aws-bedrockagentcore'
import * as sqs from 'aws-cdk-lib/aws-sqs'
import * as iam from 'aws-cdk-lib/aws-iam';
import * as cdk from "aws-cdk-lib/core";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as path from 'path';
import * as apigwv2 from 'aws-cdk-lib/aws-apigatewayv2';
import * as apigw from 'aws-cdk-lib/aws-apigateway';
import * as logs from 'aws-cdk-lib/aws-logs';

import { Construct } from "constructs";
import { HttpLambdaIntegration } from 'aws-cdk-lib/aws-apigatewayv2-integrations';


export class Api extends Construct {
    public readonly httpApi: apigwv2.HttpApi;
    public readonly lambda: lambda.Function;

    constructor(scope: Construct, id: string, props: {
        jobsQueue: sqs.IQueue
        agentRuntime: agentcore.Runtime
        environmentName: string
    }) {
        super(scope, id);

        this.lambda = new lambda.Function(this, 'LambdaFunction',
            {
                functionName: `ai-customer-support-agent-cdk-${props.environmentName}`,
                description: 'API for the AI Customer Support Agent',
                runtime: lambda.Runtime.PYTHON_3_14,
                code: lambda.Code.fromAsset(path.join(__dirname, '../../../../src')),
                handler: 'functions.api.handler.handler',
                memorySize: 128,
                timeout: cdk.Duration.seconds(30),
                logGroup: new logs.LogGroup(this, 'LogGroup', {
                    logGroupName: `/aws/lambda/ai-customer-support-agent-cdk-${props.environmentName}`,
                    retention: logs.RetentionDays.TWO_WEEKS
                }),
                environment: {
                    APP_ENV: `${props.environmentName}`,
                    SERVICE_NAME: 'ai-customer-support-agent',
                    LOG_LEVEL: 'INFO',
                    SUPPORT_JOBS_QUEUE_URL: props.jobsQueue.queueUrl,
                    BEDROCK_MODEL_ID: 'amazon.nova-micro-v1:0',
                    KNOWLEDGE_BASE_ID: 'REFACTOR_NEEDED',
                    AGENTCORE_RUNTIME_ARN: props.agentRuntime.agentRuntimeArn,
                    AGENTCORE_MEMORY_ID: 'REFACTOR_NEEDED',
                },
            }
        );

        props.jobsQueue.grantSendMessages(this.lambda);

        const apiIntegration = new HttpLambdaIntegration('LambdaIntegration', this.lambda);

        this.httpApi = new apigwv2.HttpApi(this, 'HttpApi',
            {
                apiName: `ai-customer-support-agent-api-cdk-${props.environmentName}`,
                description: 'HTTP Api for the AI Customer Support Agent',
                defaultIntegration: apiIntegration,
                createDefaultStage: false,
            }
        );


        const apiAccessLogGroup = new logs.LogGroup(this, 'GatewayAccessLogGroup', {
            logGroupName: `/aws/apigateway/ai-customer-support-agent-cdk-${props.environmentName}`,
            retention: logs.RetentionDays.TWO_WEEKS,
        });


        new apigwv2.HttpStage(this, 'DefaultStage', {
            httpApi: this.httpApi,
            stageName: '$default',
            autoDeploy: true,
            accessLogSettings: {
                destination: new apigwv2.LogGroupLogDestination(apiAccessLogGroup),
                format: apigw.AccessLogFormat.custom(
                    '{"request_id":"$context.requestId","method":"$context.httpMethod","route_key":"$context.routeKey","path":"$context.path","status":"$context.status","response_length":"$context.responseLength","response_latency":"$context.responseLatency","source_ip":"$context.identity.sourceIp"}'
                ),
            },
        });

        this.httpApi.addRoutes({
            path: '/health',
            methods: [apigwv2.HttpMethod.GET],
            integration: apiIntegration,
        });

        this.httpApi.addRoutes({
            path: '/chat',
            methods: [apigwv2.HttpMethod.POST],
            integration: apiIntegration,
        });

    }
}