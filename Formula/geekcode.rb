class Geekcode < Formula
  include Language::Python::Virtualenv

  desc "Filesystem-driven AI agent for knowledge work"
  homepage "https://github.com/sur950/GeekCode"
  url "https://github.com/sur950/GeekCode/archive/refs/tags/v1.0.0.tar.gz"
  sha256 "95f04f123078b0a289ae73c894f0c31dc35bd2cd374f454fc6136fa53fb8e974"
  license "Apache-2.0"
  head "https://github.com/sur950/GeekCode.git", branch: "main"

  depends_on "python@3.12"

  resource "click" do
    url "https://github.com/sur950/GeekCode/archive/refs/tags/v1.0.0.tar.gz"
    sha256 "95f04f123078b0a289ae73c894f0c31dc35bd2cd374f454fc6136fa53fb8e974"
  end

  resource "pyyaml" do
    url "https://github.com/sur950/GeekCode/archive/refs/tags/v1.0.0.tar.gz"
    sha256 "95f04f123078b0a289ae73c894f0c31dc35bd2cd374f454fc6136fa53fb8e974"
  end

  resource "rich" do
    url "https://github.com/sur950/GeekCode/archive/refs/tags/v1.0.0.tar.gz"
    sha256 "95f04f123078b0a289ae73c894f0c31dc35bd2cd374f454fc6136fa53fb8e974"
  end

  def install
    virtualenv_install_with_resources
  end

  def caveats
    <<~EOS
      GeekCode is installed. Run it in any project directory:
        geekcode

      API keys are loaded from environment variables:
        export ANTHROPIC_API_KEY="sk-ant-..."
        export OPENAI_API_KEY="sk-..."
    EOS
  end

  test do
    assert_match "geekcode", shell_output("#{bin}/geekcode --help 2>&1", 0)
  end
end
