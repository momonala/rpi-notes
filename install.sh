apt-get update

# install git
apt-get install bc git -y

# Install uv (Python package manager)
if ! command -v uv &> /dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
else
    echo "✅ uv is already installed. Updating to latest version."
    uv self update
fi
