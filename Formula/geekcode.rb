class Geekcode < Formula
  include Language::Python::Virtualenv

  desc "Filesystem-driven AI agent for knowledge work"
  homepage "https://github.com/sur950/GeekCode"
  url "https://github.com/sur950/GeekCode/archive/refs/tags/v1.0.0.tar.gz"
  sha256 "REPLACE_WITH_SHA256_OF_RELEASE_TARBALL"
  license "Apache-2.0"
  head "https://github.com/sur950/GeekCode.git", branch: "main"

  depends_on "python@3.12"

  resource "click" do
    url "https://files.pythonhosted.org/packages/96/d3/f04c7bfcf5c1862a2a5b845c6b2b360488cf47af55dfa79c98f6a6bf98b5/click-8.1.7.tar.gz"
    sha256 "ca9853ad459e787e2192211578cc907e7594e294c7ccc834310722b41b9ca6de"
  end

  resource "pyyaml" do
    url "https://files.pythonhosted.org/packages/cd/e5/af35f7ea75cf72f2cd079c95ee16797de7cd71f29ea7c68ae5ce7be1edd0/PyYAML-6.0.1.tar.gz"
    sha256 "bfdf460b1736c775f2ba9f6a92bca30bc2095067b8a9d77876d1fad6cc3b4a43"
  end

  resource "rich" do
    url "https://files.pythonhosted.org/packages/a7/ec/4a7d80728b1b74f7db3847f0d4b6a6c345494e58cc29ae2c1e6006bc4185/rich-13.9.4.tar.gz"
    sha256 "439594978a49a09530cff7ebc4b5c7103ef57c74d50de5708b36f6c288d829e2"
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
