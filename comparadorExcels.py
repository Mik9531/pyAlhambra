from tkinter import Tk, Label, filedialog, Button


import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import PatternFill
from datetime import datetime  # Importar el módulo datetime


def compare_excels(file1, file2, output_file):
    # Leer ambos archivos Excel (ajustando encabezados)
    df1 = pd.read_excel(file1, header=1, engine="openpyxl")
    df2 = pd.read_excel(file2, header=1, engine="openpyxl")

    # Renombrar columnas no válidas

    df1.columns = [f"Col_{i}" if 'Unnamed' in col else col for i, col in enumerate(df1.columns)]
    df2.columns = [f"Col_{i}" if 'Unnamed' in col else col for i, col in enumerate(df2.columns)]

    # Eliminar la primera columna "Col_0" si existe
    if "Col_0" in df1.columns:
        df1 = df1.drop(columns=["Col_0"])
    if "Col_0" in df2.columns:
        df2 = df2.drop(columns=["Col_0"])

    # Verificar columnas requeridas
    required_columns = ["Name", "Sex"]
    for col in required_columns:
        if col not in df1.columns or col not in df2.columns:
            raise ValueError(f"La columna requerida '{col}' no está presente en uno o ambos archivos Excel.")

    # Comparar los archivos Excel
    diff_df = df1.copy()
    for row in range(len(df1)):
        if row < len(df2):
            for col in required_columns:
                if df1.at[row, col] != df2.at[row, col]:
                    diff_df.at[row, col] = f'{df1.at[row, col]} --> {df2.at[row, col]}'

    # Identificar filas adicionales únicas en el archivo 2
    # Comparar las filas completas, no solo las columnas requeridas
    additional_rows = df2[~df2.apply(tuple, axis=1).isin(df1.apply(tuple, axis=1))]

    # Guardar diferencias en un nuevo archivo
    diff_df.to_excel(output_file, index=False)

    # Resaltar diferencias en el archivo generado
    wb = load_workbook(output_file)
    ws = wb.active
    red_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
    yellow_fill = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")

    # Resaltar diferencias
    for row in range(2, ws.max_row + 1):
        for col in range(1, ws.max_column + 1):
            cell = ws.cell(row=row, column=col)
            if '-->' in str(cell.value):
                cell.fill = red_fill

    # Verificar el número de filas en df1
    last_row_in_df1 = len(df1)

    # Solo agregar filas adicionales cuyo número de fila en df2 sea mayor que el último en df1
    for _, additional_row in additional_rows.iterrows():
        # Verificar el número de la fila en df2 (NO)
        row_number_in_df2 = additional_row.name + 1  # La fila en df2
        if row_number_in_df2 > last_row_in_df1:
            # Agregar la fila al archivo de salida si es mayor
            ws.append(additional_row.tolist())
            for col in range(1, len(additional_row) + 1):
                ws.cell(row=ws.max_row, column=col).fill = yellow_fill

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
