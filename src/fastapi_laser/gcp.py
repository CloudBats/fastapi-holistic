from __future__ import annotations

import json
import logging

import google.cloud.logging
from google.cloud.logging_v2.handlers import CloudLoggingHandler


# https://cloud.google.com/logging/docs/reference/v2/rest/v2/LogEntry
# https://cloud.google.com/run/docs/logging
# https://cloud.google.com/logging/docs/access-control
class CloudLoggingLoguruHandler(CloudLoggingHandler):
    def emit(self, record: logging.LogRecord):
        """Adapted from original emit() in CloudLoggingHandler for Loguru.

        The standard logging library creates attributes in logging.LogRecord
        automatically from the extra dictionary, while Loguru doesn't.
        Thus, data other than the message is looked up in the extra dictionary.
        """
        # disabled the typical message formatting in favor of structured logging
        # message = super().format(record)
        # TODO: see how to populate jsonPayload with the record fields instead of message
        logging_labels = dict()
        message = json.loads(record.msg)
        # remove elements that become part of the log entry automatically
        message["record"].pop("message")
        logging_labels["logger"] = message["record"].pop("name")
        # disabled in favor of message["record"]["extra"] to eliminate redundancy
        # extra = record.extra
        extra = message["record"]["extra"]
        trace_id = extra.pop("trace", None)
        span_id = extra.pop("span_id", None)
        http_request = extra.pop("http_request", None)
        resource = extra.pop("resource", self.resource)
        user_labels = extra.pop("labels", {})
        # merge labels
        total_labels = self.labels if self.labels is not None else {}
        total_labels |= user_labels | logging_labels
        if not total_labels:
            total_labels = None
        # send off request
        self.transport.send(
            record,
            message,
            resource=resource,
            labels=total_labels,
            trace=trace_id,
            span_id=span_id,
            http_request=http_request,
        )


# https://cloud.google.com/logging/docs/setup/python
# https://googleapis.dev/python/logging/latest/usage.html
def get_cloud_logging_handler() -> CloudLoggingLoguruHandler:
    client = google.cloud.logging.Client()
    # TODO: see if the global resource being used by default makes sense or
    #   if we should use a more specific resource
    # resource = Resource(type="global", labels={})

    return CloudLoggingLoguruHandler(client)
