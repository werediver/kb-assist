from typing import Literal
from langchain_core.language_models.base import LanguageModelOutput
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts.chat import ChatPromptTemplate
from langchain_core.messages import AIMessage

from langchain_ollama.chat_models import ChatOllama
from pydantic import BaseModel

from md_utils import deemphasize_subject, remove_tags


class Assist:
    model: BaseChatModel

    def __init__(self):
        self.model = (
            ChatOllama(
                # Fast and good at using the tools, but somewhat dumb.
                # model="llama3.2",
                # num_ctx=128 * 1024,
                #
                # Smart enough and okay at using tools.
                # model="mistral",
                # num_ctx=32 * 1024,
                #
                # Smarter than Mistral 7B and good at using tools.
                model="qwen2.5-coder:7b",
                num_ctx=32 * 1024,
                #
                # Less good at using tools than the "-coder" version.
                # model="qwen2.5:7b",
                # num_ctx=32 * 1024,
                format="json",
            )
            .bind_tools(
                [
                    # ReportTextSubjectConsistency,
                    ReportArticleQuality,
                ],
                tool_choice="any",
            )
            .with_retry()
        )
        print(f"Tools bound:\n\n{self.model.kwargs["tools"]}")

    def assess_subject_consistency(self, s: str):
        s = deemphasize_subject(s)
        s = remove_tags(s)

        chain = (
            _subject_consistency_prompt | self.model | assert_tool_calls
        ).with_retry(stop_after_attempt=5)

        resp = chain.invoke({"content": s})

        if isinstance(resp, AIMessage):
            print(f"Content: {resp.content}")
            if resp.tool_calls:
                print(f"Tool calls: {resp.tool_calls}")

    def assess_article_quality(self, s: str):
        s = remove_tags(s)

        chain = (_article_quality_prompt | self.model | assert_tool_calls).with_retry(
            stop_after_attempt=5
        )

        resp = chain.invoke({"content": s})

        if isinstance(resp, AIMessage):
            print(f"Content: {resp.content}")
            if resp.tool_calls:
                print(f"Tool calls: {resp.tool_calls}")


def assert_tool_calls(resp: LanguageModelOutput) -> LanguageModelOutput:
    if isinstance(resp, AIMessage) and resp.tool_calls:
        return resp
    else:
        raise Exception("Tool calls expected")


_subject_consistency_prompt = ChatPromptTemplate(
    [
        (
            "system",
            "Use the available tools to report whether the following text is consistent with its main subject, in JSON.",
            # "Use the available tools to report whether the following text is focused on the single matter of its main subject, in JSON.",
        ),
        (
            "user",
            "{content}",
        ),
    ]
)

_article_quality_prompt = ChatPromptTemplate(
    [
        (
            "system",
            "Use the available tools to report the subject, the subject presentation issues, and the quality of the following Markdown-formatted article, in JSON. Asses the requested parameters critically.",
        ),
        (
            "user",
            "{content}",
        ),
    ]
)


class ReportTextSubjectConsistency(BaseModel):
    """Use this function to report the subject of a text and whether the text is consistent with that subject."""

    # """Use this function to report the subject of a text and whether the text is focused on the single matter of its main subject."""

    subject: str
    is_consistent: bool


class ReportArticleQuality(BaseModel):
    """Use this function to report the subject, the subject presentation issues, and the quality of an article."""

    subject: str
    issues: list[str]
    quality: Literal["poor", "fair", "good", "excellent"]
