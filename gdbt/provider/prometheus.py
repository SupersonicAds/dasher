import hashlib
import typing

import attr
import deserialize  # type: ignore
import durations  # type: ignore
import jsonpath_ng  # type: ignore
import requests

from gdbt.dynamic import Evaluation
from gdbt.provider import EvaluationProvider, Provider


@deserialize.downcast_identifier(Provider, "prometheus")
@attr.s
class PrometheusProvider(EvaluationProvider):
    endpoint: str = attr.ib()
    timeout: typing.Optional[int] = attr.ib(default=5)

    @property
    def client(self) -> None:
        return None

    def query(self, query: str) -> typing.List[typing.Any]:
        url = self.endpoint.rstrip("/") + "/api/v1/query"
        params = {"query": query}
        response = requests.get(url, params, timeout=self.timeout)
        response.raise_for_status()
        answer = response.json().get("data").get("result")
        return answer


@deserialize.downcast_identifier(Evaluation, "prometheus")
@attr.s
class PrometheusEvaluation(Evaluation):
    metric: str = attr.ib()
    label: str = attr.ib()

    def evaluate(self, provider: EvaluationProvider) -> typing.Any:
        filter = jsonpath_ng.parse(f"$[*].metric.{self.label}")
        metric_values = provider.query(self.metric)
        values = [item.value for item in filter.find(metric_values)]
        return values

    @property
    def hash(self) -> str:
        data = self.source + self.metric + self.label
        md5 = hashlib.md5()
        md5.update(data.encode())
        digest = md5.hexdigest()
        return digest
