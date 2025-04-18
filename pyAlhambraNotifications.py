import threading
import tkinter as tk
from tkinter import messagebox
import datetime
import calendar
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


def enviar_telegram(mensaje, onlyMiguel=0):
    url = "https://api.telegram.org/bot7908020608:AAEGRux_wQ8tlKxPoMEGLR5vMtG1X3LW2WY/sendMessage"
    chat_belen = [8120620954, 7225762073]  # Belén (dos IDs diferentes)
    chat_miguel = [780778418]  # Miguel

    # chat_ids = chat_belen + chat_miguel

    if onlyMiguel:
        chat_ids = chat_miguel
    else:
        chat_ids = chat_belen

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


def convertir_a_fecha(fecha_str):
    try:
        return datetime.datetime.strptime(fecha_str, "%B-%d").replace(year=datetime.datetime.now().year).date()
    except ValueError:
        return None


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


def ejecutar_script(icon):
    try:

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

                # Esperar a que desaparezca la capa de carga si existe
                try:
                    WebDriverWait(driver, 5).until(
                        EC.invisibility_of_element_located((By.ID, "divCargando"))
                    )
                except:
                    print("La capa de carga no desapareció, se continúa de todas formas.")

                dias_tachados_inicial = obtener_dias_tachados_completos(driver, 0)

                # time.sleep(TIEMPO)

                if dias_tachados_inicial:
                    break
                # alerta_sonora_error()
                intentos += 1
                print(f"Intento {intentos}: No se encontraron días tachados. Accediendo a viewState")
                # print(driver.page_source)  # Para ver si hay mensajes ocultos o errores

                # 3. Reemplazar manualmente el valor de __VIEWSTATE con el que tú sabes que funciona
                viewstate_funcional = "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OTUyZxAFBDE5NTMFBDE5NTNnEAUEMTk1NAUEMTk1NGcQBQQxOTU1BQQxOTU1ZxAFBDE5NTYFBDE5NTZnEAUEMTk1NwUEMTk1N2cQBQQxOTU4BQQxOTU4ZxAFBDE5NTkFBDE5NTlnEAUEMTk2MAUEMTk2MGcQBQQxOTYxBQQxOTYxZxAFBDE5NjIFBDE5NjJnEAUEMTk2MwUEMTk2M2cQBQQxOTY0BQQxOTY0ZxAFBDE5NjUFBDE5NjVnEAUEMTk2NgUEMTk2NmcQBQQxOTY3BQQxOTY3ZxAFBDE5NjgFBDE5NjhnEAUEMTk2OQUEMTk2OWcQBQQxOTcwBQQxOTcwZxAFBDE5NzEFBDE5NzFnEAUEMTk3MgUEMTk3MmcQBQQxOTczBQQxOTczZxAFBDE5NzQFBDE5NzRnEAUEMTk3NQUEMTk3NWcQBQQxOTc2BQQxOTc2ZxAFBDE5NzcFBDE5NzdnEAUEMTk3OAUEMTk3OGcQBQQxOTc5BQQxOTc5ZxAFBDE5ODAFBDE5ODBnEAUEMTk4MQUEMTk4MWcQBQQxOTgyBQQxOTgyZxAFBDE5ODMFBDE5ODNnEAUEMTk4NAUEMTk4NGcQBQQxOTg1BQQxOTg1ZxAFBDE5ODYFBDE5ODZnEAUEMTk4NwUEMTk4N2cQBQQxOTg4BQQxOTg4ZxAFBDE5ODkFBDE5ODlnEAUEMTk5MAUEMTk5MGcQBQQxOTkxBQQxOTkxZxAFBDE5OTIFBDE5OTJnEAUEMTk5MwUEMTk5M2cQBQQxOTk0BQQxOTk0ZxAFBDE5OTUFBDE5OTVnEAUEMTk5NgUEMTk5NmcQBQQxOTk3BQQxOTk3ZxAFBDE5OTgFBDE5OThnEAUEMTk5OQUEMTk5OWcQBQQyMDAwBQQyMDAwZxAFBDIwMDEFBDIwMDFnEAUEMjAwMgUEMjAwMmcQBQQyMDAzBQQyMDAzZxAFBDIwMDQFBDIwMDRnEAUEMjAwNQUEMjAwNWcQBQQyMDA2BQQyMDA2ZxAFBDIwMDcFBDIwMDdnEAUEMjAwOAUEMjAwOGcQBQQyMDA5BQQyMDA5ZxAFBDIwMTAFBDIwMTBnEAUEMjAxMQUEMjAxMWcQBQQyMDEyBQQyMDEyZxAFBDIwMTMFBDIwMTNnEAUEMjAxNAUEMjAxNGcQBQQyMDE1BQQyMDE1ZxAFBDIwMTYFBDIwMTZnEAUEMjAxNwUEMjAxN2cQBQQyMDE4BQQyMDE4ZxAFBDIwMTkFBDIwMTlnEAUEMjAyMAUEMjAyMGcQBQQyMDIxBQQyMDIxZxAFBDIwMjIFBDIwMjJnEAUEMjAyMwUEMjAyM2cQBQQyMDI0BQQyMDI0ZxAFBDIwMjUFBDIwMjVnFgFmZAILDxYCHwZoFgICAQ8WAh8HZGQCDA9kFgICAQ8WAh8HBQVFbWFpbGQCDQ9kFgICAQ8WAh8HBQ5Db25maXJtYSBFbWFpbGQCDg9kFgICAQ8WAh8HBQtDb250cmFzZcOxYWQCDw9kFgICAQ8WAh8HBRNSZXBldGlyIENvbnRyYXNlw7FhZAIQDxYCHwZoFgICAQ8WAh8HZWQCEQ8WAh8GaBYCAgEPFgIfB2VkAhIPFgIfBmgWAgIBDxYCHwdlZAITDxYCHwZoFgYCAQ8WAh8HZWQCAw8PFgQeCENzc0NsYXNzBRJpbnB1dC10ZXh0IG9jdWx0YXIeBF8hU0ICAmRkAgUPEA8WBB8JZR8KAgJkEBU1FFNlbGVjY2lvbmUgcHJvdmluY2lhCEFsYmFjZXRlCEFsaWNhbnRlCEFsbWVyw61hBsOBbGF2YQhBc3R1cmlhcwbDgXZpbGEHQmFkYWpveg1CYWxlYXJzIElsbGVzCUJhcmNlbG9uYQdCaXprYWlhBkJ1cmdvcwhDw6FjZXJlcwZDw6FkaXoJQ2FudGFicmlhCkNhc3RlbGzDs24LQ2l1ZGFkIFJlYWwIQ8OzcmRvYmEJQ29ydcOxYSBBBkN1ZW5jYQhHaXB1emtvYQZHaXJvbmEHR3JhbmFkYQtHdWFkYWxhamFyYQZIdWVsdmEGSHVlc2NhBUphw6luBUxlw7NuBkxsZWlkYQRMdWdvBk1hZHJpZAdNw6FsYWdhBk11cmNpYQdOYXZhcnJhB091cmVuc2UIUGFsZW5jaWEKUGFsbWFzIExhcwpQb250ZXZlZHJhCFJpb2phIExhCVNhbGFtYW5jYRZTYW50YSBDcnV6IGRlIFRlbmVyaWZlB1NlZ292aWEHU2V2aWxsYQVTb3JpYQlUYXJyYWdvbmEGVGVydWVsBlRvbGVkbwhWYWxlbmNpYQpWYWxsYWRvbGlkBlphbW9yYQhaYXJhZ296YQVDZXV0YQdNZWxpbGxhFTUAAjAyAjAzAjA0AjAxAjMzAjA1AjA2AjA3AjA4AjQ4AjA5AjEwAjExAjM5AjEyAjEzAjE0AjE1AjE2AjIwAjE3AjE4AjE5AjIxAjIyAjIzAjI0AjI1AjI3AjI4AjI5AjMwAjMxAjMyAjM0AjM1AjM2AjI2AjM3AjM4AjQwAjQxAjQyAjQzAjQ0AjQ1AjQ2AjQ3AjQ5AjUwAjUxAjUyFCsDNWdnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnFgFmZAIUD2QWBgIBDxYCHwcFBVBhw61zZAIDDw8WAh8GaGRkAgUPEGQQFe8BE1NlbGVjY2lvbmUgdW4gcGHDrXMJQXJnZW50aW5hCUF1c3RyYWxpYQVDaGluYQVJdGFseQVKYXBhbgZNZXhpY28LTmV3IFplYWxhbmQIUG9ydHVnYWwHRXNwYcOxYQdHZXJtYW55BkZyYW5jZRJSdXNzaWFuIEZlZGVyYXRpb24OVW5pdGVkIEtpbmdkb20UVW5pdGVkIFN0YXRlcyBvZiBBbWULQWZnaGFuaXN0YW4HQWxiYW5pYQdBbGdlcmlhDkFtZXJpY2FuIFNhbW9hB0FuZG9ycmEGQW5nb2xhCEFuZ3VpbGxhCkFudGFyY3RpY2EHQW50aWd1YQdBcm1lbmlhBUFydWJhB0F1c3RyaWEKQXplcmJhaWphbgdCYWhhbWFzB0JhaHJhaW4KQmFuZ2xhZGVzaAhCYXJiYWRvcwdCZWxhcnVzB0JlbGdpdW0GQmVsaXplBUJlbmluB0Jlcm11ZGEGQmh1dGFuB0JvbGl2aWEGQm9zbmlhCEJvdHN3YW5hDUJvdXZldCBJc2xhbmQGQnJhemlsDkJyaXRpc2ggSW5kaWFuEUJydW5laSBEYXJ1c3NhbGFtCEJ1bGdhcmlhDEJ1cmtpbmEgRmFzbwdCdXJ1bmRpCENhbWJvZGlhCENhbWVyb29uBkNhbmFkYQpDYXBlIFZlcmRlDkNheW1hbiBJc2xhbmRzE0NlbnRyYWwgQWZyaWNhbiBSZXAEQ2hhZAVDaGlsZRBDaHJpc3RtYXMgSXNsYW5kDUNvY29zIElzbGFuZHMIQ29sb21iaWEHQ29tb3JvcwVDb25nbwxDb29rIElzbGFuZHMKQ29zdGEgUmljYQdDcm9hdGlhBEN1YmEGQ3lwcnVzDkN6ZWNoIFJlcHVibGljB0Rlbm1hcmsIRGppYm91dGkIRG9taW5pY2ESRG9taW5pY2FuIFJlcHVibGljCkVhc3QgVGltb3IHRWN1YWRvcgVFZ3lwdAtFbCBTYWx2YWRvchFFcXVhdG9yaWFsIEd1aW5lYQdFcml0cmVhB0VzdG9uaWEIRXRoaW9waWENRmFyb2UgSXNsYW5kcwRGaWppB0ZpbmxhbmQNRnJlbmNoIEd1aWFuYRBGcmVuY2ggUG9seW5lc2lhBUdhYm9uBkdhbWJpYQdHZW9yZ2lhBUdoYW5hBkdyZWVjZQlHcmVlbmxhbmQHR3JlbmFkYQpHdWFkZWxvdXBlBEd1YW0JR3VhdGVtYWxhBkd1aW5lYQ1HdWluZWEgQmlzc2F1Bkd1eWFuYQVIYWl0aQhIb25kdXJhcwlIb25nIEtvbmcHSHVuZ2FyeQdJY2VsYW5kBUluZGlhCUluZG9uZXNpYQRJcmFuBElyYXEHSXJlbGFuZAZJc3JhZWwLSXZvcnkgQ29hc3QHSmFtYWljYQZKb3JkYW4KS2F6YWtoc3RhbgVLZW55YQhLaXJpYmF0aQZLdXdhaXQKS3lyZ3l6c3RhbgNMYW8GTGF0dmlhB0xlYmFub24HTGVzb3RobwdMaWJlcmlhBUxpYnlhDUxpZWNodGVuc3RlaW4JTGl0aHVhbmlhCkx1eGVtYm91cmcFTWFjYXUJTWFjZWRvbmlhCk1hZGFnYXNjYXIGTWFsYXdpCE1hbGF5c2lhCE1hbGRpdmVzBE1hbGkFTWFsdGEITWFsdmluYXMQTWFyc2hhbGwgSXNsYW5kcwpNYXJ0aW5pcXVlCk1hdXJpdGFuaWEJTWF1cml0aXVzB01heW90dGUKTWljcm9uZXNpYQdNb2xkb3ZhBk1vbmFjbwhNb25nb2xpYQpNb250ZW5lZ3JvCk1vbnRzZXJyYXQHTW9yb2NjbwpNb3phbWJpcXVlB015YW5tYXIHTmFtaWJpYQVOYXVydQVOZXBhbAtOZXRoZXJsYW5kcxROZXRoZXJsYW5kcyBBbnRpbGxlcw1OZXcgQ2FsZWRvbmlhCU5pY2FyYWd1YQVOaWdlcgdOaWdlcmlhBE5pdWUOTm9yZm9sayBJc2xhbmQLTm9ydGggS29yZWETTm9ydGhlcm4gTWFyaWFuYSBJcwZOb3J3YXkET21hbhlPdHJvcyBkZSBwYWlzZXMgZGVsIG11bmRvCFBha2lzdGFuBVBhbGF1BlBhbmFtYRBQYXB1YSBOZXcgR3VpbmVhCFBhcmFndWF5BFBlcnULUGhpbGlwcGluZXMIUGl0Y2Fpcm4GUG9sYW5kC1B1ZXJ0byBSaWNvBVFhdGFyB1JldW5pb24HUm9tYW5pYQZSd2FuZGEPUyBHZW9yZ2lhIFNvdXRoC1NhaW50IEx1Y2lhBVNhbW9hClNhbiBNYXJpbm8TU2FvIFRvbWUgLSBQcmluY2lwZQxTYXVkaSBBcmFiaWEHU2VuZWdhbAZTZXJiaWEKU2V5Y2hlbGxlcwxTaWVycmEgTGVvbmUJU2luZ2Fwb3JlCFNsb3Zha2lhCFNsb3ZlbmlhD1NvbG9tb24gSXNsYW5kcwdTb21hbGlhDFNvdXRoIEFmcmljYQtTb3V0aCBLb3JlYQlTcmkgTGFua2EJU3QgSGVsZW5hElN0IEtpdHRzIGFuZCBOZXZpcxNTdCBQaWVycmUgIE1pcXVlbG9uEVN0IFZpbmNlbnQtR3JlbmFkBVN1ZGFuCFN1cmluYW1lEVN2YWxiYXJkIEphbiBNIElzCVN3YXppbGFuZAZTd2VkZW4LU3dpdHplcmxhbmQFU3lyaWEGVGFpd2FuClRhamlraXN0YW4IVGFuemFuaWEIVGhhaWxhbmQEVG9nbwdUb2tlbGF1BVRvbmdhE1RyaW5pZGFkIEFuZCBUb2JhZ28HVHVuaXNpYQZUdXJrZXkMVHVya21lbmlzdGFuFFR1cmtzIENhaWNvcyBJc2xhbmRzBlR1dmFsdQZVZ2FuZGEHVWtyYWluZRRVbml0ZWQgQXJhYiBFbWlyYXRlcwdVcnVndWF5EFVTIE1pbm9yIElzbGFuZHMKVXpiZWtpc3RhbgdWYW51YXR1B1ZhdGljYW4JVmVuZXp1ZWxhB1ZpZXRuYW0OVmlyZ2luIElzbGFuZHMRVmlyZ2luIElzbGFuZHMgVVMQV2FsbGlzIEZ1dHVuYSBJcw5XZXN0ZXJuIFNhaGFyYQVZZW1lbgpZdWdvc2xhdmlhBVphaXJlBlphbWJpYQhaaW1iYWJ3ZRXvAQADMDMyAzAzNgMxNTYDMzgwAzM5MgM0ODQDNTU0AzYyMAM3MjQDMjc2AzI1MAM2NDMDODI2Azg0MAMwMDQDMDA4AzAxMgMwMTYDMDIwAzAyNAM2NjADMDEwAzAyOAMwNTEDNTMzAzA0MAMwMzEDMDQ0AzA0OAMwNTADMDUyAzExMgMwNTYDMDg0AzIwNAMwNjADMDY0AzA2OAMwNzADMDcyAzA3NAMwNzYDMDg2AzA5NgMxMDADODU0AzEwOAMxMTYDMTIwAzEyNAMxMzIDMTM2AzE0MAMxNDgDMTUyAzE2MgMxNjYDMTcwAzE3NAMxNzgDMTg0AzE4OAMxOTEDMTkyAzE5NgMyMDMDMjA4AzI2MgMyMTIDMjE0AzYyNgMyMTgDODE4AzIyMgMyMjYDMjMyAzIzMwMyMzEDMjM0AzI0MgMyNDYDMjU0AzI1OAMyNjYDMjcwAzI2OAMyODgDMzAwAzMwNAMzMDgDMzEyAzMxNgMzMjADMzI0AzYyNAMzMjgDMzMyAzM0MAMzNDQDMzQ4AzM1MgMzNTYDMzYwAzM2NAMzNjgDMzcyAzM3NgMzODQDMzg4AzQwMAMzOTgDNDA0AzI5NgM0MTQDNDE3AzQxOAM0MjgDNDIyAzQyNgM0MzADNDM0AzQzOAM0NDADNDQyAzQ0NgM4MDcDNDUwAzQ1NAM0NTgDNDYyAzQ2NgM0NzADMjM4AzU4NAM0NzQDNDc4AzQ4MAMxNzUDNTgzAzQ5OAM0OTIDNDk2AzQ5OQM1MDADNTA0AzUwOAMxMDQDNTE2AzUyMAM1MjQDNTI4AzUzMAM1NDADNTU4AzU2MgM1NjYDNTcwAzU3NAM0MDgDNTgwAzU3OAM1MTIDNzQ0AzU4NgM1ODUDNTkxAzU5OAM2MDADNjA0AzYwOAM2MTIDNjE2AzYzMAM2MzQDNjM4AzY0MgM2NDYDMjM5AzY2MgM4ODIDNjc0AzY3OAM2ODIDNjg2AzY4OAM2OTADNjk0AzcwMgM3MDMDNzA1AzA5MAM3MDYDNzEwAzQxMAMxNDQDNjU0AzY1OQM2NjYDNjcwAzczNgM3NDADNzQ0Azc0OAM3NTIDNzU2Azc2MAMxNTgDNzYyAzgzNAM3NjQDNzY4Azc3MgM3NzYDNzgwAzc4OAM3OTIDNzk1Azc5NgM3OTgDODAwAzgwNAM3ODQDODU4AzU4MQM4NjADNTQ4AzMzNgM4NjIDNzA0AzA5MgM4NTADODc2AzczMgM4ODcDODkxAzE4MAM4OTQDNzE2FCsD7wFnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2RkAhUPZBYCAgEPFgIfBwUJVGVsw6lmb25vZAIXD2QWAgIDDxYCHwcFiQFIZSBsZcOtZG8geSBhY2VwdG8gbGEgPGEgaHJlZj0iaHR0cHM6Ly90aWNrZXRzLmFsaGFtYnJhLXBhdHJvbmF0by5lcy9wb2xpdGljYS1kZS1wcml2YWNpZGFkLyIgdGFyZ2V0PSJfYmxhbmsiPlBvbMOtdGljYSBkZSBwcml2YWNpZGFkPC9hPmQCGA8WAh8GaBYCAgMPFgIfB2VkAggPDxYCHwEFC1JlZ8Otc3RyZXNlZGQCAw8WAh8GaBYEAgMPDxYCHwMFHi9yZXNlcnZhckVudHJhZGFzLmFzcHg/b3BjPTE0MmRkAgUPDxYCHwEFDkNlcnJhciBzZXNpw7NuZGQCAQ9kFgICAQ8PFgQfCQUGYWN0aXZlHwoCAmRkAgIPDxYEHwMFPmh0dHBzOi8vd3d3LmFsaGFtYnJhLXBhdHJvbmF0by5lcy92aXNpdGFyL3ByZWd1bnRhcy1mcmVjdWVudGVzHwZnZGQCBA9kFgICAQ8PFgIfAwUoaHR0cDovL3d3dy55b3V0dWJlLmNvbS9hbGhhbWJyYXBhdHJvbmF0b2RkAgUPZBYCAgEPDxYCHwMFK2h0dHBzOi8vd3d3Lmluc3RhZ3JhbS5jb20vYWxoYW1icmFfb2ZpY2lhbC9kZAIGD2QWAgIBDw8WAh8DBShodHRwczovL3d3dy5mYWNlYm9vay5jb20vYWxoYW1icmFjdWx0dXJhZGQCBw9kFgICAQ8PFgIfAwUmaHR0cDovL3d3dy50d2l0dGVyLmNvbS9hbGhhbWJyYWN1bHR1cmFkZAIID2QWAgIBDw8WAh8DBSlodHRwczovL2VzLnBpbnRlcmVzdC5jb20vYWxoYW1icmFncmFuYWRhL2RkAgkPFgIfBmhkAgoPFgIfBmgWAgIBDw8WAh8DZGQWAmYPDxYCHwUFFUFsaGFtYnJhIHkgR2VuZXJhbGlmZWRkAgsPZBYCZg8PFgQfAwU+aHR0cHM6Ly93d3cuYWxoYW1icmEtcGF0cm9uYXRvLmVzL3Zpc2l0YXIvcHJlZ3VudGFzLWZyZWN1ZW50ZXMfBmdkZAIND2QWCAIBDw8WAh8GaGQWAgIBD2QWAmYPZBYGAgMPDxYCHwZoZGQCBA8PFgIeBkVzdGFkb2ZkFgJmD2QWAgIBD2QWAmYPZBYCAgEPZBYCAggPFgIfBmhkAg4PZBYEAgsPZBYEAgEPZBYCAgMPEGRkFgBkAgYPZBYCAgcPEGRkFgBkAg0PZBYEAgYPZBYCAgEPZBYCAgMPEGRkFgBkAgkPZBYCAgcPEGRkFgBkAgMPDxYCHwZoZBYCZg9kFgJmD2QWBgIBDw8WAh8GaGRkAggPZBYGAgUPZBYCAgEPEGRkFgBkAgYPZBYCAgEPEGRkFgBkAggPZBYEZg8QZGQWAGQCAQ8QZGQWAGQCCg9kFgICBQ9kFg4CAw9kFgICBQ8QZGQWAGQCBA9kFgICAw8QZGQWAGQCBg9kFgICBw8QZGQWAGQCCA9kFgICBQ8QZGQWAGQCCQ9kFgICBQ8QZGQWAGQCDw9kFgICBw8QZGQWAGQCFg9kFgQCAQ9kFgICAw8QZGQWAGQCBg9kFgICBw8QZGQWAGQCBQ8PFgIfBmhkFgJmD2QWAmYPZBYEAgMPDxYCHwtmZBYCZg9kFgICAQ9kFgJmD2QWAgIBD2QWAgIIDxYCHwZoZAIGD2QWAmYPZBYCAgEPZBYCZg9kFgICAQ88KwAKAQAPFgQeDVByZXZNb250aFRleHRlHg1OZXh0TW9udGhUZXh0BS08aW1nIHNyYz0vQXBwX3RoZW1lcy9BTEhBTUJSQS9pbWcvbmV4dC5wbmcgLz5kZAIHDw8WIB4UTG9jYWxpemFkb3JQYXJhbWV0cm9kHhBGaW5hbGl6YXJNZW5vcmVzaB4OQWZvcm9QYXJhbWV0cm8CAR4GUGFnYWRhBQVGYWxzZR4HU2ltYm9sbwUD4oKsHhNFbmxhY2VNZW51UGFyYW1ldHJvBQdHRU5FUkFMHgxTZXNpb25EaWFyaWFoHgpOb21pbmFjaW9uZh4MQ2FwdGNoYVBhc28xZx4MTnVtRGVjaW1hbGVzAgIeD0NhcHRjaGFWYWxpZGFkb2ceCFNpbkZlY2hhZh4VRmVjaGFNaW5pbWFEaXNwb25pYmxlBv8/N/R1KMorHgxUZW5lbW9zTmlub3NoHhZHcnVwb0ludGVybmV0UGFyYW1ldHJvBQMxNDIeDFNlc2lvbkFjdHVhbAUfNG1vZXBsNDVubWZiYzNpMXhlbHlnZHVrMjcwMDg3NGQWBAIBD2QWAmYPZBYiAgMPDxYCHwZoZGQCBA8PFgIfC2ZkFgJmD2QWAgIBD2QWAmYPZBYCAgEPZBYGZg8PFgIfAQUFZW1haWxkZAICDw8WAh8BBQxUZWxlZm9ubyBTTVNkZAIIDxYCHwZoZAIFDw8WAh8DBTBodHRwczovL3d3dy5hbGhhbWJyYS1wYXRyb25hdG8uZXMvP2NhPTAmbGc9ZXMtRVNkZAIGDxYCHwFlZAIHDxYCHwEFF1Zpc2l0YSBBbGhhbWJyYSBHZW5lcmFsZAIIDxYCHgVjbGFzcwUWc3RlcC10aXRsZSBzdGVwLWFjdGl2ZRYCAgEPFgIfAWRkAgkPDxYCHwZoZBYCAgEPDxYCHwEFC0lyIGEgcGFzbyAxZGQCCg8PFgIfBmdkFghmDxYCHwFlZAIBDxYCHwFlZAIGDw8WHB4RRmVjaGFNaW5pbWFHbG9iYWwGgLdurmV43QgeBFBhc28CAR4NR3J1cG9JbnRlcm5ldAUDMTQyHhVUb3RhbE1lc2VzQWRlbGFudGFkb3MCAR4MRGF0b3NGZXN0aXZvMrsEAAEAAAD/////AQAAAAAAAAAMAgAAAEhBcHBfQ29kZS54aGpwdml6bywgVmVyc2lvbj0wLjAuMC4wLCBDdWx0dXJlPW5ldXRyYWwsIFB1YmxpY0tleVRva2VuPW51bGwFAQAAAB9EYXRvc0Zlc3Rpdm9zK0RhdG9zTGlzdEZlc3Rpdm9zAQAAABFfTHN0RGF0b3NGZXN0aXZvcwOJAVN5c3RlbS5Db2xsZWN0aW9ucy5HZW5lcmljLkxpc3RgMVtbRGF0b3NGZXN0aXZvcytEYXRvc0Zlc3Rpdm8sIEFwcF9Db2RlLnhoanB2aXpvLCBWZXJzaW9uPTAuMC4wLjAsIEN1bHR1cmU9bmV1dHJhbCwgUHVibGljS2V5VG9rZW49bnVsbF1dAgAAAAkDAAAABAMAAACJAVN5c3RlbS5Db2xsZWN0aW9ucy5HZW5lcmljLkxpc3RgMVtbRGF0b3NGZXN0aXZvcytEYXRvc0Zlc3Rpdm8sIEFwcF9Db2RlLnhoanB2aXpvLCBWZXJzaW9uPTAuMC4wLjAsIEN1bHR1cmU9bmV1dHJhbCwgUHVibGljS2V5VG9rZW49bnVsbF1dAwAAAAZfaXRlbXMFX3NpemUIX3ZlcnNpb24EAAAcRGF0b3NGZXN0aXZvcytEYXRvc0Zlc3Rpdm9bXQIAAAAICAkEAAAAAAAAAAAAAAAHBAAAAAABAAAAAAAAAAQaRGF0b3NGZXN0aXZvcytEYXRvc0Zlc3Rpdm8CAAAACx4TTWluaW1vR3J1cG9JbnRlcm5ldAIBHhFGZWNoYU1heGltYUdsb2JhbAYAusZyFKfeCB4PRGlyZWNjaW9uQWN0dWFsBQRQcmV2Hg1Fc0xpc3RhRXNwZXJhaB4LRm9yemFyQ2FyZ2FoHg5GZWNoYXNWaWdlbmNpYTKIDQABAAAA/////wEAAAAAAAAABAEAAADiAVN5c3RlbS5Db2xsZWN0aW9ucy5HZW5lcmljLkRpY3Rpb25hcnlgMltbU3lzdGVtLlN0cmluZywgbXNjb3JsaWIsIFZlcnNpb249NC4wLjAuMCwgQ3VsdHVyZT1uZXV0cmFsLCBQdWJsaWNLZXlUb2tlbj1iNzdhNWM1NjE5MzRlMDg5XSxbU3lzdGVtLlN0cmluZywgbXNjb3JsaWIsIFZlcnNpb249NC4wLjAuMCwgQ3VsdHVyZT1uZXV0cmFsLCBQdWJsaWNLZXlUb2tlbj1iNzdhNWM1NjE5MzRlMDg5XV0EAAAAB1ZlcnNpb24IQ29tcGFyZXIISGFzaFNpemUNS2V5VmFsdWVQYWlycwADAAMIkgFTeXN0ZW0uQ29sbGVjdGlvbnMuR2VuZXJpYy5HZW5lcmljRXF1YWxpdHlDb21wYXJlcmAxW1tTeXN0ZW0uU3RyaW5nLCBtc2NvcmxpYiwgVmVyc2lvbj00LjAuMC4wLCBDdWx0dXJlPW5ldXRyYWwsIFB1YmxpY0tleVRva2VuPWI3N2E1YzU2MTkzNGUwODldXQjmAVN5c3RlbS5Db2xsZWN0aW9ucy5HZW5lcmljLktleVZhbHVlUGFpcmAyW1tTeXN0ZW0uU3RyaW5nLCBtc2NvcmxpYiwgVmVyc2lvbj00LjAuMC4wLCBDdWx0dXJlPW5ldXRyYWwsIFB1YmxpY0tleVRva2VuPWI3N2E1YzU2MTkzNGUwODldLFtTeXN0ZW0uU3RyaW5nLCBtc2NvcmxpYiwgVmVyc2lvbj00LjAuMC4wLCBDdWx0dXJlPW5ldXRyYWwsIFB1YmxpY0tleVRva2VuPWI3N2E1YzU2MTkzNGUwODldXVtdBwAAAAkCAAAABwAAAAkDAAAABAIAAACSAVN5c3RlbS5Db2xsZWN0aW9ucy5HZW5lcmljLkdlbmVyaWNFcXVhbGl0eUNvbXBhcmVyYDFbW1N5c3RlbS5TdHJpbmcsIG1zY29ybGliLCBWZXJzaW9uPTQuMC4wLjAsIEN1bHR1cmU9bmV1dHJhbCwgUHVibGljS2V5VG9rZW49Yjc3YTVjNTYxOTM0ZTA4OV1dAAAAAAcDAAAAAAEAAAAHAAAAA+QBU3lzdGVtLkNvbGxlY3Rpb25zLkdlbmVyaWMuS2V5VmFsdWVQYWlyYDJbW1N5c3RlbS5TdHJpbmcsIG1zY29ybGliLCBWZXJzaW9uPTQuMC4wLjAsIEN1bHR1cmU9bmV1dHJhbCwgUHVibGljS2V5VG9rZW49Yjc3YTVjNTYxOTM0ZTA4OV0sW1N5c3RlbS5TdHJpbmcsIG1zY29ybGliLCBWZXJzaW9uPTQuMC4wLjAsIEN1bHR1cmU9bmV1dHJhbCwgUHVibGljS2V5VG9rZW49Yjc3YTVjNTYxOTM0ZTA4OV1dBPz////kAVN5c3RlbS5Db2xsZWN0aW9ucy5HZW5lcmljLktleVZhbHVlUGFpcmAyW1tTeXN0ZW0uU3RyaW5nLCBtc2NvcmxpYiwgVmVyc2lvbj00LjAuMC4wLCBDdWx0dXJlPW5ldXRyYWwsIFB1YmxpY0tleVRva2VuPWI3N2E1YzU2MTkzNGUwODldLFtTeXN0ZW0uU3RyaW5nLCBtc2NvcmxpYiwgVmVyc2lvbj00LjAuMC4wLCBDdWx0dXJlPW5ldXRyYWwsIFB1YmxpY0tleVRva2VuPWI3N2E1YzU2MTkzNGUwODldXQIAAAADa2V5BXZhbHVlAQEGBQAAAAM0MjYGBgAAABcjMTAvMDQvMjAyNS0zMC8wNC8yMDI1IwH5/////P///wYIAAAAAzQzMQYJAAAAFyMxMC8wNC8yMDI1LTMwLzA0LzIwMjUjAfb////8////BgsAAAADNDMwBgwAAAAXIzEwLzA0LzIwMjUtMzAvMDQvMjAyNSMB8/////z///8GDgAAAAM0MjcGDwAAABcjMTAvMDQvMjAyNS0zMC8wNC8yMDI1IwHw/////P///wYRAAAAAzQyOAYSAAAAFyMxMC8wNC8yMDI1LTMwLzA0LzIwMjUjAe3////8////BhQAAAADNDI5BhUAAAAXIzEwLzA0LzIwMjUtMzAvMDQvMjAyNSMB6v////z///8GFwAAAAM0ODUGGAAAABcjMTAvMDQvMjAyNS0zMC8wNC8yMDI1IwsfBmceEENhbnRpZGFkRW50cmFkYXMy2wQAAQAAAP////8BAAAAAAAAAAQBAAAA4QFTeXN0ZW0uQ29sbGVjdGlvbnMuR2VuZXJpYy5EaWN0aW9uYXJ5YDJbW1N5c3RlbS5TdHJpbmcsIG1zY29ybGliLCBWZXJzaW9uPTQuMC4wLjAsIEN1bHR1cmU9bmV1dHJhbCwgUHVibGljS2V5VG9rZW49Yjc3YTVjNTYxOTM0ZTA4OV0sW1N5c3RlbS5JbnQzMiwgbXNjb3JsaWIsIFZlcnNpb249NC4wLjAuMCwgQ3VsdHVyZT1uZXV0cmFsLCBQdWJsaWNLZXlUb2tlbj1iNzdhNWM1NjE5MzRlMDg5XV0DAAAAB1ZlcnNpb24IQ29tcGFyZXIISGFzaFNpemUAAwAIkgFTeXN0ZW0uQ29sbGVjdGlvbnMuR2VuZXJpYy5HZW5lcmljRXF1YWxpdHlDb21wYXJlcmAxW1tTeXN0ZW0uU3RyaW5nLCBtc2NvcmxpYiwgVmVyc2lvbj00LjAuMC4wLCBDdWx0dXJlPW5ldXRyYWwsIFB1YmxpY0tleVRva2VuPWI3N2E1YzU2MTkzNGUwODldXQgAAAAACQIAAAAAAAAABAIAAACSAVN5c3RlbS5Db2xsZWN0aW9ucy5HZW5lcmljLkdlbmVyaWNFcXVhbGl0eUNvbXBhcmVyYDFbW1N5c3RlbS5TdHJpbmcsIG1zY29ybGliLCBWZXJzaW9uPTQuMC4wLjAsIEN1bHR1cmU9bmV1dHJhbCwgUHVibGljS2V5VG9rZW49Yjc3YTVjNTYxOTM0ZTA4OV1dAAAAAAseF0Nh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Hx4FCnN0ZXAtdGl0bGUWAgIBDxYCHwFkZAIMDw8WAh8GaGQWDAIBDxYCHwFlZAIFDxYCHwZoZAIHD2QWCAIBDw8WAh8GaGQWAgIBD2QWAmYPZBYCAgEPPCsACgEADxYEHwxlHw0FLTxpbWcgc3JjPS9BcHBfdGhlbWVzL0FMSEFNQlJBL2ltZy9uZXh0LnBuZyAvPmRkAgMPFgIfBmgWAgIBDxBkZBYAZAIFDxYCHwZoFgICAQ8QZGQWAGQCCQ8PFgIfBmhkFgRmDxBkEBUIGFNlbGVjY2lvbmUgdW4gaXRpbmVyYXJpbyBWaXNpdGFzIEd1aWFkYXMgcG9yIGVsIE1vbnVtZW50byxWaXNpdGFzIEF1dG9ndWlhZGFzIHBvciBlbCBNb251bWVudG8gR2VuZXJhbCRWaXNpdGFzIENvbWJpbmFkYXMgQWxoYW1icmEgKyBDaXVkYWQsVmlzaXRhcyBHdWlhZGFzIHBvciBsYSBEZWhlc2EgZGVsIEdlbmVyYWxpZmUpVmlzaXRhcyBHdWlhZGFzIHBvciBlbCBNb251bWVudG8gSmFyZGluZXMtVmlzaXRhcyBBdXRvZ3VpYWRhcyBwb3IgZWwgTW9udW1lbnRvIEphcmRpbmVzHlZpc2l0YXMgR3VpYWRhcyBNdXNlbyArIENpdWRhZBUIACBWaXNpdGFzIEd1aWFkYXMgcG9yIGVsIE1vbnVtZW50byxWaXNpdGFzIEF1dG9ndWlhZGFzIHBvciBlbCBNb251bWVudG8gR2VuZXJhbCRWaXNpdGFzIENvbWJpbmFkYXMgQWxoYW1icmEgKyBDaXVkYWQsVmlzaXRhcyBHdWlhZGFzIHBvciBsYSBEZWhlc2EgZGVsIEdlbmVyYWxpZmUpVmlzaXRhcyBHdWlhZGFzIHBvciBlbCBNb251bWVudG8gSmFyZGluZXMtVmlzaXRhcyBBdXRvZ3VpYWRhcyBwb3IgZWwgTW9udW1lbnRvIEphcmRpbmVzHlZpc2l0YXMgR3VpYWRhcyBNdXNlbyArIENpdWRhZBQrAwhnZ2dnZ2dnZxYBZmQCAQ8QDxYCHwZoZBAVARhTZWxlY2Npb25lIHVuIGl0aW5lcmFyaW8VAQAUKwMBZxYBZmQCCw8WAh8GaGQCDQ8PFgIfAQUXdm9sdmVyIGFsIHBhc28gYW50ZXJpb3JkZAIPD2QWAmYPZBYCAgEPDxYEHwEFC0lyIGEgcGFzbyAzHwZoZGQCDQ8WBB8eBQpzdGVwLXRpdGxlHwZnZAIODw8WAh8GaGQWGmYPFgIfAWVkAgEPFgIfAQUBLmQCAg9kFgJmD2QWCgIBDw8WAh4KSGVhZGVyVGV4dAUlRGViZSBpbnRyb2R1Y2lyIGxvcyB2YWxvcmVzIGNvcnJlY3Rvc2RkAgMPZBYEZg9kFgJmDw8WAh8BBRdOb21icmUgZGVsIGNvbXByYWRvciAqIGRkAgEPZBYCZg8PFgIfAQUMQXBlbGxpZG9zICogZGQCBA9kFgRmD2QWBGYPDxYCHwEFGURvY3VtZW50byBkZSBpZGVudGlkYWQgKiBkZAICDxBkEBUDDEROSSBFc3Bhw7FvbAxOSUUgRXNwYcOxb2wXT3RybyBOcm8uIGlkZW50aWZpY2Fkb3IVAwNkbmkDbmllB290cm9faWQUKwMDZ2dnFgFmZAIBD2QWAmYPDxYCHwEFF07Dum1lcm8gZGUgZG9jdW1lbnRvICogZGQCBQ9kFgRmD2QWAmYPDxYCHwEFCEVtYWlsICogZGQCAQ9kFgJmDw8WAh8BBRFDb25maXJtYSBFbWFpbCAqIGRkAgYPZBYCZg9kFgJmDw8WAh8BBQxUZWzDqWZvbm8gKiBkZAIEDxYCHwZnFgICAQ8QDxYCHgdDaGVja2VkaGRkZGQCBg9kFgQCAQ9kFgICAw8QZBAVBAxETkkgRXNwYcOxb2wMQ0lGIEVzcGHDsW9sDE5JRSBFc3Bhw7FvbBdPdHJvIE5yby4gaWRlbnRpZmljYWRvchUEA2RuaQNjaWYDbmllB290cm9faWQUKwMEZ2dnZxYBZmQCBg9kFgQCBQ8PFgIfBmhkZAIHDxBkEBXvARNTZWxlY2Npb25lIHVuIHBhw61zCUFyZ2VudGluYQlBdXN0cmFsaWEFQ2hpbmEFSXRhbHkFSmFwYW4GTWV4aWNvC05ldyBaZWFsYW5kCFBvcnR1Z2FsB0VzcGHDsWEHR2VybWFueQZGcmFuY2USUnVzc2lhbiBGZWRlcmF0aW9uDlVuaXRlZCBLaW5nZG9tFFVuaXRlZCBTdGF0ZXMgb2YgQW1lC0FmZ2hhbmlzdGFuB0FsYmFuaWEHQWxnZXJpYQ5BbWVyaWNhbiBTYW1vYQdBbmRvcnJhBkFuZ29sYQhBbmd1aWxsYQpBbnRhcmN0aWNhB0FudGlndWEHQXJtZW5pYQVBcnViYQdBdXN0cmlhCkF6ZXJiYWlqYW4HQmFoYW1hcwdCYWhyYWluCkJhbmdsYWRlc2gIQmFyYmFkb3MHQmVsYXJ1cwdCZWxnaXVtBkJlbGl6ZQVCZW5pbgdCZXJtdWRhBkJodXRhbgdCb2xpdmlhBkJvc25pYQhCb3Rzd2FuYQ1Cb3V2ZXQgSXNsYW5kBkJyYXppbA5Ccml0aXNoIEluZGlhbhFCcnVuZWkgRGFydXNzYWxhbQhCdWxnYXJpYQxCdXJraW5hIEZhc28HQnVydW5kaQhDYW1ib2RpYQhDYW1lcm9vbgZDYW5hZGEKQ2FwZSBWZXJkZQ5DYXltYW4gSXNsYW5kcxNDZW50cmFsIEFmcmljYW4gUmVwBENoYWQFQ2hpbGUQQ2hyaXN0bWFzIElzbGFuZA1Db2NvcyBJc2xhbmRzCENvbG9tYmlhB0NvbW9yb3MFQ29uZ28MQ29vayBJc2xhbmRzCkNvc3RhIFJpY2EHQ3JvYXRpYQRDdWJhBkN5cHJ1cw5DemVjaCBSZXB1YmxpYwdEZW5tYXJrCERqaWJvdXRpCERvbWluaWNhEkRvbWluaWNhbiBSZXB1YmxpYwpFYXN0IFRpbW9yB0VjdWFkb3IFRWd5cHQLRWwgU2FsdmFkb3IRRXF1YXRvcmlhbCBHdWluZWEHRXJpdHJlYQdFc3RvbmlhCEV0aGlvcGlhDUZhcm9lIElzbGFuZHMERmlqaQdGaW5sYW5kDUZyZW5jaCBHdWlhbmEQRnJlbmNoIFBvbHluZXNpYQVHYWJvbgZHYW1iaWEHR2VvcmdpYQVHaGFuYQZHcmVlY2UJR3JlZW5sYW5kB0dyZW5hZGEKR3VhZGVsb3VwZQRHdWFtCUd1YXRlbWFsYQZHdWluZWENR3VpbmVhIEJpc3NhdQZHdXlhbmEFSGFpdGkISG9uZHVyYXMJSG9uZyBLb25nB0h1bmdhcnkHSWNlbGFuZAVJbmRpYQlJbmRvbmVzaWEESXJhbgRJcmFxB0lyZWxhbmQGSXNyYWVsC0l2b3J5IENvYXN0B0phbWFpY2EGSm9yZGFuCkthemFraHN0YW4FS2VueWEIS2lyaWJhdGkGS3V3YWl0Ckt5cmd5enN0YW4DTGFvBkxhdHZpYQdMZWJhbm9uB0xlc290aG8HTGliZXJpYQVMaWJ5YQ1MaWVjaHRlbnN0ZWluCUxpdGh1YW5pYQpMdXhlbWJvdXJnBU1hY2F1CU1hY2Vkb25pYQpNYWRhZ2FzY2FyBk1hbGF3aQhNYWxheXNpYQhNYWxkaXZlcwRNYWxpBU1hbHRhCE1hbHZpbmFzEE1hcnNoYWxsIElzbGFuZHMKTWFydGluaXF1ZQpNYXVyaXRhbmlhCU1hdXJpdGl1cwdNYXlvdHRlCk1pY3JvbmVzaWEHTW9sZG92YQZNb25hY28ITW9uZ29saWEKTW9udGVuZWdybwpNb250c2VycmF0B01vcm9jY28KTW96YW1iaXF1ZQdNeWFubWFyB05hbWliaWEFTmF1cnUFTmVwYWwLTmV0aGVybGFuZHMUTmV0aGVybGFuZHMgQW50aWxsZXMNTmV3IENhbGVkb25pYQlOaWNhcmFndWEFTmlnZXIHTmlnZXJpYQROaXVlDk5vcmZvbGsgSXNsYW5kC05vcnRoIEtvcmVhE05vcnRoZXJuIE1hcmlhbmEgSXMGTm9yd2F5BE9tYW4ZT3Ryb3MgZGUgcGFpc2VzIGRlbCBtdW5kbwhQYWtpc3RhbgVQYWxhdQZQYW5hbWEQUGFwdWEgTmV3IEd1aW5lYQhQYXJhZ3VheQRQZXJ1C1BoaWxpcHBpbmVzCFBpdGNhaXJuBlBvbGFuZAtQdWVydG8gUmljbwVRYXRhcgdSZXVuaW9uB1JvbWFuaWEGUndhbmRhD1MgR2VvcmdpYSBTb3V0aAtTYWludCBMdWNpYQVTYW1vYQpTYW4gTWFyaW5vE1NhbyBUb21lIC0gUHJpbmNpcGUMU2F1ZGkgQXJhYmlhB1NlbmVnYWwGU2VyYmlhClNleWNoZWxsZXMMU2llcnJhIExlb25lCVNpbmdhcG9yZQhTbG92YWtpYQhTbG92ZW5pYQ9Tb2xvbW9uIElzbGFuZHMHU29tYWxpYQxTb3V0aCBBZnJpY2ELU291dGggS29yZWEJU3JpIExhbmthCVN0IEhlbGVuYRJTdCBLaXR0cyBhbmQgTmV2aXMTU3QgUGllcnJlICBNaXF1ZWxvbhFTdCBWaW5jZW50LUdyZW5hZAVTdWRhbghTdXJpbmFtZRFTdmFsYmFyZCBKYW4gTSBJcwlTd2F6aWxhbmQGU3dlZGVuC1N3aXR6ZXJsYW5kBVN5cmlhBlRhaXdhbgpUYWppa2lzdGFuCFRhbnphbmlhCFRoYWlsYW5kBFRvZ28HVG9rZWxhdQVUb25nYRNUcmluaWRhZCBBbmQgVG9iYWdvB1R1bmlzaWEGVHVya2V5DFR1cmttZW5pc3RhbhRUdXJrcyBDYWljb3MgSXNsYW5kcwZUdXZhbHUGVWdhbmRhB1VrcmFpbmUUVW5pdGVkIEFyYWIgRW1pcmF0ZXMHVXJ1Z3VheRBVUyBNaW5vciBJc2xhbmRzClV6YmVraXN0YW4HVmFudWF0dQdWYXRpY2FuCVZlbmV6dWVsYQdWaWV0bmFtDlZpcmdpbiBJc2xhbmRzEVZpcmdpbiBJc2xhbmRzIFVTEFdhbGxpcyBGdXR1bmEgSXMOV2VzdGVybiBTYWhhcmEFWWVtZW4KWXVnb3NsYXZpYQVaYWlyZQZaYW1iaWEIWmltYmFid2UV7wEAAzAzMgMwMzYDMTU2AzM4MAMzOTIDNDg0AzU1NAM2MjADNzI0AzI3NgMyNTADNjQzAzgyNgM4NDADMDA0AzAwOAMwMTIDMDE2AzAyMAMwMjQDNjYwAzAxMAMwMjgDMDUxAzUzMwMwNDADMDMxAzA0NAMwNDgDMDUwAzA1MgMxMTIDMDU2AzA4NAMyMDQDMDYwAzA2NAMwNjgDMDcwAzA3MgMwNzQDMDc2AzA4NgMwOTYDMTAwAzg1NAMxMDgDMTE2AzEyMAMxMjQDMTMyAzEzNgMxNDADMTQ4AzE1MgMxNjIDMTY2AzE3MAMxNzQDMTc4AzE4NAMxODgDMTkxAzE5MgMxOTYDMjAzAzIwOAMyNjIDMjEyAzIxNAM2MjYDMjE4AzgxOAMyMjIDMjI2AzIzMgMyMzMDMjMxAzIzNAMyNDIDMjQ2AzI1NAMyNTgDMjY2AzI3MAMyNjgDMjg4AzMwMAMzMDQDMzA4AzMxMgMzMTYDMzIwAzMyNAM2MjQDMzI4AzMzMgMzNDADMzQ0AzM0OAMzNTIDMzU2AzM2MAMzNjQDMzY4AzM3MgMzNzYDMzg0AzM4OAM0MDADMzk4AzQwNAMyOTYDNDE0AzQxNwM0MTgDNDI4AzQyMgM0MjYDNDMwAzQzNAM0MzgDNDQwAzQ0MgM0NDYDODA3AzQ1MAM0NTQDNDU4AzQ2MgM0NjYDNDcwAzIzOAM1ODQDNDc0AzQ3OAM0ODADMTc1AzU4MwM0OTgDNDkyAzQ5NgM0OTkDNTAwAzUwNAM1MDgDMTA0AzUxNgM1MjADNTI0AzUyOAM1MzADNTQwAzU1OAM1NjIDNTY2AzU3MAM1NzQDNDA4AzU4MAM1NzgDNTEyAzc0NAM1ODYDNTg1AzU5MQM1OTgDNjAwAzYwNAM2MDgDNjEyAzYxNgM2MzADNjM0AzYzOAM2NDIDNjQ2AzIzOQM2NjIDODgyAzY3NAM2NzgDNjgyAzY4NgM2ODgDNjkwAzY5NAM3MDIDNzAzAzcwNQMwOTADNzA2AzcxMAM0MTADMTQ0AzY1NAM2NTkDNjY2AzY3MAM3MzYDNzQwAzc0NAM3NDgDNzUyAzc1NgM3NjADMTU4Azc2MgM4MzQDNzY0Azc2OAM3NzIDNzc2Azc4MAM3ODgDNzkyAzc5NQM3OTYDNzk4AzgwMAM4MDQDNzg0Azg1OAM1ODEDODYwAzU0OAMzMzYDODYyAzcwNAMwOTIDODUwAzg3NgM3MzIDODg3Azg5MQMxODADODk0AzcxNhQrA+8BZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2cWAQIJZAIHD2QWBAIGD2QWAgIBD2QWAgIDDxBkEBUDDEROSSBFc3Bhw7FvbAxDSUYgRXNwYcOxb2wXT3RybyBOcm8uIGlkZW50aWZpY2Fkb3IVAwNkbmkDY2lmB290cm9faWQUKwMDZ2dnFgFmZAIJD2QWAgIHDxBkEBXvARNTZWxlY2Npb25lIHVuIHBhw61zCUFyZ2VudGluYQlBdXN0cmFsaWEFQ2hpbmEFSXRhbHkFSmFwYW4GTWV4aWNvC05ldyBaZWFsYW5kCFBvcnR1Z2FsB0VzcGHDsWEHR2VybWFueQZGcmFuY2USUnVzc2lhbiBGZWRlcmF0aW9uDlVuaXRlZCBLaW5nZG9tFFVuaXRlZCBTdGF0ZXMgb2YgQW1lC0FmZ2hhbmlzdGFuB0FsYmFuaWEHQWxnZXJpYQ5BbWVyaWNhbiBTYW1vYQdBbmRvcnJhBkFuZ29sYQhBbmd1aWxsYQpBbnRhcmN0aWNhB0FudGlndWEHQXJtZW5pYQVBcnViYQdBdXN0cmlhCkF6ZXJiYWlqYW4HQmFoYW1hcwdCYWhyYWluCkJhbmdsYWRlc2gIQmFyYmFkb3MHQmVsYXJ1cwdCZWxnaXVtBkJlbGl6ZQVCZW5pbgdCZXJtdWRhBkJodXRhbgdCb2xpdmlhBkJvc25pYQhCb3Rzd2FuYQ1Cb3V2ZXQgSXNsYW5kBkJyYXppbA5Ccml0aXNoIEluZGlhbhFCcnVuZWkgRGFydXNzYWxhbQhCdWxnYXJpYQxCdXJraW5hIEZhc28HQnVydW5kaQhDYW1ib2RpYQhDYW1lcm9vbgZDYW5hZGEKQ2FwZSBWZXJkZQ5DYXltYW4gSXNsYW5kcxNDZW50cmFsIEFmcmljYW4gUmVwBENoYWQFQ2hpbGUQQ2hyaXN0bWFzIElzbGFuZA1Db2NvcyBJc2xhbmRzCENvbG9tYmlhB0NvbW9yb3MFQ29uZ28MQ29vayBJc2xhbmRzCkNvc3RhIFJpY2EHQ3JvYXRpYQRDdWJhBkN5cHJ1cw5DemVjaCBSZXB1YmxpYwdEZW5tYXJrCERqaWJvdXRpCERvbWluaWNhEkRvbWluaWNhbiBSZXB1YmxpYwpFYXN0IFRpbW9yB0VjdWFkb3IFRWd5cHQLRWwgU2FsdmFkb3IRRXF1YXRvcmlhbCBHdWluZWEHRXJpdHJlYQdFc3RvbmlhCEV0aGlvcGlhDUZhcm9lIElzbGFuZHMERmlqaQdGaW5sYW5kDUZyZW5jaCBHdWlhbmEQRnJlbmNoIFBvbHluZXNpYQVHYWJvbgZHYW1iaWEHR2VvcmdpYQVHaGFuYQZHcmVlY2UJR3JlZW5sYW5kB0dyZW5hZGEKR3VhZGVsb3VwZQRHdWFtCUd1YXRlbWFsYQZHdWluZWENR3VpbmVhIEJpc3NhdQZHdXlhbmEFSGFpdGkISG9uZHVyYXMJSG9uZyBLb25nB0h1bmdhcnkHSWNlbGFuZAVJbmRpYQlJbmRvbmVzaWEESXJhbgRJcmFxB0lyZWxhbmQGSXNyYWVsC0l2b3J5IENvYXN0B0phbWFpY2EGSm9yZGFuCkthemFraHN0YW4FS2VueWEIS2lyaWJhdGkGS3V3YWl0Ckt5cmd5enN0YW4DTGFvBkxhdHZpYQdMZWJhbm9uB0xlc290aG8HTGliZXJpYQVMaWJ5YQ1MaWVjaHRlbnN0ZWluCUxpdGh1YW5pYQpMdXhlbWJvdXJnBU1hY2F1CU1hY2Vkb25pYQpNYWRhZ2FzY2FyBk1hbGF3aQhNYWxheXNpYQhNYWxkaXZlcwRNYWxpBU1hbHRhCE1hbHZpbmFzEE1hcnNoYWxsIElzbGFuZHMKTWFydGluaXF1ZQpNYXVyaXRhbmlhCU1hdXJpdGl1cwdNYXlvdHRlCk1pY3JvbmVzaWEHTW9sZG92YQZNb25hY28ITW9uZ29saWEKTW9udGVuZWdybwpNb250c2VycmF0B01vcm9jY28KTW96YW1iaXF1ZQdNeWFubWFyB05hbWliaWEFTmF1cnUFTmVwYWwLTmV0aGVybGFuZHMUTmV0aGVybGFuZHMgQW50aWxsZXMNTmV3IENhbGVkb25pYQlOaWNhcmFndWEFTmlnZXIHTmlnZXJpYQROaXVlDk5vcmZvbGsgSXNsYW5kC05vcnRoIEtvcmVhE05vcnRoZXJuIE1hcmlhbmEgSXMGTm9yd2F5BE9tYW4ZT3Ryb3MgZGUgcGFpc2VzIGRlbCBtdW5kbwhQYWtpc3RhbgVQYWxhdQZQYW5hbWEQUGFwdWEgTmV3IEd1aW5lYQhQYXJhZ3VheQRQZXJ1C1BoaWxpcHBpbmVzCFBpdGNhaXJuBlBvbGFuZAtQdWVydG8gUmljbwVRYXRhcgdSZXVuaW9uB1JvbWFuaWEGUndhbmRhD1MgR2VvcmdpYSBTb3V0aAtTYWludCBMdWNpYQVTYW1vYQpTYW4gTWFyaW5vE1NhbyBUb21lIC0gUHJpbmNpcGUMU2F1ZGkgQXJhYmlhB1NlbmVnYWwGU2VyYmlhClNleWNoZWxsZXMMU2llcnJhIExlb25lCVNpbmdhcG9yZQhTbG92YWtpYQhTbG92ZW5pYQ9Tb2xvbW9uIElzbGFuZHMHU29tYWxpYQxTb3V0aCBBZnJpY2ELU291dGggS29yZWEJU3JpIExhbmthCVN0IEhl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eUdvbGRkZAIQD2QWAmYPZBYIZg8WAh8BBSs8c3Ryb25nPlN1IGNvbXByYSBkZSBlbnRyYWRhczwvc3Ryb25nPiBwYXJhZAIBDxYCHwEFF1Zpc2l0YSBBbGhhbWJyYSBHZW5lcmFsZAICDxYCHwEF2AM8ZGl2IGNsYXNzPSdyZXN1bHQnPiAgIDxkaXYgY2xhc3M9J20tYi0xMic+ICAgICAgPGkgY2xhc3M9J2ljb24gaWNvbi1wZW9wbGUnPjwvaT4gICA8L2Rpdj4gICA8ZGl2IGNsYXNzPSdtLWItMTInPiAgICAgIDxpIGNsYXNzPSdpY29uIGljb24tZGF0ZSc+PC9pPiAgICAgIDxwPkZlY2hhOiA8YnIgLz4gICAgICA8L3A+ICAgPC9kaXY+PC9kaXY+PGRpdiBjbGFzcz0ncHJpeC10b3RhbCBicmQtc3VwLTIwJz4gICA8c3BhbiBjbGFzcz0ndGl0dWxvUHJlY2lvRmluYWwnPlRvdGFsIGVudHJhZGFzPC9zcGFuPjxzdHJvbmcgY2xhc3M9J2NvbnRlbmlkb1ByZWNpb0ZpbmFsJz4wPC9zdHJvbmc+ICAgPHNwYW4gY2xhc3M9J3RpdHVsb1ByZWNpb0ZpbmFsIHByZWNpb0ZpbmFsJz5QcmVjaW8gZmluYWw8L3NwYW4+PHN0cm9uZyBjbGFzcz0nY29udGVuaWRvUHJlY2lvRmluYWwgcHJlY2lvRmluYWwnPjAsMDAg4oKsPC9zdHJvbmc+PC9kaXY+ZAIDDxYCHwFkZAISD2QWBAIBDw8WAh8BBQ5BdmlzbyBob3Jhcmlvc2RkAgMPDxYCHwEFogFSZWN1ZXJkZSBzZXIgPGI+cHVudHVhbDwvYj4gZW4gbGEgaG9yYSBzZWxlY2Npb25hZGEgYSBsb3MgPGI+UGFsYWNpb3MgTmF6YXLDrWVzPC9iPi4gUmVzdG8gZGVsIG1vbnVtZW50byBkZSA4OjMwIGEgMTg6MDAgaG9yYXMgaW52aWVybm87IDg6MzAgYSAyMDowMCBob3JhcyB2ZXJhbm9kZAITD2QWCAIBDw8WAh8BBR9BdmlzbyBzb2JyZSB2aXNpdGFzIGNvbiBtZW5vcmVzZGQCAw8PFgIfAQX2AVNpIHZhIGEgcmVhbGl6YXIgbGEgdmlzaXRhIGNvbiBtZW5vcmVzIGRlIDMgYSAxMSBhw7Fvcywgw6lzdG9zIHByZWNpc2FuIGRlIHN1IGVudHJhZGEgY29ycmVzcG9uZGllbnRlLg0KUG9yIGZhdm9yIHNlbGVjY2nDs25lbGEgZW4gc3UgY29tcHJhOiBMYXMgZW50cmFkYXMgZGUgbWVub3JlcyBkZSAzIGHDsW9zIHNlcsOhbiBmYWNpbGl0YWRhcyBlbiBsYXMgdGFxdWlsbGFzIGRlbCBtb251bWVudG8uIMK/RGVzZWEgY29udGludWFyP2RkAgUPDxYCHwEFAlNpZGQCBw8PFgIfAQUCTm9kZAIUD2QWBAIBDw8WAh8BBRZBVklTTyBEQVRPUyBWSVNJVEFOVEVTZGQCAw8PFgIfAQVcQ29tcHJ1ZWJlIHF1ZSBsb3MgZGF0b3MgZGUgdmlzaXRhbnRlcyBzb24gY29ycmVjdG9zLCBhc8OtIGNvbW8gbGEgZmVjaGEgeSBob3JhIHNlbGVjY2lvbmFkYS5kZAICDw8WAh8GaGRkAg4PFgQfAQW/HTxmb290ZXIgY2xhc3M9ImZvb3RlciI+DQogIDxkaXYgaWQ9ImRpdkZvb3RlcjIiIGNsYXNzPSJmb290ZXIyIj4NCiAgICA8ZGl2IGNsYXNzPSJjb250YWluZXIiPg0KICAgICAgPGRpdiBjbGFzcz0ibG9nbyAiPg0KICAgICAgICAgIDxhIGhyZWY9Imh0dHA6Ly93d3cuYWxoYW1icmEtcGF0cm9uYXRvLmVzLyIgdGFyZ2V0PSJfYmxhbmsiPjxpbWcgaWQ9ImltZ0Zvb3RlciIgc3JjPSIvQXBwX1RoZW1lcy9BTEhBTUJSQS9pbWcvbG9nby1mb290ZXIucG5nIiBhbHQ9IkFsaGFtYnJhIHkgR2VuZXJhbGlmZSI+PC9hPg0KICAgICAgICA8L2Rpdj4NCiAgICAgIDxkaXYgY2xhc3M9InJvdyI+DQogICAgICAgICA8ZGl2IGNsYXNzPSJmb290ZXItaXRlbSBjb2x1bW4tMSI+DQogICAgICAgICAgPHVsPg0KICAgICAgICAgICAgPGxpPjxhIGNsYXNzPSJsaW5rcy1pdGVtIiBocmVmPSJodHRwczovL3RpY2tldHMuYWxoYW1icmEtcGF0cm9uYXRvLmVzL3RlLXB1ZWRlLWF5dWRhci8iIHRhcmdldD0iX2JsYW5rIj5MRSBQVUVETyBBWVVEQVI8L2E+PC9saT4NCiAgICAgICAgICAgIDxsaT48YSBjbGFzcz0ibGlua3MtaXRlbSIgaHJlZj0iaHR0cHM6Ly90aWNrZXRzLmFsaGFtYnJhLXBhdHJvbmF0by5lcy9wb2xpdGljYS1kZS1jb21wcmEvIiB0YXJnZXQ9Il9ibGFuayI+UE9Mw41USUNBIERFIENPTVBSQVM8L2E+PC9saT4NCiAgICAgICAgICAgIDxsaT48YSBjbGFzcz0ibGlua3MtaXRlbSIgaHJlZj0iL3BvbGl0aWNhLWNvb2tpZXMuYXNweCIgdGFyZ2V0PSJfYmxhbmsiPlBPTMONVElDQSBERSBDT09LSUVTPC9hPjwvbGk+DQogICAgICAgICAgICA8bGk+PGEgY2xhc3M9ImxpbmtzLWl0ZW0iIGhyZWY9ImphdmFzY3JpcHQ6dm9pZCgwKSIgIG9uQ2xpY2s9IlJlY29uZmlndXJhckNvb2tpZXMoKSI+Q2FuY2VsYXIgLyBjb25maWd1cmFyIHBvbGl0aWNhIGRlIGNvb2tpZXM8L2E+PC9saT4NCiAgICAgICAgICAgIDxsaT48YSBjbGFzcz0ibGlua3MtaXRlbSIgaHJlZj0iaHR0cHM6Ly90aWNrZXRzLmFsaGFtYnJhLXBhdHJvbmF0by5lcy9wb2xpdGljYS1kZS1wcml2YWNpZGFkIiB0YXJnZXQ9Il9ibGFuayI+UE9Mw41USUNBIERFIFBSSVZBQ0lEQUQ8L2E+PC9saT4NCiAgICAgICAgICAgIDxsaT48YSBjbGFzcz0ibGlua3MtaXRlbSIgaHJlZj0iaHR0cHM6Ly90aWNrZXRzLmFsaGFtYnJhLXBhdHJvbmF0by5lcy9hdmlzby1sZWdhbC8iIHRhcmdldD0iX2JsYW5rIj5BVklTTyBMRUdBTDwvYT48L2xpPg0KICAgICAgICAgICAgPGxpPjxwIGNsYXNzPSJsaW5rcy1pdGVtIj5URUzDiUZPTk8gREVMIFZJU0lUQU5URSA8YSBocmVmPSJ0ZWw6KzM0ODU4ODg5MDAyIiBjbGFzcz0idGVsIj4rMzQgOTU4IDAyNyA5NzE8L2E+PC9wPjwvbGk+DQogICAgICAgICAgICA8bGk+PHAgY2xhc3M9ImxpbmtzLWl0ZW0iPlRFTMOJRk9OTyBERSBTT1BPUlRFIEEgTEEgVkVOVEEgREUgRU5UUkFEQVMgPGEgaHJlZj0idGVsOiszNDg1ODg4OTAwMiIgY2xhc3M9InRlbCI+KzM0ODU4ODg5MDAyPC9hPjwvcD48L2xpPg0KPGxpPjxwIGNsYXNzPSJsaW5rcy1pdGVtIj5DT1JSRU8gRUxFQ1RSw5NOSUNPIERFIFNPUE9SVEUgQSBMQSBWRU5UQSBERSBFTlRSQURBUyA8YSBocmVmPSJtYWlsdG86dGlja2V0cy5hbGhhbWJyYUBpYWNwb3MuY29tIiBjbGFzcz0idGVsIj50aWNrZXRzLmFsaGFtYnJhQGlhY3Bvcy5jb208L2E+PC9wPjwvbGk+DQogICAgICAgICAgPC91bD4NCiAgICAgICAgIDwvZGl2Pg0KICAgICAgPC9kaXY+DQogICAgICA8IS0tIENvbnRhY3RvIHkgUlJTUyAtLT4NCiAgICAgIDxkaXYgY2xhc3M9ImZvb3RlcjQiPg0KICAgICAgICA8ZGl2IGNsYXNzPSJmb2xsb3ciPg0KICAgICAgICAgIDxwPlPDrWd1ZW5vcyBlbjo8L3A+DQogICAgICAgICAgPHVsIGNsYXNzPSJzb2NpYWwiPg0KICAgICAgICAgICAgPGxpIGlkPSJsaUZhY2Vib29rIj4NCiAgICAgICAgICAgICAgPGEgaWQ9ImxpbmtGYWNlYm9vayIgY2xhc3M9Imljb24gaWNvbi1mYWNlYm9vayIgdGl0bGU9IkZhY2Vib29rIiBocmVmPSJodHRwczovL3d3dy5mYWNlYm9vay5jb20vYWxoYW1icmFjdWx0dXJhIiB0YXJnZXQ9Il9ibGFuayI+PC9hPg0KICAgICAgICAgICAgPC9saT4NCiAgICAgICAgICAgIDxsaSBpZD0ibGlUd2l0ZXIiPg0KICAgICAgICAgICAgICA8YSBpZD0ibGlua1R3aXR0ZXIiIGNsYXNzPSJpY29uIGljb24tdHdpdHRlciIgdGl0bGU9IlR3aXR0ZXIiIGhyZWY9Imh0dHA6Ly93d3cudHdpdHRlci5jb20vYWxoYW1icmFjdWx0dXJhIiB0YXJnZXQ9Il9ibGFuayI+PC9hPg0KICAgICAgICAgICAgPC9saT4NCiAgICAgICAgICAgIDxsaSBpZD0ibGlZb3VUdWJlIj4NCiAgICAgICAgICAgICAgPGEgaWQ9ImxpbmtZb3VUdWJlIiBjbGFzcz0iaWNvbiBpY29uLXlvdXR1YmUiIHRpdGxlPSJZb3V0dWJlIiBocmVmPSJodHRwOi8vd3d3LnlvdXR1YmUuY29tL2FsaGFtYnJhcGF0cm9uYXRvIiB0YXJnZXQ9Il9ibGFuayI+PC9hPg0KICAgICAgICAgICAgPC9saT4NCiAgICAgICAgICAgIDxsaSBpZD0ibGlJbnN0YWdyYW0iPg0KICAgICAgICAgICAgICA8YSBpZD0ibGlua0ludGFncmFtIiBjbGFzcz0iaWNvbiBpY29uLWluc3RhZ3JhbSIgdGl0bGU9Ikluc3RhZ3JhbSIgaHJlZj0iaHR0cHM6Ly93d3cuaW5zdGFncmFtLmNvbS9hbGhhbWJyYV9vZmljaWFsLyIgdGFyZ2V0PSJfYmxhbmsiPjwvYT4NCiAgICAgICAgICAgIDwvbGk+DQogICAgICAgICAgICA8bGkgaWQ9ImxpUGludGVyZXN0Ij4NCiAgICAgICAgICAgICAgPGEgaWQ9ImxpbmtQaW50ZXJlc3QiIGNsYXNzPSJpY29uIGljb24tcGludGVyZXN0IiB0aXRsZT0iUGludGVyZXN0IiBocmVmPSJodHRwczovL2VzLnBpbnRlcmVzdC5jb20vYWxoYW1icmFncmFuYWRhLyIgdGFyZ2V0PSJfYmxhbmsiPjwvYT4NCiAgICAgICAgICAgIDwvbGk+DQogICAgICAgICAgPC91bD4NCiAgICAgICAgPC9kaXY+DQogICAgICAgIDwhLS0gLy9Db250YWN0byB5IFJSU1MgLS0+DQogICAgICA8L2Rpdj4NCiAgICA8L2Rpdj4NCiAgPC9kaXY+DQogIDxkaXYgaWQ9ImRpdkZvb3RlcjMiIGNsYXNzPSJmb290ZXIzIj4NCiAgICA8ZGl2IGNsYXNzPSJjb250YWluZXIiPg0KICAgICAgPGRpdiBjbGFzcz0iZm9vdGVyLWl0ZW0gY29sdW1uLTEiPg0KICAgICAgICA8ZGl2IGNsYXNzPSJsb2dvIGxvZ29Gb290ZXIiPg0KICAgICAgICAgIDxhIGhyZWY9Imh0dHA6Ly93d3cuYWxoYW1icmEtcGF0cm9uYXRvLmVzLyIgdGFyZ2V0PSJfYmxhbmsiPg0KICAgICAgICAgICAgPGltZyBpZD0iaW1nRm9vdGVyIiBzcmM9Ii9BcHBfVGhlbWVzL0FMSEFNQlJBL2ltZy9sb2dvX3BhdHJvbmF0by5wbmciIGFsdD0iQWxoYW1icmEgeSBHZW5lcmFsaWZlIj4NCiAgICAgICAgICA8L2E+DQogICAgICA8L2Rpdj4NCiAgICAgICAgPHAgY2xhc3M9ImRlc2lnbiI+DQogICAgICAgICAgPHNwYW4gaWQ9ImRldmVsb3BlZCI+Q29weXJpZ2h0IMKpIElBQ1BPUzwvc3Bhbj4NCiAgICAgICAgPC9wPg0KICAgICAgPC9kaXY+DQogICAgICA8ZGl2IGlkPSJkaXZEaXJlY2Npb25Gb290ZXIiIGNsYXNzPSJkaXJlY2Npb24gZm9vdGVyLWl0ZW0gY29sdW1uLTEiPg0KICAgICAgICA8cD5QYXRyb25hdG8gZGUgbGEgQWxoYW1icmEgeSBHZW5lcmFsaWZlPC9wPg0KICAgICAgICAgICAgICAgICAgICA8cD5DLyBSZWFsIGRlIGxhIEFsaGFtYnJhIHMvbjwvcD4NCiAgICAgICAgICAgICAgICAgICAgPHA+Q1AgLSAxODAwOSAoR3JhbmFkYSk8L3A+DQogICAgICA8L2Rpdj4NCiAgICA8L2Rpdj4NCiAgPC9kaXY+DQo8L2Zvb3Rlcj4fBmdkAg8PFgIfBmgWFAICD2QWCgIBD2QWAgIBDw8WAh8DBShodHRwczovL3d3dy5mYWNlYm9vay5jb20vYWxoYW1icmFjdWx0dXJhZGQCAg9kFgICAQ8PFgIfAwUmaHR0cDovL3d3dy50d2l0dGVyLmNvbS9hbGhhbWJyYWN1bHR1cmFkZAIDD2QWAgIBDw8WAh8DBShodHRwOi8vd3d3LnlvdXR1YmUuY29tL2FsaGFtYnJhcGF0cm9uYXRvZGQCBA9kFgICAQ8PFgIfAwUraHR0cHM6Ly93d3cuaW5zdGFncmFtLmNvbS9hbGhhbWJyYV9vZmljaWFsL2RkAgUPZBYCAgEPDxYCHwMFKWh0dHBzOi8vZXMucGludGVyZXN0LmNvbS9hbGhhbWJyYWdyYW5hZGEvZGQCAw9kFgYCAQ9kFgJmDw8WBB8EBSgvQXBwX1RoZW1lcy9BTEhBTUJSQS9pbWcvbG9nby1mb290ZXIucG5nHwUFFUFsaGFtYnJhIHkgR2VuZXJhbGlmZWRkAgMPFgIfBwWUATxwPlBhdHJvbmF0byBkZSBsYSBBbGhhbWJyYSB5IEdlbmVyYWxpZmU8L3A+DQogICAgICAgICAgICAgICAgICAgIDxwPkMvIFJlYWwgZGUgbGEgQWxoYW1icmEgcy9uPC9wPg0KICAgICAgICAgICAgICAgICAgICA8cD5DUCAtIDE4MDA5IChHcmFuYWRhKTwvcD5kAgUPDxYCHwEFE0NvcHlyaWdodCDCqSBJQUNQT1NkZAIEDw8WAh8DBShodHRwczovL3d3dy5mYWNlYm9vay5jb20vYWxoYW1icmFjdWx0dXJhZGQCBQ8PFgIfAwUmaHR0cDovL3d3dy50d2l0dGVyLmNvbS9hbGhhbWJyYWN1bHR1cmFkZAIGDw8WAh8DBStodHRwczovL3d3dy5pbnN0YWdyYW0uY29tL2FsaGFtYnJhX29maWNpYWwvZGQCBw8PFgIfAwUoaHR0cDovL3d3dy55b3V0dWJlLmNvbS9hbGhhbWJyYXBhdHJvbmF0b2RkAggPDxYCHwNkZGQCCQ8PFgIfA2RkZAIKDxYCHwcFlAE8cD5QYXRyb25hdG8gZGUgbGEgQWxoYW1icmEgeSBHZW5lcmFsaWZlPC9wPg0KICAgICAgICAgICAgICAgICAgICA8cD5DLyBSZWFsIGRlIGxhIEFsaGFtYnJhIHMvbjwvcD4NCiAgICAgICAgICAgICAgICAgICAgPHA+Q1AgLSAxODAwOSAoR3JhbmFkYSk8L3A+ZAILDw8WAh8BBRNDb3B5cmlnaHQgwqkgSUFDUE9TZGQCEQ8PFgIfBmhkFgQCAQ9kFgQCAQ8WAh8BBccEPHAgPkVsIHJlc3BvbnNhYmxlIGRlIGVzdGUgc2l0aW8gd2ViIGZpZ3VyYSBlbiBudWVzdHJvICA8YSBocmVmPSJodHRwczovL3RpY2tldHMuYWxoYW1icmEtcGF0cm9uYXRvLmVzL2F2aXNvLWxlZ2FsLyIgPkF2aXNvIExlZ2FsIDwvYSA+LiA8YnIgLyA+VXRpbGl6YW1vcyBjb29raWVzIHByb3BpYXMgeSBvcGNpb25hbG1lbnRlIHBvZGVtb3MgdXRpbGl6YXIgY29va2llcyBkZSB0ZXJjZXJvcy4gTGEgZmluYWxpZGFkIGRlIGxhcyBjb29raWVzIHV0aWxpemFkYXMgZXM6IGZ1bmNpb25hbGVzLCBhbmFsw610aWNhcyB5IHB1YmxpY2l0YXJpYXMuIE5vIHNlIHVzYW4gcGFyYSBsYSBlbGFib3JhY2nDs24gZGUgcGVyZmlsZXMuIFVzdGVkIHB1ZWRlIGNvbmZpZ3VyYXIgZWwgdXNvIGRlIGNvb2tpZXMgZW4gZXN0ZSBtZW51LiA8YnIgLyA+UHVlZGUgb2J0ZW5lciBtw6FzIGluZm9ybWFjacOzbiwgbyBiaWVuIGNvbm9jZXIgY8OzbW8gY2FtYmlhciBsYSBjb25maWd1cmFjacOzbiwgZW4gbnVlc3RyYSA8YnIgLyA+IDxhIGhyZWY9Ii9wb2xpdGljYS1jb29raWVzLmFzcHgiID5Qb2zDrXRpY2EgZGUgY29va2llcyA8L2EgPi48L3AgPmQCAw8PFgIfAQUYQWNlcHRhciB0b2RvIHkgY29udGludWFyZGQCAw9kFggCAQ8PFgIfBmhkZAIDDxYCHwEFxwQ8cCA+RWwgcmVzcG9uc2FibGUgZGUgZXN0ZSBzaXRpbyB3ZWIgZmlndXJhIGVuIG51ZXN0cm8gIDxhIGhyZWY9Imh0dHBzOi8vdGlja2V0cy5hbGhhbWJyYS1wYXRyb25hdG8uZXMvYXZpc28tbGVnYWwvIiA+QXZpc28gTGVnYWwgPC9hID4uPGJyIC8gPiBVdGlsaXphbW9zIGNvb2tpZXMgcHJvcGlhcyB5IG9wY2lvbmFsbWVudGUgcG9kZW1vcyB1dGlsaXphciBjb29raWVzIGRlIHRlcmNlcm9zLiBMYSBmaW5hbGlkYWQgZGUgbGFzIGNvb2tpZXMgdXRpbGl6YWRhcyBlczogZnVuY2lvbmFsZXMsIGFuYWzDrXRpY2FzIHkgcHVibGljaXRhcmlhcy4gTm8gc2UgdXNhbiBwYXJhIGxhIGVsYWJvcmFjacOzbiBkZSBwZXJmaWxlcy4gVXN0ZWQgcHVlZGUgY29uZmlndXJhciBlbCB1c28gZGUgY29va2llcyBlbiBlc3RlIG1lbnUuIDxiciAvID5QdWVkZSBvYnRlbmVyIG3DoXMgaW5mb3JtYWNpw7NuLCBvIGJpZW4gY29ub2NlciBjw7NtbyBjYW1iaWFyIGxhIGNvbmZpZ3VyYWNpw7NuLCBlbiBudWVzdHJhIDxiciAvID4gPGEgaHJlZj0iL3BvbGl0aWNhLWNvb2tpZXMuYXNweCIgPlBvbMOtdGljYSBkZSBjb29raWVzIDwvYSA+LjwvcCA+ZAIHDw8WAh8BBRhBY2VwdGFyIHRvZG8geSBjb250aW51YXJkZAIJDw8WAh8BBSBBY2VwdGFyIHNlbGVjY2lvbmFkbyB5IGNvbnRpbnVhcmRkAgMPFgQfAQXiATwhLS0gU3RhcnQgb2YgY2F1YWxoYW1icmEgWmVuZGVzayBXaWRnZXQgc2NyaXB0IC0tPg0KPHNjcmlwdCBpZD0iemUtc25pcHBldCIgc3JjPWh0dHBzOi8vc3RhdGljLnpkYXNzZXRzLmNvbS9la3Ivc25pcHBldC5qcz9rZXk9NWI3YWUxMjktOWEzYy00ZDJmLWI5NDQtMTQ3MmRmOWZiNTMzPiA8L3NjcmlwdD4NCjwhLS0gRW5kIG9mIGNhdWFsaGFtYnJhIFplbmRlc2sgV2lkZ2V0IHNjcmlwdCAtLT4fBmdkGAMFHl9fQ29udHJvbHNSZXF1aXJlUG9zdEJhY2tLZXlfXxYBBR9jdGwwMCRjaGtSZWdpc3Ryb0FjZXB0b1BvbGl0aWNhBUdjdGwwMCRDb250ZW50TWFzdGVyMSR1Y1Jlc2VydmFyRW50cmFkYXNCYXNlQWxoYW1icmExJHVjSW1wb3J0YXIkV2l6YXJkMQ8QZBQrAQFmZmQFV2N0bDAwJENvbnRlbnRNYXN0ZXIxJHVjUmVzZXJ2YXJFbnRyYWRhc0Jhc2VBbGhhbWJyYTEkdWNJbXBvcnRhciRXaXphcmQxJFdpemFyZE11bHRpVmlldw8PZGZkIAUHlIs4qU7d587zYXSL0GPQp68="
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
                    WebDriverWait(driver, 2).until(
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
                    viewstate_funcional = "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OTUyZxAFBDE5NTMFBDE5NTNnEAUEMTk1NAUEMTk1NGcQBQQxOTU1BQQxOTU1ZxAFBDE5NTYFBDE5NTZnEAUEMTk1NwUEMTk1N2cQBQQxOTU4BQQxOTU4ZxAFBDE5NTkFBDE5NTlnEAUEMTk2MAUEMTk2MGcQBQQxOTYxBQQxOTYxZxAFBDE5NjIFBDE5NjJnEAUEMTk2MwUEMTk2M2cQBQQxOTY0BQQxOTY0ZxAFBDE5NjUFBDE5NjVnEAUEMTk2NgUEMTk2NmcQBQQxOTY3BQQxOTY3ZxAFBDE5NjgFBDE5NjhnEAUEMTk2OQUEMTk2OWcQBQQxOTcwBQQxOTcwZxAFBDE5NzEFBDE5NzFnEAUEMTk3MgUEMTk3MmcQBQQxOTczBQQxOTczZxAFBDE5NzQFBDE5NzRnEAUEMTk3NQUEMTk3NWcQBQQxOTc2BQQxOTc2ZxAFBDE5NzcFBDE5NzdnEAUEMTk3OAUEMTk3OGcQBQQxOTc5BQQxOTc5ZxAFBDE5ODAFBDE5ODBnEAUEMTk4MQUEMTk4MWcQBQQxOTgyBQQxOTgyZxAFBDE5ODMFBDE5ODNnEAUEMTk4NAUEMTk4NGcQBQQxOTg1BQQxOTg1ZxAFBDE5ODYFBDE5ODZnEAUEMTk4NwUEMTk4N2cQBQQxOTg4BQQxOTg4ZxAFBDE5ODkFBDE5ODlnEAUEMTk5MAUEMTk5MGcQBQQxOTkxBQQxOTkxZxAFBDE5OTIFBDE5OTJnEAUEMTk5MwUEMTk5M2cQBQQxOTk0BQQxOTk0ZxAFBDE5OTUFBDE5OTVnEAUEMTk5NgUEMTk5NmcQBQQxOTk3BQQxOTk3ZxAFBDE5OTgFBDE5OThnEAUEMTk5OQUEMTk5OWcQBQQyMDAwBQQyMDAwZxAFBDIwMDEFBDIwMDFnEAUEMjAwMgUEMjAwMmcQBQQyMDAzBQQyMDAzZxAFBDIwMDQFBDIwMDRnEAUEMjAwNQUEMjAwNWcQBQQyMDA2BQQyMDA2ZxAFBDIwMDcFBDIwMDdnEAUEMjAwOAUEMjAwOGcQBQQyMDA5BQQyMDA5ZxAFBDIwMTAFBDIwMTBnEAUEMjAxMQUEMjAxMWcQBQQyMDEyBQQyMDEyZxAFBDIwMTMFBDIwMTNnEAUEMjAxNAUEMjAxNGcQBQQyMDE1BQQyMDE1ZxAFBDIwMTYFBDIwMTZnEAUEMjAxNwUEMjAxN2cQBQQyMDE4BQQyMDE4ZxAFBDIwMTkFBDIwMTlnEAUEMjAyMAUEMjAyMGcQBQQyMDIxBQQyMDIxZxAFBDIwMjIFBDIwMjJnEAUEMjAyMwUEMjAyM2cQBQQyMDI0BQQyMDI0ZxAFBDIwMjUFBDIwMjVnFgFmZAILDxYCHwZoFgICAQ8WAh8HZGQCDA9kFgICAQ8WAh8HBQVFbWFpbGQCDQ9kFgICAQ8WAh8HBQ5Db25maXJtYSBFbWFpbGQCDg9kFgICAQ8WAh8HBQtDb250cmFzZcOxYWQCDw9kFgICAQ8WAh8HBRNSZXBldGlyIENvbnRyYXNlw7FhZAIQDxYCHwZoFgICAQ8WAh8HZWQCEQ8WAh8GaBYCAgEPFgIfB2VkAhIPFgIfBmgWAgIBDxYCHwdlZAITDxYCHwZoFgYCAQ8WAh8HZWQCAw8PFgQeCENzc0NsYXNzBRJpbnB1dC10ZXh0IG9jdWx0YXIeBF8hU0ICAmRkAgUPEA8WBB8JZR8KAgJkEBU1FFNlbGVjY2lvbmUgcHJvdmluY2lhCEFsYmFjZXRlCEFsaWNhbnRlCEFsbWVyw61hBsOBbGF2YQhBc3R1cmlhcwbDgXZpbGEHQmFkYWpveg1CYWxlYXJzIElsbGVzCUJhcmNlbG9uYQdCaXprYWlhBkJ1cmdvcwhDw6FjZXJlcwZDw6FkaXoJQ2FudGFicmlhCkNhc3RlbGzDs24LQ2l1ZGFkIFJlYWwIQ8OzcmRvYmEJQ29ydcOxYSBBBkN1ZW5jYQhHaXB1emtvYQZHaXJvbmEHR3JhbmFkYQtHdWFkYWxhamFyYQZIdWVsdmEGSHVlc2NhBUphw6luBUxlw7NuBkxsZWlkYQRMdWdvBk1hZHJpZAdNw6FsYWdhBk11cmNpYQdOYXZhcnJhB091cmVuc2UIUGFsZW5jaWEKUGFsbWFzIExhcwpQb250ZXZlZHJhCFJpb2phIExhCVNhbGFtYW5jYRZTYW50YSBDcnV6IGRlIFRlbmVyaWZlB1NlZ292aWEHU2V2aWxsYQVTb3JpYQlUYXJyYWdvbmEGVGVydWVsBlRvbGVkbwhWYWxlbmNpYQpWYWxsYWRvbGlkBlphbW9yYQhaYXJhZ296YQVDZXV0YQdNZWxpbGxhFTUAAjAyAjAzAjA0AjAxAjMzAjA1AjA2AjA3AjA4AjQ4AjA5AjEwAjExAjM5AjEyAjEzAjE0AjE1AjE2AjIwAjE3AjE4AjE5AjIxAjIyAjIzAjI0AjI1AjI3AjI4AjI5AjMwAjMxAjMyAjM0AjM1AjM2AjI2AjM3AjM4AjQwAjQxAjQyAjQzAjQ0AjQ1AjQ2AjQ3AjQ5AjUwAjUxAjUyFCsDNWdnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnFgFmZAIUD2QWBgIBDxYCHwcFBVBhw61zZAIDDw8WAh8GaGRkAgUPEGQQFe8BE1NlbGVjY2lvbmUgdW4gcGHDrXMJQXJnZW50aW5hCUF1c3RyYWxpYQVDaGluYQVJdGFseQVKYXBhbgZNZXhpY28LTmV3IFplYWxhbmQIUG9ydHVnYWwHRXNwYcOxYQdHZXJtYW55BkZyYW5jZRJSdXNzaWFuIEZlZGVyYXRpb24OVW5pdGVkIEtpbmdkb20UVW5pdGVkIFN0YXRlcyBvZiBBbWULQWZnaGFuaXN0YW4HQWxiYW5pYQdBbGdlcmlhDkFtZXJpY2FuIFNhbW9hB0FuZG9ycmEGQW5nb2xhCEFuZ3VpbGxhCkFudGFyY3RpY2EHQW50aWd1YQdBcm1lbmlhBUFydWJhB0F1c3RyaWEKQXplcmJhaWphbgdCYWhhbWFzB0JhaHJhaW4KQmFuZ2xhZGVzaAhCYXJiYWRvcwdCZWxhcnVzB0JlbGdpdW0GQmVsaXplBUJlbmluB0Jlcm11ZGEGQmh1dGFuB0JvbGl2aWEGQm9zbmlhCEJvdHN3YW5hDUJvdXZldCBJc2xhbmQGQnJhemlsDkJyaXRpc2ggSW5kaWFuEUJydW5laSBEYXJ1c3NhbGFtCEJ1bGdhcmlhDEJ1cmtpbmEgRmFzbwdCdXJ1bmRpCENhbWJvZGlhCENhbWVyb29uBkNhbmFkYQpDYXBlIFZlcmRlDkNheW1hbiBJc2xhbmRzE0NlbnRyYWwgQWZyaWNhbiBSZXAEQ2hhZAVDaGlsZRBDaHJpc3RtYXMgSXNsYW5kDUNvY29zIElzbGFuZHMIQ29sb21iaWEHQ29tb3JvcwVDb25nbwxDb29rIElzbGFuZHMKQ29zdGEgUmljYQdDcm9hdGlhBEN1YmEGQ3lwcnVzDkN6ZWNoIFJlcHVibGljB0Rlbm1hcmsIRGppYm91dGkIRG9taW5pY2ESRG9taW5pY2FuIFJlcHVibGljCkVhc3QgVGltb3IHRWN1YWRvcgVFZ3lwdAtFbCBTYWx2YWRvchFFcXVhdG9yaWFsIEd1aW5lYQdFcml0cmVhB0VzdG9uaWEIRXRoaW9waWENRmFyb2UgSXNsYW5kcwRGaWppB0ZpbmxhbmQNRnJlbmNoIEd1aWFuYRBGcmVuY2ggUG9seW5lc2lhBUdhYm9uBkdhbWJpYQdHZW9yZ2lhBUdoYW5hBkdyZWVjZQlHcmVlbmxhbmQHR3JlbmFkYQpHdWFkZWxvdXBlBEd1YW0JR3VhdGVtYWxhBkd1aW5lYQ1HdWluZWEgQmlzc2F1Bkd1eWFuYQVIYWl0aQhIb25kdXJhcwlIb25nIEtvbmcHSHVuZ2FyeQdJY2VsYW5kBUluZGlhCUluZG9uZXNpYQRJcmFuBElyYXEHSXJlbGFuZAZJc3JhZWwLSXZvcnkgQ29hc3QHSmFtYWljYQZKb3JkYW4KS2F6YWtoc3RhbgVLZW55YQhLaXJpYmF0aQZLdXdhaXQKS3lyZ3l6c3RhbgNMYW8GTGF0dmlhB0xlYmFub24HTGVzb3RobwdMaWJlcmlhBUxpYnlhDUxpZWNodGVuc3RlaW4JTGl0aHVhbmlhCkx1eGVtYm91cmcFTWFjYXUJTWFjZWRvbmlhCk1hZGFnYXNjYXIGTWFsYXdpCE1hbGF5c2lhCE1hbGRpdmVzBE1hbGkFTWFsdGEITWFsdmluYXMQTWFyc2hhbGwgSXNsYW5kcwpNYXJ0aW5pcXVlCk1hdXJpdGFuaWEJTWF1cml0aXVzB01heW90dGUKTWljcm9uZXNpYQdNb2xkb3ZhBk1vbmFjbwhNb25nb2xpYQpNb250ZW5lZ3JvCk1vbnRzZXJyYXQHTW9yb2NjbwpNb3phbWJpcXVlB015YW5tYXIHTmFtaWJpYQVOYXVydQVOZXBhbAtOZXRoZXJsYW5kcxROZXRoZXJsYW5kcyBBbnRpbGxlcw1OZXcgQ2FsZWRvbmlhCU5pY2FyYWd1YQVOaWdlcgdOaWdlcmlhBE5pdWUOTm9yZm9sayBJc2xhbmQLTm9ydGggS29yZWETTm9ydGhlcm4gTWFyaWFuYSBJcwZOb3J3YXkET21hbhlPdHJvcyBkZSBwYWlzZXMgZGVsIG11bmRvCFBha2lzdGFuBVBhbGF1BlBhbmFtYRBQYXB1YSBOZXcgR3VpbmVhCFBhcmFndWF5BFBlcnULUGhpbGlwcGluZXMIUGl0Y2Fpcm4GUG9sYW5kC1B1ZXJ0byBSaWNvBVFhdGFyB1JldW5pb24HUm9tYW5pYQZSd2FuZGEPUyBHZW9yZ2lhIFNvdXRoC1NhaW50IEx1Y2lhBVNhbW9hClNhbiBNYXJpbm8TU2FvIFRvbWUgLSBQcmluY2lwZQxTYXVkaSBBcmFiaWEHU2VuZWdhbAZTZXJiaWEKU2V5Y2hlbGxlcwxTaWVycmEgTGVvbmUJU2luZ2Fwb3JlCFNsb3Zha2lhCFNsb3ZlbmlhD1NvbG9tb24gSXNsYW5kcwdTb21hbGlhDFNvdXRoIEFmcmljYQtTb3V0aCBLb3JlYQlTcmkgTGFua2EJU3QgSGVsZW5hElN0IEtpdHRzIGFuZCBOZXZpcxNTdCBQaWVycmUgIE1pcXVlbG9uEVN0IFZpbmNlbnQtR3JlbmFkBVN1ZGFuCFN1cmluYW1lEVN2YWxiYXJkIEphbiBNIElzCVN3YXppbGFuZAZTd2VkZW4LU3dpdHplcmxhbmQFU3lyaWEGVGFpd2FuClRhamlraXN0YW4IVGFuemFuaWEIVGhhaWxhbmQEVG9nbwdUb2tlbGF1BVRvbmdhE1RyaW5pZGFkIEFuZCBUb2JhZ28HVHVuaXNpYQZUdXJrZXkMVHVya21lbmlzdGFuFFR1cmtzIENhaWNvcyBJc2xhbmRzBlR1dmFsdQZVZ2FuZGEHVWtyYWluZRRVbml0ZWQgQXJhYiBFbWlyYXRlcwdVcnVndWF5EFVTIE1pbm9yIElzbGFuZHMKVXpiZWtpc3RhbgdWYW51YXR1B1ZhdGljYW4JVmVuZXp1ZWxhB1ZpZXRuYW0OVmlyZ2luIElzbGFuZHMRVmlyZ2luIElzbGFuZHMgVVMQV2FsbGlzIEZ1dHVuYSBJcw5XZXN0ZXJuIFNhaGFyYQVZZW1lbgpZdWdvc2xhdmlhBVphaXJlBlphbWJpYQhaaW1iYWJ3ZRXvAQADMDMyAzAzNgMxNTYDMzgwAzM5MgM0ODQDNTU0AzYyMAM3MjQDMjc2AzI1MAM2NDMDODI2Azg0MAMwMDQDMDA4AzAxMgMwMTYDMDIwAzAyNAM2NjADMDEwAzAyOAMwNTEDNTMzAzA0MAMwMzEDMDQ0AzA0OAMwNTADMDUyAzExMgMwNTYDMDg0AzIwNAMwNjADMDY0AzA2OAMwNzADMDcyAzA3NAMwNzYDMDg2AzA5NgMxMDADODU0AzEwOAMxMTYDMTIwAzEyNAMxMzIDMTM2AzE0MAMxNDgDMTUyAzE2MgMxNjYDMTcwAzE3NAMxNzgDMTg0AzE4OAMxOTEDMTkyAzE5NgMyMDMDMjA4AzI2MgMyMTIDMjE0AzYyNgMyMTgDODE4AzIyMgMyMjYDMjMyAzIzMwMyMzEDMjM0AzI0MgMyNDYDMjU0AzI1OAMyNjYDMjcwAzI2OAMyODgDMzAwAzMwNAMzMDgDMzEyAzMxNgMzMjADMzI0AzYyNAMzMjgDMzMyAzM0MAMzNDQDMzQ4AzM1MgMzNTYDMzYwAzM2NAMzNjgDMzcyAzM3NgMzODQDMzg4AzQwMAMzOTgDNDA0AzI5NgM0MTQDNDE3AzQxOAM0MjgDNDIyAzQyNgM0MzADNDM0AzQzOAM0NDADNDQyAzQ0NgM4MDcDNDUwAzQ1NAM0NTgDNDYyAzQ2NgM0NzADMjM4AzU4NAM0NzQDNDc4AzQ4MAMxNzUDNTgzAzQ5OAM0OTIDNDk2AzQ5OQM1MDADNTA0AzUwOAMxMDQDNTE2AzUyMAM1MjQDNTI4AzUzMAM1NDADNTU4AzU2MgM1NjYDNTcwAzU3NAM0MDgDNTgwAzU3OAM1MTIDNzQ0AzU4NgM1ODUDNTkxAzU5OAM2MDADNjA0AzYwOAM2MTIDNjE2AzYzMAM2MzQDNjM4AzY0MgM2NDYDMjM5AzY2MgM4ODIDNjc0AzY3OAM2ODIDNjg2AzY4OAM2OTADNjk0AzcwMgM3MDMDNzA1AzA5MAM3MDYDNzEwAzQxMAMxNDQDNjU0AzY1OQM2NjYDNjcwAzczNgM3NDADNzQ0Azc0OAM3NTIDNzU2Azc2MAMxNTgDNzYyAzgzNAM3NjQDNzY4Azc3MgM3NzYDNzgwAzc4OAM3OTIDNzk1Azc5NgM3OTgDODAwAzgwNAM3ODQDODU4AzU4MQM4NjADNTQ4AzMzNgM4NjIDNzA0AzA5MgM4NTADODc2AzczMgM4ODcDODkxAzE4MAM4OTQDNzE2FCsD7wFnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2RkAhUPZBYCAgEPFgIfBwUJVGVsw6lmb25vZAIXD2QWAgIDDxYCHwcFiQFIZSBsZcOtZG8geSBhY2VwdG8gbGEgPGEgaHJlZj0iaHR0cHM6Ly90aWNrZXRzLmFsaGFtYnJhLXBhdHJvbmF0by5lcy9wb2xpdGljYS1kZS1wcml2YWNpZGFkLyIgdGFyZ2V0PSJfYmxhbmsiPlBvbMOtdGljYSBkZSBwcml2YWNpZGFkPC9hPmQCGA8WAh8GaBYCAgMPFgIfB2VkAggPDxYCHwEFC1JlZ8Otc3RyZXNlZGQCAw8WAh8GaBYEAgMPDxYCHwMFHi9yZXNlcnZhckVudHJhZGFzLmFzcHg/b3BjPTE0MmRkAgUPDxYCHwEFDkNlcnJhciBzZXNpw7NuZGQCAQ9kFgICAQ8PFgQfCQUGYWN0aXZlHwoCAmRkAgIPDxYEHwMFPmh0dHBzOi8vd3d3LmFsaGFtYnJhLXBhdHJvbmF0by5lcy92aXNpdGFyL3ByZWd1bnRhcy1mcmVjdWVudGVzHwZnZGQCBA9kFgICAQ8PFgIfAwUoaHR0cDovL3d3dy55b3V0dWJlLmNvbS9hbGhhbWJyYXBhdHJvbmF0b2RkAgUPZBYCAgEPDxYCHwMFK2h0dHBzOi8vd3d3Lmluc3RhZ3JhbS5jb20vYWxoYW1icmFfb2ZpY2lhbC9kZAIGD2QWAgIBDw8WAh8DBShodHRwczovL3d3dy5mYWNlYm9vay5jb20vYWxoYW1icmFjdWx0dXJhZGQCBw9kFgICAQ8PFgIfAwUmaHR0cDovL3d3dy50d2l0dGVyLmNvbS9hbGhhbWJyYWN1bHR1cmFkZAIID2QWAgIBDw8WAh8DBSlodHRwczovL2VzLnBpbnRlcmVzdC5jb20vYWxoYW1icmFncmFuYWRhL2RkAgkPFgIfBmhkAgoPFgIfBmgWAgIBDw8WAh8DZGQWAmYPDxYCHwUFFUFsaGFtYnJhIHkgR2VuZXJhbGlmZWRkAgsPZBYCZg8PFgQfAwU+aHR0cHM6Ly93d3cuYWxoYW1icmEtcGF0cm9uYXRvLmVzL3Zpc2l0YXIvcHJlZ3VudGFzLWZyZWN1ZW50ZXMfBmdkZAIND2QWCAIBDw8WAh8GaGQWAgIBD2QWAmYPZBYGAgMPDxYCHwZoZGQCBA8PFgIeBkVzdGFkb2ZkFgJmD2QWAgIBD2QWAmYPZBYCAgEPZBYCAggPFgIfBmhkAg4PZBYEAgsPZBYEAgEPZBYCAgMPEGRkFgBkAgYPZBYCAgcPEGRkFgBkAg0PZBYEAgYPZBYCAgEPZBYCAgMPEGRkFgBkAgkPZBYCAgcPEGRkFgBkAgMPDxYCHwZoZBYCZg9kFgJmD2QWBgIBDw8WAh8GaGRkAggPZBYGAgUPZBYCAgEPEGRkFgBkAgYPZBYCAgEPEGRkFgBkAggPZBYEZg8QZGQWAGQCAQ8QZGQWAGQCCg9kFgICBQ9kFg4CAw9kFgICBQ8QZGQWAGQCBA9kFgICAw8QZGQWAGQCBg9kFgICBw8QZGQWAGQCCA9kFgICBQ8QZGQWAGQCCQ9kFgICBQ8QZGQWAGQCDw9kFgICBw8QZGQWAGQCFg9kFgQCAQ9kFgICAw8QZGQWAGQCBg9kFgICBw8QZGQWAGQCBQ8PFgIfBmhkFgJmD2QWAmYPZBYEAgMPDxYCHwtmZBYCZg9kFgICAQ9kFgJmD2QWAgIBD2QWAgIIDxYCHwZoZAIGD2QWAmYPZBYCAgEPZBYCZg9kFgICAQ88KwAKAQAPFgQeDVByZXZNb250aFRleHRlHg1OZXh0TW9udGhUZXh0BS08aW1nIHNyYz0vQXBwX3RoZW1lcy9BTEhBTUJSQS9pbWcvbmV4dC5wbmcgLz5kZAIHDw8WIB4UTG9jYWxpemFkb3JQYXJhbWV0cm9kHhBGaW5hbGl6YXJNZW5vcmVzaB4OQWZvcm9QYXJhbWV0cm8CAR4GUGFnYWRhBQVGYWxzZR4HU2ltYm9sbwUD4oKsHhNFbmxhY2VNZW51UGFyYW1ldHJvBQdHRU5FUkFMHgxTZXNpb25EaWFyaWFoHgpOb21pbmFjaW9uZh4MQ2FwdGNoYVBhc28xZx4MTnVtRGVjaW1hbGVzAgIeD0NhcHRjaGFWYWxpZGFkb2ceCFNpbkZlY2hhZh4VRmVjaGFNaW5pbWFEaXNwb25pYmxlBv8/N/R1KMorHgxUZW5lbW9zTmlub3NoHhZHcnVwb0ludGVybmV0UGFyYW1ldHJvBQMxNDIeDFNlc2lvbkFjdHVhbAUfNG1vZXBsNDVubWZiYzNpMXhlbHlnZHVrMjcwMDg3NGQWBAIBD2QWAmYPZBYiAgMPDxYCHwZoZGQCBA8PFgIfC2ZkFgJmD2QWAgIBD2QWAmYPZBYCAgEPZBYGZg8PFgIfAQUFZW1haWxkZAICDw8WAh8BBQxUZWxlZm9ubyBTTVNkZAIIDxYCHwZoZAIFDw8WAh8DBTBodHRwczovL3d3dy5hbGhhbWJyYS1wYXRyb25hdG8uZXMvP2NhPTAmbGc9ZXMtRVNkZAIGDxYCHwFlZAIHDxYCHwEFF1Zpc2l0YSBBbGhhbWJyYSBHZW5lcmFsZAIIDxYCHgVjbGFzcwUWc3RlcC10aXRsZSBzdGVwLWFjdGl2ZRYCAgEPFgIfAWRkAgkPDxYCHwZoZBYCAgEPDxYCHwEFC0lyIGEgcGFzbyAxZGQCCg8PFgIfBmdkFghmDxYCHwFlZAIBDxYCHwFlZAIGDw8WHB4RRmVjaGFNaW5pbWFHbG9iYWwGgLdurmV43QgeBFBhc28CAR4NR3J1cG9JbnRlcm5ldAUDMTQyHhVUb3RhbE1lc2VzQWRlbGFudGFkb3MCAR4MRGF0b3NGZXN0aXZvMrsEAAEAAAD/////AQAAAAAAAAAMAgAAAEhBcHBfQ29kZS54aGpwdml6bywgVmVyc2lvbj0wLjAuMC4wLCBDdWx0dXJlPW5ldXRyYWwsIFB1YmxpY0tleVRva2VuPW51bGwFAQAAAB9EYXRvc0Zlc3Rpdm9zK0RhdG9zTGlzdEZlc3Rpdm9zAQAAABFfTHN0RGF0b3NGZXN0aXZvcwOJAVN5c3RlbS5Db2xsZWN0aW9ucy5HZW5lcmljLkxpc3RgMVtbRGF0b3NGZXN0aXZvcytEYXRvc0Zlc3Rpdm8sIEFwcF9Db2RlLnhoanB2aXpvLCBWZXJzaW9uPTAuMC4wLjAsIEN1bHR1cmU9bmV1dHJhbCwgUHVibGljS2V5VG9rZW49bnVsbF1dAgAAAAkDAAAABAMAAACJAVN5c3RlbS5Db2xsZWN0aW9ucy5HZW5lcmljLkxpc3RgMVtbRGF0b3NGZXN0aXZvcytEYXRvc0Zlc3Rpdm8sIEFwcF9Db2RlLnhoanB2aXpvLCBWZXJzaW9uPTAuMC4wLjAsIEN1bHR1cmU9bmV1dHJhbCwgUHVibGljS2V5VG9rZW49bnVsbF1dAwAAAAZfaXRlbXMFX3NpemUIX3ZlcnNpb24EAAAcRGF0b3NGZXN0aXZvcytEYXRvc0Zlc3Rpdm9bXQIAAAAICAkEAAAAAAAAAAAAAAAHBAAAAAABAAAAAAAAAAQaRGF0b3NGZXN0aXZvcytEYXRvc0Zlc3Rpdm8CAAAACx4TTWluaW1vR3J1cG9JbnRlcm5ldAIBHhFGZWNoYU1heGltYUdsb2JhbAYAusZyFKfeCB4PRGlyZWNjaW9uQWN0dWFsBQRQcmV2Hg1Fc0xpc3RhRXNwZXJhaB4LRm9yemFyQ2FyZ2FoHg5GZWNoYXNWaWdlbmNpYTKIDQABAAAA/////wEAAAAAAAAABAEAAADiAVN5c3RlbS5Db2xsZWN0aW9ucy5HZW5lcmljLkRpY3Rpb25hcnlgMltbU3lzdGVtLlN0cmluZywgbXNjb3JsaWIsIFZlcnNpb249NC4wLjAuMCwgQ3VsdHVyZT1uZXV0cmFsLCBQdWJsaWNLZXlUb2tlbj1iNzdhNWM1NjE5MzRlMDg5XSxbU3lzdGVtLlN0cmluZywgbXNjb3JsaWIsIFZlcnNpb249NC4wLjAuMCwgQ3VsdHVyZT1uZXV0cmFsLCBQdWJsaWNLZXlUb2tlbj1iNzdhNWM1NjE5MzRlMDg5XV0EAAAAB1ZlcnNpb24IQ29tcGFyZXIISGFzaFNpemUNS2V5VmFsdWVQYWlycwADAAMIkgFTeXN0ZW0uQ29sbGVjdGlvbnMuR2VuZXJpYy5HZW5lcmljRXF1YWxpdHlDb21wYXJlcmAxW1tTeXN0ZW0uU3RyaW5nLCBtc2NvcmxpYiwgVmVyc2lvbj00LjAuMC4wLCBDdWx0dXJlPW5ldXRyYWwsIFB1YmxpY0tleVRva2VuPWI3N2E1YzU2MTkzNGUwODldXQjmAVN5c3RlbS5Db2xsZWN0aW9ucy5HZW5lcmljLktleVZhbHVlUGFpcmAyW1tTeXN0ZW0uU3RyaW5nLCBtc2NvcmxpYiwgVmVyc2lvbj00LjAuMC4wLCBDdWx0dXJlPW5ldXRyYWwsIFB1YmxpY0tleVRva2VuPWI3N2E1YzU2MTkzNGUwODldLFtTeXN0ZW0uU3RyaW5nLCBtc2NvcmxpYiwgVmVyc2lvbj00LjAuMC4wLCBDdWx0dXJlPW5ldXRyYWwsIFB1YmxpY0tleVRva2VuPWI3N2E1YzU2MTkzNGUwODldXVtdBwAAAAkCAAAABwAAAAkDAAAABAIAAACSAVN5c3RlbS5Db2xsZWN0aW9ucy5HZW5lcmljLkdlbmVyaWNFcXVhbGl0eUNvbXBhcmVyYDFbW1N5c3RlbS5TdHJpbmcsIG1zY29ybGliLCBWZXJzaW9uPTQuMC4wLjAsIEN1bHR1cmU9bmV1dHJhbCwgUHVibGljS2V5VG9rZW49Yjc3YTVjNTYxOTM0ZTA4OV1dAAAAAAcDAAAAAAEAAAAHAAAAA+QBU3lzdGVtLkNvbGxlY3Rpb25zLkdlbmVyaWMuS2V5VmFsdWVQYWlyYDJbW1N5c3RlbS5TdHJpbmcsIG1zY29ybGliLCBWZXJzaW9uPTQuMC4wLjAsIEN1bHR1cmU9bmV1dHJhbCwgUHVibGljS2V5VG9rZW49Yjc3YTVjNTYxOTM0ZTA4OV0sW1N5c3RlbS5TdHJpbmcsIG1zY29ybGliLCBWZXJzaW9uPTQuMC4wLjAsIEN1bHR1cmU9bmV1dHJhbCwgUHVibGljS2V5VG9rZW49Yjc3YTVjNTYxOTM0ZTA4OV1dBPz////kAVN5c3RlbS5Db2xsZWN0aW9ucy5HZW5lcmljLktleVZhbHVlUGFpcmAyW1tTeXN0ZW0uU3RyaW5nLCBtc2NvcmxpYiwgVmVyc2lvbj00LjAuMC4wLCBDdWx0dXJlPW5ldXRyYWwsIFB1YmxpY0tleVRva2VuPWI3N2E1YzU2MTkzNGUwODldLFtTeXN0ZW0uU3RyaW5nLCBtc2NvcmxpYiwgVmVyc2lvbj00LjAuMC4wLCBDdWx0dXJlPW5ldXRyYWwsIFB1YmxpY0tleVRva2VuPWI3N2E1YzU2MTkzNGUwODldXQIAAAADa2V5BXZhbHVlAQEGBQAAAAM0MjYGBgAAABcjMTAvMDQvMjAyNS0zMC8wNC8yMDI1IwH5/////P///wYIAAAAAzQzMQYJAAAAFyMxMC8wNC8yMDI1LTMwLzA0LzIwMjUjAfb////8////BgsAAAADNDMwBgwAAAAXIzEwLzA0LzIwMjUtMzAvMDQvMjAyNSMB8/////z///8GDgAAAAM0MjcGDwAAABcjMTAvMDQvMjAyNS0zMC8wNC8yMDI1IwHw/////P///wYRAAAAAzQyOAYSAAAAFyMxMC8wNC8yMDI1LTMwLzA0LzIwMjUjAe3////8////BhQAAAADNDI5BhUAAAAXIzEwLzA0LzIwMjUtMzAvMDQvMjAyNSMB6v////z///8GFwAAAAM0ODUGGAAAABcjMTAvMDQvMjAyNS0zMC8wNC8yMDI1IwsfBmceEENhbnRpZGFkRW50cmFkYXMy2wQAAQAAAP////8BAAAAAAAAAAQBAAAA4QFTeXN0ZW0uQ29sbGVjdGlvbnMuR2VuZXJpYy5EaWN0aW9uYXJ5YDJbW1N5c3RlbS5TdHJpbmcsIG1zY29ybGliLCBWZXJzaW9uPTQuMC4wLjAsIEN1bHR1cmU9bmV1dHJhbCwgUHVibGljS2V5VG9rZW49Yjc3YTVjNTYxOTM0ZTA4OV0sW1N5c3RlbS5JbnQzMiwgbXNjb3JsaWIsIFZlcnNpb249NC4wLjAuMCwgQ3VsdHVyZT1uZXV0cmFsLCBQdWJsaWNLZXlUb2tlbj1iNzdhNWM1NjE5MzRlMDg5XV0DAAAAB1ZlcnNpb24IQ29tcGFyZXIISGFzaFNpemUAAwAIkgFTeXN0ZW0uQ29sbGVjdGlvbnMuR2VuZXJpYy5HZW5lcmljRXF1YWxpdHlDb21wYXJlcmAxW1tTeXN0ZW0uU3RyaW5nLCBtc2NvcmxpYiwgVmVyc2lvbj00LjAuMC4wLCBDdWx0dXJlPW5ldXRyYWwsIFB1YmxpY0tleVRva2VuPWI3N2E1YzU2MTkzNGUwODldXQgAAAAACQIAAAAAAAAABAIAAACSAVN5c3RlbS5Db2xsZWN0aW9ucy5HZW5lcmljLkdlbmVyaWNFcXVhbGl0eUNvbXBhcmVyYDFbW1N5c3RlbS5TdHJpbmcsIG1zY29ybGliLCBWZXJzaW9uPTQuMC4wLjAsIEN1bHR1cmU9bmV1dHJhbCwgUHVibGljS2V5VG9rZW49Yjc3YTVjNTYxOTM0ZTA4OV1dAAAAAAseF0Nh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Hx4FCnN0ZXAtdGl0bGUWAgIBDxYCHwFkZAIMDw8WAh8GaGQWDAIBDxYCHwFlZAIFDxYCHwZoZAIHD2QWCAIBDw8WAh8GaGQWAgIBD2QWAmYPZBYCAgEPPCsACgEADxYEHwxlHw0FLTxpbWcgc3JjPS9BcHBfdGhlbWVzL0FMSEFNQlJBL2ltZy9uZXh0LnBuZyAvPmRkAgMPFgIfBmgWAgIBDxBkZBYAZAIFDxYCHwZoFgICAQ8QZGQWAGQCCQ8PFgIfBmhkFgRmDxBkEBUIGFNlbGVjY2lvbmUgdW4gaXRpbmVyYXJpbyBWaXNpdGFzIEd1aWFkYXMgcG9yIGVsIE1vbnVtZW50byxWaXNpdGFzIEF1dG9ndWlhZGFzIHBvciBlbCBNb251bWVudG8gR2VuZXJhbCRWaXNpdGFzIENvbWJpbmFkYXMgQWxoYW1icmEgKyBDaXVkYWQsVmlzaXRhcyBHdWlhZGFzIHBvciBsYSBEZWhlc2EgZGVsIEdlbmVyYWxpZmUpVmlzaXRhcyBHdWlhZGFzIHBvciBlbCBNb251bWVudG8gSmFyZGluZXMtVmlzaXRhcyBBdXRvZ3VpYWRhcyBwb3IgZWwgTW9udW1lbnRvIEphcmRpbmVzHlZpc2l0YXMgR3VpYWRhcyBNdXNlbyArIENpdWRhZBUIACBWaXNpdGFzIEd1aWFkYXMgcG9yIGVsIE1vbnVtZW50byxWaXNpdGFzIEF1dG9ndWlhZGFzIHBvciBlbCBNb251bWVudG8gR2VuZXJhbCRWaXNpdGFzIENvbWJpbmFkYXMgQWxoYW1icmEgKyBDaXVkYWQsVmlzaXRhcyBHdWlhZGFzIHBvciBsYSBEZWhlc2EgZGVsIEdlbmVyYWxpZmUpVmlzaXRhcyBHdWlhZGFzIHBvciBlbCBNb251bWVudG8gSmFyZGluZXMtVmlzaXRhcyBBdXRvZ3VpYWRhcyBwb3IgZWwgTW9udW1lbnRvIEphcmRpbmVzHlZpc2l0YXMgR3VpYWRhcyBNdXNlbyArIENpdWRhZBQrAwhnZ2dnZ2dnZxYBZmQCAQ8QDxYCHwZoZBAVARhTZWxlY2Npb25lIHVuIGl0aW5lcmFyaW8VAQAUKwMBZxYBZmQCCw8WAh8GaGQCDQ8PFgIfAQUXdm9sdmVyIGFsIHBhc28gYW50ZXJpb3JkZAIPD2QWAmYPZBYCAgEPDxYEHwEFC0lyIGEgcGFzbyAzHwZoZGQCDQ8WBB8eBQpzdGVwLXRpdGxlHwZnZAIODw8WAh8GaGQWGmYPFgIfAWVkAgEPFgIfAQUBLmQCAg9kFgJmD2QWCgIBDw8WAh4KSGVhZGVyVGV4dAUlRGViZSBpbnRyb2R1Y2lyIGxvcyB2YWxvcmVzIGNvcnJlY3Rvc2RkAgMPZBYEZg9kFgJmDw8WAh8BBRdOb21icmUgZGVsIGNvbXByYWRvciAqIGRkAgEPZBYCZg8PFgIfAQUMQXBlbGxpZG9zICogZGQCBA9kFgRmD2QWBGYPDxYCHwEFGURvY3VtZW50byBkZSBpZGVudGlkYWQgKiBkZAICDxBkEBUDDEROSSBFc3Bhw7FvbAxOSUUgRXNwYcOxb2wXT3RybyBOcm8uIGlkZW50aWZpY2Fkb3IVAwNkbmkDbmllB290cm9faWQUKwMDZ2dnFgFmZAIBD2QWAmYPDxYCHwEFF07Dum1lcm8gZGUgZG9jdW1lbnRvICogZGQCBQ9kFgRmD2QWAmYPDxYCHwEFCEVtYWlsICogZGQCAQ9kFgJmDw8WAh8BBRFDb25maXJtYSBFbWFpbCAqIGRkAgYPZBYCZg9kFgJmDw8WAh8BBQxUZWzDqWZvbm8gKiBkZAIEDxYCHwZnFgICAQ8QDxYCHgdDaGVja2VkaGRkZGQCBg9kFgQCAQ9kFgICAw8QZBAVBAxETkkgRXNwYcOxb2wMQ0lGIEVzcGHDsW9sDE5JRSBFc3Bhw7FvbBdPdHJvIE5yby4gaWRlbnRpZmljYWRvchUEA2RuaQNjaWYDbmllB290cm9faWQUKwMEZ2dnZxYBZmQCBg9kFgQCBQ8PFgIfBmhkZAIHDxBkEBXvARNTZWxlY2Npb25lIHVuIHBhw61zCUFyZ2VudGluYQlBdXN0cmFsaWEFQ2hpbmEFSXRhbHkFSmFwYW4GTWV4aWNvC05ldyBaZWFsYW5kCFBvcnR1Z2FsB0VzcGHDsWEHR2VybWFueQZGcmFuY2USUnVzc2lhbiBGZWRlcmF0aW9uDlVuaXRlZCBLaW5nZG9tFFVuaXRlZCBTdGF0ZXMgb2YgQW1lC0FmZ2hhbmlzdGFuB0FsYmFuaWEHQWxnZXJpYQ5BbWVyaWNhbiBTYW1vYQdBbmRvcnJhBkFuZ29sYQhBbmd1aWxsYQpBbnRhcmN0aWNhB0FudGlndWEHQXJtZW5pYQVBcnViYQdBdXN0cmlhCkF6ZXJiYWlqYW4HQmFoYW1hcwdCYWhyYWluCkJhbmdsYWRlc2gIQmFyYmFkb3MHQmVsYXJ1cwdCZWxnaXVtBkJlbGl6ZQVCZW5pbgdCZXJtdWRhBkJodXRhbgdCb2xpdmlhBkJvc25pYQhCb3Rzd2FuYQ1Cb3V2ZXQgSXNsYW5kBkJyYXppbA5Ccml0aXNoIEluZGlhbhFCcnVuZWkgRGFydXNzYWxhbQhCdWxnYXJpYQxCdXJraW5hIEZhc28HQnVydW5kaQhDYW1ib2RpYQhDYW1lcm9vbgZDYW5hZGEKQ2FwZSBWZXJkZQ5DYXltYW4gSXNsYW5kcxNDZW50cmFsIEFmcmljYW4gUmVwBENoYWQFQ2hpbGUQQ2hyaXN0bWFzIElzbGFuZA1Db2NvcyBJc2xhbmRzCENvbG9tYmlhB0NvbW9yb3MFQ29uZ28MQ29vayBJc2xhbmRzCkNvc3RhIFJpY2EHQ3JvYXRpYQRDdWJhBkN5cHJ1cw5DemVjaCBSZXB1YmxpYwdEZW5tYXJrCERqaWJvdXRpCERvbWluaWNhEkRvbWluaWNhbiBSZXB1YmxpYwpFYXN0IFRpbW9yB0VjdWFkb3IFRWd5cHQLRWwgU2FsdmFkb3IRRXF1YXRvcmlhbCBHdWluZWEHRXJpdHJlYQdFc3RvbmlhCEV0aGlvcGlhDUZhcm9lIElzbGFuZHMERmlqaQdGaW5sYW5kDUZyZW5jaCBHdWlhbmEQRnJlbmNoIFBvbHluZXNpYQVHYWJvbgZHYW1iaWEHR2VvcmdpYQVHaGFuYQZHcmVlY2UJR3JlZW5sYW5kB0dyZW5hZGEKR3VhZGVsb3VwZQRHdWFtCUd1YXRlbWFsYQZHdWluZWENR3VpbmVhIEJpc3NhdQZHdXlhbmEFSGFpdGkISG9uZHVyYXMJSG9uZyBLb25nB0h1bmdhcnkHSWNlbGFuZAVJbmRpYQlJbmRvbmVzaWEESXJhbgRJcmFxB0lyZWxhbmQGSXNyYWVsC0l2b3J5IENvYXN0B0phbWFpY2EGSm9yZGFuCkthemFraHN0YW4FS2VueWEIS2lyaWJhdGkGS3V3YWl0Ckt5cmd5enN0YW4DTGFvBkxhdHZpYQdMZWJhbm9uB0xlc290aG8HTGliZXJpYQVMaWJ5YQ1MaWVjaHRlbnN0ZWluCUxpdGh1YW5pYQpMdXhlbWJvdXJnBU1hY2F1CU1hY2Vkb25pYQpNYWRhZ2FzY2FyBk1hbGF3aQhNYWxheXNpYQhNYWxkaXZlcwRNYWxpBU1hbHRhCE1hbHZpbmFzEE1hcnNoYWxsIElzbGFuZHMKTWFydGluaXF1ZQpNYXVyaXRhbmlhCU1hdXJpdGl1cwdNYXlvdHRlCk1pY3JvbmVzaWEHTW9sZG92YQZNb25hY28ITW9uZ29saWEKTW9udGVuZWdybwpNb250c2VycmF0B01vcm9jY28KTW96YW1iaXF1ZQdNeWFubWFyB05hbWliaWEFTmF1cnUFTmVwYWwLTmV0aGVybGFuZHMUTmV0aGVybGFuZHMgQW50aWxsZXMNTmV3IENhbGVkb25pYQlOaWNhcmFndWEFTmlnZXIHTmlnZXJpYQROaXVlDk5vcmZvbGsgSXNsYW5kC05vcnRoIEtvcmVhE05vcnRoZXJuIE1hcmlhbmEgSXMGTm9yd2F5BE9tYW4ZT3Ryb3MgZGUgcGFpc2VzIGRlbCBtdW5kbwhQYWtpc3RhbgVQYWxhdQZQYW5hbWEQUGFwdWEgTmV3IEd1aW5lYQhQYXJhZ3VheQRQZXJ1C1BoaWxpcHBpbmVzCFBpdGNhaXJuBlBvbGFuZAtQdWVydG8gUmljbwVRYXRhcgdSZXVuaW9uB1JvbWFuaWEGUndhbmRhD1MgR2VvcmdpYSBTb3V0aAtTYWludCBMdWNpYQVTYW1vYQpTYW4gTWFyaW5vE1NhbyBUb21lIC0gUHJpbmNpcGUMU2F1ZGkgQXJhYmlhB1NlbmVnYWwGU2VyYmlhClNleWNoZWxsZXMMU2llcnJhIExlb25lCVNpbmdhcG9yZQhTbG92YWtpYQhTbG92ZW5pYQ9Tb2xvbW9uIElzbGFuZHMHU29tYWxpYQxTb3V0aCBBZnJpY2ELU291dGggS29yZWEJU3JpIExhbmthCVN0IEhlbGVuYRJTdCBLaXR0cyBhbmQgTmV2aXMTU3QgUGllcnJlICBNaXF1ZWxvbhFTdCBWaW5jZW50LUdyZW5hZAVTdWRhbghTdXJpbmFtZRFTdmFsYmFyZCBKYW4gTSBJcwlTd2F6aWxhbmQG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UnVzc2lhbiBGZWRlcmF0aW9uDlVuaXRlZCBLaW5nZG9tFFVuaXRlZCBTdGF0ZXMgb2YgQW1lC0FmZ2hhbmlzdGFuB0FsYmFuaWEHQWxnZXJpYQ5BbWVyaWNhbiBTYW1vYQdBbmRvcnJhBkFuZ29sYQhBbmd1aWxsYQpBbnRhcmN0aWNhB0FudGlndWEHQXJtZW5pYQVBcnViYQdBdXN0cmlhCkF6ZXJiYWlqYW4HQmFoYW1hcwdCYWhyYWluCkJhbmdsYWRlc2gIQmFyYmFkb3MHQmVsYXJ1cwdCZWxnaXVtBkJlbGl6ZQVCZW5pbgdCZXJtdWRhBkJodXRhbgdCb2xpdmlhBkJvc25pYQhCb3Rzd2FuYQ1Cb3V2ZXQgSXNsYW5kBkJyYXppbA5Ccml0aXNoIEluZGlhbhFCcnVuZWkgRGFydXNzYWxhbQhCdWxnYXJpYQxCdXJraW5hIEZhc28HQnVydW5kaQhDYW1ib2RpYQhDYW1lcm9vbgZDYW5hZGEKQ2FwZSBWZXJkZQ5DYXltYW4gSXNsYW5kcxNDZW50cmFsIEFmcmljYW4gUmVwBENoYWQFQ2hpbGUQQ2hyaXN0bWFzIElzbGFuZA1Db2NvcyBJc2xhbmRzCENvbG9tYmlhB0NvbW9yb3MFQ29uZ28MQ29vayBJc2xhbmRzCkNvc3RhIFJpY2EHQ3JvYXRpYQRDdWJhBkN5cHJ1cw5DemVjaCBSZXB1YmxpYwdEZW5tYXJrCERqaWJvdXRpCERvbWluaWNhEkRvbWluaWNhbiBSZXB1YmxpYwpFYXN0IFRpbW9yB0VjdWFkb3IFRWd5cHQLRWwgU2FsdmFkb3IRRXF1YXRvcmlhbCBHdWluZWEHRXJpdHJlYQdFc3RvbmlhCEV0aGlvcGlhDUZhcm9lIElzbGFuZHMERmlqaQdGaW5sYW5kDUZyZW5jaCBHdWlhbmEQRnJlbmNoIFBvbHluZXNpYQVHYWJvbgZHYW1iaWEHR2VvcmdpYQVHaGFuYQZHcmVlY2UJR3JlZW5sYW5kB0dyZW5hZGEKR3VhZGVsb3VwZQRHdWFtCUd1YXRlbWFsYQZHdWluZWENR3VpbmVhIEJpc3NhdQZHdXlhbmEFSGFpdGkISG9uZHVyYXMJSG9uZyBLb25nB0h1bmdhcnkHSWNlbGFuZAVJbmRpYQlJbmRvbmVzaWEESXJhbgRJcmFxB0lyZWxhbmQGSXNyYWVsC0l2b3J5IENvYXN0B0phbWFpY2EGSm9yZGFuCkthemFraHN0YW4FS2VueWEIS2lyaWJhdGkGS3V3YWl0Ckt5cmd5enN0YW4DTGFvBkxhdHZpYQdMZWJhbm9uB0xlc290aG8HTGliZXJpYQVMaWJ5YQ1MaWVjaHRlbnN0ZWluCUxpdGh1YW5pYQpMdXhlbWJvdXJnBU1hY2F1CU1hY2Vkb25pYQpNYWRhZ2FzY2FyBk1hbGF3aQhNYWxheXNpYQhNYWxkaXZlcwRNYWxpBU1hbHRhCE1hbHZpbmFzEE1hcnNoYWxsIElzbGFuZHMKTWFydGluaXF1ZQpNYXVyaXRhbmlhCU1hdXJpdGl1cwdNYXlvdHRlCk1pY3JvbmVzaWEHTW9sZG92YQZNb25hY28ITW9uZ29saWEKTW9udGVuZWdybwpNb250c2VycmF0B01vcm9jY28KTW96YW1iaXF1ZQdNeWFubWFyB05hbWliaWEFTmF1cnUFTmVwYWwLTmV0aGVybGFuZHMUTmV0aGVybGFuZHMgQW50aWxsZXMNTmV3IENhbGVkb25pYQlOaWNhcmFndWEFTmlnZXIHTmlnZXJpYQROaXVlDk5vcmZvbGsgSXNsYW5kC05vcnRoIEtvcmVhE05vcnRoZXJuIE1hcmlhbmEgSXMGTm9yd2F5BE9tYW4ZT3Ryb3MgZGUgcGFpc2VzIGRlbCBtdW5kbwhQYWtpc3RhbgVQYWxhdQZQYW5hbWEQUGFwdWEgTmV3IEd1aW5lYQhQYXJhZ3VheQRQZXJ1C1BoaWxpcHBpbmVzCFBpdGNhaXJuBlBvbGFuZAtQdWVydG8gUmljbwVRYXRhcgdSZXVuaW9uB1JvbWFuaWEGUndhbmRhD1MgR2VvcmdpYSBTb3V0aAtTYWludCBMdWNpYQVTYW1vYQpTYW4gTWFyaW5vE1NhbyBUb21lIC0gUHJpbmNpcGUMU2F1ZGkgQXJhYmlhB1NlbmVnYWwGU2VyYmlhClNleWNoZWxsZXMMU2llcnJhIExlb25lCVNpbmdhcG9yZQhTbG92YWtpYQhTbG92ZW5pYQ9Tb2xvbW9uIElzbGFuZHMHU29tYWxpYQxTb3V0aCBBZnJpY2ELU291dGggS29yZWEJU3JpIExhbmthCVN0IEhl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eUdvbGRkZAIQD2QWAmYPZBYIZg8WAh8BBSs8c3Ryb25nPlN1IGNvbXByYSBkZSBlbnRyYWRhczwvc3Ryb25nPiBwYXJhZAIBDxYCHwEFF1Zpc2l0YSBBbGhhbWJyYSBHZW5lcmFsZAICDxYCHwEF2AM8ZGl2IGNsYXNzPSdyZXN1bHQnPiAgIDxkaXYgY2xhc3M9J20tYi0xMic+ICAgICAgPGkgY2xhc3M9J2ljb24gaWNvbi1wZW9wbGUnPjwvaT4gICA8L2Rpdj4gICA8ZGl2IGNsYXNzPSdtLWItMTInPiAgICAgIDxpIGNsYXNzPSdpY29uIGljb24tZGF0ZSc+PC9pPiAgICAgIDxwPkZlY2hhOiA8YnIgLz4gICAgICA8L3A+ICAgPC9kaXY+PC9kaXY+PGRpdiBjbGFzcz0ncHJpeC10b3RhbCBicmQtc3VwLTIwJz4gICA8c3BhbiBjbGFzcz0ndGl0dWxvUHJlY2lvRmluYWwnPlRvdGFsIGVudHJhZGFzPC9zcGFuPjxzdHJvbmcgY2xhc3M9J2NvbnRlbmlkb1ByZWNpb0ZpbmFsJz4wPC9zdHJvbmc+ICAgPHNwYW4gY2xhc3M9J3RpdHVsb1ByZWNpb0ZpbmFsIHByZWNpb0ZpbmFsJz5QcmVjaW8gZmluYWw8L3NwYW4+PHN0cm9uZyBjbGFzcz0nY29udGVuaWRvUHJlY2lvRmluYWwgcHJlY2lvRmluYWwnPjAsMDAg4oKsPC9zdHJvbmc+PC9kaXY+ZAIDDxYCHwFkZAISD2QWBAIBDw8WAh8BBQ5BdmlzbyBob3Jhcmlvc2RkAgMPDxYCHwEFogFSZWN1ZXJkZSBzZXIgPGI+cHVudHVhbDwvYj4gZW4gbGEgaG9yYSBzZWxlY2Npb25hZGEgYSBsb3MgPGI+UGFsYWNpb3MgTmF6YXLDrWVzPC9iPi4gUmVzdG8gZGVsIG1vbnVtZW50byBkZSA4OjMwIGEgMTg6MDAgaG9yYXMgaW52aWVybm87IDg6MzAgYSAyMDowMCBob3JhcyB2ZXJhbm9kZAITD2QWCAIBDw8WAh8BBR9BdmlzbyBzb2JyZSB2aXNpdGFzIGNvbiBtZW5vcmVzZGQCAw8PFgIfAQX2AVNpIHZhIGEgcmVhbGl6YXIgbGEgdmlzaXRhIGNvbiBtZW5vcmVzIGRlIDMgYSAxMSBhw7Fvcywgw6lzdG9zIHByZWNpc2FuIGRlIHN1IGVudHJhZGEgY29ycmVzcG9uZGllbnRlLg0KUG9yIGZhdm9yIHNlbGVjY2nDs25lbGEgZW4gc3UgY29tcHJhOiBMYXMgZW50cmFkYXMgZGUgbWVub3JlcyBkZSAzIGHDsW9zIHNlcsOhbiBmYWNpbGl0YWRhcyBlbiBsYXMgdGFxdWlsbGFzIGRlbCBtb251bWVudG8uIMK/RGVzZWEgY29udGludWFyP2RkAgUPDxYCHwEFAlNpZGQCBw8PFgIfAQUCTm9kZAIUD2QWBAIBDw8WAh8BBRZBVklTTyBEQVRPUyBWSVNJVEFOVEVTZGQCAw8PFgIfAQVcQ29tcHJ1ZWJlIHF1ZSBsb3MgZGF0b3MgZGUgdmlzaXRhbnRlcyBzb24gY29ycmVjdG9zLCBhc8OtIGNvbW8gbGEgZmVjaGEgeSBob3JhIHNlbGVjY2lvbmFkYS5kZAICDw8WAh8GaGRkAg4PFgQfAQW/HTxmb290ZXIgY2xhc3M9ImZvb3RlciI+DQogIDxkaXYgaWQ9ImRpdkZvb3RlcjIiIGNsYXNzPSJmb290ZXIyIj4NCiAgICA8ZGl2IGNsYXNzPSJjb250YWluZXIiPg0KICAgICAgPGRpdiBjbGFzcz0ibG9nbyAiPg0KICAgICAgICAgIDxhIGhyZWY9Imh0dHA6Ly93d3cuYWxoYW1icmEtcGF0cm9uYXRvLmVzLyIgdGFyZ2V0PSJfYmxhbmsiPjxpbWcgaWQ9ImltZ0Zvb3RlciIgc3JjPSIvQXBwX1RoZW1lcy9BTEhBTUJSQS9pbWcvbG9nby1mb290ZXIucG5nIiBhbHQ9IkFsaGFtYnJhIHkgR2VuZXJhbGlmZSI+PC9hPg0KICAgICAgICA8L2Rpdj4NCiAgICAgIDxkaXYgY2xhc3M9InJvdyI+DQogICAgICAgICA8ZGl2IGNsYXNzPSJmb290ZXItaXRlbSBjb2x1bW4tMSI+DQogICAgICAgICAgPHVsPg0KICAgICAgICAgICAgPGxpPjxhIGNsYXNzPSJsaW5rcy1pdGVtIiBocmVmPSJodHRwczovL3RpY2tldHMuYWxoYW1icmEtcGF0cm9uYXRvLmVzL3RlLXB1ZWRlLWF5dWRhci8iIHRhcmdldD0iX2JsYW5rIj5MRSBQVUVETyBBWVVEQVI8L2E+PC9saT4NCiAgICAgICAgICAgIDxsaT48YSBjbGFzcz0ibGlua3MtaXRlbSIgaHJlZj0iaHR0cHM6Ly90aWNrZXRzLmFsaGFtYnJhLXBhdHJvbmF0by5lcy9wb2xpdGljYS1kZS1jb21wcmEvIiB0YXJnZXQ9Il9ibGFuayI+UE9Mw41USUNBIERFIENPTVBSQVM8L2E+PC9saT4NCiAgICAgICAgICAgIDxsaT48YSBjbGFzcz0ibGlua3MtaXRlbSIgaHJlZj0iL3BvbGl0aWNhLWNvb2tpZXMuYXNweCIgdGFyZ2V0PSJfYmxhbmsiPlBPTMONVElDQSBERSBDT09LSUVTPC9hPjwvbGk+DQogICAgICAgICAgICA8bGk+PGEgY2xhc3M9ImxpbmtzLWl0ZW0iIGhyZWY9ImphdmFzY3JpcHQ6dm9pZCgwKSIgIG9uQ2xpY2s9IlJlY29uZmlndXJhckNvb2tpZXMoKSI+Q2FuY2VsYXIgLyBjb25maWd1cmFyIHBvbGl0aWNhIGRlIGNvb2tpZXM8L2E+PC9saT4NCiAgICAgICAgICAgIDxsaT48YSBjbGFzcz0ibGlua3MtaXRlbSIgaHJlZj0iaHR0cHM6Ly90aWNrZXRzLmFsaGFtYnJhLXBhdHJvbmF0by5lcy9wb2xpdGljYS1kZS1wcml2YWNpZGFkIiB0YXJnZXQ9Il9ibGFuayI+UE9Mw41USUNBIERFIFBSSVZBQ0lEQUQ8L2E+PC9saT4NCiAgICAgICAgICAgIDxsaT48YSBjbGFzcz0ibGlua3MtaXRlbSIgaHJlZj0iaHR0cHM6Ly90aWNrZXRzLmFsaGFtYnJhLXBhdHJvbmF0by5lcy9hdmlzby1sZWdhbC8iIHRhcmdldD0iX2JsYW5rIj5BVklTTyBMRUdBTDwvYT48L2xpPg0KICAgICAgICAgICAgPGxpPjxwIGNsYXNzPSJsaW5rcy1pdGVtIj5URUzDiUZPTk8gREVMIFZJU0lUQU5URSA8YSBocmVmPSJ0ZWw6KzM0ODU4ODg5MDAyIiBjbGFzcz0idGVsIj4rMzQgOTU4IDAyNyA5NzE8L2E+PC9wPjwvbGk+DQogICAgICAgICAgICA8bGk+PHAgY2xhc3M9ImxpbmtzLWl0ZW0iPlRFTMOJRk9OTyBERSBTT1BPUlRFIEEgTEEgVkVOVEEgREUgRU5UUkFEQVMgPGEgaHJlZj0idGVsOiszNDg1ODg4OTAwMiIgY2xhc3M9InRlbCI+KzM0ODU4ODg5MDAyPC9hPjwvcD48L2xpPg0KPGxpPjxwIGNsYXNzPSJsaW5rcy1pdGVtIj5DT1JSRU8gRUxFQ1RSw5NOSUNPIERFIFNPUE9SVEUgQSBMQSBWRU5UQSBERSBFTlRSQURBUyA8YSBocmVmPSJtYWlsdG86dGlja2V0cy5hbGhhbWJyYUBpYWNwb3MuY29tIiBjbGFzcz0idGVsIj50aWNrZXRzLmFsaGFtYnJhQGlhY3Bvcy5jb208L2E+PC9wPjwvbGk+DQogICAgICAgICAgPC91bD4NCiAgICAgICAgIDwvZGl2Pg0KICAgICAgPC9kaXY+DQogICAgICA8IS0tIENvbnRhY3RvIHkgUlJTUyAtLT4NCiAgICAgIDxkaXYgY2xhc3M9ImZvb3RlcjQiPg0KICAgICAgICA8ZGl2IGNsYXNzPSJmb2xsb3ciPg0KICAgICAgICAgIDxwPlPDrWd1ZW5vcyBlbjo8L3A+DQogICAgICAgICAgPHVsIGNsYXNzPSJzb2NpYWwiPg0KICAgICAgICAgICAgPGxpIGlkPSJsaUZhY2Vib29rIj4NCiAgICAgICAgICAgICAgPGEgaWQ9ImxpbmtGYWNlYm9vayIgY2xhc3M9Imljb24gaWNvbi1mYWNlYm9vayIgdGl0bGU9IkZhY2Vib29rIiBocmVmPSJodHRwczovL3d3dy5mYWNlYm9vay5jb20vYWxoYW1icmFjdWx0dXJhIiB0YXJnZXQ9Il9ibGFuayI+PC9hPg0KICAgICAgICAgICAgPC9saT4NCiAgICAgICAgICAgIDxsaSBpZD0ibGlUd2l0ZXIiPg0KICAgICAgICAgICAgICA8YSBpZD0ibGlua1R3aXR0ZXIiIGNsYXNzPSJpY29uIGljb24tdHdpdHRlciIgdGl0bGU9IlR3aXR0ZXIiIGhyZWY9Imh0dHA6Ly93d3cudHdpdHRlci5jb20vYWxoYW1icmFjdWx0dXJhIiB0YXJnZXQ9Il9ibGFuayI+PC9hPg0KICAgICAgICAgICAgPC9saT4NCiAgICAgICAgICAgIDxsaSBpZD0ibGlZb3VUdWJlIj4NCiAgICAgICAgICAgICAgPGEgaWQ9ImxpbmtZb3VUdWJlIiBjbGFzcz0iaWNvbiBpY29uLXlvdXR1YmUiIHRpdGxlPSJZb3V0dWJlIiBocmVmPSJodHRwOi8vd3d3LnlvdXR1YmUuY29tL2FsaGFtYnJhcGF0cm9uYXRvIiB0YXJnZXQ9Il9ibGFuayI+PC9hPg0KICAgICAgICAgICAgPC9saT4NCiAgICAgICAgICAgIDxsaSBpZD0ibGlJbnN0YWdyYW0iPg0KICAgICAgICAgICAgICA8YSBpZD0ibGlua0ludGFncmFtIiBjbGFzcz0iaWNvbiBpY29uLWluc3RhZ3JhbSIgdGl0bGU9Ikluc3RhZ3JhbSIgaHJlZj0iaHR0cHM6Ly93d3cuaW5zdGFncmFtLmNvbS9hbGhhbWJyYV9vZmljaWFsLyIgdGFyZ2V0PSJfYmxhbmsiPjwvYT4NCiAgICAgICAgICAgIDwvbGk+DQogICAgICAgICAgICA8bGkgaWQ9ImxpUGludGVyZXN0Ij4NCiAgICAgICAgICAgICAgPGEgaWQ9ImxpbmtQaW50ZXJlc3QiIGNsYXNzPSJpY29uIGljb24tcGludGVyZXN0IiB0aXRsZT0iUGludGVyZXN0IiBocmVmPSJodHRwczovL2VzLnBpbnRlcmVzdC5jb20vYWxoYW1icmFncmFuYWRhLyIgdGFyZ2V0PSJfYmxhbmsiPjwvYT4NCiAgICAgICAgICAgIDwvbGk+DQogICAgICAgICAgPC91bD4NCiAgICAgICAgPC9kaXY+DQogICAgICAgIDwhLS0gLy9Db250YWN0byB5IFJSU1MgLS0+DQogICAgICA8L2Rpdj4NCiAgICA8L2Rpdj4NCiAgPC9kaXY+DQogIDxkaXYgaWQ9ImRpdkZvb3RlcjMiIGNsYXNzPSJmb290ZXIzIj4NCiAgICA8ZGl2IGNsYXNzPSJjb250YWluZXIiPg0KICAgICAgPGRpdiBjbGFzcz0iZm9vdGVyLWl0ZW0gY29sdW1uLTEiPg0KICAgICAgICA8ZGl2IGNsYXNzPSJsb2dvIGxvZ29Gb290ZXIiPg0KICAgICAgICAgIDxhIGhyZWY9Imh0dHA6Ly93d3cuYWxoYW1icmEtcGF0cm9uYXRvLmVzLyIgdGFyZ2V0PSJfYmxhbmsiPg0KICAgICAgICAgICAgPGltZyBpZD0iaW1nRm9vdGVyIiBzcmM9Ii9BcHBfVGhlbWVzL0FMSEFNQlJBL2ltZy9sb2dvX3BhdHJvbmF0by5wbmciIGFsdD0iQWxoYW1icmEgeSBHZW5lcmFsaWZlIj4NCiAgICAgICAgICA8L2E+DQogICAgICA8L2Rpdj4NCiAgICAgICAgPHAgY2xhc3M9ImRlc2lnbiI+DQogICAgICAgICAgPHNwYW4gaWQ9ImRldmVsb3BlZCI+Q29weXJpZ2h0IMKpIElBQ1BPUzwvc3Bhbj4NCiAgICAgICAgPC9wPg0KICAgICAgPC9kaXY+DQogICAgICA8ZGl2IGlkPSJkaXZEaXJlY2Npb25Gb290ZXIiIGNsYXNzPSJkaXJlY2Npb24gZm9vdGVyLWl0ZW0gY29sdW1uLTEiPg0KICAgICAgICA8cD5QYXRyb25hdG8gZGUgbGEgQWxoYW1icmEgeSBHZW5lcmFsaWZlPC9wPg0KICAgICAgICAgICAgICAgICAgICA8cD5DLyBSZWFsIGRlIGxhIEFsaGFtYnJhIHMvbjwvcD4NCiAgICAgICAgICAgICAgICAgICAgPHA+Q1AgLSAxODAwOSAoR3JhbmFkYSk8L3A+DQogICAgICA8L2Rpdj4NCiAgICA8L2Rpdj4NCiAgPC9kaXY+DQo8L2Zvb3Rlcj4fBmdkAg8PFgIfBmgWFAICD2QWCgIBD2QWAgIBDw8WAh8DBShodHRwczovL3d3dy5mYWNlYm9vay5jb20vYWxoYW1icmFjdWx0dXJhZGQCAg9kFgICAQ8PFgIfAwUmaHR0cDovL3d3dy50d2l0dGVyLmNvbS9hbGhhbWJyYWN1bHR1cmFkZAIDD2QWAgIBDw8WAh8DBShodHRwOi8vd3d3LnlvdXR1YmUuY29tL2FsaGFtYnJhcGF0cm9uYXRvZGQCBA9kFgICAQ8PFgIfAwUraHR0cHM6Ly93d3cuaW5zdGFncmFtLmNvbS9hbGhhbWJyYV9vZmljaWFsL2RkAgUPZBYCAgEPDxYCHwMFKWh0dHBzOi8vZXMucGludGVyZXN0LmNvbS9hbGhhbWJyYWdyYW5hZGEvZGQCAw9kFgYCAQ9kFgJmDw8WBB8EBSgvQXBwX1RoZW1lcy9BTEhBTUJSQS9pbWcvbG9nby1mb290ZXIucG5nHwUFFUFsaGFtYnJhIHkgR2VuZXJhbGlmZWRkAgMPFgIfBwWUATxwPlBhdHJvbmF0byBkZSBsYSBBbGhhbWJyYSB5IEdlbmVyYWxpZmU8L3A+DQogICAgICAgICAgICAgICAgICAgIDxwPkMvIFJlYWwgZGUgbGEgQWxoYW1icmEgcy9uPC9wPg0KICAgICAgICAgICAgICAgICAgICA8cD5DUCAtIDE4MDA5IChHcmFuYWRhKTwvcD5kAgUPDxYCHwEFE0NvcHlyaWdodCDCqSBJQUNQT1NkZAIEDw8WAh8DBShodHRwczovL3d3dy5mYWNlYm9vay5jb20vYWxoYW1icmFjdWx0dXJhZGQCBQ8PFgIfAwUmaHR0cDovL3d3dy50d2l0dGVyLmNvbS9hbGhhbWJyYWN1bHR1cmFkZAIGDw8WAh8DBStodHRwczovL3d3dy5pbnN0YWdyYW0uY29tL2FsaGFtYnJhX29maWNpYWwvZGQCBw8PFgIfAwUoaHR0cDovL3d3dy55b3V0dWJlLmNvbS9hbGhhbWJyYXBhdHJvbmF0b2RkAggPDxYCHwNkZGQCCQ8PFgIfA2RkZAIKDxYCHwcFlAE8cD5QYXRyb25hdG8gZGUgbGEgQWxoYW1icmEgeSBHZW5lcmFsaWZlPC9wPg0KICAgICAgICAgICAgICAgICAgICA8cD5DLyBSZWFsIGRlIGxhIEFsaGFtYnJhIHMvbjwvcD4NCiAgICAgICAgICAgICAgICAgICAgPHA+Q1AgLSAxODAwOSAoR3JhbmFkYSk8L3A+ZAILDw8WAh8BBRNDb3B5cmlnaHQgwqkgSUFDUE9TZGQCEQ8PFgIfBmhkFgQCAQ9kFgQCAQ8WAh8BBccEPHAgPkVsIHJlc3BvbnNhYmxlIGRlIGVzdGUgc2l0aW8gd2ViIGZpZ3VyYSBlbiBudWVzdHJvICA8YSBocmVmPSJodHRwczovL3RpY2tldHMuYWxoYW1icmEtcGF0cm9uYXRvLmVzL2F2aXNvLWxlZ2FsLyIgPkF2aXNvIExlZ2FsIDwvYSA+LiA8YnIgLyA+VXRpbGl6YW1vcyBjb29raWVzIHByb3BpYXMgeSBvcGNpb25hbG1lbnRlIHBvZGVtb3MgdXRpbGl6YXIgY29va2llcyBkZSB0ZXJjZXJvcy4gTGEgZmluYWxpZGFkIGRlIGxhcyBjb29raWVzIHV0aWxpemFkYXMgZXM6IGZ1bmNpb25hbGVzLCBhbmFsw610aWNhcyB5IHB1YmxpY2l0YXJpYXMuIE5vIHNlIHVzYW4gcGFyYSBsYSBlbGFib3JhY2nDs24gZGUgcGVyZmlsZXMuIFVzdGVkIHB1ZWRlIGNvbmZpZ3VyYXIgZWwgdXNvIGRlIGNvb2tpZXMgZW4gZXN0ZSBtZW51LiA8YnIgLyA+UHVlZGUgb2J0ZW5lciBtw6FzIGluZm9ybWFjacOzbiwgbyBiaWVuIGNvbm9jZXIgY8OzbW8gY2FtYmlhciBsYSBjb25maWd1cmFjacOzbiwgZW4gbnVlc3RyYSA8YnIgLyA+IDxhIGhyZWY9Ii9wb2xpdGljYS1jb29raWVzLmFzcHgiID5Qb2zDrXRpY2EgZGUgY29va2llcyA8L2EgPi48L3AgPmQCAw8PFgIfAQUYQWNlcHRhciB0b2RvIHkgY29udGludWFyZGQCAw9kFggCAQ8PFgIfBmhkZAIDDxYCHwEFxwQ8cCA+RWwgcmVzcG9uc2FibGUgZGUgZXN0ZSBzaXRpbyB3ZWIgZmlndXJhIGVuIG51ZXN0cm8gIDxhIGhyZWY9Imh0dHBzOi8vdGlja2V0cy5hbGhhbWJyYS1wYXRyb25hdG8uZXMvYXZpc28tbGVnYWwvIiA+QXZpc28gTGVnYWwgPC9hID4uPGJyIC8gPiBVdGlsaXphbW9zIGNvb2tpZXMgcHJvcGlhcyB5IG9wY2lvbmFsbWVudGUgcG9kZW1vcyB1dGlsaXphciBjb29raWVzIGRlIHRlcmNlcm9zLiBMYSBmaW5hbGlkYWQgZGUgbGFzIGNvb2tpZXMgdXRpbGl6YWRhcyBlczogZnVuY2lvbmFsZXMsIGFuYWzDrXRpY2FzIHkgcHVibGljaXRhcmlhcy4gTm8gc2UgdXNhbiBwYXJhIGxhIGVsYWJvcmFjacOzbiBkZSBwZXJmaWxlcy4gVXN0ZWQgcHVlZGUgY29uZmlndXJhciBlbCB1c28gZGUgY29va2llcyBlbiBlc3RlIG1lbnUuIDxiciAvID5QdWVkZSBvYnRlbmVyIG3DoXMgaW5mb3JtYWNpw7NuLCBvIGJpZW4gY29ub2NlciBjw7NtbyBjYW1iaWFyIGxhIGNvbmZpZ3VyYWNpw7NuLCBlbiBudWVzdHJhIDxiciAvID4gPGEgaHJlZj0iL3BvbGl0aWNhLWNvb2tpZXMuYXNweCIgPlBvbMOtdGljYSBkZSBjb29raWVzIDwvYSA+LjwvcCA+ZAIHDw8WAh8BBRhBY2VwdGFyIHRvZG8geSBjb250aW51YXJkZAIJDw8WAh8BBSBBY2VwdGFyIHNlbGVjY2lvbmFkbyB5IGNvbnRpbnVhcmRkAgMPFgQfAQXiATwhLS0gU3RhcnQgb2YgY2F1YWxoYW1icmEgWmVuZGVzayBXaWRnZXQgc2NyaXB0IC0tPg0KPHNjcmlwdCBpZD0iemUtc25pcHBldCIgc3JjPWh0dHBzOi8vc3RhdGljLnpkYXNzZXRzLmNvbS9la3Ivc25pcHBldC5qcz9rZXk9NWI3YWUxMjktOWEzYy00ZDJmLWI5NDQtMTQ3MmRmOWZiNTMzPiA8L3NjcmlwdD4NCjwhLS0gRW5kIG9mIGNhdWFsaGFtYnJhIFplbmRlc2sgV2lkZ2V0IHNjcmlwdCAtLT4fBmdkGAMFHl9fQ29udHJvbHNSZXF1aXJlUG9zdEJhY2tLZXlfXxYBBR9jdGwwMCRjaGtSZWdpc3Ryb0FjZXB0b1BvbGl0aWNhBUdjdGwwMCRDb250ZW50TWFzdGVyMSR1Y1Jlc2VydmFyRW50cmFkYXNCYXNlQWxoYW1icmExJHVjSW1wb3J0YXIkV2l6YXJkMQ8QZBQrAQFmZmQFV2N0bDAwJENvbnRlbnRNYXN0ZXIxJHVjUmVzZXJ2YXJFbnRyYWRhc0Jhc2VBbGhhbWJyYTEkdWNJbXBvcnRhciRXaXphcmQxJFdpemFyZE11bHRpVmlldw8PZGZkIAUHlIs4qU7d587zYXSL0GPQp68="
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
                    # alerta_sonora_acierto()
                    # Cambiar el icono a rojo y comenzar a parpadear
                    icon.icon = crear_icono_verde()
                    parpadeo_evento.set()  # Activar el parpadeo
                    parpadear_icono(icon)  # Iniciar el parpadeo

                    enviar_telegram(f"¡Días liberados: {dias_liberados} en GENERAL detectados!", 0)

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

icono = Icon("Alhambra Script", crear_icono(), "Gestor de Calendarios General", menu)

iniciar(icono, None)

if __name__ == "__main__":
    icono.run()
