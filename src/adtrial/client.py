from dataclasses import dataclass
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

@dataclass
class SearchResult:
    studies: list
    api_version: dict | None

class CTGovClient:
    def __init__(self, base_url="https://clinicaltrials.gov/api/v2", timeout_seconds=45, user_agent="ad-clinical-landscape/0.1"):
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent, "Accept": "application/json"})
        retry = Retry(total=5, connect=5, read=5, status=5, backoff_factor=1.0,
                      status_forcelist=(429,500,502,503,504), allowed_methods=frozenset(["GET"]),
                      respect_retry_after_header=True)
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def get_version(self):
        r = self.session.get(f"{self.base_url}/version", timeout=self.timeout_seconds)
        r.raise_for_status()
        return r.json()

    def iter_studies(self, condition, page_size=1000, max_studies=None):
        url = f"{self.base_url}/studies"
        token = None
        n = 0
        while True:
            params = {"query.cond": condition, "pageSize": min(max(int(page_size),1),1000),
                      "format": "json", "countTotal": "true"}
            if token:
                params["pageToken"] = token
            r = self.session.get(url, params=params, timeout=self.timeout_seconds)
            r.raise_for_status()
            payload = r.json()
            for study in payload.get("studies", []):
                yield study
                n += 1
                if max_studies is not None and n >= max_studies:
                    return
            token = payload.get("nextPageToken")
            if not token:
                return

    def search_studies(self, condition, page_size=1000, max_studies=None):
        try:
            version = self.get_version()
        except Exception:
            version = None
        return SearchResult(list(self.iter_studies(condition, page_size, max_studies)), version)
