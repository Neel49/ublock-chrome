class UblockChrome < Formula
  desc "One-command uBlock Origin installer for Chrome (macOS)"
  homepage "https://github.com/Neel49/ublock-chrome"
  url "https://github.com/Neel49/ublock-chrome/archive/refs/tags/v1.0.3.tar.gz"
  sha256 "51614ea1f5fcf8c3ff97758a2af4457862637101e2c917cea485b0c86ed11cfd"
  license "MIT"

  depends_on :macos
  depends_on "jq"

  def install
    bin.install "bin/ublock-chrome"
  end

  def caveats
    <<~EOS
      Run this to finish setup:

        ublock-chrome install

      Then quit Chrome and open "Chrome (uBO)" from ~/Applications/.

      Other commands:
        ublock-chrome update      # grab latest uBlock Origin
        ublock-chrome launch      # quit Chrome & relaunch with uBO
        ublock-chrome uninstall   # remove extension + launcher
    EOS
  end

  test do
    assert_match "ublock-chrome", shell_output("#{bin}/ublock-chrome help")
  end
end
