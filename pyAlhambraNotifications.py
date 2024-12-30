import threading
import tkinter as tk
from tkinter import messagebox
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import winsound
from selenium.webdriver.chrome.options import Options
from pystray import Icon, MenuItem, Menu
from PIL import Image, ImageDraw

# Configuración inicial
TIEMPO_REFRESCO = 300  # Tiempo entre revisiones en segundos
TIEMPO = 5  # Tiempo de espera tras cada paso
DETENER = False  # Variable global para detener el script
SCRIPT_THREAD = None  # Hilo de ejecución del script


def crear_icono():
    """Crea un icono circular para la bandeja del sistema."""
    width, height = 64, 64
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    draw.ellipse((0, 0, width, height), fill="blue")
    return image


def alerta_sonora():
    """Reproduce un sonido para alertar."""
    winsound.Beep(1000, 500)  # Tono de 1000 Hz durante 500 ms


def notificar_popup(mensaje):
    """Muestra un pop-up con un mensaje."""
    root = tk.Tk()
    root.withdraw()  # Oculta la ventana principal
    messagebox.showinfo("Notificación", mensaje)


def ejecutar_script():
    """Función principal del script."""
    global DETENER

    chrome_options = Options()
    chrome_options.add_argument("--incognito")  # Modo incógnito
    chrome_options.add_argument("--start-maximized")  # Opcional: iniciar maximizado
    driver = webdriver.Chrome(options=chrome_options)

    try:
        URL_INICIAL = 'https://tickets.alhambra-patronato.es/'
        URL_RESERVAS = 'https://compratickets.alhambra-patronato.es/reservarEntradas.aspx?opc=142&gid=432&lg=es-ES&ca=0&m=GENERAL'

        # Función para navegar y llegar al calendario
        def navegar_a_calendario():
            driver.get(URL_INICIAL)
            time.sleep(TIEMPO)

            # Aceptar cookies si es necesario
            try:
                boton_aceptar_todo = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, ".mgbutton.moove-gdpr-infobar-allow-all.gdpr-fbo-0"))
                )
                boton_aceptar_todo.click()
                print("Botón 'ACEPTAR TODO' pulsado.")
                time.sleep(TIEMPO)
            except Exception:
                print("Botón 'ACEPTAR TODO' no encontrado o ya aceptado.")

            # Encuentra el botón por su texto y haz clic
            enlace = driver.find_element(By.XPATH,
                                         "//a[@href='https://tickets.alhambra-patronato.es/producto/alhambra-general/']")
            enlace.click()

            time.sleep(TIEMPO)

            # Hacer clic en el enlace para las reservas
            enlace = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, f"//a[@href='{URL_RESERVAS}']"))
            )
            enlace.click()
            time.sleep(TIEMPO)

            # Aceptar cookies si es necesario
            try:
                boton_cookies = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "ctl00_lnkAceptarTodoCookies_Info"))
                )
                boton_cookies.click()
                time.sleep(TIEMPO)
            except Exception:
                print("Botón de cookies no encontrado o ya aceptado.")

            # Hacer clic en el botón para pasar al calendario
            boton = driver.find_element(By.ID, "ctl00_ContentMaster1_ucReservarEntradasBaseAlhambra1_btnIrPaso1")
            boton.click()
            time.sleep(TIEMPO)

        # Inicia el proceso
        navegar_a_calendario()

        # Obtener los días iniciales tachados
        dias_tachados_inicial = driver.find_elements(By.CSS_SELECTOR,
                                                     "#ctl00_ContentMaster1_ucReservarEntradasBaseAlhambra1_ucCalendarioPaso1_calendarioFecha .calendario_padding.no-dispo")
        dias_tachados_ids_inicial = [dia.get_attribute("id") for dia in dias_tachados_inicial]

        print(f"Días tachados inicialmente: {dias_tachados_ids_inicial}")

        while not DETENER:
            # Refrescar la página actual
            driver.refresh()
            print("Página refrescada.")
            time.sleep(TIEMPO)

            # Hacer clic en el botón para pasar al calendario nuevamente
            try:
                boton = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable(
                        (By.ID, "ctl00_ContentMaster1_ucReservarEntradasBaseAlhambra1_btnIrPaso1"))
                )
                boton.click()
                print("Botón para pasar al calendario pulsado.")
                time.sleep(TIEMPO)
            except Exception as e:
                print(f"Error al hacer clic en el botón para pasar al calendario: {e}")

            # Obtener los días actuales tachados
            dias_tachados_actual = driver.find_elements(By.CSS_SELECTOR,
                                                        "#ctl00_ContentMaster1_ucReservarEntradasBaseAlhambra1_ucCalendarioPaso1_calendarioFecha .calendario_padding.no-dispo")
            dias_tachados_ids_actual = [dia.get_attribute("id") for dia in dias_tachados_actual]

            print(f"Días tachados actual: {dias_tachados_ids_actual}")

            # Comparar los días iniciales con los actuales
            print(f" Longitud Días tachados inicial: " + str(len(dias_tachados_ids_inicial)))
            print(f" Longitud Días tachados actual: " + str(len(dias_tachados_ids_actual)))

            if (len(dias_tachados_ids_inicial) != len(dias_tachados_ids_actual)) and len(
                    dias_tachados_ids_actual) != 0:
                print("¡Cambios detectados en el calendario!")
                alerta_sonora()  # Alerta sonora
                notificar_popup("¡Un día anteriormente no disponible ahora tiene plazas!")  # Notificación visual
                break  # Salir del bucle si se detectan cambios

            # Si se solicita detener el programa, salir
            if DETENER:
                print("Deteniendo el script según lo solicitado por el usuario.")
                break

            # Esperar antes de la próxima revisión
            print("No se detectaron cambios. Revisando nuevamente en unos segundos...")
            time.sleep(TIEMPO_REFRESCO)

    finally:
        driver.quit()


def iniciar(icon, item):
    """Inicia el script en un hilo separado."""
    print("Pulsado iniciar")
    global DETENER, SCRIPT_THREAD

    if SCRIPT_THREAD is None or not SCRIPT_THREAD.is_alive():  # Verifica si el hilo no está corriendo
        DETENER = False
        SCRIPT_THREAD = threading.Thread(target=ejecutar_script, daemon=True)
        SCRIPT_THREAD.start()
        print("Script iniciado.")
    else:
        print("El script ya está en ejecución.")


def detener(icon, item):
    """Detiene la ejecución del script."""
    global DETENER
    if not DETENER:
        DETENER = True
        print("Script detenido.")


def salir(icon, item):
    """Cierra completamente el programa."""
    detener(icon, item)
    icon.stop()


# Menú para la bandeja del sistema
menu = Menu(
    MenuItem("Iniciar", iniciar),
    MenuItem("Detener", detener),
    MenuItem("Salir", salir),
)

icono = Icon("Alhambra Script", crear_icono(), "Gestor de Calendarios", menu)

if __name__ == "__main__":
    icono.run()
