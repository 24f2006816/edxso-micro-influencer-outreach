"""
GitHub Uploader Script using GitHub REST API.
Creates the public repository 'edxso-micro-influencer-outreach' under user '24f2006816'
and uploads all project files directly without requiring a local git binary.
"""

import os
import sys
import base64
import json
import urllib.request
import urllib.error

GITHUB_USER = "24f2006816"
REPO_NAME = "edxso-micro-influencer-outreach"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def api_request(url, data=None, token=None, method=None):
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "EDXSO-Uploader-Script",
    }
    if token:
        headers["Authorization"] = f"token {token}"
    
    encoded_data = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=encoded_data, headers=headers, method=method)
    
    try:
        with urllib.request.urlopen(req) as response:
            res_body = response.read().decode("utf-8")
            return json.loads(res_body) if res_body else {}
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8")
        try:
            return {"_error_code": e.code, "_error": json.loads(err_msg)}
        except Exception:
            return {"_error_code": e.code, "_error": err_msg}


def create_or_get_repo(token):
    print(f"[*] Checking/Creating Public Repository: https://github.com/{GITHUB_USER}/{REPO_NAME}...")
    url = "https://api.github.com/user/repos"
    payload = {
        "name": REPO_NAME,
        "description": "EDXSO AI Engineer Intern - Assignment 1: Automated Micro-Influencer Outreach System",
        "private": False,
        "auto_init": True
    }
    res = api_request(url, data=payload, token=token, method="POST")
    if "_error_code" in res and res["_error_code"] != 422: # 422 usually means already exists
        print(f"[!] Warning/Info creating repo: {res['_error']}")
    else:
        print(f"[+] Repository ready: https://github.com/{GITHUB_USER}/{REPO_NAME}")


def upload_file(rel_path, token):
    file_path = os.path.join(BASE_DIR, rel_path)
    with open(file_path, "rb") as f:
        content_b64 = base64.b64encode(f.read()).decode("utf-8")

    url = f"https://api.github.com/repos/{GITHUB_USER}/{REPO_NAME}/contents/{rel_path}"
    
    # Check if file exists to get sha
    sha = None
    existing = api_request(url, token=token, method="GET")
    if isinstance(existing, dict) and "sha" in existing:
        sha = existing["sha"]

    payload = {
        "message": f"feat: add {rel_path}",
        "content": content_b64,
    }
    if sha:
        payload["sha"] = sha

    res = api_request(url, data=payload, token=token, method="PUT")
    if "_error_code" in res:
        print(f"[-] Failed uploading {rel_path}: {res['_error']}")
    else:
        print(f"[+] Uploaded: {rel_path}")


def main():
    if len(sys.argv) < 2:
        print("=" * 70)
        print(" GitHub Automatic Uploader for 24f2006816")
        print("=" * 70)
        print("Usage:")
        print("  python3 push_to_github.py <YOUR_GITHUB_PERSONAL_ACCESS_TOKEN>")
        print("\nTo generate a token:")
        print("  1. Go to: https://github.com/settings/tokens")
        print("  2. Click 'Generate new token (classic)'")
        print("  3. Select scope 'repo' and click 'Generate token'")
        print("  4. Run: python3 push_to_github.py ghp_yourTokenHere")
        print("=" * 70)
        sys.exit(1)

    token = sys.argv[1].strip()
    create_or_get_repo(token)

    files_to_upload = []
    for root, dirs, files in os.walk(BASE_DIR):
        if "__pycache__" in root or ".git" in root:
            continue
        for file in files:
            if file.endswith(".pyc") or file == "push_to_github.py":
                continue
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, BASE_DIR)
            files_to_upload.append(rel_path)

    print(f"\n[*] Uploading {len(files_to_upload)} project files to GitHub...")
    for rel_p in sorted(files_to_upload):
        upload_file(rel_p, token)

    print("\n" + "=" * 70)
    print(f"🎉 Successfully pushed to: https://github.com/{GITHUB_USER}/{REPO_NAME}")
    print("=" * 70)


if __name__ == "__main__":
    main()
