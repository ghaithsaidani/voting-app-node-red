import json
from typing import Dict, List
import logging
from fastapi import FastAPI, HTTPException
import paho.mqtt.client as mqtt
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Voting Server")


class VotingServer:
    def __init__(self, broker: str = "localhost", port: int = 1883):
        self.broker = broker
        self.port = port
        self.votes: Dict[str, int] = {}
        self.vote_history: List[Dict] = []

        self.client = mqtt.Client(protocol=mqtt.MQTTv5)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect

        # Set up error handling
        self.client.enable_logger(logger)

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            logger.info("Connected to MQTT broker successfully")
            client.subscribe("voting/cast")
        else:
            logger.error(f"Failed to connect to MQTT broker with code: {rc}")

    def _on_disconnect(self, client, userdata, rc):
        if rc != 0:
            logger.warning("Unexpected disconnection from MQTT broker")

    def _on_message(self, client, userdata, msg):
        try:
            data = json.loads(msg.payload.decode())
            candidate = data.get("candidate")
            voter = data.get("voter", "Anonymous")

            if not candidate or not isinstance(candidate, str):
                logger.warning("Invalid vote received: missing or invalid candidate")
                return
            if candidate == "clear":
                self.clear_results()
                return

            vote_record = {
                "candidate": candidate,
                "voter": voter,
                "timestamp": datetime.now().isoformat()
            }
            self.vote_history.append(vote_record)
            print(self.vote_history)
            self.votes[candidate] = self.votes.get(candidate, 0) + 1
            self._update_results()
            logger.info(f"Vote recorded for {candidate}")

        except json.JSONDecodeError:
            logger.error("Failed to decode vote message")
        except Exception as e:
            logger.error(f"Error processing vote: {str(e)}")

    def _update_results(self):
        try:
            # Prepare data in the required format for Node-RED's ui_chart
            labels = list(self.votes.keys()) if self.votes else ["No Votes"]
            data = list(self.votes.values()) if self.votes else [0]

            chart_data = {
                "labels": labels,
                "data": [data],
            }
            # Publish formatted data to the MQTT topic
            self.client.publish("voting/results", json.dumps(chart_data))
            logger.info(f"Published results: {chart_data}")
        except Exception as e:
            logger.error(f"Failed to publish results: {str(e)}")

    def clear_results(self):
        self.votes.clear()
        self.vote_history.clear()
        self._update_results()  # Publish the cleared results
        logger.info("Voting results cleared")

    def start(self):
        try:
            self.client.connect(self.broker, self.port)
            self.client.loop_start()
        except Exception as e:
            logger.error(f"Failed to start MQTT client: {str(e)}")
            raise


voting_server = VotingServer()


@app.on_event("startup")
async def startup_event():
    voting_server.start()


@app.get("/results")
async def get_results():
    return voting_server.votes


@app.get("/health")
async def health_check():
    if not voting_server.client.is_connected():
        raise HTTPException(status_code=503, detail="MQTT broker connection lost")
    return {"status": "healthy"}
