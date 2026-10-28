import os
import shutil
import subprocess
import threading
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib

os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Tutaj podaj nazwy swoich plików .png dla poszczególnych programów:
APPS_CONFIG = [
    {
        "name": "Mozilla Firefox",
        "binary": "firefox",
        "package": "firefox",
        "desc": "Web Browser",
        "icon": "firefox.png"
    },
    {
        "name": "Discord",
        "binary": "discord",
        "package": "discord",
        "desc": "Communication",
        "icon": "discord.png"
    },
    {
        "name": "Aseprite",
        "binary": "aseprite",
        "package": "aseprite",
        "desc": "Pixel Art Editor",
        "icon": "aseprite.png"
    }
]


class SystemManager:
    @staticmethod
    def get_preferred_manager():
        for mgr in ["yay", "pacman", "apt"]:
            if shutil.which(mgr):
                return mgr
        return None

    @classmethod
    def is_installed(cls, binary_name, pkg_name):
        if shutil.which(binary_name):
            return True
        mgr = cls.get_preferred_manager()
        try:
            if mgr in ["pacman", "yay"]:
                res = subprocess.run(["pacman", "-Qi", pkg_name],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return res.returncode == 0
            elif mgr == "apt":
                res = subprocess.run(["dpkg", "-s", pkg_name],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return res.returncode == 0
        except Exception:
            pass
        return False


class TermosLauncher(Gtk.Window):
    def __init__(self):
        super().__init__(title="Termos Launcher")
        self.set_default_size(580, 680)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.mgr = SystemManager.get_preferred_manager()

        self.load_css()

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(main_box)

        # =========================================================
        # SEKCJA 1: Tytuł (Twój thumbnail.png bez stylów i dodatków)
        # =========================================================
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        header.get_style_context().add_class("header-box")

        if os.path.exists("thumbnail.png"):
            thumb_img = Gtk.Image.new_from_file("thumbnail.png")
            header.pack_start(thumb_img, False, False, 0)
        else:
            header.pack_start(Gtk.Label(label="[Brak thumbnail.png w katalogu]", xalign=0), False, False, 0)

        main_box.pack_start(header, False, False, 0)

        # =========================================================
        # SEKCJA 2: Guziki programów (Miniatury po lewej, Start/Download po prawej)
        # =========================================================
        scroller = Gtk.ScrolledWindow()
        scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        main_box.pack_start(scroller, True, True, 0)

        list_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        list_box.set_margin_top(16)
        list_box.set_margin_bottom(16)
        list_box.set_margin_start(16)
        list_box.set_margin_end(16)
        scroller.add(list_box)

        for app in APPS_CONFIG:
            card = self.create_app_card(app)
            list_box.pack_start(card, False, False, 0)

    def load_css(self):
        css_provider = Gtk.CssProvider()
        if os.path.exists("style.css"):
            css_provider.load_from_path("style.css")
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def create_app_card(self, app):
        card = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
        card.get_style_context().add_class("app-card")

        # 1. Miniatura programu po LEWEJ stronie (Twój plik .png)
        if os.path.exists(app["icon"]):
            icon_img = Gtk.Image.new_from_file(app["icon"])
            card.pack_start(icon_img, False, False, 0)

        # 2. Nazwa i opis programu
        info = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        lbl_name = Gtk.Label(label=app["name"], xalign=0)
        lbl_name.get_style_context().add_class("app-name")
        lbl_desc = Gtk.Label(label=app["desc"], xalign=0)
        lbl_desc.get_style_context().add_class("app-desc")
        info.pack_start(lbl_name, False, False, 0)
        info.pack_start(lbl_desc, False, False, 0)
        card.pack_start(info, True, True, 0)

        # 3. Przycisk po PRAWEJ stronie (Download / Start)
        btn = Gtk.Button()
        pkg = app["package"]
        pkg_name = pkg.get(self.mgr, app["binary"]) if isinstance(pkg, dict) else pkg

        self.update_button(btn, app, pkg_name)
        card.pack_end(btn, False, False, 0)

        return card

    def update_button(self, btn, app, pkg_name):
        ctx = btn.get_style_context()
        ctx.remove_class("btn-start")
        ctx.remove_class("btn-download")
        ctx.remove_class("btn-busy")

        if SystemManager.is_installed(app["binary"], pkg_name):
            btn.set_label("▶ Start")
            ctx.add_class("btn-start")
            btn.set_sensitive(True)
            try: btn.disconnect_by_func(self.on_start_clicked)
            except Exception: pass
            try: btn.disconnect_by_func(self.on_download_clicked)
            except Exception: pass
            btn.connect("clicked", self.on_start_clicked, app["binary"])
        else:
            btn.set_label("⬇ Download")
            ctx.add_class("btn-download")
            btn.set_sensitive(True)
            try: btn.disconnect_by_func(self.on_start_clicked)
            except Exception: pass
            try: btn.disconnect_by_func(self.on_download_clicked)
            except Exception: pass
            btn.connect("clicked", self.on_download_clicked, app, pkg_name)

    def on_start_clicked(self, btn, binary_name):
        try:
            subprocess.Popen([binary_name])
        except Exception as e:
            dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.OK, f"Błąd:\n{e}")
            dialog.run()
            dialog.destroy()

    def on_download_clicked(self, btn, app, pkg_name):
        if not self.mgr:
            dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.WARNING, Gtk.ButtonsType.OK, "Brak menedżera pakietów.")
            dialog.run()
            dialog.destroy()
            return

        btn.set_label("Instalacja...")
        btn.set_sensitive(False)
        btn.get_style_context().remove_class("btn-download")
        btn.get_style_context().add_class("btn-busy")

        def worker():
            ask_pass = "pkexec" if shutil.which("pkexec") else "sudo"
            if self.mgr == "yay":
                cmd = ["yay", "-S", "--noconfirm", pkg_name]
            elif self.mgr == "pacman":
                cmd = [ask_pass, "pacman", "-S", "--noconfirm", pkg_name]
            elif self.mgr == "apt":
                cmd = [ask_pass, "apt-get", "install", "-y", pkg_name]

            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            success = (res.returncode == 0)

            def update_ui():
                self.update_button(btn, app, pkg_name)
                msg_type = Gtk.MessageType.INFO if success else Gtk.MessageType.ERROR
                msg_txt = f"Zainstalowano {app['name']}!" if success else f"Błąd:\n{res.stderr[:200]}"
                dialog = Gtk.MessageDialog(self, 0, msg_type, Gtk.ButtonsType.OK, msg_txt)
                dialog.run()
                dialog.destroy()

            GLib.idle_add(update_ui)

        threading.Thread(target=worker, daemon=True).start()


if __name__ == "__main__":
    win = TermosLauncher()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
