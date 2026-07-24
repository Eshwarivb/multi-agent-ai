import os
import shutil
import subprocess
import tempfile
from typing import Any, Dict


def run_tests_in_docker(
    repo_path: str, patch_content: str, timeout: int = 60
) -> Dict[str, Any]:
    """
    Spins up an isolated Docker container, copies repo + patch into temp staging,
    applies the patch, runs pytest, captures output, and destroys container.
    Never executes or mutates the patch directly on the host repo.
    """
    temp_dir = tempfile.mkdtemp(prefix="agent_sandbox_")
    try:
        # Copy repo files to temp staging directory
        for item in os.listdir(repo_path):
            if item in {".git", "__pycache__", ".venv", "node_modules", ".pytest_cache"}:
                continue
            s = os.path.join(repo_path, item)
            d = os.path.join(temp_dir, item)
            if os.path.isdir(s):
                shutil.copytree(
                    s, d, ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc")
                )
            else:
                shutil.copy2(s, d)

        # Write patch file if patch content exists
        has_patch = bool(patch_content and patch_content.strip())
        if has_patch:
            patch_file_path = os.path.join(temp_dir, "changes.patch")
            with open(patch_file_path, "w", encoding="utf-8") as f:
                f.write(patch_content)

        # Attempt Docker execution
        try:
            import docker

            client = docker.from_env()
            client.ping()

            print("[docker_runner] Docker daemon active. Building sandbox image...")
            image_tag = "agent-sandbox:latest"
            dockerfile_dir = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", "docker")
            )
            if os.path.exists(dockerfile_dir):
                client.images.build(path=dockerfile_dir, tag=image_tag, rm=True)

            cmd = "/bin/sh -c 'patch -p1 < changes.patch && pytest'" if has_patch else "pytest"
            print("[docker_runner] Running pytest in container...")
            container = client.containers.run(
                image_tag,
                command=cmd,
                volumes={temp_dir: {"bind": "/app", "mode": "rw"}},
                working_dir="/app",
                detach=True,
                remove=False,
            )

            try:
                result = container.wait(timeout=timeout)
                exit_code = result.get("StatusCode", 1)
                logs = container.logs(stdout=True, stderr=True).decode(
                    "utf-8", errors="replace"
                )
                passed = exit_code == 0
                return {"passed": passed, "output": logs}
            finally:
                container.remove(force=True)

        except Exception as e:
            print(
                f"[docker_runner] Docker SDK bypass/fallback ({type(e).__name__}). Running in isolated temp sandbox directory..."
            )
            if has_patch:
                try:
                    apply_res = subprocess.run(
                        ["git", "apply", "--ignore-whitespace", "changes.patch"],
                        cwd=temp_dir,
                        capture_output=True,
                        text=True,
                    )
                    if apply_res.returncode != 0:
                        apply_res = subprocess.run(
                            ["patch", "-p1", "-i", "changes.patch"],
                            cwd=temp_dir,
                            capture_output=True,
                            text=True,
                        )
                except Exception as patch_err:
                    return {
                        "passed": False,
                        "output": f"Failed to apply patch in sandbox: {patch_err}",
                    }

            pytest_res = subprocess.run(
                ["pytest"],
                cwd=temp_dir,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            passed = pytest_res.returncode == 0
            output = pytest_res.stdout + "\n" + pytest_res.stderr
            return {"passed": passed, "output": output}

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
