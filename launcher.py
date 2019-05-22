"""
Welcome to Launcher
"""
from __future__ import print_function
import os
import sys
import subprocess
try:                                        # Older Pythons lack this
    import urllib.request                   # We'll let them reach the Python
    from importlib.util import find_spec    # check anyway
except ImportError:
    pass
import platform
import webbrowser
import hashlib
import argparse
import shutil
import stat
import time
try:
    import pip
except ImportError:
    pip = None

REQS_DIR = "lib"
sys.path.insert(0, REQS_DIR)
REQS_TXT = "requirements.txt"
REQS_NO_AUDIO_TXT = "requirements_no_audio.txt"
FFMPEG_BUILDS_URL = "https://ffmpeg.zeranoe.com/builds/"

INTRO = ("==========================\n"
         "레드 봇 \n"
         "==========================\n")

IS_WINDOWS = os.name == "nt"
IS_MAC = sys.platform == "darwin"
IS_64BIT = platform.machine().endswith("64")
INTERACTIVE_MODE = not len(sys.argv) > 1  # CLI flags = non-interactive
PYTHON_OK = sys.version_info >= (3, 5)

FFMPEG_FILES = {
    "ffmpeg.exe"  : "e0d60f7c0d27ad9d7472ddf13e78dc89",
    "ffplay.exe"  : "d100abe8281cbcc3e6aebe550c675e09",
    "ffprobe.exe" : "0e84b782c0346a98434ed476e937764f"
}


def parse_cli_arguments():
    parser = argparse.ArgumentParser(description="Red - Discord Bot's launcher")
    parser.add_argument("--start", "-s",
                        help="Starts Red",
                        action="store_true")
    parser.add_argument("--auto-restart",
                        help="Autorestarts Red in case of issues",
                        action="store_true")
    parser.add_argument("--update-red",
                        help="Updates Red (git)",
                        action="store_true")
    parser.add_argument("--update-reqs",
                        help="Updates requirements (w/ audio)",
                        action="store_true")
    parser.add_argument("--update-reqs-no-audio",
                        help="Updates requirements (w/o audio)",
                        action="store_true")
    parser.add_argument("--repair",
                        help="Issues a git reset --hard",
                        action="store_true")
    return parser.parse_args()


def install_reqs(audio):
    remove_reqs_readonly()
    interpreter = sys.executable

    if interpreter is None:
        print("파이썬 인터프리터를 찾을 수 없음")
        return

    txt = REQS_TXT if audio else REQS_NO_AUDIO_TXT

    args = [
        interpreter, "-m",
        "pip", "install",
        "--upgrade",
        "--target", REQS_DIR,
        "-r", txt
    ]

    if IS_MAC: # --target is a problem on Homebrew. See PR #552
        args.remove("--target")
        args.remove(REQS_DIR)

    code = subprocess.call(args)

    if code == 0:
        print("\n요구 사항 설정이 완료되었습니다.")
    else:
        print("\n오류가 발생했으며 요구 사항 설정이 "
              "완료하지 마십시오. 문서를 참조하십시오..\n")


def update_pip():
    interpreter = sys.executable

    if interpreter is None:
        print("파이썬 인터프리터가 없습니다.")
        return

    args = [
        interpreter, "-m",
        "pip", "install",
        "--upgrade", "pip"
    ]

    code = subprocess.call(args)

    if code == 0:
        print("\nPip가 업데이트되었습니다.")
    else:
        print("\n오류가 발생했으며 pip가 업데이트되지 않았을 수 있습니다.")


def update_red():
    try:
        code = subprocess.call(("git", "pull", "--ff-only"))
    except FileNotFoundError:
        print("\n오류 : 힘내 찾을 수 없습니다. 그것은 설치되지 않았거나 "
              "PATH 환경 변수는 가이드에서 요청한 것과 같습니다.")
        return
    if code == 0:
        print("\n레드 봇 업데이트")
    else:
        print("\n빨간색이 제대로 업데이트되지 않았습니다. 이것이 편집으로 인해 발생하는 경우 "
              "코드에서 수리 옵션을 시도 할 수 있습니다"
              "유지 관리 하위 메뉴")


def reset_red(reqs=False, data=False, cogs=False, git_reset=False):
    if reqs:
        try:
            shutil.rmtree(REQS_DIR, onerror=remove_readonly)
            print("설치된 로컬 패키지가 지워졌습니다..")
        except FileNotFoundError:
            pass
        except Exception as e:
            print("설치 제거 중 오류가 발생했습니다. "
                  "requirements: {}".format(e))
    if data:
        try:
            shutil.rmtree("data", onerror=remove_readonly)
            print("'data' 폴더를 깔끔하게 밀어버렸습니다!")
        except FileNotFoundError:
            pass
        except Exception as e:
            print("'data' 폴더를 미는데 오류가 발생하였습니다! 오류코드: "
                  "{}".format(e))

    if cogs:
        try:
            shutil.rmtree("cogs", onerror=remove_readonly)
            print("'cogs'폴더를 깔끔하게 밀어버렸습니다!")
        except FileNotFoundError:
            pass
        except Exception as e:
            print("'cog' 폴더를 미는데 오류가 발생하였습니다! 오류코드: "
                  "{}".format(e))


    if git_reset:
        code = subprocess.call(("git", "reset", "--hard"))
        if code == 0:
            print("Red has been restored to the last local commit.")
        else:
            print("The repair has failed.")


def download_ffmpeg(bitness):
    clear_screen()
    repo = "https://github.com/Twentysix26/Red-DiscordBot/raw/master/"
    verified = []

    if bitness == "32bit":
        print("Please download 'ffmpeg 32bit static' from the page that "
              "is about to open.\nOnce done, open the 'bin' folder located "
              "inside the zip.\nThere should be 3 files: ffmpeg.exe, "
              "ffplay.exe, ffprobe.exe.\nPut all three of them into the "
              "bot's main folder.")
        time.sleep(4)
        webbrowser.open(FFMPEG_BUILDS_URL)
        return

    for filename in FFMPEG_FILES:
        if os.path.isfile(filename):
            print("{} already present. Verifying integrity... "
                  "".format(filename), end="")
            _hash = calculate_md5(filename)
            if _hash == FFMPEG_FILES[filename]:
                verified.append(filename)
                print("Ok")
                continue
            else:
                print("Hash mismatch. Redownloading.")
        print("{}을 다운로드 하고 있는 중입니다! 잠시만 기달려 주.".format(filename))
        with urllib.request.urlopen(repo + filename) as data:
            with open(filename, "wb") as f:
                f.write(data.read())
        print("다운로드가 완료되었습니다!.")

    for filename, _hash in FFMPEG_FILES.items():
        if filename in verified:
            continue
        print("Verifying {}... ".format(filename), end="")
        if not calculate_md5(filename) != _hash:
            print("Passed.")
        else:
            print("Hash mismatch. Please redownload.")

    print("\nAll files have been downloaded.")


def verify_requirements():
    sys.path_importer_cache = {} # I don't know if the cache reset has any
    basic = find_spec("discord") # side effect. Without it, the lib folder
    audio = find_spec("nacl")    # wouldn't be seen if it didn't exist
    if not basic:                # when the launcher was started
        return None
    elif not audio:
        return False
    else:
        return True


def is_git_installed():
    try:
        subprocess.call(["git", "--version"], stdout=subprocess.DEVNULL,
                                              stdin =subprocess.DEVNULL,
                                              stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        return False
    else:
        return True


def requirements_menu():
    clear_screen()
    while True:
        print(INTRO)
        print("Main requirements:\n")
        print("1. Install basic + audio requirements (recommended)")
        print("2. Install basic requirements")
        if IS_WINDOWS:
            print("\nffmpeg (required for audio):")
            print("3. Install ffmpeg 32bit")
            if IS_64BIT:
                print("4. Install ffmpeg 64bit (recommended on Windows 64bit)")
        print("\n0. Go back")
        choice = user_choice()
        if choice == "1":
            install_reqs(audio=True)
            wait()
        elif choice == "2":
            install_reqs(audio=False)
            wait()
        elif choice == "3" and IS_WINDOWS:
            download_ffmpeg(bitness="32bit")
            wait()
        elif choice == "4" and (IS_WINDOWS and IS_64BIT):
            download_ffmpeg(bitness="64bit")
            wait()
        elif choice == "0":
            break
        clear_screen()


def update_menu():
    clear_screen()
    while True:
        print(INTRO)
        reqs = verify_requirements()
        if reqs is None:
            status = "No requirements installed"
        elif reqs is False:
            status = "Basic requirements installed (no audio)"
        else:
            status = "Basic + audio requirements installed"
        print("Status: " + status + "\n")
        print("Update:\n")
        print("Red:")
        print("1. Update Red + requirements (recommended)")
        print("2. Update Red")
        print("3. Update requirements")
        print("\nOthers:")
        print("4. Update pip (might require admin privileges)")
        print("\n0. Go back")
        choice = user_choice()
        if choice == "1":
            update_red()
            print("Updating requirements...")
            reqs = verify_requirements()
            if reqs is not None:
                install_reqs(audio=reqs)
            else:
                print("The requirements haven't been installed yet.")
            wait()
        elif choice == "2":
            update_red()
            wait()
        elif choice == "3":
            reqs = verify_requirements()
            if reqs is not None:
                install_reqs(audio=reqs)
            else:
                print("The requirements haven't been installed yet.")
            wait()
        elif choice == "4":
            update_pip()
            wait()
        elif choice == "0":
            break
        clear_screen()


def maintenance_menu():
    clear_screen()
    while True:
        print(INTRO)
        print("Maintenance:\n")
        print("1. Repair Red (discards code changes, keeps data intact)")
        print("2. Wipe 'data' folder (all settings, cogs' data...)")
        print("3. Wipe 'lib' folder (all local requirements / local installed"
              " python packages)")
        print("4. Factory reset")
        print("\n0. Go back")
        choice = user_choice()
        if choice == "1":
            print("Any code modification you have made will be lost. Data/"
                  "non-default cogs will be left intact. Are you sure?")
            if user_pick_yes_no():
                reset_red(git_reset=True)
                wait()
        elif choice == "2":
            print("Are you sure? This will wipe the 'data' folder, which "
                  "contains all your settings and cogs' data.\nThe 'cogs' "
                  "folder, however, will be left intact.")
            if user_pick_yes_no():
                reset_red(data=True)
                wait()
        elif choice == "3":
            reset_red(reqs=True)
            wait()
        elif choice == "4":
            print("Are you sure? This will wipe ALL your Red's installation "
                  "data.\nYou'll lose all your settings, cogs and any "
                  "modification you have made.\nThere is no going back.")
            if user_pick_yes_no():
                reset_red(reqs=True, data=True, cogs=True, git_reset=True)
                wait()
        elif choice == "0":
            break
        clear_screen()


def run_red(autorestart):
    interpreter = sys.executable

    if interpreter is None: # This should never happen
        raise RuntimeError("Couldn't find Python's interpreter")

    if verify_requirements() is None:
        print("You don't have the requirements to start Red. "
              "Install them from the launcher.")
        if not INTERACTIVE_MODE:
            exit(1)

    cmd = (interpreter, "red.py")

    while True:
        try:
            code = subprocess.call(cmd)
        except KeyboardInterrupt:
            code = 0
            break
        else:
            if code == 0:
                break
            elif code == 26:
                print("Restarting Red...")
                continue
            else:
                if not autorestart:
                    break

    print("Red has been terminated. Exit code: %d" % code)

    if INTERACTIVE_MODE:
        wait()


def clear_screen():
    if IS_WINDOWS:
        os.system("cls")
    else:
        os.system("clear")


def wait():
    if INTERACTIVE_MODE:
        input("엔터를 눌러 계속 하십시오.")


def user_choice():
    return input("> ").lower().strip()


def user_pick_yes_no():
    choice = None
    yes = ("yes", "y")
    no = ("no", "n")
    while choice not in yes and choice not in no:
        choice = input("Yes/No > ").lower().strip()
    return choice in yes


def remove_readonly(func, path, excinfo):
    os.chmod(path, 0o755)
    func(path)


def remove_reqs_readonly():
    """Workaround for issue #569"""
    if not os.path.isdir(REQS_DIR):
        return
    os.chmod(REQS_DIR, 0o755)
    for root, dirs, files in os.walk(REQS_DIR):
        for d in dirs:
            os.chmod(os.path.join(root, d), 0o755)
        for f in files:
            os.chmod(os.path.join(root, f), 0o755)


def calculate_md5(filename):
    hash_md5 = hashlib.md5()
    with open(filename, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def create_fast_start_scripts():
    """Creates scripts for fast boot of Red without going
    through the launcher"""
    interpreter = sys.executable
    if not interpreter:
        return

    call = "\"{}\" launcher.py".format(interpreter)
    start_red = "{} --start".format(call)
    start_red_autorestart = "{} --start --auto-restart".format(call)
    modified = False

    if IS_WINDOWS:
        ccd = "pushd %~dp0\n"
        pause = "\npause"
        ext = ".bat"
    else:
        ccd = 'cd "$(dirname "$0")"\n'
        pause = "\nread -rsp $'Press enter to continue...\\n'"
        if not IS_MAC:
            ext = ".sh"
        else:
            ext = ".command"

    start_red             = ccd + start_red             + pause
    start_red_autorestart = ccd + start_red_autorestart + pause

    files = {
        "start_red"             + ext : start_red,
        "start_red_autorestart" + ext : start_red_autorestart
    }

    if not IS_WINDOWS:
        files["start_launcher" + ext] = ccd + call

    for filename, content in files.items():
        if not os.path.isfile(filename):
            print("{}을 만드는 중.... (fast start scripts)".format(filename))
            modified = True
            with open(filename, "w") as f:
                f.write(content)

    if not IS_WINDOWS and modified: # Let's make them executable on Unix
        for script in files:
            st = os.stat(script)
            os.chmod(script, st.st_mode | stat.S_IEXEC)


def main():
    print("git 설치 확인 중...")
    has_git = is_git_installed()
    is_git_installation = os.path.isdir(".git")
    if IS_WINDOWS:
        os.system("TITLE Red Discord Bot - Launcher")
    clear_screen()

    try:
        create_fast_start_scripts()
    except Exception as e:
        print("Failed making fast start scripts: {}\n".format(e))

    while True:
        print(INTRO)

        if not is_git_installation:
            print("WARNING: It doesn't look like Red has been "
                  "installed with git.\nThis means that you won't "
                  "be able to update and some features won't be working.\n"
                  "A reinstallation is recommended. Follow the guide "
                  "properly this time:\n"
                  "https://twentysix26.github.io/Red-Docs/\n")

        if not has_git:
            print("WARNING: Git not found. This means that it's either not "
                  "installed or not in the PATH environment variable like "
                  "requested in the guide.\n")

        print("1. 레드봇을 작동합니다! 자동재시작 포함")
        print("2. 레드봇을 작동합니다!")
        print("3. 업데이트")
        print("4. 설치해야할 필요한 것들")
        print("5. 위급할때 건드는 곳 (고치기, 리셋...)")
        print("\n0. 나가기")
        choice = user_choice()
        if choice == "1":
            run_red(autorestart=True)
        elif choice == "2":
            run_red(autorestart=False)
        elif choice == "3":
            update_menu()
        elif choice == "4":
            requirements_menu()
        elif choice == "5":
            maintenance_menu()
        elif choice == "0":
            break
        clear_screen()

args = parse_cli_arguments()

if __name__ == '__main__':
    abspath = os.path.abspath(__file__)
    dirname = os.path.dirname(abspath)
    # Sets current directory to the script's
    os.chdir(dirname)
    if not PYTHON_OK:
        print("Red needs Python 3.5 or superior. Install the required "
              "version.\nPress enter to continue.")
        if INTERACTIVE_MODE:
            wait()
        exit(1)
    if pip is None:
        print("Red cannot work without the pip module. Please make sure to "
              "install Python without unchecking any option during the setup")
        wait()
        exit(1)
    if args.repair:
        reset_red(git_reset=True)
    if args.update_red:
        update_red()
    if args.update_reqs:
        install_reqs(audio=True)
    elif args.update_reqs_no_audio:
        install_reqs(audio=False)
    if INTERACTIVE_MODE:
        main()
    elif args.start:
        print("봇을 실행하는중...")
        run_red(autorestart=args.auto_restart)
