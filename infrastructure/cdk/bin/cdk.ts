#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib/core';
import { CustomerSupportAgentCdkStack } from '../lib/customer-support-agent-stack';

const app = new cdk.App();
new CustomerSupportAgentCdkStack(app, 'CustomerSupportAgentCdkStack', {
    environmentName: 'dev'
}); 
