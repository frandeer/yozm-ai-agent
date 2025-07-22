import os
import subprocess


def run_chapter1_scripts():
    """
    chapter1 디렉토리의 모든 파이썬 스크립트를 실행합니다.
    """
    chapter1_dir = "chapter1"
    print("Running chapter1 scripts...")

    if not os.path.isdir(chapter1_dir):
        print(f"Error: Directory '{chapter1_dir}' not found.")
        return

    # chapter1 디렉토리 내의 모든 .py 파일을 찾습니다.
    scripts = sorted([f for f in os.listdir(chapter1_dir) if f.endswith(".py")])

    for script in scripts:
        script_path = os.path.join(chapter1_dir, script)
        print("----------------------------------------")
        print(f"Executing {script_path}...")
        print("----------------------------------------")
        try:
            # 각 스크립트를 파이썬으로 실행합니다.
            # `check=True`는 실행 중 오류가 발생하면 예외를 발생시킵니다.
            subprocess.run(["python", script_path], check=True, text=True)
        except subprocess.CalledProcessError as e:
            print(f"Error executing {script_path}:")
            print(e)
        except FileNotFoundError:
            print(
                f"Error: 'python' command not found. Make sure Python is installed and in your PATH."
            )
            break
        print("\n")

    print("All chapter1 scripts have been executed.")


if __name__ == "__main__":
    run_chapter1_scripts()
