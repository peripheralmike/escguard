import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PackageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='escguard test ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        self.env = dict(os.environ, XDG_CONFIG_HOME=str(self.root / 'config'),
                        ESCGUARD_BIN_DIR=str(self.bin))
        self.env.pop('ESCGUARD_CODEX_BIN', None)

    def run_script(self, path, *args):
        return subprocess.run([str(path), *args], env=self.env, text=True,
                              capture_output=True)

    def test_install_and_backup_existing_files(self):
        first = self.run_script(ROOT / 'install.sh')
        self.assertEqual(first.returncode, 0, first.stderr)
        launcher = self.bin / 'codex-ssh'
        self.assertTrue(os.access(launcher, os.X_OK))
        launcher.write_text('old launcher\n')
        config = self.root / 'config/escguard/tmux.conf'
        config.write_text('old config\n')
        second = self.run_script(ROOT / 'install.sh')
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(next(self.bin.glob('codex-ssh.backup-*')).read_text(), 'old launcher\n')
        self.assertEqual(next(config.parent.glob('tmux.conf.backup-*')).read_text(), 'old config\n')
        self.assertEqual(launcher.read_bytes(), (ROOT / 'bin/codex-ssh').read_bytes())

    def test_existing_symlink_target_is_not_overwritten(self):
        target = self.root / 'original'
        target.write_text('preserve me')
        (self.bin / 'codex-ssh').symlink_to(target)
        result = self.run_script(ROOT / 'install.sh')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(target.read_text(), 'preserve me')
        self.assertFalse((self.bin / 'codex-ssh').is_symlink())
        self.assertTrue(next(self.bin.glob('codex-ssh.backup-*')).is_symlink())

    def test_noninteractive_forwarding_preserves_arguments_and_exit_code(self):
        fake = self.bin / 'real codex'
        fake.write_text('#!/usr/bin/env python3\nimport json,sys\nprint(json.dumps(sys.argv[1:]))\nsys.exit(23)\n')
        fake.chmod(0o755)
        self.env['ESCGUARD_CODEX_BIN'] = str(fake)
        args = ['exec', 'a prompt with spaces', 'literal $HOME; text', '']
        result = self.run_script(ROOT / 'bin/codex-ssh', *args)
        self.assertEqual(result.returncode, 23)
        self.assertEqual(json.loads(result.stdout), args)

    def test_recursion_is_rejected(self):
        self.env['ESCGUARD_CODEX_BIN'] = str(ROOT / 'bin/codex-ssh')
        result = self.run_script(ROOT / 'bin/codex-ssh')
        self.assertEqual(result.returncode, 1)
        self.assertIn('points back', result.stderr)

    def test_missing_codex_has_actionable_error(self):
        self.env['ESCGUARD_CODEX_BIN'] = str(self.root / 'missing')
        result = self.run_script(ROOT / 'bin/codex-ssh')
        self.assertEqual(result.returncode, 1)
        self.assertIn('ESCGUARD_CODEX_BIN', result.stderr)


if __name__ == '__main__':
    unittest.main()
