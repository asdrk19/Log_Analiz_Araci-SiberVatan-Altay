import json
import time
import os
import csv
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Button, Log, Label, Static
from textual.containers import Container, Horizontal
from textual.worker import Worker
from rich.markup import escape  # <-- BU EKLENDİ (Hatayı önleyen kilit komut)
from textual.widgets import Header, Footer, Button, RichLog, Label, Static # Log yerine RichLog geldi

# Ayar dosyasını okuma
def ayarlari_yukle():
    try:
        if os.path.exists("settings.json"):
            with open("settings.json", "r", encoding="utf-8") as f:
                return json.load(f)
    except:
        pass
    #Eğer bir hata çıkarsa default olan keyword ve log dosyalarının yolunu veriyoruz..    
    return {
        "log_files": ["/var/log/auth.log", "/var/log/syslog"], 
        "keywords": ["failed", "error", "password", "root", "sudo"]
    }

class LogAnalizUygulamasi(App):
    ENABLE_COMMAND_PALETTE = False


    CSS = """
    /* genel ekran */
    Screen {
        background: #0a0a0a;
        color: #ffffff;
    }

    /* header bölümü */
    #header_area {
        height: 3;
        background: #111111;
        border-bottom: heavy #E30A17; 
        layout: horizontal;
        padding: 0 1;
        margin-top: 2;
        text-style:bold;
    }

    /* 3 başlık yapısı */
    #baslik_sol {
        width: 1fr;
        content-align: left middle;
    }
    
    #baslik_orta {
        width: 2fr;
        content-align: center middle;
        text-style: bold;
        color: #888888;
    }

    #baslik_sag {
        width: 1fr;
        content-align: right middle;
    }

    /* ana gövde yapısı */
    #main_layout {
        layout: horizontal;
        height: 1fr;
    }

    /* ana gövde-sol */
    #sidebar {
        width: 32;
        background: #111111;
        border-right: heavy #E30A17;
        padding: 1 2;
    }

    .menu-baslik {
        width:100%;                 
        content-align:center middle; 
        text-align:center;           
        color:#ffffff;
        text-style:bold;
        margin-bottom:2;
        background:#E30A17; 
        padding:1;
    }

    /* butonlar */
    Button {
        width: 100%;
        height: 5;
        content-align: center middle; 
        
        margin-bottom: 1;
        background: #222222;
        color: #ffffff;
        border: wide #444444;
        text-style: bold;
    }
    
    /*butonlara efekt*/
    Button:hover {
        background: #E30A17;   
        border: wide #E30A17;
        color: #ffffff;
    }
    
    #btn_cikis {
        background: #330000;
        border: wide #ff0000;
        color: #ffcccc;
    }
    #btn_cikis:hover { background: #ff0000; color: white; }

    /* log veri ekranı */
   RichLog {  /* #log_ekrani yerine direkt RichLog bileşenini hedefledik */
        background: #000000;
        color: #00ff00; 
        border: heavy #E30A17;
        scrollbar-background: #111111;
        scrollbar-color: #E30A17;
        margin: 1;
    }
   /*canlı izlemeyi durdurma butonu*/
    .kirmizi-buton {
        background: #cc0000 !important;
        color: white;
        border: wide #ffaaaa;
        text-style: bold;
        
        /* İŞTE ORTALAMAYI SAĞLAYAN SATIR: */
        content-align: center middle; 
    }
    """

    def compose(self) -> ComposeResult:
        
        with Container(id="header_area"):
            yield Label("[bold white]SİBER[/][bold red]VATAN[/]", id="baslik_sol")
            yield Label("LOG ANALİZ SİSTEMİ", id="baslik_orta")
            yield Label(" [bold white]ALTAY[/] [bold white]TAKIMI[/]", id="baslik_sag")

        # ana gövde yapısı
        with Container(id="main_layout"):
            # sol taraf:
            with Container(id="sidebar"):
                yield Label("KONTROL PANELİ", classes="menu-baslik")
                yield Button("Dosyaları Tara", id="btn_tara")
                yield Button("Canlı İzleme Modu", id="btn_canli")
                yield Button("CSV Raporla", id="btn_csv")
                yield Static("\n") 
                yield Button("Çıkış Yap", id="btn_cikis")
            #sag taraf:
            yield RichLog(id="log_ekrani", markup=True, highlight=True)
        
        yield Footer()

    def on_mount(self):
        self.ayarlar = ayarlari_yukle()
        self.kayitlar = []
        self.canli_mod_aktif = False

    def on_button_pressed(self, event: Button.Pressed):
        log = self.query_one("#log_ekrani", RichLog)
        
        if event.button.id == "btn_cikis":
            self.exit()
            
        elif event.button.id == "btn_tara":
            log.clear()
            log.write("[bold cyan]Dosya okuma yapılıp tarama başlatılıyor...[/]")
            
            dosyalar = self.ayarlar.get("log_files", [])
            kelimeler = self.ayarlar.get("keywords", [])
            bulundu = 0
            
            for dosya in dosyalar:
                if os.path.exists(dosya):
                    try:
                        with open(dosya, "r", encoding="utf-8", errors="ignore") as f:
                            for i, satir in enumerate(f, 1):
                                for k in kelimeler:
                                    if k in satir:
                                        d_temiz = escape(dosya)
                                        s_temiz = escape(satir.strip())
                                        
                                        log.write(f"[bold red]TESPİT[/] ({d_temiz}:{i}) [white]{s_temiz}[/]")
                                        self.kayitlar.append([time.ctime(), dosya, k, satir.strip()])
                                        bulundu += 1
                    except Exception as e:
                        log.write(f"[bold red]Hata: {escape(str(e))}[/]")
                else:
                    log.write(f"[bold red]Dosya bulunamadı: {escape(dosya)}[/]")
            
            log.write(f"\n[bold green]Tarama tamamlandı. Toplam {bulundu} tehdit bulundu.[/]")
        

        elif event.button.id == "btn_canli":
            btn = self.query_one("#btn_canli", Button)
            
            if not self.canli_mod_aktif:
                # --- BAŞLATMA MODU ---
                log.write("[bold yellow]Canlı izleme modu başlatıldı. Loglar bekleniyor...[/]")
                self.canli_mod_aktif = True
                
                btn.label = "\nCanlı İzlemeyi Durdur"
                btn.add_class("kirmizi-buton")
                
                self.run_worker(self.canli_izleme_worker, exclusive=True, thread=True)
            else:
                self.canli_mod_aktif = False
                log.write("[bold red] Canlı izleme modu durduruldu.[/]")
                
                btn.label = "Canlı İzleme Modu"
                btn.remove_class("kirmizi-buton")

        elif event.button.id == "btn_csv":
            if self.kayitlar:
                try:
                    with open("rapor.csv", "w", newline="", encoding="utf-8") as f:
                        w = csv.writer(f)
                        w.writerow(["Zaman", "Dosya", "Kural", "Icerik"])
                        w.writerows(self.kayitlar)
                    log.write("[bold green]Rapor 'rapor.csv' olarak başarıyla kaydedildi.[/]")
                except Exception as e:
                    log.write(f"[bold red]CSV Hatası: {escape(str(e))}[/]")
            else:
                log.write("[bold red]Kaydedilecek veri yok. Önce tarama yapın.[/]")
    def canli_izleme_worker(self):
        
        log_widget = self.query_one("#log_ekrani", RichLog)
        dosyalar = self.ayarlar.get("log_files", [])
        kelimeler = self.ayarlar.get("keywords", [])
        
        acik_dosyalar = []
        for yol in dosyalar:
            if os.path.exists(yol):
                try:
                    f = open(yol, "r", encoding="utf-8", errors="ignore")
                    f.seek(0, 2)
                    acik_dosyalar.append(f)
                except:
                    pass
        
        while self.canli_mod_aktif:
            veri_geldi = False
            for f in acik_dosyalar:
                line = f.readline()
                if line:
                    veri_geldi = True
                    for k in kelimeler:
                        if k in line:
                            line_temiz = escape(line.strip())
                            self.call_from_thread(log_widget.write, f"[bold on red blink] CANLI UYARI [/] [white]{line_temiz}[/]")
            
            if not veri_geldi:
                time.sleep(0.5)

if __name__ == "__main__":
    app = LogAnalizUygulamasi()
    app.run()