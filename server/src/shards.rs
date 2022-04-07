use crate::utils::SafeAs;
use futures::prelude::*;
use tokio::net::TcpListener;
use tokio_tungstenite::accept_async;
use tracing::info;

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

#[derive(Debug)]
pub struct Shard {
    ip: String,
    port: String,
}

impl Shard {
    pub async fn new(ip: Option<String>, port: Option<String>) -> Self {
        let addr = ip.unwrap_or("127.0.0.1".to_string()).to_string().to_owned();

        Self {
            ip: addr,
            port: port.unwrap_or("8000".to_string()).to_string().to_owned(),
        }
    }

    pub async fn start(&mut self) -> SafeAs<()> {
        let addr = format!("{}:{}", self.ip, self.port);
        let binder = TcpListener::bind(&addr)
            .await
            .expect("Failed to bind to address");

        info!("Listening on {}", addr);

        while let Ok((stream, addr)) = binder.accept().await {
            info!("Connection from {}", addr);

            let mut ws = accept_async(stream).await?;

            tokio::spawn(async move {
                while let Some(msg) = ws.next().await {
                    let msg = msg.unwrap().to_owned();
                    let signal = Signal::from(msg.to_string());

                    println!("{:?}", signal.to_string());
                }
            });
        }

        Ok(())
    }

}
