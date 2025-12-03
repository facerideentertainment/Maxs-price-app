import os
import asyncio
import firebase_admin
from firebase_admin import credentials, firestore
from crawl4ai import AsyncWebCrawler
import json

# Initialize Firebase from the Secret
cred_dict = json.loads(os.environ.get("FIREBASE_SERVICE_ACCOUNT"))
cred = credentials.Certificate(cred_dict)
firebase_admin.initialize_app(cred)
db = firestore.client()

async def process_items():
    # 1. Fetch all items with status 'pending'
    docs = db.collection('tracked_items').where('status', '==', 'pending').stream()
    
    # 2. Start the Crawler
    async with AsyncWebCrawler(verbose=True) as crawler:
        for doc in docs:
            item = doc.to_dict()
            url = item.get('url')
            print(f"Processing: {url}")
            
            try:
                # 3. Scrape the page
                result = await crawler.arun(url=url)
                
                if not result.success:
                    raise Exception(f"Crawl failed: {result.error_message}")

                # 4. Extract Price (Basic Example - you might need regex or LLM here)
                # For now, we just mock a price to prove the loop works.
                # In a real app, you would parse `result.markdown` or `result.html`
                extracted_price = 99.99 
                
                # 5. Update Firestore
                db.collection('tracked_items').document(doc.id).update({
                    'status': 'active',
                    'currentPrice': extracted_price,
                    'lastChecked': firestore.SERVER_TIMESTAMP,
                    'history': firestore.ArrayUnion([{
                        'price': extracted_price,
                        'date': datetime.datetime.now().isoformat()
                    }])
                })
                print(f"Updated {doc.id}")

            except Exception as e:
                print(f"Error scraping {url}: {e}")
                db.collection('tracked_items').document(doc.id).update({
                    'status': 'error',
                    'errorReason': str(e)
                })

if __name__ == "__main__":
    import datetime
    asyncio.run(process_items())
