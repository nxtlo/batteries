mod shards;
mod utils;

use crate::shards::Shard;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    let _ = env_logger::try_init();

    let mut shard = Shard::new(None, None).await;
    shard.start().await.unwrap();

    Ok(())
}
