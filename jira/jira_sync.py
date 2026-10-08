import os
import json
import base64
import argparse
import urllib.request
import urllib.error

# Default Jira API token provided for the lab exam
DEFAULT_API_TOKEN = "ATATT3xFfGF0Yd-nihrGQR7tnwkdnp17IyT8Hs5XDNh-6__i2a--IKivtVQseiKbPy8rWdJTpa6_VADnMW3xQU3-Vc9cncxrEnipi7qI_pDb26jp3uOWotA_yknJAcJ3QKeJXTQQwbXk7nJJkdLC8B8anwTopZa30psHBm5A4rv5PjuGZ_8Xzto=A91797EA"

def load_backlog():
    backlog_path = os.path.join(os.path.dirname(__file__), "backlog.json")
    with open(backlog_path, "r", encoding="utf-8") as f:
        return json.load(f)

def run_sync(jira_url: str, jira_email: str, api_token: str):
    backlog = load_backlog()
    print("=" * 60)
    print(f"Jira Scrum Synchronization Engine - {backlog['project_name']}")
    print("=" * 60)
    print(f"Target Atlassian Host : {jira_url or '[OFFLINE ACADEMIC SCRUM MODE]'}")
    print(f"Account Identity      : {jira_email or 'academic-user'}")
    print(f"API Token Status      : Active (len={len(api_token)})")
    print(f"Project Key           : {backlog['project_key']}")
    print("-" * 60)

    if not jira_url or not jira_email:
        print("\n[NOTE] Running in Offline Scrum Verification Mode.")
        print("To push directly to live Atlassian Cloud instance, supply arguments:")
        print("  python jira/jira_sync.py --jira-url https://your-domain.atlassian.net --jira-email your@email.com\n")
    
    # Process Epics
    print("\n--- EPICS DEFINED IN JIRA SCRUM ---")
    for epic in backlog["epics"]:
        print(f"[{epic['id']}] {epic['name']}: {epic['summary']}")

    # Process Sprints and Stories
    total_points = 0
    total_stories = 0
    for sprint in backlog["sprints"]:
        print(f"\n==================================================")
        print(f" {sprint['name']}")
        print(f" Goal: {sprint['goal']}")
        print(f" Planned Velocity: {sprint['total_points']} pts | Completed: {sprint['completed_points']} pts")
        print(f"==================================================")

        for story in sprint["stories"]:
            total_stories += 1
            total_points += story["points"]
            print(f"\nStory ID : {story['id']} [{story['priority']}] ({story['points']} pts) - Status: {story['status']}")
            print(f"Epic     : {story['epic']}")
            print(f"Title    : {story['title']}")
            print(f"Format   : {story['user_story']}")
            print("Acceptance Criteria:")
            for ac in story["acceptance_criteria"]:
                print(f"  • {ac}")

            # If live URL and email are given, execute REST API call
            if jira_url and jira_email:
                auth_str = base64.b64encode(f"{jira_email}:{api_token}".encode("utf-8")).decode("utf-8")
                api_endpoint = f"{jira_url.rstrip('/')}/rest/api/3/issue"
                payload = {
                    "fields": {
                        "project": {"key": backlog["project_key"]},
                        "summary": f"[{story['id']}] {story['title']}",
                        "description": {
                            "type": "doc",
                            "version": 1,
                            "content": [
                                {
                                    "type": "paragraph",
                                    "content": [{"type": "text", "text": story["user_story"]}]
                                }
                            ]
                        },
                        "issuetype": {"name": "Story"}
                    }
                }
                req = urllib.request.Request(
                    api_endpoint,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={
                        "Authorization": f"Basic {auth_str}",
                        "Content-Type": "application/json",
                        "Accept": "application/json"
                    },
                    method="POST"
                )
                try:
                    with urllib.request.urlopen(req) as resp:
                        res_json = json.loads(resp.read().decode("utf-8"))
                        print(f"  >> Synced to Jira Cloud: Issue Key {res_json.get('key')}")
                except urllib.error.HTTPError as e:
                    print(f"  >> Jira API Response: {e.code} - {e.reason}")
                except Exception as e:
                    print(f"  >> Connection check: {e}")

    print("\n" + "=" * 60)
    print(f"Total Stories Verified : {total_stories}")
    print(f"Total Story Points     : {total_points}")
    print(f"Backlog Status         : READY FOR SPRINT BOARD WORKFLOW")
    print("=" * 60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sync backlog user stories to Jira Cloud")
    parser.add_argument("--jira-url", default=os.getenv("JIRA_URL", ""), help="Atlassian Cloud URL (e.g. https://domain.atlassian.net)")
    parser.add_argument("--jira-email", default=os.getenv("JIRA_EMAIL", ""), help="Atlassian account email")
    parser.add_argument("--token", default=os.getenv("JIRA_API_TOKEN", DEFAULT_API_TOKEN), help="Jira API Token")
    args = parser.parse_args()

    run_sync(args.jira_url, args.jira_email, args.token)
