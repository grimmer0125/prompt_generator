import anthropic
import time
import requests
from bs4 import BeautifulSoup
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ANTHROPIC_API_KEY: str = ""
    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        
setting = Settings()  

client = anthropic.Anthropic(api_key=setting.ANTHROPIC_API_KEY)
MODEL_NAME = "claude-3-5-sonnet-20240620"

def fetch_article_content(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.decompose()
    
    # Get text
    text = soup.get_text()
    
    # Break into lines and remove leading and trailing space on each
    lines = (line.strip() for line in text.splitlines())
    # Break multi-headlines into a line each
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    # Drop blank lines
    text = '\n'.join(chunk for chunk in chunks if chunk)
    
    return text



def make_non_cached_api_call(book_content: str):
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "<book>" + book_content + "</book>",
                    "cache_control": {"type": "ephemeral"}
                },
                {
                    "type": "text",
                    "text": "What is the title of this book? Only output the title."
                }
            ]
        }
    ]

    start_time = time.time()
    response = client.messages.create(
        model=MODEL_NAME,
        max_tokens=300,
        messages=messages,
        extra_headers={"anthropic-beta": "prompt-caching-2024-07-31"}

    )
    end_time = time.time()

    return response, end_time - start_time




def make_cached_api_call(book_content: str):
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "<book>" + book_content + "</book>",
                    "cache_control": {"type": "ephemeral"}
                },
                {
                    "type": "text",
                    "text": "What is the title of this book? Only output the title."
                }
            ]
        }
    ]

    start_time = time.time()
    response = client.messages.create(
        model=MODEL_NAME,
        max_tokens=300,
        messages=messages,
        extra_headers={"anthropic-beta": "prompt-caching-2024-07-31"}
    )
    end_time = time.time()

    return response, end_time - start_time



def main():
    # Fetch the content of the bookd, Pride and Prejudice by Jane Austen
    book_url = "https://www.gutenberg.org/cache/epub/1342/pg1342.txt"
    book_content = fetch_article_content(book_url)

    print(f"Fetched {len(book_content)} characters from the book.")
    print("First 500 characters:")
    print(book_content[:500])

    # make_non_cached_api_call
    non_cached_response, non_cached_time = make_non_cached_api_call(book_content)

    print(f"Non-cached API call time: {non_cached_time:.2f} seconds")
    print(f"Non-cached API call input tokens: {non_cached_response.usage.input_tokens}")
    print(f"Non-cached API call output tokens: {non_cached_response.usage.output_tokens}")

    print("\nSummary (non-cached):")
    print(non_cached_response.content)

    # make_cached_api_call
    cached_response, cached_time = make_cached_api_call(book_content)

    print(f"Cached API call time: {cached_time:.2f} seconds")
    print(f"Cached API call input tokens: {cached_response.usage.input_tokens}")
    print(f"Cached API call output tokens: {cached_response.usage.output_tokens}")

    print("\nSummary (cached):")
    print(cached_response.content)


if __name__ == "__main__":
    main()