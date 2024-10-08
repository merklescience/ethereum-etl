# MIT License
#
# Copyright (c) 2018 Evgeny Medvedev, evge.medvedev@gmail.com
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
import os
from confluent_kafka import Producer
from timeout_decorator import timeout_decorator

import logging

import socket
import json


class KafkaItemExporter:
    def __init__(
            self, item_type_to_topic_mapping
    ) -> None:
        logging.basicConfig(
            level=logging.INFO,
            filename="message-publish.log",
            format='{"time" : "%(asctime)s", "level" : "%(levelname)s" , "message" : "%(message)s"}',
        )

        conf = {
            "bootstrap.servers": os.getenv("CONFLUENT_BROKER"),
            "security.protocol": "SASL_SSL",
            "sasl.mechanisms": "PLAIN",
            "client.id": socket.gethostname(),
            "message.max.bytes": 5242880,
            "sasl.username": os.getenv("KAFKA_PRODUCER_KEY"),
            "sasl.password": os.getenv("KAFKA_PRODUCER_PASSWORD"),
            "linger.ms": 10,
            "batch.size": 5000,
            "acks": 1,
            "batch.num.messages": 10000,
            "delivery.report.only.error": True,
            "compression.type": "gzip"
        }

        producer = Producer(conf)
        self.item_type_to_topic_mapping = item_type_to_topic_mapping
        self.producer = producer
        self.logging = logging.getLogger(__name__)

    def open(self):
        pass

    def export_items(self, items):
        try:
            self._export_items_with_timeout(items)
        except timeout_decorator.TimeoutError as e:
            logging.info("Timeout error with kafka")
            raise e

    @timeout_decorator.timeout(300)
    def _export_items_with_timeout(self, items):
        for item in items:
            self.export_item(item)

    def export_item(self, item):
        item_type = item.get("type")
        # logging.info("publishing " + item_type)
        has_item_type = item_type is not None
        if has_item_type and item_type in self.item_type_to_topic_mapping:
            data = json.dumps(item).encode("utf-8")
            topic = self.item_type_to_topic_mapping[item_type]
            self.write_txns(key=item.get("token_address"),
                            value=data.decode("utf-8"),
                            topic=topic)
        else:
            logging.error('Topic for item type "{item_type}" is not configured.')

    def close(self):
        self.producer.flush()

    def write_txns(self, key: str, value: str, topic: str):
        def acked(err, msg):
            if err is not None:
                self.logging.error('%% Message failed delivery: %s\n' % err)

        try:
            self.producer.produce(topic, key=key, value=value, on_delivery=acked)
            self.producer.poll(0)
        except BufferError:
            self.logging.error('%% Local producer queue is full (%d messages awaiting delivery): try again\n' %
                               len(self.producer))
            self.logging.error('%% Flushing producer and retrying')
            self.producer.flush()
            self.producer.produce(topic, key=key, value=value, on_delivery=acked)
