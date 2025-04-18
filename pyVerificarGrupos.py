from tkinterdnd2 import DND_FILES, TkinterDnD
import pandas as pd
from selenium.webdriver.support.ui import WebDriverWait
import os
import time
import io
import tkinter as tk
from PIL import Image, ImageEnhance, ImageOps, ImageTk
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import fitz  # PyMuPDF


def pedir_captcha_manual(imagen_path):
    ventana = tk.Toplevel()
    ventana.title("Introduce el captcha")
    ventana.resizable(False, False)

    # Cargar y escalar imagen
    img = Image.open(imagen_path)
    img = img.resize((img.width * 2, img.height * 2), Image.LANCZOS)
    tk_img = ImageTk.PhotoImage(img)

    ventana.tk_img = tk_img  # evita que se borre

    # Imagen del captcha
    label_img = tk.Label(ventana, image=ventana.tk_img)
    label_img.pack(pady=(10, 5))

    # Entrada de texto
    entry = tk.Entry(ventana, font=("Helvetica", 16), justify="center")
    entry.pack(pady=(0, 10))

    captcha_var = tk.StringVar()

    def submit():
        captcha_var.set(entry.get())
        ventana.destroy()

    button = tk.Button(ventana, text="Enviar", command=submit)
    button.pack(pady=(0, 10))

    # Centrar ventana
    ventana.update_idletasks()
    width = ventana.winfo_width()
    height = ventana.winfo_height()
    x = (ventana.winfo_screenwidth() // 2) - (width // 2)
    y = (ventana.winfo_screenheight() // 2) - (height // 2)
    ventana.geometry(f'{width}x{height}+{x}+{y}')

    # Esperar a que se llene la variable
    ventana.grab_set()
    ventana.wait_variable(captcha_var)

    return captcha_var.get()


def iniciar_sesion_y_navegar(url, root):
    options = uc.ChromeOptions()
    options.add_argument("--start-maximized")

    driver = uc.Chrome(options=options)

    wait = WebDriverWait(driver, 30)

    driver.get(url)

    time.sleep(2)

    login_input = driver.find_element(By.XPATH, "//input[@placeholder='Login']")
    password_input = driver.find_element(By.XPATH, "//input[@placeholder='Contraseña']")

    login_input.send_keys("j.martinez")
    password_input.send_keys("G616lSOpmcIT")

    # Capturar captcha desde la web
    captcha_img = driver.find_element(By.ID, "img_securitycode")
    driver.execute_script("arguments[0].scrollIntoView();", captcha_img)
    time.sleep(1)

    location = captcha_img.location
    size = captcha_img.size
    dpr = driver.execute_script("return window.devicePixelRatio")
    time.sleep(0.5)

    screenshot = driver.get_screenshot_as_png()
    image = Image.open(io.BytesIO(screenshot))
    image.save("pantalla_completa.png")

    # Recorte con ajuste de DPR
    padding = 5
    left = int(location['x'] * dpr) - padding
    top = int(location['y'] * dpr) - padding
    right = left + int(size['width'] * dpr) + padding * 2
    bottom = top + int(size['height'] * dpr) + padding * 2

    captcha_crop = image.crop((left, top, right, bottom))
    captcha_crop.save("captcha_crop.png")

    # Procesar para OCR
    captcha_image = captcha_crop.convert('L')
    captcha_image = ImageOps.invert(captcha_image)
    enhancer = ImageEnhance.Contrast(captcha_image)
    captcha_image = enhancer.enhance(2.0)
    captcha_image = captcha_image.point(lambda x: 0 if x < 120 else 255, '1')
    captcha_image = captcha_image.resize((captcha_image.width * 2, captcha_image.height * 2), Image.LANCZOS)
    captcha_image.save("captcha_processed.png")

    captcha_code = pedir_captcha_manual("captcha_processed.png")

    driver.find_element(By.ID, "securitycode").send_keys(captcha_code)
    driver.find_element(By.CSS_SELECTOR, "input.button[type='submit']").click()

    time.sleep(3)

    # Ir a la URL introducida por el usuario
    driver.get(url)
    time.sleep(3)

    # Encuentra todos los tr del tbody
    rows = driver.find_elements(By.CSS_SELECTOR, "tbody tr")

    # Diccionario con los campos que quieres extraer
    campos_deseados = {
        "Ref.": None,
        "Localizador": None,
        "PAX Adultas": None,
        "PAX Jubilado": None,
        "PAX Infantil 3 a 11 años": None,
        "PAX Infantil 12 a 15 años": None,
        "Fecha de Visita": None,
        "Tipo": None,
        "Hora de Palacios": None,
        "Hora de Palacios 2": None,
    }

    # Ordenar las claves por longitud inversa para evitar conflictos (más largas primero)
    claves_ordenadas = sorted(campos_deseados.keys(), key=lambda x: -len(x))

    # Recorremos las filas y asignamos valores
    for row in rows:
        columnas = row.find_elements(By.TAG_NAME, "td")
        if len(columnas) >= 2:
            campo = columnas[0].text.strip()
            valor = columnas[1].text.strip()
            for clave in claves_ordenadas:
                if campo.startswith(clave):
                    campos_deseados[clave] = valor
                    break  # Salimos del bucle tras encontrar la coincidencia correcta

    # Mostrar resultados
    for campo, valor in campos_deseados.items():
        print(f"{campo}: {valor}")

    # --- Ir a la pestaña "Docs. Asociados" y descargar el Excel ---
    try:
        # Hacer clic en la pestaña "Docs. Asociados"
        docs_tab = driver.find_element(By.ID, "datos_documentos_asociados")
        docs_tab.click()
        time.sleep(3)  # Esperar que cargue la pestaña

        # Esperar y hacer clic en el enlace del Excel
        enlace_excel = driver.find_element(By.XPATH, "//a[contains(@href, '.xlsx')]")
        href_excel = enlace_excel.get_attribute("href")
        nombre_excel = enlace_excel.text.strip()
        print(f"Descargando archivo: {nombre_excel}")
        enlace_excel.click()

        # Esperar que se descargue el archivo (ajustar si es necesario)
        time.sleep(5)

        # Ruta de descarga (asumiendo carpeta por defecto)
        carpeta_descargas = os.path.join(os.path.expanduser("~"), "Downloads")
        ruta_excel = os.path.join(carpeta_descargas, nombre_excel)

        if os.path.isfile(ruta_excel):
            print(f"Excel descargado correctamente: {ruta_excel}")
            df_excel = pd.read_excel(ruta_excel)
            # datos_excel = list(
            #     zip(df_excel['Fecha'].astype(str), df_excel['Nombre'], df_excel['Apellidos'], df_excel['Tipo ticket']))

            # for fila in datos_excel:
            #     if False:
            #         print("Diferencia encontrada:", fila)
            #         break
            # else:
            #     resultado_label = tk.Label(root, text="Comparación realizada correctamente sin diferencias", fg="green",
            #                                font=("Helvetica", 12))
            #     resultado_label.pack(pady=10)
        else:
            print(f"No se encontró el archivo descargado: {ruta_excel}")

    except Exception as e:
        print(f"Error al descargar el Excel: {e}")


    # --- Localizar y abrir el PDF ---

    from datetime import datetime

    # Paso 1: Obtener Localizador y Fecha
    ref = campos_deseados["Localizador"]
    fecha_visita = campos_deseados["Fecha de Visita"]

    # Paso 2: Formatear fecha
    fecha_formateada = fecha_visita.replace("/", "-")  # Ej. 07/04/2025 -> 07-04-2025

    # Paso 3: Obtener año actual
    anio_actual = str(datetime.now().year)

    # Paso 4: Construir nueva ruta absoluta al PDF
    base_path = os.path.dirname(os.path.abspath(__file__))  # Ruta del script
    ruta_pdf = os.path.join(base_path, anio_actual, "ALHAMBRA", "ENTRADAS", fecha_formateada, f"{ref}.pdf")

    # Paso 5: Comprobar si existe y abrirlo
    if os.path.isfile(ruta_pdf):
        print(f"Abriendo PDF: {ruta_pdf}")
        subprocess.run(['start', '', ruta_pdf], shell=True)  # Abre el PDF con visor predeterminado
    else:
        print(f"PDF no encontrado: {ruta_pdf}")

    # Leer el PDF y buscar los campos dentro del texto
    try:
        doc = fitz.open(ruta_pdf)
        contenido_pdf = ""
        for page in doc:
            contenido_pdf += page.get_text()

        doc.close()

        # Buscar los valores en el texto extraído
        coincidencias = {
            "Fecha de Visita": campos_deseados["Fecha de Visita"] in contenido_pdf,
            "Tipo": campos_deseados["Tipo"] in contenido_pdf,
            "Hora de Palacios": campos_deseados["Hora de Palacios"] in contenido_pdf,
        }

        print("\n--- Verificación de campos en el PDF ---")
        for campo, presente in coincidencias.items():
            valor = campos_deseados[campo]
            estado = "OK" if presente else "NO"
            print(f"{campo} ({valor}): {estado}")

    except Exception as e:
        print(f"Error al leer el PDF: {e}")





def lanzar_interfaz():
    root = TkinterDnD.Tk()
    root.title("Comparador de reservas")
    root.geometry("500x500")
    root.configure(bg="#f2f2f2")

    root.archivo_excel_path = None  # Guardamos el path aquí

    def on_submit():
        url = entry_url.get()
        if not (url):
            return

        iniciar_sesion_y_navegar(url, root)

    # Widgets

    tk.Label(root, text="URL:", bg="#f2f2f2").pack(pady=(10, 5))
    entry_url = tk.Entry(root, width=40)
    entry_url.pack()

    submit_btn = tk.Button(root, text="Comparar reservas", command=on_submit, bg="#4CAF50", fg="white", padx=10, pady=5)
    submit_btn.pack(pady=20)

    root.mainloop()


if __name__ == "__main__":
    lanzar_interfaz()
