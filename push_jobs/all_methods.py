from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
from prometheus_client.exposition import basic_auth_handler
import os, ssl

class PrometheusPusher(AbstractMetricsPusher):
    
    """
    Pusher to a Prometheus push gateway.
    Args:
        job_name: Prometheus job name
        username: Push gateway credentials
        password: Push gateway credentials
        url: URL (with portnum) of push gateway
        push_interval: Seconds between each upload call
        thread_name: Name of thread to start. If omitted, a standard name such as Thread-4 will be generated.
        cancelation_token: Event object to be used as a thread cancelation event
    """
    def __init__(self,
        job_name: str,
        url: str,
        push_interval: int,
        username: Optional[str] = None,
        password: Optional[str] = None,
        thread_name: Optional[str] = None,
        cancelation_token: Event = Event(),
    ):
        super(PrometheusPusher, self).__init__(push_interval, thread_name, cancelation_token)

        self.username = username
        self.job_name = job_name
        self.password = password

        self.url = url

    def _auth_handler(self, url: str, method: str, timeout: int, headers: Dict[str, str], data: Any) -> Callable:
        """
        Returns a authentication handler against the Prometheus Pushgateway to use in the pushadd_to_gateway method.

        Args:
            url:      Push gateway
            method:   HTTP method
            timeout:  Request timeout (seconds)
            headers:  HTTP headers
            data:     Data to send

        Returns:
            prometheus_client.exposition.basic_auth_handler: A authentication handler based on this client.
        """
        return basic_auth_handler(url, method, timeout, headers, data, self.username, self.password)

    def _push_to_server(self) -> None:
        """
        Push the default metrics registry to the configured Prometheus Pushgateway.
        """
        if not self.url or not self.job_name:
            return

        try:
            pushadd_to_gateway(self.url, job=self.job_name, registry=REGISTRY, handler=self._auth_handler)

        except OSError as exp:
            self.logger.warning("Failed to push metrics to %s: %s", self.url, str(exp))
        except:
            self.logger.exception("Failed to push metrics to %s", self.url)

        self.logger.debug("Pushed metrics to %s", self.url)
    
    def clear_gateway(self) -> None:
        """
        Delete metrics stored at the gateway (reset gateway).
        """
        delete_from_gateway(self.url, job=self.job_name, handler=self._auth_handler)
        self.logger.debug("Deleted metrics from push gateway %s", self.url)

if __name__ == '__main__':
    
