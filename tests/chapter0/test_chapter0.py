import os
import subprocess
import sys

# 프로젝트 루트를 sys.path에 추가하여 const 모듈을 임포트할 수 있도록 합니다.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from const import ROOT_PATH


def run_script(script_path, env=None):
    """스크립트를 실행하고 표준 출력과 에러를 반환하는 헬퍼 함수"""
    # chapter0 디렉토리에서 스크립트를 실행하도록 `cwd`를 설정합니다.
    # .env 파일이나 test.log 파일이 chapter0 디렉토리 기준으로 생성되고 참조되기 때문입니다.
    cwd = os.path.dirname(script_path)
    result = subprocess.run(
        [sys.executable, os.path.basename(script_path)],
        capture_output=True,
        text=True,
        cwd=cwd,
        env=env,
    )
    return result.stdout, result.stderr


def test_dotenv_example():
    """dotenv_example.py가 .env 파일의 환경 변수를 올바르게 로드하는지 테스트합니다."""
    script_path = ROOT_PATH / "chapter0" / "dotenv_example.py"
    stdout, stderr = run_script(script_path)

    assert "mongodb://root:root1234" in stdout
    assert "local" in stdout
    assert stderr == ""


def test_get_env_example():
    """get_env_example.py가 os.getenv를 사용하여 환경 변수를 올바르게 읽는지 테스트합니다."""
    script_path = ROOT_PATH / "chapter0" / "get_env_example.py"

    # 테스트를 위한 환경 변수 설정
    test_env = os.environ.copy()
    test_env["OPENAI_API_KEY"] = "test_api_key_12345"

    stdout, stderr = run_script(script_path, env=test_env)

    assert "test_api_key_12345" in stdout
    assert stderr == ""


def cleanup_log_file():
    """테스트 후 생성된 로그 파일을 삭제하는 함수"""
    log_file = ROOT_PATH / "chapter0" / "test.log"
    if os.path.exists(log_file):
        os.remove(log_file)


def test_logging_example():
    """logging_example.py가 로그를 파일에 올바르게 기록하는지 테스트합니다."""
    cleanup_log_file()  # 이전 테스트에서 남은 로그 파일이 있다면 삭제

    script_path = ROOT_PATH / "chapter0" / "logging_example.py"
    stdout, stderr = run_script(script_path)

    assert stderr == ""

    log_file = ROOT_PATH / "chapter0" / "test.log"
    assert os.path.exists(log_file)

    with open(log_file, "r", encoding="utf-8") as f:
        log_content = f.read()
        assert "디버그 레벨 메시지입니다." in log_content
        assert "정보 레벨 메시지입니다." in log_content
        assert "경고 레벨 메시지입니다." in log_content
        assert "에러 레벨 메시지입니다." in log_content
        assert "치명적 에러 레벨 메시지입니다." in log_content

    cleanup_log_file()  # 테스트 종료 후 로그 파일 삭제


def test_handler_logging_example():
    """handler_logging_example.py가 설정된 레벨에 따라 로그를 올바르게 기록하는지 테스트합니다."""
    cleanup_log_file()  # 이전 테스트에서 남은 로그 파일이 있다면 삭제

    script_path = ROOT_PATH / "chapter0" / "handler_logging_example.py"
    stdout, stderr = run_script(script_path)

    assert "디버그 레벨 메시지입니다." in stdout  # 콘솔 출력 확인
    assert "정보 레벨 메시지입니다." in stdout
    assert stderr == ""

    log_file = ROOT_PATH / "chapter0" / "test.log"
    assert os.path.exists(log_file)

    with open(log_file, "r", encoding="utf-8") as f:
        log_content = f.read()
        # 파일에는 INFO 레벨 이상만 기록되어야 합니다.
        assert "디버그 레벨 메시지입니다." not in log_content
        assert "정보 레벨 메시지입니다." in log_content
        assert "경고 레벨 메시지입니다." in log_content
        assert "에러 레벨 메시지입니다." in log_content
        assert "치명적 에러 레벨 메시지입니다." in log_content

    cleanup_log_file()  # 테스트 종료 후 로그 파일 삭제
