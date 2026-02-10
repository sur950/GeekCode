# Synchronous API client - needs async migration
# This is sample input for Task 3: Async Migration

import requests
import time
from typing import Dict, Any, Optional, List


class APIClient:
    """Synchronous API client using requests."""

    def __init__(self, base_url: str, timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self._retry_count = 3
        self._retry_delay = 1.0

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a GET request."""
        url = f"{self.base_url}{endpoint}"
        response = self._request_with_retry("GET", url, params=params)
        return response.json()

    def post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make a POST request."""
        url = f"{self.base_url}{endpoint}"
        response = self._request_with_retry("POST", url, json=data)
        return response.json()

    def put(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make a PUT request."""
        url = f"{self.base_url}{endpoint}"
        response = self._request_with_retry("PUT", url, json=data)
        return response.json()

    def delete(self, endpoint: str) -> bool:
        """Make a DELETE request."""
        url = f"{self.base_url}{endpoint}"
        response = self._request_with_retry("DELETE", url)
        return response.status_code == 204

    def _request_with_retry(
        self, method: str, url: str, **kwargs
    ) -> requests.Response:
        """Make a request with retry logic."""
        kwargs["timeout"] = self.timeout
        last_exception = None

        for attempt in range(self._retry_count):
            try:
                response = self.session.request(method, url, **kwargs)
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as e:
                last_exception = e
                if attempt < self._retry_count - 1:
                    time.sleep(self._retry_delay * (attempt + 1))

        raise last_exception

    def batch_get(self, endpoints: List[str]) -> List[Dict[str, Any]]:
        """Get multiple endpoints sequentially."""
        results = []
        for endpoint in endpoints:
            result = self.get(endpoint)
            results.append(result)
        return results

    def upload_file(self, endpoint: str, filepath: str) -> Dict[str, Any]:
        """Upload a file."""
        url = f"{self.base_url}{endpoint}"
        with open(filepath, "rb") as f:
            files = {"file": f}
            response = self._request_with_retry("POST", url, files=files)
        return response.json()

    def download_file(self, endpoint: str, filepath: str) -> bool:
        """Download a file."""
        url = f"{self.base_url}{endpoint}"
        response = self.session.get(url, timeout=self.timeout, stream=True)
        response.raise_for_status()
        with open(filepath, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True

    def close(self):
        """Close the session."""
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
