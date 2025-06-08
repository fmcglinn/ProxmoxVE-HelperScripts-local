#!/usr/bin/env python3
import os
import sys
import subprocess
import json

VENV_DIR = os.path.join(os.path.dirname(__file__), ".venv")
REQUIRED_PKG = "questionary"
JSON_DIR = "./frontend/public/json"

def show_header():
  print(r"""
╔════════════════════════════════════════════════════════════════════╗
║                    ProxmoxVE-HelperScripts                         ║
║        https://github.com/fmcglinn/ProxmoxVE-HelperScripts         ║
╚════════════════════════════════════════════════════════════════════╝
""")

def is_inside_venv():
  return sys.prefix == os.path.abspath(VENV_DIR)

def get_python_venv_package():
    version = f"{sys.version_info.major}.{sys.version_info.minor}"
    return f"python{version}-venv"


def is_package_installed(pkg):
    result = subprocess.run(["dpkg", "-s", pkg], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return result.returncode == 0


def install_system_package(pkg):
    print(f"> Installing {pkg}...")
    update_cmd = ["apt-get", "update"]
    install_cmd = ["apt-get", "install", "-y", pkg]
    if os.geteuid() != 0:
        update_cmd.insert(0, "sudo")
        install_cmd.insert(0, "sudo")
    subprocess.run(update_cmd, check=True)
    subprocess.run(install_cmd, check=True)


def pip_install(package):
    print(f"> Installing {package}...")
    subprocess.check_call([os.path.join(VENV_DIR, "bin", "python"), "-m", "pip", "install", package])


def is_package_installed_in_venv(pip_path, package):
    result = subprocess.run(
        [pip_path, "show", package],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    return result.returncode == 0


def create_venv_if_needed():
    if not os.path.exists(VENV_DIR):
        venv_pkg = get_python_venv_package()
        if not is_package_installed(venv_pkg):
            print(f"> {venv_pkg} is missing")
            install_system_package(venv_pkg)

        print("> Creating virtual environment...")
        import venv
        venv.create(VENV_DIR, with_pip=True)


def ensure_venv_and_deps():
    create_venv_if_needed()

    if not is_package_installed("python3-pip"):
        print("> python3-pip is missing. Installing...")
        install_system_package("python3-pip")

    pip_path = os.path.join(VENV_DIR, "bin", "pip")
    if not is_package_installed_in_venv(pip_path, REQUIRED_PKG):
        pip_install(REQUIRED_PKG)


def relaunch_inside_venv():
    python = os.path.join(VENV_DIR, "bin", "python")
    os.execv(python, [python] + sys.argv)


# === Menu Script Logic ===
def load_metadata():
    scripts = []
    for filename in os.listdir(JSON_DIR):
        if filename.endswith(".json"):
            full_path = os.path.join(JSON_DIR, filename)
            try:
                with open(full_path, "r") as f:
                    data = json.load(f)
                    if not isinstance(data, dict):
                        continue
                    name = data.get("name")
                    script_type = data.get("type", "other")
                    for method in data.get("install_methods", []):
                        script = method.get("script")
                        if script:
                            scripts.append({
                                "name": name,
                                "type": script_type,
                                "script": script
                            })
            except Exception as e:
                print(f"> Failed to parse {filename}: {e}")
    return scripts


def group_by_type(scripts):
    grouped = {}
    for entry in scripts:
        grouped.setdefault(entry["type"], []).append(entry)
    return grouped


def run_script(path):
    abs_path = os.path.abspath(path)
    if not os.path.exists(abs_path):
        print(f"> Script not found: {abs_path}")
        return
    print(f"\n> Running: {abs_path}\n")
    subprocess.run(["bash", abs_path])


def present_menu(grouped):
    import questionary

    types = sorted(grouped.keys())
    selected_type = questionary.select(
        "Select a script type:",
        choices=types,
        qmark=">"
    ).ask()

    if not selected_type:
        return

    entries = grouped[selected_type]
    choices = [f'{e["name"]} ({e["script"]})' for e in entries]

    selected = questionary.select(
        "Select a script to run:",
        choices=choices,
        qmark=">"
    ).ask()

    if selected:
        index = choices.index(selected)
        run_script(entries[index]["script"])


def main():
    if not is_inside_venv():
      ensure_venv_and_deps()
      relaunch_inside_venv()

    scripts = load_metadata()
    if not scripts:
        print("> No valid scripts found.")
        sys.exit(1)

    os.system("echo -ne '\ec'")
    show_header()
    grouped = group_by_type(scripts)
    present_menu(grouped)


if __name__ == "__main__":
    main()
