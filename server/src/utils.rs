pub type Safe = Result<(), Box<dyn std::error::Error + Send + Sync>>;
pub type SafeAs<T> = Result<T, Box<dyn std::error::Error + Send + Sync>>;
