from tkinterdnd2 import DND_FILES, TkinterDnD
import pandas as pd
from selenium.webdriver.support.ui import WebDriverWait
import os
import time
import io
import tkinter as tk
from PIL import Image, ImageEnhance, ImageOps, ImageTk
import undetected_chromedriver as uc
import fitz  # PyMuPDF
from selenium.webdriver.common.by import By
import re
import glob


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
    entry.focus()  # pone el foco en el campo de entrada automáticamente

    captcha_var = tk.StringVar()

    def submit(event=None):  # aceptamos el evento para que funcione también con el binding
        captcha_var.set(entry.get())
        ventana.destroy()

    # Botón para enviar
    button = tk.Button(ventana, text="Enviar", command=submit)
    button.pack(pady=(0, 10))

    # Asociar tecla Enter con el botón
    ventana.bind('<Return>', submit)

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
    ruta_perfil_chrome = os.path.join(os.getenv("LOCALAPPDATA"), "Google", "Chrome", "User Data", "Perfil2")

    options = uc.ChromeOptions()

    # Otros flags útiles
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-first-run --no-service-autorun --password-store=basic")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--disable-extensions")

    options.add_argument("--disable-popup-blocking")

    options.add_argument(f"--user-data-dir={ruta_perfil_chrome}")  # <-- Asegurar que está bien escrito

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

    claves_equivalentes = {
        "Ref.": "Ref.",
        "Localizador Original": "Localizador Original",
        "PAX Adultas": "PAX Adultas",
        "PAX Jubilado": "PAX Jubilado",
        "PAX Infantil 3 a 11 años": "PAX Infantil 3 a 11 años",
        "PAX Infantil 12 a 15 años": "PAX Infantil 12 a 15 años",
        "Fecha de Visita": "Fecha de Visita",
        "Turno": "Turno",
        "Tipo": "Tipo",
        "Hora de Palacios": "Hora de Palacios",
        "Hora de Palacios 2": "Hora de Palacios 2",
    }

    campos_deseados = {v: None for v in claves_equivalentes.values()}

    fieldset_elements = driver.find_elements(By.CSS_SELECTOR, "div.tabBarWithBottom fieldset")

    for fieldset in fieldset_elements:
        filas = fieldset.find_elements(By.CSS_SELECTOR, "tr")
        for fila in filas:
            columnas = fila.find_elements(By.TAG_NAME, "td")
            if len(columnas) >= 2:
                # Extraemos solo el texto visible del primer <td>, ignorando los <a>, <span>, etc.
                clave_element = columnas[0]
                clave_raw = clave_element.get_property("innerText").strip()
                valor_raw = columnas[1].get_property("innerText").strip()

                for clave_parcial, clave_estandar in claves_equivalentes.items():
                    if clave_parcial in clave_raw:
                        campos_deseados[clave_estandar] = valor_raw
                        break

    # Imprimir resultado
    for campo, valor in campos_deseados.items():
        print(f"{campo}: {valor}")

    # --- Ir a la pestaña "Docs. Asociados" y descargar el Excel ---

    # Hacer clic en la pestaña "Docs. Asociados"
    docs_tab = driver.find_element(By.ID, "datos_documentos_asociados")
    docs_tab.click()
    time.sleep(3)  # Esperar que cargue la pestaña

    from datetime import datetime

    # Esperar y obtener todos los enlaces a Excels y sus fechas
    filas = driver.find_elements(By.XPATH, "//table[contains(@class, 'border')]/tbody/tr[position()>1]")

    excel_mas_reciente = None
    fecha_mas_reciente = None

    for fila in filas:
        try:
            enlaces = fila.find_elements(By.XPATH, ".//td[1]/a[contains(@href, '.xlsx')]")
            if not enlaces:
                continue  # Saltamos la fila si no hay enlaces .xlsx

            enlace = enlaces[0]
            fecha_texto = fila.find_element(By.XPATH, ".//td[2]").text.strip()
            fecha_subida = datetime.strptime(fecha_texto, "%d/%m/%Y %H:%M:%S")

            if fecha_mas_reciente is None or fecha_subida > fecha_mas_reciente:
                fecha_mas_reciente = fecha_subida
                excel_mas_reciente = enlace
        except Exception as e:
            print(f"Error al procesar fila: {e}")
            continue

    if excel_mas_reciente:
        href_excel = excel_mas_reciente.get_attribute("href")
        nombre_excel = excel_mas_reciente.text.strip()
        print(f"Descargando archivo más reciente: {nombre_excel}")
        excel_mas_reciente.click()

        carpeta_descargas = os.path.join(os.path.expanduser("~"), "Downloads")

        # Esperamos hasta que no haya archivos .crdownload activos
        tiempo_max_espera = 20  # segundos
        inicio = time.time()

        while True:
            descargando = glob.glob(os.path.join(carpeta_descargas, "*.crdownload"))
            if not descargando or (time.time() - inicio) > tiempo_max_espera:
                break
            time.sleep(1)

        # Una vez finalizada la descarga, buscamos el Excel más reciente
        lista_excel = glob.glob(os.path.join(carpeta_descargas, "*.xlsx"))
        if lista_excel:
            ruta_excel = max(lista_excel, key=os.path.getctime)
            print(f"Último Excel detectado: {ruta_excel}")
        else:
            print("No se encontró ningún archivo Excel en la carpeta de descargas.")
        if lista_excel:
            ruta_excel = max(lista_excel, key=os.path.getctime)
            print(f"Último Excel detectado: {ruta_excel}")
            # df_excel = pd.read_excel(ruta_excel)
        else:
            print("No se encontró ningún archivo Excel en la carpeta de descargas.")
    else:
        print("No se encontró ningún enlace a archivo Excel.")

    # --- Localizar y abrir el PDF ---

    # Paso 1: Obtener Localizador y Fecha
    ref = campos_deseados["Localizador Original"]
    fecha_visita = campos_deseados["Fecha de Visita"]

    # Paso 2: Formatear fecha
    fecha_formateada = fecha_visita.replace("/", "-")  # Ej. 07/04/2025 -> 07-04-2025

    # Paso 3: Obtener año actual
    anio_actual = str(datetime.now().year)

    # Paso 4: Construir nueva ruta absoluta al PDF
    base_path = os.path.dirname(os.path.abspath(__file__))  # Ruta del script

    # Paso 4: Construir ruta a la carpeta donde buscar los PDFs
    carpeta_pdfs = os.path.join(base_path, anio_actual, "ALHAMBRA", "ENTRADAS", fecha_formateada)

    # Buscar todos los PDFs que empiezan por el localizador
    patron_pdf = os.path.join(carpeta_pdfs, f"{ref}*.pdf")
    archivos_pdf = glob.glob(patron_pdf)

    if archivos_pdf:
        print(f"Se encontraron {len(archivos_pdf)} PDF(s): {archivos_pdf}")

        contenido_pdf = ""
        total_paginas_pdf = 0  # <--- Aquí guardarás las páginas
        for ruta_pdf in archivos_pdf:
            print(f"Abriendo PDF: {ruta_pdf}")
            try:
                doc = fitz.open(ruta_pdf)
                total_paginas_pdf += len(doc)  # <--- Guarda páginas antes de cerrar
                for page in doc:
                    contenido_pdf += page.get_text()
                doc.close()
            except Exception as e:
                print(f"Error al leer el PDF {ruta_pdf}: {e}")
                tk.Label(root, text=f"Error al leer el PDF {os.path.basename(ruta_pdf)}: {e}", fg="red",
                         font=("Helvetica", 12)).pack(pady=10)

        # contenido_pdf_lower = contenido_pdf.lower()
        # print(f"Abriendo PDF: {ruta_pdf}")
        try:
            # doc = fitz.open(ruta_pdf)
            # contenido_pdf = ""
            # for page in doc:
            #     contenido_pdf += page.get_text()

            contenido_pdf_lower = contenido_pdf.lower()

            # Crear contenedor con canvas + scrollbar vertical funcional
            container = tk.Frame(root)
            container.pack(fill="both", expand=True)

            canvas = tk.Canvas(container, borderwidth=0)
            scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
            scrollable_frame = tk.Frame(canvas)

            # Actualizar scrollregion cuando cambia el contenido
            def on_configure(event):
                canvas.configure(scrollregion=canvas.bbox("all"))

            scrollable_frame.bind("<Configure>", on_configure)

            # Crear ventana dentro del canvas
            window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

            # Asegurar redimensionamiento horizontal
            def resize_canvas(event):
                canvas.itemconfig(window_id, width=event.width)

            canvas.bind("<Configure>", resize_canvas)

            canvas.configure(yscrollcommand=scrollbar.set)

            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")

            # Enlazar el scroll con la rueda del ratón
            def on_mouse_wheel(event):
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

            canvas.bind_all("<MouseWheel>", on_mouse_wheel)  # Windows
            canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))  # Linux scroll up
            canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))  # Linux scroll down

            # Este será tu frame donde añadirás los resultados como siempre
            resultado_frame = scrollable_frame
            resultado_frame.pack(pady=10)

            tk.Label(resultado_frame, text="--- Verificación de campos en el PDF ---",
                     font=("Helvetica", 12, "bold")).pack()

            for campo in ["Fecha de Visita", "Tipo"]:
                valor_original = campos_deseados[campo]
                # Dividir en partes posibles (separadas por / o , por ejemplo)
                partes = [parte.strip().lower() for parte in re.split(r'[/,;]', valor_original)]

                # Verificar si alguna de esas partes está en el texto
                encontrado = any(parte in contenido_pdf_lower for parte in partes)

                color = "green" if encontrado else "red"
                texto = f"{campo} ({valor_original}): {'OK' if encontrado else 'NO'}"
                tk.Label(resultado_frame, text=texto, fg=color, font=("Helvetica", 11)).pack(anchor="w")

            # Verificación de número de visitantes vs páginas del PDF
            try:
                total_pax = 0
                for clave_pax in ["PAX Adultas", "PAX Jubilado", "PAX Infantil 3 a 11 años",
                                  "PAX Infantil 12 a 15 años"]:
                    valor = campos_deseados.get(clave_pax)
                    if valor is not None:
                        try:
                            total_pax += int(valor)
                        except ValueError:
                            pass  # Si no es número, ignoramos

                visitantes_en_pdf = total_paginas_pdf // 2

                coincide = total_pax == visitantes_en_pdf
                color = "green" if coincide else "red"
                texto = f"Número de visitantes ({total_pax}) vs número de páginas total ({visitantes_en_pdf}): {'OK' if coincide else 'NO'}"
                tk.Label(resultado_frame, text=texto, fg=color, font=("Helvetica", 12)).pack(anchor="w")

            except Exception as e:
                tk.Label(resultado_frame, text=f"Error en verificación de visitantes: {e}",
                         fg="red", font=("Helvetica", 11)).pack(anchor="w")

            # --- Verificación de nombres y pasaportes desde Excel con búsqueda dinámica ---
            try:
                def find_header_row(file, keywords):
                    try:
                        df = pd.read_excel(file, engine="openpyxl", nrows=10, header=None)
                        for i, row in df.iterrows():
                            if any(any(keyword.lower() in str(cell).lower() for keyword in keywords) for cell in
                                   row):
                                return i
                    except Exception as e:
                        print(f"Error al leer el archivo: {e}")
                        return -1
                    return -1

                # Palabras clave
                keywords_nombre = ["영문성", "영문명", "영문이름", "영문성함", "name", "nombre", "surname", "apellido"]
                keywords_pasaporte = ["passport", "pasapor", "pass", "여권번호", "doc"]

                # Buscar fila del encabezado
                fila_headers = find_header_row(ruta_excel, keywords_nombre + keywords_pasaporte)
                if fila_headers == -1:
                    raise Exception("No se encontraron encabezados válidos en el Excel.")

                df_excel_full = pd.read_excel(ruta_excel, engine="openpyxl", header=None)
                df_datos = df_excel_full.iloc[fila_headers + 1:].copy()
                headers = df_excel_full.iloc[fila_headers]
                df_datos.columns = headers

                # Detectar nombres y pasaportes usando columnas con nombres cercanos
                col_nombre = next((col for col in df_datos.columns if
                                   any(k.lower() in str(col).lower() for k in keywords_nombre)), None)
                col_pasaporte = next((col for col in df_datos.columns if
                                      any(k.lower() in str(col).lower() for k in keywords_pasaporte)), None)

                if col_nombre and col_pasaporte:
                    tk.Label(resultado_frame, text="--- Verificación desde Excel ---",
                             font=("Helvetica", 12, "bold")).pack(pady=(10, 0))

                    for idx, row in df_datos.iterrows():
                        nombre_original = str(row[col_nombre]).strip()
                        nombre_excel = nombre_original.lower()

                        # Si tiene barra, asumimos formato APELLIDO/NOMBRE y lo invertimos
                        if "/" in nombre_excel:
                            partes = nombre_excel.split("/")
                            if len(partes) == 2:
                                nombre_excel = f"{partes[1]} {partes[0]}".strip()

                        pasaporte_excel = str(row[col_pasaporte]).strip().lower()

                        from itertools import permutations

                        partes = nombre_excel.split()
                        combinaciones = set()

                        # Combinaciones de todas las permutaciones posibles de hasta 3 palabras
                        for i in range(2, len(partes) + 1):
                            for p in permutations(partes, i):
                                combinaciones.add(" ".join(p))

                        # También añadir el nombre exacto como aparece, por si acaso
                        combinaciones.add(nombre_excel)

                        nombre_encontrado = any(c in contenido_pdf_lower for c in combinaciones)
                        pasaporte_encontrado = pasaporte_excel in contenido_pdf_lower

                        ambos_ok = nombre_encontrado and pasaporte_encontrado
                        color = "green" if ambos_ok else "red"
                        texto = f"{row[col_nombre]} - {row[col_pasaporte]}: {'OK' if ambos_ok else 'NO'}"

                        tk.Label(resultado_frame, text=texto, fg=color, font=("Helvetica", 11)).pack(anchor="w")
                else:
                    raise Exception("No se encontraron columnas de nombre o pasaporte en el Excel.")

            except Exception as e:
                tk.Label(resultado_frame,
                         text=f"Error al procesar nombres y pasaportes desde Excel: {e}",
                         fg="red", font=("Helvetica", 11)).pack(anchor="w")

            driver.quit()  # Muy importante

            tk.Label(resultado_frame, text="Comparación completa", font=("Helvetica", 12), fg="green").pack(pady=10)

        except Exception as e:
            print(f"Error al leer el PDF: {e}")
            tk.Label(root, text=f"Error al leer el PDF: {e}", fg="red", font=("Helvetica", 12)).pack(pady=10)
    else:
        print(f"PDF no encontrado: {ruta_pdf}")
        tk.Label(root, text=f"PDF no encontrado: {ruta_pdf}", fg="red", font=("Helvetica", 12)).pack(pady=10)

    # doc.close()


def lanzar_interfaz():
    root = TkinterDnD.Tk()
    root.title("Comparador de reservas")
    root.geometry("700x800")
    root.configure(bg="#f2f2f2")
    root.archivo_excel_path = None

    def on_submit():
        url = entry_url.get()
        if not url:
            return

        # Limpiar resultados anteriores
        for widget in resultado_frame.winfo_children():
            widget.destroy()

        # (Opcional) Deshabilitar el botón para evitar doble click
        submit_btn.config(state=tk.DISABLED)

        # Llamamos a la función principal, pasándole el resultado_frame
        iniciar_sesion_y_navegar(url, resultado_frame)

        # (Opcional) Limpiar el campo de entrada
        entry_url.delete(0, tk.END)

        # Reactivar el botón
        submit_btn.config(state=tk.NORMAL)

    # Widgets
    tk.Label(root, text="URL:", bg="#f2f2f2", font=("Helvetica", 12)).pack(pady=(10, 5))

    entry_url = tk.Entry(root, width=80, font=("Courier", 10))
    entry_url.pack(padx=20)

    submit_btn = tk.Button(
        root, text="Comparar reservas", command=on_submit,
        bg="#4CAF50", fg="white", padx=10, pady=5
    )
    submit_btn.pack(pady=20)

    # Marco donde se colocan los resultados (scroll o no, según necesites)
    resultado_frame = tk.Frame(root, bg="#ffffff", padx=10, pady=10)
    resultado_frame.pack(fill="both", expand=True, padx=20, pady=10)

    root.mainloop()


if __name__ == "__main__":
    lanzar_interfaz()
