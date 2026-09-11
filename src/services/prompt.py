import boto3

from agentcore_config import AGENTCORE_SETTINGS

ssm = boto3.client("ssm")
bedrock = boto3.client("bedrock-agent")


def load_system_prompt() -> str:
    parameter = ssm.get_parameter(
        Name=AGENTCORE_SETTINGS.bedrock_prompt_parameter_name,
    )

    prompt_arn = parameter["Parameter"]["Value"]

    resource = prompt_arn.rsplit("/", 1)[1]
    prompt_id, version = resource.rsplit(":", 1)

    response = bedrock.get_prompt(
        promptIdentifier=prompt_id,
        promptVersion=version,
    )

    default_variant_name = response["defaultVariant"]

    default_variant = next(
        variant
        for variant in response["variants"]
        if variant["name"] == default_variant_name
    )

    system_blocks = default_variant["templateConfiguration"]["chat"]["system"]

    result: str = "\n".join(str(block.get("text") or "") for block in system_blocks)
    return result
