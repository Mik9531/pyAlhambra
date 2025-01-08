from tkinter import Tk, Label, filedialog, Button
import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import PatternFill
from datetime import datetime


def find_header_row(file, keyword):
    """
    Encuentra la fila donde se encuentra una columna que contiene el keyword.
    """
    wb = load_workbook(file, read_only=True)
    ws = wb.active
    for i, row in enumerate(ws.iter_rows(values_only=True), start=1):
        if any(keyword.lower() in (str(cell).lower() if cell else "") for cell in row):
            return i
    return 1  # Por defecto, si no se encuentra, usar la primera fila


def compare_excels(file1, file2, output_file):
    # Detectar la fila de encabezados en ambos archivos
    header_row1 = find_header_row(file1, "no")
    header_row2 = find_header_row(file2, "no")

    # Leer ambos archivos Excel desde la fila detectada
    df1 = pd.read_excel(file1, header=header_row1 - 1, engine="openpyxl")
    df2 = pd.read_excel(file2, header=header_row2 - 1, engine="openpyxl")

    # Renombrar columnas no válidas
    df1.columns = [f"Col_{i}" if 'Unnamed' in col else col for i, col in enumerate(df1.columns)]
    df2.columns = [f"Col_{i}" if 'Unnamed' in col else col for i, col in enumerate(df2.columns)]

    # Identificar columnas de interés
    cols_of_interest1 = [col for col in df1.columns if any(
        keyword in col.lower() for keyword in ["name", "nombre", "pass", "영문명", "영문성함", "여권번호"]) and "kor" not in col.lower()]
    cols_of_interest2 = [col for col in df2.columns if any(
        keyword in col.lower() for keyword in ["name", "nombre", "pass", "영문명", "영문성함", "여권번호"]) and "kor" not in col.lower()]

    # Filtrar ambas tablas
    df1_filtered = df1[cols_of_interest1]
    df2_filtered = df2[cols_of_interest2]

    # Normalizar nombres de columnas
    df1_filtered.columns = df2_filtered.columns = ["Nombre/Apellido", "Pasaporte"]

    # Crear diccionarios para comparación
    dict1 = {str(row["Nombre/Apellido"]).strip().lower(): str(row["Pasaporte"]).strip() for _, row in df1_filtered.iterrows()}
    dict2 = {str(row["Nombre/Apellido"]).strip().lower(): str(row["Pasaporte"]).strip() for _, row in df2_filtered.iterrows()}

    # Fusionar los nombres de ambos diccionarios
    all_names = set(dict1.keys()).union(set(dict2.keys()))

    # Preparar las filas para el resultado
    result_rows = []
    for name in all_names:
        passport1 = dict1.get(name, "")
        passport2 = dict2.get(name, "")
        if passport1 and passport2 and passport1 != passport2:
            # Diferentes pasaportes
            result_rows.append([name.title(), f"{passport1} -> {passport2}"])
        elif passport1 and not passport2:
            # Solo en archivo 1
            result_rows.append([name.title(), f"{passport1} -> "])
        elif passport2 and not passport1:
            # Solo en archivo 2
            result_rows.append([name.title(), f" -> {passport2}"])
        else:
            # Igual pasaporte
            result_rows.append([name.title(), passport1])

    # Crear DataFrame de diferencias
    diff_df = pd.DataFrame(result_rows, columns=["Nombre/Apellido", "Pasaporte"])

    # Guardar diferencias en un nuevo archivo
    diff_df.to_excel(output_file, index=False)

    # Resaltar diferencias en el archivo generado
    wb = load_workbook(output_file)
    ws = wb.active
    red_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")

    # Resaltar diferencias en las celdas donde hay cambios
    for row in range(2, ws.max_row + 1):
        cell = ws.cell(row=row, column=2)  # Columna de Pasaporte
        if "->" in str(cell.value) and str(cell.value).strip() != "":
            cell.fill = red_fill

    # Guardar el archivo final
    wb.save(output_file)


def browse_file(label):
    filename = filedialog.askopenfilename(filetypes=[["Excel files", "*.xlsx"]])
    if filename:
        label.config(text=filename)
        return filename
    return None


def run_comparator():
    file1 = label_file1.cget("text")
    file2 = label_file2.cget("text")

    if not file1 or not file2:
        result_label.config(text="Por favor, selecciona ambos archivos.", fg="red")
        return

    output_file = f"roomingConDiferencias_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    try:
        compare_excels(file1, file2, output_file)
        result_label.config(text=f"Comparación completada. Archivo guardado como: {output_file}", fg="green")
    except ValueError as e:
        result_label.config(text=str(e), fg="red")


# Crear la interfaz gráfica
root = Tk()
root.title("Comparador de Excel de Roomings")

Label(root, text="Selecciona el Excel 1").pack()
label_file1 = Label(root, text="", bg="lightgray", width=50)
label_file1.pack(pady=5)
Button(root, text="Seleccionar Excel 1", command=lambda: browse_file(label_file1)).pack()

Label(root, text="Selecciona el Excel 2").pack()
label_file2 = Label(root, text="", bg="lightgray", width=50)
label_file2.pack(pady=5)
Button(root, text="Seleccionar Excel 2", command=lambda: browse_file(label_file2)).pack()

Button(root, text="Comparar Excels", command=run_comparator).pack(pady=20)

result_label = Label(root, text="")
result_label.pack()

root.mainloop()
