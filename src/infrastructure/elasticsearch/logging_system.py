import logging
import os
import traceback
from datetime import datetime, timezone
from elasticsearch import Elasticsearch

ES_HOST =  os.getenv("ELASTICSEARCH_URL", "http://elasticsearch:9200")

LOG_INDEX = "app-logs"

es_client = Elasticsearch(ES_HOST)


class ElasticsearchLogHandler(logging.Handler):
    def emit(self, record: logging.LogRecord):
        try:
            log_entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "module": record.module,
                "func": record.funcName,
                "line": record.lineno,
            }
            if record.exc_info:
                log_entry["traceback"] = "".join(
                    traceback.format_exception(*record.exc_info)
                )
            es_client.index(index=LOG_INDEX, document=log_entry)
        except Exception:
            # tránh vòng lặp lỗi khi chính việc log bị lỗi
            pass


def setup_logging():
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    es_handler = ElasticsearchLogHandler()
    es_handler.setLevel(logging.WARNING)  # chỉ đẩy WARNING/ERROR lên ES
    root_logger.addHandler(es_handler)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)