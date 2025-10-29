from pydantic import BaseModel, ConfigDict

class MongoDBModel(BaseModel):
    """Base model for MongoDB documents with common configuration."""
    model_config = ConfigDict(populate_by_name=True)
