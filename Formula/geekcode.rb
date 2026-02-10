class Geekcode < Formula
  include Language::Python::Virtualenv

  desc "Filesystem-driven AI agent for knowledge work"
  homepage "https://github.com/sur950/GeekCode"
  url "https://github.com/sur950/GeekCode/archive/refs/tags/v1.0.2.tar.gz"
  sha256 "REPLACE_WITH_SHA256_OF_RELEASE_TARBALL"
  license "Apache-2.0"
  head "https://github.com/sur950/GeekCode.git", branch: "main"

  depends_on "python@3.12"

  def install
    venv = virtualenv_create(libexec, "python3.12")
    # Use pip with full dependency resolution (not --no-deps)
    system Formula["python@3.12"].opt_bin/"python3.12", "-m", "pip",
           "--python=#{libexec}/bin/python", "install", "--no-cache-dir", buildpath
    bin.install_symlink libexec/"bin/geekcode"
  end

  def caveats
    <<~EOS
      GeekCode is installed. Run it in any project directory:
        geekcode

      API keys are loaded from environment variables:
        export ANTHROPIC_API_KEY="sk-ant-..."
        export OPENAI_API_KEY="sk-..."

      Free to start — no API key needed with Ollama (local), or get a free key at:
        https://openrouter.ai/settings/keys
    EOS
  end

  test do
    assert_match "GeekCode", shell_output("#{bin}/geekcode --version 2>&1", 0)
  end
end
