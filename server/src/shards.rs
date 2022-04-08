use crate::utils::{SafeAs, Safe};
use futures::prelude::*;
use tokio::net::{TcpListener, TcpStream};
use tokio_tungstenite::{accept_async, WebSocketStream};
use tracing::info;

use crate::marshaller::Marshaller;

#[derive(Clone, Debug)]
pub enum Signal {
    Begin,
    Open,
    Close,
    Hello,
    Restart,
    Reconnect,
    Unknown,
}

impl ToString for Signal {
    fn to_string(&self) -> String {
        match self {
            Signal::Begin => "BEGIN".to_string(),
            Signal::Open => "OPEN".to_string(),
            Signal::Close => "CLOSE".to_string(),
            Signal::Hello => "HELLO".to_string(),
            Signal::Restart => "RESTART".to_string(),
            Signal::Reconnect => "RECONNECT".to_string(),
            Signal::Unknown => "UNKNOWN".to_string(),
        }
    }
}

impl From<String> for Signal {
    fn from(s: String) -> Self {
        match s.as_str() {
            "BEGIN" => Signal::Begin,
            "OPEN" => Signal::Open,
            "CLOSE" => Signal::Close,
            "HELLO" => Signal::Hello,
            "RESTART" => Signal::Restart,
            "RECONNECT" => Signal::Reconnect,
            _ => Signal::Unknown,
        }
    }
}

#[derive(Debug, Clone)]
pub struct Shard {
    marshaller: Marshaller,
    ip: String,
    port: String,
}

impl std::fmt::Display for Shard {
    fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
        write!(f, "Shard(ip: {}, port: {})", self.ip, self.port)
    }
}

impl Shard {
    pub fn new(ip: Option<&'static str>, port: Option<&'static str>) -> Self {
        let addr = ip.unwrap_or("127.0.0.1");
        let marsh = Marshaller::new();

        Self {
            marshaller: marsh,
            ip: addr.to_string(),
            port: port.unwrap_or("8000").to_string(),
        }
    }

    pub async fn start<'a>(&'a self) -> SafeAs<()> {
        let addr = format!("{}:{}", self.ip, self.port);
        let binder = TcpListener::bind(&addr)
            .await
            .expect("Failed to bind to address");

        info!("Listening on {}", addr);

        while let Ok((stream_, _)) = binder.accept().await {
            let stream = accept_async(stream_).await.unwrap();
            self.dispatch(stream).await.unwrap();
        }

        Ok(())
    }


    pub async fn dispatch(&self, mut stream: WebSocketStream<TcpStream>) -> Safe {
        while let Some(msg) = stream.next().await {
            if let Ok(msg) = msg {

                let value: serde_json::Value = match serde_json::from_str(&msg.to_string().as_str()) {
                    Ok(v) => v,
                    Err(e) => {
                        println!("Failed to parse message: {}", e);
                        continue;
                    }
                };

                let payload = self.marshaller.deserialize_payload(&value);
                println!("{}", payload);
            }
        }

        Ok(())
    }

}
