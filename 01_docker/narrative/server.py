import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import psycopg


HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8181"))
WORDS_BASE_URL = os.getenv("WORDS_BASE_URL", "http://words:8080")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://model-runner.docker.internal/engines/v1")
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "ai/smollm2")
DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "postgres")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")


class NarrativeHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        print(f"[narrative] {self.command} {self.path}")
        if self.path == "/narrative":
            self.handle_narrative()
            return

        if self.path == "/healthz":
            self.send_json(200, {"status": "ok"})
            return

        self.send_json(404, {"error": "Not found"})

    def log_message(self, format, *args):
        return

    def handle_narrative(self):
        try:
            components = fetch_words()
            print(f"[narrative] fetched words: {components}")
            story = generate_story(components)
            print(f"[narrative] generated story length={len(story)}")
            save_story(story)
            self.send_json(200, {
                "story": story,
                "components": components,
                "model": LLM_MODEL_NAME
            })
        except Exception as error:
            print(f"[narrative] error: {error}")
            self.send_json(500, {
                "error": str(error),
                "model": LLM_MODEL_NAME,
                "llm_base_url": LLM_BASE_URL,
            })

    def send_json(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def fetch_words():
    return {
        "adjective1": fetch_word("/adjective"),
        "noun1": fetch_word("/noun"),
        "verb": fetch_word("/verb"),
        "adjective2": fetch_word("/adjective"),
        "noun2": fetch_word("/noun"),
    }


def fetch_word(path):
    print(f"[narrative] fetching word from {WORDS_BASE_URL}{path}")
    with urlopen(f"{WORDS_BASE_URL}{path}") as response:
        payload = json.loads(response.read().decode("utf-8"))
        print(f"[narrative] word response {path}: {payload}")
        return payload["word"]


def generate_story(components):
    prompt = (
        "Write a short whimsical story of 3 sentences max using these words: "
        f"{components['adjective1']}, {components['noun1']}, {components['verb']}, "
        f"{components['adjective2']}, {components['noun2']}. "
        "Return plain text only."
    )

    payload = {
        "model": LLM_MODEL_NAME,
        "messages": [
            {"role": "system", "content": "You write playful, family-friendly micro-stories."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.8,
    }

    request = Request(
        f"{LLM_BASE_URL}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer docker-model-runner",
        },
        method="POST",
    )

    try:
        print(f"[narrative] calling model {LLM_MODEL_NAME} at {LLM_BASE_URL}/chat/completions")
        print(f"[narrative] prompt preview: {prompt[:160]}")
        with urlopen(request) as response:
            completion = json.loads(response.read().decode("utf-8"))
            print(f"[narrative] model response keys: {list(completion.keys())}")
    except HTTPError as error:
        error_body = error.read().decode("utf-8", errors="replace")
        print(f"[narrative] model HTTP error status={error.code} reason={error.reason}")
        print(f"[narrative] model HTTP error body: {error_body[:1000]}")
        raise RuntimeError(f"Model server returned HTTP {error.code}: {error.reason}") from error
    except URLError as error:
        print(f"[narrative] model network error: {error}")
        raise RuntimeError(f"Failed to reach model server: {error}") from error
    except Exception as error:
        print(f"[narrative] unexpected model call error: {error}")
        raise

    try:
        return completion["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError) as error:
        print(f"[narrative] unexpected model response payload: {json.dumps(completion)[:1000]}")
        raise RuntimeError(f"Unexpected model response: {completion}") from error


def save_story(story):
    print(f"[narrative] saving story with model {LLM_MODEL_NAME}")
    with psycopg.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    ) as connection:
        ensure_stories_table(connection)
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO stories (story, model) VALUES (%s, %s)",
                (story, LLM_MODEL_NAME),
            )
        connection.commit()
    print("[narrative] story saved")


def ensure_stories_table(connection):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS stories (
                story TEXT NOT NULL,
                model TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


if __name__ == "__main__":
    print(f"[narrative] words base URL: {WORDS_BASE_URL}")
    print(f"[narrative] model base URL: {LLM_BASE_URL}")
    print(f"[narrative] model name: {LLM_MODEL_NAME}")
    print(f"[narrative] database host: {DB_HOST}:{DB_PORT}/{DB_NAME}")
    server = ThreadingHTTPServer((HOST, PORT), NarrativeHandler)
    print(f"narrative listening on http://{HOST}:{PORT}")
    server.serve_forever()
