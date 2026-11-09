#!/usr/bin/env bash
set -euo pipefail
source_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
bin_dir=${ESCGUARD_BIN_DIR:-$HOME/.local/bin}
config_dir=${XDG_CONFIG_HOME:-$HOME/.config}/escguard
backup_stamp=$(date +%Y%m%d%H%M%S)-$$
for dependency in bash tmux infocmp; do
    if ! command -v "$dependency" >/dev/null 2>&1; then
        printf 'Missing dependency: %s\nOn Debian: sudo apt install bash tmux ncurses-bin ncurses-term\n' "$dependency" >&2
        exit 1
    fi
done
infocmp tmux-256color >/dev/null 2>&1 || {
    printf '%s\n' 'Missing tmux-256color terminfo. On Debian: sudo apt install ncurses-term' >&2
    exit 1
}
mkdir -p -- "$bin_dir" "$config_dir"
for destination in "$bin_dir/codex-ssh" "$config_dir/tmux.conf"; do
    if [[ -e "$destination" || -L "$destination" ]]; then
        cp -Pp -- "$destination" "$destination.backup-$backup_stamp"
        printf 'Backup: %s\n' "$destination.backup-$backup_stamp"
        # Unlink a previous symlink rather than overwrite its target.
        if [[ -L "$destination" ]]; then
            unlink -- "$destination"
        fi
    fi
done
install -m 755 -- "$source_dir/bin/codex-ssh" "$bin_dir/codex-ssh"
install -m 644 -- "$source_dir/config/tmux.conf" "$config_dir/tmux.conf"
printf 'Installed %s\nConfiguration: %s\n' "$bin_dir/codex-ssh" "$config_dir/tmux.conf"
printf '%s\n' 'Ensure the install directory is on PATH, then run: codex-ssh' 'Optional Bash alias: alias codex="codex-ssh"'
