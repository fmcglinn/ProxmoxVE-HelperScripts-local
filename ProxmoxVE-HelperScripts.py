import os
import subprocess
import json
import questionary

JSON_DIR = "./frontend/public/json"

def load_metadata():
    scripts = []
    for filename in os.listdir(JSON_DIR):
        if filename.endswith(".json"):
            full_path = os.path.join(JSON_DIR, filename)
            try:
                with open(full_path, "r") as f:
                    data = json.load(f)
                    if not isinstance(data, dict):
                      continue  # skip files like versions.json
                    name = data.get("name")
                    script_type = data.get("type", "other")
                    install_methods = data.get("install_methods", [])
                    for method in install_methods:
                        script_path = method.get("script")
                        if script_path:
                            scripts.append({
                                "name": name,
                                "type": script_type,
                                "script": script_path
                            })
            except Exception as e:
                print(f"⚠️ Failed to parse {filename}: {e}")
    return scripts

def group_by_type(scripts):
    grouped = {}
    for script in scripts:
        grouped.setdefault(script["type"], []).append(script)
    return grouped

def present_menu(grouped_scripts):
    type_choices = sorted(grouped_scripts.keys())

    selected_type = questionary.select(
        "Select a script type:",
        choices=type_choices,
        qmark="📁",
    ).ask()

    if not selected_type:
        return

    entries = grouped_scripts[selected_type]
    script_choices = [f'{entry["name"]}' for entry in entries]

    selected_script = questionary.select(
        "Select a script to run:",
        choices=script_choices,
        qmark="📜",
    ).ask()

    if selected_script:
        index = script_choices.index(selected_script)
        run_script(entries[index]["script"])

def run_script(path):
    abs_path = os.path.abspath(path)
    if not os.path.exists(abs_path):
        print(f"❌ Script not found: {abs_path}")
        return
    print(f"\n🚀 Running: {abs_path}\n")
    subprocess.run(["bash", abs_path])

def main():
    scripts = load_metadata()
    if not scripts:
        print("❌ No valid scripts found.")
        return
    grouped = group_by_type(scripts)
    present_menu(grouped)

if __name__ == "__main__":
    main()
