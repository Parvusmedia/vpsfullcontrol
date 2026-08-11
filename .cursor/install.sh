#!/usr/bin/env bash
# Idempotent setup for the vpsfullcontrol Cloud Agent environment.
#
# This repo is a CI/CD control repo: it only contains GitHub Actions workflow
# YAML. There is nothing to build or run. The development workflow is editing
# and validating those workflows, so we install the two linters used for that:
#   - actionlint : GitHub Actions workflow linter
#   - yamllint   : generic YAML linter
set -euo pipefail

ACTIONLINT_VERSION="1.7.7"
BIN_DIR="${HOME}/.local/bin"
mkdir -p "${BIN_DIR}"

install_actionlint() {
  if command -v "${BIN_DIR}/actionlint" >/dev/null 2>&1 \
     && "${BIN_DIR}/actionlint" -version 2>/dev/null | grep -qE "^v?${ACTIONLINT_VERSION}$"; then
    echo "actionlint ${ACTIONLINT_VERSION} already installed"
    return 0
  fi
  echo "Installing actionlint ${ACTIONLINT_VERSION}..."
  local arch tarball url tmp
  case "$(uname -m)" in
    x86_64|amd64) arch="amd64" ;;
    aarch64|arm64) arch="arm64" ;;
    *) echo "Unsupported arch $(uname -m)" >&2; return 1 ;;
  esac
  tarball="actionlint_${ACTIONLINT_VERSION}_linux_${arch}.tar.gz"
  url="https://github.com/rhysd/actionlint/releases/download/v${ACTIONLINT_VERSION}/${tarball}"
  tmp="$(mktemp -d)"
  curl -fsSL "${url}" -o "${tmp}/${tarball}"
  tar -xzf "${tmp}/${tarball}" -C "${tmp}" actionlint
  install -m 0755 "${tmp}/actionlint" "${BIN_DIR}/actionlint"
  rm -rf "${tmp}"
}

install_yamllint() {
  if command -v "${BIN_DIR}/yamllint" >/dev/null 2>&1; then
    echo "yamllint already installed"
    return 0
  fi
  echo "Installing yamllint..."
  # --break-system-packages keeps this working on PEP 668 (externally managed)
  # Python installs; --user places the console script in ~/.local/bin.
  pip3 install --user --break-system-packages yamllint
}

install_actionlint
install_yamllint

echo "Verifying tools..."
"${BIN_DIR}/actionlint" -version
"${BIN_DIR}/yamllint" --version
echo "Setup complete. Ensure ${BIN_DIR} is on PATH (export PATH=\"\$HOME/.local/bin:\$PATH\")."
