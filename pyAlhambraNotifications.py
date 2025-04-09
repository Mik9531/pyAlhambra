import threading
import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import calendar

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from pystray import Icon, MenuItem, Menu
from PIL import Image, ImageDraw
import random  # Asegúrate de tener esto arriba del todo
import pickle
import os
from threading import Event

import undetected_chromedriver as uc
import atexit
import pyttsx3

import smtplib
from email.mime.text import MIMEText
import requests

parpadeo_evento = Event()

FALLOS_SEGUIDOS = 0
MAX_FALLOS = 2
ESTADO_FILE = "dias_tachados_inicial_general.pkl"

import time
import win32gui
import win32con

import logging

# Configurar el logging
logging.basicConfig(
    filename="general.log",  # Nombre del archivo donde se guardará el log
    level=logging.INFO,  # Nivel mínimo de mensajes a registrar (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format="%(asctime)s - %(levelname)s - %(message)s",  # Formato del mensaje de log
    datefmt="%Y-%m-%d %H:%M:%S"  # Formato de fecha
)


def enviar_telegram(mensaje):
    url = "https://api.telegram.org/bot7908020608:AAEGRux_wQ8tlKxPoMEGLR5vMtG1X3LW2WY/sendMessage"
    # datos = {"chat_id": str(780778418), "text": mensaje}  # Miguel

    chat_ids = [780778418]  # Belén (dos IDs diferentes)

    for chat_id in chat_ids:
        datos = {"chat_id": str(chat_id), "text": mensaje}

        try:
            respuesta = requests.post(url, data=datos)

            if respuesta.status_code == 200:
                print(f"Mensaje enviado a {chat_id}.")
            else:
                print(f"Error al enviar mensaje a {chat_id}: {respuesta.text}")
        except Exception as e:
            print(f"Error en la conexión con {chat_id}: {e}")


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


def obtener_dias_tachados_completos(driver, isViewState=0):
    dias_total = []

    # 🔹 Obtener el mes actual en formato "Enero", "Febrero", etc.
    mes_actual_num = datetime.now().month  # Ejemplo: 3 (marzo)
    mes_actual_nombre = calendar.month_name[mes_actual_num]  # "March"

    if isViewState == 1:
        print(f"Entramos por ViewState")

        try:
            boton_mes_siguiente = WebDriverWait(driver, 60).until(
                EC.element_to_be_clickable((By.XPATH, "//td[@align='right']//a[contains(@href,'__doPostBack')]"))
            )

            driver.execute_script("arguments[0].scrollIntoView();", boton_mes_siguiente)
            time.sleep(5)
            driver.execute_script("arguments[0].click();", boton_mes_siguiente)


        except Exception as e:
            print(f"No se pudo avanzar al mes siguiente: {e}")
            return []

        try:
            boton_mes_anterior = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//a[contains(@href,'__doPostBack')]/img[contains(@src,'prev.png')]/.."))
            )

            driver.execute_script("arguments[0].scrollIntoView();", boton_mes_anterior)
            time.sleep(2)
            driver.execute_script("arguments[0].click();", boton_mes_anterior)
            print("Comenzamos de nuevo la lectura del calendario")
        except Exception as e:
            print(f"No se pudo retroceder al mes anterior: {e}")
            return []

        time.sleep(5)

    # Obtener días tachados del mes actual

    try:
        dias_mes_actual = WebDriverWait(driver, 3).until(
            EC.presence_of_all_elements_located((
                By.CSS_SELECTOR,
                "#ctl00_ContentMaster1_ucReservarEntradasBaseAlhambra1_ucCalendarioPaso1_calendarioFecha .calendario_padding.no-dispo"
            ))
        )
    except Exception as e:
        print(f"No se pudieron cargar los días del mes actual: {e}")
        dias_mes_actual = []

    dias_total.extend([f"{mes_actual_nombre}-{dia.text.strip()}" for dia in dias_mes_actual if dia.text.strip()])

    logging.info(f"Días extraído del mes actual (innerText): '{dias_total}'")
    print(f"Días extraído del mes actual (innerText): '{dias_total}'")

    if (True):
        # 🔹 Avanzar al mes siguiente

        try:
            boton_mes_siguiente = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.XPATH, "//td[@align='right']//a[contains(@href,'__doPostBack')]"))
            )

            driver.execute_script("arguments[0].scrollIntoView();", boton_mes_siguiente)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", boton_mes_siguiente)

            # 🔹 Esperar a que los nuevos elementos se carguen después del cambio de mes
            time.sleep(2)  # Pequeña pausa para asegurar la carga de la página

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

            for dia in dias_mes_siguiente:
                texto_dia = dia.get_attribute("innerText").strip()
                logging.info(f"Día extraído del mes siguiente (innerText): '{texto_dia}'")
                # print(f"Días extraído del mes siguiente (innerText): '{dias_total}'")
                if texto_dia.isdigit():
                    dias_total.append(f"{mes_siguiente_nombre}-{texto_dia}")
        except Exception as e:
            print(f"No se pudo obtener fechas del mes siguiente: {e}")
            return []

    return dias_total


# Configuración inicial
TIEMPO_REFRESCO = 10  # Tiempo entre revisiones en segundos
TIEMPO = random.uniform(5, 6)  # Tiempo de espera tras cada paso
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
    engine.say("Días liberados para reservar en General")
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

    random_port = random.randint(9200, 9400)

    def iniciar_navegador():

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
        options.add_argument("--disable-extensions")

        options.add_argument("--disable-popup-blocking")
        options.add_argument(f"--remote-debugging-port={random_port}")
        # options.add_argument("--headless=new")

        options.add_argument(f"--user-data-dir={ruta_perfil_chrome}")  # <-- Asegurar que está bien escrito

        driver = uc.Chrome(options=options)

        return driver

    def navegar_y_preparar(driver):
        URL_INICIAL = 'https://tickets.alhambra-patronato.es/'
        URL_RESERVAS_GENERAL = 'https://compratickets.alhambra-patronato.es/reservarEntradas.aspx?opc=142&gid=432&lg=es-ES&ca=0&m=GENERAL'

        driver.get(URL_RESERVAS_GENERAL)
        driver.delete_all_cookies()
        driver.execute_script("window.localStorage.clear();")
        driver.execute_script("window.sessionStorage.clear();")

        try:
            WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.ID, "ctl00_lnkAceptarTodoCookies_Info"))
            ).click()
            print("Botón 'Aceptar cookies' pulsado.")
            time.sleep(TIEMPO)
        except Exception:
            print("Botón de cookies no encontrado o ya aceptado.")

    driver = iniciar_navegador()

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
                WebDriverWait(driver, 1).until(
                    EC.element_to_be_clickable(
                        (By.ID, "ctl00_ContentMaster1_ucReservarEntradasBaseAlhambra1_btnIrPaso1"))
                ).click()
                # time.sleep(TIEMPO)

            except Exception:
                print("Botón de paso 1 ya pulsado.")

            # time.sleep(TIEMPO)
            dias_tachados_inicial = obtener_dias_tachados_completos(driver, 0)

            # time.sleep(TIEMPO)

            if dias_tachados_inicial:
                break
            # alerta_sonora_error()
            intentos += 1
            print(f"Intento {intentos}: No se encontraron días tachados. Accediendo a viewState")
            # print(driver.page_source)  # Para ver si hay mensajes ocultos o errores

            # 3. Reemplazar manualmente el valor de __VIEWSTATE con el que tú sabes que funciona
            viewstate_funcional = "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OTUyZxAFBDE5NTMFBDE5NTNnEAUEMTk1NAUEMTk1NGcQBQQxOTU1BQQxOTU1ZxAFBDE5NTYFBDE5NTZnEAUEMTk1NwUEMTk1N2cQBQQxOTU4BQQxOTU4ZxAFBDE5NTkFBDE5NTlnEAUEMTk2MAUEMTk2MGcQBQQxOTYxBQQxOTYxZxAFBDE5NjIFBDE5NjJnEAUEMTk2MwUEMTk2M2cQBQQxOTY0BQQxOTY0ZxAFBDE5NjUFBDE5NjVnEAUEMTk2NgUEMTk2NmcQBQQxOTY3BQQxOTY3ZxAFBDE5NjgFBDE5NjhnEAUEMTk2OQUEMTk2OWcQBQQxOTcwBQQxOTcwZxAFBDE5NzEFBDE5NzFnEAUEMTk3MgUEMTk3MmcQBQQxOTczBQQxOTczZxAFBDE5NzQFBDE5NzRnEAUEMTk3NQUEMTk3NWcQBQQxOTc2BQQxOTc2ZxAFBDE5NzcFBDE5NzdnEAUEMTk3OAUEMTk3OGcQBQQxOTc5BQQxOTc5ZxAFBDE5ODAFBDE5ODBnEAUEMTk4MQUEMTk4MWcQBQQxOTgyBQQxOTgyZxAFBDE5ODMFBDE5ODNnEAUEMTk4NAUEMTk4NGcQBQQxOTg1BQQxOTg1ZxAFBDE5ODYFBDE5ODZnEAUEMTk4NwUEMTk4N2cQBQQxOTg4BQQxOTg4ZxAFBDE5ODkFBDE5ODlnEAUEMTk5MAUEMTk5MGcQBQQxOTkxBQQxOTkxZxAFBDE5OTIFBDE5OTJnEAUEMTk5MwUEMTk5M2cQBQQxOTk0BQQxOTk0ZxAFBDE5OTUFBDE5OTVnEAUEMTk5NgUEMTk5NmcQBQQxOTk3BQQxOTk3ZxAFBDE5OTgFBDE5OThnEAUEMTk5OQUEMTk5OWcQBQQyMDAwBQQyMDAwZxAFBDIwMDEFBDIwMDFnEAUEMjAwMgUEMjAwMmcQBQQyMDAzBQQyMDAzZxAFBDIwMDQFBDIwMDRnEAUEMjAwNQUEMjAwNWcQBQQyMDA2BQQyMDA2ZxAFBDIwMDcFBDIwMDdnEAUEMjAwOAUEMjAwOGcQBQQyMDA5BQQyMDA5ZxAFBDIwMTAFBDIwMTBnEAUEMjAxMQUEMjAxMWcQBQQyMDEyBQQyMDEyZxAFBDIwMTMFBDIwMTNnEAUEMjAxNAUEMjAxNGcQBQQyMDE1BQQyMDE1ZxAFBDIwMTYFBDIwMTZnEAUEMjAxNwUEMjAxN2cQBQQyMDE4BQQyMDE4ZxAFBDIwMTkFBDIwMTlnEAUEMjAyMAUEMjAyMGcQBQQyMDIxBQQyMDIxZxAFBDIwMjIFBDIwMjJnEAUEMjAyMwUEMjAyM2cQBQQyMDI0BQQyMDI0ZxAFBDIwMjUFBDIwMjVnFgFmZAILDxYCHwZoFgICAQ8WAh8HZGQCDA9kFgICAQ8WAh8HBQVFbWFpbGQCDQ9kFgICAQ8WAh8HBQ5Db25maXJtYSBFbWFpbGQCDg9kFgICAQ8WAh8HBQtDb250cmFzZcOxYWQCDw9kFgICAQ8WAh8HBRNSZXBldGlyIENvbnRyYXNlw7FhZAIQDxYCHwZoFgICAQ8WAh8HZWQCEQ8WAh8GaBYCAgEPFgIfB2VkAhIPFgIfBmgWAgIBDxYCHwdlZAITDxYCHwZoFgYCAQ8WAh8HZWQCAw8PFgQeCENzc0NsYXNzBRJpbnB1dC10ZXh0IG9jdWx0YXIeBF8hU0ICAmRkAgUPEA8WBB8JZR8KAgJkEBU1FFNlbGVjY2lvbmUgcHJvdmluY2lhCEFsYmFjZXRlCEFsaWNhbnRlCEFsbWVyw61hBsOBbGF2YQhBc3R1cmlhcwbDgXZpbGEHQmFkYWpveg1CYWxlYXJzIElsbGVzCUJhcmNlbG9uYQdCaXprYWlhBkJ1cmdvcwhDw6FjZXJlcwZDw6FkaXoJQ2FudGFicmlhCkNhc3RlbGzDs24LQ2l1ZGFkIFJlYWwIQ8OzcmRvYmEJQ29ydcOxYSBBBkN1ZW5jYQhHaXB1emtvYQZHaXJvbmEHR3JhbmFkYQtHdWFkYWxhamFyYQZIdWVsdmEGSHVlc2NhBUphw6luBUxlw7NuBkxsZWlkYQRMdWdvBk1hZHJpZAdNw6FsYWdhBk11cmNpYQdOYXZhcnJhB091cmVuc2UIUGFsZW5jaWEKUGFsbWFzIExhcwpQb250ZXZlZHJhCFJpb2phIExhCVNhbGFtYW5jYRZTYW50YSBDcnV6IGRlIFRlbmVyaWZlB1NlZ292aWEHU2V2aWxsYQVTb3JpYQlUYXJyYWdvbmEGVGVydWVsBlRvbGVkbwhWYWxlbmNpYQpWYWxsYWRvbGlkBlphbW9yYQhaYXJhZ296YQVDZXV0YQdNZWxpbGxhFTUAAjAyAjAzAjA0AjAxAjMzAjA1AjA2AjA3AjA4AjQ4AjA5AjEwAjExAjM5AjEyAjEzAjE0AjE1AjE2AjIwAjE3AjE4AjE5AjIxAjIyAjIzAjI0AjI1AjI3AjI4AjI5AjMwAjMxAjMyAjM0AjM1AjM2AjI2AjM3AjM4AjQwAjQxAjQyAjQzAjQ0AjQ1AjQ2AjQ3AjQ5AjUwAjUxAjUyFCsDNWdnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnFgFmZAIUD2QWBgIBDxYCHwcFBVBhw61zZAIDDw8WAh8GaGRkAgUPEGQQFe8BE1NlbGVjY2lvbmUgdW4gcGHDrXMJQXJnZW50aW5hCUF1c3RyYWxpYQVDaGluYQVJdGFseQVKYXBhbgZNZXhpY28LTmV3IFplYWxhbmQIUG9ydHVnYWwHRXNwYcOxYQdHZXJtYW55BkZyYW5jZRJSdXNzaWFuIEZlZGVyYXRpb24OVW5pdGVkIEtpbmdkb20UVW5pdGVkIFN0YXRlcyBvZiBBbWULQWZnaGFuaXN0YW4HQWxiYW5pYQdBbGdlcmlhDkFtZXJpY2FuIFNhbW9hB0FuZG9ycmEGQW5nb2xhCEFuZ3VpbGxhCkFudGFyY3RpY2EHQW50aWd1YQdBcm1lbmlhBUFydWJhB0F1c3RyaWEKQXplcmJhaWphbgdCYWhhbWFzB0JhaHJhaW4KQmFuZ2xhZGVzaAhCYXJiYWRvcwdCZWxhcnVzB0JlbGdpdW0GQmVsaXplBUJlbmluB0Jlcm11ZGEGQmh1dGFuB0JvbGl2aWEGQm9zbmlhCEJvdHN3YW5hDUJvdXZldCBJc2xhbmQGQnJhemlsDkJyaXRpc2ggSW5kaWFuEUJydW5laSBEYXJ1c3NhbGFtCEJ1bGdhcmlhDEJ1cmtpbmEgRmFzbwdCdXJ1bmRpCENhbWJvZGlhCENhbWVyb29uBkNhbmFkYQpDYXBlIFZlcmRlDkNheW1hbiBJc2xhbmRzE0NlbnRyYWwgQWZyaWNhbiBSZXAEQ2hhZAVDaGlsZRBDaHJpc3RtYXMgSXNsYW5kDUNvY29zIElzbGFuZHMIQ29sb21iaWEHQ29tb3JvcwVDb25nbwxDb29rIElzbGFuZHMKQ29zdGEgUmljYQdDcm9hdGlhBEN1YmEGQ3lwcnVzDkN6ZWNoIFJlcHVibGljB0Rlbm1hcmsIRGppYm91dGkIRG9taW5pY2ESRG9taW5pY2FuIFJlcHVibGljCkVhc3QgVGltb3IHRWN1YWRvcgVFZ3lwdAtFbCBTYWx2YWRvchFFcXVhdG9yaWFsIEd1aW5lYQdFcml0cmVhB0VzdG9uaWEIRXRoaW9waWENRmFyb2UgSXNsYW5kcwRGaWppB0ZpbmxhbmQNRnJlbmNoIEd1aWFuYRBGcmVuY2ggUG9seW5lc2lhBUdhYm9uBkdhbWJpYQdHZW9yZ2lhBUdoYW5hBkdyZWVjZQlHcmVlbmxhbmQHR3JlbmFkYQpHdWFkZWxvdXBlBEd1YW0JR3VhdGVtYWxhBkd1aW5lYQ1HdWluZWEgQmlzc2F1Bkd1eWFuYQVIYWl0aQhIb25kdXJhcwlIb25nIEtvbmcHSHVuZ2FyeQdJY2VsYW5kBUluZGlhCUluZG9uZXNpYQRJcmFuBElyYXEHSXJlbGFuZAZJc3JhZWwLSXZvcnkgQ29hc3QHSmFtYWljYQZKb3JkYW4KS2F6YWtoc3RhbgVLZW55YQhLaXJpYmF0aQZLdXdhaXQKS3lyZ3l6c3RhbgNMYW8GTGF0dmlhB0xlYmFub24HTGVzb3RobwdMaWJlcmlhBUxpYnlhDUxpZWNodGVuc3RlaW4JTGl0aHVhbmlhCkx1eGVtYm91cmcFTWFjYXUJTWFjZWRvbmlhCk1hZGFnYXNjYXIGTWFsYXdpCE1hbGF5c2lhCE1hbGRpdmVzBE1hbGkFTWFsdGEITWFsdmluYXMQTWFyc2hhbGwgSXNsYW5kcwpNYXJ0aW5pcXVlCk1hdXJpdGFuaWEJTWF1cml0aXVzB01heW90dGUKTWljcm9uZXNpYQdNb2xkb3ZhBk1vbmFjbwhNb25nb2xpYQpNb250ZW5lZ3JvCk1vbnRzZXJyYXQHTW9yb2NjbwpNb3phbWJpcXVlB015YW5tYXIHTmFtaWJpYQVOYXVydQVOZXBhbAtOZXRoZXJsYW5kcxROZXRoZXJsYW5kcyBBbnRpbGxlcw1OZXcgQ2FsZWRvbmlhCU5pY2FyYWd1YQVOaWdlcgdOaWdlcmlhBE5pdWUOTm9yZm9sayBJc2xhbmQLTm9ydGggS29yZWETTm9ydGhlcm4gTWFyaWFuYSBJcwZOb3J3YXkET21hbhlPdHJvcyBkZSBwYWlzZXMgZGVsIG11bmRvCFBha2lzdGFuBVBhbGF1BlBhbmFtYRBQYXB1YSBOZXcgR3VpbmVhCFBhcmFndWF5BFBlcnULUGhpbGlwcGluZXMIUGl0Y2Fpcm4GUG9sYW5kC1B1ZXJ0byBSaWNvBVFhdGFyB1JldW5pb24HUm9tYW5pYQZSd2FuZGEPUyBHZW9yZ2lhIFNvdXRoC1NhaW50IEx1Y2lhBVNhbW9hClNhbiBNYXJpbm8TU2FvIFRvbWUgLSBQcmluY2lwZQxTYXVkaSBBcmFiaWEHU2VuZWdhbAZTZXJiaWEKU2V5Y2hlbGxlcwxTaWVycmEgTGVvbmUJU2luZ2Fwb3JlCFNsb3Zha2lhCFNsb3ZlbmlhD1NvbG9tb24gSXNsYW5kcwdTb21hbGlhDFNvdXRoIEFmcmljYQtTb3V0aCBLb3JlYQlTcmkgTGFua2EJU3QgSGVsZW5hElN0IEtpdHRzIGFuZCBOZXZpcxNTdCBQaWVycmUgIE1pcXVlbG9uEVN0IFZpbmNlbnQtR3JlbmFkBVN1ZGFuCFN1cmluYW1lEVN2YWxiYXJkIEphbiBNIElzCVN3YXppbGFuZAZTd2VkZW4LU3dpdHplcmxhbmQFU3lyaWEGVGFpd2FuClRhamlraXN0YW4IVGFuemFuaWEIVGhhaWxhbmQEVG9nbwdUb2tlbGF1BVRvbmdhE1RyaW5pZGFkIEFuZCBUb2JhZ28HVHVuaXNpYQZUdXJrZXkMVHVya21lbmlzdGFuFFR1cmtzIENhaWNvcyBJc2xhbmRzBlR1dmFsdQZVZ2FuZGEHVWtyYWluZRRVbml0ZWQgQXJhYiBFbWlyYXRlcwdVcnVndWF5EFVTIE1pbm9yIElzbGFuZHMKVXpiZWtpc3RhbgdWYW51YXR1B1ZhdGljYW4JVmVuZXp1ZWxhB1ZpZXRuYW0OVmlyZ2luIElzbGFuZHMRVmlyZ2luIElzbGFuZHMgVVMQV2FsbGlzIEZ1dHVuYSBJcw5XZXN0ZXJuIFNhaGFyYQVZZW1lbgpZdWdvc2xhdmlhBVphaXJlBlphbWJpYQhaaW1iYWJ3ZRXvAQADMDMyAzAzNgMxNTYDMzgwAzM5MgM0ODQDNTU0AzYyMAM3MjQDMjc2AzI1MAM2NDMDODI2Azg0MAMwMDQDMDA4AzAxMgMwMTYDMDIwAzAyNAM2NjADMDEwAzAyOAMwNTEDNTMzAzA0MAMwMzEDMDQ0AzA0OAMwNTADMDUyAzExMgMwNTYDMDg0AzIwNAMwNjADMDY0AzA2OAMwNzADMDcyAzA3NAMwNzYDMDg2AzA5NgMxMDADODU0AzEwOAMxMTYDMTIwAzEyNAMxMzIDMTM2AzE0MAMxNDgDMTUyAzE2MgMxNjYDMTcwAzE3NAMxNzgDMTg0AzE4OAMxOTEDMTkyAzE5NgMyMDMDMjA4AzI2MgMyMTIDMjE0AzYyNgMyMTgDODE4AzIyMgMyMjYDMjMyAzIzMwMyMzEDMjM0AzI0MgMyNDYDMjU0AzI1OAMyNjYDMjcwAzI2OAMyODgDMzAwAzMwNAMzMDgDMzEyAzMxNgMzMjADMzI0AzYyNAMzMjgDMzMyAzM0MAMzNDQDMzQ4AzM1MgMzNTYDMzYwAzM2NAMzNjgDMzcyAzM3NgMzODQDMzg4AzQwMAMzOTgDNDA0AzI5NgM0MTQDNDE3AzQxOAM0MjgDNDIyAzQyNgM0MzADNDM0AzQzOAM0NDADNDQyAzQ0NgM4MDcDNDUwAzQ1NAM0NTgDNDYyAzQ2NgM0NzADMjM4AzU4NAM0NzQDNDc4AzQ4MAMxNzUDNTgzAzQ5OAM0OTIDNDk2AzQ5OQM1MDADNTA0AzUwOAMxMDQDNTE2AzUyMAM1MjQDNTI4AzUzMAM1NDADNTU4AzU2MgM1NjYDNTcwAzU3NAM0MDgDNTgwAzU3OAM1MTIDNzQ0AzU4NgM1ODUDNTkxAzU5OAM2MDADNjA0AzYwOAM2MTIDNjE2AzYzMAM2MzQDNjM4AzY0MgM2NDYDMjM5AzY2MgM4ODIDNjc0AzY3OAM2ODIDNjg2AzY4OAM2OTADNjk0AzcwMgM3MDMDNzA1AzA5MAM3MDYDNzEwAzQxMAMxNDQDNjU0AzY1OQM2NjYDNjcwAzczNgM3NDADNzQ0Azc0OAM3NTIDNzU2Azc2MAMxNTgDNzYyAzgzNAM3NjQDNzY4Azc3MgM3NzYDNzgwAzc4OAM3OTIDNzk1Azc5NgM3OTgDODAwAzgwNAM3ODQDODU4AzU4MQM4NjADNTQ4AzMzNgM4NjIDNzA0AzA5MgM4NTADODc2AzczMgM4ODcDODkxAzE4MAM4OTQDNzE2FCsD7wFnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2RkAhUPZBYCAgEPFgIfBwUJVGVsw6lmb25vZAIXD2QWAgIDDxYCHwcFiQFIZSBsZcOtZG8geSBhY2VwdG8gbGEgPGEgaHJlZj0iaHR0cHM6Ly90aWNrZXRzLmFsaGFtYnJhLXBhdHJvbmF0by5lcy9wb2xpdGljYS1kZS1wcml2YWNpZGFkLyIgdGFyZ2V0PSJfYmxhbmsiPlBvbMOtdGljYSBkZSBwcml2YWNpZGFkPC9hPmQCGA8WAh8GaBYCAgMPFgIfB2VkAggPDxYCHwEFC1JlZ8Otc3RyZXNlZGQCAw8WAh8GaBYEAgMPDxYCHwMFHi9yZXNlcnZhckVudHJhZGFzLmFzcHg/b3BjPTE0MmRkAgUPDxYCHwEFDkNlcnJhciBzZXNpw7NuZGQCAQ9kFgICAQ8PFgQfCQUGYWN0aXZlHwoCAmRkAgIPDxYEHwMFPmh0dHBzOi8vd3d3LmFsaGFtYnJhLXBhdHJvbmF0by5lcy92aXNpdGFyL3ByZWd1bnRhcy1mcmVjdWVudGVzHwZnZGQCBA9kFgICAQ8PFgIfAwUoaHR0cDovL3d3dy55b3V0dWJlLmNvbS9hbGhhbWJyYXBhdHJvbmF0b2RkAgUPZBYCAgEPDxYCHwMFK2h0dHBzOi8vd3d3Lmluc3RhZ3JhbS5jb20vYWxoYW1icmFfb2ZpY2lhbC9kZAIGD2QWAgIBDw8WAh8DBShodHRwczovL3d3dy5mYWNlYm9vay5jb20vYWxoYW1icmFjdWx0dXJhZGQCBw9kFgICAQ8PFgIfAwUmaHR0cDovL3d3dy50d2l0dGVyLmNvbS9hbGhhbWJyYWN1bHR1cmFkZAIID2QWAgIBDw8WAh8DBSlodHRwczovL2VzLnBpbnRlcmVzdC5jb20vYWxoYW1icmFncmFuYWRhL2RkAgkPFgIfBmhkAgoPFgIfBmgWAgIBDw8WAh8DZGQWAmYPDxYCHwUFFUFsaGFtYnJhIHkgR2VuZXJhbGlmZWRkAgsPZBYCZg8PFgQfAwU+aHR0cHM6Ly93d3cuYWxoYW1icmEtcGF0cm9uYXRvLmVzL3Zpc2l0YXIvcHJlZ3VudGFzLWZyZWN1ZW50ZXMfBmdkZAIND2QWCAIBDw8WAh8GaGQWAgIBD2QWAmYPZBYGAgMPDxYCHwZoZGQCBA8PFgIeBkVzdGFkb2ZkFgJmD2QWAgIBD2QWAmYPZBYCAgEPZBYCAggPFgIfBmhkAg4PZBYEAgsPZBYEAgEPZBYCAgMPEGRkFgBkAgYPZBYCAgcPEGRkFgBkAg0PZBYEAgYPZBYCAgEPZBYCAgMPEGRkFgBkAgkPZBYCAgcPEGRkFgBkAgMPDxYCHwZoZBYCZg9kFgJmD2QWBgIBDw8WAh8GaGRkAggPZBYGAgUPZBYCAgEPEGRkFgBkAgYPZBYCAgEPEGRkFgBkAggPZBYEZg8QZGQWAGQCAQ8QZGQWAGQCCg9kFgICBQ9kFg4CAw9kFgICBQ8QZGQWAGQCBA9kFgICAw8QZGQWAGQCBg9kFgICBw8QZGQWAGQCCA9kFgICBQ8QZGQWAGQCCQ9kFgICBQ8QZGQWAGQCDw9kFgICBw8QZGQWAGQCFg9kFgQCAQ9kFgICAw8QZGQWAGQCBg9kFgICBw8QZGQWAGQCBQ8PFgIfBmhkFgJmD2QWAmYPZBYEAgMPDxYCHwtmZBYCZg9kFgICAQ9kFgJmD2QWAgIBD2QWAgIIDxYCHwZoZAIGD2QWAmYPZBYCAgEPZBYCZg9kFgICAQ88KwAKAQAPFgQeDVByZXZNb250aFRleHRlHg1OZXh0TW9udGhUZXh0BS08aW1nIHNyYz0vQXBwX3RoZW1lcy9BTEhBTUJSQS9pbWcvbmV4dC5wbmcgLz5kZAIHDw8WIB4UTG9jYWxpemFkb3JQYXJhbWV0cm9kHhVGZWNoYU1pbmltYURpc3BvbmlibGUG/z839HUoyiseEEZpbmFsaXphck1lbm9yZXNoHg5BZm9yb1BhcmFtZXRybwIBHgZQYWdhZGEFBUZhbHNlHgdTaW1ib2xvBQPigqweE0VubGFjZU1lbnVQYXJhbWV0cm8FB0dFTkVSQUweDFNlc2lvbkRpYXJpYWgeDFNlc2lvbkFjdHVhbAUfeGYweHl3MnZreXNpYTBhenUzNGlqMXBrNTE1OTIwMh4MQ2FwdGNoYVBhc28xZx4MTnVtRGVjaW1hbGVzAgIeD0NhcHRjaGFWYWxpZGFkb2ceCk5vbWluYWNpb25mHgxUZW5lbW9zTmlub3NoHhZHcnVwb0ludGVybmV0UGFyYW1ldHJvBQMxNDIeCFNpbkZlY2hhZmQWBAIBD2QWAmYPZBYiAgMPDxYCHwZoZGQCBA8PFgIfC2ZkFgJmD2QWAgIBD2QWAmYPZBYCAgEPZBYGZg8PFgIfAQUFZW1haWxkZAICDw8WAh8BBQxUZWxlZm9ubyBTTVNkZAIIDxYCHwZoZAIFDw8WAh8DBTBodHRwczovL3d3dy5hbGhhbWJyYS1wYXRyb25hdG8uZXMvP2NhPTAmbGc9ZXMtRVNkZAIGDxYCHwFlZAIHDxYCHwEFF1Zpc2l0YSBBbGhhbWJyYSBHZW5lcmFsZAIIDxYCHgVjbGFzcwUWc3RlcC10aXRsZSBzdGVwLWFjdGl2ZRYCAgEPFgIfAWRkAgkPDxYCHwZoZBYCAgEPDxYCHwEFC0lyIGEgcGFzbyAxZGQCCg8PFgIfBmdkFghmDxYCHwEFvQE8c2NyaXB0IHR5cGU9InRleHQvamF2YXNjcmlwdCI+d2luZG93LmRhdGFMYXllciA9IHdpbmRvdy5kYXRhTGF5ZXIgfHwgW107IGRhdGFMYXllci5wdXNoKHsgJ1BlcmZpbCc6J0dlbmVyYWwnLCAnQ2F0ZWdvcmlhJzonVmlzaXRhIEFsaGFtYnJhIEdlbmVyYWwnLCAnVGlwb0VudHJhZGEnOidJbmRpdmlkdWFsJyB9KTs8L3NjcmlwdD5kAgEPFgIfAWVkAgYPDxYWHhFGZWNoYU1pbmltYUdsb2JhbAYAf+q/AHfdCB4EUGFzbwIBHg1HcnVwb0ludGVybmV0BQMxNDIeDERhdG9zRmVzdGl2bzK7BAABAAAA/////wEAAAAAAAAADAIAAABIQXBwX0NvZGUueGhqcHZpem8sIFZlcnNpb249MC4wLjAuMCwgQ3VsdHVyZT1uZXV0cmFsLCBQdWJsaWNLZXlUb2tlbj1udWxsBQEAAAAfRGF0b3NGZXN0aXZvcytEYXRvc0xpc3RGZXN0aXZvcwEAAAARX0xzdERhdG9zRmVzdGl2b3MDiQFTeXN0ZW0uQ29sbGVjdGlvbnMuR2VuZXJpYy5MaXN0YDFbW0RhdG9zRmVzdGl2b3MrRGF0b3NGZXN0aXZvLCBBcHBfQ29kZS54aGpwdml6bywgVmVyc2lvbj0wLjAuMC4wLCBDdWx0dXJlPW5ldXRyYWwsIFB1YmxpY0tleVRva2VuPW51bGxdXQIAAAAJAwAAAAQDAAAAiQFTeXN0ZW0uQ29sbGVjdGlvbnMuR2VuZXJpYy5MaXN0YDFbW0RhdG9zRmVzdGl2b3MrRGF0b3NGZXN0aXZvLCBBcHBfQ29kZS54aGpwdml6bywgVmVyc2lvbj0wLjAuMC4wLCBDdWx0dXJlPW5ldXRyYWwsIFB1YmxpY0tleVRva2VuPW51bGxdXQMAAAAGX2l0ZW1zBV9zaXplCF92ZXJzaW9uBAAAHERhdG9zRmVzdGl2b3MrRGF0b3NGZXN0aXZvW10CAAAACAgJBAAAAAAAAAAAAAAABwQAAAAAAQAAAAAAAAAEGkRhdG9zRmVzdGl2b3MrRGF0b3NGZXN0aXZvAgAAAAseE01pbmltb0dydXBvSW50ZXJuZXQCAR4RRmVjaGFNYXhpbWFHbG9iYWwGALrGchSn3ggeDUVzTGlzdGFFc3BlcmFoHgtGb3J6YXJDYXJnYWgeDkZlY2hhc1ZpZ2VuY2lhMogNAAEAAAD/////AQAAAAAAAAAEAQAAAOIBU3lzdGVtLkNvbGxlY3Rpb25zLkdlbmVyaWMuRGljdGlvbmFyeWAyW1tTeXN0ZW0uU3RyaW5nLCBtc2NvcmxpYiwgVmVyc2lvbj00LjAuMC4wLCBDdWx0dXJlPW5ldXRyYWwsIFB1YmxpY0tleVRva2VuPWI3N2E1YzU2MTkzNGUwODldLFtTeXN0ZW0uU3RyaW5nLCBtc2NvcmxpYiwgVmVyc2lvbj00LjAuMC4wLCBDdWx0dXJlPW5ldXRyYWwsIFB1YmxpY0tleVRva2VuPWI3N2E1YzU2MTkzNGUwODldXQQAAAAHVmVyc2lvbghDb21wYXJlcghIYXNoU2l6ZQ1LZXlWYWx1ZVBhaXJzAAMAAwiSAVN5c3RlbS5Db2xsZWN0aW9ucy5HZW5lcmljLkdlbmVyaWNFcXVhbGl0eUNvbXBhcmVyYDFbW1N5c3RlbS5TdHJpbmcsIG1zY29ybGliLCBWZXJzaW9uPTQuMC4wLjAsIEN1bHR1cmU9bmV1dHJhbCwgUHVibGljS2V5VG9rZW49Yjc3YTVjNTYxOTM0ZTA4OV1dCOYBU3lzdGVtLkNvbGxlY3Rpb25zLkdlbmVyaWMuS2V5VmFsdWVQYWlyYDJbW1N5c3RlbS5TdHJpbmcsIG1zY29ybGliLCBWZXJzaW9uPTQuMC4wLjAsIEN1bHR1cmU9bmV1dHJhbCwgUHVibGljS2V5VG9rZW49Yjc3YTVjNTYxOTM0ZTA4OV0sW1N5c3RlbS5TdHJpbmcsIG1zY29ybGliLCBWZXJzaW9uPTQuMC4wLjAsIEN1bHR1cmU9bmV1dHJhbCwgUHVibGljS2V5VG9rZW49Yjc3YTVjNTYxOTM0ZTA4OV1dW10HAAAACQIAAAAHAAAACQMAAAAEAgAAAJIBU3lzdGVtLkNvbGxlY3Rpb25zLkdlbmVyaWMuR2VuZXJpY0VxdWFsaXR5Q29tcGFyZXJgMVtbU3lzdGVtLlN0cmluZywgbXNjb3JsaWIsIFZlcnNpb249NC4wLjAuMCwgQ3VsdHVyZT1uZXV0cmFsLCBQdWJsaWNLZXlUb2tlbj1iNzdhNWM1NjE5MzRlMDg5XV0AAAAABwMAAAAAAQAAAAcAAAAD5AFTeXN0ZW0uQ29sbGVjdGlvbnMuR2VuZXJpYy5LZXlWYWx1ZVBhaXJgMltbU3lzdGVtLlN0cmluZywgbXNjb3JsaWIsIFZlcnNpb249NC4wLjAuMCwgQ3VsdHVyZT1uZXV0cmFsLCBQdWJsaWNLZXlUb2tlbj1iNzdhNWM1NjE5MzRlMDg5XSxbU3lzdGVtLlN0cmluZywgbXNjb3JsaWIsIFZlcnNpb249NC4wLjAuMCwgQ3VsdHVyZT1uZXV0cmFsLCBQdWJsaWNLZXlUb2tlbj1iNzdhNWM1NjE5MzRlMDg5XV0E/P///+QBU3lzdGVtLkNvbGxlY3Rpb25zLkdlbmVyaWMuS2V5VmFsdWVQYWlyYDJbW1N5c3RlbS5TdHJpbmcsIG1zY29ybGliLCBWZXJzaW9uPTQuMC4wLjAsIEN1bHR1cmU9bmV1dHJhbCwgUHVibGljS2V5VG9rZW49Yjc3YTVjNTYxOTM0ZTA4OV0sW1N5c3RlbS5TdHJpbmcsIG1z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YcOxYSkfAQUBMGRkAgUPFgIfHgUWaW5jIGJ1dHRvbkFjdGl2byBjb2wtNBYCAgEPDxYEHwkFEWJ0bk1hc01lbm9zQWN0aXZvHwoCAmRkAgMPFgIfBmhkAgUPDxYEHwEFCUNvbnRpbnVhch8GaGRkAgsPFgIfHgUKc3RlcC10aXRsZRYCAgEPFgIfAWRkAgwPDxYCHwZoZBYMAgEPFgIfAWVkAgUPFgIfBmhkAgcPZBYIAgEPDxYCHwZoZBYCAgEPZBYCZg9kFgICAQ88KwAKAQAPFgQfDGUfDQUtPGltZyBzcmM9L0FwcF90aGVtZXMvQUxIQU1CUkEvaW1nL25leHQucG5nIC8+ZGQCAw8WAh8GaBYCAgEPEGRkFgBkAgUPFgIfBmgWAgIBDxBkZBYAZAIJDw8WAh8GaGQWBGYPEGQQFQgYU2VsZWNjaW9uZSB1biBpdGluZXJhcmlvIFZpc2l0YXMgR3VpYWRhcyBwb3IgZWwgTW9udW1lbnRvLFZpc2l0YXMgQXV0b2d1aWFkYXMgcG9yIGVsIE1vbnVtZW50byBHZW5lcmFsJFZpc2l0YXMgQ29tYmluYWRhcyBBbGhhbWJyYSArIENpdWRhZCxWaXNpdGFzIEd1aWFkYXMgcG9yIGxhIERlaGVzYSBkZWwgR2VuZXJhbGlmZSlWaXNpdGFzIEd1aWFkYXMgcG9yIGVsIE1vbnVtZW50byBKYXJkaW5lcy1WaXNpdGFzIEF1dG9ndWlhZGFzIHBvciBlbCBNb251bWVudG8gSmFyZGluZXMeVmlzaXRhcyBHdWlhZGFzIE11c2VvICsgQ2l1ZGFkFQgAIFZpc2l0YXMgR3VpYWRhcyBwb3IgZWwgTW9udW1lbnRvLFZpc2l0YXMgQXV0b2d1aWFkYXMgcG9yIGVsIE1vbnVtZW50byBHZW5lcmFsJFZpc2l0YXMgQ29tYmluYWRhcyBBbGhhbWJyYSArIENpdWRhZCxWaXNpdGFzIEd1aWFkYXMgcG9yIGxhIERlaGVzYSBkZWwgR2VuZXJhbGlmZSlWaXNpdGFzIEd1aWFkYXMgcG9yIGVsIE1vbnVtZW50byBKYXJkaW5lcy1WaXNpdGFzIEF1dG9ndWlhZGFzIHBvciBlbCBNb251bWVudG8gSmFyZGluZXMeVmlzaXRhcyBHdWlhZGFzIE11c2VvICsgQ2l1ZGFkFCsDCGdnZ2dnZ2dnFgFmZAIBDxAPFgIfBmhkEBUBGFNlbGVjY2lvbmUgdW4gaXRpbmVyYXJpbxUBABQrAwFnFgFmZAILDxYCHwZoZAINDw8WAh8BBRd2b2x2ZXIgYWwgcGFzbyBhbnRlcmlvcmRkAg8PZBYCZg9kFgICAQ8PFgQfAQULSXIgYSBwYXNvIDMfBmhkZAINDxYEHx4FCnN0ZXAtdGl0bGUfBmdkAg4PDxYCHwZoZBYaZg8WAh8BZWQCAQ8WAh8BBQEuZAICD2QWAmYPZBYKAgEPDxYCHgpIZWFkZXJUZXh0BSVEZWJlIGludHJvZHVjaXIgbG9zIHZhbG9yZXMgY29ycmVjdG9zZGQCAw9kFgRmD2QWAmYPDxYCHwEFF05vbWJyZSBkZWwgY29tcHJhZG9yICogZGQCAQ9kFgJmDw8WAh8BBQxBcGVsbGlkb3MgKiBkZAIED2QWBGYPZBYEZg8PFgIfAQUZRG9jdW1lbnRvIGRlIGlkZW50aWRhZCAqIGRkAgIPEGQQFQMMRE5JIEVzcGHDsW9sDE5JRSBFc3Bhw7FvbBdPdHJvIE5yby4gaWRlbnRpZmljYWRvchUDA2RuaQNuaWUHb3Ryb19pZBQrAwNnZ2cWAWZkAgEPZBYCZg8PFgIfAQUXTsO6bWVybyBkZSBkb2N1bWVudG8gKiBkZAIFD2QWBGYPZBYCZg8PFgIfAQUIRW1haWwgKiBkZAIBD2QWAmYPDxYCHwEFEUNvbmZpcm1hIEVtYWlsICogZGQCBg9kFgJmD2QWAmYPDxYCHwEFDFRlbMOpZm9ubyAqIGRkAgQPFgIfBmcWAgIBDxAPFgIeB0NoZWNrZWRoZGRkZAIGD2QWBAIBD2QWAgIDDxBkEBUEDEROSSBFc3Bhw7FvbAxDSUYgRXNwYcOxb2wMTklFIEVzcGHDsW9sF090cm8gTnJvLiBpZGVudGlmaWNhZG9yFQQDZG5pA2NpZgNuaWUHb3Ryb19pZBQrAwRnZ2dnFgFmZAIGD2QWBAIFDw8WAh8GaGRkAgcPEGQQFe8BE1NlbGVjY2lvbmUgdW4gcGHDrXMJQXJnZW50aW5hCUF1c3RyYWxpYQVDaGluYQVJdGFseQVKYXBhbgZNZXhpY28LTmV3IFplYWxhbmQIUG9ydHVnYWwHRXNwYcOxYQdHZXJtYW55BkZyYW5jZRJSdXNzaWFuIEZlZGVyYXRpb24OVW5pdGVkIEtpbmdkb20UVW5pdGVkIFN0YXRlcyBvZiBBbWULQWZnaGFuaXN0YW4HQWxiYW5pYQdBbGdlcmlhDkFtZXJpY2FuIFNhbW9hB0FuZG9ycmEGQW5nb2xhCEFuZ3VpbGxhCkFudGFyY3RpY2EHQW50aWd1YQdBcm1lbmlhBUFydWJhB0F1c3RyaWEKQXplcmJhaWphbgdCYWhhbWFzB0JhaHJhaW4KQmFuZ2xhZGVzaAhCYXJiYWRvcwdCZWxhcnVzB0JlbGdpdW0GQmVsaXplBUJlbmluB0Jlcm11ZGEGQmh1dGFuB0JvbGl2aWEGQm9zbmlhCEJvdHN3YW5hDUJvdXZldCBJc2xhbmQGQnJhemlsDkJyaXRpc2ggSW5kaWFuEUJydW5laSBEYXJ1c3NhbGFtCEJ1bGdhcmlhDEJ1cmtpbmEgRmFzbwdCdXJ1bmRpCENhbWJvZGlhCENhbWVyb29uBkNhbmFkYQpDYXBlIFZlcmRlDkNheW1hbiBJc2xhbmRzE0NlbnRyYWwgQWZyaWNhbiBSZXAEQ2hhZAVDaGlsZRBDaHJpc3RtYXMgSXNsYW5kDUNvY29zIElzbGFuZHMIQ29sb21iaWEHQ29tb3JvcwVDb25nbwxDb29rIElzbGFuZHMKQ29zdGEgUmljYQdDcm9hdGlhBEN1YmEGQ3lwcnVzDkN6ZWNoIFJlcHVibGljB0Rlbm1hcmsIRGppYm91dGkIRG9taW5pY2ESRG9taW5pY2FuIFJlcHVibGljCkVhc3QgVGltb3IHRWN1YWRvcgVFZ3lwdAtFbCBTYWx2YWRvchFFcXVhdG9yaWFsIEd1aW5lYQdFcml0cmVhB0VzdG9uaWEIRXRoaW9waWENRmFyb2UgSXNsYW5kcwRGaWppB0ZpbmxhbmQNRnJlbmNoIEd1aWFuYRBGcmVuY2ggUG9seW5lc2lhBUdhYm9uBkdhbWJpYQdHZW9yZ2lhBUdoYW5hBkdyZWVjZQlHcmVlbmxhbmQHR3JlbmFkYQpHdWFkZWxvdXBlBEd1YW0JR3VhdGVtYWxhBkd1aW5lYQ1HdWluZWEgQmlzc2F1Bkd1eWFuYQVIYWl0aQhIb25kdXJhcwlIb25nIEtvbmcHSHVuZ2FyeQdJY2VsYW5kBUluZGlhCUluZG9uZXNpYQRJcmFuBElyYXEHSXJlbGFuZAZJc3JhZWwLSXZvcnkgQ29hc3QHSmFtYWljYQZKb3JkYW4KS2F6YWtoc3RhbgVLZW55YQhLaXJpYmF0aQZLdXdhaXQKS3lyZ3l6c3RhbgNMYW8GTGF0dmlhB0xlYmFub24HTGVzb3RobwdMaWJlcmlhBUxpYnlhDUxpZWNodGVuc3RlaW4JTGl0aHVhbmlhCkx1eGVtYm91cmcFTWFjYXUJTWFjZWRvbmlhCk1hZGFnYXNjYXIGTWFsYXdpCE1hbGF5c2lhCE1hbGRpdmVzBE1hbGkFTWFsdGEITWFsdmluYXMQTWFyc2hhbGwgSXNsYW5kcwpNYXJ0aW5pcXVlCk1hdXJpdGFuaWEJTWF1cml0aXVzB01heW90dGUKTWljcm9uZXNpYQdNb2xkb3ZhBk1vbmFjbwhNb25nb2xpYQpNb250ZW5lZ3JvCk1vbnRzZXJyYXQHTW9yb2NjbwpNb3phbWJpcXVlB015YW5tYXIHTmFtaWJpYQVOYXVydQVOZXBhbAtOZXRoZXJsYW5kcxROZXRoZXJsYW5kcyBBbnRpbGxlcw1OZXcgQ2FsZWRvbmlhCU5pY2FyYWd1YQVOaWdlcgdOaWdlcmlhBE5pdWUOTm9yZm9sayBJc2xhbmQLTm9ydGggS29yZWETTm9ydGhlcm4gTWFyaWFuYSBJcwZOb3J3YXkET21hbhlPdHJvcyBkZSBwYWlzZXMgZGVsIG11bmRvCFBha2lzdGFuBVBhbGF1BlBhbmFtYRBQYXB1YSBOZXcgR3VpbmVhCFBhcmFndWF5BFBlcnULUGhpbGlwcGluZXMIUGl0Y2Fpcm4GUG9sYW5kC1B1ZXJ0byBSaWNvBVFhdGFyB1JldW5pb24HUm9tYW5pYQZSd2FuZGEPUyBHZW9yZ2lhIFNvdXRoC1NhaW50IEx1Y2lhBVNhbW9hClNhbiBNYXJpbm8TU2FvIFRvbWUgLSBQcmluY2lwZQxTYXVkaSBBcmFiaWEHU2VuZWdhbAZTZXJiaWEKU2V5Y2hlbGxlcwxTaWVycmEgTGVvbmUJU2luZ2Fwb3JlCFNsb3Zha2lhCFNsb3ZlbmlhD1NvbG9tb24gSXNsYW5kcwdTb21hbGlhDFNvdXRoIEFmcmljYQtTb3V0aCBLb3JlYQlTcmkg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EGQQFe8BE1NlbGVjY2lvbmUgdW4gcGHDrXMJQXJnZW50aW5hCUF1c3RyYWxpYQVDaGluYQVJdGFseQVKYXBhbgZNZXhpY28LTmV3IFplYWxhbmQIUG9ydHVnYWwHRXNwYcOxYQdHZXJtYW55BkZyYW5jZRJSdXNzaWFuIEZlZGVyYXRpb24OVW5pdGVkIEtpbmdkb20UVW5pdGVkIFN0YXRlcyBvZiBBbWULQWZnaGFuaXN0YW4HQWxiYW5pYQdBbGdlcmlhDkFtZXJpY2FuIFNhbW9hB0FuZG9ycmEGQW5nb2xhCEFuZ3VpbGxhCkFudGFyY3RpY2EHQW50aWd1YQdBcm1lbmlhBUFydWJhB0F1c3RyaWEKQXplcmJhaWphbgdCYWhhbWFzB0JhaHJhaW4KQmFuZ2xhZGVzaAhCYXJiYWRvcwdCZWxhcnVzB0JlbGdpdW0GQmVsaXplBUJlbmluB0Jlcm11ZGEGQmh1dGFuB0JvbGl2aWEGQm9zbmlhCEJvdHN3YW5hDUJvdXZldCBJc2xhbmQGQnJhemlsDkJyaXRpc2ggSW5kaWFuEUJydW5laSBEYXJ1c3NhbGFtCEJ1bGdhcmlhDEJ1cmtpbmEgRmFzbwdCdXJ1bmRpCENhbWJvZGlhCENhbWVyb29uBkNhbmFkYQpDYXBlIFZlcmRlDkNheW1hbiBJc2xhbmRzE0NlbnRyYWwgQWZyaWNhbiBSZXAEQ2hhZAVDaGlsZRBDaHJpc3RtYXMgSXNsYW5kDUNvY29zIElzbGFuZHMIQ29sb21iaWEHQ29tb3JvcwVDb25nbwxDb29rIElzbGFuZHMKQ29zdGEgUmljYQdDcm9hdGlhBEN1YmEGQ3lwcnVzDkN6ZWNoIFJlcHVibGljB0Rlbm1hcmsIRGppYm91dGkIRG9taW5pY2ESRG9taW5pY2FuIFJlcHVibGljCkVhc3QgVGltb3IHRWN1YWRvcgVFZ3lwdAtFbCBTYWx2YWRvchFFcXVhdG9yaWFsIEd1aW5lYQdFcml0cmVhB0VzdG9uaWEIRXRoaW9waWENRmFyb2UgSXNsYW5kcwRGaWppB0ZpbmxhbmQNRnJlbmNoIEd1aWFuYRBGcmVuY2ggUG9seW5lc2lhBUdhYm9uBkdhbWJpYQdHZW9yZ2lhBUdoYW5hBkdyZWVjZQlHcmVlbmxhbmQHR3JlbmFkYQpHdWFkZWxvdXBlBEd1YW0JR3VhdGVtYWxhBkd1aW5lYQ1HdWluZWEgQmlzc2F1Bkd1eWFuYQVIYWl0aQhIb25kdXJhcwlIb25nIEtvbmcHSHVuZ2FyeQdJY2VsYW5kBUluZGlhCUluZG9uZXNpYQRJcmFuBElyYXEHSXJlbGFuZAZJc3JhZWwLSXZvcnkgQ29hc3QHSmFtYWljYQZKb3JkYW4KS2F6YWtoc3RhbgVLZW55YQhLaXJpYmF0aQZLdXdhaXQKS3lyZ3l6c3RhbgNMYW8GTGF0dmlhB0xlYmFub24HTGVzb3RobwdMaWJlcmlhBUxpYnlhDUxpZWNodGVuc3RlaW4JTGl0aHVhbmlhCkx1eGVtYm91cmcFTWFjYXUJTWFjZWRvbmlhCk1hZGFnYXNjYXIGTWFsYXdpCE1hbGF5c2lhCE1hbGRpdmVzBE1hbGkFTWFsdGEITWFsdmluYXMQTWFyc2hhbGwgSXNsYW5kcwpNYXJ0aW5pcXVlCk1hdXJpdGFuaWEJTWF1cml0aXVzB01heW90dGUKTWljcm9uZXNpYQdNb2xkb3ZhBk1vbmFjbwhNb25nb2xpYQpNb250ZW5lZ3JvCk1vbnRzZXJyYXQHTW9yb2NjbwpNb3phbWJpcXVlB015YW5tYXIHTmFtaWJpYQVOYXVydQVOZXBhbAtOZXRoZXJsYW5kcxROZXRoZXJsYW5kcyBBbnRpbGxlcw1OZXcgQ2FsZWRvbmlhCU5pY2FyYWd1YQVOaWdlcgdOaWdlcmlhBE5pdWUOTm9yZm9sayBJc2xhbmQLTm9ydGggS29yZWETTm9ydGhlcm4gTWFyaWFuYSBJcwZOb3J3YXkET21hbhlPdHJvcyBkZSBwYWlzZXMgZGVsIG11bmRvCFBha2lzdGFuBVBhbGF1BlBhbmFtYRBQYXB1YSBOZXcgR3VpbmVhCFBhcmFndWF5BFBlcnULUGhpbGlwcGluZXMIUGl0Y2Fpcm4GUG9sYW5kC1B1ZXJ0byBSaWNvBVFhdGFyB1JldW5pb24HUm9tYW5pYQZSd2FuZGEPUyBHZW9yZ2lhIFNvdXRoC1NhaW50IEx1Y2lhBVNhbW9hClNhbiBNYXJpbm8TU2FvIFRvbWUgLSBQcmluY2lwZQxTYXVkaSBBcmFiaWEHU2VuZWdhbAZTZXJiaWEKU2V5Y2hlbGxlcwxTaWVycmEgTGVvbmUJU2luZ2Fwb3JlCFNsb3Zha2lhCFNsb3ZlbmlhD1NvbG9tb24gSXNsYW5kcwdTb21hbGlhDFNvdXRoIEFmcmljYQtTb3V0aCBLb3JlYQlTcmkgTGFua2EJU3QgSGVsZW5hElN0IEtpdHRzIGFuZCBOZXZpcxNTdCBQaWVycmUgIE1pcXVlbG9uEVN0IFZpbmNlbnQtR3JlbmFkBVN1ZGFuCFN1cmluYW1lEVN2YWxiYXJkIEphbiBNIElzCVN3YXppbGFuZAZTd2VkZW4LU3dpdHplcmxhbmQFU3lyaWEGVGFpd2FuClRhamlraXN0YW4IVGFuemFuaWEIVGhhaWxhbmQEVG9nbwdUb2tlbGF1BVRvbmdhE1RyaW5pZGFkIEFuZCBUb2JhZ28HVHVuaXNpYQZUdXJrZXkMVHVya21lbmlzdGFuFFR1cmtzIENhaWNvcyBJc2xhbmRzBlR1dmFsdQZVZ2FuZGEHVWtyYWluZRRVbml0ZWQgQXJhYiBFbWlyYXRlcwdVcnVndWF5EFVTIE1pbm9yIElzbGFuZHMKVXpiZWtpc3RhbgdWYW51YXR1B1ZhdGljYW4JVmVuZXp1ZWxhB1ZpZXRuYW0OVmlyZ2luIElzbGFuZHMRVmlyZ2luIElzbGFuZHMgVVMQV2FsbGlzIEZ1dHVuYSBJcw5XZXN0ZXJuIFNhaGFyYQVZZW1lbgpZdWdvc2xhdmlhBVphaXJlBlphbWJpYQhaaW1iYWJ3ZRXvAQADMDMyAzAzNgMxNTYDMzgwAzM5MgM0ODQDNTU0AzYyMAM3MjQDMjc2AzI1MAM2NDMDODI2Azg0MAMwMDQDMDA4AzAxMgMwMTYDMDIwAzAyNAM2NjADMDEwAzAyOAMwNTEDNTMzAzA0MAMwMzEDMDQ0AzA0OAMwNTADMDUyAzExMgMwNTYDMDg0AzIwNAMwNjADMDY0AzA2OAMwNzADMDcyAzA3NAMwNzYDMDg2AzA5NgMxMDADODU0AzEwOAMxMTYDMTIwAzEyNAMxMzIDMTM2AzE0MAMxNDgDMTUyAzE2MgMxNjYDMTcwAzE3NAMxNzgDMTg0AzE4OAMxOTEDMTkyAzE5NgMyMDMDMjA4AzI2MgMyMTIDMjE0AzYyNgMyMTgDODE4AzIyMgMyMjYDMjMyAzIzMwMyMzEDMjM0AzI0MgMyNDYDMjU0AzI1OAMyNjYDMjcwAzI2OAMyODgDMzAwAzMwNAMzMDgDMzEyAzMxNgMzMjADMzI0AzYyNAMzMjgDMzMyAzM0MAMzNDQDMzQ4AzM1MgMzNTYDMzYwAzM2NAMzNjgDMzcyAzM3NgMzODQDMzg4AzQwMAMzOTgDNDA0AzI5NgM0MTQDNDE3AzQxOAM0MjgDNDIyAzQyNgM0MzADNDM0AzQzOAM0NDADNDQyAzQ0NgM4MDcDNDUwAzQ1NAM0NTgDNDYyAzQ2NgM0NzADMjM4AzU4NAM0NzQDNDc4AzQ4MAMxNzUDNTgzAzQ5OAM0OTIDNDk2AzQ5OQM1MDADNTA0AzUwOAMxMDQDNTE2AzUyMAM1MjQDNTI4AzUzMAM1NDADNTU4AzU2MgM1NjYDNTcwAzU3NAM0MDgDNTgwAzU3OAM1MTIDNzQ0AzU4NgM1ODUDNTkxAzU5OAM2MDADNjA0AzYwOAM2MTIDNjE2AzYzMAM2MzQDNjM4AzY0MgM2NDYDMjM5AzY2MgM4ODIDNjc0AzY3OAM2ODIDNjg2AzY4OAM2OTADNjk0AzcwMgM3MDMDNzA1AzA5MAM3MDYDNzEwAzQxMAMxNDQDNjU0AzY1OQM2NjYDNjcwAzczNgM3NDADNzQ0Azc0OAM3NTIDNzU2Azc2MAMxNTgDNzYyAzgzNAM3NjQDNzY4Azc3MgM3NzYDNzgwAzc4OAM3OTIDNzk1Azc5NgM3OTgDODAwAzgwNAM3ODQDODU4AzU4MQM4NjADNTQ4AzMzNgM4NjIDNzA0AzA5MgM4NTADODc2AzczMgM4ODcDODkxAzE4MAM4OTQDNzE2FCsD7wFnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZxYBAglkAgkPDxYCHwZoZBYEAgEPEA8WAh8BBRBBbmV4YXIgc29saWNpdHVkZGRkZAIDDw8WAh8GaGRkAg4PZBYCAgEPDxYCHgtUaXBvVXN1YXJpbwspY2Nsc0Z1bmNpb25lcyt0aXBvX3VzdWFyaW8sIEFwcF9Db2RlLnhoanB2aXpvLCBWZXJzaW9uPTAuMC4wLjAsIEN1bHR1cmU9bmV1dHJhbCwgUHVibGljS2V5VG9rZW49bnVsbAFkFgJmD2QWAmYPZBYCAgMPZBYCZg9kFgJmD2QWBGYPZBYCAgEPPCsACQEADxYGHg1TZWxlY3RlZEluZGV4Zh4IRGF0YUtleXMWAB8tAgNkFgZmD2QWAgIBDw8WCB8BBQxJbmZvcm1hY2nDs24eCFRhYkluZGV4AQAAHgtDb21tYW5kTmFtZQUETW92ZR4PQ29tbWFuZEFyZ3VtZW50BQEwZGQCAQ9kFgICAQ8PFggfAQUQQ2FyZ2EgZWwgZmljaGVybx80AQAAHzUFBE1vdmUfNgUBMWRkAgIPZBYCAgEPDxYIHwEFCUNvbmZpcm1hch80AQAAHzUFBE1vdmUfNgUBMmRkAgEPZBYCZg9kFgQCAQ9kFgJmD2QWAmYPZBYGZg8WAh4FVGl0bGUFDEluZm9ybWFjacOzbmQCAQ8WAh83BRBDYXJnYSBlbCBmaWNoZXJvZAICDxYCHzcFCUNvbmZpcm1hcmQCAg9kFgJmD2QWBGYPZBYCAgEPDxYCHwEFCVNpZ3VpZW50ZWRkAgIPZBYEAgEPDxYCHwEFCEFudGVyaW9yZGQCAw8PFgIfAQUJQ29uZmlybWFyZGQCEA9kFgICAQ8WAh8GaGQCEg8PFgIfBmhkFgJmD2QWAgIBD2QWAmYPZBYCAgUPZBYEAhkPEGRkFgBkAh8PEGRkFgBkAhMPFgIfBmhkAhQPDxYCHwEFF3ZvbHZlciBhbCBwYXNvIGFudGVyaW9yZGQCFQ9kFgICAQ8PFgIfAQULSXIgYSBwYXNvIDRkZAIPD2QWBAIBDxYEHx4FCnN0ZXAtdGl0bGUfBmdkAgIPDxYCHwZoZBYQZg8WAh8GaBYCAgIPDxYCHwEFEENvbXByb2JhciBjdXDDs25kZAIBDxYCHwFlZAICDxYCHwZoZAIEDw8WAh8BBRd2b2x2ZXIgYWwgcGFzbyBhbnRlcmlvcmRkAgUPFgIfBmgWBgIBDw8WBB8BZR8GaGRkAgMPFgIfLmVkAgUPDxYCHwEFEUZpbmFsaXphciByZXNlcnZhZGQCBw8PFgQfAQUQRmluYWxpemFyIGNvbXByYR8GZ2RkAggPDxYCHwEFDlBob25lIGFuZCBTZWxsZGQCCQ8PFgIfAQUHUGF5R29sZGRkAhAPZBYCZg9kFghmDxYCHwEFKzxzdHJvbmc+U3UgY29tcHJhIGRlIGVudHJhZGFzPC9zdHJvbmc+IHBhcmFkAgEPFgIfAQUXVmlzaXRhIEFsaGFtYnJhIEdlbmVyYWxkAgIPFgIfAQXYAzxkaXYgY2xhc3M9J3Jlc3VsdCc+ICAgPGRpdiBjbGFzcz0nbS1iLTEyJz4gICAgICA8aSBjbGFzcz0naWNvbiBpY29uLXBlb3BsZSc+PC9pPiAgIDwvZGl2PiAgIDxkaXYgY2xhc3M9J20tYi0xMic+ICAgICAgPGkgY2xhc3M9J2ljb24gaWNvbi1kYXRlJz48L2k+ICAgICAgPHA+RmVjaGE6IDxiciAvPiAgICAgIDwvcD4gICA8L2Rpdj48L2Rpdj48ZGl2IGNsYXNzPSdwcml4LXRvdGFsIGJyZC1zdXAtMjAnPiAgIDxzcGFuIGNsYXNzPSd0aXR1bG9QcmVjaW9GaW5hbCc+VG90YWwgZW50cmFkYXM8L3NwYW4+PHN0cm9uZyBjbGFzcz0nY29udGVuaWRvUHJlY2lvRmluYWwnPjA8L3N0cm9uZz4gICA8c3BhbiBjbGFzcz0ndGl0dWxvUHJlY2lvRmluYWwgcHJlY2lvRmluYWwnPlByZWNpbyBmaW5hbDwvc3Bhbj48c3Ryb25nIGNsYXNzPSdjb250ZW5pZG9QcmVjaW9GaW5hbCBwcmVjaW9GaW5hbCc+MCwwMCDigqw8L3N0cm9uZz48L2Rpdj5kAgMPFgIfAWRkAhIPZBYEAgEPDxYCHwEFDkF2aXNvIGhvcmFyaW9zZGQCAw8PFgIfAQWiAVJlY3VlcmRlIHNlciA8Yj5wdW50dWFsPC9iPiBlbiBsYSBob3JhIHNlbGVjY2lvbmFkYSBhIGxvcyA8Yj5QYWxhY2lvcyBOYXphcsOtZXM8L2I+LiBSZXN0byBkZWwgbW9udW1lbnRvIGRlIDg6MzAgYSAxODowMCBob3JhcyBpbnZpZXJubzsgODozMCBhIDIwOjAwIGhvcmFzIHZlcmFub2RkAhMPZBYIAgEPDxYCHwEFH0F2aXNvIHNvYnJlIHZpc2l0YXMgY29uIG1lbm9yZXNkZAIDDw8WAh8BBfYBU2kgdmEgYSByZWFsaXphciBsYSB2aXNpdGEgY29uIG1lbm9yZXMgZGUgMyBhIDExIGHDsW9zLCDDqXN0b3MgcHJlY2lzYW4gZGUgc3UgZW50cmFkYSBjb3JyZXNwb25kaWVudGUuDQpQb3IgZmF2b3Igc2VsZWNjacOzbmVsYSBlbiBzdSBjb21wcmE6IExhcyBlbnRyYWRhcyBkZSBtZW5vcmVzIGRlIDMgYcOxb3Mgc2Vyw6FuIGZhY2lsaXRhZGFzIGVuIGxhcyB0YXF1aWxsYXMgZGVsIG1vbnVtZW50by4gwr9EZXNlYSBjb250aW51YXI/ZGQCBQ8PFgIfAQUCU2lkZAIHDw8WAh8BBQJOb2RkAhQPZBYEAgEPDxYCHwEFFkFWSVNPIERBVE9TIFZJU0lUQU5URVNkZAIDDw8WAh8BBVxDb21wcnVlYmUgcXVlIGxvcyBkYXRvcyBkZSB2aXNpdGFudGVzIHNvbiBjb3JyZWN0b3MsIGFzw60gY29tbyBsYSBmZWNoYSB5IGhvcmEgc2VsZWNjaW9uYWRhLmRkAgIPDxYCHwZoZGQCDg8WBB8BBb8dPGZvb3RlciBjbGFzcz0iZm9vdGVyIj4NCiAgPGRpdiBpZD0iZGl2Rm9vdGVyMiIgY2xhc3M9ImZvb3RlcjIiPg0KICAgIDxkaXYgY2xhc3M9ImNvbnRhaW5lciI+DQogICAgICA8ZGl2IGNsYXNzPSJsb2dvICI+DQogICAgICAgICAgPGEgaHJlZj0iaHR0cDovL3d3dy5hbGhhbWJyYS1wYXRyb25hdG8uZXMvIiB0YXJnZXQ9Il9ibGFuayI+PGltZyBpZD0iaW1nRm9vdGVyIiBzcmM9Ii9BcHBfVGhlbWVzL0FMSEFNQlJBL2ltZy9sb2dvLWZvb3Rlci5wbmciIGFsdD0iQWxoYW1icmEgeSBHZW5lcmFsaWZlIj48L2E+DQogICAgICAgIDwvZGl2Pg0KICAgICAgPGRpdiBjbGFzcz0icm93Ij4NCiAgICAgICAgIDxkaXYgY2xhc3M9ImZvb3Rlci1pdGVtIGNvbHVtbi0xIj4NCiAgICAgICAgICA8dWw+DQogICAgICAgICAgICA8bGk+PGEgY2xhc3M9ImxpbmtzLWl0ZW0iIGhyZWY9Imh0dHBzOi8vdGlja2V0cy5hbGhhbWJyYS1wYXRyb25hdG8uZXMvdGUtcHVlZGUtYXl1ZGFyLyIgdGFyZ2V0PSJfYmxhbmsiPkxFIFBVRURPIEFZVURBUjwvYT48L2xpPg0KICAgICAgICAgICAgPGxpPjxhIGNsYXNzPSJsaW5rcy1pdGVtIiBocmVmPSJodHRwczovL3RpY2tldHMuYWxoYW1icmEtcGF0cm9uYXRvLmVzL3BvbGl0aWNhLWRlLWNvbXByYS8iIHRhcmdldD0iX2JsYW5rIj5QT0zDjVRJQ0EgREUgQ09NUFJBUzwvYT48L2xpPg0KICAgICAgICAgICAgPGxpPjxhIGNsYXNzPSJsaW5rcy1pdGVtIiBocmVmPSIvcG9saXRpY2EtY29va2llcy5hc3B4IiB0YXJnZXQ9Il9ibGFuayI+UE9Mw41USUNBIERFIENPT0tJRVM8L2E+PC9saT4NCiAgICAgICAgICAgIDxsaT48YSBjbGFzcz0ibGlua3MtaXRlbSIgaHJlZj0iamF2YXNjcmlwdDp2b2lkKDApIiAgb25DbGljaz0iUmVjb25maWd1cmFyQ29va2llcygpIj5DYW5jZWxhciAvIGNvbmZpZ3VyYXIgcG9saXRpY2EgZGUgY29va2llczwvYT48L2xpPg0KICAgICAgICAgICAgPGxpPjxhIGNsYXNzPSJsaW5rcy1pdGVtIiBocmVmPSJodHRwczovL3RpY2tldHMuYWxoYW1icmEtcGF0cm9uYXRvLmVzL3BvbGl0aWNhLWRlLXByaXZhY2lkYWQiIHRhcmdldD0iX2JsYW5rIj5QT0zDjVRJQ0EgREUgUFJJVkFDSURBRDwvYT48L2xpPg0KICAgICAgICAgICAgPGxpPjxhIGNsYXNzPSJsaW5rcy1pdGVtIiBocmVmPSJodHRwczovL3RpY2tldHMuYWxoYW1icmEtcGF0cm9uYXRvLmVzL2F2aXNvLWxlZ2FsLyIgdGFyZ2V0PSJfYmxhbmsiPkFWSVNPIExFR0FMPC9hPjwvbGk+DQogICAgICAgICAgICA8bGk+PHAgY2xhc3M9ImxpbmtzLWl0ZW0iPlRFTMOJRk9OTyBERUwgVklTSVRBTlRFIDxhIGhyZWY9InRlbDorMzQ4NTg4ODkwMDIiIGNsYXNzPSJ0ZWwiPiszNCA5NTggMDI3IDk3MTwvYT48L3A+PC9saT4NCiAgICAgICAgICAgIDxsaT48cCBjbGFzcz0ibGlua3MtaXRlbSI+VEVMw4lGT05PIERFIFNPUE9SVEUgQSBMQSBWRU5UQSBERSBFTlRSQURBUyA8YSBocmVmPSJ0ZWw6KzM0ODU4ODg5MDAyIiBjbGFzcz0idGVsIj4rMzQ4NTg4ODkwMDI8L2E+PC9wPjwvbGk+DQo8bGk+PHAgY2xhc3M9ImxpbmtzLWl0ZW0iPkNPUlJFTyBFTEVDVFLDk05JQ08gREUgU09QT1JURSBBIExBIFZFTlRBIERFIEVOVFJBREFTIDxhIGhyZWY9Im1haWx0bzp0aWNrZXRzLmFsaGFtYnJhQGlhY3Bvcy5jb20iIGNsYXNzPSJ0ZWwiPnRpY2tldHMuYWxoYW1icmFAaWFjcG9zLmNvbTwvYT48L3A+PC9saT4NCiAgICAgICAgICA8L3VsPg0KICAgICAgICAgPC9kaXY+DQogICAgICA8L2Rpdj4NCiAgICAgIDwhLS0gQ29udGFjdG8geSBSUlNTIC0tPg0KICAgICAgPGRpdiBjbGFzcz0iZm9vdGVyNCI+DQogICAgICAgIDxkaXYgY2xhc3M9ImZvbGxvdyI+DQogICAgICAgICAgPHA+U8OtZ3Vlbm9zIGVuOjwvcD4NCiAgICAgICAgICA8dWwgY2xhc3M9InNvY2lhbCI+DQogICAgICAgICAgICA8bGkgaWQ9ImxpRmFjZWJvb2siPg0KICAgICAgICAgICAgICA8YSBpZD0ibGlua0ZhY2Vib29rIiBjbGFzcz0iaWNvbiBpY29uLWZhY2Vib29rIiB0aXRsZT0iRmFjZWJvb2siIGhyZWY9Imh0dHBzOi8vd3d3LmZhY2Vib29rLmNvbS9hbGhhbWJyYWN1bHR1cmEiIHRhcmdldD0iX2JsYW5rIj48L2E+DQogICAgICAgICAgICA8L2xpPg0KICAgICAgICAgICAgPGxpIGlkPSJsaVR3aXRlciI+DQogICAgICAgICAgICAgIDxhIGlkPSJsaW5rVHdpdHRlciIgY2xhc3M9Imljb24gaWNvbi10d2l0dGVyIiB0aXRsZT0iVHdpdHRlciIgaHJlZj0iaHR0cDovL3d3dy50d2l0dGVyLmNvbS9hbGhhbWJyYWN1bHR1cmEiIHRhcmdldD0iX2JsYW5rIj48L2E+DQogICAgICAgICAgICA8L2xpPg0KICAgICAgICAgICAgPGxpIGlkPSJsaVlvdVR1YmUiPg0KICAgICAgICAgICAgICA8YSBpZD0ibGlua1lvdVR1YmUiIGNsYXNzPSJpY29uIGljb24teW91dHViZSIgdGl0bGU9IllvdXR1YmUiIGhyZWY9Imh0dHA6Ly93d3cueW91dHViZS5jb20vYWxoYW1icmFwYXRyb25hdG8iIHRhcmdldD0iX2JsYW5rIj48L2E+DQogICAgICAgICAgICA8L2xpPg0KICAgICAgICAgICAgPGxpIGlkPSJsaUluc3RhZ3JhbSI+DQogICAgICAgICAgICAgIDxhIGlkPSJsaW5rSW50YWdyYW0iIGNsYXNzPSJpY29uIGljb24taW5zdGFncmFtIiB0aXRsZT0iSW5zdGFncmFtIiBocmVmPSJodHRwczovL3d3dy5pbnN0YWdyYW0uY29tL2FsaGFtYnJhX29maWNpYWwvIiB0YXJnZXQ9Il9ibGFuayI+PC9hPg0KICAgICAgICAgICAgPC9saT4NCiAgICAgICAgICAgIDxsaSBpZD0ibGlQaW50ZXJlc3QiPg0KICAgICAgICAgICAgICA8YSBpZD0ibGlua1BpbnRlcmVzdCIgY2xhc3M9Imljb24gaWNvbi1waW50ZXJlc3QiIHRpdGxlPSJQaW50ZXJlc3QiIGhyZWY9Imh0dHBzOi8vZXMucGludGVyZXN0LmNvbS9hbGhhbWJyYWdyYW5hZGEvIiB0YXJnZXQ9Il9ibGFuayI+PC9hPg0KICAgICAgICAgICAgPC9saT4NCiAgICAgICAgICA8L3VsPg0KICAgICAgICA8L2Rpdj4NCiAgICAgICAgPCEtLSAvL0NvbnRhY3RvIHkgUlJTUyAtLT4NCiAgICAgIDwvZGl2Pg0KICAgIDwvZGl2Pg0KICA8L2Rpdj4NCiAgPGRpdiBpZD0iZGl2Rm9vdGVyMyIgY2xhc3M9ImZvb3RlcjMiPg0KICAgIDxkaXYgY2xhc3M9ImNvbnRhaW5lciI+DQogICAgICA8ZGl2IGNsYXNzPSJmb290ZXItaXRlbSBjb2x1bW4tMSI+DQogICAgICAgIDxkaXYgY2xhc3M9ImxvZ28gbG9nb0Zvb3RlciI+DQogICAgICAgICAgPGEgaHJlZj0iaHR0cDovL3d3dy5hbGhhbWJyYS1wYXRyb25hdG8uZXMvIiB0YXJnZXQ9Il9ibGFuayI+DQogICAgICAgICAgICA8aW1nIGlkPSJpbWdGb290ZXIiIHNyYz0iL0FwcF9UaGVtZXMvQUxIQU1CUkEvaW1nL2xvZ29fcGF0cm9uYXRvLnBuZyIgYWx0PSJBbGhhbWJyYSB5IEdlbmVyYWxpZmUiPg0KICAgICAgICAgIDwvYT4NCiAgICAgIDwvZGl2Pg0KICAgICAgICA8cCBjbGFzcz0iZGVzaWduIj4NCiAgICAgICAgICA8c3BhbiBpZD0iZGV2ZWxvcGVkIj5Db3B5cmlnaHQgwqkgSUFDUE9TPC9zcGFuPg0KICAgICAgICA8L3A+DQogICAgICA8L2Rpdj4NCiAgICAgIDxkaXYgaWQ9ImRpdkRpcmVjY2lvbkZvb3RlciIgY2xhc3M9ImRpcmVjY2lvbiBmb290ZXItaXRlbSBjb2x1bW4tMSI+DQogICAgICAgIDxwPlBhdHJvbmF0byBkZSBsYSBBbGhhbWJyYSB5IEdlbmVyYWxpZmU8L3A+DQogICAgICAgICAgICAgICAgICAgIDxwPkMvIFJlYWwgZGUgbGEgQWxoYW1icmEgcy9uPC9wPg0KICAgICAgICAgICAgICAgICAgICA8cD5DUCAtIDE4MDA5IChHcmFuYWRhKTwvcD4NCiAgICAgIDwvZGl2Pg0KICAgIDwvZGl2Pg0KICA8L2Rpdj4NCjwvZm9vdGVyPh8GZ2QCDw8WAh8GaBYUAgIPZBYKAgEPZBYCAgEPDxYCHwMFKGh0dHBzOi8vd3d3LmZhY2Vib29rLmNvbS9hbGhhbWJyYWN1bHR1cmFkZAICD2QWAgIBDw8WAh8DBSZodHRwOi8vd3d3LnR3aXR0ZXIuY29tL2FsaGFtYnJhY3VsdHVyYWRkAgMPZBYCAgEPDxYCHwMFKGh0dHA6Ly93d3cueW91dHViZS5jb20vYWxoYW1icmFwYXRyb25hdG9kZAIED2QWAgIBDw8WAh8DBStodHRwczovL3d3dy5pbnN0YWdyYW0uY29tL2FsaGFtYnJhX29maWNpYWwvZGQCBQ9kFgICAQ8PFgIfAwUpaHR0cHM6Ly9lcy5waW50ZXJlc3QuY29tL2FsaGFtYnJhZ3JhbmFkYS9kZAIDD2QWBgIBD2QWAmYPDxYEHwQFKC9BcHBfVGhlbWVzL0FMSEFNQlJBL2ltZy9sb2dvLWZvb3Rlci5wbmcfBQUVQWxoYW1icmEgeSBHZW5lcmFsaWZlZGQCAw8WAh8HBZQBPHA+UGF0cm9uYXRvIGRlIGxhIEFsaGFtYnJhIHkgR2VuZXJhbGlmZTwvcD4NCiAgICAgICAgICAgICAgICAgICAgPHA+Qy8gUmVhbCBkZSBsYSBBbGhhbWJyYSBzL248L3A+DQogICAgICAgICAgICAgICAgICAgIDxwPkNQIC0gMTgwMDkgKEdyYW5hZGEpPC9wPmQCBQ8PFgIfAQUTQ29weXJpZ2h0IMKpIElBQ1BPU2RkAgQPDxYCHwMFKGh0dHBzOi8vd3d3LmZhY2Vib29rLmNvbS9hbGhhbWJyYWN1bHR1cmFkZAIFDw8WAh8DBSZodHRwOi8vd3d3LnR3aXR0ZXIuY29tL2FsaGFtYnJhY3VsdHVyYWRkAgYPDxYCHwMFK2h0dHBzOi8vd3d3Lmluc3RhZ3JhbS5jb20vYWxoYW1icmFfb2ZpY2lhbC9kZAIHDw8WAh8DBShodHRwOi8vd3d3LnlvdXR1YmUuY29tL2FsaGFtYnJhcGF0cm9uYXRvZGQCCA8PFgIfA2RkZAIJDw8WAh8DZGRkAgoPFgIfBwWUATxwPlBhdHJvbmF0byBkZSBsYSBBbGhhbWJyYSB5IEdlbmVyYWxpZmU8L3A+DQogICAgICAgICAgICAgICAgICAgIDxwPkMvIFJlYWwgZGUgbGEgQWxoYW1icmEgcy9uPC9wPg0KICAgICAgICAgICAgICAgICAgICA8cD5DUCAtIDE4MDA5IChHcmFuYWRhKTwvcD5kAgsPDxYCHwEFE0NvcHlyaWdodCDCqSBJQUNQT1NkZAIRDw8WAh8GaGQWBAIBD2QWBAIBDxYCHwEFxwQ8cCA+RWwgcmVzcG9uc2FibGUgZGUgZXN0ZSBzaXRpbyB3ZWIgZmlndXJhIGVuIG51ZXN0cm8gIDxhIGhyZWY9Imh0dHBzOi8vdGlja2V0cy5hbGhhbWJyYS1wYXRyb25hdG8uZXMvYXZpc28tbGVnYWwvIiA+QXZpc28gTGVnYWwgPC9hID4uIDxiciAvID5VdGlsaXphbW9zIGNvb2tpZXMgcHJvcGlhcyB5IG9wY2lvbmFsbWVudGUgcG9kZW1vcyB1dGlsaXphciBjb29raWVzIGRlIHRlcmNlcm9zLiBMYSBmaW5hbGlkYWQgZGUgbGFzIGNvb2tpZXMgdXRpbGl6YWRhcyBlczogZnVuY2lvbmFsZXMsIGFuYWzDrXRpY2FzIHkgcHVibGljaXRhcmlhcy4gTm8gc2UgdXNhbiBwYXJhIGxhIGVsYWJvcmFjacOzbiBkZSBwZXJmaWxlcy4gVXN0ZWQgcHVlZGUgY29uZmlndXJhciBlbCB1c28gZGUgY29va2llcyBlbiBlc3RlIG1lbnUuIDxiciAvID5QdWVkZSBvYnRlbmVyIG3DoXMgaW5mb3JtYWNpw7NuLCBvIGJpZW4gY29ub2NlciBjw7NtbyBjYW1iaWFyIGxhIGNvbmZpZ3VyYWNpw7NuLCBlbiBudWVzdHJhIDxiciAvID4gPGEgaHJlZj0iL3BvbGl0aWNhLWNvb2tpZXMuYXNweCIgPlBvbMOtdGljYSBkZSBjb29raWVzIDwvYSA+LjwvcCA+ZAIDDw8WAh8BBRhBY2VwdGFyIHRvZG8geSBjb250aW51YXJkZAIDD2QWCAIBDw8WAh8GaGRkAgMPFgIfAQXHBDxwID5FbCByZXNwb25zYWJsZSBkZSBlc3RlIHNpdGlvIHdlYiBmaWd1cmEgZW4gbnVlc3RybyAgPGEgaHJlZj0iaHR0cHM6Ly90aWNrZXRzLmFsaGFtYnJhLXBhdHJvbmF0by5lcy9hdmlzby1sZWdhbC8iID5BdmlzbyBMZWdhbCA8L2EgPi48YnIgLyA+IFV0aWxpemFtb3MgY29va2llcyBwcm9waWFzIHkgb3BjaW9uYWxtZW50ZSBwb2RlbW9zIHV0aWxpemFyIGNvb2tpZXMgZGUgdGVyY2Vyb3MuIExhIGZpbmFsaWRhZCBkZSBsYXMgY29va2llcyB1dGlsaXphZGFzIGVzOiBmdW5jaW9uYWxlcywgYW5hbMOtdGljYXMgeSBwdWJsaWNpdGFyaWFzLiBObyBzZSB1c2FuIHBhcmEgbGEgZWxhYm9yYWNpw7NuIGRlIHBlcmZpbGVzLiBVc3RlZCBwdWVkZSBjb25maWd1cmFyIGVsIHVzbyBkZSBjb29raWVzIGVuIGVzdGUgbWVudS4gPGJyIC8gPlB1ZWRlIG9idGVuZXIgbcOhcyBpbmZvcm1hY2nDs24sIG8gYmllbiBjb25vY2VyIGPDs21vIGNhbWJpYXIgbGEgY29uZmlndXJhY2nDs24sIGVuIG51ZXN0cmEgPGJyIC8gPiA8YSBocmVmPSIvcG9saXRpY2EtY29va2llcy5hc3B4IiA+UG9sw610aWNhIGRlIGNvb2tpZXMgPC9hID4uPC9wID5kAgcPDxYCHwEFGEFjZXB0YXIgdG9kbyB5IGNvbnRpbnVhcmRkAgkPDxYCHwEFIEFjZXB0YXIgc2VsZWNjaW9uYWRvIHkgY29udGludWFyZGQCAw8WBB8BBeIBPCEtLSBTdGFydCBvZiBjYXVhbGhhbWJyYSBaZW5kZXNrIFdpZGdldCBzY3JpcHQgLS0+DQo8c2NyaXB0IGlkPSJ6ZS1zbmlwcGV0IiBzcmM9aHR0cHM6Ly9zdGF0aWMuemRhc3NldHMuY29tL2Vrci9zbmlwcGV0LmpzP2tleT01YjdhZTEyOS05YTNjLTRkMmYtYjk0NC0xNDcyZGY5ZmI1MzM+IDwvc2NyaXB0Pg0KPCEtLSBFbmQgb2YgY2F1YWxoYW1icmEgWmVuZGVzayBXaWRnZXQgc2NyaXB0IC0tPh8GZ2QYAwUeX19Db250cm9sc1JlcXVpcmVQb3N0QmFja0tleV9fFgEFH2N0bDAwJGNoa1JlZ2lzdHJvQWNlcHRvUG9saXRpY2EFR2N0bDAwJENvbnRlbnRNYXN0ZXIxJHVjUmVzZXJ2YXJFbnRyYWRhc0Jhc2VBbGhhbWJyYTEkdWNJbXBvcnRhciRXaXphcmQxDxBkFCsBAWZmZAVXY3RsMDAkQ29udGVudE1hc3RlcjEkdWNSZXNlcnZhckVudHJhZGFzQmFzZUFsaGFtYnJhMSR1Y0ltcG9ydGFyJFdpemFyZDEkV2l6YXJkTXVsdGlWaWV3Dw9kZmRqUeGC771nXDjqOfYiFHoMzE1r2Q=="
            driver.execute_script(
                f"document.getElementById('__VIEWSTATE').value = `{viewstate_funcional}`;"
            )

            # time.sleep(TIEMPO)

            # 4. Hacer clic de nuevo en el mismo botón
            boton = WebDriverWait(driver, 2).until(
                EC.element_to_be_clickable(
                    (By.ID, "ctl00_ContentMaster1_ucReservarEntradasBaseAlhambra1_btnIrPaso1")
                )
            )
            boton.click()

            dias_tachados_inicial = obtener_dias_tachados_completos(driver, 1)
            if dias_tachados_inicial:
                break

            driver.refresh()
            time.sleep(random.uniform(5, 7))  # Pausa para simular comportamiento humano o evitar bloqueos

        guardar_dias_tachados(dias_tachados_inicial)

    print(f"Días tachados inicialmente: {dias_tachados_inicial}")
    logging.info(f"Días tachados inicialmente: {dias_tachados_inicial}")

    counter = 1
    counter_diasTachados = 1

    try:
        while not DETENER:
            viewState = 0

            icon.icon = crear_icono_verde()

            print(f"\n Intento #{counter}")
            logging.info(f"\n Intento #{counter}")

            counter += 1

            driver.refresh()

            try:
                boton = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable(
                        (By.ID, "ctl00_ContentMaster1_ucReservarEntradasBaseAlhambra1_btnIrPaso1"))
                )
                driver.execute_script("arguments[0].click();", boton)
                print("Botón 'Paso 1' pulsado.")
                time.sleep(TIEMPO)

                # Verificamos que el calendario ha cargado
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.ID,
                                                    "ctl00_ContentMaster1_ucReservarEntradasBaseAlhambra1_ucCalendarioPaso1_calendarioFecha"))
                )

                FALLOS_SEGUIDOS = 0  # reiniciar contador
            except Exception as e:
                print(f" Fallo al ir a Paso 1: {e}")
                logging.info(f" Fallo al ir a Paso 1: {e}")

                FALLOS_SEGUIDOS += 1
                viewState = 1

                # 3. Reemplazar manualmente el valor de __VIEWSTATE con el que tú sabes que funciona
                viewstate_funcional = "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OTUyZxAFBDE5NTMFBDE5NTNnEAUEMTk1NAUEMTk1NGcQBQQxOTU1BQQxOTU1ZxAFBDE5NTYFBDE5NTZnEAUEMTk1NwUEMTk1N2cQBQQxOTU4BQQxOTU4ZxAFBDE5NTkFBDE5NTlnEAUEMTk2MAUEMTk2MGcQBQQxOTYxBQQxOTYxZxAFBDE5NjIFBDE5NjJnEAUEMTk2MwUEMTk2M2cQBQQxOTY0BQQxOTY0ZxAFBDE5NjUFBDE5NjVnEAUEMTk2NgUEMTk2NmcQBQQxOTY3BQQxOTY3ZxAFBDE5NjgFBDE5NjhnEAUEMTk2OQUEMTk2OWcQBQQxOTcwBQQxOTcwZxAFBDE5NzEFBDE5NzFnEAUEMTk3MgUEMTk3MmcQBQQxOTczBQQxOTczZxAFBDE5NzQFBDE5NzRnEAUEMTk3NQUEMTk3NWcQBQQxOTc2BQQxOTc2ZxAFBDE5NzcFBDE5NzdnEAUEMTk3OAUEMTk3OGcQBQQxOTc5BQQxOTc5ZxAFBDE5ODAFBDE5ODBnEAUEMTk4MQUEMTk4MWcQBQQxOTgyBQQxOTgyZxAFBDE5ODMFBDE5ODNnEAUEMTk4NAUEMTk4NGcQBQQxOTg1BQQxOTg1ZxAFBDE5ODYFBDE5ODZnEAUEMTk4NwUEMTk4N2cQBQQxOTg4BQQxOTg4ZxAFBDE5ODkFBDE5ODlnEAUEMTk5MAUEMTk5MGcQBQQxOTkxBQQxOTkxZxAFBDE5OTIFBDE5OTJnEAUEMTk5MwUEMTk5M2cQBQQxOTk0BQQxOTk0ZxAFBDE5OTUFBDE5OTVnEAUEMTk5NgUEMTk5NmcQBQQxOTk3BQQxOTk3ZxAFBDE5OTgFBDE5OThnEAUEMTk5OQUEMTk5OWcQBQQyMDAwBQQyMDAwZxAFBDIwMDEFBDIwMDFnEAUEMjAwMgUEMjAwMmcQBQQyMDAzBQQyMDAzZxAFBDIwMDQFBDIwMDRnEAUEMjAwNQUEMjAwNWcQBQQyMDA2BQQyMDA2ZxAFBDIwMDcFBDIwMDdnEAUEMjAwOAUEMjAwOGcQBQQyMDA5BQQyMDA5ZxAFBDIwMTAFBDIwMTBnEAUEMjAxMQUEMjAxMWcQBQQyMDEyBQQyMDEyZxAFBDIwMTMFBDIwMTNnEAUEMjAxNAUEMjAxNGcQBQQyMDE1BQQyMDE1ZxAFBDIwMTYFBDIwMTZnEAUEMjAxNwUEMjAxN2cQBQQyMDE4BQQyMDE4ZxAFBDIwMTkFBDIwMTlnEAUEMjAyMAUEMjAyMGcQBQQyMDIxBQQyMDIxZxAFBDIwMjIFBDIwMjJnEAUEMjAyMwUEMjAyM2cQBQQyMDI0BQQyMDI0ZxAFBDIwMjUFBDIwMjVnFgFmZAILDxYCHwZoFgICAQ8WAh8HZGQCDA9kFgICAQ8WAh8HBQVFbWFpbGQCDQ9kFgICAQ8WAh8HBQ5Db25maXJtYSBFbWFpbGQCDg9kFgICAQ8WAh8HBQtDb250cmFzZcOxYWQCDw9kFgICAQ8WAh8HBRNSZXBldGlyIENvbnRyYXNlw7FhZAIQDxYCHwZoFgICAQ8WAh8HZWQCEQ8WAh8GaBYCAgEPFgIfB2VkAhIPFgIfBmgWAgIBDxYCHwdlZAITDxYCHwZoFgYCAQ8WAh8HZWQCAw8PFgQeCENzc0NsYXNzBRJpbnB1dC10ZXh0IG9jdWx0YXIeBF8hU0ICAmRkAgUPEA8WBB8JZR8KAgJkEBU1FFNlbGVjY2lvbmUgcHJvdmluY2lhCEFsYmFjZXRlCEFsaWNhbnRlCEFsbWVyw61hBsOBbGF2YQhBc3R1cmlhcwbDgXZpbGEHQmFkYWpveg1CYWxlYXJzIElsbGVzCUJhcmNlbG9uYQdCaXprYWlhBkJ1cmdvcwhDw6FjZXJlcwZDw6FkaXoJQ2FudGFicmlhCkNhc3RlbGzDs24LQ2l1ZGFkIFJlYWwIQ8OzcmRvYmEJQ29ydcOxYSBBBkN1ZW5jYQhHaXB1emtvYQZHaXJvbmEHR3JhbmFkYQtHdWFkYWxhamFyYQZIdWVsdmEGSHVlc2NhBUphw6luBUxlw7NuBkxsZWlkYQRMdWdvBk1hZHJpZAdNw6FsYWdhBk11cmNpYQdOYXZhcnJhB091cmVuc2UIUGFsZW5jaWEKUGFsbWFzIExhcwpQb250ZXZlZHJhCFJpb2phIExhCVNhbGFtYW5jYRZTYW50YSBDcnV6IGRlIFRlbmVyaWZlB1NlZ292aWEHU2V2aWxsYQVTb3JpYQlUYXJyYWdvbmEGVGVydWVsBlRvbGVkbwhWYWxlbmNpYQpWYWxsYWRvbGlkBlphbW9yYQhaYXJhZ296YQVDZXV0YQdNZWxpbGxhFTUAAjAyAjAzAjA0AjAxAjMzAjA1AjA2AjA3AjA4AjQ4AjA5AjEwAjExAjM5AjEyAjEzAjE0AjE1AjE2AjIwAjE3AjE4AjE5AjIxAjIyAjIzAjI0AjI1AjI3AjI4AjI5AjMwAjMxAjMyAjM0AjM1AjM2AjI2AjM3AjM4AjQwAjQxAjQyAjQzAjQ0AjQ1AjQ2AjQ3AjQ5AjUwAjUxAjUyFCsDNWdnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnFgFmZAIUD2QWBgIBDxYCHwcFBVBhw61zZAIDDw8WAh8GaGRkAgUPEGQQFe8BE1NlbGVjY2lvbmUgdW4gcGHDrXMJQXJnZW50aW5hCUF1c3RyYWxpYQVDaGluYQVJdGFseQVKYXBhbgZNZXhpY28LTmV3IFplYWxhbmQIUG9ydHVnYWwHRXNwYcOxYQdHZXJtYW55BkZyYW5jZRJSdXNzaWFuIEZlZGVyYXRpb24OVW5pdGVkIEtpbmdkb20UVW5pdGVkIFN0YXRlcyBvZiBBbWULQWZnaGFuaXN0YW4HQWxiYW5pYQdBbGdlcmlhDkFtZXJpY2FuIFNhbW9hB0FuZG9ycmEGQW5nb2xhCEFuZ3VpbGxhCkFudGFyY3RpY2EHQW50aWd1YQdBcm1lbmlhBUFydWJhB0F1c3RyaWEKQXplcmJhaWphbgdCYWhhbWFzB0JhaHJhaW4KQmFuZ2xhZGVzaAhCYXJiYWRvcwdCZWxhcnVzB0JlbGdpdW0GQmVsaXplBUJlbmluB0Jlcm11ZGEGQmh1dGFuB0JvbGl2aWEGQm9zbmlhCEJvdHN3YW5hDUJvdXZldCBJc2xhbmQGQnJhemlsDkJyaXRpc2ggSW5kaWFuEUJydW5laSBEYXJ1c3NhbGFtCEJ1bGdhcmlhDEJ1cmtpbmEgRmFzbwdCdXJ1bmRpCENhbWJvZGlhCENhbWVyb29uBkNhbmFkYQpDYXBlIFZlcmRlDkNheW1hbiBJc2xhbmRzE0NlbnRyYWwgQWZyaWNhbiBSZXAEQ2hhZAVDaGlsZRBDaHJpc3RtYXMgSXNsYW5kDUNvY29zIElzbGFuZHMIQ29sb21iaWEHQ29tb3JvcwVDb25nbwxDb29rIElzbGFuZHMKQ29zdGEgUmljYQdDcm9hdGlhBEN1YmEGQ3lwcnVzDkN6ZWNoIFJlcHVibGljB0Rlbm1hcmsIRGppYm91dGkIRG9taW5pY2ESRG9taW5pY2FuIFJlcHVibGljCkVhc3QgVGltb3IHRWN1YWRvcgVFZ3lwdAtFbCBTYWx2YWRvchFFcXVhdG9yaWFsIEd1aW5lYQdFcml0cmVhB0VzdG9uaWEIRXRoaW9waWENRmFyb2UgSXNsYW5kcwRGaWppB0ZpbmxhbmQNRnJlbmNoIEd1aWFuYRBGcmVuY2ggUG9seW5lc2lhBUdhYm9uBkdhbWJpYQdHZW9yZ2lhBUdoYW5hBkdyZWVjZQlHcmVlbmxhbmQHR3JlbmFkYQpHdWFkZWxvdXBlBEd1YW0JR3VhdGVtYWxhBkd1aW5lYQ1HdWluZWEgQmlzc2F1Bkd1eWFuYQVIYWl0aQhIb25kdXJhcwlIb25nIEtvbmcHSHVuZ2FyeQdJY2VsYW5kBUluZGlhCUluZG9uZXNpYQRJcmFuBElyYXEHSXJlbGFuZAZJc3JhZWwLSXZvcnkgQ29hc3QHSmFtYWljYQZKb3JkYW4KS2F6YWtoc3RhbgVLZW55YQhLaXJpYmF0aQZLdXdhaXQKS3lyZ3l6c3RhbgNMYW8GTGF0dmlhB0xlYmFub24HTGVzb3RobwdMaWJlcmlhBUxpYnlhDUxpZWNodGVuc3RlaW4JTGl0aHVhbmlhCkx1eGVtYm91cmcFTWFjYXUJTWFjZWRvbmlhCk1hZGFnYXNjYXIGTWFsYXdpCE1hbGF5c2lhCE1hbGRpdmVzBE1hbGkFTWFsdGEITWFsdmluYXMQTWFyc2hhbGwgSXNsYW5kcwpNYXJ0aW5pcXVlCk1hdXJpdGFuaWEJTWF1cml0aXVzB01heW90dGUKTWljcm9uZXNpYQdNb2xkb3ZhBk1vbmFjbwhNb25nb2xpYQpNb250ZW5lZ3JvCk1vbnRzZXJyYXQHTW9yb2NjbwpNb3phbWJpcXVlB015YW5tYXIHTmFtaWJpYQVOYXVydQVOZXBhbAtOZXRoZXJsYW5kcxROZXRoZXJsYW5kcyBBbnRpbGxlcw1OZXcgQ2FsZWRvbmlhCU5pY2FyYWd1YQVOaWdlcgdOaWdlcmlhBE5pdWUOTm9yZm9sayBJc2xhbmQLTm9ydGggS29yZWETTm9ydGhlcm4gTWFyaWFuYSBJcwZOb3J3YXkET21hbhlPdHJvcyBkZSBwYWlzZXMgZGVsIG11bmRvCFBha2lzdGFuBVBhbGF1BlBhbmFtYRBQYXB1YSBOZXcgR3VpbmVhCFBhcmFndWF5BFBlcnULUGhpbGlwcGluZXMIUGl0Y2Fpcm4GUG9sYW5kC1B1ZXJ0byBSaWNvBVFhdGFyB1JldW5pb24HUm9tYW5pYQZSd2FuZGEPUyBHZW9yZ2lhIFNvdXRoC1NhaW50IEx1Y2lhBVNhbW9hClNhbiBNYXJpbm8TU2FvIFRvbWUgLSBQcmluY2lwZQxTYXVkaSBBcmFiaWEHU2VuZWdhbAZTZXJiaWEKU2V5Y2hlbGxlcwxTaWVycmEgTGVvbmUJU2luZ2Fwb3JlCFNsb3Zha2lhCFNsb3ZlbmlhD1NvbG9tb24gSXNsYW5kcwdTb21hbGlhDFNvdXRoIEFmcmljYQtTb3V0aCBLb3JlYQlTcmkgTGFua2EJU3QgSGVsZW5hElN0IEtpdHRzIGFuZCBOZXZpcxNTdCBQaWVycmUgIE1pcXVlbG9uEVN0IFZpbmNlbnQtR3JlbmFkBVN1ZGFuCFN1cmluYW1lEVN2YWxiYXJkIEphbiBNIElzCVN3YXppbGFuZAZTd2VkZW4LU3dpdHplcmxhbmQFU3lyaWEGVGFpd2FuClRhamlraXN0YW4IVGFuemFuaWEIVGhhaWxhbmQEVG9nbwdUb2tlbGF1BVRvbmdhE1RyaW5pZGFkIEFuZCBUb2JhZ28HVHVuaXNpYQZUdXJrZXkMVHVya21lbmlzdGFuFFR1cmtzIENhaWNvcyBJc2xhbmRzBlR1dmFsdQZVZ2FuZGEHVWtyYWluZRRVbml0ZWQgQXJhYiBFbWlyYXRlcwdVcnVndWF5EFVTIE1pbm9yIElzbGFuZHMKVXpiZWtpc3RhbgdWYW51YXR1B1ZhdGljYW4JVmVuZXp1ZWxhB1ZpZXRuYW0OVmlyZ2luIElzbGFuZHMRVmlyZ2luIElzbGFuZHMgVVMQV2FsbGlzIEZ1dHVuYSBJcw5XZXN0ZXJuIFNhaGFyYQVZZW1lbgpZdWdvc2xhdmlhBVphaXJlBlphbWJpYQhaaW1iYWJ3ZRXvAQADMDMyAzAzNgMxNTYDMzgwAzM5MgM0ODQDNTU0AzYyMAM3MjQDMjc2AzI1MAM2NDMDODI2Azg0MAMwMDQDMDA4AzAxMgMwMTYDMDIwAzAyNAM2NjADMDEwAzAyOAMwNTEDNTMzAzA0MAMwMzEDMDQ0AzA0OAMwNTADMDUyAzExMgMwNTYDMDg0AzIwNAMwNjADMDY0AzA2OAMwNzADMDcyAzA3NAMwNzYDMDg2AzA5NgMxMDADODU0AzEwOAMxMTYDMTIwAzEyNAMxMzIDMTM2AzE0MAMxNDgDMTUyAzE2MgMxNjYDMTcwAzE3NAMxNzgDMTg0AzE4OAMxOTEDMTkyAzE5NgMyMDMDMjA4AzI2MgMyMTIDMjE0AzYyNgMyMTgDODE4AzIyMgMyMjYDMjMyAzIzMwMyMzEDMjM0AzI0MgMyNDYDMjU0AzI1OAMyNjYDMjcwAzI2OAMyODgDMzAwAzMwNAMzMDgDMzEyAzMxNgMzMjADMzI0AzYyNAMzMjgDMzMyAzM0MAMzNDQDMzQ4AzM1MgMzNTYDMzYwAzM2NAMzNjgDMzcyAzM3NgMzODQDMzg4AzQwMAMzOTgDNDA0AzI5NgM0MTQDNDE3AzQxOAM0MjgDNDIyAzQyNgM0MzADNDM0AzQzOAM0NDADNDQyAzQ0NgM4MDcDNDUwAzQ1NAM0NTgDNDYyAzQ2NgM0NzADMjM4AzU4NAM0NzQDNDc4AzQ4MAMxNzUDNTgzAzQ5OAM0OTIDNDk2AzQ5OQM1MDADNTA0AzUwOAMxMDQDNTE2AzUyMAM1MjQDNTI4AzUzMAM1NDADNTU4AzU2MgM1NjYDNTcwAzU3NAM0MDgDNTgwAzU3OAM1MTIDNzQ0AzU4NgM1ODUDNTkxAzU5OAM2MDADNjA0AzYwOAM2MTIDNjE2AzYzMAM2MzQDNjM4AzY0MgM2NDYDMjM5AzY2MgM4ODIDNjc0AzY3OAM2ODIDNjg2AzY4OAM2OTADNjk0AzcwMgM3MDMDNzA1AzA5MAM3MDYDNzEwAzQxMAMxNDQDNjU0AzY1OQM2NjYDNjcwAzczNgM3NDADNzQ0Azc0OAM3NTIDNzU2Azc2MAMxNTgDNzYyAzgzNAM3NjQDNzY4Azc3MgM3NzYDNzgwAzc4OAM3OTIDNzk1Azc5NgM3OTgDODAwAzgwNAM3ODQDODU4AzU4MQM4NjADNTQ4AzMzNgM4NjIDNzA0AzA5MgM4NTADODc2AzczMgM4ODcDODkxAzE4MAM4OTQDNzE2FCsD7wFnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2RkAhUPZBYCAgEPFgIfBwUJVGVsw6lmb25vZAIXD2QWAgIDDxYCHwcFiQFIZSBsZcOtZG8geSBhY2VwdG8gbGEgPGEgaHJlZj0iaHR0cHM6Ly90aWNrZXRzLmFsaGFtYnJhLXBhdHJvbmF0by5lcy9wb2xpdGljYS1kZS1wcml2YWNpZGFkLyIgdGFyZ2V0PSJfYmxhbmsiPlBvbMOtdGljYSBkZSBwcml2YWNpZGFkPC9hPmQCGA8WAh8GaBYCAgMPFgIfB2VkAggPDxYCHwEFC1JlZ8Otc3RyZXNlZGQCAw8WAh8GaBYEAgMPDxYCHwMFHi9yZXNlcnZhckVudHJhZGFzLmFzcHg/b3BjPTE0MmRkAgUPDxYCHwEFDkNlcnJhciBzZXNpw7NuZGQCAQ9kFgICAQ8PFgQfCQUGYWN0aXZlHwoCAmRkAgIPDxYEHwMFPmh0dHBzOi8vd3d3LmFsaGFtYnJhLXBhdHJvbmF0by5lcy92aXNpdGFyL3ByZWd1bnRhcy1mcmVjdWVudGVzHwZnZGQCBA9kFgICAQ8PFgIfAwUoaHR0cDovL3d3dy55b3V0dWJlLmNvbS9hbGhhbWJyYXBhdHJvbmF0b2RkAgUPZBYCAgEPDxYCHwMFK2h0dHBzOi8vd3d3Lmluc3RhZ3JhbS5jb20vYWxoYW1icmFfb2ZpY2lhbC9kZAIGD2QWAgIBDw8WAh8DBShodHRwczovL3d3dy5mYWNlYm9vay5jb20vYWxoYW1icmFjdWx0dXJhZGQCBw9kFgICAQ8PFgIfAwUmaHR0cDovL3d3dy50d2l0dGVyLmNvbS9hbGhhbWJyYWN1bHR1cmFkZAIID2QWAgIBDw8WAh8DBSlodHRwczovL2VzLnBpbnRlcmVzdC5jb20vYWxoYW1icmFncmFuYWRhL2RkAgkPFgIfBmhkAgoPFgIfBmgWAgIBDw8WAh8DZGQWAmYPDxYCHwUFFUFsaGFtYnJhIHkgR2VuZXJhbGlmZWRkAgsPZBYCZg8PFgQfAwU+aHR0cHM6Ly93d3cuYWxoYW1icmEtcGF0cm9uYXRvLmVzL3Zpc2l0YXIvcHJlZ3VudGFzLWZyZWN1ZW50ZXMfBmdkZAIND2QWCAIBDw8WAh8GaGQWAgIBD2QWAmYPZBYGAgMPDxYCHwZoZGQCBA8PFgIeBkVzdGFkb2ZkFgJmD2QWAgIBD2QWAmYPZBYCAgEPZBYCAggPFgIfBmhkAg4PZBYEAgsPZBYEAgEPZBYCAgMPEGRkFgBkAgYPZBYCAgcPEGRkFgBkAg0PZBYEAgYPZBYCAgEPZBYCAgMPEGRkFgBkAgkPZBYCAgcPEGRkFgBkAgMPDxYCHwZoZBYCZg9kFgJmD2QWBgIBDw8WAh8GaGRkAggPZBYGAgUPZBYCAgEPEGRkFgBkAgYPZBYCAgEPEGRkFgBkAggPZBYEZg8QZGQWAGQCAQ8QZGQWAGQCCg9kFgICBQ9kFg4CAw9kFgICBQ8QZGQWAGQCBA9kFgICAw8QZGQWAGQCBg9kFgICBw8QZGQWAGQCCA9kFgICBQ8QZGQWAGQCCQ9kFgICBQ8QZGQWAGQCDw9kFgICBw8QZGQWAGQCFg9kFgQCAQ9kFgICAw8QZGQWAGQCBg9kFgICBw8QZGQWAGQCBQ8PFgIfBmhkFgJmD2QWAmYPZBYEAgMPDxYCHwtmZBYCZg9kFgICAQ9kFgJmD2QWAgIBD2QWAgIIDxYCHwZoZAIGD2QWAmYPZBYCAgEPZBYCZg9kFgICAQ88KwAKAQAPFgQeDVByZXZNb250aFRleHRlHg1OZXh0TW9udGhUZXh0BS08aW1nIHNyYz0vQXBwX3RoZW1lcy9BTEhBTUJSQS9pbWcvbmV4dC5wbmcgLz5kZAIHDw8WIB4UTG9jYWxpemFkb3JQYXJhbWV0cm9kHhVGZWNoYU1pbmltYURpc3BvbmlibGUG/z839HUoyiseEEZpbmFsaXphck1lbm9yZXNoHg5BZm9yb1BhcmFtZXRybwIBHgZQYWdhZGEFBUZhbHNlHgdTaW1ib2xvBQPigqweE0VubGFjZU1lbnVQYXJhbWV0cm8FB0dFTkVSQUweDFNlc2lvbkRpYXJpYWgeDFNlc2lvbkFjdHVhbAUfeGYweHl3MnZreXNpYTBhenUzNGlqMXBrNTE1OTIwMh4MQ2FwdGNoYVBhc28xZx4MTnVtRGVjaW1hbGVzAgIeD0NhcHRjaGFWYWxpZGFkb2ceCk5vbWluYWNpb25mHgxUZW5lbW9zTmlub3NoHhZHcnVwb0ludGVybmV0UGFyYW1ldHJvBQMxNDIeCFNpbkZlY2hhZmQWBAIBD2QWAmYPZBYiAgMPDxYCHwZoZGQCBA8PFgIfC2ZkFgJmD2QWAgIBD2QWAmYPZBYCAgEPZBYGZg8PFgIfAQUFZW1haWxkZAICDw8WAh8BBQxUZWxlZm9ubyBTTVNkZAIIDxYCHwZoZAIFDw8WAh8DBTBodHRwczovL3d3dy5hbGhhbWJyYS1wYXRyb25hdG8uZXMvP2NhPTAmbGc9ZXMtRVNkZAIGDxYCHwFlZAIHDxYCHwEFF1Zpc2l0YSBBbGhhbWJyYSBHZW5lcmFsZAIIDxYCHgVjbGFzcwUWc3RlcC10aXRsZSBzdGVwLWFjdGl2ZRYCAgEPFgIfAWRkAgkPDxYCHwZoZBYCAgEPDxYCHwEFC0lyIGEgcGFzbyAxZGQCCg8PFgIfBmdkFghmDxYCHwEFvQE8c2NyaXB0IHR5cGU9InRleHQvamF2YXNjcmlwdCI+d2luZG93LmRhdGFMYXllciA9IHdpbmRvdy5kYXRhTGF5ZXIgfHwgW107IGRhdGFMYXllci5wdXNoKHsgJ1BlcmZpbCc6J0dlbmVyYWwnLCAnQ2F0ZWdvcmlhJzonVmlzaXRhIEFsaGFtYnJhIEdlbmVyYWwnLCAnVGlwb0VudHJhZGEnOidJbmRpdmlkdWFsJyB9KTs8L3NjcmlwdD5kAgEPFgIfAWVkAgYPDxYWHhFGZWNoYU1pbmltYUdsb2JhbAYAf+q/AHfdCB4EUGFzbwIBHg1HcnVwb0ludGVybmV0BQMxNDIeDERhdG9zRmVzdGl2bzK7BAABAAAA/////wEAAAAAAAAADAIAAABIQXBwX0NvZGUueGhqcHZpem8sIFZlcnNpb249MC4wLjAuMCwgQ3VsdHVyZT1uZXV0cmFsLCBQdWJsaWNLZXlUb2tlbj1udWxsBQEAAAAfRGF0b3NGZXN0aXZvcytEYXRvc0xpc3RGZXN0aXZvcwEAAAARX0xzdERhdG9zRmVzdGl2b3MDiQFTeXN0ZW0uQ29sbGVjdGlvbnMuR2VuZXJpYy5MaXN0YDFbW0RhdG9zRmVzdGl2b3MrRGF0b3NGZXN0aXZvLCBBcHBfQ29kZS54aGpwdml6bywgVmVyc2lvbj0wLjAuMC4wLCBDdWx0dXJlPW5ldXRyYWwsIFB1YmxpY0tleVRva2VuPW51bGxdXQIAAAAJAwAAAAQDAAAAiQFTeXN0ZW0uQ29sbGVjdGlvbnMuR2VuZXJpYy5MaXN0YDFbW0RhdG9zRmVzdGl2b3MrRGF0b3NGZXN0aXZvLCBBcHBfQ29kZS54aGpwdml6bywgVmVyc2lvbj0wLjAuMC4wLCBDdWx0dXJlPW5ldXRyYWwsIFB1YmxpY0tleVRva2VuPW51bGxdXQMAAAAGX2l0ZW1zBV9zaXplCF92ZXJzaW9uBAAAHERhdG9zRmVzdGl2b3MrRGF0b3NGZXN0aXZvW10CAAAACAgJBAAAAAAAAAAAAAAABwQAAAAAAQAAAAAAAAAEGkRhdG9zRmVzdGl2b3MrRGF0b3NGZXN0aXZvAgAAAAseE01pbmltb0dydXBvSW50ZXJuZXQCAR4RRmVjaGFNYXhpbWFHbG9iYWwGALrGchSn3ggeDUVzTGlzdGFFc3BlcmFoHgtGb3J6YXJDYXJnYWgeDkZlY2hhc1ZpZ2VuY2lhMogNAAEAAAD/////AQAAAAAAAAAEAQAAAOIBU3lzdGVtLkNvbGxlY3Rpb25zLkdlbmVyaWMuRGljdGlvbmFyeWAyW1tTeXN0ZW0uU3RyaW5nLCBtc2NvcmxpYiwgVmVyc2lvbj00LjAuMC4wLCBDdWx0dXJlPW5ldXRyYWwsIFB1YmxpY0tleVRva2VuPWI3N2E1YzU2MTkzNGUwODldLFtTeXN0ZW0uU3RyaW5nLCBtc2NvcmxpYiwgVmVyc2lvbj00LjAuMC4wLCBDdWx0dXJlPW5ldXRyYWwsIFB1YmxpY0tleVRva2VuPWI3N2E1YzU2MTkzNGUwODldXQQAAAAHVmVyc2lvbghDb21wYXJlcghIYXNoU2l6ZQ1LZXlWYWx1ZVBhaXJzAAMAAwiSAVN5c3RlbS5Db2xsZWN0aW9ucy5HZW5lcmljLkdlbmVyaWNFcXVhbGl0eUNvbXBhcmVyYDFbW1N5c3RlbS5TdHJpbmcsIG1zY29ybGliLCBWZXJzaW9uPTQuMC4wLjAsIEN1bHR1cmU9bmV1dHJhbCwgUHVibGljS2V5VG9rZW49Yjc3YTVjNTYxOTM0ZTA4OV1dCOYBU3lzdGVtLkNvbGxlY3Rpb25zLkdlbmVyaWMuS2V5VmFsdWVQYWlyYDJbW1N5c3RlbS5TdHJpbmcsIG1zY29ybGliLCBWZXJzaW9uPTQuMC4wLjAsIEN1bHR1cmU9bmV1dHJhbCwgUHVibGljS2V5VG9rZW49Yjc3YTVjNTYxOTM0ZTA4OV0sW1N5c3RlbS5TdHJpbmcsIG1zY29ybGliLCBWZXJzaW9uPTQuMC4wLjAsIEN1bHR1cmU9bmV1dHJhbCwgUHVibGljS2V5VG9rZW49Yjc3YTVjNTYxOTM0ZTA4OV1dW10HAAAACQIAAAAHAAAACQMAAAAEAgAAAJIBU3lzdGVtLkNvbGxlY3Rpb25zLkdlbmVyaWMuR2VuZXJpY0VxdWFsaXR5Q29tcGFyZXJgMVtbU3lzdGVtLlN0cmluZywgbXNjb3JsaWIsIFZlcnNpb249NC4wLjAuMCwgQ3VsdHVyZT1uZXV0cmFsLCBQdWJsaWNLZXlUb2tlbj1iNzdhNWM1NjE5MzRlMDg5XV0AAAAABwMAAAAAAQAAAAcAAAAD5AFTeXN0ZW0uQ29sbGVjdGlvbnMuR2VuZXJpYy5LZXlWYWx1ZVBhaXJgMltbU3lzdGVtLlN0cmluZywgbXNjb3JsaWIsIFZlcnNpb249NC4wLjAuMCwgQ3VsdHVyZT1uZXV0cmFsLCBQdWJsaWNLZXlUb2tlbj1iNzdhNWM1NjE5MzRlMDg5XSxbU3lzdGVtLlN0cmluZywgbXNjb3JsaWIsIFZlcnNpb249NC4wLjAuMCwgQ3VsdHVyZT1uZXV0cmFsLCBQdWJsaWNLZXlUb2tlbj1iNzdhNWM1NjE5MzRlMDg5XV0E/P///+QBU3lzdGVtLkNvbGxlY3Rpb25zLkdlbmVyaWMuS2V5VmFsdWVQYWlyYDJbW1N5c3RlbS5TdHJpbmcsIG1zY29ybGliLCBWZXJzaW9uPTQuMC4wLjAsIEN1bHR1cmU9bmV1dHJhbCwgUHVibGljS2V5VG9rZW49Yjc3YTVjNTYxOTM0ZTA4OV0sW1N5c3RlbS5TdHJpbmcsIG1z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YcOxYSkfAQUBMGRkAgUPFgIfHgUWaW5jIGJ1dHRvbkFjdGl2byBjb2wtNBYCAgEPDxYEHwkFEWJ0bk1hc01lbm9zQWN0aXZvHwoCAmRkAgMPFgIfBmhkAgUPDxYEHwEFCUNvbnRpbnVhch8GaGRkAgsPFgIfHgUKc3RlcC10aXRsZRYCAgEPFgIfAWRkAgwPDxYCHwZoZBYMAgEPFgIfAWVkAgUPFgIfBmhkAgcPZBYIAgEPDxYCHwZoZBYCAgEPZBYCZg9kFgICAQ88KwAKAQAPFgQfDGUfDQUtPGltZyBzcmM9L0FwcF90aGVtZXMvQUxIQU1CUkEvaW1nL25leHQucG5nIC8+ZGQCAw8WAh8GaBYCAgEPEGRkFgBkAgUPFgIfBmgWAgIBDxBkZBYAZAIJDw8WAh8GaGQWBGYPEGQQFQgYU2VsZWNjaW9uZSB1biBpdGluZXJhcmlvIFZpc2l0YXMgR3VpYWRhcyBwb3IgZWwgTW9udW1lbnRvLFZpc2l0YXMgQXV0b2d1aWFkYXMgcG9yIGVsIE1vbnVtZW50byBHZW5lcmFsJFZpc2l0YXMgQ29tYmluYWRhcyBBbGhhbWJyYSArIENpdWRhZCxWaXNpdGFzIEd1aWFkYXMgcG9yIGxhIERlaGVzYSBkZWwgR2VuZXJhbGlmZSlWaXNpdGFzIEd1aWFkYXMgcG9yIGVsIE1vbnVtZW50byBKYXJkaW5lcy1WaXNpdGFzIEF1dG9ndWlhZGFzIHBvciBlbCBNb251bWVudG8gSmFyZGluZXMeVmlzaXRhcyBHdWlhZGFzIE11c2VvICsgQ2l1ZGFkFQgAIFZpc2l0YXMgR3VpYWRhcyBwb3IgZWwgTW9udW1lbnRvLFZpc2l0YXMgQXV0b2d1aWFkYXMgcG9yIGVsIE1vbnVtZW50byBHZW5lcmFsJFZpc2l0YXMgQ29tYmluYWRhcyBBbGhhbWJyYSArIENpdWRhZCxWaXNpdGFzIEd1aWFkYXMgcG9yIGxhIERlaGVzYSBkZWwgR2VuZXJhbGlmZSlWaXNpdGFzIEd1aWFkYXMgcG9yIGVsIE1vbnVtZW50byBKYXJkaW5lcy1WaXNpdGFzIEF1dG9ndWlhZGFzIHBvciBlbCBNb251bWVudG8gSmFyZGluZXMeVmlzaXRhcyBHdWlhZGFzIE11c2VvICsgQ2l1ZGFkFCsDCGdnZ2dnZ2dnFgFmZAIBDxAPFgIfBmhkEBUBGFNlbGVjY2lvbmUgdW4gaXRpbmVyYXJpbxUBABQrAwFnFgFmZAILDxYCHwZoZAINDw8WAh8BBRd2b2x2ZXIgYWwgcGFzbyBhbnRlcmlvcmRkAg8PZBYCZg9kFgICAQ8PFgQfAQULSXIgYSBwYXNvIDMfBmhkZAINDxYEHx4FCnN0ZXAtdGl0bGUfBmdkAg4PDxYCHwZoZBYaZg8WAh8BZWQCAQ8WAh8BBQEuZAICD2QWAmYPZBYKAgEPDxYCHgpIZWFkZXJUZXh0BSVEZWJlIGludHJvZHVjaXIgbG9zIHZhbG9yZXMgY29ycmVjdG9zZGQCAw9kFgRmD2QWAmYPDxYCHwEFF05vbWJyZSBkZWwgY29tcHJhZG9yICogZGQCAQ9kFgJmDw8WAh8BBQxBcGVsbGlkb3MgKiBkZAIED2QWBGYPZBYEZg8PFgIfAQUZRG9jdW1lbnRvIGRlIGlkZW50aWRhZCAqIGRkAgIPEGQQFQMMRE5JIEVzcGHDsW9sDE5JRSBFc3Bhw7FvbBdPdHJvIE5yby4gaWRlbnRpZmljYWRvchUDA2RuaQNuaWUHb3Ryb19pZBQrAwNnZ2cWAWZkAgEPZBYCZg8PFgIfAQUXTsO6bWVybyBkZSBkb2N1bWVudG8gKiBkZAIFD2QWBGYPZBYCZg8PFgIfAQUIRW1haWwgKiBkZAIBD2QWAmYPDxYCHwEFEUNvbmZpcm1hIEVtYWlsICogZGQCBg9kFgJmD2QWAmYPDxYCHwEFDFRlbMOpZm9ubyAqIGRkAgQPFgIfBmcWAgIBDxAPFgIeB0NoZWNrZWRoZGRkZAIGD2QWBAIBD2QWAgIDDxBkEBUEDEROSSBFc3Bhw7FvbAxDSUYgRXNwYcOxb2wMTklFIEVzcGHDsW9sF090cm8gTnJvLiBpZGVudGlmaWNhZG9yFQQDZG5pA2NpZgNuaWUHb3Ryb19pZBQrAwRnZ2dnFgFmZAIGD2QWBAIFDw8WAh8GaGRkAgcPEGQQFe8BE1NlbGVjY2lvbmUgdW4gcGHDrXMJQXJnZW50aW5hCUF1c3RyYWxpYQVDaGluYQVJdGFseQVKYXBhbgZNZXhpY28LTmV3IFplYWxhbmQIUG9ydHVnYWwHRXNwYcOxYQdHZXJtYW55BkZyYW5jZRJSdXNzaWFuIEZlZGVyYXRpb24OVW5pdGVkIEtpbmdkb20UVW5pdGVkIFN0YXRlcyBvZiBBbWULQWZnaGFuaXN0YW4HQWxiYW5pYQdBbGdlcmlhDkFtZXJpY2FuIFNhbW9hB0FuZG9ycmEGQW5nb2xhCEFuZ3VpbGxhCkFudGFyY3RpY2EHQW50aWd1YQdBcm1lbmlhBUFydWJhB0F1c3RyaWEKQXplcmJhaWphbgdCYWhhbWFzB0JhaHJhaW4KQmFuZ2xhZGVzaAhCYXJiYWRvcwdCZWxhcnVzB0JlbGdpdW0GQmVsaXplBUJlbmluB0Jlcm11ZGEGQmh1dGFuB0JvbGl2aWEGQm9zbmlhCEJvdHN3YW5hDUJvdXZldCBJc2xhbmQGQnJhemlsDkJyaXRpc2ggSW5kaWFuEUJydW5laSBEYXJ1c3NhbGFtCEJ1bGdhcmlhDEJ1cmtpbmEgRmFzbwdCdXJ1bmRpCENhbWJvZGlhCENhbWVyb29uBkNhbmFkYQpDYXBlIFZlcmRlDkNheW1hbiBJc2xhbmRzE0NlbnRyYWwgQWZyaWNhbiBSZXAEQ2hhZAVDaGlsZRBDaHJpc3RtYXMgSXNsYW5kDUNvY29zIElzbGFuZHMIQ29sb21iaWEHQ29tb3JvcwVDb25nbwxDb29rIElzbGFuZHMKQ29zdGEgUmljYQdDcm9hdGlhBEN1YmEGQ3lwcnVzDkN6ZWNoIFJlcHVibGljB0Rlbm1hcmsIRGppYm91dGkIRG9taW5pY2ESRG9taW5pY2FuIFJlcHVibGljCkVhc3QgVGltb3IHRWN1YWRvcgVFZ3lwdAtFbCBTYWx2YWRvchFFcXVhdG9yaWFsIEd1aW5lYQdFcml0cmVhB0VzdG9uaWEIRXRoaW9waWENRmFyb2UgSXNsYW5kcwRGaWppB0ZpbmxhbmQNRnJlbmNoIEd1aWFuYRBGcmVuY2ggUG9seW5lc2lhBUdhYm9uBkdhbWJpYQdHZW9yZ2lhBUdoYW5hBkdyZWVjZQlHcmVlbmxhbmQHR3JlbmFkYQpHdWFkZWxvdXBlBEd1YW0JR3VhdGVtYWxhBkd1aW5lYQ1HdWluZWEgQmlzc2F1Bkd1eWFuYQVIYWl0aQhIb25kdXJhcwlIb25nIEtvbmcHSHVuZ2FyeQdJY2VsYW5kBUluZGlhCUluZG9uZXNpYQRJcmFuBElyYXEHSXJlbGFuZAZJc3JhZWwLSXZvcnkgQ29hc3QHSmFtYWljYQZKb3JkYW4KS2F6YWtoc3RhbgVLZW55YQhLaXJpYmF0aQZLdXdhaXQKS3lyZ3l6c3RhbgNMYW8GTGF0dmlhB0xlYmFub24HTGVzb3RobwdMaWJlcmlhBUxpYnlhDUxpZWNodGVuc3RlaW4JTGl0aHVhbmlhCkx1eGVtYm91cmcFTWFjYXUJTWFjZWRvbmlhCk1hZGFnYXNjYXIGTWFsYXdpCE1hbGF5c2lhCE1hbGRpdmVzBE1hbGkFTWFsdGEITWFsdmluYXMQTWFyc2hhbGwgSXNsYW5kcwpNYXJ0aW5pcXVlCk1hdXJpdGFuaWEJTWF1cml0aXVzB01heW90dGUKTWljcm9uZXNpYQdNb2xkb3ZhBk1vbmFjbwhNb25nb2xpYQpNb250ZW5lZ3JvCk1vbnRzZXJyYXQHTW9yb2NjbwpNb3phbWJpcXVlB015YW5tYXIHTmFtaWJpYQVOYXVydQVOZXBhbAtOZXRoZXJsYW5kcxROZXRoZXJsYW5kcyBBbnRpbGxlcw1OZXcgQ2FsZWRvbmlhCU5pY2FyYWd1YQVOaWdlcgdOaWdlcmlhBE5pdWUOTm9yZm9sayBJc2xhbmQLTm9ydGggS29yZWETTm9ydGhlcm4gTWFyaWFuYSBJcwZOb3J3YXkET21hbhlPdHJvcyBkZSBwYWlzZXMgZGVsIG11bmRvCFBha2lzdGFuBVBhbGF1BlBhbmFtYRBQYXB1YSBOZXcgR3VpbmVhCFBhcmFndWF5BFBlcnULUGhpbGlwcGluZXMIUGl0Y2Fpcm4GUG9sYW5kC1B1ZXJ0byBSaWNvBVFhdGFyB1JldW5pb24HUm9tYW5pYQZSd2FuZGEPUyBHZW9yZ2lhIFNvdXRoC1NhaW50IEx1Y2lhBVNhbW9hClNhbiBNYXJpbm8TU2FvIFRvbWUgLSBQcmluY2lwZQxTYXVkaSBBcmFiaWEHU2VuZWdhbAZTZXJiaWEKU2V5Y2hlbGxlcwxTaWVycmEgTGVvbmUJU2luZ2Fwb3JlCFNsb3Zha2lhCFNsb3ZlbmlhD1NvbG9tb24gSXNsYW5kcwdTb21hbGlhDFNvdXRoIEFmcmljYQtTb3V0aCBLb3JlYQlTcmkg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EGQQFe8BE1NlbGVjY2lvbmUgdW4gcGHDrXMJQXJnZW50aW5hCUF1c3RyYWxpYQVDaGluYQVJdGFseQVKYXBhbgZNZXhpY28LTmV3IFplYWxhbmQIUG9ydHVnYWwHRXNwYcOxYQdHZXJtYW55BkZyYW5jZRJSdXNzaWFuIEZlZGVyYXRpb24OVW5pdGVkIEtpbmdkb20UVW5pdGVkIFN0YXRlcyBvZiBBbWULQWZnaGFuaXN0YW4HQWxiYW5pYQdBbGdlcmlhDkFtZXJpY2FuIFNhbW9hB0FuZG9ycmEGQW5nb2xhCEFuZ3VpbGxhCkFudGFyY3RpY2EHQW50aWd1YQdBcm1lbmlhBUFydWJhB0F1c3RyaWEKQXplcmJhaWphbgdCYWhhbWFzB0JhaHJhaW4KQmFuZ2xhZGVzaAhCYXJiYWRvcwdCZWxhcnVzB0JlbGdpdW0GQmVsaXplBUJlbmluB0Jlcm11ZGEGQmh1dGFuB0JvbGl2aWEGQm9zbmlhCEJvdHN3YW5hDUJvdXZldCBJc2xhbmQGQnJhemlsDkJyaXRpc2ggSW5kaWFuEUJydW5laSBEYXJ1c3NhbGFtCEJ1bGdhcmlhDEJ1cmtpbmEgRmFzbwdCdXJ1bmRpCENhbWJvZGlhCENhbWVyb29uBkNhbmFkYQpDYXBlIFZlcmRlDkNheW1hbiBJc2xhbmRzE0NlbnRyYWwgQWZyaWNhbiBSZXAEQ2hhZAVDaGlsZRBDaHJpc3RtYXMgSXNsYW5kDUNvY29zIElzbGFuZHMIQ29sb21iaWEHQ29tb3JvcwVDb25nbwxDb29rIElzbGFuZHMKQ29zdGEgUmljYQdDcm9hdGlhBEN1YmEGQ3lwcnVzDkN6ZWNoIFJlcHVibGljB0Rlbm1hcmsIRGppYm91dGkIRG9taW5pY2ESRG9taW5pY2FuIFJlcHVibGljCkVhc3QgVGltb3IHRWN1YWRvcgVFZ3lwdAtFbCBTYWx2YWRvchFFcXVhdG9yaWFsIEd1aW5lYQdFcml0cmVhB0VzdG9uaWEIRXRoaW9waWENRmFyb2UgSXNsYW5kcwRGaWppB0ZpbmxhbmQNRnJlbmNoIEd1aWFuYRBGcmVuY2ggUG9seW5lc2lhBUdhYm9uBkdhbWJpYQdHZW9yZ2lhBUdoYW5hBkdyZWVjZQlHcmVlbmxhbmQHR3JlbmFkYQpHdWFkZWxvdXBlBEd1YW0JR3VhdGVtYWxhBkd1aW5lYQ1HdWluZWEgQmlzc2F1Bkd1eWFuYQVIYWl0aQhIb25kdXJhcwlIb25nIEtvbmcHSHVuZ2FyeQdJY2VsYW5kBUluZGlhCUluZG9uZXNpYQRJcmFuBElyYXEHSXJlbGFuZAZJc3JhZWwLSXZvcnkgQ29hc3QHSmFtYWljYQZKb3JkYW4KS2F6YWtoc3RhbgVLZW55YQhLaXJpYmF0aQZLdXdhaXQKS3lyZ3l6c3RhbgNMYW8GTGF0dmlhB0xlYmFub24HTGVzb3RobwdMaWJlcmlhBUxpYnlhDUxpZWNodGVuc3RlaW4JTGl0aHVhbmlhCkx1eGVtYm91cmcFTWFjYXUJTWFjZWRvbmlhCk1hZGFnYXNjYXIGTWFsYXdpCE1hbGF5c2lhCE1hbGRpdmVzBE1hbGkFTWFsdGEITWFsdmluYXMQTWFyc2hhbGwgSXNsYW5kcwpNYXJ0aW5pcXVlCk1hdXJpdGFuaWEJTWF1cml0aXVzB01heW90dGUKTWljcm9uZXNpYQdNb2xkb3ZhBk1vbmFjbwhNb25nb2xpYQpNb250ZW5lZ3JvCk1vbnRzZXJyYXQHTW9yb2NjbwpNb3phbWJpcXVlB015YW5tYXIHTmFtaWJpYQVOYXVydQVOZXBhbAtOZXRoZXJsYW5kcxROZXRoZXJsYW5kcyBBbnRpbGxlcw1OZXcgQ2FsZWRvbmlhCU5pY2FyYWd1YQVOaWdlcgdOaWdlcmlhBE5pdWUOTm9yZm9sayBJc2xhbmQLTm9ydGggS29yZWETTm9ydGhlcm4gTWFyaWFuYSBJcwZOb3J3YXkET21hbhlPdHJvcyBkZSBwYWlzZXMgZGVsIG11bmRvCFBha2lzdGFuBVBhbGF1BlBhbmFtYRBQYXB1YSBOZXcgR3VpbmVhCFBhcmFndWF5BFBlcnULUGhpbGlwcGluZXMIUGl0Y2Fpcm4GUG9sYW5kC1B1ZXJ0byBSaWNvBVFhdGFyB1JldW5pb24HUm9tYW5pYQZSd2FuZGEPUyBHZW9yZ2lhIFNvdXRoC1NhaW50IEx1Y2lhBVNhbW9hClNhbiBNYXJpbm8TU2FvIFRvbWUgLSBQcmluY2lwZQxTYXVkaSBBcmFiaWEHU2VuZWdhbAZTZXJiaWEKU2V5Y2hlbGxlcwxTaWVycmEgTGVvbmUJU2luZ2Fwb3JlCFNsb3Zha2lhCFNsb3ZlbmlhD1NvbG9tb24gSXNsYW5kcwdTb21hbGlhDFNvdXRoIEFmcmljYQtTb3V0aCBLb3JlYQlTcmkgTGFua2EJU3QgSGVsZW5hElN0IEtpdHRzIGFuZCBOZXZpcxNTdCBQaWVycmUgIE1pcXVlbG9uEVN0IFZpbmNlbnQtR3JlbmFkBVN1ZGFuCFN1cmluYW1lEVN2YWxiYXJkIEphbiBNIElzCVN3YXppbGFuZAZTd2VkZW4LU3dpdHplcmxhbmQFU3lyaWEGVGFpd2FuClRhamlraXN0YW4IVGFuemFuaWEIVGhhaWxhbmQEVG9nbwdUb2tlbGF1BVRvbmdhE1RyaW5pZGFkIEFuZCBUb2JhZ28HVHVuaXNpYQZUdXJrZXkMVHVya21lbmlzdGFuFFR1cmtzIENhaWNvcyBJc2xhbmRzBlR1dmFsdQZVZ2FuZGEHVWtyYWluZRRVbml0ZWQgQXJhYiBFbWlyYXRlcwdVcnVndWF5EFVTIE1pbm9yIElzbGFuZHMKVXpiZWtpc3RhbgdWYW51YXR1B1ZhdGljYW4JVmVuZXp1ZWxhB1ZpZXRuYW0OVmlyZ2luIElzbGFuZHMRVmlyZ2luIElzbGFuZHMgVVMQV2FsbGlzIEZ1dHVuYSBJcw5XZXN0ZXJuIFNhaGFyYQVZZW1lbgpZdWdvc2xhdmlhBVphaXJlBlphbWJpYQhaaW1iYWJ3ZRXvAQADMDMyAzAzNgMxNTYDMzgwAzM5MgM0ODQDNTU0AzYyMAM3MjQDMjc2AzI1MAM2NDMDODI2Azg0MAMwMDQDMDA4AzAxMgMwMTYDMDIwAzAyNAM2NjADMDEwAzAyOAMwNTEDNTMzAzA0MAMwMzEDMDQ0AzA0OAMwNTADMDUyAzExMgMwNTYDMDg0AzIwNAMwNjADMDY0AzA2OAMwNzADMDcyAzA3NAMwNzYDMDg2AzA5NgMxMDADODU0AzEwOAMxMTYDMTIwAzEyNAMxMzIDMTM2AzE0MAMxNDgDMTUyAzE2MgMxNjYDMTcwAzE3NAMxNzgDMTg0AzE4OAMxOTEDMTkyAzE5NgMyMDMDMjA4AzI2MgMyMTIDMjE0AzYyNgMyMTgDODE4AzIyMgMyMjYDMjMyAzIzMwMyMzEDMjM0AzI0MgMyNDYDMjU0AzI1OAMyNjYDMjcwAzI2OAMyODgDMzAwAzMwNAMzMDgDMzEyAzMxNgMzMjADMzI0AzYyNAMzMjgDMzMyAzM0MAMzNDQDMzQ4AzM1MgMzNTYDMzYwAzM2NAMzNjgDMzcyAzM3NgMzODQDMzg4AzQwMAMzOTgDNDA0AzI5NgM0MTQDNDE3AzQxOAM0MjgDNDIyAzQyNgM0MzADNDM0AzQzOAM0NDADNDQyAzQ0NgM4MDcDNDUwAzQ1NAM0NTgDNDYyAzQ2NgM0NzADMjM4AzU4NAM0NzQDNDc4AzQ4MAMxNzUDNTgzAzQ5OAM0OTIDNDk2AzQ5OQM1MDADNTA0AzUwOAMxMDQDNTE2AzUyMAM1MjQDNTI4AzUzMAM1NDADNTU4AzU2MgM1NjYDNTcwAzU3NAM0MDgDNTgwAzU3OAM1MTIDNzQ0AzU4NgM1ODUDNTkxAzU5OAM2MDADNjA0AzYwOAM2MTIDNjE2AzYzMAM2MzQDNjM4AzY0MgM2NDYDMjM5AzY2MgM4ODIDNjc0AzY3OAM2ODIDNjg2AzY4OAM2OTADNjk0AzcwMgM3MDMDNzA1AzA5MAM3MDYDNzEwAzQxMAMxNDQDNjU0AzY1OQM2NjYDNjcwAzczNgM3NDADNzQ0Azc0OAM3NTIDNzU2Azc2MAMxNTgDNzYyAzgzNAM3NjQDNzY4Azc3MgM3NzYDNzgwAzc4OAM3OTIDNzk1Azc5NgM3OTgDODAwAzgwNAM3ODQDODU4AzU4MQM4NjADNTQ4AzMzNgM4NjIDNzA0AzA5MgM4NTADODc2AzczMgM4ODcDODkxAzE4MAM4OTQDNzE2FCsD7wFnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZxYBAglkAgkPDxYCHwZoZBYEAgEPEA8WAh8BBRBBbmV4YXIgc29saWNpdHVkZGRkZAIDDw8WAh8GaGRkAg4PZBYCAgEPDxYCHgtUaXBvVXN1YXJpbwspY2Nsc0Z1bmNpb25lcyt0aXBvX3VzdWFyaW8sIEFwcF9Db2RlLnhoanB2aXpvLCBWZXJzaW9uPTAuMC4wLjAsIEN1bHR1cmU9bmV1dHJhbCwgUHVibGljS2V5VG9rZW49bnVsbAFkFgJmD2QWAmYPZBYCAgMPZBYCZg9kFgJmD2QWBGYPZBYCAgEPPCsACQEADxYGHg1TZWxlY3RlZEluZGV4Zh4IRGF0YUtleXMWAB8tAgNkFgZmD2QWAgIBDw8WCB8BBQxJbmZvcm1hY2nDs24eCFRhYkluZGV4AQAAHgtDb21tYW5kTmFtZQUETW92ZR4PQ29tbWFuZEFyZ3VtZW50BQEwZGQCAQ9kFgICAQ8PFggfAQUQQ2FyZ2EgZWwgZmljaGVybx80AQAAHzUFBE1vdmUfNgUBMWRkAgIPZBYCAgEPDxYIHwEFCUNvbmZpcm1hch80AQAAHzUFBE1vdmUfNgUBMmRkAgEPZBYCZg9kFgQCAQ9kFgJmD2QWAmYPZBYGZg8WAh4FVGl0bGUFDEluZm9ybWFjacOzbmQCAQ8WAh83BRBDYXJnYSBlbCBmaWNoZXJvZAICDxYCHzcFCUNvbmZpcm1hcmQCAg9kFgJmD2QWBGYPZBYCAgEPDxYCHwEFCVNpZ3VpZW50ZWRkAgIPZBYEAgEPDxYCHwEFCEFudGVyaW9yZGQCAw8PFgIfAQUJQ29uZmlybWFyZGQCEA9kFgICAQ8WAh8GaGQCEg8PFgIfBmhkFgJmD2QWAgIBD2QWAmYPZBYCAgUPZBYEAhkPEGRkFgBkAh8PEGRkFgBkAhMPFgIfBmhkAhQPDxYCHwEFF3ZvbHZlciBhbCBwYXNvIGFudGVyaW9yZGQCFQ9kFgICAQ8PFgIfAQULSXIgYSBwYXNvIDRkZAIPD2QWBAIBDxYEHx4FCnN0ZXAtdGl0bGUfBmdkAgIPDxYCHwZoZBYQZg8WAh8GaBYCAgIPDxYCHwEFEENvbXByb2JhciBjdXDDs25kZAIBDxYCHwFlZAICDxYCHwZoZAIEDw8WAh8BBRd2b2x2ZXIgYWwgcGFzbyBhbnRlcmlvcmRkAgUPFgIfBmgWBgIBDw8WBB8BZR8GaGRkAgMPFgIfLmVkAgUPDxYCHwEFEUZpbmFsaXphciByZXNlcnZhZGQCBw8PFgQfAQUQRmluYWxpemFyIGNvbXByYR8GZ2RkAggPDxYCHwEFDlBob25lIGFuZCBTZWxsZGQCCQ8PFgIfAQUHUGF5R29sZGRkAhAPZBYCZg9kFghmDxYCHwEFKzxzdHJvbmc+U3UgY29tcHJhIGRlIGVudHJhZGFzPC9zdHJvbmc+IHBhcmFkAgEPFgIfAQUXVmlzaXRhIEFsaGFtYnJhIEdlbmVyYWxkAgIPFgIfAQXYAzxkaXYgY2xhc3M9J3Jlc3VsdCc+ICAgPGRpdiBjbGFzcz0nbS1iLTEyJz4gICAgICA8aSBjbGFzcz0naWNvbiBpY29uLXBlb3BsZSc+PC9pPiAgIDwvZGl2PiAgIDxkaXYgY2xhc3M9J20tYi0xMic+ICAgICAgPGkgY2xhc3M9J2ljb24gaWNvbi1kYXRlJz48L2k+ICAgICAgPHA+RmVjaGE6IDxiciAvPiAgICAgIDwvcD4gICA8L2Rpdj48L2Rpdj48ZGl2IGNsYXNzPSdwcml4LXRvdGFsIGJyZC1zdXAtMjAnPiAgIDxzcGFuIGNsYXNzPSd0aXR1bG9QcmVjaW9GaW5hbCc+VG90YWwgZW50cmFkYXM8L3NwYW4+PHN0cm9uZyBjbGFzcz0nY29udGVuaWRvUHJlY2lvRmluYWwnPjA8L3N0cm9uZz4gICA8c3BhbiBjbGFzcz0ndGl0dWxvUHJlY2lvRmluYWwgcHJlY2lvRmluYWwnPlByZWNpbyBmaW5hbDwvc3Bhbj48c3Ryb25nIGNsYXNzPSdjb250ZW5pZG9QcmVjaW9GaW5hbCBwcmVjaW9GaW5hbCc+MCwwMCDigqw8L3N0cm9uZz48L2Rpdj5kAgMPFgIfAWRkAhIPZBYEAgEPDxYCHwEFDkF2aXNvIGhvcmFyaW9zZGQCAw8PFgIfAQWiAVJlY3VlcmRlIHNlciA8Yj5wdW50dWFsPC9iPiBlbiBsYSBob3JhIHNlbGVjY2lvbmFkYSBhIGxvcyA8Yj5QYWxhY2lvcyBOYXphcsOtZXM8L2I+LiBSZXN0byBkZWwgbW9udW1lbnRvIGRlIDg6MzAgYSAxODowMCBob3JhcyBpbnZpZXJubzsgODozMCBhIDIwOjAwIGhvcmFzIHZlcmFub2RkAhMPZBYIAgEPDxYCHwEFH0F2aXNvIHNvYnJlIHZpc2l0YXMgY29uIG1lbm9yZXNkZAIDDw8WAh8BBfYBU2kgdmEgYSByZWFsaXphciBsYSB2aXNpdGEgY29uIG1lbm9yZXMgZGUgMyBhIDExIGHDsW9zLCDDqXN0b3MgcHJlY2lzYW4gZGUgc3UgZW50cmFkYSBjb3JyZXNwb25kaWVudGUuDQpQb3IgZmF2b3Igc2VsZWNjacOzbmVsYSBlbiBzdSBjb21wcmE6IExhcyBlbnRyYWRhcyBkZSBtZW5vcmVzIGRlIDMgYcOxb3Mgc2Vyw6FuIGZhY2lsaXRhZGFzIGVuIGxhcyB0YXF1aWxsYXMgZGVsIG1vbnVtZW50by4gwr9EZXNlYSBjb250aW51YXI/ZGQCBQ8PFgIfAQUCU2lkZAIHDw8WAh8BBQJOb2RkAhQPZBYEAgEPDxYCHwEFFkFWSVNPIERBVE9TIFZJU0lUQU5URVNkZAIDDw8WAh8BBVxDb21wcnVlYmUgcXVlIGxvcyBkYXRvcyBkZSB2aXNpdGFudGVzIHNvbiBjb3JyZWN0b3MsIGFzw60gY29tbyBsYSBmZWNoYSB5IGhvcmEgc2VsZWNjaW9uYWRhLmRkAgIPDxYCHwZoZGQCDg8WBB8BBb8dPGZvb3RlciBjbGFzcz0iZm9vdGVyIj4NCiAgPGRpdiBpZD0iZGl2Rm9vdGVyMiIgY2xhc3M9ImZvb3RlcjIiPg0KICAgIDxkaXYgY2xhc3M9ImNvbnRhaW5lciI+DQogICAgICA8ZGl2IGNsYXNzPSJsb2dvICI+DQogICAgICAgICAgPGEgaHJlZj0iaHR0cDovL3d3dy5hbGhhbWJyYS1wYXRyb25hdG8uZXMvIiB0YXJnZXQ9Il9ibGFuayI+PGltZyBpZD0iaW1nRm9vdGVyIiBzcmM9Ii9BcHBfVGhlbWVzL0FMSEFNQlJBL2ltZy9sb2dvLWZvb3Rlci5wbmciIGFsdD0iQWxoYW1icmEgeSBHZW5lcmFsaWZlIj48L2E+DQogICAgICAgIDwvZGl2Pg0KICAgICAgPGRpdiBjbGFzcz0icm93Ij4NCiAgICAgICAgIDxkaXYgY2xhc3M9ImZvb3Rlci1pdGVtIGNvbHVtbi0xIj4NCiAgICAgICAgICA8dWw+DQogICAgICAgICAgICA8bGk+PGEgY2xhc3M9ImxpbmtzLWl0ZW0iIGhyZWY9Imh0dHBzOi8vdGlja2V0cy5hbGhhbWJyYS1wYXRyb25hdG8uZXMvdGUtcHVlZGUtYXl1ZGFyLyIgdGFyZ2V0PSJfYmxhbmsiPkxFIFBVRURPIEFZVURBUjwvYT48L2xpPg0KICAgICAgICAgICAgPGxpPjxhIGNsYXNzPSJsaW5rcy1pdGVtIiBocmVmPSJodHRwczovL3RpY2tldHMuYWxoYW1icmEtcGF0cm9uYXRvLmVzL3BvbGl0aWNhLWRlLWNvbXByYS8iIHRhcmdldD0iX2JsYW5rIj5QT0zDjVRJQ0EgREUgQ09NUFJBUzwvYT48L2xpPg0KICAgICAgICAgICAgPGxpPjxhIGNsYXNzPSJsaW5rcy1pdGVtIiBocmVmPSIvcG9saXRpY2EtY29va2llcy5hc3B4IiB0YXJnZXQ9Il9ibGFuayI+UE9Mw41USUNBIERFIENPT0tJRVM8L2E+PC9saT4NCiAgICAgICAgICAgIDxsaT48YSBjbGFzcz0ibGlua3MtaXRlbSIgaHJlZj0iamF2YXNjcmlwdDp2b2lkKDApIiAgb25DbGljaz0iUmVjb25maWd1cmFyQ29va2llcygpIj5DYW5jZWxhciAvIGNvbmZpZ3VyYXIgcG9saXRpY2EgZGUgY29va2llczwvYT48L2xpPg0KICAgICAgICAgICAgPGxpPjxhIGNsYXNzPSJsaW5rcy1pdGVtIiBocmVmPSJodHRwczovL3RpY2tldHMuYWxoYW1icmEtcGF0cm9uYXRvLmVzL3BvbGl0aWNhLWRlLXByaXZhY2lkYWQiIHRhcmdldD0iX2JsYW5rIj5QT0zDjVRJQ0EgREUgUFJJVkFDSURBRDwvYT48L2xpPg0KICAgICAgICAgICAgPGxpPjxhIGNsYXNzPSJsaW5rcy1pdGVtIiBocmVmPSJodHRwczovL3RpY2tldHMuYWxoYW1icmEtcGF0cm9uYXRvLmVzL2F2aXNvLWxlZ2FsLyIgdGFyZ2V0PSJfYmxhbmsiPkFWSVNPIExFR0FMPC9hPjwvbGk+DQogICAgICAgICAgICA8bGk+PHAgY2xhc3M9ImxpbmtzLWl0ZW0iPlRFTMOJRk9OTyBERUwgVklTSVRBTlRFIDxhIGhyZWY9InRlbDorMzQ4NTg4ODkwMDIiIGNsYXNzPSJ0ZWwiPiszNCA5NTggMDI3IDk3MTwvYT48L3A+PC9saT4NCiAgICAgICAgICAgIDxsaT48cCBjbGFzcz0ibGlua3MtaXRlbSI+VEVMw4lGT05PIERFIFNPUE9SVEUgQSBMQSBWRU5UQSBERSBFTlRSQURBUyA8YSBocmVmPSJ0ZWw6KzM0ODU4ODg5MDAyIiBjbGFzcz0idGVsIj4rMzQ4NTg4ODkwMDI8L2E+PC9wPjwvbGk+DQo8bGk+PHAgY2xhc3M9ImxpbmtzLWl0ZW0iPkNPUlJFTyBFTEVDVFLDk05JQ08gREUgU09QT1JURSBBIExBIFZFTlRBIERFIEVOVFJBREFTIDxhIGhyZWY9Im1haWx0bzp0aWNrZXRzLmFsaGFtYnJhQGlhY3Bvcy5jb20iIGNsYXNzPSJ0ZWwiPnRpY2tldHMuYWxoYW1icmFAaWFjcG9zLmNvbTwvYT48L3A+PC9saT4NCiAgICAgICAgICA8L3VsPg0KICAgICAgICAgPC9kaXY+DQogICAgICA8L2Rpdj4NCiAgICAgIDwhLS0gQ29udGFjdG8geSBSUlNTIC0tPg0KICAgICAgPGRpdiBjbGFzcz0iZm9vdGVyNCI+DQogICAgICAgIDxkaXYgY2xhc3M9ImZvbGxvdyI+DQogICAgICAgICAgPHA+U8OtZ3Vlbm9zIGVuOjwvcD4NCiAgICAgICAgICA8dWwgY2xhc3M9InNvY2lhbCI+DQogICAgICAgICAgICA8bGkgaWQ9ImxpRmFjZWJvb2siPg0KICAgICAgICAgICAgICA8YSBpZD0ibGlua0ZhY2Vib29rIiBjbGFzcz0iaWNvbiBpY29uLWZhY2Vib29rIiB0aXRsZT0iRmFjZWJvb2siIGhyZWY9Imh0dHBzOi8vd3d3LmZhY2Vib29rLmNvbS9hbGhhbWJyYWN1bHR1cmEiIHRhcmdldD0iX2JsYW5rIj48L2E+DQogICAgICAgICAgICA8L2xpPg0KICAgICAgICAgICAgPGxpIGlkPSJsaVR3aXRlciI+DQogICAgICAgICAgICAgIDxhIGlkPSJsaW5rVHdpdHRlciIgY2xhc3M9Imljb24gaWNvbi10d2l0dGVyIiB0aXRsZT0iVHdpdHRlciIgaHJlZj0iaHR0cDovL3d3dy50d2l0dGVyLmNvbS9hbGhhbWJyYWN1bHR1cmEiIHRhcmdldD0iX2JsYW5rIj48L2E+DQogICAgICAgICAgICA8L2xpPg0KICAgICAgICAgICAgPGxpIGlkPSJsaVlvdVR1YmUiPg0KICAgICAgICAgICAgICA8YSBpZD0ibGlua1lvdVR1YmUiIGNsYXNzPSJpY29uIGljb24teW91dHViZSIgdGl0bGU9IllvdXR1YmUiIGhyZWY9Imh0dHA6Ly93d3cueW91dHViZS5jb20vYWxoYW1icmFwYXRyb25hdG8iIHRhcmdldD0iX2JsYW5rIj48L2E+DQogICAgICAgICAgICA8L2xpPg0KICAgICAgICAgICAgPGxpIGlkPSJsaUluc3RhZ3JhbSI+DQogICAgICAgICAgICAgIDxhIGlkPSJsaW5rSW50YWdyYW0iIGNsYXNzPSJpY29uIGljb24taW5zdGFncmFtIiB0aXRsZT0iSW5zdGFncmFtIiBocmVmPSJodHRwczovL3d3dy5pbnN0YWdyYW0uY29tL2FsaGFtYnJhX29maWNpYWwvIiB0YXJnZXQ9Il9ibGFuayI+PC9hPg0KICAgICAgICAgICAgPC9saT4NCiAgICAgICAgICAgIDxsaSBpZD0ibGlQaW50ZXJlc3QiPg0KICAgICAgICAgICAgICA8YSBpZD0ibGlua1BpbnRlcmVzdCIgY2xhc3M9Imljb24gaWNvbi1waW50ZXJlc3QiIHRpdGxlPSJQaW50ZXJlc3QiIGhyZWY9Imh0dHBzOi8vZXMucGludGVyZXN0LmNvbS9hbGhhbWJyYWdyYW5hZGEvIiB0YXJnZXQ9Il9ibGFuayI+PC9hPg0KICAgICAgICAgICAgPC9saT4NCiAgICAgICAgICA8L3VsPg0KICAgICAgICA8L2Rpdj4NCiAgICAgICAgPCEtLSAvL0NvbnRhY3RvIHkgUlJTUyAtLT4NCiAgICAgIDwvZGl2Pg0KICAgIDwvZGl2Pg0KICA8L2Rpdj4NCiAgPGRpdiBpZD0iZGl2Rm9vdGVyMyIgY2xhc3M9ImZvb3RlcjMiPg0KICAgIDxkaXYgY2xhc3M9ImNvbnRhaW5lciI+DQogICAgICA8ZGl2IGNsYXNzPSJmb290ZXItaXRlbSBjb2x1bW4tMSI+DQogICAgICAgIDxkaXYgY2xhc3M9ImxvZ28gbG9nb0Zvb3RlciI+DQogICAgICAgICAgPGEgaHJlZj0iaHR0cDovL3d3dy5hbGhhbWJyYS1wYXRyb25hdG8uZXMvIiB0YXJnZXQ9Il9ibGFuayI+DQogICAgICAgICAgICA8aW1nIGlkPSJpbWdGb290ZXIiIHNyYz0iL0FwcF9UaGVtZXMvQUxIQU1CUkEvaW1nL2xvZ29fcGF0cm9uYXRvLnBuZyIgYWx0PSJBbGhhbWJyYSB5IEdlbmVyYWxpZmUiPg0KICAgICAgICAgIDwvYT4NCiAgICAgIDwvZGl2Pg0KICAgICAgICA8cCBjbGFzcz0iZGVzaWduIj4NCiAgICAgICAgICA8c3BhbiBpZD0iZGV2ZWxvcGVkIj5Db3B5cmlnaHQgwqkgSUFDUE9TPC9zcGFuPg0KICAgICAgICA8L3A+DQogICAgICA8L2Rpdj4NCiAgICAgIDxkaXYgaWQ9ImRpdkRpcmVjY2lvbkZvb3RlciIgY2xhc3M9ImRpcmVjY2lvbiBmb290ZXItaXRlbSBjb2x1bW4tMSI+DQogICAgICAgIDxwPlBhdHJvbmF0byBkZSBsYSBBbGhhbWJyYSB5IEdlbmVyYWxpZmU8L3A+DQogICAgICAgICAgICAgICAgICAgIDxwPkMvIFJlYWwgZGUgbGEgQWxoYW1icmEgcy9uPC9wPg0KICAgICAgICAgICAgICAgICAgICA8cD5DUCAtIDE4MDA5IChHcmFuYWRhKTwvcD4NCiAgICAgIDwvZGl2Pg0KICAgIDwvZGl2Pg0KICA8L2Rpdj4NCjwvZm9vdGVyPh8GZ2QCDw8WAh8GaBYUAgIPZBYKAgEPZBYCAgEPDxYCHwMFKGh0dHBzOi8vd3d3LmZhY2Vib29rLmNvbS9hbGhhbWJyYWN1bHR1cmFkZAICD2QWAgIBDw8WAh8DBSZodHRwOi8vd3d3LnR3aXR0ZXIuY29tL2FsaGFtYnJhY3VsdHVyYWRkAgMPZBYCAgEPDxYCHwMFKGh0dHA6Ly93d3cueW91dHViZS5jb20vYWxoYW1icmFwYXRyb25hdG9kZAIED2QWAgIBDw8WAh8DBStodHRwczovL3d3dy5pbnN0YWdyYW0uY29tL2FsaGFtYnJhX29maWNpYWwvZGQCBQ9kFgICAQ8PFgIfAwUpaHR0cHM6Ly9lcy5waW50ZXJlc3QuY29tL2FsaGFtYnJhZ3JhbmFkYS9kZAIDD2QWBgIBD2QWAmYPDxYEHwQFKC9BcHBfVGhlbWVzL0FMSEFNQlJBL2ltZy9sb2dvLWZvb3Rlci5wbmcfBQUVQWxoYW1icmEgeSBHZW5lcmFsaWZlZGQCAw8WAh8HBZQBPHA+UGF0cm9uYXRvIGRlIGxhIEFsaGFtYnJhIHkgR2VuZXJhbGlmZTwvcD4NCiAgICAgICAgICAgICAgICAgICAgPHA+Qy8gUmVhbCBkZSBsYSBBbGhhbWJyYSBzL248L3A+DQogICAgICAgICAgICAgICAgICAgIDxwPkNQIC0gMTgwMDkgKEdyYW5hZGEpPC9wPmQCBQ8PFgIfAQUTQ29weXJpZ2h0IMKpIElBQ1BPU2RkAgQPDxYCHwMFKGh0dHBzOi8vd3d3LmZhY2Vib29rLmNvbS9hbGhhbWJyYWN1bHR1cmFkZAIFDw8WAh8DBSZodHRwOi8vd3d3LnR3aXR0ZXIuY29tL2FsaGFtYnJhY3VsdHVyYWRkAgYPDxYCHwMFK2h0dHBzOi8vd3d3Lmluc3RhZ3JhbS5jb20vYWxoYW1icmFfb2ZpY2lhbC9kZAIHDw8WAh8DBShodHRwOi8vd3d3LnlvdXR1YmUuY29tL2FsaGFtYnJhcGF0cm9uYXRvZGQCCA8PFgIfA2RkZAIJDw8WAh8DZGRkAgoPFgIfBwWUATxwPlBhdHJvbmF0byBkZSBsYSBBbGhhbWJyYSB5IEdlbmVyYWxpZmU8L3A+DQogICAgICAgICAgICAgICAgICAgIDxwPkMvIFJlYWwgZGUgbGEgQWxoYW1icmEgcy9uPC9wPg0KICAgICAgICAgICAgICAgICAgICA8cD5DUCAtIDE4MDA5IChHcmFuYWRhKTwvcD5kAgsPDxYCHwEFE0NvcHlyaWdodCDCqSBJQUNQT1NkZAIRDw8WAh8GaGQWBAIBD2QWBAIBDxYCHwEFxwQ8cCA+RWwgcmVzcG9uc2FibGUgZGUgZXN0ZSBzaXRpbyB3ZWIgZmlndXJhIGVuIG51ZXN0cm8gIDxhIGhyZWY9Imh0dHBzOi8vdGlja2V0cy5hbGhhbWJyYS1wYXRyb25hdG8uZXMvYXZpc28tbGVnYWwvIiA+QXZpc28gTGVnYWwgPC9hID4uIDxiciAvID5VdGlsaXphbW9zIGNvb2tpZXMgcHJvcGlhcyB5IG9wY2lvbmFsbWVudGUgcG9kZW1vcyB1dGlsaXphciBjb29raWVzIGRlIHRlcmNlcm9zLiBMYSBmaW5hbGlkYWQgZGUgbGFzIGNvb2tpZXMgdXRpbGl6YWRhcyBlczogZnVuY2lvbmFsZXMsIGFuYWzDrXRpY2FzIHkgcHVibGljaXRhcmlhcy4gTm8gc2UgdXNhbiBwYXJhIGxhIGVsYWJvcmFjacOzbiBkZSBwZXJmaWxlcy4gVXN0ZWQgcHVlZGUgY29uZmlndXJhciBlbCB1c28gZGUgY29va2llcyBlbiBlc3RlIG1lbnUuIDxiciAvID5QdWVkZSBvYnRlbmVyIG3DoXMgaW5mb3JtYWNpw7NuLCBvIGJpZW4gY29ub2NlciBjw7NtbyBjYW1iaWFyIGxhIGNvbmZpZ3VyYWNpw7NuLCBlbiBudWVzdHJhIDxiciAvID4gPGEgaHJlZj0iL3BvbGl0aWNhLWNvb2tpZXMuYXNweCIgPlBvbMOtdGljYSBkZSBjb29raWVzIDwvYSA+LjwvcCA+ZAIDDw8WAh8BBRhBY2VwdGFyIHRvZG8geSBjb250aW51YXJkZAIDD2QWCAIBDw8WAh8GaGRkAgMPFgIfAQXHBDxwID5FbCByZXNwb25zYWJsZSBkZSBlc3RlIHNpdGlvIHdlYiBmaWd1cmEgZW4gbnVlc3RybyAgPGEgaHJlZj0iaHR0cHM6Ly90aWNrZXRzLmFsaGFtYnJhLXBhdHJvbmF0by5lcy9hdmlzby1sZWdhbC8iID5BdmlzbyBMZWdhbCA8L2EgPi48YnIgLyA+IFV0aWxpemFtb3MgY29va2llcyBwcm9waWFzIHkgb3BjaW9uYWxtZW50ZSBwb2RlbW9zIHV0aWxpemFyIGNvb2tpZXMgZGUgdGVyY2Vyb3MuIExhIGZpbmFsaWRhZCBkZSBsYXMgY29va2llcyB1dGlsaXphZGFzIGVzOiBmdW5jaW9uYWxlcywgYW5hbMOtdGljYXMgeSBwdWJsaWNpdGFyaWFzLiBObyBzZSB1c2FuIHBhcmEgbGEgZWxhYm9yYWNpw7NuIGRlIHBlcmZpbGVzLiBVc3RlZCBwdWVkZSBjb25maWd1cmFyIGVsIHVzbyBkZSBjb29raWVzIGVuIGVzdGUgbWVudS4gPGJyIC8gPlB1ZWRlIG9idGVuZXIgbcOhcyBpbmZvcm1hY2nDs24sIG8gYmllbiBjb25vY2VyIGPDs21vIGNhbWJpYXIgbGEgY29uZmlndXJhY2nDs24sIGVuIG51ZXN0cmEgPGJyIC8gPiA8YSBocmVmPSIvcG9saXRpY2EtY29va2llcy5hc3B4IiA+UG9sw610aWNhIGRlIGNvb2tpZXMgPC9hID4uPC9wID5kAgcPDxYCHwEFGEFjZXB0YXIgdG9kbyB5IGNvbnRpbnVhcmRkAgkPDxYCHwEFIEFjZXB0YXIgc2VsZWNjaW9uYWRvIHkgY29udGludWFyZGQCAw8WBB8BBeIBPCEtLSBTdGFydCBvZiBjYXVhbGhhbWJyYSBaZW5kZXNrIFdpZGdldCBzY3JpcHQgLS0+DQo8c2NyaXB0IGlkPSJ6ZS1zbmlwcGV0IiBzcmM9aHR0cHM6Ly9zdGF0aWMuemRhc3NldHMuY29tL2Vrci9zbmlwcGV0LmpzP2tleT01YjdhZTEyOS05YTNjLTRkMmYtYjk0NC0xNDcyZGY5ZmI1MzM+IDwvc2NyaXB0Pg0KPCEtLSBFbmQgb2YgY2F1YWxoYW1icmEgWmVuZGVzayBXaWRnZXQgc2NyaXB0IC0tPh8GZ2QYAwUeX19Db250cm9sc1JlcXVpcmVQb3N0QmFja0tleV9fFgEFH2N0bDAwJGNoa1JlZ2lzdHJvQWNlcHRvUG9saXRpY2EFR2N0bDAwJENvbnRlbnRNYXN0ZXIxJHVjUmVzZXJ2YXJFbnRyYWRhc0Jhc2VBbGhhbWJyYTEkdWNJbXBvcnRhciRXaXphcmQxDxBkFCsBAWZmZAVXY3RsMDAkQ29udGVudE1hc3RlcjEkdWNSZXNlcnZhckVudHJhZGFzQmFzZUFsaGFtYnJhMSR1Y0ltcG9ydGFyJFdpemFyZDEkV2l6YXJkTXVsdGlWaWV3Dw9kZmRqUeGC771nXDjqOfYiFHoMzE1r2Q=="
                driver.execute_script(
                    f"document.getElementById('__VIEWSTATE').value = `{viewstate_funcional}`;"
                )

                time.sleep(2)

                # 4. Hacer clic de nuevo en el mismo botón
                boton = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable(
                        (By.ID, "ctl00_ContentMaster1_ucReservarEntradasBaseAlhambra1_btnIrPaso1")
                    )
                )
                boton.click()

                # if FALLOS_SEGUIDOS >= MAX_FALLOS:
                #     icon.icon = crear_icono_amarillo()
                #     print(" Reiniciando navegador por múltiples fallos...")
                #     logging.info(" Reiniciando navegador por múltiples fallos...")
                #     # alerta_sonora_reinicio()
                #     # driver.quit()
                #     # driver = iniciar_navegador()
                #     # minimizar_chrome(driver)  # Ocultar Chrome después de abrirlo
                #     # driver.refresh()
                #
                #     # navegar_y_preparar(driver)
                #
                #     driver.delete_all_cookies()
                #     driver.execute_script("window.localStorage.clear();")
                #     driver.execute_script("window.sessionStorage.clear();")
                #     driver.get('https://compratickets.alhambra-patronato.es/reservarEntradas.aspx?opc=142&gid=432&lg=es-ES&ca=0&m=GENERAL')
                #
                #     FALLOS_SEGUIDOS = 0
                #     continue
                # else:
                #     continue

            dias_tachados_actual = obtener_dias_tachados_completos(driver, viewState)
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

                enviar_telegram(f"¡Días liberados: {dias_liberados} en GENERAL detectados!")

                # dias_tachados_inicial = dias_tachados_actual

                # mensaje = "¡Días disponibles detectados!\nDías que ya no están tachados: " + ", ".join(
                #     sorted(dias_liberados, key=int))
                # notificar_popup(mensaje)

            if DETENER:
                print(" Deteniendo el script.")
                break

            if viewState == 0:
                espera = random.uniform(50, 60)
                print(f" Esperando {espera:.2f} segundos antes de volver a intentar...")
                time.sleep(espera)
            else:
                print(f" Esperando 20 segundos antes de volver a intentar...")
                time.sleep(20)

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

icono = Icon("Alhambra Script", crear_icono(), "Gestor de Calendarios General", menu)

iniciar(icono, None)

if __name__ == "__main__":
    icono.run()
