import os
import shutil
import subprocess
import threading
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib

os.chdir(os.path.dirname(os.path.abspath(__file__)))

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
    },
    {
        "name": "Cliamp",
        "binary": "cliamp",
        "package": "cliamp",
        "desc": "Terminal Music Player",
        "icon": "cliamp.png"
    },
    {
        "name": "Nuclear",
        "binary": "nuclear-player-bin",
        "package": "nuclear-player-bin",
        "desc": "Music Player",
        "icon": "nuclear.png"
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
        self.set_default_size(800, 750)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.mgr = SystemManager.get_preferred_manager()

        self.load_css()

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(main_box)

        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        header.get_style_context().add_class("header-box")

        if os.path.exists("thumbnail.png"):
            thumb_img = Gtk.Image.new_from_file("thumbnail.png")
            header.pack_start(thumb_img, False, False, 0)
        else:
            header.pack_start(Gtk.Label(label="[Zrob kiedys thumbnail!!!]", xalign=0), False, False, 0)

        main_box.pack_start(header, False, False, 0)

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
        card = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        card.get_style_context().add_class("app-card")

        if os.path.exists(app["icon"]):
            icon_img = Gtk.Image.new_from_file(app["icon"])
            card.pack_start(icon_img, False, False, 0)

        info = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        info.set_valign(Gtk.Align.CENTER)
        lbl_name = Gtk.Label(label=app["name"], xalign=0)
        lbl_name.get_style_context().add_class("app-name")
        lbl_desc = Gtk.Label(label=app["desc"], xalign=0)
        lbl_desc.get_style_context().add_class("app-desc")
        info.pack_start(lbl_name, False, False, 0)
        info.pack_start(lbl_desc, False, False, 0)
        card.pack_start(info, True, True, 0)

        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
        btn_box.set_valign(Gtk.Align.CENTER)
        btn_box.set_homogeneous(False)

        btn_main = Gtk.Button()
        btn_update = Gtk.Button(label="Update")
        btn_remove = Gtk.Button(label="Remove")

        for b in (btn_main, btn_update, btn_remove):
            b.set_size_request(140, 140)
            b.set_halign(Gtk.Align.CENTER)
            b.set_valign(Gtk.Align.CENTER)
            b.get_style_context().add_class("btn-action")

        btn_update.get_style_context().add_class("btn-update")
        btn_remove.get_style_context().add_class("btn-remove")

        btn_box.pack_start(btn_main, False, False, 0)
        btn_box.pack_start(btn_update, False, False, 0)
        btn_box.pack_start(btn_remove, False, False, 0)

        card.pack_end(btn_box, False, False, 0)

        pkg = app["package"]
        pkg_name = pkg.get(self.mgr, app["binary"]) if isinstance(pkg, dict) else pkg

        buttons = {
            "main": btn_main,
            "update": btn_update,
            "remove": btn_remove
        }

        self.update_ui_state(buttons, app, pkg_name)
        return card

    def update_ui_state(self, buttons, app, pkg_name):
        btn_main = buttons["main"]
        btn_update = buttons["update"]
        btn_remove = buttons["remove"]

        for b in (btn_main, btn_update, btn_remove):
            b.get_style_context().remove_class("btn-busy")
            try: b.disconnect_by_func(self.on_start_clicked)
            except Exception: pass
            try: b.disconnect_by_func(self.on_install_clicked)
            except Exception: pass
            try: b.disconnect_by_func(self.on_update_clicked)
            except Exception: pass
            try: b.disconnect_by_func(self.on_remove_clicked)
            except Exception: pass

        ctx_main = btn_main.get_style_context()
        ctx_main.remove_class("btn-start")
        ctx_main.remove_class("btn-download")

        btn_update.set_label("Update")
        btn_remove.set_label("Remove")

        installed = SystemManager.is_installed(app["binary"], pkg_name)

        if installed:
            btn_main.set_label("▶ Start")
            ctx_main.add_class("btn-start")
            btn_main.set_sensitive(True)
            btn_main.connect("clicked", self.on_start_clicked, app["binary"])

            btn_update.set_sensitive(True)
            btn_update.connect("clicked", self.on_update_clicked, buttons, app, pkg_name)

            btn_remove.set_sensitive(True)
            btn_remove.connect("clicked", self.on_remove_clicked, buttons, app, pkg_name)
        else:
            btn_main.set_label("⬇ Download")
            ctx_main.add_class("btn-download")
            btn_main.set_sensitive(True)
            btn_main.connect("clicked", self.on_install_clicked, buttons, app, pkg_name)

            btn_update.set_sensitive(False)
            btn_remove.set_sensitive(False)

    def on_start_clicked(self, btn, binary_name):
        try:
            subprocess.Popen([binary_name])
        except Exception as e:
            dialog = Gtk.MessageDialog(
                parent=self,
                modal=True,
                destroy_with_parent=True,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text=f"Błąd uruchamiania:\n{e}"
            )
            dialog.run()
            dialog.destroy()

    def set_buttons_busy(self, buttons, active_btn, status_text):
        for b in buttons.values():
            b.set_sensitive(False)
        active_btn.set_label(status_text)
        active_btn.get_style_context().add_class("btn-busy")

    def run_package_command(self, cmd, buttons, app, pkg_name, success_msg, err_title):
        def worker():
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            success = (res.returncode == 0)

            def update_ui():
                self.update_ui_state(buttons, app, pkg_name)
                msg_type = Gtk.MessageType.INFO if success else Gtk.MessageType.ERROR
                msg_txt = success_msg if success else f"{err_title}:\n{res.stderr[:200]}"
                dialog = Gtk.MessageDialog(
                    parent=self,
                    modal=True,
                    destroy_with_parent=True,
                    message_type=msg_type,
                    buttons=Gtk.ButtonsType.OK,
                    text=msg_txt
                )
                dialog.run()
                dialog.destroy()

            GLib.idle_add(update_ui)

        threading.Thread(target=worker, daemon=True).start()

    def on_install_clicked(self, btn, buttons, app, pkg_name):
        if not self.mgr:
            return
        self.set_buttons_busy(buttons, btn, "Downloading...")

        ask_pass = "pkexec" if shutil.which("pkexec") else "sudo"
        if self.mgr == "yay":
            cmd = ["yay", "-S", "--noconfirm", pkg_name]
        elif self.mgr == "pacman":
            cmd = [ask_pass, "pacman", "-S", "--noconfirm", pkg_name]
        elif self.mgr == "apt":
            cmd = [ask_pass, "apt-get", "install", "-y", pkg_name]

        self.run_package_command(cmd, buttons, app, pkg_name,
                                 f"Download of {app['name']} finished!", "Download error")

    def on_update_clicked(self, btn, buttons, app, pkg_name):
        if not self.mgr:
            return
        self.set_buttons_busy(buttons, btn, "Updating...")

        ask_pass = "pkexec" if shutil.which("pkexec") else "sudo"
        if self.mgr == "yay":
            cmd = ["yay", "-S", "--noconfirm", pkg_name]
        elif self.mgr == "pacman":
            cmd = [ask_pass, "pacman", "-S", "--noconfirm", pkg_name]
        elif self.mgr == "apt":
            cmd = [ask_pass, "apt-get", "install", "--only-upgrade", "-y", pkg_name]

        self.run_package_command(cmd, buttons, app, pkg_name,
                                 f"Updated {app['name']}!", "Update Error")

    def on_remove_clicked(self, btn, buttons, app, pkg_name):
        if not self.mgr:
            return
        self.set_buttons_busy(buttons, btn, "Deleting...")

        ask_pass = "pkexec" if shutil.which("pkexec") else "sudo"
        if self.mgr in ["yay", "pacman"]:
            cmd = [ask_pass, "pacman", "-Rns", "--noconfirm", pkg_name]
        elif self.mgr == "apt":
            cmd = [ask_pass, "apt-get", "purge", "--autoremove", "-y", pkg_name]

        self.run_package_command(cmd, buttons, app, pkg_name,
                                 f"Deleted {app['name']}.", "Deletion Error")


if __name__ == "__main__":
    win = TermosLauncher()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
