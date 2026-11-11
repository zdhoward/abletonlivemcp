"""One compact install/reinstall/fault scenario; optionally exercise a built wheel."""

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


def _hashes(directory):
    return {
        str(path.relative_to(directory)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(directory.rglob("*")) if path.is_file()
    }


def _scenario(root):
    import abletonlivemcp
    from abletonlivemcp import config, install

    print(f"module={abletonlivemcp.__file__}")
    home = root / "home"
    home.mkdir()
    library = root / "library"
    (library / "Presets").mkdir(parents=True)
    with pytest.MonkeyPatch.context() as patch:
        for name in ("HOME", "USERPROFILE"):
            patch.setenv(name, str(home))
        patch.setenv("HOMEDRIVE", home.drive)
        patch.setenv("HOMEPATH", str(home)[len(home.drive):])
        patch.setenv("ABLETONLIVEMCP_CONFIG", str(home / "private" / "bridge.json"))
        print(f"home={Path.home()} config={config.config_path()} cwd={Path.cwd()}")
        assert Path.home() == home
        unrelated = library / "Remote Scripts" / "OtherScript"
        unrelated.mkdir(parents=True)
        (unrelated / "keep.txt").write_text("unrelated", encoding="utf-8")
        unrelated_before = _hashes(unrelated)
        dest = install.install(library)
        initial = _hashes(dest)
        private = config.load_config()
        secret_present = bool(private.get("secret"))
        assert secret_present and private["read_only"] is True
        config._check_private(config.config_path())
        principal = (
            "current-user-only; protected DACL; full control"
            if os.name == "nt" else "owner uid; mode 0600"
        )
        print(
            f"secret_present={secret_present} read_only_default={private['read_only']} "
            f"permissions={principal}"
        )
        # Preserve a user-selected policy too, rather than only checking the default.
        private["read_only"] = False
        config.config_path().write_text(json.dumps(private), encoding="utf-8")
        install.install(library)
        after = _hashes(dest)
        print(f"success before={json.dumps(initial, sort_keys=True)}")
        print(f"success after={json.dumps(after, sort_keys=True)}")
        assert initial == after
        backups = list(dest.parent.glob(f".{install.SCRIPT}.backup-*"))
        assert len(backups) == 1 and _hashes(backups[0]) == initial
        # A running Python script creates bytecode: retain that in the next backup.
        (dest / "__pycache__").mkdir()
        (dest / "__pycache__" / "core.cpython-312.pyc").write_bytes(b"runtime cache")
        cached = _hashes(dest)
        install.install(library)
        backups = list(dest.parent.glob(f".{install.SCRIPT}.backup-*"))
        assert any(_hashes(backup) == cached for backup in backups)
        assert not (dest / "config.py").exists()  # nothing in the Remote Script imports it
        # Backups do not pile up: one more install leaves only the newest owned backup.
        install.install(library)
        assert len(list(dest.parent.glob(f".{install.SCRIPT}.backup-*"))) == 1
        restored = config.load_config()
        secret_same = restored["secret"] == private["secret"]
        policy_same = restored["read_only"] == private["read_only"]
        assert secret_same and policy_same
        print(
            f"secret_unchanged={secret_same} policy_unchanged={policy_same} "
            "no_config_copy=True backups_pruned_to=1"
        )
        with pytest.MonkeyPatch.context() as default:
            default.delenv("ABLETONLIVEMCP_CONFIG")
            default_same = config.config_path() == home / ".abletonlivemcp" / "bridge.json"
            assert default_same
        print(f"default_discovery={default_same}")

        def attempt(label, fault_code):
            before = _hashes(dest)
            code = (
                "import sys\nfrom pathlib import Path\n"
                f"sys.path.insert(0, {str(Path(abletonlivemcp.__file__).parents[1])!r})\n"
                "from abletonlivemcp import install\n" + fault_code
                + f"\ninstall.main({[str(library)]!r})\n"
            )
            command = [sys.executable, "-c", code]
            result = subprocess.run(command, cwd=root, capture_output=True, text=True)
            assert result.returncode == 1 and "Installation failed:" in result.stderr
            after = _hashes(dest)
            print(f"{label} command={command!r}")
            print(f"{label} exit={result.returncode}: {result.stderr.strip()}")
            print(f"{label} before={json.dumps(before, sort_keys=True)}")
            print(f"{label} after={json.dumps(after, sort_keys=True)}")
            assert before == after

        attempt(
            "copy_failure",
            "def fail(*args, **kwargs):\n    raise OSError('injected copy failure')\n"
            "install.shutil.copyfileobj = fail\n",
        )
        attempt(
            "replacement_failure",
            "rename = Path.rename\ndef fail(path, target):\n"
            "    if '.stage-' in path.name:\n"
            "        raise PermissionError('injected locked destination')\n"
            "    return rename(path, target)\nPath.rename = fail\n",
        )
        assert not list(dest.parent.glob(f".{install.SCRIPT}.stage-*"))
        (dest / install.MANIFEST).rename(dest / "unknown-owner.json")
        attempt("unknown_folder", "")
        (dest / "unknown-owner.json").rename(dest / install.MANIFEST)
        assert _hashes(unrelated) == unrelated_before
        print(f"unrelated before={json.dumps(unrelated_before)}")
        print(f"unrelated after={json.dumps(_hashes(unrelated))}")
        with pytest.MonkeyPatch.context() as invalid:
            for value in ("", "relative.json"):
                invalid.setenv("ABLETONLIVEMCP_CONFIG", value)
                with pytest.raises(config.ConfigError, match="absolute"):
                    config.ensure_config()
        print("invalid_explicit_override_refused=True")
        # Exercise actual directory reparse rejection without requiring symlink privileges.
        linked = root / "linked-library"
        if os.name == "nt":
            result = subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(linked), str(library)],
                capture_output=True, text=True,
            )
            assert result.returncode == 0
        else:
            linked.symlink_to(library, target_is_directory=True)
        with pytest.raises(config.ConfigError, match="symlink/junction/reparse"):
            install.install(linked)
        # Remove only the link, never recurse through it.
        if os.name == "nt":
            linked.rmdir()
        else:
            linked.unlink()
        with pytest.MonkeyPatch.context() as overlap:
            overlap.setenv("ABLETONLIVEMCP_CONFIG", str(dest / "bridge.json"))
            with pytest.raises(install.InstallError, match="overlap"):
                install.install(library)
        insecure = home / "insecure.json"
        insecure.write_text("{}", encoding="utf-8")
        if os.name == "nt":
            result = subprocess.run(
                ["icacls", str(insecure), "/grant", "*S-1-1-0:(R)"],
                capture_output=True, text=True,
            )
            assert result.returncode == 0
        else:
            insecure.chmod(0o644)
        with pytest.MonkeyPatch.context() as permissions:
            permissions.setenv("ABLETONLIVEMCP_CONFIG", str(insecure))
            with pytest.raises(config.ConfigError, match="owner"):
                config.ensure_config()
        print("reparse_refused=True overlap_refused=True insecure_config_refused=True")
        config._check_private(config.config_path())
        final = config.load_config()
        unchanged = (
            final["secret"] == private["secret"] and final["read_only"] == private["read_only"]
        )
        assert unchanged
        print(f"faults_config_unchanged={unchanged} restrictive_access=True")


def test_install_reinstall_and_failures(tmp_path):
    wheel = os.environ.get("ABLETONLIVEMCP_TEST_WHEEL")
    if wheel:
        command = [
            sys.executable, "-c",
            "import sys, runpy; sys.path.insert(0, sys.argv[1]); "
            "runpy.run_path(sys.argv[2], run_name='__main__')",
            wheel, str(Path(__file__).absolute()), str(tmp_path),
        ]
        result = subprocess.run(command, cwd=tmp_path, capture_output=True, text=True)
        evidence = os.environ.get("ABLETONLIVEMCP_TEST_EVIDENCE")
        if evidence:
            Path(evidence).write_text(
                f"command={subprocess.list2cmdline(command)}\nexit={result.returncode}\n"
                + result.stdout + result.stderr, encoding="utf-8",
            )
        assert result.returncode == 0, result.stdout + result.stderr
    else:
        _scenario(tmp_path)


if __name__ == "__main__":
    _scenario(Path(sys.argv[3]))
