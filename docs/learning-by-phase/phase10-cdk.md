The main mental model you should carry forward is:

```text
CDK App
  ↓
Stacks = CloudFormation deployment boundaries
  ↓
Constructs = architectural building blocks
  ↓
L2/L1 resources
  ↓
synthesized CloudFormation
  ↓
CloudFormation performs the actual deployment
```

CDK did not replace CloudFormation. It moved us one abstraction level up while still exposing CloudFormation concepts whenever identity, replacement, import, dependencies, or deployment semantics matter.

You now have practical experience with the parts that tend to cause real-world CDK surprises: construct paths affect logical IDs; logical IDs represent CloudFormation identity, not physical AWS identity; physical names do not imply ownership; tokens become `Ref`, `GetAtt`, `Join`, etc.; references often create implicit dependencies; some service readiness conditions require explicit dependencies; and property changes such as an SQS `QueueName` can force replacement even if the logical resource itself remains the same.

The queue migration was particularly valuable because we exercised both sides of resource identity. We released existing queues from the old CloudFormation stack using retention, temporarily treated them as external references, declared them as new CDK-managed resources, adopted the same physical queues with `cdk import`, then rewired the application to use real CDK references again. We also hit a genuine migration failure when changing the queue construct identity caused CDK to generate a new Lambda event-source-mapping logical resource even though the same physical queue/Lambda relationship already existed. That was a good demonstration of the difference between **CloudFormation’s model of identity** and **the service’s real-world uniqueness constraints**.

Testing also reached a useful level. The repository now has a substantial stack assertion test suite rather than only the initial generated test.  The important testing principle is:

```text
weak:
"there is a Lambda"

better:
"the worker is connected to this specific queue"

better:
"this queue has this specific DLQ"

better:
"the API exposes these architectural routes"
```

For important dependencies, we learned not to settle for `Match.anyValue()` when the actual resource identity matters. The stronger pattern is to locate the intended synthesized resource, obtain its generated logical ID, then verify that `Ref` or `Fn::GetAtt` points to that specific logical resource.

`cdk watch` gave us another useful distinction:

```text
Code.fromAsset(...)
→ what gets packaged/deployed

watch.include
→ what filesystem changes trigger another deployment
```

Our nested repository structure exposed a watcher limitation around paths outside the CDK directory, and the symlink experiment isolated that behavior cleanly. Hotswap also clarified that faster development deployments deliberately bypass CloudFormation and therefore introduce temporary drift.

On configuration, we separated two concepts that are easy to confuse:

```text
environmentName: dev/prod
→ application/deployment stage

StackProps.env:
  account + region
→ AWS deployment environment
```

And the precise rule for context lookups is now:

```text
explicit concrete env on the Stack
→ environment-specific stack
→ account/region-dependent lookups can run during synthesis

no env on Stack
→ environment-agnostic stack
→ context lookups cannot resolve a target environment
```

The CLI having `CDK_DEFAULT_ACCOUNT` and `CDK_DEFAULT_REGION` available does not automatically specialize the stack; those values only matter to the stack when you pass them through `env`.

Outputs are now centralized in the stack, which is the direction I prefer: constructs expose useful properties, and the stack decides what becomes part of the deployment’s external interface. The current stack exposes queue URLs, API endpoint, Lambda ARNs, Knowledge Base ID, runtime ARN, and memory ID.  We may eventually decide a couple of those are overly internal, but the ownership location is good.
