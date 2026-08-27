import * as iam from 'aws-cdk-lib/aws-iam';
import * as cdk from "aws-cdk-lib/core";
import { Construct } from "constructs";
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as s3vectors from 'aws-cdk-lib/aws-s3vectors';
import * as bedrock from 'aws-cdk-lib/aws-bedrock';

export class KnowledgeBase extends Construct {
    public readonly knowledgeBase: bedrock.CfnKnowledgeBase;
    // public readonly sourceBucket: s3.Bucket;

    constructor(scope: Construct, id: string, props: {
        environmentName: string
    }) {
        super(scope, id);

        const sourceBucket = new s3.Bucket(this, 'SourceBucket');

        const vectorBucket = new s3vectors.CfnVectorBucket(this, 'VectorBucket',
            {
                vectorBucketName:
                    `squad-prep-ai-customer-support-knowledge-base-vectors-cdk-${props.environmentName}`,
            },
        );

        const vectorIndex = new s3vectors.CfnIndex(this, 'VectorIndex',
            {
                vectorBucketArn: vectorBucket.attrVectorBucketArn,
                indexName: 'knowledge-base-index',
                dataType: 'float32',
                dimension: 1024,
                distanceMetric: 'cosine',
            },
        );

        const serviceRole = new iam.Role(this, 'ServiceRole',
            {
                assumedBy: new iam.ServicePrincipal('bedrock.amazonaws.com'),
            },
        );

        sourceBucket.grantRead(serviceRole);

        const embeddingModelArn = cdk.Stack.of(this).formatArn({
            service: 'bedrock',
            account: '',
            resource: 'foundation-model',
            resourceName: 'amazon.titan-embed-text-v2:0',
        });

        serviceRole.addToPolicy(
            new iam.PolicyStatement({
                actions: ['bedrock:InvokeModel'],
                resources: [embeddingModelArn],
            }),
        );

        serviceRole.addToPolicy(
            new iam.PolicyStatement({
                actions: [
                    's3vectors:PutVectors',
                    's3vectors:GetVectors',
                    's3vectors:DeleteVectors',
                    's3vectors:QueryVectors',
                    's3vectors:GetIndex',
                ],
                resources: [vectorIndex.attrIndexArn],
            }),
        );


        this.knowledgeBase = new bedrock.CfnKnowledgeBase(
            this,
            'KnowledgeBase',
            {
                name: `ai-customer-support-knowledge-base-cdk-${props.environmentName}`,
                roleArn: serviceRole.roleArn,
                knowledgeBaseConfiguration: {
                    type: 'VECTOR',
                    vectorKnowledgeBaseConfiguration: {
                        embeddingModelArn,
                    },
                },
                storageConfiguration: {
                    type: 'S3_VECTORS',
                    s3VectorsConfiguration: {
                        indexArn: vectorIndex.attrIndexArn,
                    },
                },
            },
        );

        this.knowledgeBase.node.addDependency(serviceRole.node.findChild('DefaultPolicy'));

        new bedrock.CfnDataSource(this, 'DataSource',
            {
                name: `ai-customer-support-knowledge-base-data-source-cdk-${props.environmentName}`,
                knowledgeBaseId: this.knowledgeBase.attrKnowledgeBaseId,
                dataDeletionPolicy: 'DELETE',
                dataSourceConfiguration: {
                    type: 'S3',
                    s3Configuration: {
                        bucketArn: sourceBucket.bucketArn,
                    },
                },
            },
        );
    }
}