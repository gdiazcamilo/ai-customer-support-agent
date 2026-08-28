import * as cdk from 'aws-cdk-lib/core';
import { Match, Template } from 'aws-cdk-lib/assertions';

import { CustomerSupportAgentCdkStack } from '../lib/customer-support-agent-stack';


let template: Template;

beforeAll(() => {
    const app = new cdk.App();

    const stack = new CustomerSupportAgentCdkStack(
        app,
        'TestStack',
        {
            environmentName: 'dev',
        },
    );

    template = Template.fromStack(stack);
});


test('configures the API Lambda with the jobs queue URL', () => {
    const jobsQueue = template.findResources('AWS::SQS::Queue', {
        Properties: {
            QueueName: 'ai-customer-support-jobs-cdk-dev',
        },
    });

    const jobsQueueLogicalId = Object.keys(jobsQueue)[0];

    template.hasResourceProperties(
        'AWS::Lambda::Function',
        {
            FunctionName: 'ai-customer-support-agent-cdk-dev',
            Environment: {
                Variables: Match.exact({
                    APP_ENV: 'dev',
                    SERVICE_NAME: 'ai-customer-support-agent',
                    LOG_LEVEL: 'INFO',
                    SUPPORT_JOBS_QUEUE_URL: {
                        Ref: jobsQueueLogicalId,
                    },
                }),
            },
        },
    );
});

test('connects the jobs queue to the worker Lambda', () => {
    const queues = template.findResources('AWS::SQS::Queue', {
        Properties: {
            QueueName: 'ai-customer-support-jobs-cdk-dev',
        },
    });

    const jobsQueueLogicalId = Object.keys(queues)[0];

    const functions = template.findResources(
        'AWS::Lambda::Function',
        {
            Properties: {
                FunctionName:
                    'ai-customer-support-worker-cdk-dev',
            },
        },
    );

    const workerLogicalId = Object.keys(functions)[0];

    template.hasResourceProperties(
        'AWS::Lambda::EventSourceMapping',
        {
            EventSourceArn: {
                'Fn::GetAtt': [
                    jobsQueueLogicalId,
                    'Arn',
                ],
            },

            FunctionName: {
                Ref: workerLogicalId,
            },

            BatchSize: 5,

            FunctionResponseTypes: [
                'ReportBatchItemFailures',
            ],
        },
    );
});


test('configures the jobs queue with its dead-letter queue', () => {
    const dlqs = template.findResources('AWS::SQS::Queue', {
        Properties: {
            QueueName:
                'ai-customer-support-jobs-dlq-cdk-dev',
        },
    });

    const dlqLogicalId = Object.keys(dlqs)[0];

    template.hasResourceProperties(
        'AWS::SQS::Queue',
        {
            QueueName:
                'ai-customer-support-jobs-cdk-dev',

            RedrivePolicy: {
                deadLetterTargetArn: {
                    'Fn::GetAtt': [
                        dlqLogicalId,
                        'Arn',
                    ],
                },
                maxReceiveCount: 5,
            },
        },
    );
});


test('exposes the health and chat routes', () => {
    template.hasResourceProperties(
        'AWS::ApiGatewayV2::Route',
        {
            RouteKey: 'GET /health',
        },
    );

    template.hasResourceProperties(
        'AWS::ApiGatewayV2::Route',
        {
            RouteKey: 'POST /chat',
        },
    );
});


test('configures the worker only with AgentCore runtime access', () => {
    const runtimes = template.findResources('AWS::BedrockAgentCore::Runtime');
    const runtimeLogicalId = Object.keys(runtimes)[0];

    template.hasResourceProperties(
        'AWS::Lambda::Function',
        {
            FunctionName: 'ai-customer-support-worker-cdk-dev',
            Environment: {
                Variables: Match.exact({
                    APP_ENV: 'dev',
                    SERVICE_NAME: 'ai-customer-support-worker',
                    LOG_LEVEL: 'INFO',
                    AGENTCORE_RUNTIME_ARN: {
                        'Fn::GetAtt': [
                            runtimeLogicalId, 'AgentRuntimeArn'
                        ]
                    }
                })
            }
        }
    )
});


test('configures AgentCore Runtime only with its service dependencies', () => {
    const memories = template.findResources(
        'AWS::BedrockAgentCore::Memory',
    );
    const memoryLogicalId = Object.keys(memories)[0];

    const knowledgeBases = template.findResources(
        'AWS::Bedrock::KnowledgeBase',
    );
    const knowledgeBaseLogicalId = Object.keys(knowledgeBases)[0];

    template.hasResourceProperties(
        'AWS::BedrockAgentCore::Runtime',
        {
            EnvironmentVariables: Match.exact({
                APP_ENV: 'dev',
                SERVICE_NAME: 'ai-customer-support-agentcore',
                LOG_LEVEL: 'INFO',
                BEDROCK_MODEL_ID: 'amazon.nova-micro-v1:0',
                KNOWLEDGE_BASE_ID: {
                    'Fn::GetAtt': [
                        knowledgeBaseLogicalId,
                        'KnowledgeBaseId',
                    ],
                },
                AGENTCORE_MEMORY_ID: {
                    'Fn::GetAtt': [
                        memoryLogicalId,
                        'MemoryId',
                    ],
                },
            }),
        },
    );
});
