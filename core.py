import glob
import os
import subprocess
import shutil


def get_installed_gui_apps():
    apps = {}
    directories = [
        "/usr/share/applications",
        os.path.expanduser("~/.local/share/applications"),
        "/var/lib/snapd/desktop/applications",
    ]
    for directory in directories:
        if not os.path.exists(directory):
            continue
        for desktop_file in glob.glob(os.path.join(directory, "*.desktop")):
            try:
                with open(desktop_file, "r") as f:
                    content = f.read()
                    name_line = [
                        line
                        for line in content.split("\n")
                        if line.startswith("Name=")
                    ]
                    if name_line:
                        app_name = name_line[0].split("=", 1)[1].strip()
                        apps[desktop_file] = app_name
            except Exception:
                pass
    return apps


def resolve_app_package(desktop_file):
    try:
        with open(desktop_file, "r") as f:
            content = f.read()
            snap_line = [
                line
                for line in content.split("\n")
                if line.startswith("X-SnapInstanceName=")
            ]
            if snap_line:
                return "snap", snap_line[0].split("=", 1)[1].strip()
    except Exception:
        pass

    try:
        output = subprocess.check_output(
            ["dpkg", "-S", desktop_file], stderr=subprocess.DEVNULL
        ).decode("utf-8")
        return "apt", output.split(":")[0].strip()
    except Exception:
        try:
            with open(desktop_file, "r") as f:
                content = f.read()
                exec_line = [
                    line
                    for line in content.split("\n")
                    if line.startswith("Exec=")
                ]
                if exec_line:
                    pkg_candidate = (
                        exec_line[0]
                        .split("=", 1)[1]
                        .strip()
                        .split()[0]
                        .split("/")[-1]
                    )
                    if (
                        subprocess.run(
                            ["dpkg", "-l", pkg_candidate],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                        ).returncode
                        == 0
                    ):
                        return "apt", pkg_candidate
        except Exception:
            pass
    return None, None


def uninstall_packages(desktop_files, full=False):
    packages_to_apt_remove = []
    packages_to_snap_remove = []

    for desk_file in desktop_files:
        pkg_type, pkg_name = resolve_app_package(desk_file)
        if pkg_type == "apt":
            packages_to_apt_remove.append(pkg_name)
        elif pkg_type == "snap":
            packages_to_snap_remove.append(pkg_name)

    if packages_to_apt_remove:
        packages_to_apt_remove = list(set(packages_to_apt_remove))
        print(f"Uninstalling via apt: {', '.join(packages_to_apt_remove)}")
        subprocess.call(["sudo", "apt-get", "remove", "-y"] + packages_to_apt_remove)

    if packages_to_snap_remove:
        packages_to_snap_remove = list(set(packages_to_snap_remove))
        print(f"Uninstalling via snap: {', '.join(packages_to_snap_remove)}")
        for pkg in packages_to_snap_remove:
            subprocess.call(["sudo", "snap", "remove", pkg])

    if full:
        print("Performing deep cleanup (--full)...")
        for desk_file in desktop_files:
            try:
                with open(desk_file, "r") as f:
                    content = f.read()
                    name_line = [
                        line
                        for line in content.split("\n")
                        if line.startswith("Name=")
                    ]
                    if name_line:
                        app_name = name_line[0].split("=", 1)[1].strip()
                        names_to_clean = list(
                            set(
                                [
                                    app_name.lower(),
                                    app_name.lower().replace(" ", ""),
                                    app_name.lower().replace(" ", "-"),
                                ]
                            )
                        )

                        home = os.path.expanduser("~")
                        for name in names_to_clean:
                            paths = [
                                os.path.join(home, ".cache", name),
                                os.path.join(home, ".config", name),
                                os.path.join(home, ".local", "share", name),
                                os.path.join(home, "snap", name),
                                os.path.join("/tmp", name),
                            ]
                            for path in paths:
                                if os.path.exists(path):
                                    if os.path.isdir(path):
                                        shutil.rmtree(path)
                                    else:
                                        os.remove(path)
                                    print(f"Removed tracking artifact: {path}")
            except Exception:
                pass
            if os.path.exists(desk_file) and ".local/share" in desk_file:
                try:
                    os.remove(desk_file)
                    print(f"Removed local desktop file: {desk_file}")
                except Exception:
                    pass

    print("Uninstallation complete.")
