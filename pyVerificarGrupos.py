import threading
import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import calendar

from selenium.webdriver.common.action_chains import ActionChains


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

def ejecutar_script(icon):
    global DETENER, FALLOS_SEGUIDOS

    random_port = random.randint(9200, 9400)

    def iniciar_navegador():

        ruta_perfil_chrome = os.path.join(os.getenv("LOCALAPPDATA"), "Google", "Chrome", "User Data", "Perfil1")

        options = uc.ChromeOptions()

        # Otros flags útiles
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--no-first-run --no-service-autorun --password-store=basic")
        #
        # options.add_argument("--incognito")
        options.add_argument("--start-maximized")
        # options.add_argument("--window-size=1280,800")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-software-rasterizer")
        # options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-extensions")
        # # options.add_argument("Accept-Language: en-US,en;q=0.9")
        # # options.add_argument("Accept-Encoding: gzip, deflate, br")
        # options.add_argument("Connection: keep-alive")
        # options.add_argument("--remote-debugging-port=9222")
        options.add_argument("--disable-popup-blocking")
        # options.add_argument("--start-minimized")
        options.add_argument(f"--remote-debugging-port={random_port}")
        # options.add_argument("--headless=new")

        # options.add_argument(
        #     "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")


        # options.add_argument(r"--user-data-dir=C:\Users\migue\AppData\Local\Google\Chrome\User Data")

        # options.add_argument(r"--user-data-dir=C:\Users\migue\AppData\Local\Google\Chrome\UserData1")  # Perfil 1

        # options.debugger_address = "127.0.0.1:9222"

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

        # driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        # Agregar cookies manualmente
        # cookies = [
        #     {"name": "ASP.NET_SessionId", "value": "zpfpldtiv50qxi52atqaljmv", "domain": "compratickets.alhambra-patronato.es"},
        # ]
        #
        # driver.add_cookie({
        #     "name": "_GRECAPTCHA",
        #     "value": "09ALcxeyr0dRbO37ktxzd-VY5182PamvfSxR1ipGRhHY3FPQR0eVGKr-2YvCzQeLkD2xG57iXxhc_LgXCFC1Dml80",
        #     "domain": "www.google.com"
        # })
        #
        # for cookie in cookies:
        #     driver.add_cookie(cookie)
        #
        # driver.refresh()  # Recargar la página con las cookies añadidas



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
        #                              "//a[@href='https://tickets.alhambra-patronato.es/producto/alhambra-general/']")
        # enlace.click()
        # time.sleep(TIEMPO)
        #
        # try:
        #     WebDriverWait(driver, 5).until(
        #         EC.element_to_be_clickable((By.XPATH, f"//a[@href='{URL_RESERVAS_GENERAL}']"))
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
            # print(driver.page_source)  # Para ver si hay mensajes ocultos o errores

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
                    logging.info(" Reiniciando navegador por múltiples fallos...")
                    # alerta_sonora_reinicio()
                    # driver.quit()
                    # driver = iniciar_navegador()
                    # minimizar_chrome(driver)  # Ocultar Chrome después de abrirlo
                    # driver.refresh()

                    # navegar_y_preparar(driver)

                    driver.delete_all_cookies()
                    driver.execute_script("window.localStorage.clear();")
                    driver.execute_script("window.sessionStorage.clear();")
                    driver.get('https://compratickets.alhambra-patronato.es/reservarEntradas.aspx?opc=142&gid=432&lg=es-ES&ca=0&m=GENERAL')

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

                enviar_telegram(f"¡Días liberados: {dias_liberados} en GENERAL detectados!")

                # dias_tachados_inicial = dias_tachados_actual

                # mensaje = "¡Días disponibles detectados!\nDías que ya no están tachados: " + ", ".join(
                #     sorted(dias_liberados, key=int))
                # notificar_popup(mensaje)

            if DETENER:
                print(" Deteniendo el script.")
                break

            espera = random.uniform(50, 60)
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

icono = Icon("Alhambra Script", crear_icono(), "Gestor de Calendarios General", menu)

iniciar(icono, None)

if __name__ == "__main__":
    ruta_perfil_chrome = os.path.join(os.getenv("LOCALAPPDATA"), "Google", "Chrome", "User Data", "Perfil1")

    options = uc.ChromeOptions()

    # Otros flags útiles
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-first-run --no-service-autorun --password-store=basic")
    #
    # options.add_argument("--incognito")
    options.add_argument("--start-maximized")
    # options.add_argument("--window-size=1280,800")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-software-rasterizer")
    # options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-extensions")
    # # options.add_argument("Accept-Language: en-US,en;q=0.9")
    # # options.add_argument("Accept-Encoding: gzip, deflate, br")
    # options.add_argument("Connection: keep-alive")
    # options.add_argument("--remote-debugging-port=9222")
    options.add_argument("--disable-popup-blocking")
    # options.add_argument("--start-minimized")
    options.add_argument(f"--remote-debugging-port={random_port}")

    options.add_argument(f"--user-data-dir={ruta_perfil_chrome}")  # <-- Asegurar que está bien escrito

    driver = uc.Chrome(options=options)

    # Ir al sitio web
    driver.get("https://erp.adipatourviajes.com")
    # Espera para que cargue la página
    time.sleep(2)

    # Buscar campos de login y contraseña por el placeholder
    login_input = driver.find_element(By.XPATH, "//input[@placeholder='login']")
    password_input = driver.find_element(By.XPATH, "//input[@placeholder='contraseña']")

    # Introducir los datos
    login_input.send_keys("j.martinez")
    password_input.send_keys("G616lSOpmcIT")

    # Leer el valor del captcha (texto junto al campo)
    captcha_text = driver.find_element(By.XPATH, "//input[@placeholder='Código']/following-sibling::span").text

    # Introducir el captcha
    driver.find_element(By.XPATH, "//input[@placeholder='Código']").send_keys(captcha_text)

    # Hacer clic en el botón "Conexión"
    driver.find_element(By.XPATH, "//button[contains(text(), 'Conexión')]").click()

    # Esperar para ver si se accedió correctamente
    time.sleep(5)


asdfasdfasdfasdfasdfasdfasdfasdfa

    # Cerrar el navegador (opcional)
    driver.quit()
