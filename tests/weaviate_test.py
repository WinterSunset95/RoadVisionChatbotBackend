
import weaviate
import dotenv
import os

dotenv.load_dotenv()

# weaviate_url = os.getenv("WEAVIATE_URL")
# weaviate_api_key = os.getenv("WEAVIATE_API_KEY")
weaviate_url = None
weaviate_api_key = None

client = None
try:
    if weaviate_url and weaviate_api_key:
        print("Connecting to Weaviate Cloud Services (WCS)")
        client = weaviate.connect_to_weaviate_cloud(
            cluster_url=weaviate_url,
            auth_credentials=weaviate.auth.Auth.api_key(weaviate_api_key),
        )
        print("""✅ Connected to Weaviate Cloud Services (WCS)""")
    else:
        print("Connecting to local weaviate instance via docker")
        client = weaviate.connect_to_local()
        print("""✅ Connected to local weaviate instance via docker""")

    if client.is_ready():
        print("✅ Weaviate connection successful.")
    else:
        print("❌ Weaviate connection failed.")
except Exception as e:
    print(f"❌ Failed to connect to Weaviate at {weaviate_url}. Please ensure it is running.")
    print(f"   Error: {e}")
finally:
    if client:
        client.close()
        print("✅ Weaviate connection closed.")
