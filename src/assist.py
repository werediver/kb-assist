from pathlib import Path
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts.chat import ChatPromptTemplate
from langchain_core.messages import AIMessage

# from langchain_ollama.llms import OllamaLLM
from langchain_ollama.chat_models import ChatOllama
from pydantic import BaseModel


class Assist:
    model: BaseChatModel
    prompt = ChatPromptTemplate(
        [
            (
                "system",
                # "Use the available tools to report the subject of the following text in JSON.",
                "Use the available tools to report whether the following text is coherent around its main subject, in JSON.",
            ),
            (
                "user",
                "{content}",
            ),
        ]
    )

    def __init__(self):
        self.model = ChatOllama(
            # model="llama3.2",
            # num_ctx=128 * 1024,
            model="mistral",
            num_ctx=32 * 1024,
            format="json",
        ).bind_tools(
            [ReportTextSubjectCoherency],
            tool_choice="any",
        )
        print(f"Tools bound:\n\n{self.model.kwargs["tools"]}")

    def ponder(self, f: Path):
        s = f.read_text()

        print()
        chain = self.prompt | self.model
        resp = chain.invoke({"content": s})
        if isinstance(resp, AIMessage):
            print(f"Content: {resp.content}")
            if resp.tool_calls:
                print(f"Tool calls: {resp.tool_calls}")


class ReportTextSubjectCoherency(BaseModel):
    """Use this function to report the subject of a text and whether the text is coherent around that subject."""

    subject: str
    is_coherent: bool
