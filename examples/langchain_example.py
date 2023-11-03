from typing import Any, Dict, List

import boto3
import newrelic.agent
from langchain.agents import AgentType, initialize_agent
from langchain.chat_models import ChatOpenAI, BedrockChat
from langchain.llms import Bedrock
from langchain.llms.base import LLM
from langchain.tools import Tool
from nr_openai_observability.langchain_callback import NewRelicCallbackHandler


@newrelic.agent.background_task()
@newrelic.agent.function_trace(name="langchain-openai")
def runLangchainOpenAI(prompt):
    new_relic_monitor = NewRelicCallbackHandler()

    openai_llm = ChatOpenAI(temperature=0)

    openai_agent = get_agent(openai_llm)
    print("Langchain with OpenAI")
    result = openai_agent.run(prompt, callbacks=[new_relic_monitor])
    print(f"prompt: {prompt}")
    print(f"result: {result}")
    print("\n\n")


@newrelic.agent.background_task()
@newrelic.agent.function_trace(name="langchain-bedrock")
def runLangchainBedrock(prompt):
    new_relic_monitor = NewRelicCallbackHandler()

    boto_client = boto3.client("bedrock-runtime", "us-east-1")
    bedrock_llm = BedrockChat(
        model_id="anthropic.claude-instant-v1",  # "anthropic.claude-v2",
        client=boto_client,
    )

    bedrock_agent = get_agent(bedrock_llm)
    print("Langchain with Bedrock")
    result = bedrock_agent.run(prompt, callbacks=[new_relic_monitor])

    print(f"prompt: {prompt}")
    print(f"result: {result}")
    print("\n\n")


def get_agent(llm: LLM):
    return initialize_agent(
        [
            Tool(
                func=math,
                name="Calculator",
                description="useful for when you need to answer questions about math",
            )
        ],
        llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        stop="stop_sequence",
    )


def math(x):
    print(f"Running math tool with input {x}. Returning 4.")
    return 4


if __name__ == "__main__":
    # Enable New Relic Python agent. You must make sure your application name is either defined in the ini file below
    # or in the environment variable NEW_RELIC_APP_NAME
    newrelic.agent.initialize("newrelic.ini")
    newrelic.agent.register_application(timeout=10)

    prompt = "What is 2 + 2?"

    runLangchainOpenAI(prompt)
    runLangchainBedrock(prompt)

    # Allow the New Relic agent to send final messages as part of shutdown
    # The agent by default can send data up to a minute later
    newrelic.agent.shutdown_agent(60)

    print("Agent run finished!")
