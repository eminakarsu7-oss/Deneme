# -*- coding: utf-8 -*-
import threading, time, random, math
from datetime import datetime
import requests
from kivy.app import App
from kivy.clock import Clock, mainthread
from kivy.metrics import dp, sp
from kivy.properties import StringProperty, NumericProperty
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.camera import Camera

# --- Android Özel Kütüphaneleri ---
try:
    from android.permissions import request_permissions, Permission
    from jnius import autoclass
    ANDROID = True
except ImportError:
    ANDROID = False

Window.clearcolor = (0.07, 0.07, 0.11, 1)
IP_API = "http://ip-api.com/json/?fields=status,country,countryCode,city,isp,timezone,query"

CLR = {
    "bg": (0.07, 0.07, 0.11, 1), "card": (0.16, 0.16, 0.22, 1),
    "accent": (0.54, 0.71, 0.98, 1), "green": (0.65, 0.89, 0.63, 1),
    "red": (0.95, 0.55, 0.66, 1), "yellow": (0.98, 0.89, 0.69, 1),
    "text": (0.80, 0.84, 0.96, 1), "dim": (0.65, 0.68, 0.78, 1),
}

class ARRadar(FloatLayout):
    rssi = NumericProperty(-100)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(rssi=self.update_radar, pos=self.update_radar, size=self.update_radar)
        
    def update_radar(self, *args):
        self.canvas.clear()
        cx, cy = self.center_x, self.center_y
        norm = max(0, min(1, (self.rssi + 90) / 60.0))
        
        if norm < 0.5:
            r, g, b = 0.95, 0.55 + (norm * 0.6), 0.66
        else:
            r, g, b = 0.95 - ((norm - 0.5) * 0.6), 0.85, 0.63
            
        radius = dp(100) - (norm * dp(70))
        
        with self.canvas:
            Color(1, 1, 1, 0.8)
            Line(points=[cx - dp(20), cy, cx + dp(20), cy], width=dp(1.5))
            Line(points=[cx, cy - dp(20), cx, cy + dp(20)], width=dp(1.5))
            
            Color(r, g, b, 0.6)
            Line(circle=(cx, cy, radius), width=dp(3))
            
            Color(r, g, b, 0.2)
            Line(circle=(cx, cy, radius + dp(20)), width=dp(1))

class WifiSinyalOkuyucu(threading.Thread):
    def __init__(self, callback):
        super().__init__(daemon=True)
        self.callback = callback
        self.running = True
        
    def run(self):
        if ANDROID:
            try:
                Context = autoclass('android.content.Context')
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                activity = PythonActivity.mActivity
                wifi_service = activity.getSystemService(Context.WIFI_SERVICE)
            except Exception:
                return

        while self.running:
            if ANDROID:
                try:
                    info = wifi_service.getConnectionInfo()
                    rssi = info.getRssi()
                    self.callback(rssi)
                except Exception:
                    self.callback(-100)
            else:
                fake_rssi = -30 - (math.sin(time.time()) * 20) - random.randint(0, 20)
                self.callback(int(fake_rssi))
            time.sleep(0.5)

class IPRotatorApp(App):
    ip_text = StringProperty("---")

    def build(self):
        self.title = "IP Rotator AR"
        
        if ANDROID:
            request_permissions([
                Permission.INTERNET, 
                Permission.ACCESS_NETWORK_STATE,
                Permission.CAMERA,
                Permission.ACCESS_FINE_LOCATION,
                Permission.ACCESS_WIFI_STATE
            ])

        root = FloatLayout()

        try:
            self.camera = Camera(play=True, resolution=(640, 480), size_hint=(1, 1))
            root.add_widget(self.camera)
        except Exception:
            root.add_widget(Label(text="Kamera Yok (Bilgisayarda normaldir)", pos_hint={'center_x':0.5, 'center_y':0.8}))

        self.radar = ARRadar(size_hint=(1, 1))
        root.add_widget(self.radar)

        top_bar = BoxLayout(orientation="vertical", size_hint=(1, None), height=dp(80), pos_hint={'top': 1})
        with top_bar.canvas.before:
            Color(0, 0, 0, 0.6)
            self._top_bg = RoundedRectangle(radius=[0])
        top_bar.bind(pos=lambda *a: setattr(self._top_bg, 'pos', top_bar.pos))
        top_bar.bind(size=lambda *a: setattr(self._top_bg, 'size', top_bar.size))

        self.ip_lbl = Label(text="IP: ---", font_size=sp(16), color=CLR["green"], bold=True)
        self.rssi_lbl = Label(text="Sinyal: Bekleniyor...", font_size=sp(14), color=CLR["yellow"])
        top_bar.add_widget(self.ip_lbl)
        top_bar.add_widget(self.rssi_lbl)
        root.add_widget(top_bar)

        bottom_panel = BoxLayout(orientation="vertical", size_hint=(1, None), height=dp(100), pos_hint={'y': 0}, padding=dp(10), spacing=dp(8))
        with bottom_panel.canvas.before:
            Color(0, 0, 0, 0.7)
            self._bot_bg = RoundedRectangle(radius=[0])
        bottom_panel.bind(pos=lambda *a: setattr(self._bot_bg, 'pos', bottom_panel.pos))
        bottom_panel.bind(size=lambda *a: setattr(self._bot_bg, 'size', bottom_panel.size))

        btn_layout = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        self.btn_ip = Button(text="IP Yenile", background_color=CLR["accent"], background_normal="", bold=True)
        self.btn_ip.bind(on_press=self.refresh_ip)
        
        self.btn_scan = Button(text="Radarı Başlat", background_color=CLR["green"], background_normal="", bold=True)
        self.btn_scan.bind(on_press=self.toggle_scan)

        btn_layout.add_widget(self.btn_ip)
        btn_layout.add_widget(self.btn_scan)
        bottom_panel.add_widget(btn_layout)
        root.add_widget(bottom_panel)

        Clock.schedule_once(lambda dt: self.refresh_ip(), 0.5)
        return root

    def toggle_scan(self, *args):
        if not hasattr(self, 'scanner'):
            self.scanner = WifiSinyalOkuyucu(self.update_rssi)
            self.scanner.start()
            self.btn_scan.text = "Radar Aktif"
            self.btn_scan.background_color = CLR["red"]
        else:
            self.scanner.running = False
            del self.scanner
            self.btn_scan.text = "Radarı Başlat"
            self.btn_scan.background_color = CLR["green"]
            self.radar.rssi = -100
            self.rssi_lbl.text = "Sinyal: Kapalı"

    @mainthread
    def update_rssi(self, rssi):
        self.radar.rssi = rssi
        self.rssi_lbl.text = f"Sinyal Gücü: {rssi} dBm"
        if rssi > -60:
            self.rssi_lbl.color = CLR["green"]
        elif rssi > -80:
            self.rssi_lbl.color = CLR["yellow"]
        else:
            self.rssi_lbl.color = CLR["red"]

    def refresh_ip(self, *args):
        threading.Thread(target=self._fetch_ip_worker, daemon=True).start()

    def _fetch_ip_worker(self):
        try:
            r = requests.get(IP_API, timeout=8)
            d = r.json()
            if d.get("status") == "success":
                self.ip_lbl.text = f"IP: {d.get('query')} | {d.get('country')}"
        except Exception:
            self.ip_lbl.text = "IP: Alınamadı"

if __name__ == "__main__":
    IPRotatorApp().run()