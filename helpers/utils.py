import os
from datetime import datetime
from supabase import create_client, Client

from dotenv import load_dotenv # can be installed with `pip install python-dotenv`

load_dotenv('.env.local')



def get_supabase_client():
    url: str = os.getenv("SUPABASE_URL")
    key: str = os.getenv("SUPABASE_KEY")
    supabase: Client = create_client(url, key)
    supabase.auth.sign_in_with_password({ "email": os.getenv("SUPABASE_USER"), "password": os.getenv("SUPABASE_PASSWORD") })
    return supabase

def get_last_n_posts(supabase, n=10):
    response = supabase.auth.refresh_session()
    print(response)

    """
    Get the N most recent posts ordered by timestamp in descending order.
    
    Args:
        supabase: Supabase client instance
        n (int): Number of posts to return (default 10)
        
    Returns:
        list: The N most recent posts
    """
    response = supabase.table("posts_created") \
                      .select("*") \
                      .order("timestamp", desc=True) \
                      .limit(n) \
                      .execute()
    return response.data


def get_all_posts(supabase):
    response = supabase.table("posts_created").select("*").execute()
    return response.data

def set_post_created(supabase, post):
    hash = post['hash']
    text = post['text']
    parent_id = post['parent_id']
    timestamp = str(datetime.now())

    response = supabase.table("posts_created").insert(
        {"hash": hash, 
         "content": text, 
         "parent_id": parent_id,
         "timestamp": timestamp}).execute()
    return response.data

def main():
    supabase = get_supabase_client()
    print("Successfully connected to Supabase!")

    response = get_last_n_posts(supabase, 10)
    print(response)

    # print(user)

    # response = (
    #     supabase.table("countries")
    #     .insert({"id": 1, "name": "Denmark"})
    #     .execute()
    # )    
    # print(response.content)

    # sample_post = {
    #     'hash': '0x123abc123xyz',
    #     'text': 'This is a sample post',
    #     'parent_id': '0x000FFF'
    # }
    # set_post_created(supabase, sample_post)
    # get_posts(supabase)


if __name__ == "__main__":
    main()


