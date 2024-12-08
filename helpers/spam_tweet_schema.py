from pydantic import BaseModel, Field
from typing import Optional

class SpamTweet(BaseModel):
    is_spam: bool = Field(description="Whether the tweet is spam")