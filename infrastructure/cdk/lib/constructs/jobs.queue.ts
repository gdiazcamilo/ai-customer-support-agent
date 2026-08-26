import { Construct } from 'constructs';
import { Duration } from 'aws-cdk-lib';
import * as sqs from 'aws-cdk-lib/aws-sqs';

export class JobsQueue extends Construct {
    public readonly queue: sqs.Queue;
    public readonly deadLetterQueue: sqs.Queue;

    constructor(scope: Construct, id: string) {
        super(scope, id);

        this.deadLetterQueue = new sqs.Queue(this, 'DeadLetterQueue', {
            queueName: 'ai-customer-support-jobs-dlq-cdk-dev',
        });

        this.queue = new sqs.Queue(this, 'Queue', {
            queueName: 'ai-customer-support-jobs-cdk-dev',
            visibilityTimeout: Duration.seconds(60),
            deadLetterQueue: {
                queue: this.deadLetterQueue,
                maxReceiveCount: 5,
            },
        });
    }
}
