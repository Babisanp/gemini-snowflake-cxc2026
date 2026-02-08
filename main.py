import os
import json
import time
from fastapi import FastAPI
from dotenv import load_dotenv
from google import genai
from google.genai import types
from snowflake_db import snowflake_table

load_dotenv()

app = FastAPI()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

@app.get("/")
def read_root():
    return {"message": "FastAPI is running!"}


@app.post("/recipes")
def run_recipe_engine(payload: dict):
    ### List of Fridge Items for CV Model ###
    fridge_cv = payload["fridge_items"]

    data_json = snowflake_table(fridge_cv)

    def get_all_titles():
        print("[DEBUG] Loading JSON file...")
        try:
            data = json.loads(data_json)
            return [str(i).strip() for i in data if i]
        except Exception as e:
            print(f"[DEBUG] Error: {e}")
            return []

    all_titles = get_all_titles()

    prompt = payload["prompt"]

    print(f"[DEBUG] 👤 User Input: {prompt}")
    start_process = time.time()

    titles_block = "\n".join(all_titles)

    system_prompt = f"""
You are a recipe matching engine.

From the DATABASE below:
1. First, consider relevance to: "{prompt}"
2. Then randomly select EXACTLY 5 different recipe titles

Return a bulleted list of exactly 5 titles.
Only return titles that exist in the database.
Do not add explanations or extra text.

DATABASE:
{titles_block}
"""

    try:
        print("[DEBUG] 🚀 Sending full database to Gemini...")
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=system_prompt,
            config=types.GenerateContentConfig(temperature=0.7)
        )
        final_response = response.text
        print(final_response)
    except Exception as e:
        final_response = f"Error: {e}"
        print(final_response)

    end_process = time.time()
    print(f"[DEBUG] ✅ Total time: {end_process - start_process:.2f} seconds.")
    print(type(final_response))

    lines = final_response.split('\n')
    clean_list = [line.replace("*", "").strip() for line in lines if line.strip()]

    print(clean_list)

    recipe_database = json.loads(data_json)

    final_output = []

    for target_title in clean_list:
        for recipe in recipe_database:
            if recipe["title"] == target_title:
                selected_data = {
                    "title": recipe["title"],
                    "NER": recipe["NER"],
                    "directions": recipe["directions"],
                    "link": recipe["link"]
                }
                final_output.append(selected_data)
                break


    with open("recipe_frontend_output.json", "w") as f:
        json.dump(final_output, f, indent=4)

    print("✅ File saved as recipe_frontend_output.json")

    return final_output
