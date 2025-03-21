import threading
import tkinter as tk
from tkinter import messagebox

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

parpadeo_evento = Event()

FALLOS_SEGUIDOS = 0
MAX_FALLOS = 2
ESTADO_FILE = "dias_tachados_inicial.pkl"


def borrar_archivo_estado():
    if os.path.exists(ESTADO_FILE):
        try:
            os.remove(ESTADO_FILE)
            print(f"Archivo temporal '{ESTADO_FILE}' eliminado.")
        except Exception as e:
            print(f"Error al eliminar el archivo '{ESTADO_FILE}': {e}")


atexit.register(borrar_archivo_estado)


def crear_icono_azul():
    """Crea un icono azul para la bandeja del sistema."""
    width, height = 64, 64
    image = Image.new("RGB", (width, height), "blue")
    draw = ImageDraw.Draw(image)
    draw.ellipse((0, 0, width, height), fill="blue")
    return image


def crear_icono_amarillo():
    """Crea un icono amarillo para la bandeja del sistema."""
    width, height = 64, 64
    image = Image.new("RGB", (width, height), "yellow")
    draw = ImageDraw.Draw(image)
    draw.ellipse((0, 0, width, height), fill="yellow")
    return image


def crear_icono_rojo():
    """Crea un icono rojo para la bandeja del sistema."""
    width, height = 64, 64
    image = Image.new("RGB", (width, height), "red")
    draw = ImageDraw.Draw(image)
    draw.ellipse((0, 0, width, height), fill="red")
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
    icono_normal = crear_icono_azul()
    icono_alerta = crear_icono_rojo()

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

    # Obtener días tachados del mes actual
    dias_mes_actual = driver.find_elements(By.CSS_SELECTOR,
                                           "#ctl00_ContentMaster1_ucReservarEntradasBaseAlhambra1_ucCalendarioPaso1_calendarioFecha .calendario_padding.no-dispo")
    dias_total.extend([dia.get_attribute("id") for dia in dias_mes_actual])



    # Pulsar el botón para ir al mes siguiente
    try:
        boton_mes_siguiente = driver.find_element(
            By.XPATH,
            "//td[@align='right' and contains(@style, 'width:15%')]//a[contains(@href,'__doPostBack')]"
        )
        boton_mes_siguiente.click()
        time.sleep(TIEMPO)
    except Exception as e:
        print(f" No se pudo avanzar al mes siguiente: {e}")
        return dias_total

    # Obtener días tachados del mes siguiente
    dias_mes_siguiente = driver.find_elements(By.CSS_SELECTOR,
                                              "#ctl00_ContentMaster1_ucReservarEntradasBaseAlhambra1_ucCalendarioPaso1_calendarioFecha .calendario_padding.no-dispo")
    dias_total.extend([dia.text.strip() for dia in dias_mes_siguiente if dia.text.strip()])

    return dias_total


# Configuración inicial
TIEMPO_REFRESCO = 10  # Tiempo entre revisiones en segundos
TIEMPO = random.uniform(4, 6)  # Tiempo de espera tras cada paso
DETENER = False  # Variable global para detener el script
SCRIPT_THREAD = None  # Hilo de ejecución del script


def crear_icono():
    """Crea un icono circular para la bandeja del sistema."""
    width, height = 64, 64
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    draw.ellipse((0, 0, width, height), fill="blue")
    return image


def alerta_sonora_error():
    """Reproduce un sonido para alertar."""
    winsound.Beep(1000, 2000)  # Tono de 1000 Hz durante 500 ms


def alerta_sonora_acierto():
    """Reproduce un sonido para alertar."""
    winsound.Beep(1000, 500)  # Tono de 1000 Hz durante 500 ms


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


def ejecutar_script():
    global DETENER, FALLOS_SEGUIDOS

    # chrome_options = Options()
    # chrome_options.add_argument("--incognito")
    # chrome_options.add_argument("--start-maximized")
    # # options.add_argument('--disable-blink-features=AutomationControlled')
    #
    # # Opciones anti-detección
    # chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    # chrome_options.add_experimental_option('useAutomationExtension', False)
    #
    # # User-Agent realista
    # chrome_options.add_argument(
    #     "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    #     "AppleWebKit/537.36 (KHTML, like Gecko) "
    #     "Chrome/121.0.0.0 Safari/537.36"
    # )

    def iniciar_navegador():

        options = uc.ChromeOptions()

        # Ruta a tu perfil de Chrome
        user_data_dir = r"C:\Users\migue\AppData\Local\Google\Chrome\User Data"

        # (opcional) Puedes especificar un perfil dentro del user data dir (como "Default" o "Profile 1")
        profile_dir = "Default"

        # options = uc.ChromeOptions()
        # options.add_argument(f"--user-data-dir={user_data_dir}")
        # options.add_argument(f"--profile-directory={profile_dir}")

        # Otros flags útiles
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--no-first-run --no-service-autorun --password-store=basic")

        options.add_argument("--incognito")
        options.add_argument("--start-maximized")
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/121.0.0.0 Safari/537.36"
        )

        driver = uc.Chrome(options=options, headless=False)
        return driver

    def navegar_y_preparar(driver):
        URL_INICIAL = 'https://tickets.alhambra-patronato.es/'
        URL_RESERVAS = 'https://compratickets.alhambra-patronato.es/reservarEntradas.aspx?opc=142&gid=432&lg=es-ES&ca=0&m=GENERAL'

        driver.get(URL_INICIAL)
        driver.delete_all_cookies()
        driver.execute_script("window.localStorage.clear();")
        driver.execute_script("window.sessionStorage.clear();")
        time.sleep(TIEMPO)

        try:
            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".mgbutton.moove-gdpr-infobar-allow-all.gdpr-fbo-0"))
            ).click()
            print("Botón 'ACEPTAR TODO' pulsado.")
            time.sleep(TIEMPO)
        except Exception:
            print("Botón 'ACEPTAR TODO' no encontrado o ya aceptado.")

        enlace = driver.find_element(By.XPATH,
                                     "//a[@href='https://tickets.alhambra-patronato.es/producto/alhambra-general/']")
        enlace.click()
        time.sleep(TIEMPO)

        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, f"//a[@href='{URL_RESERVAS}']"))
        ).click()
        time.sleep(TIEMPO)

        try:
            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "ctl00_lnkAceptarTodoCookies_Info"))
            ).click()
            time.sleep(TIEMPO)
        except Exception:
            print("Botón de cookies no encontrado o ya aceptado.")

        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "ctl00_ContentMaster1_ucReservarEntradasBaseAlhambra1_btnIrPaso1"))
        ).click()
        time.sleep(TIEMPO)

    driver = iniciar_navegador()
    navegar_y_preparar(driver)

    dias_tachados_inicial = cargar_dias_tachados()

    # Si no hay días tachados guardados, intentar obtenerlos de la web hasta que haya al menos uno
    if not dias_tachados_inicial:
        intentos = 0
        while True:

            # WebDriverWait(driver, 20).until(
            #     EC.element_to_be_clickable((By.ID, "ctl00_ContentMaster1_ucReservarEntradasBaseAlhambra1_btnIrPaso1"))
            # ).click()

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

            # enlace = driver.find_element(By.ID,
            #                              "ctl00_ContentMaster1_ucReservarEntradasBaseAlhambra1_btnIrPaso1")
            # enlace.click()

            try:
                WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable(
                        (By.ID, "ctl00_ContentMaster1_ucReservarEntradasBaseAlhambra1_btnIrPaso1"))
                ).click()
                time.sleep(TIEMPO)
            except Exception:
                print("Botón de paso 1 ya pulsado.")

            time.sleep(TIEMPO)

            dias_tachados_inicial = obtener_dias_tachados_completos(driver)
            if dias_tachados_inicial:
                break
            intentos += 1
            print(f"Intento {intentos}: No se encontraron días tachados. Recargando la página...")
            driver.refresh()
            time.sleep(random.uniform(3, 5))  # Pausa para simular comportamiento humano o evitar bloqueos

        guardar_dias_tachados(dias_tachados_inicial)

    print(f"Días tachados inicialmente: {len(dias_tachados_inicial)}")

    counter = 1
    counter_diasTachados = 1

    try:
        while not DETENER:
            print(f"\n Intento #{counter}")
            counter += 1
            # Reiniciar navegador cada 10 ciclos
            # if counter % 5 == 0:
            #     print("Reiniciando navegador tras 10 intentos para evitar bloqueos.")
            #     try:
            #         driver.quit()
            #     except:
            #         pass
            #     try:
            #         shutil.rmtree(driver.temp_profile_path, ignore_errors=True)
            #     except:
            #         pass
            #     driver = iniciar_navegador()
            #     navegar_y_preparar(driver)
            #     continue  # Para evitar intentar doble clic en esta iteración
            driver.refresh()
            time.sleep(TIEMPO)

            # Muchos bloqueos si lo activo
            # try:
            #     WebDriverWait(driver, 10).until(
            #         EC.element_to_be_clickable((By.ID, "ctl00_lnkAceptarTodoCookies_Info"))
            #     ).click()
            #     time.sleep(TIEMPO)
            # except Exception:
            #     print("Botón de cookies no encontrado o ya aceptado.")

            try:
                boton = WebDriverWait(driver, 10).until(
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
                alerta_sonora_error()
                # notificar_popup("¡Error al ir al paso 1!")
                FALLOS_SEGUIDOS += 1

                if FALLOS_SEGUIDOS >= MAX_FALLOS:
                    print(" Reiniciando navegador por múltiples fallos...")
                    driver.quit()
                    driver = iniciar_navegador()
                    navegar_y_preparar(driver)
                    FALLOS_SEGUIDOS = 0
                    continue
                else:
                    continue

            dias_tachados_actual = obtener_dias_tachados_completos(driver)
            print(f"Días tachados actuales: {len(dias_tachados_actual)}")

            set_inicial = set(dias_tachados_inicial)
            set_actual = set(dias_tachados_actual)

            dias_liberados = set_inicial - set_actual

            if dias_liberados:
                print(f" ¡Días liberados: {dias_liberados}!")
                alerta_sonora_acierto()
                mensaje = "¡Días disponibles detectados!\nDías que ya no están tachados: " + ", ".join(
                    sorted(dias_liberados, key=int))
                notificar_popup(mensaje)

                # Cambiar el icono a rojo y comenzar a parpadear
                icon.icon = crear_icono_rojo()
                parpadeo_evento.set()  # Activar el parpadeo
                parpadear_icono(icon)  # Iniciar el parpadeo

            if DETENER:
                print(" Deteniendo el script.")
                break

            espera = random.uniform(30, 60)
            print(f" Esperando {espera:.2f} segundos antes de volver a intentar...")
            time.sleep(espera)
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
        SCRIPT_THREAD = threading.Thread(target=ejecutar_script, daemon=True)
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
        icon.icon = crear_icono_azul()

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

icono = Icon("Alhambra Script", crear_icono(), "Gestor de Calendarios", menu)

if __name__ == "__main__":
    icono.run()
