import webview
import os
import time
import sys
import threading
import paho.mqtt.client as mqtt
import logging
import json
import uuid
import requests
import configparser
import utils
import urllib.request
from protocol import MessageProtocol

def on_connect(client, userdata, flags, reason_code, properties):
    mqtt_logger.info("Connected to Broker")
    
    if registered:
        return

    # subscribe to topic with our unique identifier
    # so that the server can send us messages "directly"
    client.subscribe(identifier)

    # send register message
    width, height = utils.get_monitor_size()
    publish_message(client, config["MQTT"]["register"], MessageProtocol.register(width, height, identifier, name))

def on_disconnect(client, userdata, flags, reason_code, properties):
    mqtt_logger.error("Lost Connection to Broker")

def on_message(client, userdata, msg):

    message = json.loads(msg.payload.decode())
    mqtt_logger.info(f"Received message on topic '{msg.topic}': {message}")

    method = message["method"]

    if(method == "CONFIRM_REGISTER"):
        registered = True

    elif(method == "TEMPLATE"):

        files = message["files"]
        if isinstance(files, list) and len(files) != 0:
            for url in files:
                response = requests.head(url)
                if "Content-Disposition" in response.headers:
                    content_disposition = response.headers["Content-Disposition"]
                    filename_index = content_disposition.find("filename=")
                    if filename_index != -1:
                        filename = content_disposition[filename_index + len("filename="):]
                        filename = filename.strip('"')
                        
                        response = requests.get(url)
                        with open(os.path.join("static", filename), "wb") as file:
                            file.write(response.content)

        utils.store_static("current.html", message["html"])
        window.load_url(utils.get_full_path("static/current.html"))

def publish_message(client, topic, payload):
    client.publish(topic, payload)
    mqtt_logger.info(f"Sent message on topic '{topic}': {payload}")

if __name__ == '__main__':

    # load config
    config = configparser.ConfigParser()
    config.read("config.ini")

    # create unique uuid
    identifier = str(uuid.uuid4())

    registered = False
    name = config["MQTT"]["name"]

    # setup logging
    logging.basicConfig(level=config["Logging"]["log_level"], format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', filename=config["Logging"]["log_file"])
    mqtt_logger = logging.getLogger("MQTTClient")
    webview_logger = logging.getLogger("webview")

    # setup the mqtt client and start loop
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, transport=config["MQTT"]["transport"])
    client.username_pw_set(config["MQTT"]["username"], config["MQTT"]["password"])
    client.on_message = on_message
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.connect_async(config["MQTT"]["host"], int(config["MQTT"]["port"]), int(config["MQTT"]["keepalive"]))
    client.loop_start()

    # setup the window and display it
    window = webview.create_window('MediaPlayer', config["MediaPlayer"]["default_template"], fullscreen=True, confirm_close=False)
    webview.start()

