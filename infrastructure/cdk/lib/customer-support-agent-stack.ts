import * as cdk from "aws-cdk-lib/core";

import { Construct } from "constructs";

import { JobsQueue } from "./constructs/jobs.queue";
import { KnowledgeBase } from './constructs/knowledge-base';
import { AgentCore } from './constructs/agentcore';
import { Api } from './constructs/api';
import { Worker } from "./constructs/worker";

export interface CustomerSupportAgentStackProps extends cdk.StackProps {
  readonly environmentName: 'dev' | 'prod'
}


export class CustomerSupportAgentCdkStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: CustomerSupportAgentStackProps) {
    super(scope, id, props);
    const environmentName = props.environmentName;

    cdk.Tags.of(this).add('Project', 'ai-customer-support-agent');
    cdk.Tags.of(this).add('Environment', environmentName);
    cdk.Tags.of(this).add('ManagedBy', 'CDK');

    const jobsQueue = new JobsQueue(this, "JobsInfrastructure", {
      environmentName
    });

    new cdk.CfnOutput(this, "QueueUrl", {
      value: jobsQueue.queue.queueUrl
    });

    const knowledge = new KnowledgeBase(this, 'KnowledgeBase', {
      environmentName
    });

    const agent = new AgentCore(this, 'AgentCore', {
      knowledgeBase: knowledge.knowledgeBase,
      environmentName
    });

    const api = new Api(this, 'Api', {
      jobsQueue: jobsQueue.queue,
      agentRuntime: agent.runtime,
      environmentName
    });

    const worker = new Worker(this, 'Worker', {
      queue: jobsQueue.queue,
      knowledgeBase: knowledge.knowledgeBase,
      agentRuntime: agent.runtime,
      agentMemory: agent.memory,
      environmentName
    });




  }
}
