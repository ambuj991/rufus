from rufus import RufusClient
import os

key = os.getenv('RUFUS_API_KEY')
client = RufusClient(api_key=key)

# Works with ANY URL and ANY instructions
instructions = "Tell me about shopping deals on Amazon."
documents = client.scrape("https://www.amazon.com/")

# Or the HR example
# instructions = "We're making a chatbot for the HR in San Francisco."
# documents = client.scrape("https://www.sfgov.com")

# Save the results
client.save(documents, "extracted_data.json")