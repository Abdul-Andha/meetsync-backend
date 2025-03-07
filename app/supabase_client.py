"""A file to create a supabase client"""

import os

from dotenv import dotenv_values
from supabase import Client, create_client

config = dotenv_values(".env")
supabase: Client = None


def get_supabase_client() -> Client:
    global supabase

    if supabase is None:
        supabase_url = config.get("SUPABASE_URL", os.getenv("SUPABASE_URL"))
        supabase_key = config.get("SUPABASE_KEY", os.getenv("SUPABASE_KEY"))
        if not supabase_url:
            raise ValueError("Supabase URL must be set in environment variables.")
        if not supabase_key:
            raise ValueError("Supabase Key must be set in environment variables.")
        supabase = create_client(supabase_url, supabase_key)
    return supabase
