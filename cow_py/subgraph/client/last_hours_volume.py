# Generated by ariadne-codegen
# Source: cow_py/subgraph/queries

from typing import Any, List, Optional

from pydantic import Field

from .base_model import BaseModel


class LastHoursVolume(BaseModel):
    hourly_totals: List["LastHoursVolumeHourlyTotals"] = Field(alias="hourlyTotals")


class LastHoursVolumeHourlyTotals(BaseModel):
    timestamp: int
    volume_usd: Optional[Any] = Field(alias="volumeUsd")
