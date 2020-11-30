from fritzconnection import FritzConnection
from fritzconnection.lib.fritzhomeauto import FritzHomeAutomation
from fritzconnection.lib.fritzwlan import FritzWLAN
from fritzconnection.lib.fritzstatus import FritzStatus
from influxdb import line_protocol
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS, WritePrecision
import influxdb
import json
import time
import socket


DefaultFFConfig = {
    "fb_address":"fritz.box",
    "fb_user":"",
    "fb_pass":"",
    "i_address":"localhost",
    "i_port":8086,
    "i_user":"",
    "i_pass":"",
    "i_database":"fritzdata",
    "i_url":"",
    "i_token":"",
    "i_org": "",
    "i_bucket": "",
    "hostname":socket.gethostname()
}

class FritzFlux:
  def __init__(self, ff_config):
    self.fc = FritzConnection(address=ff_config["fb_address"], user=ff_config["fb_user"], password=ff_config["fb_pass"])
    self.fs = FritzStatus(self.fc)
    self.fh = FritzHomeAutomation(self.fc)
    if len(ff_config["i_url"])>0:
      self.ic = InfluxDBClient(url=ff_config["i_url"], token=ff_config["i_token"])
    else:
      self.ic = influxdb.InfluxDBClient(host=ff_config["i_address"], port=ff_config["i_port"])
      self.ic.create_database(ff_config["i_database"])
      self.ic.switch_database(ff_config["i_database"])
    self.config = ff_config

  def push(self):
    json_body = {
        "tags": {
            "fb": "6490",
            "hostname": self.config["hostname"]
        },
        "points": []
    }

    t = int(time.time())
    for d in self.fh.device_informations():
      temp = float(d["NewTemperatureCelsius"])/10
      name = d["NewDeviceName"]
      if temp > 0:
        m = {"measurement": name, "fields": {"temp": temp}, "time": t}
        json_body["points"].append(m)
    #  else:
    #   print(d)

    f_status = {
        "uptime": (self.fs.uptime, "seconds"),
        "bytes_received": (self.fs.bytes_received, "bytes"),
        "bytes_sent": (self.fs.bytes_sent, "bytes"),
        "transmission_rate_up": (self.fs.transmission_rate[0], "bps"),
        "transmission_rate_down": (self.fs.transmission_rate[1], "bps")
    }

    for name, (v, f) in f_status.items():
      m = {"measurement": name, "fields": {f: v}, "time": t}
      json_body["points"].append(m)

    lines = line_protocol.make_lines(json_body)
    print(lines)

    if len(self.config["i_url"])>0:

      write_api = self.ic.write_api(write_options=SYNCHRONOUS)
      write_api.write(self.config["i_bucket"], self.config["i_org"], lines, write_precision=WritePrecision.S)
      print("Written to the cloud")
    else:
      self.ic.write_points(lines, protocol="line_protocol", time_precision="s")

