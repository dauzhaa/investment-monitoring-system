from pydantic import BaseModel, Field
from typing import Optional


# ==================== Districts Dispersion (идея 5) ====================

class DistrictBoxplotData(BaseModel):
    name: str
    count: int
    median_ipo: float
    q25: float
    q75: float
    min: float
    max: float
    outliers: list[float] = Field(default_factory=list)


class DistrictsDispersionResponse(BaseModel):
    year: int
    icc: float = Field(..., ge=0, le=1)
    icc_level: str  # "low" / "moderate" / "high"
    icc_text: str
    icc_explanation: str
    total_organizations: int
    districts: list[DistrictBoxplotData]


# ==================== Peers (идея 3) ====================

class TargetOrganization(BaseModel):
    id: int
    name: str
    ipo: float
    discipline: float
    quality: float
    execution: float
    category: str
    okved: str
    district: str
    plan: float


class ComponentComparison(BaseModel):
    name: str
    your: float
    median: float
    gap: float
    is_main_gap: bool


class PeersSummary(BaseModel):
    count: int
    median_ipo: float
    median_discipline: float
    median_quality: float
    median_execution: float
    rank_in_peers: int  # 1 = лучше всех
    rank_text: str


class PeersResponse(BaseModel):
    target: TargetOrganization
    peers_summary: PeersSummary
    components_comparison: list[ComponentComparison]
    peers_distribution: list[float]  # для dot-plot
    found_count: int  # сколько реально нашли (может быть меньше n)


# ==================== Districts Clusters (идея 7) ====================

class DistrictClusterPoint(BaseModel):
    name: str
    cluster_id: int
    avg_ipo: float
    avg_late_days: float
    smp_share: float
    median_plan: float
    organizations_count: int


class ClusterInfo(BaseModel):
    id: int
    name: str
    color: str
    districts_count: int
    avg_ipo: float
    description: str


class DistrictsClustersResponse(BaseModel):
    year: int
    n_clusters: int
    districts: list[DistrictClusterPoint]
    clusters: list[ClusterInfo]