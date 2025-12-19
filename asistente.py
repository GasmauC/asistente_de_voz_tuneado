import customtkinter as ctk
import threading
import speech_recognition as sr
import pyttsx3
import pywhatkit
import pyjokes
import webbrowser
import datetime
import wikipedia
import pythoncom 

# --- CONFIGURACIÓN VISUAL ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class UranoApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Ventana
        self.title("URANO - A.I. Assistant")
        self.geometry("500x600")
        self.resizable(False, False)

        # Estado
        self.escuchando = False
        
        # Interfaz
        self.header_frame = ctk.CTkFrame(self, height=50, corner_radius=0, fg_color="#101010")
        self.header_frame.pack(fill="x", side="top")
        
        self.label_titulo = ctk.CTkLabel(self.header_frame, text="URANO A.I.", font=("Roboto Medium", 20), text_color="#00E5FF")
        self.label_titulo.pack(pady=10)

        self.chat_box = ctk.CTkTextbox(self, width=460, height=350, corner_radius=15, font=("Consolas", 14))
        self.chat_box.pack(pady=20)
        self.chat_box.insert("0.0", "Iniciando sistemas...\nEsperando activación.\n")
        self.chat_box.configure(state="disabled")

        self.estado_label = ctk.CTkLabel(self, text="EN ESPERA", font=("Roboto", 16), text_color="gray")
        self.estado_label.pack(pady=(0, 5))

        self.boton_micro = ctk.CTkButton(self, text="ACTIVAR SISTEMA", command=self.iniciar_hilo_escucha, width=200, height=50, corner_radius=25, fg_color="#1f6aa5", font=("Roboto Bold", 14))
        self.boton_micro.pack(pady=10)

        self.boton_salir = ctk.CTkButton(self, text="Cerrar Sistema", command=self.cerrar_app, fg_color="#444", width=100)
        self.boton_salir.pack(pady=10)

    # --- LÓGICA DEL ASISTENTE ---

    def escribir_en_chat(self, texto, tipo="bot"):
        self.chat_box.configure(state="normal")
        if tipo == "user":
            self.chat_box.insert("end", f"\n👤 TÚ: {texto}\n")
        elif tipo == "error":
            self.chat_box.insert("end", f"\n❌ INFO: {texto}\n")
        else:
            self.chat_box.insert("end", f"\n🤖 URANO: {texto}\n")
        self.chat_box.see("end")
        self.chat_box.configure(state="disabled")

    # --- FUNCIÓN CONFIGURAR VOZ ---
    def configurar_voz_latina(self, engine):
        voces = engine.getProperty('voices')
        voz_encontrada = False
        
        for voz in voces:
            if "Mexico" in voz.name or "SABINA" in voz.id:
                engine.setProperty('voice', voz.id)
                voz_encontrada = True
                break
        
        if not voz_encontrada:
            for voz in voces:
                if "Spanish" in voz.name:
                    engine.setProperty('voice', voz.id)
                    break
                    
        engine.setProperty('rate', 150)

    def hablar(self, mensaje):
        self.escribir_en_chat(mensaje, "bot")
        try:
            engine = pyttsx3.init()
            self.configurar_voz_latina(engine)
            engine.say(mensaje)
            engine.runAndWait()
        except Exception as e:
            print(f"Error crítico de audio: {e}")

    def transformar_audio_en_texto(self):
        r = sr.Recognizer()
        r.energy_threshold = 400 
        r.dynamic_energy_threshold = False 
        r.pause_threshold = 0.8

        try:
            with sr.Microphone() as origen:
                self.estado_label.configure(text="ESCUCHANDO...", text_color="#00E5FF")
                r.adjust_for_ambient_noise(origen, duration=0.2)
                
                print(">>> Escuchando ahora...")
                audio = r.listen(origen, timeout=5, phrase_time_limit=5)
                
                self.estado_label.configure(text="PROCESANDO...", text_color="#FFA500")
                
                pedido = r.recognize_google(audio, language="es-AR")
                print(f">>> Detectado: {pedido}")
                return pedido.lower()

        except sr.WaitTimeoutError:
            return "silencio"
        except sr.UnknownValueError:
            return "ruido"
        except Exception as e:
            print(f"Error micro: {e}")
            return "error"
        finally:
             if self.escuchando:
                self.estado_label.configure(text="EN ESPERA", text_color="gray")

    def ejecutar_asistente(self):
        pythoncom.CoInitialize() 
        
        self.hablar("Hola Gastón, ¿Cómo estás? Soy Urano, tu asistente inteligente. ¿En qué te ayudo?")
        
        while self.escuchando:
            pedido = self.transformar_audio_en_texto()

            if pedido == "silencio":
                continue
            elif pedido == "ruido":
                self.escribir_en_chat("No entendí...", "error")
                continue
            elif pedido == "error":
                self.escribir_en_chat("Error de micrófono", "error")
                continue

            self.escribir_en_chat(pedido, "user")

            # --- COMANDOS ---

            # 1. YOUTUBE
            if 'youtube' in pedido:
                palabras_relleno = ['buscar', 'busca', 'pon', 'puedes', 'podrías', 'quiero', 'ver', 'abrir', 'reproducir', 'el', 'un', 'video', 'de', 'en', 'youtube', 'por favor']
                consulta = pedido
                for palabra in palabras_relleno:
                    consulta = consulta.replace(palabra, "")
                consulta = consulta.strip()

                if consulta != "":
                    if 'reproducir' in pedido or 'pon' in pedido:
                        self.hablar(f'Reproduciendo {consulta}')
                        pywhatkit.playonyt(consulta)
                    else:
                        self.hablar(f'Buscando videos de {consulta}')
                        webbrowser.open(f"https://www.youtube.com/results?search_query={consulta}")
                else:
                    self.hablar('Abriendo YouTube')
                    webbrowser.open('https://www.youtube.com')

            # 2. GOOGLE / NAVEGADOR (¡MEJORADO!)
            elif 'google' in pedido or 'internet' in pedido or 'busca' in pedido:
                # Palabras que quitamos para dejar limpia la búsqueda
                palabras_relleno = ['busca', 'buscar', 'búscame', 'en', 'google', 'internet', 'navegador', 'quiero', 'saber', 'dime', 'decime', 'por favor', 'el']
                
                consulta = pedido
                for palabra in palabras_relleno:
                    # Reemplazamos por vacío
                    consulta = consulta.replace(palabra, "")
                
                consulta = consulta.strip()

                # Si quedó algo (ej: "clima cordoba 10 dias") buscamos eso
                if consulta != "":
                    self.hablar(f'Buscando {consulta} en Google')
                    # Abrimos la URL de búsqueda directa
                    webbrowser.open(f"https://www.google.com/search?q={consulta}")
                
                # Si no quedó nada (solo dijiste "abrir google"), abrimos la home
                else:
                    self.hablar('Abriendo la página principal de Google')
                    webbrowser.open('https://www.google.com')

            elif 'hora' in pedido:
                hora = datetime.datetime.now()
                self.hablar(f'Son las {hora.hour} y {hora.minute}.')

            elif 'día' in pedido:
                dia = datetime.date.today()
                dias = {0:'Lunes',1:'Martes',2:'Miércoles',3:'Jueves',4:'Viernes',5:'Sábado',6:'Domingo'}
                self.hablar(f'Hoy es {dias[dia.weekday()]}')

            elif 'wikipedia' in pedido:
                self.hablar('Buscando información...')
                consulta = pedido.replace('busca en wikipedia', '').replace('wikipedia', '').replace('buscar', '').strip()
                wikipedia.set_lang('es')
                try:
                    res = wikipedia.summary(consulta, sentences=1)
                    self.hablar(res)
                except:
                    self.hablar("No encontré eso en Wikipedia.")

            elif 'cerrar' in pedido or  'apagar' in pedido:
                self.hablar("Hasta luego, Gastón.")
                self.escuchando = False
                self.boton_micro.configure(state="normal", text="ACTIVAR SISTEMA", fg_color="#1f6aa5")
                break
            
            else:
                self.hablar("Escuché eso, pero no sé qué hacer.")

    def iniciar_hilo_escucha(self):
        if not self.escuchando:
            self.escuchando = True
            self.boton_micro.configure(state="disabled", text="SISTEMA ACTIVO", fg_color="#2b8256")
            hilo = threading.Thread(target=self.ejecutar_asistente)
            hilo.daemon = True
            hilo.start()

    def cerrar_app(self):
        self.escuchando = False
        self.destroy()

if __name__ == "__main__":
    app = UranoApp()
    app.mainloop()