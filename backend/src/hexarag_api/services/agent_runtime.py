import json

import boto3


class AgentRuntimeService:
    def __init__(self, runtime_arn: str, region: str) -> None:
        self.runtime_arn = runtime_arn
        self.client = boto3.client('bedrock-agentcore', region_name=region)

    def answer(self, session_id: str, message: str, memory_window: list[str]) -> dict:
        payload = json.dumps({'prompt': message, 'memory_window': memory_window})
        response = self.client.invoke_agent_runtime(
            agentRuntimeArn=self.runtime_arn,
            runtimeSessionId=session_id,
            payload=payload,
            qualifier='DEFAULT',
        )
        return json.loads(response['response'].read())
