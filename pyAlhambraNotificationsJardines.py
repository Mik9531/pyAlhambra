import threading
import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import calendar
from PyInstaller.building import icon
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import winsound
from selenium.webdriver.chrome.options import Options
from pystray import Icon, MenuItem, Menu
from PIL import Image, ImageDraw
import random  # Asegúrate de tener esto arriba del todo
import pickle
import os
from threading import Event
import tempfile
import shutil  # para limpiar perfiles temporales antiguos
import undetected_chromedriver as uc
import atexit
import pyttsx3
import pygetwindow as gw
import time
import smtplib
from email.mime.text import MIMEText
import requests

parpadeo_evento = Event()

FALLOS_SEGUIDOS = 0
MAX_FALLOS = 2
ESTADO_FILE = "dias_tachados_inicial_jardines.pkl"

import time
import win32gui
import win32con

import logging

import os
import winreg

def obtener_ruta_chrome():
    try:
        # Intentar acceder a la clave del registro que contiene la ruta de Chrome
        ruta_chrome = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        return ruta_chrome
    except FileNotFoundError:
        print("La clave del registro no existe. Chrome puede no estar instalado o tener una ruta diferente.")
        return None
    except Exception as e:
        print(f"Error al acceder al registro: {e}")
        return None



# Configurar el logging
logging.basicConfig(
    filename="jardines.log",  # Nombre del archivo donde se guardará el log
    level=logging.INFO,  # Nivel mínimo de mensajes a registrar (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format="%(asctime)s - %(levelname)s - %(message)s",  # Formato del mensaje de log
    datefmt="%Y-%m-%d %H:%M:%S"  # Formato de fecha
)


def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot7908020608:AAEGRux_wQ8tlKxPoMEGLR5vMtG1X3LW2WY/sendMessage"
    datos = {"chat_id": str(780778418), "text": mensaje}  # Miguel
    # datos = {"chat_id": str(8120620954), "text": mensaje}  # Belén

    try:
        respuesta = requests.post(url, data=datos)
        if respuesta.status_code == 200:
            print("Mensaje enviado por Telegram.")
        else:
            print("Error al enviar mensaje:", respuesta.text)
    except Exception as e:
        print("Error en la conexión:", e)


def enviar_correo(mensaje):
    remitente = "miguelafannn@gmail.com"
    destinatario = "miguelafannn@gmail.com"
    asunto = "Días liberados detectados"

    msg = MIMEText(mensaje)
    msg["Subject"] = asunto
    msg["From"] = remitente
    msg["To"] = destinatario

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(remitente, "iybz zvli cxic xsts")  # Usa una App Password de Gmail
            server.sendmail(remitente, destinatario, msg.as_string())
        print("Correo enviado exitosamente.")
    except Exception as e:
        print("Error al enviar correo:", e)


def minimizar_ventana(driver):
    time.sleep(2)  # Espera a que la ventana de Chrome abra
    window_handle = driver.current_window_handle  # Obtiene el handle de la ventana de Selenium
    hwnd = win32gui.GetForegroundWindow()  # Obtiene la ventana en primer plano

    if hwnd:
        win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)  # Minimiza solo esa ventana


def borrar_archivo_estado():
    if os.path.exists(ESTADO_FILE):
        try:
            os.remove(ESTADO_FILE)
            print(f"Archivo temporal '{ESTADO_FILE}' eliminado.")
        except Exception as e:
            print(f"Error al eliminar el archivo '{ESTADO_FILE}': {e}")


atexit.register(borrar_archivo_estado)


def crear_icono_verde():
    """Crea un icono verde para la bandeja del sistema."""
    width, height = 64, 64
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))  # Fondo transparente
    draw = ImageDraw.Draw(image)
    draw.ellipse((0, 0, width, height), fill="green")  # Círculo rojo
    return image


def crear_icono_amarillo():
    """Crea un icono circular con fondo transparente para la bandeja del sistema."""
    width, height = 64, 64
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))  # Fondo transparente
    draw = ImageDraw.Draw(image)
    draw.ellipse((0, 0, width, height), fill="yellow")  # Círculo rojo
    return image


def crear_icono_rojo():
    """Crea un icono rojo para la bandeja del sistema."""
    """Crea un icono circular con fondo transparente para la bandeja del sistema."""
    width, height = 64, 64
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))  # Fondo transparente
    draw = ImageDraw.Draw(image)
    draw.ellipse((0, 0, width, height), fill="red")  # Círculo rojo
    return image


def crear_icono_alerta():
    """Crea un icono rojo para alertas."""
    width, height = 64, 64
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    draw.ellipse((0, 0, width, height), fill="red")
    return image


def parpadear_icono(icono, repeticiones=6, intervalo=0.5):
    """Hace parpadear el icono de la bandeja alternando entre normal y alerta hasta que el usuario interactúe o se detenga."""
    icono_normal = crear_icono_verde()
    icono_alerta = crear_icono_amarillo()

    def _parpadear():
        while parpadeo_evento.is_set():  # Mientras el evento esté activado
            icono.icon = icono_alerta
            time.sleep(intervalo)
            icono.icon = icono_normal
            time.sleep(intervalo)

    # Inicia el parpadeo en un hilo separado
    threading.Thread(target=_parpadear, daemon=True).start()


def guardar_dias_tachados(data):
    with open(ESTADO_FILE, "wb") as f:
        pickle.dump(data, f)


def cargar_dias_tachados():
    if os.path.exists(ESTADO_FILE):
        with open(ESTADO_FILE, "rb") as f:
            return pickle.load(f)
    return []


def obtener_dias_tachados_completos(driver):
    dias_total = []

    # 🔹 Obtener el mes actual en formato "Enero", "Febrero", etc.
    dias_total = []

    # 🔹 Obtener el mes actual en formato "Enero", "Febrero", etc.
    mes_actual_num = datetime.now().month  # Ejemplo: 3 (marzo)
    mes_actual_nombre = calendar.month_name[mes_actual_num]  # "March"

    time.sleep(2)


    # Obtener días tachados del mes actual
    dias_mes_actual = driver.find_elements(By.CSS_SELECTOR,
                                           "#ctl00_ContentMaster1_ucReservarEntradasBaseAlhambra1_ucCalendarioPaso1_calendarioFecha .calendario_padding.no-dispo")

    dias_total.extend([f"{mes_actual_nombre}-{dia.text.strip()}" for dia in dias_mes_actual if dia.text.strip()])

    logging.info(f"Días extraído del mes actual (innerText): '{dias_total}'")


    if (True):

        # 🔹 Avanzar al mes siguiente
        try:
            boton_mes_siguiente = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//td[@align='right']//a[contains(@href,'__doPostBack')]"))
            )

            driver.execute_script("arguments[0].scrollIntoView();", boton_mes_siguiente)
            time.sleep(2)
            driver.execute_script("arguments[0].click();", boton_mes_siguiente)

            # 🔹 Esperar a que los nuevos elementos se carguen después del cambio de mes
            time.sleep(7)  # Pequeña pausa para asegurar la carga de la página
            # WebDriverWait(driver, 20).until(
            #     EC.presence_of_all_elements_located((By.CSS_SELECTOR,
            #                                          "#ctl00_ContentMaster1_ucReservarEntradasBaseAlhambra1_ucCalendarioPaso1_calendarioFecha .calendario_padding.no-dispo"))
            # )
        except Exception as e:
            print(f"No se pudo avanzar al mes siguiente: {e}")
            return []

        # 🔹 Obtener el mes siguiente
        mes_siguiente_num = mes_actual_num + 1 if mes_actual_num < 12 else 1  # Si es diciembre, pasa a enero
        mes_siguiente_nombre = calendar.month_name[mes_siguiente_num]

        time.sleep(2)  # Pequeña pausa para asegurar la carga de la página


        try:
            dias_mes_siguiente = driver.find_elements(By.CSS_SELECTOR,
                                                      "#ctl00_ContentMaster1_ucReservarEntradasBaseAlhambra1_ucCalendarioPaso1_calendarioFecha .calendario_padding.no-dispo")

            time.sleep(3)  # Pequeña pausa para asegurar la carga de la página

            for dia in dias_mes_siguiente:
                texto_dia = dia.get_attribute("innerText").strip()
                logging.info(f"Día extraído del mes siguiente (innerText): '{texto_dia}'")
                if texto_dia.isdigit():
                    dias_total.append(f"{mes_siguiente_nombre}-{texto_dia}")
        except Exception as e:
            print(f"No se pudo obtener fechas del mes siguiente: {e}")
            return []

    return dias_total


# Configuración inicial
TIEMPO_REFRESCO = 10  # Tiempo entre revisiones en segundos
TIEMPO = random.uniform(5, 7)  # Tiempo de espera tras cada paso
DETENER = False  # Variable global para detener el script
SCRIPT_THREAD = None  # Hilo de ejecución del script


def crear_icono():
    borrar_archivo_estado()
    """Crea un icono circular con fondo transparente para la bandeja del sistema."""
    width, height = 64, 64
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))  # Fondo transparente
    draw = ImageDraw.Draw(image)
    draw.ellipse((0, 0, width, height), fill="red")  # Círculo rojo
    return image


def alerta_sonora_reinicio():
    """Genera una alerta hablada con voz sintética."""
    engine = pyttsx3.init()
    engine.say("Reiniciando navegador")
    engine.runAndWait()


def alerta_sonora_error():
    """Genera una alerta hablada con voz sintética."""
    engine = pyttsx3.init()
    engine.say("Botón bloqueado, reintentando")
    engine.runAndWait()


def alerta_sonora_acierto():
    """Genera una alerta hablada con voz sintética."""
    engine = pyttsx3.init()
    engine.say("Días liberados para reservar en Jardines")
    engine.runAndWait()


def notificar_popup(mensaje):
    """Muestra un pop-up con un mensaje y detiene el parpadeo al hacer clic en el botón."""
    root = tk.Tk()
    root.withdraw()  # Oculta la ventana principal
    if messagebox.showinfo("Notificación", mensaje) == 'ok':
        parpadeo_evento.clear()  # Detiene el parpadeo al interactuar con el popup


def esperar_boton_activo(driver, by, value, timeout=15):
    """Espera hasta que el botón esté visible, habilitado y clickeable."""
    end_time = time.time() + timeout
    while time.time() < end_time:
        try:
            boton = driver.find_element(by, value)
            if boton.is_displayed() and boton.is_enabled():
                return boton
        except Exception:
            pass
        time.sleep(0.5)
    raise Exception(f"Botón {value} no se activó dentro del tiempo esperado.")


def ejecutar_script(icon):
    global DETENER, FALLOS_SEGUIDOS

    def iniciar_navegador():

        random_port = random.randint(9300, 9400)

        ruta_perfil_chrome = os.path.join(os.getenv("LOCALAPPDATA"), "Google", "Chrome", "User Data", "Perfil2")

        options = uc.ChromeOptions()

        # Otros flags útiles
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--no-first-run --no-service-autorun --password-store=basic")
        #
        # options.add_argument("--incognito")
        options.add_argument("--start-maximized")
        # options.add_argument("--window-size=1280,800")
        options.add_argument("--disable-blink-features=AutomationControlled")
        # options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-software-rasterizer")
        # options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-extensions")
        # # options.add_argument("Accept-Language: en-US,en;q=0.9")
        # # options.add_argument("Accept-Encoding: gzip, deflate, br")
        # # options.add_argument("Connection: keep-alive")
        # options.add_argument("--remote-debugging-port=9222")
        options.add_argument("--disable-popup-blocking")
        # options.add_argument("--start-minimized")
        options.add_argument(f"--remote-debugging-port={random_port}")
        # options.add_argument("--headless=new")

        # options.add_argument(
        #     "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

        # options.add_argument(r"--user-data-dir=C:\Users\migue\AppData\Local\Google\Chrome\UserData2")

        # options.debugger_address = "127.0.0.1:9223"

        options.add_argument(f"--user-data-dir={ruta_perfil_chrome}")  # <-- Asegurar que está bien escrito

        driver = uc.Chrome(options=options)

        return driver

    def navegar_y_preparar(driver):
        URL_INICIAL = 'https://tickets.alhambra-patronato.es/'
        URL_RESERVAS_JARDINES = 'https://compratickets.alhambra-patronato.es/reservarEntradas.aspx?opc=143&gid=432&lg=es&ca=0&m=GENERAL'

        driver.get(URL_RESERVAS_JARDINES)
        driver.delete_all_cookies()
        driver.execute_script("window.localStorage.clear();")
        driver.execute_script("window.sessionStorage.clear();")
        # time.sleep(TIEMPO)


        # try:
        #     WebDriverWait(driver, 5).until(
        #         EC.element_to_be_clickable((By.CSS_SELECTOR, ".mgbutton.moove-gdpr-infobar-allow-all.gdpr-fbo-0"))
        #     ).click()
        #     print("Botón 'ACEPTAR TODO' pulsado.")
        #     time.sleep(TIEMPO)
        # except Exception:
        #     print("Botón 'ACEPTAR TODO' no encontrado o ya aceptado.")
        # #
        # enlace = driver.find_element(By.XPATH,
        #                              "//a[@href='https://tickets.alhambra-patronato.es/producto/jardines-generalife-y-alcazaba/']")
        # enlace.click()
        # time.sleep(TIEMPO)
        #
        # try:
        #     WebDriverWait(driver, 5).until(
        #         EC.element_to_be_clickable((By.XPATH, f"//a[@href='{URL_RESERVAS_JARDINES}']"))
        #     ).click()
        #     print("Botón 'Reservas' pulsado.")
        #     time.sleep(TIEMPO)
        # except Exception:
        #     print("Fallo al acceder a las reservas")

        # time.sleep(TIEMPO)

        try:
            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "ctl00_lnkAceptarTodoCookies_Info"))
            ).click()
            print("Botón 'Aceptar cookies' pulsado.")
            time.sleep(TIEMPO)
        except Exception:
            print("Botón de cookies no encontrado o ya aceptado.")

        # WebDriverWait(driver, 5).until(
        #     EC.element_to_be_clickable((By.ID, "ctl00_ContentMaster1_ucReservarEntradasBaseAlhambra1_btnIrPaso1"))
        # ).click()
        # print("Botón 'Paso 1' pulsado.")

        # time.sleep(TIEMPO)

    driver = iniciar_navegador()
    # minimizar_chrome(driver)  # Ocultar Chrome después de abrirlo

    navegar_y_preparar(driver)

    dias_tachados_inicial = cargar_dias_tachados()

    # Si no hay días tachados guardados, intentar obtenerlos de la web hasta que haya al menos uno
    if not dias_tachados_inicial:
        intentos = 0
        while True:
            try:
                # Comprobar si aparece el mensaje de muchas peticiones
                mensaje_error = driver.find_elements(By.CSS_SELECTOR, "h3.es")
                for elem in mensaje_error:
                    if "Estamos recibiendo muchas peticiones" in elem.text:
                        messagebox.showerror("Página no disponible",
                                             "La web está recibiendo muchas peticiones. Intenta más tarde.")
                        return []  # o None, según lo que manejes como fallo

            except Exception as e:
                print(f"Error obteniendo días tachados: {e}")
                return []


            try:
                WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable(
                        (By.ID, "ctl00_ContentMaster1_ucReservarEntradasBaseAlhambra1_btnIrPaso1"))
                ).click()
                time.sleep(TIEMPO)
            except Exception:
                print("Botón de paso 1 ya pulsado.")

            # time.sleep(TIEMPO)

            dias_tachados_inicial = obtener_dias_tachados_completos(driver)
            if dias_tachados_inicial:
                break
            # alerta_sonora_error()
            intentos += 1
            print(f"Intento {intentos}: No se encontraron días tachados. Recargando la página...")
            driver.refresh()
            time.sleep(random.uniform(5, 7))  # Pausa para simular comportamiento humano o evitar bloqueos

        guardar_dias_tachados(dias_tachados_inicial)

    print(f"Días tachados inicialmente: {dias_tachados_inicial}")
    logging.info(f"Días tachados inicialmente: {dias_tachados_inicial}")

    counter = 1
    counter_diasTachados = 1


    try:
        while not DETENER:
            icon.icon = crear_icono_verde()

            print(f"\n Intento #{counter}")
            logging.info(f"\n Intento #{counter}")

            counter += 1
            driver.refresh()
            # time.sleep(TIEMPO)

            try:
                WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.ID, "ctl00_lnkAceptarTodoCookies_Info"))
                ).click()
                print("Botón 'Aceptar cookies' pulsado.")
                time.sleep(TIEMPO)
            except Exception:
                print("Botón de cookies no encontrado o ya aceptado.")

            try:
                boton = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable(
                        (By.ID, "ctl00_ContentMaster1_ucReservarEntradasBaseAlhambra1_btnIrPaso1"))
                )
                driver.execute_script("arguments[0].click();", boton)
                print("Botón 'Paso 1' pulsado.")
                time.sleep(TIEMPO)

                # Verificamos que el calendario ha cargado
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID,
                                                    "ctl00_ContentMaster1_ucReservarEntradasBaseAlhambra1_ucCalendarioPaso1_calendarioFecha"))
                )

                FALLOS_SEGUIDOS = 0  # reiniciar contador
            except Exception as e:
                print(f" Fallo al ir a Paso 1: {e}")
                logging.info(f" Fallo al ir a Paso 1: {e}")

                # alerta_sonora_error()
                # notificar_popup("¡Error al ir al paso 1!")
                FALLOS_SEGUIDOS += 1

                if FALLOS_SEGUIDOS >= MAX_FALLOS:
                    icon.icon = crear_icono_amarillo()
                    print(" Reiniciando navegador por múltiples fallos...")
                    # alerta_sonora_reinicio()
                    # driver.quit()
                    # driver = iniciar_navegador()
                    # minimizar_chrome(driver)  # Ocultar Chrome después de abrirlo

                    navegar_y_preparar(driver)

                    # driver.delete_all_cookies()
                    # driver.execute_script("window.localStorage.clear();")
                    # driver.execute_script("window.sessionStorage.clear();")
                    # driver.get('https://compratickets.alhambra-patronato.es/reservarEntradas.aspx?opc=143&gid=432&lg=es&ca=0&m=GENERAL')

                    FALLOS_SEGUIDOS = 0
                    continue
                else:
                    continue

            dias_tachados_actual = obtener_dias_tachados_completos(driver)

            print(f"Días tachados actuales: {dias_tachados_actual}")
            logging.info(f"Días tachados actuales: {dias_tachados_actual}")

            set_inicial = set(dias_tachados_inicial)
            set_actual = set(dias_tachados_actual)

            dias_liberados = set_inicial - set_actual

            if (len(set_actual) == 0):
                dias_tachados_actual = dias_tachados_inicial

            if dias_tachados_actual and len(set_actual) > 3:
                dias_tachados_inicial = dias_tachados_actual
                logging.info(f" Días tachados actualizados con tamaño: {len(set_actual)}")


            if dias_liberados and dias_tachados_actual and len(set_actual) > 3:
                print(f" ¡Días liberados: {dias_liberados}!")
                logging.info(f" ¡Días liberados: {dias_liberados}!")

                alerta_sonora_acierto()
                # Cambiar el icono a rojo y comenzar a parpadear
                icon.icon = crear_icono_verde()
                parpadeo_evento.set()  # Activar el parpadeo
                parpadear_icono(icon)  # Iniciar el parpadeo

                # enviar_correo('¡Días liberados detectados!')
                enviar_telegram(f"¡Días liberados: {dias_liberados} en JARDINES detectados!")


                # mensaje = "¡Días disponibles detectados!\nDías que ya no están tachados: " + ", ".join(
                #     sorted(dias_liberados, key=int))
                # notificar_popup(mensaje)

            if DETENER:
                print(" Deteniendo el script.")
                break

            espera = random.uniform(40, 60)
            print(f" Esperando {espera:.2f} segundos antes de volver a intentar...")
            time.sleep(espera)
            parpadeo_evento.clear()  # Detener el parpadeo
            icon.icon = crear_icono_verde()  # Restaurar el icono a su estado normal

    finally:
        driver.quit()


def iniciar(icon, item):
    """Inicia el script en un hilo separado."""
    print("Pulsado iniciar")
    global DETENER, SCRIPT_THREAD


    # Cambiar el icono a amarillo al iniciar
    icon.icon = crear_icono_amarillo()

    if SCRIPT_THREAD is None or not SCRIPT_THREAD.is_alive():  # Verifica si el hilo no está corriendo
        DETENER = False
        SCRIPT_THREAD = threading.Thread(target=ejecutar_script, args=(icon,), daemon=True)
        SCRIPT_THREAD.start()
        print("Script iniciado.")
    else:
        print("El script ya está en ejecución.")


def detener(icon, item):
    """Detiene la ejecución del script y el parpadeo del icono."""
    global DETENER
    if not DETENER:
        DETENER = True
        parpadeo_evento.clear()  # Detener el parpadeo cuando se detiene el script

        # Cambiar el icono a azul al detener
        icon.icon = crear_icono_rojo()

        print("Script detenido.")


def salir(icon, item):
    """Cierra completamente el programa."""
    detener(icon, item)
    borrar_archivo_estado()
    icon.stop()


# Menú para la bandeja del sistema
menu = Menu(
    MenuItem("Iniciar", iniciar),
    MenuItem("Detener", detener),
    MenuItem("Salir", salir),
)

icono = Icon("Alhambra Script", crear_icono(), "Gestor de Calendarios Jardines", menu)

iniciar(icono, None)

if __name__ == "__main__":
    icono.run()
