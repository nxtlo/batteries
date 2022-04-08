mod shards;
mod utils;
mod marshaller;

use crate::shards::Shard;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    let _ = env_logger::try_init();

    let shard = Shard::new(None, None);
    shard.start().await.unwrap();

    Ok(())
}
