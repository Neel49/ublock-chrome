class UblockChrome < Formula
  desc "One-command uBlock Origin installer for Chrome (macOS)"
  homepage "https://github.com/Neel49/ublock-chrome"
  url "https://github.com/Neel49/ublock-chrome/archive/refs/tags/v1.0.0.tar.gz"
  sha256 "a56851f766f0fd6165dfd1e40d2049de45cba688f0c8d114ced7b8a78f44a6eb"
  license "MIT"

  depends_on :macos
  depends_on "jq"

  def install
    bin.install "bin/ublock-chrome"
  end

  def post_install
    system "#{bin}/ublock-chrome", "install"
  end

  def caveats
    <<~EOS
      To set up uBlock Origin on Chrome:

        ublock-chrome install

      This downloads uBlock Origin and creates a "Chrome (uBO)" launcher
      app in ~/Applications/ that auto-loads the extension.

      Always launch Chrome via "Chrome (uBO)" (or `ublock-chrome launch`)
      so the ad-blocking flags stay active.

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
