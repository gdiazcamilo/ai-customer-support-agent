import { Construct } from 'constructs';
import { Duration } from 'aws-cdk-lib';
import * as sqs from 'aws-cdk-lib/aws-sqs';
import * as cdk from 'aws-cdk-lib';

export class JobsQueue extends Construct {
    public readonly queue: sqs.IQueue;
    public readonly deadLetterQueue: sqs.IQueue;

    constructor(scope: Construct, id: string, props: {
        environmentName: string
    }) {
        super(scope, id);

        this.deadLetterQueue = new sqs.Queue(this, 'DeadLetterQueue', {
            queueName: `ai-customer-support-jobs-dlq-cdk-${props.environmentName}`,
        });

        this.queue = new sqs.Queue(this, 'Queue', {
            queueName: `ai-customer-support-jobs-cdk-${props.environmentName}`,
            visibilityTimeout: Duration.seconds(60),
            deadLetterQueue: {
                queue: this.deadLetterQueue,
                maxReceiveCount: 5,
            },
        });
    }
}
