"""
Data models for Mender Deployments API.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class DeploymentStatus(str, Enum):
    """Deployment status enumeration."""

    SCHEDULED = "scheduled"
    PENDING = "pending"
    INPROGRESS = "inprogress"
    FINISHED = "finished"


class DeviceDeploymentStatus(str, Enum):
    """Device deployment status enumeration."""

    PENDING = "pending"
    DOWNLOADING = "downloading"
    INSTALLING = "installing"
    REBOOTING = "rebooting"
    SUCCESS = "success"
    FAILURE = "failure"
    NOARTIFACT = "noartifact"
    ALREADY_INSTALLED = "already-installed"
    ABORTED = "aborted"
    DECOMMISSIONED = "decommissioned"
    PAUSE_BEFORE_INSTALLING = "pause_before_installing"
    PAUSE_BEFORE_COMMITTING = "pause_before_committing"
    PAUSE_BEFORE_REBOOTING = "pause_before_rebooting"


@dataclass
class UpdateModule:
    """Update module information."""

    type: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> UpdateModule:
        """Create from API response dictionary."""
        return cls(type=data.get("type", ""))


@dataclass
class Artifact:
    """Artifact information."""

    id: str
    name: str
    description: str | None = None
    device_types_compatible: list[str] = field(default_factory=list)
    info: dict[str, Any] = field(default_factory=dict)
    signed: bool = False
    updates: list[UpdateModule] = field(default_factory=list)
    artifact_provides: dict[str, str] = field(default_factory=dict)
    artifact_depends: dict[str, Any] = field(default_factory=dict)
    clears_artifact_provides: list[str] = field(default_factory=list)
    size: int = 0
    modified: datetime | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Artifact:
        """Create from API response dictionary."""
        updates = [
            UpdateModule.from_dict(u) for u in data.get("updates", [])
        ]

        modified = None
        if data.get("modified"):
            try:
                modified = datetime.fromisoformat(
                    data["modified"].replace("Z", "+00:00")
                )
            except ValueError:
                pass

        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description"),
            device_types_compatible=data.get("device_types_compatible", []),
            info=data.get("info", {}),
            signed=data.get("signed", False),
            updates=updates,
            artifact_provides=data.get("artifact_provides", {}),
            artifact_depends=data.get("artifact_depends", {}),
            clears_artifact_provides=data.get("clears_artifact_provides", []),
            size=data.get("size", 0),
            modified=modified,
        )


@dataclass
class ArtifactUpdate:
    """Artifact update request."""

    description: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API request."""
        result = {}
        if self.description is not None:
            result["description"] = self.description
        return result


@dataclass
class DeploymentPhase:
    """Deployment phase configuration."""

    id: str | None = None
    batch_size: int | None = None
    start_ts: datetime | str | None = None
    device_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API request."""
        result: dict[str, Any] = {}

        if self.batch_size is not None:
            result["batch_size"] = self.batch_size

        if self.start_ts is not None:
            if isinstance(self.start_ts, datetime):
                result["start_ts"] = self.start_ts.isoformat()
            else:
                result["start_ts"] = self.start_ts

        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DeploymentPhase:
        """Create from API response dictionary."""
        start_ts = None
        if data.get("start_ts"):
            try:
                start_ts = datetime.fromisoformat(
                    data["start_ts"].replace("Z", "+00:00")
                )
            except ValueError:
                start_ts = data["start_ts"]

        return cls(
            id=data.get("id"),
            batch_size=data.get("batch_size"),
            start_ts=start_ts,
            device_count=data.get("device_count", 0),
        )


@dataclass
class DeploymentStatistics:
    """Deployment statistics."""

    status: DeploymentStatus
    success: int = 0
    pending: int = 0
    downloading: int = 0
    installing: int = 0
    rebooting: int = 0
    failure: int = 0
    noartifact: int = 0
    already_installed: int = 0
    aborted: int = 0
    decommissioned: int = 0
    pause_before_installing: int = 0
    pause_before_committing: int = 0
    pause_before_rebooting: int = 0

    @property
    def total(self) -> int:
        """Total number of devices."""
        return (
            self.success
            + self.pending
            + self.downloading
            + self.installing
            + self.rebooting
            + self.failure
            + self.noartifact
            + self.already_installed
            + self.aborted
            + self.decommissioned
            + self.pause_before_installing
            + self.pause_before_committing
            + self.pause_before_rebooting
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DeploymentStatistics:
        """Create from API response dictionary."""
        return cls(
            status=DeploymentStatus(data.get("status", "pending")),
            success=data.get("success", 0),
            pending=data.get("pending", 0),
            downloading=data.get("downloading", 0),
            installing=data.get("installing", 0),
            rebooting=data.get("rebooting", 0),
            failure=data.get("failure", 0),
            noartifact=data.get("noartifact", 0),
            already_installed=data.get("already-installed", 0),
            aborted=data.get("aborted", 0),
            decommissioned=data.get("decommissioned", 0),
            pause_before_installing=data.get("pause_before_installing", 0),
            pause_before_committing=data.get("pause_before_committing", 0),
            pause_before_rebooting=data.get("pause_before_rebooting", 0),
        )


@dataclass
class DeploymentDevice:
    """Device in a deployment."""

    id: str
    status: DeviceDeploymentStatus
    created: datetime | None = None
    finished: datetime | None = None
    deleted: bool = False
    device_type: str | None = None
    log: bool = False
    state: str | None = None
    substate: str | None = None
    image: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DeploymentDevice:
        """Create from API response dictionary."""
        created = None
        if data.get("created"):
            try:
                created = datetime.fromisoformat(
                    data["created"].replace("Z", "+00:00")
                )
            except ValueError:
                pass

        finished = None
        if data.get("finished"):
            try:
                finished = datetime.fromisoformat(
                    data["finished"].replace("Z", "+00:00")
                )
            except ValueError:
                pass

        return cls(
            id=data["id"],
            status=DeviceDeploymentStatus(data.get("status", "pending")),
            created=created,
            finished=finished,
            deleted=data.get("deleted", False),
            device_type=data.get("device_type"),
            log=data.get("log", False),
            state=data.get("state"),
            substate=data.get("substate"),
            image=data.get("image", {}),
        )


@dataclass
class Deployment:
    """Deployment information."""

    id: str
    name: str
    artifact_name: str
    created: datetime | None = None
    finished: datetime | None = None
    status: DeploymentStatus = DeploymentStatus.PENDING
    device_count: int = 0
    retries: int = 0
    max_devices: int | None = None
    phases: list[DeploymentPhase] = field(default_factory=list)
    statistics: DeploymentStatistics | None = None
    type: str | None = None
    filter: dict[str, Any] | None = None
    groups: list[str] | None = None
    device_list: list[str] | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Deployment:
        """Create from API response dictionary."""
        created = None
        if data.get("created"):
            try:
                created = datetime.fromisoformat(
                    data["created"].replace("Z", "+00:00")
                )
            except ValueError:
                pass

        finished = None
        if data.get("finished"):
            try:
                finished = datetime.fromisoformat(
                    data["finished"].replace("Z", "+00:00")
                )
            except ValueError:
                pass

        phases = [
            DeploymentPhase.from_dict(p) for p in data.get("phases", [])
        ]

        statistics = None
        if data.get("statistics"):
            statistics = DeploymentStatistics.from_dict(data["statistics"])

        return cls(
            id=data["id"],
            name=data["name"],
            artifact_name=data["artifact_name"],
            created=created,
            finished=finished,
            status=DeploymentStatus(data.get("status", "pending")),
            device_count=data.get("device_count", 0),
            retries=data.get("retries", 0),
            max_devices=data.get("max_devices"),
            phases=phases,
            statistics=statistics,
            type=data.get("type"),
            filter=data.get("filter"),
            groups=data.get("groups"),
            device_list=data.get("device_list"),
        )


@dataclass
class NewDeployment:
    """New deployment request."""

    name: str
    artifact_name: str
    devices: list[str] | None = None
    group: str | None = None
    all_devices: bool = False
    phases: list[DeploymentPhase] | None = None
    retries: int = 0
    max_devices: int | None = None
    filter_id: str | None = None
    update_control_map: dict[str, Any] | None = None
    autogenerate_delta: bool | None = None
    force_installation: bool | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API request."""
        result: dict[str, Any] = {
            "name": self.name,
            "artifact_name": self.artifact_name,
        }

        if self.devices:
            result["devices"] = self.devices

        if self.group:
            result["group"] = self.group

        if self.all_devices:
            result["all_devices"] = self.all_devices

        if self.phases:
            result["phases"] = [p.to_dict() for p in self.phases]

        if self.retries > 0:
            result["retries"] = self.retries

        if self.max_devices is not None:
            result["max_devices"] = self.max_devices

        if self.filter_id:
            result["filter_id"] = self.filter_id

        if self.update_control_map:
            result["update_control_map"] = self.update_control_map

        if self.autogenerate_delta is not None:
            result["autogenerate_delta"] = self.autogenerate_delta

        if self.force_installation is not None:
            result["force_installation"] = self.force_installation

        return result


@dataclass
class Release:
    """Release information containing artifacts."""

    name: str
    artifacts: list[Artifact] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    update_types: list[str] = field(default_factory=list)
    device_types: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Release:
        """Create from API response dictionary."""
        artifacts = [
            Artifact.from_dict(a) for a in data.get("artifacts", [])
        ]

        return cls(
            name=data["name"],
            artifacts=artifacts,
            tags=data.get("tags", []),
            update_types=data.get("update_types", []),
            device_types=data.get("device_types", []),
        )
