from pydantic import BaseModel, Field
from typing import List

class URLArrayReport(BaseModel):
    urls: List[List[str]] = Field(description="Array of URL information arrays. Each inner array contains [network, contract_address, token_id, full_url]")