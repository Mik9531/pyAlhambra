import psutil
import multiprocessing
import subprocess
import time

def iniciar_chrome():
    """Inicia Chrome con el puerto de depuración si no está en ejecución."""
    for proceso in psutil.process_iter(attrs=['pid', 'name']):
        if "chrome" in proceso.info['name'].lower():
            print("Chrome ya está en ejecución.")
            return  # No iniciar una nueva instancia

    print("Iniciando Chrome...")
    subprocess.Popen([
        "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
        "--remote-debugging-port=9222",
        "--user-data-dir=C:\\Temp\\ChromeSession",
        "--start-maximized"
    ], shell=False)

    time.sleep(5)  # Esperar unos segundos a que Chrome arranque


def ejecutar_script(ruta_script):
    """Ejecuta un script Python en un proceso separado."""
    subprocess.run(["python", ruta_script])


if __name__ == "__main__":
    iniciar_chrome()
    print("Chrome iniciado con depuración remota en el puerto 9222.")

    # Rutas a los scripts
    script_general = "pyAlhambraNotifications.py"
    script_jardines = "pyAlhambraNotificationsJardines.py"

    # Crear procesos para ejecutar los scripts en paralelo
    proceso_general = multiprocessing.Process(target=ejecutar_script, args=(script_general,))
    proceso_jardines = multiprocessing.Process(target=ejecutar_script, args=(script_jardines,))

    # Iniciar los procesos
    proceso_general.start()
    proceso_jardines.start()

    print("Ambos scripts han sido iniciados en paralelo.")