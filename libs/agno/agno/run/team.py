from dataclasses import asdict, dataclass, field
from time import time
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from agno.media import AudioArtifact, AudioResponse, ImageArtifact, VideoArtifact
from agno.models.message import Message
from agno.run.response import RunResponseExtraData, RunEvent, RunResponse


@dataclass
class TeamRunResponse:
    """Response returned by Team.run() functions"""

    event: str = RunEvent.run_response.value

    content: Optional[Any] = None
    content_type: str = "str"
    thinking: Optional[str] = None
    messages: Optional[List[Message]] = None
    metrics: Optional[Dict[str, Any]] = None
    model: Optional[str] = None

    member_responses: List[RunResponse] = field(default_factory=list)

    run_id: Optional[str] = None
    team_id: Optional[str] = None
    session_id: Optional[str] = None

    tools: Optional[List[Dict[str, Any]]] = None

    images: Optional[List[ImageArtifact]] = None  # Images from member runs
    videos: Optional[List[VideoArtifact]] = None  # Videos from member runs
    audio: Optional[List[AudioArtifact]] = None  # Audio from member runs

    response_audio: Optional[AudioResponse] = None  # Model audio response
    extra_data: Optional[RunResponseExtraData] = None
    created_at: int = field(default_factory=lambda: int(time()))

    def to_dict(self) -> Dict[str, Any]:
        _dict = {
            k: v
            for k, v in asdict(self).items()
            if v is not None and k not in ["messages", "extra_data", "images", "videos", "audio", "response_audio"]
        }
        if self.messages is not None:
            _dict["messages"] = [m.to_dict() for m in self.messages]

        if self.extra_data is not None:
            _dict["extra_data"] = self.extra_data.to_dict()

        if self.images is not None:
            _dict["images"] = [img.model_dump(exclude_none=True) for img in self.images]

        if self.videos is not None:
            _dict["videos"] = [vid.model_dump(exclude_none=True) for vid in self.videos]

        if self.audio is not None:
            _dict["audio"] = [aud.model_dump(exclude_none=True) for aud in self.audio]

        if self.response_audio is not None:
            _dict["response_audio"] = self.response_audio.to_dict()

        if isinstance(self.content, BaseModel):
            _dict["content"] = self.content.model_dump(exclude_none=True)

        return _dict

    def to_json(self) -> str:
        import json

        _dict = self.to_dict()

        return json.dumps(_dict, indent=2)

    def get_content_as_string(self, **kwargs) -> str:
        import json

        from pydantic import BaseModel

        if isinstance(self.content, str):
            return self.content
        elif isinstance(self.content, BaseModel):
            return self.content.model_dump_json(exclude_none=True, **kwargs)
        else:
            return json.dumps(self.content, **kwargs)

    def add_member_run(self, run_response: RunResponse) -> None:
        self.member_responses.append(run_response)
        if run_response.images is not None:
            if self.images is None:
                self.images = []
            self.images.extend(run_response.images)
        if run_response.videos is not None:
            if self.videos is None:
                self.videos = []
            self.videos.extend(run_response.videos)
        if run_response.audio is not None:
            if self.audio is None:
                self.audio = []
            self.audio.extend(run_response.audio)
