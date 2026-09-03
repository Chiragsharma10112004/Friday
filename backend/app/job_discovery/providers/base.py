from abc import ABC, abstractmethod
from typing import List, Optional
from app.job_discovery.schemas import DiscoveredJob, JobSearchQuery


class BaseJobProvider(ABC):
    """
    Abstract base for all job discovery providers.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @abstractmethod
    def search_jobs(self, query: JobSearchQuery) -> List[DiscoveredJob]:
        pass

    @abstractmethod
    def fetch_job(self, job_url_or_id: str) -> Optional[DiscoveredJob]:
        pass
