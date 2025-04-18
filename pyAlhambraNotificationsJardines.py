import threading
import tkinter as tk
from tkinter import messagebox
import datetime
import calendar
import pyautogui
from selenium.common import StaleElementReferenceException, NoAlertPresentException, UnexpectedAlertPresentException

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
ESTADO_FILE = "dias_tachados_inicial_jardines.pkl"

import time
import win32gui
import win32con

import logging

# Configurar el logging
logging.basicConfig(
    filename="jardines.log",  # Nombre del archivo donde se guardará el log
    level=logging.INFO,  # Nivel mínimo de mensajes a registrar (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format="%(asctime)s - %(levelname)s - %(message)s",  # Formato del mensaje de log
    datefmt="%Y-%m-%d %H:%M:%S"  # Formato de fecha
)


def enviar_telegram(mensaje, onlyMiguel=0):
    url = "https://api.telegram.org/bot7908020608:AAEGRux_wQ8tlKxPoMEGLR5vMtG1X3LW2WY/sendMessage"
    chat_belen = [8120620954, 7225762073]  # Belén (dos IDs diferentes)
    chat_miguel = [780778418]  # Miguel

    # chat_ids = chat_belen + chat_miguel

    if onlyMiguel:
        chat_ids = chat_miguel
    else:
        chat_ids = chat_belen

    if onlyMiguel:
        chat_ids = chat_miguel

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
    mes_actual_num = datetime.datetime.now().month  # Ejemplo: 3 (marzo)
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
            boton_mes_anterior = WebDriverWait(driver, 5).until(
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
        dias_mes_actual = WebDriverWait(driver, 5).until(
            EC.presence_of_all_elements_located((
                By.CSS_SELECTOR,
                "#ctl00_ContentMaster1_ucReservarEntradasBaseAlhambra1_ucCalendarioPaso1_calendarioFecha .calendario_padding.no-dispo"
            ))
        )
    except Exception as e:
        print(f"No se pudieron cargar los días del mes actual: {e}")
        dias_mes_actual = []

    try:
        dias_total.extend([
            f"{mes_actual_nombre}-{dia.text.strip()}"
            for dia in dias_mes_actual if dia.text.strip()
        ])
    except StaleElementReferenceException:
        print("Uno o más elementos se volvieron obsoletos (stale) al intentar leer el mes actual.")

    logging.info(f"Días extraído del mes actual (innerText): '{dias_total}'")
    print(f"Días extraído del mes actual (innerText): '{dias_total}'")

    if (True):
        # 🔹 Avanzar al mes siguiente

        try:
            boton_mes_siguiente = WebDriverWait(driver, 5).until(
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
                try:
                    texto_dia = dia.get_attribute("innerText").strip()
                    if texto_dia.isdigit():
                        dias_total.append(f"{mes_siguiente_nombre}-{texto_dia}")
                except StaleElementReferenceException:
                    continue  # Ignorar elementos stale
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


def manejar_alerta_si_existe(driver):
    try:
        alert = driver.switch_to.alert
        mensaje = alert.text
        print(f" Alerta detectada: {mensaje}")
        logging.warning(f" Alerta detectada: {mensaje}")
        alert.accept()  # También puedes usar alert.dismiss() si corresponde
        print(" Alerta aceptada.")
    except NoAlertPresentException:
        pass
    except UnexpectedAlertPresentException as e:
        print(f" Error inesperado con alerta: {e}")
        logging.error(f" Error inesperado con alerta: {e}")


def convertir_a_fecha(fecha_str):
    try:
        return datetime.datetime.strptime(fecha_str, "%B-%d").replace(year=datetime.datetime.now().year).date()
    except ValueError:
        return None


def ejecutar_script(icon):
    try:

        global DETENER, FALLOS_SEGUIDOS

        random_port = random.randint(9200, 9400)

        def iniciar_navegador():

            ruta_perfil_chrome = os.path.join(os.getenv("LOCALAPPDATA"), "Google", "Chrome", "User Data", "Perfil3")

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
            URL_RESERVAS_JARDINES = 'https://compratickets.alhambra-patronato.es/reservarEntradas.aspx?opc=143&gid=432&lg=es&ca=0&m=GENERAL'

            driver.get(URL_RESERVAS_JARDINES)
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
                    WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable(
                            (By.ID, "ctl00_ContentMaster1_ucReservarEntradasBaseAlhambra1_btnIrPaso1"))
                    ).click()
                    # time.sleep(TIEMPO)

                except Exception:
                    print("Botón de paso 1 ya pulsado.")

                # Esperar a que desaparezca la capa de carga si existe
                try:
                    WebDriverWait(driver, 5).until(
                        EC.invisibility_of_element_located((By.ID, "divCargando"))
                    )
                except:
                    print("La capa de carga no desapareció, se continúa de todas formas.")

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
                viewstate_funcional = "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OTUyZxAFBDE5NTMFBDE5NTNnEAUEMTk1NAUEMTk1NGcQBQQxOTU1BQQxOTU1ZxAFBDE5NTYFBDE5NTZnEAUEMTk1NwUEMTk1N2cQBQQxOTU4BQQxOTU4ZxAFBDE5NTkFBDE5NTlnEAUEMTk2MAUEMTk2MGcQBQQxOTYxBQQxOTYxZxAFBDE5NjIFBDE5NjJnEAUEMTk2MwUEMTk2M2cQBQQxOTY0BQQxOTY0ZxAFBDE5NjUFBDE5NjVnEAUEMTk2NgUEMTk2NmcQBQQxOTY3BQQxOTY3ZxAFBDE5NjgFBDE5NjhnEAUEMTk2OQUEMTk2OWcQBQQxOTcwBQQxOTcwZxAFBDE5NzEFBDE5NzFnEAUEMTk3MgUEMTk3MmcQBQQxOTczBQQxOTczZxAFBDE5NzQFBDE5NzRnEAUEMTk3NQUEMTk3NWcQBQQxOTc2BQQxOTc2ZxAFBDE5NzcFBDE5NzdnEAUEMTk3OAUEMTk3OGcQBQQxOTc5BQQxOTc5ZxAFBDE5ODAFBDE5ODBnEAUEMTk4MQUEMTk4MWcQBQQxOTgyBQQxOTgyZxAFBDE5ODMFBDE5ODNnEAUEMTk4NAUEMTk4NGcQBQQxOTg1BQQxOTg1ZxAFBDE5ODYFBDE5ODZnEAUEMTk4NwUEMTk4N2cQBQQxOTg4BQQxOTg4ZxAFBDE5ODkFBDE5ODlnEAUEMTk5MAUEMTk5MGcQBQQxOTkxBQQxOTkxZxAFBDE5OTIFBDE5OTJnEAUEMTk5MwUEMTk5M2cQBQQxOTk0BQQxOTk0ZxAFBDE5OTUFBDE5OTVnEAUEMTk5NgUEMTk5NmcQBQQxOTk3BQQxOTk3ZxAFBDE5OTgFBDE5OThnEAUEMTk5OQUEMTk5OWcQBQQyMDAwBQQyMDAwZxAFBDIwMDEFBDIwMDFnEAUEMjAwMgUEMjAwMmcQBQQyMDAzBQQyMDAzZxAFBDIwMDQFBDIwMDRnEAUEMjAwNQUEMjAwNWcQBQQyMDA2BQQyMDA2ZxAFBDIwMDcFBDIwMDdnEAUEMjAwOAUEMjAwOGcQBQQyMDA5BQQyMDA5ZxAFBDIwMTAFBDIwMTBnEAUEMjAxMQUEMjAxMWcQBQQyMDEyBQQyMDEyZxAFBDIwMTMFBDIwMTNnEAUEMjAxNAUEMjAxNGcQBQQyMDE1BQQyMDE1ZxAFBDIwMTYFBDIwMTZnEAUEMjAxNwUEMjAxN2cQBQQyMDE4BQQyMDE4ZxAFBDIwMTkFBDIwMTlnEAUEMjAyMAUEMjAyMGcQBQQyMDIxBQQyMDIxZxAFBDIwMjIFBDIwMjJnEAUEMjAyMwUEMjAyM2cQBQQyMDI0BQQyMDI0ZxAFBDIwMjUFBDIwMjVnFgFmZAILDxYCHwZoFgICAQ8WAh8HZGQCDA9kFgICAQ8WAh8HBQVFbWFpbGQCDQ9kFgICAQ8WAh8HBQ5Db25maXJtYSBFbWFpbGQCDg9kFgICAQ8WAh8HBQtDb250cmFzZcOxYWQCDw9kFgICAQ8WAh8HBRNSZXBldGlyIENvbnRyYXNlw7FhZAIQDxYCHwZoFgICAQ8WAh8HZWQCEQ8WAh8GaBYCAgEPFgIfB2VkAhIPFgIfBmgWAgIBDxYCHwdlZAITDxYCHwZoFgYCAQ8WAh8HZWQCAw8PFgQeCENzc0NsYXNzBRJpbnB1dC10ZXh0IG9jdWx0YXIeBF8hU0ICAmRkAgUPEA8WBB8JZR8KAgJkEBU1FFNlbGVjY2lvbmUgcHJvdmluY2lhCEFsYmFjZXRlCEFsaWNhbnRlCEFsbWVyw61hBsOBbGF2YQhBc3R1cmlhcwbDgXZpbGEHQmFkYWpveg1CYWxlYXJzIElsbGVzCUJhcmNlbG9uYQdCaXprYWlhBkJ1cmdvcwhDw6FjZXJlcwZDw6FkaXoJQ2FudGFicmlhCkNhc3RlbGzDs24LQ2l1ZGFkIFJlYWwIQ8OzcmRvYmEJQ29ydcOxYSBBBkN1ZW5jYQhHaXB1emtvYQZHaXJvbmEHR3JhbmFkYQtHdWFkYWxhamFyYQZIdWVsdmEGSHVlc2NhBUphw6luBUxlw7NuBkxsZWlkYQRMdWdvBk1hZHJpZAdNw6FsYWdhBk11cmNpYQdOYXZhcnJhB091cmVuc2UIUGFsZW5jaWEKUGFsbWFzIExhcwpQb250ZXZlZHJhCFJpb2phIExhCVNhbGFtYW5jYRZTYW50YSBDcnV6IGRlIFRlbmVyaWZlB1NlZ292aWEHU2V2aWxsYQVTb3JpYQlUYXJyYWdvbmEGVGVydWVsBlRvbGVkbwhWYWxlbmNpYQpWYWxsYWRvbGlkBlphbW9yYQhaYXJhZ296YQVDZXV0YQdNZWxpbGxhFTUAAjAyAjAzAjA0AjAxAjMzAjA1AjA2AjA3AjA4AjQ4AjA5AjEwAjExAjM5AjEyAjEzAjE0AjE1AjE2AjIwAjE3AjE4AjE5AjIxAjIyAjIzAjI0AjI1AjI3AjI4AjI5AjMwAjMxAjMyAjM0AjM1AjM2AjI2AjM3AjM4AjQwAjQxAjQyAjQzAjQ0AjQ1AjQ2AjQ3AjQ5AjUwAjUxAjUyFCsDNWdnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnFgFmZAIUD2QWBgIBDxYCHwcFBVBhw61zZAIDDw8WAh8GaGRkAgUPEGQQFe8BE1NlbGVjY2lvbmUgdW4gcGHDrXMJQXJnZW50aW5hCUF1c3RyYWxpYQVDaGluYQVJdGFseQVKYXBhbgZNZXhpY28LTmV3IFplYWxhbmQIUG9ydHVnYWwHRXNwYcOxYQdHZXJtYW55BkZyYW5jZRJSdXNzaWFuIEZlZGVyYXRpb24OVW5pdGVkIEtpbmdkb20UVW5pdGVkIFN0YXRlcyBvZiBBbWULQWZnaGFuaXN0YW4HQWxiYW5pYQdBbGdlcmlhDkFtZXJpY2FuIFNhbW9hB0FuZG9ycmEGQW5nb2xhCEFuZ3VpbGxhCkFudGFyY3RpY2EHQW50aWd1YQdBcm1lbmlhBUFydWJhB0F1c3RyaWEKQXplcmJhaWphbgdCYWhhbWFzB0JhaHJhaW4KQmFuZ2xhZGVzaAhCYXJiYWRvcwdCZWxhcnVzB0JlbGdpdW0GQmVsaXplBUJlbmluB0Jlcm11ZGEGQmh1dGFuB0JvbGl2aWEGQm9zbmlhCEJvdHN3YW5hDUJvdXZldCBJc2xhbmQGQnJhemlsDkJyaXRpc2ggSW5kaWFuEUJydW5laSBEYXJ1c3NhbGFtCEJ1bGdhcmlhDEJ1cmtpbmEgRmFzbwdCdXJ1bmRpCENhbWJvZGlhCENhbWVyb29uBkNhbmFkYQpDYXBlIFZlcmRlDkNheW1hbiBJc2xhbmRzE0NlbnRyYWwgQWZyaWNhbiBSZXAEQ2hhZAVDaGlsZRBDaHJpc3RtYXMgSXNsYW5kDUNvY29zIElzbGFuZHMIQ29sb21iaWEHQ29tb3JvcwVDb25nbwxDb29rIElzbGFuZHMKQ29zdGEgUmljYQdDcm9hdGlhBEN1YmEGQ3lwcnVzDkN6ZWNoIFJlcHVibGljB0Rlbm1hcmsIRGppYm91dGkIRG9taW5pY2ESRG9taW5pY2FuIFJlcHVibGljCkVhc3QgVGltb3IHRWN1YWRvcgVFZ3lwdAtFbCBTYWx2YWRvchFFcXVhdG9yaWFsIEd1aW5lYQdFcml0cmVhB0VzdG9uaWEIRXRoaW9waWENRmFyb2UgSXNsYW5kcwRGaWppB0ZpbmxhbmQNRnJlbmNoIEd1aWFuYRBGcmVuY2ggUG9seW5lc2lhBUdhYm9uBkdhbWJpYQdHZW9yZ2lhBUdoYW5hBkdyZWVjZQlHcmVlbmxhbmQHR3JlbmFkYQpHdWFkZWxvdXBlBEd1YW0JR3VhdGVtYWxhBkd1aW5lYQ1HdWluZWEgQmlzc2F1Bkd1eWFuYQVIYWl0aQhIb25kdXJhcwlIb25nIEtvbmcHSHVuZ2FyeQdJY2VsYW5kBUluZGlhCUluZG9uZXNpYQRJcmFuBElyYXEHSXJlbGFuZAZJc3JhZWwLSXZvcnkgQ29hc3QHSmFtYWljYQZKb3JkYW4KS2F6YWtoc3RhbgVLZW55YQhLaXJpYmF0aQZLdXdhaXQKS3lyZ3l6c3RhbgNMYW8GTGF0dmlhB0xlYmFub24HTGVzb3RobwdMaWJlcmlhBUxpYnlhDUxpZWNodGVuc3RlaW4JTGl0aHVhbmlhCkx1eGVtYm91cmcFTWFjYXUJTWFjZWRvbmlhCk1hZGFnYXNjYXIGTWFsYXdpCE1hbGF5c2lhCE1hbGRpdmVzBE1hbGkFTWFsdGEITWFsdmluYXMQTWFyc2hhbGwgSXNsYW5kcwpNYXJ0aW5pcXVlCk1hdXJpdGFuaWEJTWF1cml0aXVzB01heW90dGUKTWljcm9uZXNpYQdNb2xkb3ZhBk1vbmFjbwhNb25nb2xpYQpNb250ZW5lZ3JvCk1vbnRzZXJyYXQHTW9yb2NjbwpNb3phbWJpcXVlB015YW5tYXIHTmFtaWJpYQVOYXVydQVOZXBhbAtOZXRoZXJsYW5kcxROZXRoZXJsYW5kcyBBbnRpbGxlcw1OZXcgQ2FsZWRvbmlhCU5pY2FyYWd1YQVOaWdlcgdOaWdlcmlhBE5pdWUOTm9yZm9sayBJc2xhbmQLTm9ydGggS29yZWETTm9ydGhlcm4gTWFyaWFuYSBJcwZOb3J3YXkET21hbhlPdHJvcyBkZSBwYWlzZXMgZGVsIG11bmRvCFBha2lzdGFuBVBhbGF1BlBhbmFtYRBQYXB1YSBOZXcgR3VpbmVhCFBhcmFndWF5BFBlcnULUGhpbGlwcGluZXMIUGl0Y2Fpcm4GUG9sYW5kC1B1ZXJ0byBSaWNvBVFhdGFyB1JldW5pb24HUm9tYW5pYQZSd2FuZGEPUyBHZW9yZ2lhIFNvdXRoC1NhaW50IEx1Y2lhBVNhbW9hClNhbiBNYXJpbm8TU2FvIFRvbWUgLSBQcmluY2lwZQxTYXVkaSBBcmFiaWEHU2VuZWdhbAZTZXJiaWEKU2V5Y2hlbGxlcwxTaWVycmEgTGVvbmUJU2luZ2Fwb3JlCFNsb3Zha2lhCFNsb3ZlbmlhD1NvbG9tb24gSXNsYW5kcwdTb21hbGlhDFNvdXRoIEFmcmljYQtTb3V0aCBLb3JlYQlTcmkgTGFua2EJU3QgSGVsZW5hElN0IEtpdHRzIGFuZCBOZXZpcxNTdCBQaWVycmUgIE1pcXVlbG9uEVN0IFZpbmNlbnQtR3JlbmFkBVN1ZGFuCFN1cmluYW1lEVN2YWxiYXJkIEphbiBNIElzCVN3YXppbGFuZAZTd2VkZW4LU3dpdHplcmxhbmQFU3lyaWEGVGFpd2FuClRhamlraXN0YW4IVGFuemFuaWEIVGhhaWxhbmQEVG9nbwdUb2tlbGF1BVRvbmdhE1RyaW5pZGFkIEFuZCBUb2JhZ28HVHVuaXNpYQZUdXJrZXkMVHVya21lbmlzdGFuFFR1cmtzIENhaWNvcyBJc2xhbmRzBlR1dmFsdQZVZ2FuZGEHVWtyYWluZRRVbml0ZWQgQXJhYiBFbWlyYXRlcwdVcnVndWF5EFVTIE1pbm9yIElzbGFuZHMKVXpiZWtpc3RhbgdWYW51YXR1B1ZhdGljYW4JVmVuZXp1ZWxhB1ZpZXRuYW0OVmlyZ2luIElzbGFuZHMRVmlyZ2luIElzbGFuZHMgVVMQV2FsbGlzIEZ1dHVuYSBJcw5XZXN0ZXJuIFNhaGFyYQVZZW1lbgpZdWdvc2xhdmlhBVphaXJlBlphbWJpYQhaaW1iYWJ3ZRXvAQADMDMyAzAzNgMxNTYDMzgwAzM5MgM0ODQDNTU0AzYyMAM3MjQDMjc2AzI1MAM2NDMDODI2Azg0MAMwMDQDMDA4AzAxMgMwMTYDMDIwAzAyNAM2NjADMDEwAzAyOAMwNTEDNTMzAzA0MAMwMzEDMDQ0AzA0OAMwNTADMDUyAzExMgMwNTYDMDg0AzIwNAMwNjADMDY0AzA2OAMwNzADMDcyAzA3NAMwNzYDMDg2AzA5NgMxMDADODU0AzEwOAMxMTYDMTIwAzEyNAMxMzIDMTM2AzE0MAMxNDgDMTUyAzE2MgMxNjYDMTcwAzE3NAMxNzgDMTg0AzE4OAMxOTEDMTkyAzE5NgMyMDMDMjA4AzI2MgMyMTIDMjE0AzYyNgMyMTgDODE4AzIyMgMyMjYDMjMyAzIzMwMyMzEDMjM0AzI0MgMyNDYDMjU0AzI1OAMyNjYDMjcwAzI2OAMyODgDMzAwAzMwNAMzMDgDMzEyAzMxNgMzMjADMzI0AzYyNAMzMjgDMzMyAzM0MAMzNDQDMzQ4AzM1MgMzNTYDMzYwAzM2NAMzNjgDMzcyAzM3NgMzODQDMzg4AzQwMAMzOTgDNDA0AzI5NgM0MTQDNDE3AzQxOAM0MjgDNDIyAzQyNgM0MzADNDM0AzQzOAM0NDADNDQyAzQ0NgM4MDcDNDUwAzQ1NAM0NTgDNDYyAzQ2NgM0NzADMjM4AzU4NAM0NzQDNDc4AzQ4MAMxNzUDNTgzAzQ5OAM0OTIDNDk2AzQ5OQM1MDADNTA0AzUwOAMxMDQDNTE2AzUyMAM1MjQDNTI4AzUzMAM1NDADNTU4AzU2MgM1NjYDNTcwAzU3NAM0MDgDNTgwAzU3OAM1MTIDNzQ0AzU4NgM1ODUDNTkxAzU5OAM2MDADNjA0AzYwOAM2MTIDNjE2AzYzMAM2MzQDNjM4AzY0MgM2NDYDMjM5AzY2MgM4ODIDNjc0AzY3OAM2ODIDNjg2AzY4OAM2OTADNjk0AzcwMgM3MDMDNzA1AzA5MAM3MDYDNzEwAzQxMAMxNDQDNjU0AzY1OQM2NjYDNjcwAzczNgM3NDADNzQ0Azc0OAM3NTIDNzU2Azc2MAMxNTgDNzYyAzgzNAM3NjQDNzY4Azc3MgM3NzYDNzgwAzc4OAM3OTIDNzk1Azc5NgM3OTgDODAwAzgwNAM3ODQDODU4AzU4MQM4NjADNTQ4AzMzNgM4NjIDNzA0AzA5MgM4NTADODc2AzczMgM4ODcDODkxAzE4MAM4OTQDNzE2FCsD7wFnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2RkAhUPZBYCAgEPFgIfBwUJVGVsw6lmb25vZAIXD2QWAgIDDxYCHwcFiQFIZSBsZcOtZG8geSBhY2VwdG8gbGEgPGEgaHJlZj0iaHR0cHM6Ly90aWNrZXRzLmFsaGFtYnJhLXBhdHJvbmF0by5lcy9wb2xpdGljYS1kZS1wcml2YWNpZGFkLyIgdGFyZ2V0PSJfYmxhbmsiPlBvbMOtdGljYSBkZSBwcml2YWNpZGFkPC9hPmQCGA8WAh8GaBYCAgMPFgIfB2VkAggPDxYCHwEFC1JlZ8Otc3RyZXNlZGQCAw8WAh8GaBYEAgMPDxYCHwMFHi9yZXNlcnZhckVudHJhZGFzLmFzcHg/b3BjPTE0M2RkAgUPDxYCHwEFDkNlcnJhciBzZXNpw7NuZGQCAQ9kFgICAQ8PFgQfCQUGYWN0aXZlHwoCAmRkAgIPDxYEHwMFPmh0dHBzOi8vd3d3LmFsaGFtYnJhLXBhdHJvbmF0by5lcy92aXNpdGFyL3ByZWd1bnRhcy1mcmVjdWVudGVzHwZnZGQCBA9kFgICAQ8PFgIfAwUoaHR0cDovL3d3dy55b3V0dWJlLmNvbS9hbGhhbWJyYXBhdHJvbmF0b2RkAgUPZBYCAgEPDxYCHwMFK2h0dHBzOi8vd3d3Lmluc3RhZ3JhbS5jb20vYWxoYW1icmFfb2ZpY2lhbC9kZAIGD2QWAgIBDw8WAh8DBShodHRwczovL3d3dy5mYWNlYm9vay5jb20vYWxoYW1icmFjdWx0dXJhZGQCBw9kFgICAQ8PFgIfAwUmaHR0cDovL3d3dy50d2l0dGVyLmNvbS9hbGhhbWJyYWN1bHR1cmFkZAIID2QWAgIBDw8WAh8DBSlodHRwczovL2VzLnBpbnRlcmVzdC5jb20vYWxoYW1icmFncmFuYWRhL2RkAgkPFgIfBmhkAgoPFgIfBmgWAgIBDw8WAh8DZGQWAmYPDxYCHwUFFUFsaGFtYnJhIHkgR2VuZXJhbGlmZWRkAgsPZBYCZg8PFgQfAwU+aHR0cHM6Ly93d3cuYWxoYW1icmEtcGF0cm9uYXRvLmVzL3Zpc2l0YXIvcHJlZ3VudGFzLWZyZWN1ZW50ZXMfBmdkZAIND2QWCAIBDw8WAh8GaGQWAgIBD2QWAmYPZBYGAgMPDxYCHwZoZGQCBA8PFgIeBkVzdGFkb2ZkFgJmD2QWAgIBD2QWAmYPZBYCAgEPZBYCAggPFgIfBmhkAg4PZBYEAgsPZBYEAgEPZBYCAgMPEGRkFgBkAgYPZBYCAgcPEGRkFgBkAg0PZBYEAgYPZBYCAgEPZBYCAgMPEGRkFgBkAgkPZBYCAgcPEGRkFgBkAgMPDxYCHwZoZBYCZg9kFgJmD2QWBgIBDw8WAh8GaGRkAggPZBYGAgUPZBYCAgEPEGRkFgBkAgYPZBYCAgEPEGRkFgBkAggPZBYEZg8QZGQWAGQCAQ8QZGQWAGQCCg9kFgICBQ9kFg4CAw9kFgICBQ8QZGQWAGQCBA9kFgICAw8QZGQWAGQCBg9kFgICBw8QZGQWAGQCCA9kFgICBQ8QZGQWAGQCCQ9kFgICBQ8QZGQWAGQCDw9kFgICBw8QZGQWAGQCFg9kFgQCAQ9kFgICAw8QZGQWAGQCBg9kFgICBw8QZGQWAGQCBQ8PFgIfBmhkFgJmD2QWAmYPZBYEAgMPDxYCHwtmZBYCZg9kFgICAQ9kFgJmD2QWAgIBD2QWAgIIDxYCHwZoZAIGD2QWAmYPZBYCAgEPZBYCZg9kFgICAQ88KwAKAQAPFgQeDVByZXZNb250aFRleHRlHg1OZXh0TW9udGhUZXh0BS08aW1nIHNyYz0vQXBwX3RoZW1lcy9BTEhBTUJSQS9pbWcvbmV4dC5wbmcgLz5kZAIHDw8WIB4UTG9jYWxpemFkb3JQYXJhbWV0cm9kHhBGaW5hbGl6YXJNZW5vcmVzaB4OQWZvcm9QYXJhbWV0cm8CAR4GUGFnYWRhBQVGYWxzZR4HU2ltYm9sbwUD4oKsHhNFbmxhY2VNZW51UGFyYW1ldHJvBQdHRU5FUkFMHgxTZXNpb25EaWFyaWFoHgpOb21pbmFjaW9uZh4MQ2FwdGNoYVBhc28xZx4MTnVtRGVjaW1hbGVzAgIeD0NhcHRjaGFWYWxpZGFkb2ceCFNpbkZlY2hhZh4VRmVjaGFNaW5pbWFEaXNwb25pYmxlBv8/N/R1KMorHgxUZW5lbW9zTmlub3NoHhZHcnVwb0ludGVybmV0UGFyYW1ldHJvBQMxNDMeDFNlc2lvbkFjdHVhbAUfNG1vZXBsNDVubWZiYzNpMXhlbHlnZHVrMzA1OTEwNmQWBAIBD2QWAmYPZBYiAgMPDxYCHwZoZGQCBA8PFgIfC2ZkFgJmD2QWAgIBD2QWAmYPZBYCAgEPZBYGZg8PFgIfAQUFZW1haWxkZAICDw8WAh8BBQxUZWxlZm9ubyBTTVNkZAIIDxYCHwZoZAIFDw8WAh8DBTBodHRwczovL3d3dy5hbGhhbWJyYS1wYXRyb25hdG8uZXMvP2NhPTAmbGc9ZXMtRVNkZAIGDxYCHwFlZAIHDxYCHwEFJlZpc2l0YSBKYXJkaW5lcywgR2VuZXJhbGlmZSB5IEFsY2F6YWJhZAIIDxYCHgVjbGFzcwUWc3RlcC10aXRsZSBzdGVwLWFjdGl2ZRYCAgEPFgIfAWRkAgkPDxYCHwZoZBYCAgEPDxYCHwEFC0lyIGEgcGFzbyAxZGQCCg8PFgIfBmdkFghmDxYCHwFlZAIBDxYCHwFlZAIGDw8WHB4RRmVjaGFNaW5pbWFHbG9iYWwGAN+AOmZ43QgeBFBhc28CAR4NR3J1cG9JbnRlcm5ldAUDMTQzHhVUb3RhbE1lc2VzQWRlbGFudGFkb3MCAR4MRGF0b3NGZXN0aXZvMrsEAAEAAAD/////AQAAAAAAAAAMAgAAAEhBcHBfQ29kZS54aGpwdml6bywgVmVyc2lvbj0wLjAuMC4wLCBDdWx0dXJlPW5ldXRyYWwsIFB1YmxpY0tleVRva2VuPW51bGwFAQAAAB9EYXRvc0Zlc3Rpdm9zK0RhdG9zTGlzdEZlc3Rpdm9zAQAAABFfTHN0RGF0b3NGZXN0aXZvcwOJAVN5c3RlbS5Db2xsZWN0aW9ucy5HZW5lcmljLkxpc3RgMVtbRGF0b3NGZXN0aXZvcytEYXRvc0Zlc3Rpdm8sIEFwcF9Db2RlLnhoanB2aXpvLCBWZXJzaW9uPTAuMC4wLjAsIEN1bHR1cmU9bmV1dHJhbCwgUHVibGljS2V5VG9rZW49bnVsbF1dAgAAAAkDAAAABAMAAACJAVN5c3RlbS5Db2xsZWN0aW9ucy5HZW5lcmljLkxpc3RgMVtbRGF0b3NGZXN0aXZvcytEYXRvc0Zlc3Rpdm8sIEFwcF9Db2RlLnhoanB2aXpvLCBWZXJzaW9uPTAuMC4wLjAsIEN1bHR1cmU9bmV1dHJhbCwgUHVibGljS2V5VG9rZW49bnVsbF1dAwAAAAZfaXRlbXMFX3NpemUIX3ZlcnNpb24EAAAcRGF0b3NGZXN0aXZvcytEYXRvc0Zlc3Rpdm9bXQIAAAAICAkEAAAAAAAAAAAAAAAHBAAAAAABAAAAAAAAAAQaRGF0b3NGZXN0aXZvcytEYXRvc0Zlc3Rpdm8CAAAACx4TTWluaW1vR3J1cG9JbnRlcm5ldAIBHhFGZWNoYU1heGltYUdsb2JhbAYAusZyFKfeCB4PRGlyZWNjaW9uQWN0dWFsBQRQcmV2Hg1Fc0xpc3RhRXNwZXJhaB4LRm9yemFyQ2FyZ2FoHg5GZWNoYXNWaWdlbmNpYTKIDQABAAAA/////wEAAAAAAAAABAEAAADiAVN5c3RlbS5Db2xsZWN0aW9ucy5HZW5lcmljLkRpY3Rpb25hcnlgMltbU3lzdGVtLlN0cmluZywgbXNjb3JsaWIsIFZlcnNpb249NC4wLjAuMCwgQ3VsdHVyZT1uZXV0cmFsLCBQdWJsaWNLZXlUb2tlbj1iNzdhNWM1NjE5MzRlMDg5XSxbU3lzdGVtLlN0cmluZywgbXNjb3JsaWIsIFZlcnNpb249NC4wLjAuMCwgQ3VsdHVyZT1uZXV0cmFsLCBQdWJsaWNLZXlUb2tlbj1iNzdhNWM1NjE5MzRlMDg5XV0EAAAAB1ZlcnNpb24IQ29tcGFyZXIISGFzaFNpemUNS2V5VmFsdWVQYWlycwADAAMIkgFTeXN0ZW0uQ29sbGVjdGlvbnMuR2VuZXJpYy5HZW5lcmljRXF1YWxpdHlDb21wYXJlcmAxW1tTeXN0ZW0uU3RyaW5nLCBtc2NvcmxpYiwgVmVyc2lvbj00LjAuMC4wLCBDdWx0dXJlPW5ldXRyYWwsIFB1YmxpY0tleVRva2VuPWI3N2E1YzU2MTkzNGUwODldXQjmAVN5c3RlbS5Db2xsZWN0aW9ucy5HZW5lcmljLktleVZhbHVlUGFpcmAyW1tTeXN0ZW0uU3RyaW5nLCBtc2NvcmxpYiwgVmVyc2lvbj00LjAuMC4wLCBDdWx0dXJlPW5ldXRyYWwsIFB1YmxpY0tleVRva2VuPWI3N2E1YzU2MTkzNGUwODldLFtTeXN0ZW0uU3RyaW5nLCBtc2NvcmxpYiwgVmVyc2lvbj00LjAuMC4wLCBDdWx0dXJlPW5ldXRyYWwsIFB1YmxpY0tleVRva2VuPWI3N2E1YzU2MTkzNGUwODldXVtdBwAAAAkCAAAABwAAAAkDAAAABAIAAACSAVN5c3RlbS5Db2xsZWN0aW9ucy5HZW5lcmljLkdlbmVyaWNFcXVhbGl0eUNvbXBhcmVyYDFbW1N5c3RlbS5TdHJpbmcsIG1zY29ybGliLCBWZXJzaW9uPTQuMC4wLjAsIEN1bHR1cmU9bmV1dHJhbCwgUHVibGljS2V5VG9rZW49Yjc3YTVjNTYxOTM0ZTA4OV1dAAAAAAcDAAAAAAEAAAAHAAAAA+QBU3lzdGVtLkNvbGxlY3Rpb25zLkdlbmVyaWMuS2V5VmFsdWVQYWlyYDJbW1N5c3RlbS5TdHJpbmcsIG1zY29ybGliLCBWZXJzaW9uPTQuMC4wLjAsIEN1bHR1cmU9bmV1dHJhbCwgUHVibGljS2V5VG9rZW49Yjc3YTVjNTYxOTM0ZTA4OV0sW1N5c3RlbS5TdHJpbmcsIG1zY29ybGliLCBWZXJzaW9uPTQuMC4wLjAsIEN1bHR1cmU9bmV1dHJhbCwgUHVibGljS2V5VG9rZW49Yjc3YTVjNTYxOTM0ZTA4OV1dBPz////kAVN5c3RlbS5Db2xsZWN0aW9ucy5HZW5lcmljLktleVZhbHVlUGFpcmAyW1tTeXN0ZW0uU3RyaW5nLCBtc2NvcmxpYiwgVmVyc2lvbj00LjAuMC4wLCBDdWx0dXJlPW5ldXRyYWwsIFB1YmxpY0tleVRva2VuPWI3N2E1YzU2MTkzNGUwODldLFtTeXN0ZW0uU3RyaW5nLCBtc2NvcmxpYiwgVmVyc2lvbj00LjAuMC4wLCBDdWx0dXJlPW5ldXRyYWwsIFB1YmxpY0tleVRva2VuPWI3N2E1YzU2MTkzNGUwODldXQIAAAADa2V5BXZhbHVlAQEGBQAAAAM0MzIGBgAAABcjMTAvMDQvMjAyNS0zMC8wNC8yMDI1IwH5/////P///wYIAAAAAzQzMwYJAAAAFyMxMC8wNC8yMDI1LTMwLzA0LzIwMjUjAfb////8////BgsAAAADNDg4BgwAAAAXIzEwLzA0LzIwMjUtMzAvMDQvMjAyNSMB8/////z///8GDgAAAAM0MzQGDwAAABcjMTAvMDQvMjAyNS0zMC8wNC8yMDI1IwHw/////P///wYRAAAAAzQ4NgYSAAAAFyMxMC8wNC8yMDI1LTMwLzA0LzIwMjUjAe3////8////BhQAAAADNDg3BhUAAAAXIzEwLzA0LzIwMjUtMzAvMDQvMjAyNSMB6v////z///8GFwAAAAM0ODkGGAAAABcjMTAvMDQvMjAyNS0zMC8wNC8yMDI1IwsfBmceEENhbnRpZGFkRW50cmFkYXMy2wQAAQAAAP////8BAAAAAAAAAAQBAAAA4QFTeXN0ZW0uQ29sbGVjdGlvbnMuR2VuZXJpYy5EaWN0aW9uYXJ5YDJbW1N5c3RlbS5TdHJpbmcsIG1zY29ybGliLCBWZXJzaW9uPTQuMC4wLjAsIEN1bHR1cmU9bmV1dHJhbCwgUHVibGljS2V5VG9rZW49Yjc3YTVjNTYxOTM0ZTA4OV0sW1N5c3RlbS5JbnQzMiwgbXNjb3JsaWIsIFZlcnNpb249NC4wLjAuMCwgQ3VsdHVyZT1uZXV0cmFsLCBQdWJsaWNLZXlUb2tlbj1iNzdhNWM1NjE5MzRlMDg5XV0DAAAAB1ZlcnNpb24IQ29tcGFyZXIISGFzaFNpemUAAwAIkgFTeXN0ZW0uQ29sbGVjdGlvbnMuR2VuZXJpYy5HZW5lcmljRXF1YWxpdHlDb21wYXJlcmAxW1tTeXN0ZW0uU3RyaW5nLCBtc2NvcmxpYiwgVmVyc2lvbj00LjAuMC4wLCBDdWx0dXJlPW5ldXRyYWwsIFB1YmxpY0tleVRva2VuPWI3N2E1YzU2MTkzNGUwODldXQgAAAAACQIAAAAAAAAABAIAAACSAVN5c3RlbS5Db2xsZWN0aW9ucy5HZW5lcmljLkdlbmVyaWNFcXVhbGl0eUNvbXBhcmVyYDFbW1N5c3RlbS5TdHJpbmcsIG1zY29ybGliLCBWZXJzaW9uPTQuMC4wLjAsIEN1bHR1cmU9bmV1dHJhbCwgUHVibGljS2V5VG9rZW49Yjc3YTVjNTYxOTM0ZTA4OV1dAAAAAAseF0NhbWJpb0RpcmVjY2lvbkNvbnRhZG9yAgJkFgICAQ9kFgJmD2QWAgIBDzwrAAoBAA8WDB4LVmlzaWJsZURhdGUGAIAWo8J33QgeAlNEFgEGOCGWG0143YgeClRvZGF5c0RhdGUGAIAWo8J33QgeB1Rvb2xUaXBlHwxlHw0FLTxpbWcgc3JjPS9BcHBfdGhlbWVzL0FMSEFNQlJBL2ltZy9uZXh0LnBuZyAvPmRkAgcPDxYEHwkFIGZvcm0gYm9vdHN0cmFwLWlzby00IHRyYW5zcGFyZW50HwoCAmQWAgIBD2QWAmYPZBYGAgEPFgQeC18hSXRlbUNvdW50AgEfBmgWAmYPZBYEAgEPFgIeBVZhbHVlBQMxNDNkAgMPFgIfMAIHFg5mD2QWAgIBDxYCHx4FNnB4LTEgbWItMiBjb2wteGwtNCBjb2wtbGctNCBjb2wtbWQtNCBjb2wtc20tNCBjb2wteHMtNBZIZg8PFgIfBmdkFgJmDxYCHwEFOEVzIG5lY2VzYXJpbyBwcmVzZW50YXIgZG9jdW1lbnRvIG9yaWdpbmFsIGlkZW50aWZpY2F0aXZvZAIBDw8WAh8GZ2QWAgIBDw8WAh8EBSwvQXBwX1RoZW1lcy9BTEhBTUJSQS9pbWcvRW50cmFkYXMvQWR1bHRvLnN2Z2RkAgIPDxYCHwEFBkFkdWx0b2RkAgQPFgIfMQUDNDMyZAIFDxYCHzEFATBkAgYPFgIfMQUBMGQCBw8WAh8xZWQCCA8WAh8xBQQwLDYxZAIJDxYCHzEFATBkAgoPFgIfMQUCMjFkAgsPFgIfMQUCMTBkAgwPFgIfMQUCMTBkAg0PFgIfMQUFMTAsMDBkAg4PFgIfMQUFMTAsNjFkAg8PFgIfMQUXIzEwLzA0LzIwMjUtMzAvMDQvMjAyNiNkAhAPFgIfMQUBMWQCEQ8WAh8xBQI2MGQCEg8WAh8xZWQCEw8WAh8xZWQCFA8WAh8xBQEwZAIVDxYCHzFlZAIWDxYCHzFlZAIXDxYCHzFlZAIYDxYCHzFlZAIZDxYCHzFlZAIaDxYCHzFlZAIbDxYCHzFlZAIcDxYCHzFlZAIdDxYCHzFlZAIeDxYCHzFlZAIfDxYCHzEFATBkAiAPFgIfMWVkAiEPFgIfAQUJMTAsNjEg4oKsZAIiDxYEHwEFOEVzIG5lY2VzYXJpbyBwcmVzZW50YXIgZG9jdW1lbnRvIG9yaWdpbmFsIGlkZW50aWZpY2F0aXZvHwZoZAIjD2QWBgIBDxYCHwZoZAIDDw8WAh8GaGRkAgUPFgIfBmhkAiQPZBYGAgEPFgIfHgUhZGVjIGJ1dHRvbkRlc2FjdGl2byBpbml0aWFsIGNvbC00FgICAQ8PFgQfCQUoYnRuTWFzTWVub3NEZXNhY3Rpdm8gY29sb3JNZW5vc0Rlc2FjdGl2bx8KAgJkZAIDDw8WBB8vBQZBZHVsdG8fAQUBMGRkAgUPFgIfHgUWaW5jIGJ1dHRvbkFjdGl2byBjb2wtNBYCAgEPDxYEHwkFEWJ0bk1hc01lbm9zQWN0aXZvHwoCAmRkAgEPZBYCAgEPFgIfHgU2cHgtMSBtYi0yIGNvbC14bC00IGNvbC1sZy00IGNvbC1tZC00IGNvbC1zbS00IGNvbC14cy00FkhmDw8WAh8GZ2QWAmYPFgIfAQVeRXMgbmVjZXNhcmlvIHByZXNlbnRhciBlbCBkb2N1bWVudG8gb2ZpY2lhbCBhY3JlZGl0YXRpdm8geSBETkkuIE5vIHZhbGlkbyBjYXJuZXQgZGUgZXN0dWRpYW50ZWQCAQ8PFgIfBmdkFgICAQ8PFgIfBAU/L0FwcF9UaGVtZXMvQUxIQU1CUkEvaW1nL0VudHJhZGFzL0NpdWRhZGFub19VRV9DYXJuZXRfSm92ZW4uc3ZnZGQCAg8PFgIfAQUiVGl0dWxhcmVzIGRlbCBjYXJuw6kgam92ZW4gZXVyb3Blb2RkAgQPFgIfMQUDNDMzZAIFDxYCHzEFATBkAgYPFgIfMQUBMGQCBw8WAh8xZWQCCA8WAh8xBQQwLDQyZAIJDxYCHzEFATBkAgoPFgIfMQUCMjFkAgsPFgIfMQUBN2QCDA8WAh8xBQE3ZAINDxYCHzEFBDcsMDBkAg4PFgIfMQUENyw0MmQCDw8WAh8xBRcjMTAvMDQvMjAyNS0zMC8wNC8yMDI2I2QCEA8WAh8xBQExZAIRDxYCHzEFAjYwZAISDxYCHzFlZAITDxYCHzFlZAIUDxYCHzEFATBkAhUPFgIfMWVkAhYPFgIfMWVkAhcPFgIfMWVkAhgPFgIfMWVkAhkPFgIfMWVkAhoPFgIfMWVkAhsPFgIfMWVkAhwPFgIfMWVkAh0PFgIfMWVkAh4PFgIfMWVkAh8PFgIfMQUBMGQCIA8WAh8xZWQCIQ8WAh8BBQg3LDQyIOKCrGQCIg8WBB8BBV5FcyBuZWNlc2FyaW8gcHJlc2VudGFyIGVsIGRvY3VtZW50byBvZmljaWFsIGFjcmVkaXRhdGl2byB5IEROSS4gTm8gdmFsaWRvIGNhcm5ldCBkZSBlc3R1ZGlhbnRlHwZoZAIjD2QWBgIBDxYCHwZoZAIDDw8WAh8GaGRkAgUPFgIfBmhkAiQPZBYGAgEPFgIfHgUhZGVjIGJ1dHRvbkRlc2FjdGl2byBpbml0aWFsIGNvbC00FgICAQ8PFgQfCQUoYnRuTWFzTWVub3NEZXNhY3Rpdm8gY29sb3JNZW5vc0Rlc2FjdGl2bx8KAgJkZAIDDw8WBB8vBSJUaXR1bGFyZXMgZGVsIGNhcm7DqSBqb3ZlbiBldXJvcGVvHwEFATBkZAIFDxYCHx4FFmluYyBidXR0b25BY3Rpdm8gY29sLTQWAgIBDw8WBB8JBRFidG5NYXNNZW5vc0FjdGl2bx8KAgJkZAICD2QWAgIBDxYCHx4FNnB4LTEgbWItMiBjb2wteGwtNCBjb2wtbGctNCBjb2wtbWQtNCBjb2wtc20tNCBjb2wteHMtNBZIZg8PFgIfBmdkFgJmDxYCHwEFf1NpIGVsIG1lbm9yIG5vIHRpZW5lIEROSSBkZWJlcsOhIGluZGljYXJzZSBlbCBkZWwgdGl0dWxhciBkZSBsYSBjb21wcmEuIEVzIG5lY2VzYXJpbyBwcmVzZW50YXIgZG9jdW1lbnRvIG9maWNpYWwgYWNyZWRpdGF0aXZvDQpkAgEPDxYCHwZnZBYCAgEPDxYCHwQFKy9BcHBfVGhlbWVzL0FMSEFNQlJBL2ltZy9FbnRyYWRhcy9NZW5vci5zdmdkZAICDw8WAh8BBRhNZW5vcmVzIGRlIDEyIGEgMTUgYcOxb3NkZAIEDxYCHzEFAzQ4OGQCBQ8WAh8xBQEwZAIGDxYCHzEFATBkAgcPFgIfMWVkAggPFgIfMQUEMCw0MmQCCQ8WAh8xBQEwZAIKDxYCHzEFAjIxZAILDxYCHzEFATdkAgwPFgIfMQUBN2QCDQ8WAh8xBQQ3LDAwZAIODxYCHzEFBDcsNDJkAg8PFgIfMQUXIzEwLzA0LzIwMjUtMzAvMDQvMjAyNiNkAhAPFgIfMQUBMWQCEQ8WAh8xBQI2MGQCEg8WAh8xZWQCEw8WAh8xZWQCFA8WAh8xBQEwZAIVDxYCHzFlZAIWDxYCHzFlZAIXDxYCHzFlZAIYDxYCHzFlZAIZDxYCHzFlZAIaDxYCHzFlZAIbDxYCHzFlZAIcDxYCHzFlZAIdDxYCHzFlZAIeDxYCHzFlZAIfDxYCHzEFATBkAiAPFgIfMWVkAiEPFgIfAQUINyw0MiDigqxkAiIPFgQfAQV/U2kgZWwgbWVub3Igbm8gdGllbmUgRE5JIGRlYmVyw6EgaW5kaWNhcnNlIGVsIGRlbCB0aXR1bGFyIGRlIGxhIGNvbXByYS4gRXMgbmVjZXNhcmlvIHByZXNlbnRhciBkb2N1bWVudG8gb2ZpY2lhbCBhY3JlZGl0YXRpdm8NCh8GaGQCIw9kFgYCAQ8WAh8GaGQCAw8PFgIfBmhkZAIFDxYCHwZoZAIkD2QWBgIBDxYCHx4FIWRlYyBidXR0b25EZXNhY3Rpdm8gaW5pdGlhbCBjb2wtNBYCAgEPDxYEHwkFKGJ0bk1hc01lbm9zRGVzYWN0aXZvIGNvbG9yTWVub3NEZXNhY3Rpdm8fCgICZGQCAw8PFgQfLwUYTWVub3JlcyBkZSAxMiBhIDE1IGHDsW9zHwEFATBkZAIFDxYCHx4FFmluYyBidXR0b25BY3Rpdm8gY29sLTQWAgIBDw8WBB8JBRFidG5NYXNNZW5vc0FjdGl2bx8KAgJkZAIDD2QWAgIBDxYCHx4FNnB4LTEgbWItMiBjb2wteGwtNCBjb2wtbGctNCBjb2wtbWQtNCBjb2wtc20tNCBjb2wteHMtNBZIZg8PFgIfBmdkFgJmDxYCHwEFRlNpIGVsIG1lbm9yIG5vIHRpZW5lIEROSSwgZGViZXJhIGluZGljYXJzZSBlbCBkZWwgdGl0dWxhciBkZSBsYSBjb21wcmFkAgEPDxYCHwZnZBYCAgEPDxYCHwQFMy9BcHBfVGhlbWVzL0FMSEFNQlJBL2ltZy9FbnRyYWRhcy9NZW5vcl9QZXF1ZW5vLnN2Z2RkAgIPDxYCHwEFFE1lbm9yZXMgMyAtIDExIGHDsW9zZGQCBA8WAh8xBQM0MzRkAgUPFgIfMQUBMGQCBg8WAh8xBQEwZAIHDxYCHzFlZAIIDxYCHzEFATBkAgkPFgIfMQUBMGQCCg8WAh8xBQEwZAILDxYCHzEFATBkAgwPFgIfMQUBMGQCDQ8WAh8xBQQwLDAwZAIODxYCHzEFBDAsMDBkAg8PFgIfMQUXIzEwLzA0LzIwMjUtMzAvMDQvMjAyNiNkAhAPFgIfMQUBMGQCEQ8WAh8xBQEzZAISDxYCHzFlZAITDxYCHzFlZAIUDxYCHzEFATBkAhUPFgIfMWVkAhYPFgIfMWVkAhcPFgIfMWVkAhgPFgIfMWVkAhkPFgIfMWVkAhoPFgIfMWVkAhsPFgIfMWVkAhwPFgIfMWVkAh0PFgIfMWVkAh4PFgIfMWVkAh8PFgIfMQUBMGQCIA8WAh8xZWQCIQ8WAh8BBQgwLDAwIOKCrGQCIg8WBB8BBUZTaSBlbCBtZW5vciBubyB0aWVuZSBETkksIGRlYmVyYSBpbmRpY2Fyc2UgZWwgZGVsIHRpdHVsYXIgZGUgbGEgY29tcHJhHwZoZAIjD2QWBgIBDxYCHwZoZAIDDw8WAh8GaGRkAgUPFgIfBmhkAiQPZBYGAgEPFgIfHgUhZGVjIGJ1dHRvbkRlc2FjdGl2byBpbml0aWFsIGNvbC00FgICAQ8PFgQfCQUoYnRuTWFzTWVub3NEZXNhY3Rpdm8gY29sb3JNZW5vc0Rlc2FjdGl2bx8KAgJkZAIDDw8WBB8vBRRNZW5vcmVzIDMgLSAxMSBhw7Fvcx8BBQEwZGQCBQ8WAh8eBRZpbmMgYnV0dG9uQWN0aXZvIGNvbC00FgICAQ8PFgQfCQURYnRuTWFzTWVub3NBY3Rpdm8fCgICZGQCBA9kFgICAQ8WAh8eBTZweC0xIG1iLTIgY29sLXhsLTQgY29sLWxnLTQgY29sLW1kLTQgY29sLXNtLTQgY29sLXhzLTQWSGYPDxYCHwZnZBYCZg8WAh8BBTtFcyBuZWNlc2FyaW8gcHJlc2VudGFyIGRvY3VtZW50byBvZmljaWFsIGFjcmVkaXRhdGl2byB5IEROSWQCAQ8PFgIfBmdkFgICAQ8PFgIfBAU1L0FwcF9UaGVtZXMvQUxIQU1CUkEvaW1nL0VudHJhZGFzL0NpdWRhZGFub19VRV82NS5zdmdkZAICDw8WAh8BBSdDaXVkYWRhbm9zIGRlIGxhIFVFIG1heW9yZXMgZGUgNjUgYcOxb3NkZAIEDxYCHzEFAzQ4NmQCBQ8WAh8xBQEwZAIGDxYCHzEFATBkAgcPFgIfMWVkAggPFgIfMQUEMCw0MmQCCQ8WAh8xBQEwZAIKDxYCHzEFAjIxZAILDxYCHzEFATdkAgwPFgIfMQUBN2QCDQ8WAh8xBQQ3LDAwZAIODxYCHzEFBDcsNDJkAg8PFgIfMQUXIzEwLzA0LzIwMjUtMzAvMDQvMjAyNiNkAhAPFgIfMQUBMWQCEQ8WAh8xBQI2MGQCEg8WAh8xZWQCEw8WAh8xZWQCFA8WAh8xBQEwZAIVDxYCHzFlZAIWDxYCHzFlZAIXDxYCHzFlZAIYDxYCHzFlZAIZDxYCHzFlZAIaDxYCHzFlZAIbDxYCHzFlZAIcDxYCHzFlZAIdDxYCHzFlZAIeDxYCHzFlZAIfDxYCHzEFATBkAiAPFgIfMWVkAiEPFgIfAQUINyw0MiDigqxkAiIPFgQfAQU7RXMgbmVjZXNhcmlvIHByZXNlbnRhciBkb2N1bWVudG8gb2ZpY2lhbCBhY3JlZGl0YXRpdm8geSBETkkfBmhkAiMPZBYGAgEPFgIfBmhkAgMPDxYCHwZoZGQCBQ8WAh8GaGQCJA9kFgYCAQ8WAh8eBSFkZWMgYnV0dG9uRGVzYWN0aXZvIGluaXRpYWwgY29sLTQWAgIBDw8WBB8JBShidG5NYXNNZW5vc0Rlc2FjdGl2byBjb2xvck1lbm9zRGVzYWN0aXZvHwoCAmRkAgMPDxYEHy8FJ0NpdWRhZGFub3MgZGUgbGEgVUUgbWF5b3JlcyBkZSA2NSBhw7Fvcx8BBQEwZGQCBQ8WAh8eBRZpbmMgYnV0dG9uQWN0aXZvIGNvbC00FgICAQ8PFgQfCQURYnRuTWFzTWVub3NBY3Rpdm8fCgICZGQCBQ9kFgICAQ8WAh8eBTZweC0xIG1iLTIgY29sLXhsLTQgY29sLWxnLTQgY29sLW1kLTQgY29sLXNtLTQgY29sLXhzLTQWSGYPDxYCHwZnZBYCZg8WAh8BBR9EZWJlIGFjcmVkaXRhciBsYSBtaW51c3ZhbMOtYQ0KZAIBDw8WAh8GZ2QWAgIBDw8WAh8EBTMvQXBwX1RoZW1lcy9BTEhBTUJSQS9pbWcvRW50cmFkYXMvRGlzY2FwYWNpdGFkby5zdmdkZAICDw8WAh8BBS5QZXJzb25hcyBjb24gZGlzY2FwYWNpZGFkIGlndWFsIG8gbWF5b3IgYWwgMzMlZGQCBA8WAh8xBQM0ODdkAgUPFgIfMQUBMGQCBg8WAh8xBQEwZAIHDxYCHzFlZAIIDxYCHzEFBDAsNDJkAgkPFgIfMQUBMGQCCg8WAh8xBQIyMWQCCw8WAh8xBQE3ZAIMDxYCHzEFATdkAg0PFgIfMQUENywwMGQCDg8WAh8xBQQ3LDQyZAIPDxYCHzEFFyMxMC8wNC8yMDI1LTMwLzA0LzIwMjYjZAIQDxYCHzEFATFkAhEPFgIfMQUCNjBkAhIPFgIfMWVkAhMPFgIfMWVkAhQPFgIfMQUBMGQCFQ8WAh8xZWQCFg8WAh8xZWQCFw8WAh8xZWQCGA8WAh8xZWQCGQ8WAh8xZWQCGg8WAh8xZWQCGw8WAh8xZWQCHA8WAh8xZWQCHQ8WAh8xZWQCHg8WAh8xZWQCHw8WAh8xBQEwZAIgDxYCHzFlZAIhDxYCHwEFCDcsNDIg4oKsZAIiDxYEHwEFH0RlYmUgYWNyZWRpdGFyIGxhIG1pbnVzdmFsw61hDQofBmhkAiMPZBYGAgEPFgIfBmhkAgMPDxYCHwZoZGQCBQ8WAh8GaGQCJA9kFgYCAQ8WAh8eBSFkZWMgYnV0dG9uRGVzYWN0aXZvIGluaXRpYWwgY29sLTQWAgIBDw8WBB8JBShidG5NYXNNZW5vc0Rlc2FjdGl2byBjb2xvck1lbm9zRGVzYWN0aXZvHwoCAmRkAgMPDxYEHy8FLlBlcnNvbmFzIGNvbiBkaXNjYXBhY2lkYWQgaWd1YWwgbyBtYXlvciBhbCAzMyUfAQUBMGRkAgUPFgIfHgUWaW5jIGJ1dHRvbkFjdGl2byBjb2wtNBYCAgEPDxYEHwkFEWJ0bk1hc01lbm9zQWN0aXZvHwoCAmRkAgYPZBYCAgEPFgIfHgU2cHgtMSBtYi0yIGNvbC14bC00IGNvbC1sZy00IGNvbC1tZC00IGNvbC1zbS00IGNvbC14cy00FkhmDw8WAh8GZ2QWAmYPFgIfAQVtRXMgbmVjZXNhcmlvIHByZXNlbnRhciBkb2N1bWVudG8gYWNyZWRpdGF0aXZvIGVuIHZpZ29yIHkgZXhwZWRpZG8gZW4gRXNwYcOxYSwgeSBETkkgY29uZm9ybWUgb3JkZW4gZGUgcHJlY2lvc2QCAQ8PFgIfBmdkFgICAQ8PFgIfBAUtL0FwcF9UaGVtZXMvQUxIQU1CUkEvaW1nL0VudHJhZGFzL0ZhbV9OdW0uc3ZnZGQCAg8PFgIfAQU8TWllbWJyb3MgZGUgZmFtaWxpYXMgbnVtZXJvc2FzICh0w610dWxvIGV4cGVkaWRvIGVuIEVzcGHDsWEpZGQCBA8WAh8xBQM0ODlkAgUPFgIfMQUBMGQCBg8WAh8xBQEwZAIHDxYCHzFlZAIIDxYCHzEFBDAsNDJkAgkPFgIfMQUBMGQCCg8WAh8xBQIyMWQCCw8WAh8xBQE3ZAIMDxYCHzEFATdkAg0PFgIfMQUENywwMGQCDg8WAh8xBQQ3LDQyZAIPDxYCHzEFFyMxMC8wNC8yMDI1LTMwLzA0LzIwMjYjZAIQDxYCHzEFATFkAhEPFgIfMQUCNjBkAhIPFgIfMWVkAhMPFgIfMWVkAhQPFgIfMQUBMGQCFQ8WAh8xZWQCFg8WAh8xZWQCFw8WAh8xZWQCGA8WAh8xZWQCGQ8WAh8xZWQCGg8WAh8xZWQCGw8WAh8xZWQCHA8WAh8xZWQCHQ8WAh8xZWQCHg8WAh8xZWQCHw8WAh8xBQEwZAIgDxYCHzFlZAIhDxYCHwEFCDcsNDIg4oKsZAIiDxYEHwEFbUVzIG5lY2VzYXJpbyBwcmVzZW50YXIgZG9jdW1lbnRvIGFjcmVkaXRhdGl2byBlbiB2aWdvciB5IGV4cGVkaWRvIGVuIEVzcGHDsWEsIHkgRE5JIGNvbmZvcm1lIG9yZGVuIGRlIHByZWNpb3MfBmhkAiMPZBYGAgEPFgIfBmhkAgMPDxYCHwZoZGQCBQ8WAh8GaGQCJA9kFgYCAQ8WAh8eBSFkZWMgYnV0dG9uRGVzYWN0aXZvIGluaXRpYWwgY29sLTQWAgIBDw8WBB8JBShidG5NYXNNZW5vc0Rlc2FjdGl2byBjb2xvck1lbm9zRGVzYWN0aXZvHwoCAmRkAgMPDxYEHy8FPE1pZW1icm9zIGRlIGZhbWlsaWFzIG51bWVyb3NhcyAodMOtdHVsbyBleHBlZGlkbyBlbiBFc3Bhw7FhKR8BBQEwZGQCBQ8WAh8eBRZpbmMgYnV0dG9uQWN0aXZvIGNvbC00FgICAQ8PFgQfCQURYnRuTWFzTWVub3NBY3Rpdm8fCgICZGQCAw8WAh8GaGQCBQ8PFgQfAQUJQ29udGludWFyHwZoZGQCCw8WAh8eBQpzdGVwLXRpdGxlFgICAQ8WAh8BZGQCDA8PFgIfBmhkFgwCAQ8WAh8BZWQCBQ8WAh8GaGQCBw9kFggCAQ8PFgIfBmhkFgICAQ9kFgJmD2QWAgIBDzwrAAoBAA8WBB8MZR8NBS08aW1nIHNyYz0vQXBwX3RoZW1lcy9BTEhBTUJSQS9pbWcvbmV4dC5wbmcgLz5kZAIDDxYCHwZoFgICAQ8QZGQWAGQCBQ8WAh8GaBYCAgEPEGRkFgBkAgkPDxYCHwZoZBYEZg8QZBAVCBhTZWxlY2Npb25lIHVuIGl0aW5lcmFyaW8gVmlzaXRhcyBHdWlhZGFzIHBvciBlbCBNb251bWVudG8sVmlzaXRhcyBBdXRvZ3VpYWRhcyBwb3IgZWwgTW9udW1lbnRvIEdlbmVyYWwkVmlzaXRhcyBDb21iaW5hZGFzIEFsaGFtYnJhICsgQ2l1ZGFkLFZpc2l0YXMgR3VpYWRhcyBwb3IgbGEgRGVoZXNhIGRlbCBHZW5lcmFsaWZlKVZpc2l0YXMgR3VpYWRhcyBwb3IgZWwgTW9udW1lbnRvIEphcmRpbmVzLVZpc2l0YXMgQXV0b2d1aWFkYXMgcG9yIGVsIE1vbnVtZW50byBKYXJkaW5lcx5WaXNpdGFzIEd1aWFkYXMgTXVzZW8gKyBDaXVkYWQVCAAgVmlzaXRhcyBHdWlhZGFzIHBvciBlbCBNb251bWVudG8sVmlzaXRhcyBBdXRvZ3VpYWRhcyBwb3IgZWwgTW9udW1lbnRvIEdlbmVyYWwkVmlzaXRhcyBDb21iaW5hZGFzIEFsaGFtYnJhICsgQ2l1ZGFkLFZpc2l0YXMgR3VpYWRhcyBwb3IgbGEgRGVoZXNhIGRlbCBHZW5lcmFsaWZlKVZpc2l0YXMgR3VpYWRhcyBwb3IgZWwgTW9udW1lbnRvIEphcmRpbmVzLVZpc2l0YXMgQXV0b2d1aWFkYXMgcG9yIGVsIE1vbnVtZW50byBKYXJkaW5lcx5WaXNpdGFzIEd1aWFkYXMgTXVzZW8gKyBDaXVkYWQUKwMIZ2dnZ2dnZ2cWAWZkAgEPEA8WAh8GaGQQFQEYU2VsZWNjaW9uZSB1biBpdGluZXJhcmlvFQEAFCsDAWcWAWZkAgsPFgIfBmhkAg0PDxYCHwEFF3ZvbHZlciBhbCBwYXNvIGFudGVyaW9yZGQCDw9kFgJmD2QWAgIBDw8WBB8BBQtJciBhIHBhc28gMx8GaGRkAg0PFgQfHgUKc3RlcC10aXRsZR8GZ2QCDg8PFgIfBmhkFhpmDxYCHwFlZAIBDxYCHwEFAS5kAgIPZBYCZg9kFgoCAQ8PFgIeCkhlYWRlclRleHQFJURlYmUgaW50cm9kdWNpciBsb3MgdmFsb3JlcyBjb3JyZWN0b3NkZAIDD2QWBGYPZBYCZg8PFgIfAQUXTm9tYnJlIGRlbCBjb21wcmFkb3IgKiBkZAIBD2QWAmYPDxYCHwEFDEFwZWxsaWRvcyAqIGRkAgQPZBYEZg9kFgRmDw8WAh8BBRlEb2N1bWVudG8gZGUgaWRlbnRpZGFkICogZGQCAg8QZBAVAwxETkkgRXNwYcOxb2wMTklFIEVzcGHDsW9sF090cm8gTnJvLiBpZGVudGlmaWNhZG9yFQMDZG5pA25pZQdvdHJvX2lkFCsDA2dnZxYBZmQCAQ9kFgJmDw8WAh8BBRdOw7ptZXJvIGRlIGRvY3VtZW50byAqIGRkAgUPZBYEZg9kFgJmDw8WAh8BBQhFbWFpbCAqIGRkAgEPZBYCZg8PFgIfAQURQ29uZmlybWEgRW1haWwgKiBkZAIGD2QWAmYPZBYCZg8PFgIfAQUMVGVsw6lmb25vICogZGQCBA8WAh8GZxYCAgEPEA8WAh4HQ2hlY2tlZGhkZGRkAgYPZBYEAgEPZBYCAgMPEGQQFQQMRE5JIEVzcGHDsW9sDENJRiBFc3Bhw7FvbAxOSUUgRXNwYcOxb2wXT3RybyBOcm8uIGlkZW50aWZpY2Fkb3IVBANkbmkDY2lmA25pZQdvdHJvX2lkFCsDBGdnZ2cWAWZkAgYPZBYEAgUPDxYCHwZoZGQCBw8QZBAV7wETU2VsZWNjaW9uZSB1biBwYcOtcwlBcmdlbnRpbmEJQXVzdHJhbGlhBUNoaW5hBUl0YWx5BUphcGFuBk1leGljbwtOZXcgWmVhbGFuZAhQb3J0dWdhbAdFc3Bhw7FhB0dlcm1hbnkGRnJhbmNlElJ1c3NpYW4gRmVkZXJhdGlvbg5Vbml0ZWQgS2luZ2RvbRRVbml0ZWQgU3RhdGVzIG9mIEFtZQtBZmdoYW5pc3RhbgdBbGJhbmlhB0FsZ2VyaWEOQW1lcmljYW4gU2Ftb2EHQW5kb3JyYQZBbmdvbGEIQW5ndWlsbGEKQW50YXJjdGljYQdBbnRpZ3VhB0FybWVuaWEFQXJ1YmEHQXVzdHJpYQpBemVyYmFpamFuB0JhaGFtYXMHQmFocmFpbgpCYW5nbGFkZXNoCEJhcmJhZG9zB0JlbGFydXMHQmVsZ2l1bQZCZWxpemUFQmVuaW4HQmVybXVkYQZCaHV0YW4HQm9saXZpYQZCb3NuaWEIQm90c3dhbmENQm91dmV0IElzbGFuZAZCcmF6aWwOQnJpdGlzaCBJbmRpYW4RQnJ1bmVpIERhcnVzc2FsYW0IQnVsZ2FyaWEMQnVya2luYSBGYXNvB0J1cnVuZGkIQ2FtYm9kaWEIQ2FtZXJvb24GQ2FuYWRhCkNhcGUgVmVyZGUOQ2F5bWFuIElzbGFuZHMTQ2VudHJhbCBBZnJpY2FuIFJlcARDaGFkBUNoaWxlEENocmlzdG1hcyBJc2xhbmQNQ29jb3MgSXNsYW5kcwhDb2xvbWJpYQdDb21vcm9zBUNvbmdvDENvb2sgSXNsYW5kcwpDb3N0YSBSaWNhB0Nyb2F0aWEEQ3ViYQZDeXBydXMOQ3plY2ggUmVwdWJsaWMHRGVubWFyawhEamlib3V0aQhEb21pbmljYRJEb21pbmljYW4gUmVwdWJsaWMKRWFzdCBUaW1vcgdFY3VhZG9yBUVneXB0C0VsIFNhbHZhZG9yEUVxdWF0b3JpYWwgR3VpbmVhB0VyaXRyZWEHRXN0b25pYQhFdGhpb3BpYQ1GYXJvZSBJc2xhbmRzBEZpamkHRmlubGFuZA1GcmVuY2ggR3VpYW5hEEZyZW5jaCBQb2x5bmVzaWEFR2Fib24GR2FtYmlhB0dlb3JnaWEFR2hhbmEGR3JlZWNlCUdyZWVubGFuZAdHcmVuYWRhCkd1YWRlbG91cGUER3VhbQlHdWF0ZW1hbGEGR3VpbmVhDUd1aW5lYSBCaXNzYXUGR3V5YW5hBUhhaXRpCEhvbmR1cmFzCUhvbmcgS29uZwdIdW5nYXJ5B0ljZWxhbmQFSW5kaWEJSW5kb25lc2lhBElyYW4ESXJhcQdJcmVsYW5kBklzcmFlbAtJdm9yeSBDb2FzdAdKYW1haWNhBkpvcmRhbgpLYXpha2hzdGFuBUtlbnlhCEtpcmliYXRpBkt1d2FpdApLeXJneXpzdGFuA0xhbwZMYXR2aWEHTGViYW5vbgdMZXNvdGhvB0xpYmVyaWEFTGlieWENTGllY2h0ZW5zdGVpbglMaXRodWFuaWEKTHV4ZW1ib3VyZwVNYWNhdQlNYWNlZG9uaWEKTWFkYWdhc2NhcgZNYWxhd2kITWFsYXlzaWEITWFsZGl2ZXMETWFsaQVNYWx0YQhNYWx2aW5hcxBNYXJzaGFsbCBJc2xhbmRzCk1hcnRpbmlxdWUKTWF1cml0YW5pYQlNYXVyaXRpdXMHTWF5b3R0ZQpNaWNyb25lc2lhB01vbGRvdmEGTW9uYWNvCE1vbmdvbGlhCk1vbnRlbmVncm8KTW9udHNlcnJhdAdNb3JvY2NvCk1vemFtYmlxdWUHTXlhbm1hcgdOYW1pYmlhBU5hdXJ1BU5lcGFsC05ldGhlcmxhbmRzFE5ldGhlcmxhbmRzIEFudGlsbGVzDU5ldyBDYWxlZG9uaWEJTmljYXJhZ3VhBU5pZ2VyB05pZ2VyaWEETml1ZQ5Ob3Jmb2xrIElzbGFuZAtOb3J0aCBLb3JlYRNOb3J0aGVybiBNYXJpYW5hIElzBk5vcndheQRPbWFuGU90cm9zIGRlIHBhaXNlcyBkZWwgbXVuZG8IUGFraXN0YW4FUGFsYXUGUGFuYW1hEFBhcHVhIE5ldyBHdWluZWEIUGFyYWd1YXkEUGVydQtQaGlsaXBwaW5lcwhQaXRjYWlybgZQb2xhbmQLUHVlcnRvIFJpY28FUWF0YXIHUmV1bmlvbgdSb21hbmlhBlJ3YW5kYQ9TIEdlb3JnaWEgU291dGgLU2FpbnQgTHVjaWEFU2Ftb2EKU2FuIE1hcmlubxNTYW8gVG9tZSAtIFByaW5jaXBlDFNhdWRpIEFyYWJpYQdTZW5lZ2FsBlNlcmJpYQpTZXljaGVsbGVzDFNpZXJyYSBMZW9uZQlTaW5nYXBvcmUIU2xvdmFraWEIU2xvdmVuaWEPU29sb21vbiBJc2xhbmRzB1NvbWFsaWEMU291dGggQWZyaWNhC1NvdXRoIEtvcmVhCVNyaSBMYW5rYQlTdCBIZWxlbmESU3QgS2l0dHMgYW5kIE5ldmlzE1N0IFBpZXJyZSAgTWlxdWVsb24RU3QgVmluY2VudC1HcmVuYWQFU3VkYW4IU3VyaW5hbWURU3ZhbGJhcmQgSmFuIE0gSXMJU3dhemlsYW5kBlN3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c3NpYW4gRmVkZXJhdGlvbg5Vbml0ZWQgS2luZ2RvbRRVbml0ZWQgU3RhdGVzIG9mIEFtZQtBZmdoYW5pc3RhbgdBbGJhbmlhB0FsZ2VyaWEOQW1lcmljYW4gU2Ftb2EHQW5kb3JyYQZBbmdvbGEIQW5ndWlsbGEKQW50YXJjdGljYQdBbnRpZ3VhB0FybWVuaWEFQXJ1YmEHQXVzdHJpYQpBemVyYmFpamFuB0JhaGFtYXMHQmFocmFpbgpCYW5nbGFkZXNoCEJhcmJhZG9zB0JlbGFydXMHQmVsZ2l1bQZCZWxpemUFQmVuaW4HQmVybXVkYQZCaHV0YW4HQm9saXZpYQZCb3NuaWEIQm90c3dhbmENQm91dmV0IElzbGFuZAZCcmF6aWwOQnJpdGlzaCBJbmRpYW4RQnJ1bmVpIERhcnVzc2FsYW0IQnVsZ2FyaWEMQnVya2luYSBGYXNvB0J1cnVuZGkIQ2FtYm9kaWEIQ2FtZXJvb24GQ2FuYWRhCkNhcGUgVmVyZGUOQ2F5bWFuIElzbGFuZHMTQ2VudHJhbCBBZnJpY2FuIFJlcARDaGFkBUNoaWxlEENocmlzdG1hcyBJc2xhbmQNQ29jb3MgSXNsYW5kcwhDb2xvbWJpYQdDb21vcm9zBUNvbmdvDENvb2sgSXNsYW5kcwpDb3N0YSBSaWNhB0Nyb2F0aWEEQ3ViYQZDeXBydXMOQ3plY2ggUmVwdWJsaWMHRGVubWFyawhEamlib3V0aQhEb21pbmljYRJEb21pbmljYW4gUmVwdWJsaWMKRWFzdCBUaW1vcgdFY3VhZG9yBUVneXB0C0VsIFNhbHZhZG9yEUVxdWF0b3JpYWwgR3VpbmVhB0VyaXRyZWEHRXN0b25pYQhFdGhpb3BpYQ1GYXJvZSBJc2xhbmRzBEZpamkHRmlubGFuZA1GcmVuY2ggR3VpYW5hEEZyZW5jaCBQb2x5bmVzaWEFR2Fib24GR2FtYmlhB0dlb3JnaWEFR2hhbmEGR3JlZWNlCUdyZWVubGFuZAdHcmVuYWRhCkd1YWRlbG91cGUER3VhbQlHdWF0ZW1hbGEGR3VpbmVhDUd1aW5lYSBCaXNzYXUGR3V5YW5hBUhhaXRpCEhvbmR1cmFzCUhvbmcgS29uZwdIdW5nYXJ5B0ljZWxhbmQFSW5kaWEJSW5kb25lc2lhBElyYW4ESXJhcQdJcmVsYW5kBklzcmFlbAtJdm9yeSBDb2FzdAdKYW1haWNhBkpvcmRhbgpLYXpha2hzdGFuBUtlbnlhCEtpcmliYXRpBkt1d2FpdApLeXJneXpzdGFuA0xhbwZMYXR2aWEHTGViYW5vbgdMZXNvdGhvB0xpYmVyaWEFTGlieWENTGllY2h0ZW5zdGVpbglMaXRodWFuaWEKTHV4ZW1ib3VyZwVNYWNhdQlNYWNlZG9uaWEKTWFkYWdhc2NhcgZNYWxhd2kITWFsYXlzaWEITWFsZGl2ZXMETWFsaQVNYWx0YQhNYWx2aW5hcxBNYXJzaGFsbCBJc2xhbmRzCk1hcnRpbmlxdWUKTWF1cml0YW5pYQlNYXVyaXRpdXMHTWF5b3R0ZQpNaWNyb25lc2lhB01vbGRvdmEGTW9uYWNvCE1vbmdvbGlhCk1vbnRlbmVncm8KTW9udHNlcnJhdAdNb3JvY2NvCk1vemFtYmlxdWUHTXlhbm1hcgdOYW1pYmlhBU5hdXJ1BU5lcGFsC05ldGhlcmxhbmRzFE5ldGhlcmxhbmRzIEFudGlsbGVzDU5ldyBDYWxlZG9uaWEJTmljYXJhZ3VhBU5pZ2VyB05pZ2VyaWEETml1ZQ5Ob3Jmb2xrIElzbGFuZAtOb3J0aCBLb3JlYRNOb3J0aGVybiBNYXJpYW5hIElzBk5vcndheQRPbWFuGU90cm9zIGRlIHBhaXNlcyBkZWwgbXVuZG8IUGFraXN0YW4FUGFsYXUGUGFuYW1hEFBhcHVhIE5ldyBHdWluZWEIUGFyYWd1YXkEUGVydQtQaGlsaXBwaW5lcwhQaXRjYWlybgZQb2xhbmQLUHVlcnRvIFJpY28FUWF0YXIHUmV1bmlvbgdSb21hbmlhBlJ3YW5kYQ9TIEdlb3JnaWEgU291dGgLU2FpbnQgTHVjaWEFU2Ftb2EKU2FuIE1hcmlubxNTYW8gVG9tZSAtIFByaW5jaXBlDFNhdWRpIEFyYWJpYQdTZW5lZ2FsBlNlcmJpYQpTZXljaGVsbGVzDFNpZXJyYSBMZW9uZQlTaW5nYXBvcmUIU2xvdmFraWEIU2xvdmVuaWEPU29sb21vbiBJc2xhbmRzB1NvbWFsaWEMU291dGggQWZyaWNhC1NvdXRoIEtvcmVhCVNyaSBMYW5rYQlTdCBIZWxl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b2xkZGQCEA9kFgJmD2QWCGYPFgIfAQUrPHN0cm9uZz5TdSBjb21wcmEgZGUgZW50cmFkYXM8L3N0cm9uZz4gcGFyYWQCAQ8WAh8BBSZWaXNpdGEgSmFyZGluZXMsIEdlbmVyYWxpZmUgeSBBbGNhemFiYWQCAg8WAh8BBdgDPGRpdiBjbGFzcz0ncmVzdWx0Jz4gICA8ZGl2IGNsYXNzPSdtLWItMTInPiAgICAgIDxpIGNsYXNzPSdpY29uIGljb24tcGVvcGxlJz48L2k+ICAgPC9kaXY+ICAgPGRpdiBjbGFzcz0nbS1iLTEyJz4gICAgICA8aSBjbGFzcz0naWNvbiBpY29uLWRhdGUnPjwvaT4gICAgICA8cD5GZWNoYTogPGJyIC8+ICAgICAgPC9wPiAgIDwvZGl2PjwvZGl2PjxkaXYgY2xhc3M9J3ByaXgtdG90YWwgYnJkLXN1cC0yMCc+ICAgPHNwYW4gY2xhc3M9J3RpdHVsb1ByZWNpb0ZpbmFsJz5Ub3RhbCBlbnRyYWRhczwvc3Bhbj48c3Ryb25nIGNsYXNzPSdjb250ZW5pZG9QcmVjaW9GaW5hbCc+MDwvc3Ryb25nPiAgIDxzcGFuIGNsYXNzPSd0aXR1bG9QcmVjaW9GaW5hbCBwcmVjaW9GaW5hbCc+UHJlY2lvIGZpbmFsPC9zcGFuPjxzdHJvbmcgY2xhc3M9J2NvbnRlbmlkb1ByZWNpb0ZpbmFsIHByZWNpb0ZpbmFsJz4wLDAwIOKCrDwvc3Ryb25nPjwvZGl2PmQCAw8WAh8BZGQCEg9kFgQCAQ8PFgIfAQUOQXZpc28gaG9yYXJpb3NkZAIDDw8WAh8BBaIBUmVjdWVyZGUgc2VyIDxiPnB1bnR1YWw8L2I+IGVuIGxhIGhvcmEgc2VsZWNjaW9uYWRhIGEgbG9zIDxiPlBhbGFjaW9zIE5hemFyw61lczwvYj4uIFJlc3RvIGRlbCBtb251bWVudG8gZGUgODozMCBhIDE4OjAwIGhvcmFzIGludmllcm5vOyA4OjMwIGEgMjA6MDAgaG9yYXMgdmVyYW5vZGQCEw9kFggCAQ8PFgIfAQUfQXZpc28gc29icmUgdmlzaXRhcyBjb24gbWVub3Jlc2RkAgMPDxYCHwEF9gFTaSB2YSBhIHJlYWxpemFyIGxhIHZpc2l0YSBjb24gbWVub3JlcyBkZSAzIGEgMTEgYcOxb3MsIMOpc3RvcyBwcmVjaXNhbiBkZSBzdSBlbnRyYWRhIGNvcnJlc3BvbmRpZW50ZS4NClBvciBmYXZvciBzZWxlY2Npw7NuZWxhIGVuIHN1IGNvbXByYTogTGFzIGVudHJhZGFzIGRlIG1lbm9yZXMgZGUgMyBhw7FvcyBzZXLDoW4gZmFjaWxpdGFkYXMgZW4gbGFzIHRhcXVpbGxhcyBkZWwgbW9udW1lbnRvLiDCv0Rlc2VhIGNvbnRpbnVhcj9kZAIFDw8WAh8BBQJTaWRkAgcPDxYCHwEFAk5vZGQCFA9kFgQCAQ8PFgIfAQUWQVZJU08gREFUT1MgVklTSVRBTlRFU2RkAgMPDxYCHwEFXENvbXBydWViZSBxdWUgbG9zIGRhdG9zIGRlIHZpc2l0YW50ZXMgc29uIGNvcnJlY3RvcywgYXPDrSBjb21vIGxhIGZlY2hhIHkgaG9yYSBzZWxlY2Npb25hZGEuZGQCAg8PFgIfBmhkZAIODxYEHwEFvx08Zm9vdGVyIGNsYXNzPSJmb290ZXIiPg0KICA8ZGl2IGlkPSJkaXZGb290ZXIyIiBjbGFzcz0iZm9vdGVyMiI+DQogICAgPGRpdiBjbGFzcz0iY29udGFpbmVyIj4NCiAgICAgIDxkaXYgY2xhc3M9ImxvZ28gIj4NCiAgICAgICAgICA8YSBocmVmPSJodHRwOi8vd3d3LmFsaGFtYnJhLXBhdHJvbmF0by5lcy8iIHRhcmdldD0iX2JsYW5rIj48aW1nIGlkPSJpbWdGb290ZXIiIHNyYz0iL0FwcF9UaGVtZXMvQUxIQU1CUkEvaW1nL2xvZ28tZm9vdGVyLnBuZyIgYWx0PSJBbGhhbWJyYSB5IEdlbmVyYWxpZmUiPjwvYT4NCiAgICAgICAgPC9kaXY+DQogICAgICA8ZGl2IGNsYXNzPSJyb3ciPg0KICAgICAgICAgPGRpdiBjbGFzcz0iZm9vdGVyLWl0ZW0gY29sdW1uLTEiPg0KICAgICAgICAgIDx1bD4NCiAgICAgICAgICAgIDxsaT48YSBjbGFzcz0ibGlua3MtaXRlbSIgaHJlZj0iaHR0cHM6Ly90aWNrZXRzLmFsaGFtYnJhLXBhdHJvbmF0by5lcy90ZS1wdWVkZS1heXVkYXIvIiB0YXJnZXQ9Il9ibGFuayI+TEUgUFVFRE8gQVlVREFSPC9hPjwvbGk+DQogICAgICAgICAgICA8bGk+PGEgY2xhc3M9ImxpbmtzLWl0ZW0iIGhyZWY9Imh0dHBzOi8vdGlja2V0cy5hbGhhbWJyYS1wYXRyb25hdG8uZXMvcG9saXRpY2EtZGUtY29tcHJhLyIgdGFyZ2V0PSJfYmxhbmsiPlBPTMONVElDQSBERSBDT01QUkFTPC9hPjwvbGk+DQogICAgICAgICAgICA8bGk+PGEgY2xhc3M9ImxpbmtzLWl0ZW0iIGhyZWY9Ii9wb2xpdGljYS1jb29raWVzLmFzcHgiIHRhcmdldD0iX2JsYW5rIj5QT0zDjVRJQ0EgREUgQ09PS0lFUzwvYT48L2xpPg0KICAgICAgICAgICAgPGxpPjxhIGNsYXNzPSJsaW5rcy1pdGVtIiBocmVmPSJqYXZhc2NyaXB0OnZvaWQoMCkiICBvbkNsaWNrPSJSZWNvbmZpZ3VyYXJDb29raWVzKCkiPkNhbmNlbGFyIC8gY29uZmlndXJhciBwb2xpdGljYSBkZSBjb29raWVzPC9hPjwvbGk+DQogICAgICAgICAgICA8bGk+PGEgY2xhc3M9ImxpbmtzLWl0ZW0iIGhyZWY9Imh0dHBzOi8vdGlja2V0cy5hbGhhbWJyYS1wYXRyb25hdG8uZXMvcG9saXRpY2EtZGUtcHJpdmFjaWRhZCIgdGFyZ2V0PSJfYmxhbmsiPlBPTMONVElDQSBERSBQUklWQUNJREFEPC9hPjwvbGk+DQogICAgICAgICAgICA8bGk+PGEgY2xhc3M9ImxpbmtzLWl0ZW0iIGhyZWY9Imh0dHBzOi8vdGlja2V0cy5hbGhhbWJyYS1wYXRyb25hdG8uZXMvYXZpc28tbGVnYWwvIiB0YXJnZXQ9Il9ibGFuayI+QVZJU08gTEVHQUw8L2E+PC9saT4NCiAgICAgICAgICAgIDxsaT48cCBjbGFzcz0ibGlua3MtaXRlbSI+VEVMw4lGT05PIERFTCBWSVNJVEFOVEUgPGEgaHJlZj0idGVsOiszNDg1ODg4OTAwMiIgY2xhc3M9InRlbCI+KzM0IDk1OCAwMjcgOTcxPC9hPjwvcD48L2xpPg0KICAgICAgICAgICAgPGxpPjxwIGNsYXNzPSJsaW5rcy1pdGVtIj5URUzDiUZPTk8gREUgU09QT1JURSBBIExBIFZFTlRBIERFIEVOVFJBREFTIDxhIGhyZWY9InRlbDorMzQ4NTg4ODkwMDIiIGNsYXNzPSJ0ZWwiPiszNDg1ODg4OTAwMjwvYT48L3A+PC9saT4NCjxsaT48cCBjbGFzcz0ibGlua3MtaXRlbSI+Q09SUkVPIEVMRUNUUsOTTklDTyBERSBTT1BPUlRFIEEgTEEgVkVOVEEgREUgRU5UUkFEQVMgPGEgaHJlZj0ibWFpbHRvOnRpY2tldHMuYWxoYW1icmFAaWFjcG9zLmNvbSIgY2xhc3M9InRlbCI+dGlja2V0cy5hbGhhbWJyYUBpYWNwb3MuY29tPC9hPjwvcD48L2xpPg0KICAgICAgICAgIDwvdWw+DQogICAgICAgICA8L2Rpdj4NCiAgICAgIDwvZGl2Pg0KICAgICAgPCEtLSBDb250YWN0byB5IFJSU1MgLS0+DQogICAgICA8ZGl2IGNsYXNzPSJmb290ZXI0Ij4NCiAgICAgICAgPGRpdiBjbGFzcz0iZm9sbG93Ij4NCiAgICAgICAgICA8cD5Tw61ndWVub3MgZW46PC9wPg0KICAgICAgICAgIDx1bCBjbGFzcz0ic29jaWFsIj4NCiAgICAgICAgICAgIDxsaSBpZD0ibGlGYWNlYm9vayI+DQogICAgICAgICAgICAgIDxhIGlkPSJsaW5rRmFjZWJvb2siIGNsYXNzPSJpY29uIGljb24tZmFjZWJvb2siIHRpdGxlPSJGYWNlYm9vayIgaHJlZj0iaHR0cHM6Ly93d3cuZmFjZWJvb2suY29tL2FsaGFtYnJhY3VsdHVyYSIgdGFyZ2V0PSJfYmxhbmsiPjwvYT4NCiAgICAgICAgICAgIDwvbGk+DQogICAgICAgICAgICA8bGkgaWQ9ImxpVHdpdGVyIj4NCiAgICAgICAgICAgICAgPGEgaWQ9ImxpbmtUd2l0dGVyIiBjbGFzcz0iaWNvbiBpY29uLXR3aXR0ZXIiIHRpdGxlPSJUd2l0dGVyIiBocmVmPSJodHRwOi8vd3d3LnR3aXR0ZXIuY29tL2FsaGFtYnJhY3VsdHVyYSIgdGFyZ2V0PSJfYmxhbmsiPjwvYT4NCiAgICAgICAgICAgIDwvbGk+DQogICAgICAgICAgICA8bGkgaWQ9ImxpWW91VHViZSI+DQogICAgICAgICAgICAgIDxhIGlkPSJsaW5rWW91VHViZSIgY2xhc3M9Imljb24gaWNvbi15b3V0dWJlIiB0aXRsZT0iWW91dHViZSIgaHJlZj0iaHR0cDovL3d3dy55b3V0dWJlLmNvbS9hbGhhbWJyYXBhdHJvbmF0byIgdGFyZ2V0PSJfYmxhbmsiPjwvYT4NCiAgICAgICAgICAgIDwvbGk+DQogICAgICAgICAgICA8bGkgaWQ9ImxpSW5zdGFncmFtIj4NCiAgICAgICAgICAgICAgPGEgaWQ9ImxpbmtJbnRhZ3JhbSIgY2xhc3M9Imljb24gaWNvbi1pbnN0YWdyYW0iIHRpdGxlPSJJbnN0YWdyYW0iIGhyZWY9Imh0dHBzOi8vd3d3Lmluc3RhZ3JhbS5jb20vYWxoYW1icmFfb2ZpY2lhbC8iIHRhcmdldD0iX2JsYW5rIj48L2E+DQogICAgICAgICAgICA8L2xpPg0KICAgICAgICAgICAgPGxpIGlkPSJsaVBpbnRlcmVzdCI+DQogICAgICAgICAgICAgIDxhIGlkPSJsaW5rUGludGVyZXN0IiBjbGFzcz0iaWNvbiBpY29uLXBpbnRlcmVzdCIgdGl0bGU9IlBpbnRlcmVzdCIgaHJlZj0iaHR0cHM6Ly9lcy5waW50ZXJlc3QuY29tL2FsaGFtYnJhZ3JhbmFkYS8iIHRhcmdldD0iX2JsYW5rIj48L2E+DQogICAgICAgICAgICA8L2xpPg0KICAgICAgICAgIDwvdWw+DQogICAgICAgIDwvZGl2Pg0KICAgICAgICA8IS0tIC8vQ29udGFjdG8geSBSUlNTIC0tPg0KICAgICAgPC9kaXY+DQogICAgPC9kaXY+DQogIDwvZGl2Pg0KICA8ZGl2IGlkPSJkaXZGb290ZXIzIiBjbGFzcz0iZm9vdGVyMyI+DQogICAgPGRpdiBjbGFzcz0iY29udGFpbmVyIj4NCiAgICAgIDxkaXYgY2xhc3M9ImZvb3Rlci1pdGVtIGNvbHVtbi0xIj4NCiAgICAgICAgPGRpdiBjbGFzcz0ibG9nbyBsb2dvRm9vdGVyIj4NCiAgICAgICAgICA8YSBocmVmPSJodHRwOi8vd3d3LmFsaGFtYnJhLXBhdHJvbmF0by5lcy8iIHRhcmdldD0iX2JsYW5rIj4NCiAgICAgICAgICAgIDxpbWcgaWQ9ImltZ0Zvb3RlciIgc3JjPSIvQXBwX1RoZW1lcy9BTEhBTUJSQS9pbWcvbG9nb19wYXRyb25hdG8ucG5nIiBhbHQ9IkFsaGFtYnJhIHkgR2VuZXJhbGlmZSI+DQogICAgICAgICAgPC9hPg0KICAgICAgPC9kaXY+DQogICAgICAgIDxwIGNsYXNzPSJkZXNpZ24iPg0KICAgICAgICAgIDxzcGFuIGlkPSJkZXZlbG9wZWQiPkNvcHlyaWdodCDCqSBJQUNQT1M8L3NwYW4+DQogICAgICAgIDwvcD4NCiAgICAgIDwvZGl2Pg0KICAgICAgPGRpdiBpZD0iZGl2RGlyZWNjaW9uRm9vdGVyIiBjbGFzcz0iZGlyZWNjaW9uIGZvb3Rlci1pdGVtIGNvbHVtbi0xIj4NCiAgICAgICAgPHA+UGF0cm9uYXRvIGRlIGxhIEFsaGFtYnJhIHkgR2VuZXJhbGlmZTwvcD4NCiAgICAgICAgICAgICAgICAgICAgPHA+Qy8gUmVhbCBkZSBsYSBBbGhhbWJyYSBzL248L3A+DQogICAgICAgICAgICAgICAgICAgIDxwPkNQIC0gMTgwMDkgKEdyYW5hZGEpPC9wPg0KICAgICAgPC9kaXY+DQogICAgPC9kaXY+DQogIDwvZGl2Pg0KPC9mb290ZXI+HwZnZAIPDxYCHwZoFhQCAg9kFgoCAQ9kFgICAQ8PFgIfAwUoaHR0cHM6Ly93d3cuZmFjZWJvb2suY29tL2FsaGFtYnJhY3VsdHVyYWRkAgIPZBYCAgEPDxYCHwMFJmh0dHA6Ly93d3cudHdpdHRlci5jb20vYWxoYW1icmFjdWx0dXJhZGQCAw9kFgICAQ8PFgIfAwUoaHR0cDovL3d3dy55b3V0dWJlLmNvbS9hbGhhbWJyYXBhdHJvbmF0b2RkAgQPZBYCAgEPDxYCHwMFK2h0dHBzOi8vd3d3Lmluc3RhZ3JhbS5jb20vYWxoYW1icmFfb2ZpY2lhbC9kZAIFD2QWAgIBDw8WAh8DBSlodHRwczovL2VzLnBpbnRlcmVzdC5jb20vYWxoYW1icmFncmFuYWRhL2RkAgMPZBYGAgEPZBYCZg8PFgQfBAUoL0FwcF9UaGVtZXMvQUxIQU1CUkEvaW1nL2xvZ28tZm9vdGVyLnBuZx8FBRVBbGhhbWJyYSB5IEdlbmVyYWxpZmVkZAIDDxYCHwcFlAE8cD5QYXRyb25hdG8gZGUgbGEgQWxoYW1icmEgeSBHZW5lcmFsaWZlPC9wPg0KICAgICAgICAgICAgICAgICAgICA8cD5DLyBSZWFsIGRlIGxhIEFsaGFtYnJhIHMvbjwvcD4NCiAgICAgICAgICAgICAgICAgICAgPHA+Q1AgLSAxODAwOSAoR3JhbmFkYSk8L3A+ZAIFDw8WAh8BBRNDb3B5cmlnaHQgwqkgSUFDUE9TZGQCBA8PFgIfAwUoaHR0cHM6Ly93d3cuZmFjZWJvb2suY29tL2FsaGFtYnJhY3VsdHVyYWRkAgUPDxYCHwMFJmh0dHA6Ly93d3cudHdpdHRlci5jb20vYWxoYW1icmFjdWx0dXJhZGQCBg8PFgIfAwUraHR0cHM6Ly93d3cuaW5zdGFncmFtLmNvbS9hbGhhbWJyYV9vZmljaWFsL2RkAgcPDxYCHwMFKGh0dHA6Ly93d3cueW91dHViZS5jb20vYWxoYW1icmFwYXRyb25hdG9kZAIIDw8WAh8DZGRkAgkPDxYCHwNkZGQCCg8WAh8HBZQBPHA+UGF0cm9uYXRvIGRlIGxhIEFsaGFtYnJhIHkgR2VuZXJhbGlmZTwvcD4NCiAgICAgICAgICAgICAgICAgICAgPHA+Qy8gUmVhbCBkZSBsYSBBbGhhbWJyYSBzL248L3A+DQogICAgICAgICAgICAgICAgICAgIDxwPkNQIC0gMTgwMDkgKEdyYW5hZGEpPC9wPmQCCw8PFgIfAQUTQ29weXJpZ2h0IMKpIElBQ1BPU2RkAhEPDxYCHwZoZBYEAgEPZBYEAgEPFgIfAQXHBDxwID5FbCByZXNwb25zYWJsZSBkZSBlc3RlIHNpdGlvIHdlYiBmaWd1cmEgZW4gbnVlc3RybyAgPGEgaHJlZj0iaHR0cHM6Ly90aWNrZXRzLmFsaGFtYnJhLXBhdHJvbmF0by5lcy9hdmlzby1sZWdhbC8iID5BdmlzbyBMZWdhbCA8L2EgPi4gPGJyIC8gPlV0aWxpemFtb3MgY29va2llcyBwcm9waWFzIHkgb3BjaW9uYWxtZW50ZSBwb2RlbW9zIHV0aWxpemFyIGNvb2tpZXMgZGUgdGVyY2Vyb3MuIExhIGZpbmFsaWRhZCBkZSBsYXMgY29va2llcyB1dGlsaXphZGFzIGVzOiBmdW5jaW9uYWxlcywgYW5hbMOtdGljYXMgeSBwdWJsaWNpdGFyaWFzLiBObyBzZSB1c2FuIHBhcmEgbGEgZWxhYm9yYWNpw7NuIGRlIHBlcmZpbGVzLiBVc3RlZCBwdWVkZSBjb25maWd1cmFyIGVsIHVzbyBkZSBjb29raWVzIGVuIGVzdGUgbWVudS4gPGJyIC8gPlB1ZWRlIG9idGVuZXIgbcOhcyBpbmZvcm1hY2nDs24sIG8gYmllbiBjb25vY2VyIGPDs21vIGNhbWJpYXIgbGEgY29uZmlndXJhY2nDs24sIGVuIG51ZXN0cmEgPGJyIC8gPiA8YSBocmVmPSIvcG9saXRpY2EtY29va2llcy5hc3B4IiA+UG9sw610aWNhIGRlIGNvb2tpZXMgPC9hID4uPC9wID5kAgMPDxYCHwEFGEFjZXB0YXIgdG9kbyB5IGNvbnRpbnVhcmRkAgMPZBYIAgEPDxYCHwZoZGQCAw8WAh8BBccEPHAgPkVsIHJlc3BvbnNhYmxlIGRlIGVzdGUgc2l0aW8gd2ViIGZpZ3VyYSBlbiBudWVzdHJvICA8YSBocmVmPSJodHRwczovL3RpY2tldHMuYWxoYW1icmEtcGF0cm9uYXRvLmVzL2F2aXNvLWxlZ2FsLyIgPkF2aXNvIExlZ2FsIDwvYSA+LjxiciAvID4gVXRpbGl6YW1vcyBjb29raWVzIHByb3BpYXMgeSBvcGNpb25hbG1lbnRlIHBvZGVtb3MgdXRpbGl6YXIgY29va2llcyBkZSB0ZXJjZXJvcy4gTGEgZmluYWxpZGFkIGRlIGxhcyBjb29raWVzIHV0aWxpemFkYXMgZXM6IGZ1bmNpb25hbGVzLCBhbmFsw610aWNhcyB5IHB1YmxpY2l0YXJpYXMuIE5vIHNlIHVzYW4gcGFyYSBsYSBlbGFib3JhY2nDs24gZGUgcGVyZmlsZXMuIFVzdGVkIHB1ZWRlIGNvbmZpZ3VyYXIgZWwgdXNvIGRlIGNvb2tpZXMgZW4gZXN0ZSBtZW51LiA8YnIgLyA+UHVlZGUgb2J0ZW5lciBtw6FzIGluZm9ybWFjacOzbiwgbyBiaWVuIGNvbm9jZXIgY8OzbW8gY2FtYmlhciBsYSBjb25maWd1cmFjacOzbiwgZW4gbnVlc3RyYSA8YnIgLyA+IDxhIGhyZWY9Ii9wb2xpdGljYS1jb29raWVzLmFzcHgiID5Qb2zDrXRpY2EgZGUgY29va2llcyA8L2EgPi48L3AgPmQCBw8PFgIfAQUYQWNlcHRhciB0b2RvIHkgY29udGludWFyZGQCCQ8PFgIfAQUgQWNlcHRhciBzZWxlY2Npb25hZG8geSBjb250aW51YXJkZAIDDxYEHwEF4gE8IS0tIFN0YXJ0IG9mIGNhdWFsaGFtYnJhIFplbmRlc2sgV2lkZ2V0IHNjcmlwdCAtLT4NCjxzY3JpcHQgaWQ9InplLXNuaXBwZXQiIHNyYz1odHRwczovL3N0YXRpYy56ZGFzc2V0cy5jb20vZWtyL3NuaXBwZXQuanM/a2V5PTViN2FlMTI5LTlhM2MtNGQyZi1iOTQ0LTE0NzJkZjlmYjUzMz4gPC9zY3JpcHQ+DQo8IS0tIEVuZCBvZiBjYXVhbGhhbWJyYSBaZW5kZXNrIFdpZGdldCBzY3JpcHQgLS0+HwZnZBgDBR5fX0NvbnRyb2xzUmVxdWlyZVBvc3RCYWNrS2V5X18WAQUfY3RsMDAkY2hrUmVnaXN0cm9BY2VwdG9Qb2xpdGljYQVHY3RsMDAkQ29udGVudE1hc3RlcjEkdWNSZXNlcnZhckVudHJhZGFzQmFzZUFsaGFtYnJhMSR1Y0ltcG9ydGFyJFdpemFyZDEPEGQUKwEBZmZkBVdjdGwwMCRDb250ZW50TWFzdGVyMSR1Y1Jlc2VydmFyRW50cmFkYXNCYXNlQWxoYW1icmExJHVjSW1wb3J0YXIkV2l6YXJkMSRXaXphcmRNdWx0aVZpZXcPD2RmZI/EkmJftCy0+DHEDcgtxcSzhchG"
                try:
                    viewstate_elem = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.ID, "__VIEWSTATE"))
                    )
                    driver.execute_script(
                        f"arguments[0].value = `{viewstate_funcional}`;", viewstate_elem
                    )
                except Exception as e:
                    print(f"No se pudo encontrar o modificar __VIEWSTATE: {e}")
                    logging.error(f"No se pudo encontrar o modificar __VIEWSTATE: {e}")

                # time.sleep(TIEMPO)

                # 4. Hacer clic de nuevo en el mismo botón
                boton = WebDriverWait(driver, 2).until(
                    EC.element_to_be_clickable(
                        (By.ID, "ctl00_ContentMaster1_ucReservarEntradasBaseAlhambra1_btnIrPaso1")
                    )
                )
                boton.click()

                # Esperar a que desaparezca la capa de carga si existe
                try:
                    WebDriverWait(driver, 5).until(
                        EC.invisibility_of_element_located((By.ID, "divCargando"))
                    )
                except:
                    print("La capa de carga no desapareció, se continúa de todas formas.")

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

                # --- Espera si son las 23:59 ---
                ahora = datetime.datetime.now()
                if ahora.hour == 23 and (ahora.minute == 59 or ahora.minute == 58):
                    mensaje_bloqueo = "Es 23:59, la página puede estar bloqueada. Esperando 2 horas..."
                    print(mensaje_bloqueo)
                    logging.info(mensaje_bloqueo)
                    enviar_telegram(mensaje_bloqueo, 1)  # Prioridad 1
                    time.sleep(2 * 60 * 60)  # Esperar 2 horas
                    # time.sleep(1860)  # Esperar 2 horas

                    manejar_alerta_si_existe(driver)
                    # Simular tecla Enter tras la espera
                    # pyautogui.press('enter')
                    driver.refresh()

                    continue  # Volver al inicio del bucle

                viewState = 0

                icon.icon = crear_icono_verde()

                print(f"\n Intento #{counter}")
                logging.info(f"\n Intento #{counter}")

                counter += 1

                driver.refresh()

                try:
                    WebDriverWait(driver, 3).until(
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
                    viewstate_funcional = "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OTUyZxAFBDE5NTMFBDE5NTNnEAUEMTk1NAUEMTk1NGcQBQQxOTU1BQQxOTU1ZxAFBDE5NTYFBDE5NTZnEAUEMTk1NwUEMTk1N2cQBQQxOTU4BQQxOTU4ZxAFBDE5NTkFBDE5NTlnEAUEMTk2MAUEMTk2MGcQBQQxOTYxBQQxOTYxZxAFBDE5NjIFBDE5NjJnEAUEMTk2MwUEMTk2M2cQBQQxOTY0BQQxOTY0ZxAFBDE5NjUFBDE5NjVnEAUEMTk2NgUEMTk2NmcQBQQxOTY3BQQxOTY3ZxAFBDE5NjgFBDE5NjhnEAUEMTk2OQUEMTk2OWcQBQQxOTcwBQQxOTcwZxAFBDE5NzEFBDE5NzFnEAUEMTk3MgUEMTk3MmcQBQQxOTczBQQxOTczZxAFBDE5NzQFBDE5NzRnEAUEMTk3NQUEMTk3NWcQBQQxOTc2BQQxOTc2ZxAFBDE5NzcFBDE5NzdnEAUEMTk3OAUEMTk3OGcQBQQxOTc5BQQxOTc5ZxAFBDE5ODAFBDE5ODBnEAUEMTk4MQUEMTk4MWcQBQQxOTgyBQQxOTgyZxAFBDE5ODMFBDE5ODNnEAUEMTk4NAUEMTk4NGcQBQQxOTg1BQQxOTg1ZxAFBDE5ODYFBDE5ODZnEAUEMTk4NwUEMTk4N2cQBQQxOTg4BQQxOTg4ZxAFBDE5ODkFBDE5ODlnEAUEMTk5MAUEMTk5MGcQBQQxOTkxBQQxOTkxZxAFBDE5OTIFBDE5OTJnEAUEMTk5MwUEMTk5M2cQBQQxOTk0BQQxOTk0ZxAFBDE5OTUFBDE5OTVnEAUEMTk5NgUEMTk5NmcQBQQxOTk3BQQxOTk3ZxAFBDE5OTgFBDE5OThnEAUEMTk5OQUEMTk5OWcQBQQyMDAwBQQyMDAwZxAFBDIwMDEFBDIwMDFnEAUEMjAwMgUEMjAwMmcQBQQyMDAzBQQyMDAzZxAFBDIwMDQFBDIwMDRnEAUEMjAwNQUEMjAwNWcQBQQyMDA2BQQyMDA2ZxAFBDIwMDcFBDIwMDdnEAUEMjAwOAUEMjAwOGcQBQQyMDA5BQQyMDA5ZxAFBDIwMTAFBDIwMTBnEAUEMjAxMQUEMjAxMWcQBQQyMDEyBQQyMDEyZxAFBDIwMTMFBDIwMTNnEAUEMjAxNAUEMjAxNGcQBQQyMDE1BQQyMDE1ZxAFBDIwMTYFBDIwMTZnEAUEMjAxNwUEMjAxN2cQBQQyMDE4BQQyMDE4ZxAFBDIwMTkFBDIwMTlnEAUEMjAyMAUEMjAyMGcQBQQyMDIxBQQyMDIxZxAFBDIwMjIFBDIwMjJnEAUEMjAyMwUEMjAyM2cQBQQyMDI0BQQyMDI0ZxAFBDIwMjUFBDIwMjVnFgFmZAILDxYCHwZoFgICAQ8WAh8HZGQCDA9kFgICAQ8WAh8HBQVFbWFpbGQCDQ9kFgICAQ8WAh8HBQ5Db25maXJtYSBFbWFpbGQCDg9kFgICAQ8WAh8HBQtDb250cmFzZcOxYWQCDw9kFgICAQ8WAh8HBRNSZXBldGlyIENvbnRyYXNlw7FhZAIQDxYCHwZoFgICAQ8WAh8HZWQCEQ8WAh8GaBYCAgEPFgIfB2VkAhIPFgIfBmgWAgIBDxYCHwdlZAITDxYCHwZoFgYCAQ8WAh8HZWQCAw8PFgQeCENzc0NsYXNzBRJpbnB1dC10ZXh0IG9jdWx0YXIeBF8hU0ICAmRkAgUPEA8WBB8JZR8KAgJkEBU1FFNlbGVjY2lvbmUgcHJvdmluY2lhCEFsYmFjZXRlCEFsaWNhbnRlCEFsbWVyw61hBsOBbGF2YQhBc3R1cmlhcwbDgXZpbGEHQmFkYWpveg1CYWxlYXJzIElsbGVzCUJhcmNlbG9uYQdCaXprYWlhBkJ1cmdvcwhDw6FjZXJlcwZDw6FkaXoJQ2FudGFicmlhCkNhc3RlbGzDs24LQ2l1ZGFkIFJlYWwIQ8OzcmRvYmEJQ29ydcOxYSBBBkN1ZW5jYQhHaXB1emtvYQZHaXJvbmEHR3JhbmFkYQtHdWFkYWxhamFyYQZIdWVsdmEGSHVlc2NhBUphw6luBUxlw7NuBkxsZWlkYQRMdWdvBk1hZHJpZAdNw6FsYWdhBk11cmNpYQdOYXZhcnJhB091cmVuc2UIUGFsZW5jaWEKUGFsbWFzIExhcwpQb250ZXZlZHJhCFJpb2phIExhCVNhbGFtYW5jYRZTYW50YSBDcnV6IGRlIFRlbmVyaWZlB1NlZ292aWEHU2V2aWxsYQVTb3JpYQlUYXJyYWdvbmEGVGVydWVsBlRvbGVkbwhWYWxlbmNpYQpWYWxsYWRvbGlkBlphbW9yYQhaYXJhZ296YQVDZXV0YQdNZWxpbGxhFTUAAjAyAjAzAjA0AjAxAjMzAjA1AjA2AjA3AjA4AjQ4AjA5AjEwAjExAjM5AjEyAjEzAjE0AjE1AjE2AjIwAjE3AjE4AjE5AjIxAjIyAjIzAjI0AjI1AjI3AjI4AjI5AjMwAjMxAjMyAjM0AjM1AjM2AjI2AjM3AjM4AjQwAjQxAjQyAjQzAjQ0AjQ1AjQ2AjQ3AjQ5AjUwAjUxAjUyFCsDNWdnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnFgFmZAIUD2QWBgIBDxYCHwcFBVBhw61zZAIDDw8WAh8GaGRkAgUPEGQQFe8BE1NlbGVjY2lvbmUgdW4gcGHDrXMJQXJnZW50aW5hCUF1c3RyYWxpYQVDaGluYQVJdGFseQVKYXBhbgZNZXhpY28LTmV3IFplYWxhbmQIUG9ydHVnYWwHRXNwYcOxYQdHZXJtYW55BkZyYW5jZRJSdXNzaWFuIEZlZGVyYXRpb24OVW5pdGVkIEtpbmdkb20UVW5pdGVkIFN0YXRlcyBvZiBBbWULQWZnaGFuaXN0YW4HQWxiYW5pYQdBbGdlcmlhDkFtZXJpY2FuIFNhbW9hB0FuZG9ycmEGQW5nb2xhCEFuZ3VpbGxhCkFudGFyY3RpY2EHQW50aWd1YQdBcm1lbmlhBUFydWJhB0F1c3RyaWEKQXplcmJhaWphbgdCYWhhbWFzB0JhaHJhaW4KQmFuZ2xhZGVzaAhCYXJiYWRvcwdCZWxhcnVzB0JlbGdpdW0GQmVsaXplBUJlbmluB0Jlcm11ZGEGQmh1dGFuB0JvbGl2aWEGQm9zbmlhCEJvdHN3YW5hDUJvdXZldCBJc2xhbmQGQnJhemlsDkJyaXRpc2ggSW5kaWFuEUJydW5laSBEYXJ1c3NhbGFtCEJ1bGdhcmlhDEJ1cmtpbmEgRmFzbwdCdXJ1bmRpCENhbWJvZGlhCENhbWVyb29uBkNhbmFkYQpDYXBlIFZlcmRlDkNheW1hbiBJc2xhbmRzE0NlbnRyYWwgQWZyaWNhbiBSZXAEQ2hhZAVDaGlsZRBDaHJpc3RtYXMgSXNsYW5kDUNvY29zIElzbGFuZHMIQ29sb21iaWEHQ29tb3JvcwVDb25nbwxDb29rIElzbGFuZHMKQ29zdGEgUmljYQdDcm9hdGlhBEN1YmEGQ3lwcnVzDkN6ZWNoIFJlcHVibGljB0Rlbm1hcmsIRGppYm91dGkIRG9taW5pY2ESRG9taW5pY2FuIFJlcHVibGljCkVhc3QgVGltb3IHRWN1YWRvcgVFZ3lwdAtFbCBTYWx2YWRvchFFcXVhdG9yaWFsIEd1aW5lYQdFcml0cmVhB0VzdG9uaWEIRXRoaW9waWENRmFyb2UgSXNsYW5kcwRGaWppB0ZpbmxhbmQNRnJlbmNoIEd1aWFuYRBGcmVuY2ggUG9seW5lc2lhBUdhYm9uBkdhbWJpYQdHZW9yZ2lhBUdoYW5hBkdyZWVjZQlHcmVlbmxhbmQHR3JlbmFkYQpHdWFkZWxvdXBlBEd1YW0JR3VhdGVtYWxhBkd1aW5lYQ1HdWluZWEgQmlzc2F1Bkd1eWFuYQVIYWl0aQhIb25kdXJhcwlIb25nIEtvbmcHSHVuZ2FyeQdJY2VsYW5kBUluZGlhCUluZG9uZXNpYQRJcmFuBElyYXEHSXJlbGFuZAZJc3JhZWwLSXZvcnkgQ29hc3QHSmFtYWljYQZKb3JkYW4KS2F6YWtoc3RhbgVLZW55YQhLaXJpYmF0aQZLdXdhaXQKS3lyZ3l6c3RhbgNMYW8GTGF0dmlhB0xlYmFub24HTGVzb3RobwdMaWJlcmlhBUxpYnlhDUxpZWNodGVuc3RlaW4JTGl0aHVhbmlhCkx1eGVtYm91cmcFTWFjYXUJTWFjZWRvbmlhCk1hZGFnYXNjYXIGTWFsYXdpCE1hbGF5c2lhCE1hbGRpdmVzBE1hbGkFTWFsdGEITWFsdmluYXMQTWFyc2hhbGwgSXNsYW5kcwpNYXJ0aW5pcXVlCk1hdXJpdGFuaWEJTWF1cml0aXVzB01heW90dGUKTWljcm9uZXNpYQdNb2xkb3ZhBk1vbmFjbwhNb25nb2xpYQpNb250ZW5lZ3JvCk1vbnRzZXJyYXQHTW9yb2NjbwpNb3phbWJpcXVlB015YW5tYXIHTmFtaWJpYQVOYXVydQVOZXBhbAtOZXRoZXJsYW5kcxROZXRoZXJsYW5kcyBBbnRpbGxlcw1OZXcgQ2FsZWRvbmlhCU5pY2FyYWd1YQVOaWdlcgdOaWdlcmlhBE5pdWUOTm9yZm9sayBJc2xhbmQLTm9ydGggS29yZWETTm9ydGhlcm4gTWFyaWFuYSBJcwZOb3J3YXkET21hbhlPdHJvcyBkZSBwYWlzZXMgZGVsIG11bmRvCFBha2lzdGFuBVBhbGF1BlBhbmFtYRBQYXB1YSBOZXcgR3VpbmVhCFBhcmFndWF5BFBlcnULUGhpbGlwcGluZXMIUGl0Y2Fpcm4GUG9sYW5kC1B1ZXJ0byBSaWNvBVFhdGFyB1JldW5pb24HUm9tYW5pYQZSd2FuZGEPUyBHZW9yZ2lhIFNvdXRoC1NhaW50IEx1Y2lhBVNhbW9hClNhbiBNYXJpbm8TU2FvIFRvbWUgLSBQcmluY2lwZQxTYXVkaSBBcmFiaWEHU2VuZWdhbAZTZXJiaWEKU2V5Y2hlbGxlcwxTaWVycmEgTGVvbmUJU2luZ2Fwb3JlCFNsb3Zha2lhCFNsb3ZlbmlhD1NvbG9tb24gSXNsYW5kcwdTb21hbGlhDFNvdXRoIEFmcmljYQtTb3V0aCBLb3JlYQlTcmkgTGFua2EJU3QgSGVsZW5hElN0IEtpdHRzIGFuZCBOZXZpcxNTdCBQaWVycmUgIE1pcXVlbG9uEVN0IFZpbmNlbnQtR3JlbmFkBVN1ZGFuCFN1cmluYW1lEVN2YWxiYXJkIEphbiBNIElzCVN3YXppbGFuZAZTd2VkZW4LU3dpdHplcmxhbmQFU3lyaWEGVGFpd2FuClRhamlraXN0YW4IVGFuemFuaWEIVGhhaWxhbmQEVG9nbwdUb2tlbGF1BVRvbmdhE1RyaW5pZGFkIEFuZCBUb2JhZ28HVHVuaXNpYQZUdXJrZXkMVHVya21lbmlzdGFuFFR1cmtzIENhaWNvcyBJc2xhbmRzBlR1dmFsdQZVZ2FuZGEHVWtyYWluZRRVbml0ZWQgQXJhYiBFbWlyYXRlcwdVcnVndWF5EFVTIE1pbm9yIElzbGFuZHMKVXpiZWtpc3RhbgdWYW51YXR1B1ZhdGljYW4JVmVuZXp1ZWxhB1ZpZXRuYW0OVmlyZ2luIElzbGFuZHMRVmlyZ2luIElzbGFuZHMgVVMQV2FsbGlzIEZ1dHVuYSBJcw5XZXN0ZXJuIFNhaGFyYQVZZW1lbgpZdWdvc2xhdmlhBVphaXJlBlphbWJpYQhaaW1iYWJ3ZRXvAQADMDMyAzAzNgMxNTYDMzgwAzM5MgM0ODQDNTU0AzYyMAM3MjQDMjc2AzI1MAM2NDMDODI2Azg0MAMwMDQDMDA4AzAxMgMwMTYDMDIwAzAyNAM2NjADMDEwAzAyOAMwNTEDNTMzAzA0MAMwMzEDMDQ0AzA0OAMwNTADMDUyAzExMgMwNTYDMDg0AzIwNAMwNjADMDY0AzA2OAMwNzADMDcyAzA3NAMwNzYDMDg2AzA5NgMxMDADODU0AzEwOAMxMTYDMTIwAzEyNAMxMzIDMTM2AzE0MAMxNDgDMTUyAzE2MgMxNjYDMTcwAzE3NAMxNzgDMTg0AzE4OAMxOTEDMTkyAzE5NgMyMDMDMjA4AzI2MgMyMTIDMjE0AzYyNgMyMTgDODE4AzIyMgMyMjYDMjMyAzIzMwMyMzEDMjM0AzI0MgMyNDYDMjU0AzI1OAMyNjYDMjcwAzI2OAMyODgDMzAwAzMwNAMzMDgDMzEyAzMxNgMzMjADMzI0AzYyNAMzMjgDMzMyAzM0MAMzNDQDMzQ4AzM1MgMzNTYDMzYwAzM2NAMzNjgDMzcyAzM3NgMzODQDMzg4AzQwMAMzOTgDNDA0AzI5NgM0MTQDNDE3AzQxOAM0MjgDNDIyAzQyNgM0MzADNDM0AzQzOAM0NDADNDQyAzQ0NgM4MDcDNDUwAzQ1NAM0NTgDNDYyAzQ2NgM0NzADMjM4AzU4NAM0NzQDNDc4AzQ4MAMxNzUDNTgzAzQ5OAM0OTIDNDk2AzQ5OQM1MDADNTA0AzUwOAMxMDQDNTE2AzUyMAM1MjQDNTI4AzUzMAM1NDADNTU4AzU2MgM1NjYDNTcwAzU3NAM0MDgDNTgwAzU3OAM1MTIDNzQ0AzU4NgM1ODUDNTkxAzU5OAM2MDADNjA0AzYwOAM2MTIDNjE2AzYzMAM2MzQDNjM4AzY0MgM2NDYDMjM5AzY2MgM4ODIDNjc0AzY3OAM2ODIDNjg2AzY4OAM2OTADNjk0AzcwMgM3MDMDNzA1AzA5MAM3MDYDNzEwAzQxMAMxNDQDNjU0AzY1OQM2NjYDNjcwAzczNgM3NDADNzQ0Azc0OAM3NTIDNzU2Azc2MAMxNTgDNzYyAzgzNAM3NjQDNzY4Azc3MgM3NzYDNzgwAzc4OAM3OTIDNzk1Azc5NgM3OTgDODAwAzgwNAM3ODQDODU4AzU4MQM4NjADNTQ4AzMzNgM4NjIDNzA0AzA5MgM4NTADODc2AzczMgM4ODcDODkxAzE4MAM4OTQDNzE2FCsD7wFnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2RkAhUPZBYCAgEPFgIfBwUJVGVsw6lmb25vZAIXD2QWAgIDDxYCHwcFiQFIZSBsZcOtZG8geSBhY2VwdG8gbGEgPGEgaHJlZj0iaHR0cHM6Ly90aWNrZXRzLmFsaGFtYnJhLXBhdHJvbmF0by5lcy9wb2xpdGljYS1kZS1wcml2YWNpZGFkLyIgdGFyZ2V0PSJfYmxhbmsiPlBvbMOtdGljYSBkZSBwcml2YWNpZGFkPC9hPmQCGA8WAh8GaBYCAgMPFgIfB2VkAggPDxYCHwEFC1JlZ8Otc3RyZXNlZGQCAw8WAh8GaBYEAgMPDxYCHwMFHi9yZXNlcnZhckVudHJhZGFzLmFzcHg/b3BjPTE0M2RkAgUPDxYCHwEFDkNlcnJhciBzZXNpw7NuZGQCAQ9kFgICAQ8PFgQfCQUGYWN0aXZlHwoCAmRkAgIPDxYEHwMFPmh0dHBzOi8vd3d3LmFsaGFtYnJhLXBhdHJvbmF0by5lcy92aXNpdGFyL3ByZWd1bnRhcy1mcmVjdWVudGVzHwZnZGQCBA9kFgICAQ8PFgIfAwUoaHR0cDovL3d3dy55b3V0dWJlLmNvbS9hbGhhbWJyYXBhdHJvbmF0b2RkAgUPZBYCAgEPDxYCHwMFK2h0dHBzOi8vd3d3Lmluc3RhZ3JhbS5jb20vYWxoYW1icmFfb2ZpY2lhbC9kZAIGD2QWAgIBDw8WAh8DBShodHRwczovL3d3dy5mYWNlYm9vay5jb20vYWxoYW1icmFjdWx0dXJhZGQCBw9kFgICAQ8PFgIfAwUmaHR0cDovL3d3dy50d2l0dGVyLmNvbS9hbGhhbWJyYWN1bHR1cmFkZAIID2QWAgIBDw8WAh8DBSlodHRwczovL2VzLnBpbnRlcmVzdC5jb20vYWxoYW1icmFncmFuYWRhL2RkAgkPFgIfBmhkAgoPFgIfBmgWAgIBDw8WAh8DZGQWAmYPDxYCHwUFFUFsaGFtYnJhIHkgR2VuZXJhbGlmZWRkAgsPZBYCZg8PFgQfAwU+aHR0cHM6Ly93d3cuYWxoYW1icmEtcGF0cm9uYXRvLmVzL3Zpc2l0YXIvcHJlZ3VudGFzLWZyZWN1ZW50ZXMfBmdkZAIND2QWCAIBDw8WAh8GaGQWAgIBD2QWAmYPZBYGAgMPDxYCHwZoZGQCBA8PFgIeBkVzdGFkb2ZkFgJmD2QWAgIBD2QWAmYPZBYCAgEPZBYCAggPFgIfBmhkAg4PZBYEAgsPZBYEAgEPZBYCAgMPEGRkFgBkAgYPZBYCAgcPEGRkFgBkAg0PZBYEAgYPZBYCAgEPZBYCAgMPEGRkFgBkAgkPZBYCAgcPEGRkFgBkAgMPDxYCHwZoZBYCZg9kFgJmD2QWBgIBDw8WAh8GaGRkAggPZBYGAgUPZBYCAgEPEGRkFgBkAgYPZBYCAgEPEGRkFgBkAggPZBYEZg8QZGQWAGQCAQ8QZGQWAGQCCg9kFgICBQ9kFg4CAw9kFgICBQ8QZGQWAGQCBA9kFgICAw8QZGQWAGQCBg9kFgICBw8QZGQWAGQCCA9kFgICBQ8QZGQWAGQCCQ9kFgICBQ8QZGQWAGQCDw9kFgICBw8QZGQWAGQCFg9kFgQCAQ9kFgICAw8QZGQWAGQCBg9kFgICBw8QZGQWAGQCBQ8PFgIfBmhkFgJmD2QWAmYPZBYEAgMPDxYCHwtmZBYCZg9kFgICAQ9kFgJmD2QWAgIBD2QWAgIIDxYCHwZoZAIGD2QWAmYPZBYCAgEPZBYCZg9kFgICAQ88KwAKAQAPFgQeDVByZXZNb250aFRleHRlHg1OZXh0TW9udGhUZXh0BS08aW1nIHNyYz0vQXBwX3RoZW1lcy9BTEhBTUJSQS9pbWcvbmV4dC5wbmcgLz5kZAIHDw8WIB4UTG9jYWxpemFkb3JQYXJhbWV0cm9kHhBGaW5hbGl6YXJNZW5vcmVzaB4OQWZvcm9QYXJhbWV0cm8CAR4GUGFnYWRhBQVGYWxzZR4HU2ltYm9sbwUD4oKsHhNFbmxhY2VNZW51UGFyYW1ldHJvBQdHRU5FUkFMHgxTZXNpb25EaWFyaWFoHgpOb21pbmFjaW9uZh4MQ2FwdGNoYVBhc28xZx4MTnVtRGVjaW1hbGVzAgIeD0NhcHRjaGFWYWxpZGFkb2ceCFNpbkZlY2hhZh4VRmVjaGFNaW5pbWFEaXNwb25pYmxlBv8/N/R1KMorHgxUZW5lbW9zTmlub3NoHhZHcnVwb0ludGVybmV0UGFyYW1ldHJvBQMxNDMeDFNlc2lvbkFjdHVhbAUfNG1vZXBsNDVubWZiYzNpMXhlbHlnZHVrMzA1OTEwNmQWBAIBD2QWAmYPZBYiAgMPDxYCHwZoZGQCBA8PFgIfC2ZkFgJmD2QWAgIBD2QWAmYPZBYCAgEPZBYGZg8PFgIfAQUFZW1haWxkZAICDw8WAh8BBQxUZWxlZm9ubyBTTVNkZAIIDxYCHwZoZAIFDw8WAh8DBTBodHRwczovL3d3dy5hbGhhbWJyYS1wYXRyb25hdG8uZXMvP2NhPTAmbGc9ZXMtRVNkZAIGDxYCHwFlZAIHDxYCHwEFJlZpc2l0YSBKYXJkaW5lcywgR2VuZXJhbGlmZSB5IEFsY2F6YWJhZAIIDxYCHgVjbGFzcwUWc3RlcC10aXRsZSBzdGVwLWFjdGl2ZRYCAgEPFgIfAWRkAgkPDxYCHwZoZBYCAgEPDxYCHwEFC0lyIGEgcGFzbyAxZGQCCg8PFgIfBmdkFghmDxYCHwFlZAIBDxYCHwFlZAIGDw8WHB4RRmVjaGFNaW5pbWFHbG9iYWwGAN+AOmZ43QgeBFBhc28CAR4NR3J1cG9JbnRlcm5ldAUDMTQzHhVUb3RhbE1lc2VzQWRlbGFudGFkb3MCAR4MRGF0b3NGZXN0aXZvMrsEAAEAAAD/////AQAAAAAAAAAMAgAAAEhBcHBfQ29kZS54aGpwdml6bywgVmVyc2lvbj0wLjAuMC4wLCBDdWx0dXJlPW5ldXRyYWwsIFB1YmxpY0tleVRva2VuPW51bGwFAQAAAB9EYXRvc0Zlc3Rpdm9zK0RhdG9zTGlzdEZlc3Rpdm9zAQAAABFfTHN0RGF0b3NGZXN0aXZvcwOJAVN5c3RlbS5Db2xsZWN0aW9ucy5HZW5lcmljLkxpc3RgMVtbRGF0b3NGZXN0aXZvcytEYXRvc0Zlc3Rpdm8sIEFwcF9Db2RlLnhoanB2aXpvLCBWZXJzaW9uPTAuMC4wLjAsIEN1bHR1cmU9bmV1dHJhbCwgUHVibGljS2V5VG9rZW49bnVsbF1dAgAAAAkDAAAABAMAAACJAVN5c3RlbS5Db2xsZWN0aW9ucy5HZW5lcmljLkxpc3RgMVtbRGF0b3NGZXN0aXZvcytEYXRvc0Zlc3Rpdm8sIEFwcF9Db2RlLnhoanB2aXpvLCBWZXJzaW9uPTAuMC4wLjAsIEN1bHR1cmU9bmV1dHJhbCwgUHVibGljS2V5VG9rZW49bnVsbF1dAwAAAAZfaXRlbXMFX3NpemUIX3ZlcnNpb24EAAAcRGF0b3NGZXN0aXZvcytEYXRvc0Zlc3Rpdm9bXQIAAAAICAkEAAAAAAAAAAAAAAAHBAAAAAABAAAAAAAAAAQaRGF0b3NGZXN0aXZvcytEYXRvc0Zlc3Rpdm8CAAAACx4TTWluaW1vR3J1cG9JbnRlcm5ldAIBHhFGZWNoYU1heGltYUdsb2JhbAYAusZyFKfeCB4PRGlyZWNjaW9uQWN0dWFsBQRQcmV2Hg1Fc0xpc3RhRXNwZXJhaB4LRm9yemFyQ2FyZ2FoHg5GZWNoYXNWaWdlbmNpYTKIDQABAAAA/////wEAAAAAAAAABAEAAADiAVN5c3RlbS5Db2xsZWN0aW9ucy5HZW5lcmljLkRpY3Rpb25hcnlgMltbU3lzdGVtLlN0cmluZywgbXNjb3JsaWIsIFZlcnNpb249NC4wLjAuMCwgQ3VsdHVyZT1uZXV0cmFsLCBQdWJsaWNLZXlUb2tlbj1iNzdhNWM1NjE5MzRlMDg5XSxbU3lzdGVtLlN0cmluZywgbXNjb3JsaWIsIFZlcnNpb249NC4wLjAuMCwgQ3VsdHVyZT1uZXV0cmFsLCBQdWJsaWNLZXlUb2tlbj1iNzdhNWM1NjE5MzRlMDg5XV0EAAAAB1ZlcnNpb24IQ29tcGFyZXIISGFzaFNpemUNS2V5VmFsdWVQYWlycwADAAMIkgFTeXN0ZW0uQ29sbGVjdGlvbnMuR2VuZXJpYy5HZW5lcmljRXF1YWxpdHlDb21wYXJlcmAxW1tTeXN0ZW0uU3RyaW5nLCBtc2NvcmxpYiwgVmVyc2lvbj00LjAuMC4wLCBDdWx0dXJlPW5ldXRyYWwsIFB1YmxpY0tleVRva2VuPWI3N2E1YzU2MTkzNGUwODldXQjmAVN5c3RlbS5Db2xsZWN0aW9ucy5HZW5lcmljLktleVZhbHVlUGFpcmAyW1tTeXN0ZW0uU3RyaW5nLCBtc2NvcmxpYiwgVmVyc2lvbj00LjAuMC4wLCBDdWx0dXJlPW5ldXRyYWwsIFB1YmxpY0tleVRva2VuPWI3N2E1YzU2MTkzNGUwODldLFtTeXN0ZW0uU3RyaW5nLCBtc2NvcmxpYiwgVmVyc2lvbj00LjAuMC4wLCBDdWx0dXJlPW5ldXRyYWwsIFB1YmxpY0tleVRva2VuPWI3N2E1YzU2MTkzNGUwODldXVtdBwAAAAkCAAAABwAAAAkDAAAABAIAAACSAVN5c3RlbS5Db2xsZWN0aW9ucy5HZW5lcmljLkdlbmVyaWNFcXVhbGl0eUNvbXBhcmVyYDFbW1N5c3RlbS5TdHJpbmcsIG1zY29ybGliLCBWZXJzaW9uPTQuMC4wLjAsIEN1bHR1cmU9bmV1dHJhbCwgUHVibGljS2V5VG9rZW49Yjc3YTVjNTYxOTM0ZTA4OV1dAAAAAAcDAAAAAAEAAAAHAAAAA+QBU3lzdGVtLkNvbGxlY3Rpb25zLkdlbmVyaWMuS2V5VmFsdWVQYWlyYDJbW1N5c3RlbS5TdHJpbmcsIG1zY29ybGliLCBWZXJzaW9uPTQuMC4wLjAsIEN1bHR1cmU9bmV1dHJhbCwgUHVibGljS2V5VG9rZW49Yjc3YTVjNTYxOTM0ZTA4OV0sW1N5c3RlbS5TdHJpbmcsIG1zY29ybGliLCBWZXJzaW9uPTQuMC4wLjAsIEN1bHR1cmU9bmV1dHJhbCwgUHVibGljS2V5VG9rZW49Yjc3YTVjNTYxOTM0ZTA4OV1dBPz////kAVN5c3RlbS5Db2xsZWN0aW9ucy5HZW5lcmljLktleVZhbHVlUGFpcmAyW1tTeXN0ZW0uU3RyaW5nLCBtc2NvcmxpYiwgVmVyc2lvbj00LjAuMC4wLCBDdWx0dXJlPW5ldXRyYWwsIFB1YmxpY0tleVRva2VuPWI3N2E1YzU2MTkzNGUwODldLFtTeXN0ZW0uU3RyaW5nLCBtc2NvcmxpYiwgVmVyc2lvbj00LjAuMC4wLCBDdWx0dXJlPW5ldXRyYWwsIFB1YmxpY0tleVRva2VuPWI3N2E1YzU2MTkzNGUwODldXQIAAAADa2V5BXZhbHVlAQEGBQAAAAM0MzIGBgAAABcjMTAvMDQvMjAyNS0zMC8wNC8yMDI1IwH5/////P///wYIAAAAAzQzMwYJAAAAFyMxMC8wNC8yMDI1LTMwLzA0LzIwMjUjAfb////8////BgsAAAADNDg4BgwAAAAXIzEwLzA0LzIwMjUtMzAvMDQvMjAyNSMB8/////z///8GDgAAAAM0MzQGDwAAABcjMTAvMDQvMjAyNS0zMC8wNC8yMDI1IwHw/////P///wYRAAAAAzQ4NgYSAAAAFyMxMC8wNC8yMDI1LTMwLzA0LzIwMjUjAe3////8////BhQAAAADNDg3BhUAAAAXIzEwLzA0LzIwMjUtMzAvMDQvMjAyNSMB6v////z///8GFwAAAAM0ODkGGAAAABcjMTAvMDQvMjAyNS0zMC8wNC8yMDI1IwsfBmceEENhbnRpZGFkRW50cmFkYXMy2wQAAQAAAP////8BAAAAAAAAAAQBAAAA4QFTeXN0ZW0uQ29sbGVjdGlvbnMuR2VuZXJpYy5EaWN0aW9uYXJ5YDJbW1N5c3RlbS5TdHJpbmcsIG1zY29ybGliLCBWZXJzaW9uPTQuMC4wLjAsIEN1bHR1cmU9bmV1dHJhbCwgUHVibGljS2V5VG9rZW49Yjc3YTVjNTYxOTM0ZTA4OV0sW1N5c3RlbS5JbnQzMiwgbXNjb3JsaWIsIFZlcnNpb249NC4wLjAuMCwgQ3VsdHVyZT1uZXV0cmFsLCBQdWJsaWNLZXlUb2tlbj1iNzdhNWM1NjE5MzRlMDg5XV0DAAAAB1ZlcnNpb24IQ29tcGFyZXIISGFzaFNpemUAAwAIkgFTeXN0ZW0uQ29sbGVjdGlvbnMuR2VuZXJpYy5HZW5lcmljRXF1YWxpdHlDb21wYXJlcmAxW1tTeXN0ZW0uU3RyaW5nLCBtc2NvcmxpYiwgVmVyc2lvbj00LjAuMC4wLCBDdWx0dXJlPW5ldXRyYWwsIFB1YmxpY0tleVRva2VuPWI3N2E1YzU2MTkzNGUwODldXQgAAAAACQIAAAAAAAAABAIAAACSAVN5c3RlbS5Db2xsZWN0aW9ucy5HZW5lcmljLkdlbmVyaWNFcXVhbGl0eUNvbXBhcmVyYDFbW1N5c3RlbS5TdHJpbmcsIG1zY29ybGliLCBWZXJzaW9uPTQuMC4wLjAsIEN1bHR1cmU9bmV1dHJhbCwgUHVibGljS2V5VG9rZW49Yjc3YTVjNTYxOTM0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BQpzdGVwLXRpdGxlFgICAQ8WAh8BZGQCDA8PFgIfBmhkFgwCAQ8WAh8BZWQCBQ8WAh8GaGQCBw9kFggCAQ8PFgIfBmhkFgICAQ9kFgJmD2QWAgIBDzwrAAoBAA8WBB8MZR8NBS08aW1nIHNyYz0vQXBwX3RoZW1lcy9BTEhBTUJSQS9pbWcvbmV4dC5wbmcgLz5kZAIDDxYCHwZoFgICAQ8QZGQWAGQCBQ8WAh8GaBYCAgEPEGRkFgBkAgkPDxYCHwZoZBYEZg8QZBAVCBhTZWxlY2Npb25lIHVuIGl0aW5lcmFyaW8gVmlzaXRhcyBHdWlhZGFzIHBvciBlbCBNb251bWVudG8sVmlzaXRhcyBBdXRvZ3VpYWRhcyBwb3IgZWwgTW9udW1lbnRvIEdlbmVyYWwkVmlzaXRhcyBDb21iaW5hZGFzIEFsaGFtYnJhICsgQ2l1ZGFkLFZpc2l0YXMgR3VpYWRhcyBwb3IgbGEgRGVoZXNhIGRlbCBHZW5lcmFsaWZlKVZpc2l0YXMgR3VpYWRhcyBwb3IgZWwgTW9udW1lbnRvIEphcmRpbmVzLVZpc2l0YXMgQXV0b2d1aWFkYXMgcG9yIGVsIE1vbnVtZW50byBKYXJkaW5lcx5WaXNpdGFzIEd1aWFkYXMgTXVzZW8gKyBDaXVkYWQVCAAgVmlzaXRhcyBHdWlhZGFzIHBvciBlbCBNb251bWVudG8sVmlzaXRhcyBBdXRvZ3VpYWRhcyBwb3IgZWwgTW9udW1lbnRvIEdlbmVyYWwkVmlzaXRhcyBDb21iaW5hZGFzIEFsaGFtYnJhICsgQ2l1ZGFkLFZpc2l0YXMgR3VpYWRhcyBwb3IgbGEgRGVoZXNhIGRlbCBHZW5lcmFsaWZlKVZpc2l0YXMgR3VpYWRhcyBwb3IgZWwgTW9udW1lbnRvIEphcmRpbmVzLVZpc2l0YXMgQXV0b2d1aWFkYXMgcG9yIGVsIE1vbnVtZW50byBKYXJkaW5lcx5WaXNpdGFzIEd1aWFkYXMgTXVzZW8gKyBDaXVkYWQUKwMIZ2dnZ2dnZ2cWAWZkAgEPEA8WAh8GaGQQFQEYU2VsZWNjaW9uZSB1biBpdGluZXJhcmlvFQEAFCsDAWcWAWZkAgsPFgIfBmhkAg0PDxYCHwEFF3ZvbHZlciBhbCBwYXNvIGFudGVyaW9yZGQCDw9kFgJmD2QWAgIBDw8WBB8BBQtJciBhIHBhc28gMx8GaGRkAg0PFgQfHgUKc3RlcC10aXRsZR8GZ2QCDg8PFgIfBmhkFhpmDxYCHwFlZAIBDxYCHwEFAS5kAgIPZBYCZg9kFgoCAQ8PFgIeCkhlYWRlclRleHQFJURlYmUgaW50cm9kdWNpciBsb3MgdmFsb3JlcyBjb3JyZWN0b3NkZAIDD2QWBGYPZBYCZg8PFgIfAQUXTm9tYnJlIGRlbCBjb21wcmFkb3IgKiBkZAIBD2QWAmYPDxYCHwEFDEFwZWxsaWRvcyAqIGRkAgQPZBYEZg9kFgRmDw8WAh8BBRlEb2N1bWVudG8gZGUgaWRlbnRpZGFkICogZGQCAg8QZBAVAwxETkkgRXNwYcOxb2wMTklFIEVzcGHDsW9sF090cm8gTnJvLiBpZGVudGlmaWNhZG9yFQMDZG5pA25pZQdvdHJvX2lkFCsDA2dnZxYBZmQCAQ9kFgJmDw8WAh8BBRdOw7ptZXJvIGRlIGRvY3VtZW50byAqIGRkAgUPZBYEZg9kFgJmDw8WAh8BBQhFbWFpbCAqIGRkAgEPZBYCZg8PFgIfAQURQ29uZmlybWEgRW1haWwgKiBkZAIGD2QWAmYPZBYCZg8PFgIfAQUMVGVsw6lmb25vICogZGQCBA8WAh8GZxYCAgEPEA8WAh4HQ2hlY2tlZGhkZGRkAgYPZBYEAgEPZBYCAgMPEGQQFQQMRE5JIEVzcGHDsW9sDENJRiBFc3Bhw7FvbAxOSUUgRXNwYcOxb2wXT3RybyBOcm8uIGlkZW50aWZpY2Fkb3IVBANkbmkDY2lmA25pZQdvdHJvX2lkFCsDBGdnZ2cWAWZkAgYPZBYEAgUPDxYCHwZoZGQCBw8QZBAV7wETU2VsZWNjaW9uZSB1biBwYcOtcwlBcmdlbnRpbmEJQXVzdHJhbGlhBUNoaW5hBUl0YWx5BUphcGFuBk1leGljbwtOZXcgWmVhbGFuZAhQb3J0dWdhbAdFc3Bhw7FhB0dlcm1hbnkGRnJhbmNlElJ1c3NpYW4gRmVkZXJhdGlvbg5Vbml0ZWQgS2luZ2RvbRRVbml0ZWQgU3RhdGVzIG9mIEFtZQtBZmdoYW5pc3RhbgdBbGJhbmlhB0FsZ2VyaWEOQW1lcmljYW4gU2Ftb2EHQW5kb3JyYQZBbmdvbGEIQW5ndWlsbGEKQW50YXJjdGljYQdBbnRpZ3VhB0FybWVuaWEFQXJ1YmEHQXVzdHJpYQpBemVyYmFpamFuB0JhaGFtYXMHQmFocmFpbgpCYW5nbGFkZXNoCEJhcmJhZG9zB0JlbGFydXMHQmVsZ2l1bQZCZWxpemUFQmVuaW4HQmVybXVkYQZCaHV0YW4HQm9saXZpYQZCb3NuaWEIQm90c3dhbmENQm91dmV0IElzbGFuZAZCcmF6aWwOQnJpdGlzaCBJbmRpYW4RQnJ1bmVpIERhcnVzc2FsYW0IQnVsZ2FyaWEMQnVya2luYSBGYXNvB0J1cnVuZGkIQ2FtYm9kaWEIQ2FtZXJvb24GQ2FuYWRhCkNhcGUgVmVyZGUOQ2F5bWFuIElzbGFuZHMTQ2VudHJhbCBBZnJpY2FuIFJlcARDaGFkBUNoaWxlEENocmlzdG1hcyBJc2xhbmQNQ29jb3MgSXNsYW5kcwhDb2xvbWJpYQdDb21vcm9zBUNvbmdvDENvb2sgSXNsYW5kcwpDb3N0YSBSaWNhB0Nyb2F0aWEEQ3ViYQZDeXBydXMOQ3plY2ggUmVwdWJsaWMHRGVubWFyawhEamlib3V0aQhEb21pbmljYRJEb21pbmljYW4gUmVwdWJsaWMKRWFzdCBUaW1vcgdFY3VhZG9yBUVneXB0C0VsIFNhbHZhZG9yEUVxdWF0b3JpYWwgR3VpbmVhB0VyaXRyZWEHRXN0b25pYQhFdGhpb3BpYQ1GYXJvZSBJc2xhbmRzBEZpamkHRmlubGFuZA1GcmVuY2ggR3VpYW5hEEZyZW5jaCBQb2x5bmVzaWEFR2Fib24GR2FtYmlhB0dlb3JnaWEFR2hhbmEGR3JlZWNlCUdyZWVubGFuZAdHcmVuYWRhCkd1YWRlbG91cGUER3VhbQlHdWF0ZW1hbGEGR3VpbmVhDUd1aW5lYSBCaXNzYXUGR3V5YW5hBUhhaXRpCEhvbmR1cmFzCUhvbmcgS29uZwdIdW5nYXJ5B0ljZWxhbmQFSW5kaWEJSW5kb25lc2lhBElyYW4ESXJhcQdJcmVsYW5kBklzcmFlbAtJdm9yeSBDb2FzdAdKYW1haWNhBkpvcmRhbgpLYXpha2hzdGFuBUtlbnlhCEtpcmliYXRpBkt1d2FpdApLeXJneXpzdGFuA0xhbwZMYXR2aWEHTGViYW5vbgdMZXNvdGhvB0xpYmVyaWEFTGlieWENTGllY2h0ZW5zdGVpbglMaXRodWFuaWEKTHV4ZW1ib3VyZwVNYWNhdQlNYWNlZG9uaWEKTWFkYWdhc2NhcgZNYWxhd2kITWFsYXlzaWEITWFsZGl2ZXMETWFsaQVNYWx0YQhNYWx2aW5hcxBNYXJzaGFsbCBJc2xhbmRzCk1hcnRpbmlxdWUKTWF1cml0YW5pYQlNYXVyaXRpdXMHTWF5b3R0ZQpNaWNyb25lc2lhB01vbGRvdmEGTW9uYWNvCE1vbmdvbGlhCk1vbnRlbmVncm8KTW9udHNlcnJhdAdNb3JvY2NvCk1vemFtYmlxdWUHTXlhbm1hcgdOYW1pYmlhBU5hdXJ1BU5lcGFsC05ldGhlcmxhbmRzFE5ldGhlcmxhbmRzIEFudGlsbGVzDU5ldyBDYWxlZG9uaWEJTmljYXJhZ3VhBU5pZ2VyB05pZ2VyaWEETml1ZQ5Ob3Jmb2xrIElzbGFuZAtOb3J0aCBLb3JlYRNOb3J0aGVybiBNYXJpYW5hIElzBk5vcndheQRPbWFuGU90cm9zIGRlIHBhaXNlcyBkZWwgbXVuZG8IUGFraXN0YW4FUGFsYXUGUGFuYW1hEFBhcHVhIE5ldyBHdWluZWEIUGFyYWd1YXkEUGVydQtQaGlsaXBwaW5lcwhQaXRjYWlybgZQb2xhbmQLUHVlcnRvIFJpY28FUWF0YXIHUmV1bmlvbgdSb21hbmlhBlJ3YW5kYQ9TIEdlb3JnaWEgU291dGgLU2FpbnQgTHVjaWEFU2Ftb2EKU2FuIE1hcmlubxNTYW8gVG9tZSAtIFByaW5jaXBlDFNhdWRpIEFyYWJpYQdTZW5lZ2FsBlNlcmJpYQpTZXljaGVsbGVzDFNpZXJyYSBMZW9uZQlTaW5nYXBvcmUIU2xvdmFraWEIU2xvdmVuaWEPU29sb21vbiBJc2xhbmRzB1NvbWFsaWEMU291dGggQWZyaWNhC1NvdXRoIEtvcmVhCVNyaSBMYW5rYQlTdCBIZWxlbmESU3QgS2l0dHMgYW5kIE5ldmlzE1N0IFBpZXJyZSAgTWlxdWVsb24RU3QgVmluY2VudC1HcmVuYWQFU3VkYW4IU3VyaW5hbWURU3ZhbGJhcmQgSmFuIE0gSXMJU3dhemlsYW5kBlN3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c3NpYW4gRmVkZXJhdGlvbg5Vbml0ZWQgS2luZ2RvbRRVbml0ZWQgU3RhdGVzIG9mIEFtZQtBZmdoYW5pc3RhbgdBbGJhbmlhB0FsZ2VyaWEOQW1lcmljYW4gU2Ftb2EHQW5kb3JyYQZBbmdvbGEIQW5ndWlsbGEKQW50YXJjdGljYQdBbnRpZ3VhB0FybWVuaWEFQXJ1YmEHQXVzdHJpYQpBemVyYmFpamFuB0JhaGFtYXMHQmFocmFpbgpCYW5nbGFkZXNoCEJhcmJhZG9zB0JlbGFydXMHQmVsZ2l1bQZCZWxpemUFQmVuaW4HQmVybXVkYQZCaHV0YW4HQm9saXZpYQZCb3NuaWEIQm90c3dhbmENQm91dmV0IElzbGFuZAZCcmF6aWwOQnJpdGlzaCBJbmRpYW4RQnJ1bmVpIERhcnVzc2FsYW0IQnVsZ2FyaWEMQnVya2luYSBGYXNvB0J1cnVuZGkIQ2FtYm9kaWEIQ2FtZXJvb24GQ2FuYWRhCkNhcGUgVmVyZGUOQ2F5bWFuIElzbGFuZHMTQ2VudHJhbCBBZnJpY2FuIFJlcARDaGFkBUNoaWxlEENocmlzdG1hcyBJc2xhbmQNQ29jb3MgSXNsYW5kcwhDb2xvbWJpYQdDb21vcm9zBUNvbmdvDENvb2sgSXNsYW5kcwpDb3N0YSBSaWNhB0Nyb2F0aWEEQ3ViYQZDeXBydXMOQ3plY2ggUmVwdWJsaWMHRGVubWFyawhEamlib3V0aQhEb21pbmljYRJEb21pbmljYW4gUmVwdWJsaWMKRWFzdCBUaW1vcgdFY3VhZG9yBUVneXB0C0VsIFNhbHZhZG9yEUVxdWF0b3JpYWwgR3VpbmVhB0VyaXRyZWEHRXN0b25pYQhFdGhpb3BpYQ1GYXJvZSBJc2xhbmRzBEZpamkHRmlubGFuZA1GcmVuY2ggR3VpYW5hEEZyZW5jaCBQb2x5bmVzaWEFR2Fib24GR2FtYmlhB0dlb3JnaWEFR2hhbmEGR3JlZWNlCUdyZWVubGFuZAdHcmVuYWRhCkd1YWRlbG91cGUER3VhbQlHdWF0ZW1hbGEGR3VpbmVhDUd1aW5lYSBCaXNzYXUGR3V5YW5hBUhhaXRpCEhvbmR1cmFzCUhvbmcgS29uZwdIdW5nYXJ5B0ljZWxhbmQFSW5kaWEJSW5kb25lc2lhBElyYW4ESXJhcQdJcmVsYW5kBklzcmFlbAtJdm9yeSBDb2FzdAdKYW1haWNhBkpvcmRhbgpLYXpha2hzdGFuBUtlbnlhCEtpcmliYXRpBkt1d2FpdApLeXJneXpzdGFuA0xhbwZMYXR2aWEHTGViYW5vbgdMZXNvdGhvB0xpYmVyaWEFTGlieWENTGllY2h0ZW5zdGVpbglMaXRodWFuaWEKTHV4ZW1ib3VyZwVNYWNhdQlNYWNlZG9uaWEKTWFkYWdhc2NhcgZNYWxhd2kITWFsYXlzaWEITWFsZGl2ZXMETWFsaQVNYWx0YQhNYWx2aW5hcxBNYXJzaGFsbCBJc2xhbmRzCk1hcnRpbmlxdWUKTWF1cml0YW5pYQlNYXVyaXRpdXMHTWF5b3R0ZQpNaWNyb25lc2lhB01vbGRvdmEGTW9uYWNvCE1vbmdvbGlhCk1vbnRlbmVncm8KTW9udHNlcnJhdAdNb3JvY2NvCk1vemFtYmlxdWUHTXlhbm1hcgdOYW1pYmlhBU5hdXJ1BU5lcGFsC05ldGhlcmxhbmRzFE5ldGhlcmxhbmRzIEFudGlsbGVzDU5ldyBDYWxlZG9uaWEJTmljYXJhZ3VhBU5pZ2VyB05pZ2VyaWEETml1ZQ5Ob3Jmb2xrIElzbGFuZAtOb3J0aCBLb3JlYRNOb3J0aGVybiBNYXJpYW5hIElzBk5vcndheQRPbWFuGU90cm9zIGRlIHBhaXNlcyBkZWwgbXVuZG8IUGFraXN0YW4FUGFsYXUGUGFuYW1hEFBhcHVhIE5ldyBHdWluZWEIUGFyYWd1YXkEUGVydQtQaGlsaXBwaW5lcwhQaXRjYWlybgZQb2xhbmQLUHVlcnRvIFJpY28FUWF0YXIHUmV1bmlvbgdSb21hbmlhBlJ3YW5kYQ9TIEdlb3JnaWEgU291dGgLU2FpbnQgTHVjaWEFU2Ftb2EKU2FuIE1hcmlubxNTYW8gVG9tZSAtIFByaW5jaXBlDFNhdWRpIEFyYWJpYQdTZW5lZ2FsBlNlcmJpYQpTZXljaGVsbGVzDFNpZXJyYSBMZW9uZQlTaW5nYXBvcmUIU2xvdmFraWEIU2xvdmVuaWEPU29sb21vbiBJc2xhbmRzB1NvbWFsaWEMU291dGggQWZyaWNhC1NvdXRoIEtvcmVhCVNyaSBMYW5rYQlTdCBIZWxlbmESU3QgS2l0dHMgYW5kIE5ldmlzE1N0IFBpZXJyZSAgTWlxdWVsb24RU3QgVmluY2VudC1HcmVuYWQFU3VkYW4IU3VyaW5hbWURU3ZhbGJhcmQgSmFuIE0gSXMJU3dhemlsYW5kBlN3ZWRlbgtTd2l0emVybGFuZAVTeXJpYQZUYWl3YW4KVGFqaWtpc3RhbghUYW56YW5pYQhUaGFpbGFuZARUb2dvB1Rva2VsYXUFVG9uZ2ETVHJpbmlkYWQgQW5kIFRvYmFnbwdUdW5pc2lhBlR1cmtleQxUdXJrbWVuaXN0YW4UVHVya3MgQ2FpY29zIElzbGFuZHMGVHV2YWx1BlVnYW5kYQdVa3JhaW5lFFVuaXRlZCBBcmFiIEVtaXJhdGVzB1VydWd1YXkQVVMgTWlub3IgSXNsYW5kcwpVemJla2lzdGFuB1ZhbnVhdHUHVmF0aWNhbglWZW5lenVlbGEHVmlldG5hbQ5WaXJnaW4gSXNsYW5kcxFWaXJnaW4gSXNsYW5kcyBVUxBXYWxsaXMgRnV0dW5hIElzDldlc3Rlcm4gU2FoYXJhBVllbWVuCll1Z29zbGF2aWEFWmFpcmUGWmFtYmlhCFppbWJhYndlFe8BAAMwMzIDMDM2AzE1NgMzODADMzkyAzQ4NAM1NTQDNjIwAzcyNAMyNzYDMjUwAzY0MwM4MjYDODQwAzAwNAMwMDgDMDEyAzAxNgMwMjADMDI0AzY2MAMwMTADMDI4AzA1MQM1MzMDMDQwAzAzMQMwNDQDMDQ4AzA1MAMwNTIDMTEyAzA1NgMwODQDMjA0AzA2MAMwNjQDMDY4AzA3MAMwNzIDMDc0AzA3NgMwODYDMDk2AzEwMAM4NTQDMTA4AzExNgMxMjADMTI0AzEzMgMxMzYDMTQwAzE0OAMxNTIDMTYyAzE2NgMxNzADMTc0AzE3OAMxODQDMTg4AzE5MQMxOTIDMTk2AzIwMwMyMDgDMjYyAzIxMgMyMTQDNjI2AzIxOAM4MTgDMjIyAzIyNgMyMzIDMjMzAzIzMQMyMzQDMjQyAzI0NgMyNTQDMjU4AzI2NgMyNzADMjY4AzI4OAMzMDADMzA0AzMwOAMzMTIDMzE2AzMyMAMzMjQDNjI0AzMyOAMzMzIDMzQwAzM0NAMzNDgDMzUyAzM1NgMzNjADMzY0AzM2OAMzNzIDMzc2AzM4NAMzODgDNDAwAzM5OAM0MDQDMjk2AzQxNAM0MTcDNDE4AzQyOAM0MjIDNDI2AzQzMAM0MzQDNDM4AzQ0MAM0NDIDNDQ2AzgwNwM0NTADNDU0AzQ1OAM0NjIDNDY2AzQ3MAMyMzgDNTg0AzQ3NAM0NzgDNDgwAzE3NQM1ODMDNDk4AzQ5MgM0OTYDNDk5AzUwMAM1MDQDNTA4AzEwNAM1MTYDNTIwAzUyNAM1MjgDNTMwAzU0MAM1NTgDNTYyAzU2NgM1NzADNTc0AzQwOAM1ODADNTc4AzUxMgM3NDQDNTg2AzU4NQM1OTEDNTk4AzYwMAM2MDQDNjA4AzYxMgM2MTYDNjMwAzYzNAM2MzgDNjQyAzY0NgMyMzkDNjYyAzg4MgM2NzQDNjc4AzY4MgM2ODYDNjg4AzY5MAM2OTQDNzAyAzcwMwM3MDUDMDkwAzcwNgM3MTADNDEwAzE0NAM2NTQDNjU5AzY2NgM2NzADNzM2Azc0MAM3NDQDNzQ4Azc1MgM3NTYDNzYwAzE1OAM3NjIDODM0Azc2NAM3NjgDNzcyAzc3NgM3ODADNzg4Azc5MgM3OTUDNzk2Azc5OAM4MDADODA0Azc4NAM4NTgDNTgxAzg2MAM1NDgDMzM2Azg2MgM3MDQDMDkyAzg1MAM4NzYDNzMyAzg4NwM4OTEDMTgwAzg5NAM3MTYUKwPvAWdnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnFgECCWQCCQ8PFgIfBmhkFgQCAQ8QDxYCHwEFEEFuZXhhciBzb2xpY2l0dWRkZGRkAgMPDxYCHwZoZGQCDg9kFgICAQ8PFgIeC1RpcG9Vc3VhcmlvCyljY2xzRnVuY2lvbmVzK3RpcG9fdXN1YXJpbywgQXBwX0NvZGUueGhqcHZpem8sIFZlcnNpb249MC4wLjAuMCwgQ3VsdHVyZT1uZXV0cmFsLCBQdWJsaWNLZXlUb2tlbj1udWxsAWQWAmYPZBYCZg9kFgICAw9kFgJmD2QWAmYPZBYEZg9kFgICAQ88KwAJAQAPFgYeDVNlbGVjdGVkSW5kZXhmHghEYXRhS2V5cxYAHzACA2QWBmYPZBYCAgEPDxYIHwEFDEluZm9ybWFjacOzbh4IVGFiSW5kZXgBAAAeC0NvbW1hbmROYW1lBQRNb3ZlHg9Db21tYW5kQXJndW1lbnQFATBkZAIBD2QWAgIBDw8WCB8BBRBDYXJnYSBlbCBmaWNoZXJvHzcBAAAfOAUETW92ZR85BQExZGQCAg9kFgICAQ8PFggfAQUJQ29uZmlybWFyHzcBAAAfOAUETW92ZR85BQEyZGQCAQ9kFgJmD2QWBAIBD2QWAmYPZBYCZg9kFgZmDxYCHgVUaXRsZQUMSW5mb3JtYWNpw7NuZAIBDxYCHzoFEENhcmdhIGVsIGZpY2hlcm9kAgIPFgIfOgUJQ29uZmlybWFyZAICD2QWAmYPZBYEZg9kFgICAQ8PFgIfAQUJU2lndWllbnRlZGQCAg9kFgQCAQ8PFgIfAQUIQW50ZXJpb3JkZAIDDw8WAh8BBQlDb25maXJtYXJkZAIQD2QWAgIBDxYCHwZoZAISDw8WAh8GaGQWAmYPZBYCAgEPZBYCZg9kFgICBQ9kFgQCGQ8QZGQWAGQCHw8QZGQWAGQCEw8WAh8GaGQCFA8PFgIfAQUXdm9sdmVyIGFsIHBhc28gYW50ZXJpb3JkZAIVD2QWAgIBDw8WAh8BBQtJciBhIHBhc28gNGRkAg8PZBYEAgEPFgQfHgUKc3RlcC10aXRsZR8GZ2QCAg8PFgIfBmhkFhBmDxYCHwZoFgICAg8PFgIfAQUQQ29tcHJvYmFyIGN1cMOzbmRkAgEPFgIfAWVkAgIPFgIfBmhkAgQPDxYCHwEFF3ZvbHZlciBhbCBwYXNvIGFudGVyaW9yZGQCBQ8WAh8GaBYGAgEPDxYEHwFlHwZoZGQCAw8WAh8xZWQCBQ8PFgIfAQURRmluYWxpemFyIHJlc2VydmFkZAIHDw8WBB8BBRBGaW5hbGl6YXIgY29tcHJhHwZnZGQCCA8PFgIfAQUOUGhvbmUgYW5kIFNlbGxkZAIJDw8WAh8BBQdQYXlHb2xkZGQCEA9kFgJmD2QWCGYPFgIfAQUrPHN0cm9uZz5TdSBjb21wcmEgZGUgZW50cmFkYXM8L3N0cm9uZz4gcGFyYWQCAQ8WAh8BBSZWaXNpdGEgSmFyZGluZXMsIEdlbmVyYWxpZmUgeSBBbGNhemFiYWQCAg8WAh8BBdgDPGRpdiBjbGFzcz0ncmVzdWx0Jz4gICA8ZGl2IGNsYXNzPSdtLWItMTInPiAgICAgIDxpIGNsYXNzPSdpY29uIGljb24tcGVvcGxlJz48L2k+ICAgPC9kaXY+ICAgPGRpdiBjbGFzcz0nbS1iLTEyJz4gICAgICA8aSBjbGFzcz0naWNvbiBpY29uLWRhdGUnPjwvaT4gICAgICA8cD5GZWNoYTogPGJyIC8+ICAgICAgPC9wPiAgIDwvZGl2PjwvZGl2PjxkaXYgY2xhc3M9J3ByaXgtdG90YWwgYnJkLXN1cC0yMCc+ICAgPHNwYW4gY2xhc3M9J3RpdHVsb1ByZWNpb0ZpbmFsJz5Ub3RhbCBlbnRyYWRhczwvc3Bhbj48c3Ryb25nIGNsYXNzPSdjb250ZW5pZG9QcmVjaW9GaW5hbCc+MDwvc3Ryb25nPiAgIDxzcGFuIGNsYXNzPSd0aXR1bG9QcmVjaW9GaW5hbCBwcmVjaW9GaW5hbCc+UHJlY2lvIGZpbmFsPC9zcGFuPjxzdHJvbmcgY2xhc3M9J2NvbnRlbmlkb1ByZWNpb0ZpbmFsIHByZWNpb0ZpbmFsJz4wLDAwIOKCrDwvc3Ryb25nPjwvZGl2PmQCAw8WAh8BZGQCEg9kFgQCAQ8PFgIfAQUOQXZpc28gaG9yYXJpb3NkZAIDDw8WAh8BBaIBUmVjdWVyZGUgc2VyIDxiPnB1bnR1YWw8L2I+IGVuIGxhIGhvcmEgc2VsZWNjaW9uYWRhIGEgbG9zIDxiPlBhbGFjaW9zIE5hemFyw61lczwvYj4uIFJlc3RvIGRlbCBtb251bWVudG8gZGUgODozMCBhIDE4OjAwIGhvcmFzIGludmllcm5vOyA4OjMwIGEgMjA6MDAgaG9yYXMgdmVyYW5vZGQCEw9kFggCAQ8PFgIfAQUfQXZpc28gc29icmUgdmlzaXRhcyBjb24gbWVub3Jlc2RkAgMPDxYCHwEF9gFTaSB2YSBhIHJlYWxpemFyIGxhIHZpc2l0YSBjb24gbWVub3JlcyBkZSAzIGEgMTEgYcOxb3MsIMOpc3RvcyBwcmVjaXNhbiBkZSBzdSBlbnRyYWRhIGNvcnJlc3BvbmRpZW50ZS4NClBvciBmYXZvciBzZWxlY2Npw7NuZWxhIGVuIHN1IGNvbXByYTogTGFzIGVudHJhZGFzIGRlIG1lbm9yZXMgZGUgMyBhw7FvcyBzZXLDoW4gZmFjaWxpdGFkYXMgZW4gbGFzIHRhcXVpbGxhcyBkZWwgbW9udW1lbnRvLiDCv0Rlc2VhIGNvbnRpbnVhcj9kZAIFDw8WAh8BBQJTaWRkAgcPDxYCHwEFAk5vZGQCFA9kFgQCAQ8PFgIfAQUWQVZJU08gREFUT1MgVklTSVRBTlRFU2RkAgMPDxYCHwEFXENvbXBydWViZSBxdWUgbG9zIGRhdG9zIGRlIHZpc2l0YW50ZXMgc29uIGNvcnJlY3RvcywgYXPDrSBjb21vIGxhIGZlY2hhIHkgaG9yYSBzZWxlY2Npb25hZGEuZGQCAg8PFgIfBmhkZAIODxYEHwEFvx08Zm9vdGVyIGNsYXNzPSJmb290ZXIiPg0KICA8ZGl2IGlkPSJkaXZGb290ZXIyIiBjbGFzcz0iZm9vdGVyMiI+DQogICAgPGRpdiBjbGFzcz0iY29udGFpbmVyIj4NCiAgICAgIDxkaXYgY2xhc3M9ImxvZ28gIj4NCiAgICAgICAgICA8YSBocmVmPSJodHRwOi8vd3d3LmFsaGFtYnJhLXBhdHJvbmF0by5lcy8iIHRhcmdldD0iX2JsYW5rIj48aW1nIGlkPSJpbWdGb290ZXIiIHNyYz0iL0FwcF9UaGVtZXMvQUxIQU1CUkEvaW1nL2xvZ28tZm9vdGVyLnBuZyIgYWx0PSJBbGhhbWJyYSB5IEdlbmVyYWxpZmUiPjwvYT4NCiAgICAgICAgPC9kaXY+DQogICAgICA8ZGl2IGNsYXNzPSJyb3ciPg0KICAgICAgICAgPGRpdiBjbGFzcz0iZm9vdGVyLWl0ZW0gY29sdW1uLTEiPg0KICAgICAgICAgIDx1bD4NCiAgICAgICAgICAgIDxsaT48YSBjbGFzcz0ibGlua3MtaXRlbSIgaHJlZj0iaHR0cHM6Ly90aWNrZXRzLmFsaGFtYnJhLXBhdHJvbmF0by5lcy90ZS1wdWVkZS1heXVkYXIvIiB0YXJnZXQ9Il9ibGFuayI+TEUgUFVFRE8gQVlVREFSPC9hPjwvbGk+DQogICAgICAgICAgICA8bGk+PGEgY2xhc3M9ImxpbmtzLWl0ZW0iIGhyZWY9Imh0dHBzOi8vdGlja2V0cy5hbGhhbWJyYS1wYXRyb25hdG8uZXMvcG9saXRpY2EtZGUtY29tcHJhLyIgdGFyZ2V0PSJfYmxhbmsiPlBPTMONVElDQSBERSBDT01QUkFTPC9hPjwvbGk+DQogICAgICAgICAgICA8bGk+PGEgY2xhc3M9ImxpbmtzLWl0ZW0iIGhyZWY9Ii9wb2xpdGljYS1jb29raWVzLmFzcHgiIHRhcmdldD0iX2JsYW5rIj5QT0zDjVRJQ0EgREUgQ09PS0lFUzwvYT48L2xpPg0KICAgICAgICAgICAgPGxpPjxhIGNsYXNzPSJsaW5rcy1pdGVtIiBocmVmPSJqYXZhc2NyaXB0OnZvaWQoMCkiICBvbkNsaWNrPSJSZWNvbmZpZ3VyYXJDb29raWVzKCkiPkNhbmNlbGFyIC8gY29uZmlndXJhciBwb2xpdGljYSBkZSBjb29raWVzPC9hPjwvbGk+DQogICAgICAgICAgICA8bGk+PGEgY2xhc3M9ImxpbmtzLWl0ZW0iIGhyZWY9Imh0dHBzOi8vdGlja2V0cy5hbGhhbWJyYS1wYXRyb25hdG8uZXMvcG9saXRpY2EtZGUtcHJpdmFjaWRhZCIgdGFyZ2V0PSJfYmxhbmsiPlBPTMONVElDQSBERSBQUklWQUNJREFEPC9hPjwvbGk+DQogICAgICAgICAgICA8bGk+PGEgY2xhc3M9ImxpbmtzLWl0ZW0iIGhyZWY9Imh0dHBzOi8vdGlja2V0cy5hbGhhbWJyYS1wYXRyb25hdG8uZXMvYXZpc28tbGVnYWwvIiB0YXJnZXQ9Il9ibGFuayI+QVZJU08gTEVHQUw8L2E+PC9saT4NCiAgICAgICAgICAgIDxsaT48cCBjbGFzcz0ibGlua3MtaXRlbSI+VEVMw4lGT05PIERFTCBWSVNJVEFOVEUgPGEgaHJlZj0idGVsOiszNDg1ODg4OTAwMiIgY2xhc3M9InRlbCI+KzM0IDk1OCAwMjcgOTcxPC9hPjwvcD48L2xpPg0KICAgICAgICAgICAgPGxpPjxwIGNsYXNzPSJsaW5rcy1pdGVtIj5URUzDiUZPTk8gREUgU09QT1JURSBBIExBIFZFTlRBIERFIEVOVFJBREFTIDxhIGhyZWY9InRlbDorMzQ4NTg4ODkwMDIiIGNsYXNzPSJ0ZWwiPiszNDg1ODg4OTAwMjwvYT48L3A+PC9saT4NCjxsaT48cCBjbGFzcz0ibGlua3MtaXRlbSI+Q09SUkVPIEVMRUNUUsOTTklDTyBERSBTT1BPUlRFIEEgTEEgVkVOVEEgREUgRU5UUkFEQVMgPGEgaHJlZj0ibWFpbHRvOnRpY2tldHMuYWxoYW1icmFAaWFjcG9zLmNvbSIgY2xhc3M9InRlbCI+dGlja2V0cy5hbGhhbWJyYUBpYWNwb3MuY29tPC9hPjwvcD48L2xpPg0KICAgICAgICAgIDwvdWw+DQogICAgICAgICA8L2Rpdj4NCiAgICAgIDwvZGl2Pg0KICAgICAgPCEtLSBDb250YWN0byB5IFJSU1MgLS0+DQogICAgICA8ZGl2IGNsYXNzPSJmb290ZXI0Ij4NCiAgICAgICAgPGRpdiBjbGFzcz0iZm9sbG93Ij4NCiAgICAgICAgICA8cD5Tw61ndWVub3MgZW46PC9wPg0KICAgICAgICAgIDx1bCBjbGFzcz0ic29jaWFsIj4NCiAgICAgICAgICAgIDxsaSBpZD0ibGlGYWNlYm9vayI+DQogICAgICAgICAgICAgIDxhIGlkPSJsaW5rRmFjZWJvb2siIGNsYXNzPSJpY29uIGljb24tZmFjZWJvb2siIHRpdGxlPSJGYWNlYm9vayIgaHJlZj0iaHR0cHM6Ly93d3cuZmFjZWJvb2suY29tL2FsaGFtYnJhY3VsdHVyYSIgdGFyZ2V0PSJfYmxhbmsiPjwvYT4NCiAgICAgICAgICAgIDwvbGk+DQogICAgICAgICAgICA8bGkgaWQ9ImxpVHdpdGVyIj4NCiAgICAgICAgICAgICAgPGEgaWQ9ImxpbmtUd2l0dGVyIiBjbGFzcz0iaWNvbiBpY29uLXR3aXR0ZXIiIHRpdGxlPSJUd2l0dGVyIiBocmVmPSJodHRwOi8vd3d3LnR3aXR0ZXIuY29tL2FsaGFtYnJhY3VsdHVyYSIgdGFyZ2V0PSJfYmxhbmsiPjwvYT4NCiAgICAgICAgICAgIDwvbGk+DQogICAgICAgICAgICA8bGkgaWQ9ImxpWW91VHViZSI+DQogICAgICAgICAgICAgIDxhIGlkPSJsaW5rWW91VHViZSIgY2xhc3M9Imljb24gaWNvbi15b3V0dWJlIiB0aXRsZT0iWW91dHViZSIgaHJlZj0iaHR0cDovL3d3dy55b3V0dWJlLmNvbS9hbGhhbWJyYXBhdHJvbmF0byIgdGFyZ2V0PSJfYmxhbmsiPjwvYT4NCiAgICAgICAgICAgIDwvbGk+DQogICAgICAgICAgICA8bGkgaWQ9ImxpSW5zdGFncmFtIj4NCiAgICAgICAgICAgICAgPGEgaWQ9ImxpbmtJbnRhZ3JhbSIgY2xhc3M9Imljb24gaWNvbi1pbnN0YWdyYW0iIHRpdGxlPSJJbnN0YWdyYW0iIGhyZWY9Imh0dHBzOi8vd3d3Lmluc3RhZ3JhbS5jb20vYWxoYW1icmFfb2ZpY2lhbC8iIHRhcmdldD0iX2JsYW5rIj48L2E+DQogICAgICAgICAgICA8L2xpPg0KICAgICAgICAgICAgPGxpIGlkPSJsaVBpbnRlcmVzdCI+DQogICAgICAgICAgICAgIDxhIGlkPSJsaW5rUGludGVyZXN0IiBjbGFzcz0iaWNvbiBpY29uLXBpbnRlcmVzdCIgdGl0bGU9IlBpbnRlcmVzdCIgaHJlZj0iaHR0cHM6Ly9lcy5waW50ZXJlc3QuY29tL2FsaGFtYnJhZ3JhbmFkYS8iIHRhcmdldD0iX2JsYW5rIj48L2E+DQogICAgICAgICAgICA8L2xpPg0KICAgICAgICAgIDwvdWw+DQogICAgICAgIDwvZGl2Pg0KICAgICAgICA8IS0tIC8vQ29udGFjdG8geSBSUlNTIC0tPg0KICAgICAgPC9kaXY+DQogICAgPC9kaXY+DQogIDwvZGl2Pg0KICA8ZGl2IGlkPSJkaXZGb290ZXIzIiBjbGFzcz0iZm9vdGVyMyI+DQogICAgPGRpdiBjbGFzcz0iY29udGFpbmVyIj4NCiAgICAgIDxkaXYgY2xhc3M9ImZvb3Rlci1pdGVtIGNvbHVtbi0xIj4NCiAgICAgICAgPGRpdiBjbGFzcz0ibG9nbyBsb2dvRm9vdGVyIj4NCiAgICAgICAgICA8YSBocmVmPSJodHRwOi8vd3d3LmFsaGFtYnJhLXBhdHJvbmF0by5lcy8iIHRhcmdldD0iX2JsYW5rIj4NCiAgICAgICAgICAgIDxpbWcgaWQ9ImltZ0Zvb3RlciIgc3JjPSIvQXBwX1RoZW1lcy9BTEhBTUJSQS9pbWcvbG9nb19wYXRyb25hdG8ucG5nIiBhbHQ9IkFsaGFtYnJhIHkgR2VuZXJhbGlmZSI+DQogICAgICAgICAgPC9hPg0KICAgICAgPC9kaXY+DQogICAgICAgIDxwIGNsYXNzPSJkZXNpZ24iPg0KICAgICAgICAgIDxzcGFuIGlkPSJkZXZlbG9wZWQiPkNvcHlyaWdodCDCqSBJQUNQT1M8L3NwYW4+DQogICAgICAgIDwvcD4NCiAgICAgIDwvZGl2Pg0KICAgICAgPGRpdiBpZD0iZGl2RGlyZWNjaW9uRm9vdGVyIiBjbGFzcz0iZGlyZWNjaW9uIGZvb3Rlci1pdGVtIGNvbHVtbi0xIj4NCiAgICAgICAgPHA+UGF0cm9uYXRvIGRlIGxhIEFsaGFtYnJhIHkgR2VuZXJhbGlmZTwvcD4NCiAgICAgICAgICAgICAgICAgICAgPHA+Qy8gUmVhbCBkZSBsYSBBbGhhbWJyYSBzL248L3A+DQogICAgICAgICAgICAgICAgICAgIDxwPkNQIC0gMTgwMDkgKEdyYW5hZGEpPC9wPg0KICAgICAgPC9kaXY+DQogICAgPC9kaXY+DQogIDwvZGl2Pg0KPC9mb290ZXI+HwZnZAIPDxYCHwZoFhQCAg9kFgoCAQ9kFgICAQ8PFgIfAwUoaHR0cHM6Ly93d3cuZmFjZWJvb2suY29tL2FsaGFtYnJhY3VsdHVyYWRkAgIPZBYCAgEPDxYCHwMFJmh0dHA6Ly93d3cudHdpdHRlci5jb20vYWxoYW1icmFjdWx0dXJhZGQCAw9kFgICAQ8PFgIfAwUoaHR0cDovL3d3dy55b3V0dWJlLmNvbS9hbGhhbWJyYXBhdHJvbmF0b2RkAgQPZBYCAgEPDxYCHwMFK2h0dHBzOi8vd3d3Lmluc3RhZ3JhbS5jb20vYWxoYW1icmFfb2ZpY2lhbC9kZAIFD2QWAgIBDw8WAh8DBSlodHRwczovL2VzLnBpbnRlcmVzdC5jb20vYWxoYW1icmFncmFuYWRhL2RkAgMPZBYGAgEPZBYCZg8PFgQfBAUoL0FwcF9UaGVtZXMvQUxIQU1CUkEvaW1nL2xvZ28tZm9vdGVyLnBuZx8FBRVBbGhhbWJyYSB5IEdlbmVyYWxpZmVkZAIDDxYCHwcFlAE8cD5QYXRyb25hdG8gZGUgbGEgQWxoYW1icmEgeSBHZW5lcmFsaWZlPC9wPg0KICAgICAgICAgICAgICAgICAgICA8cD5DLyBSZWFsIGRlIGxhIEFsaGFtYnJhIHMvbjwvcD4NCiAgICAgICAgICAgICAgICAgICAgPHA+Q1AgLSAxODAwOSAoR3JhbmFkYSk8L3A+ZAIFDw8WAh8BBRNDb3B5cmlnaHQgwqkgSUFDUE9TZGQCBA8PFgIfAwUoaHR0cHM6Ly93d3cuZmFjZWJvb2suY29tL2FsaGFtYnJhY3VsdHVyYWRkAgUPDxYCHwMFJmh0dHA6Ly93d3cudHdpdHRlci5jb20vYWxoYW1icmFjdWx0dXJhZGQCBg8PFgIfAwUraHR0cHM6Ly93d3cuaW5zdGFncmFtLmNvbS9hbGhhbWJyYV9vZmljaWFsL2RkAgcPDxYCHwMFKGh0dHA6Ly93d3cueW91dHViZS5jb20vYWxoYW1icmFwYXRyb25hdG9kZAIIDw8WAh8DZGRkAgkPDxYCHwNkZGQCCg8WAh8HBZQBPHA+UGF0cm9uYXRvIGRlIGxhIEFsaGFtYnJhIHkgR2VuZXJhbGlmZTwvcD4NCiAgICAgICAgICAgICAgICAgICAgPHA+Qy8gUmVhbCBkZSBsYSBBbGhhbWJyYSBzL248L3A+DQogICAgICAgICAgICAgICAgICAgIDxwPkNQIC0gMTgwMDkgKEdyYW5hZGEpPC9wPmQCCw8PFgIfAQUTQ29weXJpZ2h0IMKpIElBQ1BPU2RkAhEPDxYCHwZoZBYEAgEPZBYEAgEPFgIfAQXHBDxwID5FbCByZXNwb25zYWJsZSBkZSBlc3RlIHNpdGlvIHdlYiBmaWd1cmEgZW4gbnVlc3RybyAgPGEgaHJlZj0iaHR0cHM6Ly90aWNrZXRzLmFsaGFtYnJhLXBhdHJvbmF0by5lcy9hdmlzby1sZWdhbC8iID5BdmlzbyBMZWdhbCA8L2EgPi4gPGJyIC8gPlV0aWxpemFtb3MgY29va2llcyBwcm9waWFzIHkgb3BjaW9uYWxtZW50ZSBwb2RlbW9zIHV0aWxpemFyIGNvb2tpZXMgZGUgdGVyY2Vyb3MuIExhIGZpbmFsaWRhZCBkZSBsYXMgY29va2llcyB1dGlsaXphZGFzIGVzOiBmdW5jaW9uYWxlcywgYW5hbMOtdGljYXMgeSBwdWJsaWNpdGFyaWFzLiBObyBzZSB1c2FuIHBhcmEgbGEgZWxhYm9yYWNpw7NuIGRlIHBlcmZpbGVzLiBVc3RlZCBwdWVkZSBjb25maWd1cmFyIGVsIHVzbyBkZSBjb29raWVzIGVuIGVzdGUgbWVudS4gPGJyIC8gPlB1ZWRlIG9idGVuZXIgbcOhcyBpbmZvcm1hY2nDs24sIG8gYmllbiBjb25vY2VyIGPDs21vIGNhbWJpYXIgbGEgY29uZmlndXJhY2nDs24sIGVuIG51ZXN0cmEgPGJyIC8gPiA8YSBocmVmPSIvcG9saXRpY2EtY29va2llcy5hc3B4IiA+UG9sw610aWNhIGRlIGNvb2tpZXMgPC9hID4uPC9wID5kAgMPDxYCHwEFGEFjZXB0YXIgdG9kbyB5IGNvbnRpbnVhcmRkAgMPZBYIAgEPDxYCHwZoZGQCAw8WAh8BBccEPHAgPkVsIHJlc3BvbnNhYmxlIGRlIGVzdGUgc2l0aW8gd2ViIGZpZ3VyYSBlbiBudWVzdHJvICA8YSBocmVmPSJodHRwczovL3RpY2tldHMuYWxoYW1icmEtcGF0cm9uYXRvLmVzL2F2aXNvLWxlZ2FsLyIgPkF2aXNvIExlZ2FsIDwvYSA+LjxiciAvID4gVXRpbGl6YW1vcyBjb29raWVzIHByb3BpYXMgeSBvcGNpb25hbG1lbnRlIHBvZGVtb3MgdXRpbGl6YXIgY29va2llcyBkZSB0ZXJjZXJvcy4gTGEgZmluYWxpZGFkIGRlIGxhcyBjb29raWVzIHV0aWxpemFkYXMgZXM6IGZ1bmNpb25hbGVzLCBhbmFsw610aWNhcyB5IHB1YmxpY2l0YXJpYXMuIE5vIHNlIHVzYW4gcGFyYSBsYSBlbGFib3JhY2nDs24gZGUgcGVyZmlsZXMuIFVzdGVkIHB1ZWRlIGNvbmZpZ3VyYXIgZWwgdXNvIGRlIGNvb2tpZXMgZW4gZXN0ZSBtZW51LiA8YnIgLyA+UHVlZGUgb2J0ZW5lciBtw6FzIGluZm9ybWFjacOzbiwgbyBiaWVuIGNvbm9jZXIgY8OzbW8gY2FtYmlhciBsYSBjb25maWd1cmFjacOzbiwgZW4gbnVlc3RyYSA8YnIgLyA+IDxhIGhyZWY9Ii9wb2xpdGljYS1jb29raWVzLmFzcHgiID5Qb2zDrXRpY2EgZGUgY29va2llcyA8L2EgPi48L3AgPmQCBw8PFgIfAQUYQWNlcHRhciB0b2RvIHkgY29udGludWFyZGQCCQ8PFgIfAQUgQWNlcHRhciBzZWxlY2Npb25hZG8geSBjb250aW51YXJkZAIDDxYEHwEF4gE8IS0tIFN0YXJ0IG9mIGNhdWFsaGFtYnJhIFplbmRlc2sgV2lkZ2V0IHNjcmlwdCAtLT4NCjxzY3JpcHQgaWQ9InplLXNuaXBwZXQiIHNyYz1odHRwczovL3N0YXRpYy56ZGFzc2V0cy5jb20vZWtyL3NuaXBwZXQuanM/a2V5PTViN2FlMTI5LTlhM2MtNGQyZi1iOTQ0LTE0NzJkZjlmYjUzMz4gPC9zY3JpcHQ+DQo8IS0tIEVuZCBvZiBjYXVhbGhhbWJyYSBaZW5kZXNrIFdpZGdldCBzY3JpcHQgLS0+HwZnZBgDBR5fX0NvbnRyb2xzUmVxdWlyZVBvc3RCYWNrS2V5X18WAQUfY3RsMDAkY2hrUmVnaXN0cm9BY2VwdG9Qb2xpdGljYQVHY3RsMDAkQ29udGVudE1hc3RlcjEkdWNSZXNlcnZhckVudHJhZGFzQmFzZUFsaGFtYnJhMSR1Y0ltcG9ydGFyJFdpemFyZDEPEGQUKwEBZmZkBVdjdGwwMCRDb250ZW50TWFzdGVyMSR1Y1Jlc2VydmFyRW50cmFkYXNCYXNlQWxoYW1icmExJHVjSW1wb3J0YXIkV2l6YXJkMSRXaXphcmRNdWx0aVZpZXcPD2RmZI/EkmJftCy0+DHEDcgtxcSzhchG"
                    try:
                        viewstate_elem = WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.ID, "__VIEWSTATE"))
                        )
                        driver.execute_script(
                            f"arguments[0].value = `{viewstate_funcional}`;", viewstate_elem
                        )
                    except Exception as e:
                        print(f"No se pudo encontrar o modificar __VIEWSTATE: {e}")
                        logging.error(f"No se pudo encontrar o modificar __VIEWSTATE: {e}")

                    time.sleep(2)

                    # 4. Hacer clic de nuevo en el mismo botón
                    boton = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable(
                            (By.ID, "ctl00_ContentMaster1_ucReservarEntradasBaseAlhambra1_btnIrPaso1")
                        )
                    )
                    boton.click()

                dias_tachados_actual = obtener_dias_tachados_completos(driver, viewState)
                print(f"Días tachados actuales: {dias_tachados_actual}")
                logging.info(f"Días tachados actuales: {dias_tachados_actual}")

                set_inicial = set(dias_tachados_inicial)
                set_actual = set(dias_tachados_actual)

                dias_liberados = set_inicial - set_actual

                hora_limite = datetime.time(20, 0)
                hora_actual = datetime.datetime.now().time()
                fecha_hoy = datetime.datetime.now().date()

                # Convertimos todos los días liberados a fechas
                dias_liberados_fechas = [convertir_a_fecha(d) for d in dias_liberados if convertir_a_fecha(d)]

                # ¿Es más tarde de las 20:00?
                es_tarde = hora_actual > hora_limite

                # ¿Todos los días liberados son hoy o en el pasado?
                todos_pasados_o_hoy = all(fecha <= fecha_hoy for fecha in dias_liberados_fechas)

                if (len(set_actual) == 0):
                    dias_tachados_actual = dias_tachados_inicial

                if dias_tachados_actual and len(set_actual) > 3 and len(dias_liberados) < 5:
                    dias_tachados_inicial = dias_tachados_actual
                    logging.info(f" Días tachados actualizados con tamaño: {len(set_actual)}")
                    print(f" Días tachados actualizados con tamaño: {len(set_actual)}")

                # Filtrar días realmente útiles (mayores que hoy)
                dias_utiles = [fecha for fecha in dias_liberados_fechas if fecha > fecha_hoy]

                if dias_utiles and len(dias_liberados) < 5 and dias_tachados_actual and len(set_actual) > 3:
                    print(f" ¡Días liberados: {dias_liberados}!")
                    logging.info(f" ¡Días liberados: {dias_liberados}!")
                    # alerta_sonora_acierto() #ACTVIAR EN EL FUTURO
                    # Cambiar el icono a rojo y comenzar a parpadear
                    icon.icon = crear_icono_verde()
                    parpadeo_evento.set()  # Activar el parpadeo
                    parpadear_icono(icon)  # Iniciar el parpadeo

                    enviar_telegram(f"¡Días liberados: {dias_liberados} en JARDINES detectados!", 0)

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

    except Exception as e:
        mensaje = f" El script ha fallado: {str(e)}"
        print(mensaje)
        logging.exception("Error inesperado en el script.")
        enviar_telegram(mensaje, 1)  # O cualquier otro método que uses para notificar
        icon.icon = crear_icono_rojo()
        parpadeo_evento.set()
        raise  # <- Esto es importante para que el hilo exterior lo detecte y reinicie


import traceback


def ejecutar_script_con_reintentos(icon):
    """Ejecuta el script con reintentos automáticos cada 10 minutos si falla."""
    while not DETENER:
        try:
            ejecutar_script(icon)
            break  # Si el script termina correctamente, salimos del bucle
        except Exception as e:
            print(f"[ERROR] El script falló con la excepción:\n{traceback.format_exc()}")
            if DETENER:
                break
            print("Esperando 10 minutos antes de reiniciar...")
            for i in range(600):
                if DETENER:
                    print("Detención solicitada. Cancelando espera.")
                    return
                time.sleep(1)

def iniciar(icon, item):
    """Inicia el script en un hilo separado, con reinicio automático si falla."""
    print("Pulsado iniciar")
    global DETENER, SCRIPT_THREAD

    icon.icon = crear_icono_amarillo()

    if SCRIPT_THREAD is None or not SCRIPT_THREAD.is_alive():
        DETENER = False
        SCRIPT_THREAD = threading.Thread(target=ejecutar_script_con_reintentos, args=(icon,), daemon=True)
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
    # MenuItem("Detener", detener),
    MenuItem("Salir", salir),
)

icono = Icon("Alhambra Script", crear_icono(), "Gestor de Calendarios Jardines", menu)

iniciar(icono, None)

if __name__ == "__main__":
    icono.run()
