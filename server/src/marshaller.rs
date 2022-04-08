use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::fmt;

#[derive(Debug, Serialize, Deserialize)]
pub struct DevicePayload {
    ip: String,
    is_dhcp: bool,
    mac: String,
    hostname: String,
    vlan: i32
}

impl DevicePayload {
    pub fn new(ip: String, is_dhcp: bool, mac: String, hostname: String, vlan: i32) -> Self {
        Self {
            ip,
            is_dhcp,
            mac,
            hostname,
            vlan
        }
    }

    pub fn serialize(&self) -> Value {
        json!({
            "ip": self.ip,
            "is_dhcp": self.is_dhcp,
            "mac": self.mac,
            "hostname": self.hostname,
            "vlan": self.vlan
        })
    }

    pub fn deserialize(value: &Value) -> Self {
        let ip = value["ip"].as_str().unwrap().to_string();
        let is_dhcp = value["is_dhcp"].as_bool().unwrap();
        let mac = value["mac"].as_str().unwrap().to_string();
        let hostname = value["hostname"].as_str().unwrap().to_string();
        let vlan = value["vlan"].as_i64().unwrap() as i32;

        Self::new(ip, is_dhcp, mac, hostname, vlan)
    }
}

impl fmt::Display for DevicePayload {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(
            f,
            "DevicePayload(ip: {}, is_dhcp: {}, mac: {}, hostname: {}, vlan: {})",
            self.ip, self.is_dhcp, self.mac, self.hostname, self.vlan
        )
    }
}

#[derive(Debug, Serialize, Deserialize)]
pub struct Payload {
    device: DevicePayload,
    signal: String
}

impl fmt::Display for Payload {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "Payload(device: {}, signal: {})", self.device, self.signal)
    }
}

impl Payload {
    pub fn new(device: DevicePayload, signal: String) -> Self {
        Self {
            device,
            signal
        }
    }

    pub fn serialize(&self) -> Value {
        json!({
            "device": self.device.serialize(),
            "signal": self.signal.to_owned()
        })
    }

    pub fn deserialize(value: &Value) -> Self {
        let device = DevicePayload::deserialize(&value["device"]);
        let signal = value["signal"].as_str().unwrap().to_string().to_owned();

        Self::new(device, signal)
    }
}

#[derive(Debug, Clone)]
pub struct Marshaller;

impl fmt::Display for Marshaller {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "Marshaller()")
    }
}

impl Marshaller {
    pub fn new() -> Self {
        Self {}
    }

    pub fn deserialize_payload(&self, payload: &Value) -> Payload {
        Payload::deserialize(payload)
    }
}