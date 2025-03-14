#!/usr/bin/env python3
"""
check_onboarding_setup.py - A diagnostic script to check for common onboarding mistakes:
1. In socialme_app.py:
   - Confirms @app.route('/store_onboarding') is present.
   - Ensures it appears above if __name__ == '__main__'.
2. In templates/socialme_onboarding.html:
   - Checks for action="/store_onboarding" in the hidden form.
"""

import os

def check_socialme_app():
    filename = "socialme_app.py"
    if not os.path.isfile(filename):
        print(f"[ERROR] {filename} not found in current directory.")
        return

    with open(filename, "r") as f:
        lines = f.readlines()

    route_line = None
    main_line = None
    for i, line in enumerate(lines):
        # Find the line with @app.route('/store_onboarding')
        if "@app.route('/store_onboarding')" in line.replace(" ", ""):
            route_line = i
        # Find the line with if __name__ == '__main__':
        if "if __name__ == '__main__':" in line.replace(" ", ""):
            main_line = i

    if route_line is None:
        print("[ERROR] Did not find @app.route('/store_onboarding') in socialme_app.py.")
    else:
        print("[OK] Found @app.route('/store_onboarding') on line", route_line+1)

    if main_line is None:
        print("[ERROR] Did not find if __name__ == '__main__': block in socialme_app.py.")
    else:
        print("[OK] Found if __name__ == '__main__': on line", main_line+1)

    if route_line is not None and main_line is not None:
        if route_line > main_line:
            print("[WARNING] @app.route('/store_onboarding') appears AFTER if __name__ == '__main__'.")
            print("         This can cause a 404 because Flask never sees the route before running.")
        else:
            print("[OK] The store_onboarding route is above the if __name__ == '__main__': line.")

def check_onboarding_html():
    directory = "templates"
    filename = os.path.join(directory, "socialme_onboarding.html")

    if not os.path.isdir(directory):
        print(f"[ERROR] The {directory} folder does not exist.")
        return
    if not os.path.isfile(filename):
        print(f"[ERROR] {filename} not found.")
        return

    with open(filename, "r") as f:
        content = f.read()

    if 'action="/store_onboarding"' in content.replace(" ", ""):
        print("[OK] Found action=\"/store_onboarding\" in socialme_onboarding.html.")
    else:
        print("[ERROR] Did not find action=\"/store_onboarding\" in socialme_onboarding.html.")
        print("        The form may not be posting to the correct route.")

def main():
    print("=== Checking socialme_app.py ===")
    check_socialme_app()
    print("\n=== Checking templates/socialme_onboarding.html ===")
    check_onboarding_html()

if __name__ == "__main__":
    main()
