pkgname=termos-launcher
pkgver=1.0.0
pkgrel=1
pkgdesc="Application launcher and package manager helper"
arch=('any')
url="https://localhost"
license=('GPL-3.0-or-later')
depends=('python' 'gtk3' 'python-gobject')

package() {

    install -dm755 "$pkgdir/usr/share/$pkgname"
    install -m644 "$startdir/main.py" "$pkgdir/usr/share/$pkgname/main.py"
    install -m644 "$startdir/style.css" "$pkgdir/usr/share/$pkgname/style.qss"

    for png in "$startdir"/*.png; do
        if [ -f "$png" ]; then
            install -m644 "$png" "$pkgdir/usr/share/$pkgname/"
        fi
    done

    install -Dm755 "$startdir/termos-launcher" "$pkgdir/usr/bin/termos-launcher"

    install -Dm644 "$startdir/termos-launcher.desktop" "$pkgdir/usr/share/applications/termos-launcher.desktop"

    if [ -f "$startdir/thumbnail.png" ]; then
        install -Dm644 "$startdir/thumbnail.png" "$pkgdir/usr/share/pixmaps/termos-launcher.png"
    fi
}
