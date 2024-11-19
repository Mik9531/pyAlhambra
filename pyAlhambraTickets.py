from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys  # Importa Keys para poder usar ENTER
import time

TIEMPO = 5

TIEMPOLARGO = 5

# Inicializa el controlador de Chrome
driver = webdriver.Chrome()

try:
    # Accede a la URL
    driver.get('https://tickets.alhambra-patronato.es/')

    # Espera un poco para que la página cargue completamente
    time.sleep(TIEMPO)

    # Encuentra el botón por su texto y haz clic
    enlace = driver.find_element(By.XPATH,
                                 "//a[@href='https://tickets.alhambra-patronato.es/producto/alhambra-general/']")
    enlace.click()

    # Espera para ver el resultado
    time.sleep(TIEMPO)

    # Encuentra el botón por su texto y haz clic
    enlace = driver.find_element(By.XPATH,
                                 "//a[@href='https://compratickets.alhambra-patronato.es/reservarEntradas.aspx?opc=142&gid=432&lg=es-ES&ca=0&m=GENERAL']")
    enlace.click()

    # Espera para ver el resultado
    time.sleep(TIEMPO)

    # Encuentra el botón por su texto y haz clic
    boton = driver.find_element(By.ID, "ctl00_lnkAceptarTodoCookies_Info")
    boton.click()

    # Espera para ver el resultado
    time.sleep(TIEMPO)

    # Encuentra el botón por su texto y haz clic
    boton = driver.find_element(By.ID, "ctl00_ContentMaster1_ucReservarEntradasBaseAlhambra1_btnIrPaso1")
    boton.click()

    # Espera para ver el resultado
    time.sleep(5)

    # Encuentra el botón por su texto y haz clic
    td_element = driver.find_element(By.CSS_SELECTOR, "td.calendario_padding.ult-plaza")
    td_element.find_element(By.TAG_NAME, "a").click()

    # Espera para ver el resultado
    time.sleep(TIEMPOLARGO)

    # Encuentra el input por su id
    input_element = driver.find_element(By.ID,
                                        "ctl00_ContentMaster1_ucReservarEntradasBaseAlhambra1_rptGruposEntradas_ctl00_rptEntradas_ctl00_txtCantidad2")

    # Selecciona todo el texto existente (si es necesario)
    input_element.click()  # Hacemos clic en el input para seleccionarlo
    input_element.clear()  # Limpia el input
    input_element.send_keys("1" + Keys.RETURN)  # Introduce "1" y luego ENTER

    # Espera para ver el resultado
    time.sleep(TIEMPOLARGO)

    # Encuentra el botón por su atributo name y haz clic
    boton = driver.find_element(By.NAME, "ctl00$ContentMaster1$ucReservarEntradasBaseAlhambra1$btnIrPaso2")
    boton.click()

    # Espera para ver el resultado después de hacer clic
    time.sleep(TIEMPOLARGO)

    # Encuentra el radio button por su id y haz clic
    span_element = driver.find_element(By.XPATH,
                                       "//label[@id='ctl00_ContentMaster1_ucReservarEntradasBaseAlhambra1_rptRecintos_ctl00_rptSesiones_ctl00_lblMarco']/span")
    span_element.click()

    # Espera para ver el resultado después de hacer clic
    time.sleep(5)

    # Encuentra el radio button por su id y haz clic
    enlace = driver.find_element(By.ID, "ctl00_ContentMaster1_ucReservarEntradasBaseAlhambra1_lnkOkHorarios")
    enlace.click()

    # Espera para ver el resultado después de hacer clic
    time.sleep(5)

    # Encuentra el botón por su atributo name y haz clic
    boton = driver.find_element(By.NAME, "ctl00$ContentMaster1$ucReservarEntradasBaseAlhambra1$btnIrPaso3")
    boton.click()

    # Espera para ver el resultado después de hacer clic
    time.sleep(TIEMPOLARGO)

    # Bucle que refresca la página cada 10 segundos
    while True:
        # Refresca la página
        driver.refresh()
        print("Página refrescada")

        # Espera 10 segundos antes de volver a refrescar
        time.sleep(10)

    # time.sleep(5000)


finally:
    # Cierra el navegador
    driver.quit()
