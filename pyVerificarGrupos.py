import os
import random
import subprocess
import time
import io
import tkinter as tk
from tkinter import messagebox
import fitz  # PyMuPDF



from PIL import Image, ImageEnhance, ImageOps, ImageTk
import pytesseract
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import os


def pedir_captcha_manual(imagen_path):
    root = tk.Tk()
    root.title("Introduce el captcha")
    root.resizable(False, False)

    # Cargar y escalar imagen
    img = Image.open(imagen_path)
    img = img.resize((img.width * 2, img.height * 2), Image.LANCZOS)
    tk_img = ImageTk.PhotoImage(img)

    # Imagen del captcha
    label_img = tk.Label(root, image=tk_img)
    label_img.image = tk_img  # evitar que se borre
    label_img.pack(pady=(10, 5))

    # Entrada de texto
    entry = tk.Entry(root, font=("Helvetica", 16), justify="center")
    entry.pack(pady=(0, 10))

    captcha_code = []

    # Botón para enviar
    def submit():
        captcha_code.append(entry.get())
        root.destroy()

    button = tk.Button(root, text="Enviar", command=submit)
    button.pack(pady=(0, 10))

    # Centrar ventana en pantalla
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')

    root.mainloop()
    return captcha_code[0] if captcha_code else ""


def iniciar_sesion_y_navegar(url_destino):
    try:
        ruta_perfil = os.path.join(os.getenv("LOCALAPPDATA"), "Google", "Chrome", "User Data", "Perfil1")
        options = Options()
        options.add_argument(f"--user-data-dir={ruta_perfil}")
        options.add_argument("--profile-directory=Perfil1")

        driver = webdriver.Chrome(service=Service(), options=options)

        driver.get(url_destino)
        time.sleep(2)

        # Verificamos si aparece el input de login, lo que indicaría que no hay sesión
        try:
            driver.find_element(By.XPATH, "//input[@placeholder='Login']")
            sesion_activa = False
        except:
            sesion_activa = True

        if not sesion_activa:
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
        else:
            print("Sesión ya activa, no es necesario loguearse.")

        # Ir a la URL introducida por el usuario
        driver.get(url_destino)
        time.sleep(3)

        # Encuentra todos los tr del tbody
        rows = driver.find_elements(By.CSS_SELECTOR, "tbody tr")

        # Diccionario con los campos que quieres extraer
        campos_deseados = {
            "Ref.": None,
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

        # --- Localizar y abrir el PDF ---

        # Paso 1: Obtener Ref. y Fecha
        ref = campos_deseados["Ref."]
        fecha_visita = campos_deseados["Fecha de Visita"]

        # Paso 2: Formatear fecha
        fecha_formateada = fecha_visita.replace("/", "-")  # 07/04/2025 -> 07-04-2025

        # Paso 3: Ruta absoluta al PDF
        base_path = os.path.dirname(os.path.abspath(__file__))  # Ruta del script
        ruta_pdf = os.path.join(base_path, "ENTRADAS", fecha_formateada, f"{ref}.pdf")

        # Paso 4: Comprobar si existe y abrirlo
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

        #TIEMPOOOO
        # time.sleep(300000)




    except Exception as e:
        messagebox.showerror("Error", f"Ocurrió un error:\n{str(e)}")


def lanzar_interfaz():
    root = tk.Tk()
    root.title("Login automático ERP")

    tk.Label(root, text="Introduzca la URL del grupo:").pack(padx=20, pady=(20, 5))

    url_entry = tk.Entry(root, width=80)
    url_entry.pack(padx=20, pady=5)

    def on_submit():
        url = url_entry.get().strip()
        if not url.startswith("http"):
            messagebox.showwarning("URL inválida", "Por favor, introduzca una URL válida que empiece por http.")
            return
        root.destroy()
        iniciar_sesion_y_navegar(url)

    tk.Button(root, text="Iniciar sesión y navegar", command=on_submit).pack(pady=(10, 20))

    root.mainloop()


if __name__ == "__main__":
    lanzar_interfaz()
