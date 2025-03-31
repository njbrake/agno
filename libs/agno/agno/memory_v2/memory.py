from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

from pydantic import BaseModel, ConfigDict
from dataclasses import dataclass, field

from agno.memory_v2.summarizer import SessionSummarizer, SessionSummary
from agno.models.base import Model
from agno.models.message import Message
from agno.run.response import RunResponse
from agno.storage.session.agent import AgentSession
from agno.storage.session.team import TeamSession
from agno.utils.log import log_debug, log_info, logger


class MemoryRetrieval(str, Enum):
    last_n = "last_n"
    first_n = "first_n"
    semantic = "semantic"



class AgentRun(BaseModel):
    message: Optional[Message] = None
    messages: Optional[List[Message]] = None
    response: Optional[RunResponse] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def to_dict(self) -> Dict[str, Any]:
        response = {
            "message": self.message.to_dict() if self.message else None,
            "messages": [message.to_dict() for message in self.messages] if self.messages else None,
            "response": self.response.to_dict() if self.response else None,
        }
        return {k: v for k, v in response.items() if v is not None}


@dataclass
class UserMemory:
    """Model for User Memories"""

    memory: str
    topic: Optional[str] = None
    input: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        response = {
            "memory": self.memory,
            "topic": self.topic,
            "input": self.input,
        }
        return {k: v for k, v in response.items() if v is not None}


@dataclass
class Memory:
    # Model used for memories and summaries
    model: Optional[Model] = None

    # Memories per user
    memories: Optional[Dict[str, Dict[str, UserMemory]]] = None

    # Session summaries per user
    session_summaries: Dict[str, Dict[str, SessionSummary]] = {}

    # Summarizer to generate session summaries
    summarizer: Optional[SessionSummarizer] = None

    def __init__(self, model: Optional[Model] = None, summarizer: Optional[SessionSummarizer] = None):
        self.model = model
        self.summarizer = summarizer

    def get_model(self) -> Model:
        if self.model is None:
            try:
                from agno.models.openai import OpenAIChat
            except ModuleNotFoundError as e:
                logger.exception(e)
                logger.error(
                    "Agno uses `openai` as the default model provider. Please provide a `model` or install `openai`."
                )
                exit(1)
            self.model = OpenAIChat(id="gpt-4o")
        return self.model
    
    def get_user_memories(self, user_id: str) -> Dict[str, UserMemory]:
        """Get the user memories for a given user id"""
        return self.memories.get(user_id, {})

    def get_session_summaries(self, user_id: str) -> Dict[str, SessionSummary]:
        """Get the session summaries for a given user id"""
        return self.session_summaries.get(user_id, {})

    def get_user_memory(self, user_id: str, memory_id: str) -> UserMemory:
        """Get the user memory for a given user id"""
        return self.memories.get(user_id, {}).get(memory_id, None)

    def get_session_summary(self, user_id: str, session_id: str) -> SessionSummary:
        """Get the session summary for a given user id"""
        return self.session_summaries.get(user_id, {}).get(session_id, None)

    def add_user_memory(self, user_id: str, memory: UserMemory) -> str:
        """Add a user memory for a given user id"""
        from uuid import uuid4
        memory_id = str(uuid4())
        self.memories.setdefault(user_id, {})[memory_id] = memory
        return memory_id
    
    def delete_user_memory(self, user_id: str, memory_id: str) -> None:
        """Delete a user memory for a given user id"""
        del self.memories[user_id][memory_id]


    def create_session_summary(self, user_id: str, session: Union[AgentSession, TeamSession]) -> Optional[SessionSummary]:
        """Creates a summary of the session"""
        # Initialize the summarizer, with the top-level model, if it is not set
        if self.summarizer is None:
            from copy import deepcopy
            model_copy = deepcopy(self.get_model())
            self.summarizer = SessionSummarizer(model=model_copy)

        summary = self.summarizer.run(self.get_message_pairs())
        self.session_summaries[user_id][session.session_id] = summary

        # TODO: Write to DB
        return summary

    async def acreate_session_summary(self, user_id: str, session: Union[AgentSession, TeamSession]) -> Optional[SessionSummary]:
        """Creates a summary of the session"""
        # Initialize the summarizer, with the top-level model, if it is not set
        if self.summarizer is None:
            from copy import deepcopy
            model_copy = deepcopy(self.get_model())
            self.summarizer = SessionSummarizer(model=model_copy)

        summary = await self.summarizer.arun(self.get_message_pairs())
        self.session_summaries[user_id][session.session_id] = summary

        # TODO: Write to DB
        return summary
    

    def get_message_pairs_for_session(
        self, session: Union[AgentSession, TeamSession], user_role: str = "user", assistant_role: Optional[List[str]] = None
    ) -> List[Tuple[Message, Message]]:
        """Returns a list of tuples of (user message, assistant response)."""

        if assistant_role is None:
            assistant_role = ["assistant", "model", "CHATBOT"]

        runs_as_message_pairs: List[Tuple[Message, Message]] = []
        for run in session.runs:
            if run.response and run.response.messages:
                user_messages_from_run = None
                assistant_messages_from_run = None

                # Start from the beginning to look for the user message
                for message in run.response.messages:
                    if hasattr(message, "from_history") and message.from_history:
                        continue
                    if message.role == user_role:
                        user_messages_from_run = message
                        break

                # Start from the end to look for the assistant response
                for message in run.response.messages[::-1]:
                    if hasattr(message, "from_history") and message.from_history:
                        continue
                    if message.role in assistant_role:
                        assistant_messages_from_run = message
                        break

                if user_messages_from_run and assistant_messages_from_run:
                    runs_as_message_pairs.append((user_messages_from_run, assistant_messages_from_run))
        return runs_as_message_pairs





    # # Runs between the user and agent
    # runs: List[AgentRun] = []
    # # List of messages sent to the model
    # messages: List[Message] = []
    update_system_message_on_change: bool = False

    # Summary of the session
    summary: Optional[SessionSummary] = None
    # Create and store session summaries
    create_session_summaries: bool = False
    # Update session summaries after each run
    update_session_summary_after_run: bool = True
    # Summarizer to generate session summaries
    summarizer: Optional[MemorySummarizer] = None

    # Create and store personalized memories for this user
    create_user_memories: bool = False
    # Update memories for the user after each run
    update_user_memories_after_run: bool = True

    # MemoryDb to store personalized memories
    db: Optional[MemoryDb] = None
    # User ID for the personalized memories
    user_id: Optional[str] = None
    retrieval: MemoryRetrieval = MemoryRetrieval.last_n
    num_memories: Optional[int] = None
    classifier: Optional[MemoryClassifier] = None
    manager: Optional[MemoryManager] = None

    # True when memory is being updated
    updating_memory: bool = False

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def to_dict(self) -> Dict[str, Any]:
        _memory_dict = self.model_dump(
            exclude_none=True,
            include={
                "update_system_message_on_change",
                "create_session_summary",
                "update_session_summary_after_run",
                "create_user_memories",
                "update_user_memories_after_run",
                "user_id",
                "num_memories",
            },
        )
        # Add summary if it exists
        if self.summary is not None:
            _memory_dict["summary"] = self.summary.to_dict()
        # Add memories if they exist
        if self.memories is not None:
            _memory_dict["memories"] = [memory.to_dict() for memory in self.memories]
        # Add messages if they exist
        if self.messages is not None:
            _memory_dict["messages"] = [message.to_dict() for message in self.messages]
        # Add runs if they exist
        if self.runs is not None:
            _memory_dict["runs"] = [run.to_dict() for run in self.runs]
        return _memory_dict

    def add_run(self, agent_run: AgentRun) -> None:
        """Adds an AgentRun to the runs list."""
        self.runs.append(agent_run)
        log_debug("Added AgentRun to AgentMemory")

    def add_system_message(self, message: Message, system_message_role: str = "system") -> None:
        """Add the system messages to the messages list"""
        # If this is the first run in the session, add the system message to the messages list
        if len(self.messages) == 0:
            if message is not None:
                self.messages.append(message)
        # If there are messages in the memory, check if the system message is already in the memory
        # If it is not, add the system message to the messages list
        # If it is, update the system message if content has changed and update_system_message_on_change is True
        else:
            system_message_index = next((i for i, m in enumerate(self.messages) if m.role == system_message_role), None)
            # Update the system message in memory if content has changed
            if system_message_index is not None:
                if (
                    self.messages[system_message_index].content != message.content
                    and self.update_system_message_on_change
                ):
                    log_info("Updating system message in memory with new content")
                    self.messages[system_message_index] = message
            else:
                # Add the system message to the messages list
                self.messages.insert(0, message)

    def add_messages(self, messages: List[Message]) -> None:
        """Add a list of messages to the messages list."""
        self.messages.extend(messages)
        log_debug(f"Added {len(messages)} Messages to AgentMemory")

    def get_messages(self) -> List[Dict[str, Any]]:
        """Returns the messages list as a list of dictionaries."""
        return [message.model_dump() for message in self.messages]

    def get_messages_from_last_n_runs(
        self, last_n: Optional[int] = None, skip_role: Optional[str] = None
    ) -> List[Message]:
        """Returns the messages from the last_n runs, excluding previously tagged history messages.

        Args:
            last_n: The number of runs to return from the end of the conversation.
            skip_role: Skip messages with this role.

        Returns:
            A list of Messages from the specified runs, excluding history messages.
        """
        if not self.runs:
            return []

        runs_to_process = self.runs if last_n is None else self.runs[-last_n:]
        messages_from_history = []

        for run in runs_to_process:
            if not (run.response and run.response.messages):
                continue

            for message in run.response.messages:
                # Skip messages with specified role
                if skip_role and message.role == skip_role:
                    continue
                # Skip messages that were tagged as history in previous runs
                if hasattr(message, "from_history") and message.from_history:
                    continue

                messages_from_history.append(message)

        log_debug(f"Getting messages from previous runs: {len(messages_from_history)}")
        return messages_from_history


    def get_tool_calls(self, num_calls: Optional[int] = None) -> List[Dict[str, Any]]:
        """Returns a list of tool calls from the messages"""

        tool_calls = []
        for message in self.messages[::-1]:
            if message.tool_calls:
                for tool_call in message.tool_calls:
                    tool_calls.append(tool_call)
                    if num_calls and len(tool_calls) >= num_calls:
                        return tool_calls
        return tool_calls

    def load_user_memories(self) -> None:
        """Load memories from memory db for this user."""

        if self.db is None:
            return

        try:
            if self.retrieval in (MemoryRetrieval.last_n, MemoryRetrieval.first_n):
                memory_rows = self.db.read_memories(
                    user_id=self.user_id,
                    limit=self.num_memories,
                    sort="asc" if self.retrieval == MemoryRetrieval.first_n else "desc",
                )
            else:
                raise NotImplementedError("Semantic retrieval not yet supported.")
        except Exception as e:
            log_debug(f"Error reading memory: {e}")
            return

        # Clear the existing memories
        self.memories = []

        # No memories to load
        if memory_rows is None or len(memory_rows) == 0:
            return

        for row in memory_rows:
            try:
                self.memories.append(Memory.model_validate(row.memory))
            except Exception as e:
                logger.warning(f"Error loading memory: {e}")
                continue

    def should_update_memory(self, input: str) -> bool:
        """Determines if a message should be added to the memory db."""
        from agno.memory.classifier import MemoryClassifier

        if self.classifier is None:
            self.classifier = MemoryClassifier()

        self.classifier.existing_memories = self.memories
        classifier_response = self.classifier.run(input)
        if classifier_response == "yes":
            return True
        return False

    async def ashould_update_memory(self, input: str) -> bool:
        """Determines if a message should be added to the memory db."""
        from agno.memory.classifier import MemoryClassifier

        if self.classifier is None:
            self.classifier = MemoryClassifier()

        self.classifier.existing_memories = self.memories
        classifier_response = await self.classifier.arun(input)
        if classifier_response == "yes":
            return True
        return False

    def update_memory(self, input: str, force: bool = False) -> Optional[str]:
        """Creates a memory from a message and adds it to the memory db."""
        from agno.memory.manager import MemoryManager

        if input is None or not isinstance(input, str):
            return "Invalid message content"

        if self.db is None:
            logger.warning("MemoryDb not provided.")
            return "Please provide a db to store memories"

        self.updating_memory = True

        # Check if this user message should be added to long term memory
        should_update_memory = force or self.should_update_memory(input=input)
        log_debug(f"Update memory: {should_update_memory}")

        if not should_update_memory:
            log_debug("Memory update not required")
            return "Memory update not required"

        if self.manager is None:
            self.manager = MemoryManager(user_id=self.user_id, db=self.db)

        else:
            self.manager.db = self.db
            self.manager.user_id = self.user_id

        response = self.manager.run(input)
        self.load_user_memories()
        self.updating_memory = False
        return response

    async def aupdate_memory(self, input: str, force: bool = False) -> Optional[str]:
        """Creates a memory from a message and adds it to the memory db."""
        from agno.memory.manager import MemoryManager

        if input is None or not isinstance(input, str):
            return "Invalid message content"

        if self.db is None:
            logger.warning("MemoryDb not provided.")
            return "Please provide a db to store memories"

        self.updating_memory = True

        # Check if this user message should be added to long term memory
        should_update_memory = force or await self.ashould_update_memory(input=input)
        log_debug(f"Async update memory: {should_update_memory}")

        if not should_update_memory:
            log_debug("Memory update not required")
            return "Memory update not required"

        if self.manager is None:
            self.manager = MemoryManager(user_id=self.user_id, db=self.db)

        else:
            self.manager.db = self.db
            self.manager.user_id = self.user_id

        response = await self.manager.arun(input)
        self.load_user_memories()
        self.updating_memory = False
        return response

    def clear(self) -> None:
        """Clear the AgentMemory"""

        self.runs = []
        self.messages = []
        self.summary = None
        self.memories = None

    def deep_copy(self) -> "AgentMemory":
        from copy import deepcopy

        # Create a shallow copy of the object
        copied_obj = self.__class__(**self.to_dict())

        # Manually deepcopy fields that are known to be safe
        for field_name, field_value in self.__dict__.items():
            if field_name not in ["db", "classifier", "manager", "summarizer"]:
                try:
                    setattr(copied_obj, field_name, deepcopy(field_value))
                except Exception as e:
                    logger.warning(f"Failed to deepcopy field: {field_name} - {e}")
                    setattr(copied_obj, field_name, field_value)

        copied_obj.db = self.db
        copied_obj.classifier = self.classifier
        copied_obj.manager = self.manager
        copied_obj.summarizer = self.summarizer

        return copied_obj
