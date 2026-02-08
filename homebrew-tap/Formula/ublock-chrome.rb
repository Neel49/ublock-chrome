class UblockChrome < Formula
  desc "One-command uBlock Origin installer for Chrome (macOS)"
  homepage "https://github.com/Neel49/ublock-chrome"
  url "https://github.com/Neel49/ublock-chrome/archive/refs/tags/v1.0.2.tar.gz"
  sha256 "4c12a3a96f6bf2b75ad206fa355625d2a433f47ef4194aa091cfc26dc7c73766"
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
